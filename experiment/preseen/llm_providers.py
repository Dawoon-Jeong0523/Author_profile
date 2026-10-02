#!/usr/bin/env python3
"""llm_providers.py: one call per LLM provider (Anthropic, OpenAI, Gemini) over plain HTTPS with requests.

    from llm_providers import call
    res = call("anthropic", "claude-opus-5-5", system, user, schema, max_output_tokens=32000)

The same system text, user text and JSON schema go to every provider; only the API envelope differs. Nothing else is
sent: no tools, no web search, no grounding, no sampling parameters (temperature etc.), no reasoning / effort /
thinking settings and no model fallbacks, so every provider runs with its defaults. The provider's JSON mode is used
(Anthropic output_config.format, OpenAI text.format strict json_schema, Gemini responseJsonSchema); the caller
validates the parsed JSON itself.

`call` returns a dict: provider, model_requested, model_reported, request (url, header names, body), http (one entry
per HTTP attempt), response_id, stop, truncated, refused, usage (input, output incl. reasoning, reasoning,
cached_input), usage_raw, response_raw, text, parsed, parse_error, error.

Secrets: each key is read with os.environ[...] when the request headers are built, sent only in a header, and never
stored: `request` keeps header names only, exceptions are recorded by class name only, and the bodies of 401/403
responses are dropped (some echo a masked key). Variable names come from config.yaml `api_keys`.
"""
import datetime as dt
import json
import os
import time
from pathlib import Path

import requests
import yaml

KEY_VARS = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())["api_keys"]
TIMEOUT = (30, 1200)                     # connect, read (s); non-streaming, so the read waits for the whole answer
TRANSIENT = {408, 429, 500, 502, 503, 504, 529}
BACKOFF = (15, 60, 180)                  # waits before HTTP attempts 2..4 on a transient status or network error
KEEP_HEADERS = ("request-id", "x-request-id", "openai-processing-ms", "retry-after")


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- request envelopes (key read at header build time)

def _anthropic_request(model, system, user, schema, max_out):
    body = {"model": model, "max_tokens": max_out, "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"format": {"type": "json_schema", "schema": schema}}}
    headers = lambda: {"x-api-key": os.environ[KEY_VARS["anthropic"]], "anthropic-version": "2023-06-01",
                       "content-type": "application/json"}
    return "https://api.anthropic.com/v1/messages", body, headers


def _openai_request(model, system, user, schema, max_out):
    body = {"model": model, "instructions": system,
            "input": [{"role": "user", "content": user}],
            "text": {"format": {"type": "json_schema", "name": "ballot", "schema": schema, "strict": True}},
            "max_output_tokens": max_out,
            "store": False}                                   # do not keep the response on OpenAI's side
    headers = lambda: {"Authorization": f"Bearer {os.environ[KEY_VARS['openai']]}", "Content-Type": "application/json"}
    return "https://api.openai.com/v1/responses", body, headers


def _gemini_request(model, system, user, schema, max_out):
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": schema,
                                 "maxOutputTokens": max_out}}
    headers = lambda: {"x-goog-api-key": os.environ[KEY_VARS["gemini"]], "Content-Type": "application/json"}
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", body, headers


# ---------------------------------------------------------------- response parsers -> common fields

def _anthropic_parse(r):
    u = r.get("usage") or {}
    stop = r.get("stop_reason")
    return {"text": "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text"),
            "model_reported": r.get("model"), "response_id": r.get("id"),
            "stop": stop, "truncated": stop == "max_tokens", "refused": stop == "refusal",
            "stop_details": r.get("stop_details"),
            "usage": {"input": u.get("input_tokens"), "output": u.get("output_tokens"),
                      "reasoning": (u.get("output_tokens_details") or {}).get("thinking_tokens"),
                      "cached_input": u.get("cache_read_input_tokens")},
            "usage_raw": u}


def _openai_parse(r):
    u = r.get("usage") or {}
    texts, refused = [], False
    for item in r.get("output", []):
        if item.get("type") != "message":
            continue
        for c in item.get("content", []):
            if c.get("type") == "output_text":
                texts.append(c.get("text", ""))
            elif c.get("type") == "refusal":
                refused = True
    inc = (r.get("incomplete_details") or {}).get("reason")
    return {"text": "".join(texts), "model_reported": r.get("model"), "response_id": r.get("id"),
            "stop": r.get("status") + (f":{inc}" if inc else "") if r.get("status") else inc,
            "truncated": inc == "max_output_tokens", "refused": refused,
            "reasoning_effort": (r.get("reasoning") or {}).get("effort"),
            "usage": {"input": u.get("input_tokens"), "output": u.get("output_tokens"),
                      "reasoning": (u.get("output_tokens_details") or {}).get("reasoning_tokens"),
                      "cached_input": (u.get("input_tokens_details") or {}).get("cached_tokens")},
            "usage_raw": u}


def _gemini_parse(r):
    u = r.get("usageMetadata") or {}
    cands = r.get("candidates") or [{}]
    c = cands[0]
    parts = (c.get("content") or {}).get("parts") or []
    stop = c.get("finishReason") or (r.get("promptFeedback") or {}).get("blockReason")
    cand, thoughts = u.get("candidatesTokenCount") or 0, u.get("thoughtsTokenCount") or 0
    return {"text": "".join(p.get("text", "") for p in parts if not p.get("thought")),
            "model_reported": r.get("modelVersion"), "response_id": r.get("responseId"),
            "stop": stop, "truncated": stop == "MAX_TOKENS",
            "refused": stop in {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION", "OTHER"},
            "usage": {"input": u.get("promptTokenCount"), "output": cand + thoughts, "reasoning": thoughts,
                      "cached_input": u.get("cachedContentTokenCount")},
            "usage_raw": u}


PROVIDERS = {"anthropic": (_anthropic_request, _anthropic_parse),
             "openai": (_openai_request, _openai_parse),
             "gemini": (_gemini_request, _gemini_parse)}


def _error_summary(status, resp):
    """Short, key-free description of an HTTP error body (dropped entirely for 401/403)."""
    if status in (401, 403):
        return "auth error (body not kept)"
    try:
        e = resp.json().get("error", {})
    except ValueError:
        return "non-JSON error body"
    if isinstance(e, dict):
        return " | ".join(str(e[k])[:500] for k in ("type", "code", "status", "message") if e.get(k))
    return str(e)[:500]


def _header_names(provider):
    return {"anthropic": ("x-api-key", "anthropic-version: 2023-06-01", "content-type"),
            "openai": ("Authorization: Bearer", "Content-Type"),
            "gemini": ("x-goog-api-key", "Content-Type")}[provider]


def call(provider, model, system, user, schema, max_output_tokens):
    build, parse = PROVIDERS[provider]
    url, body, headers = build(model, system, user, schema, max_output_tokens)
    out = {"provider": provider, "model_requested": model, "model_reported": None,
           "request": {"url": url, "header_names": list(_header_names(provider)), "body": body},
           "http": [], "response_id": None, "stop": None, "truncated": False, "refused": False,
           "usage": None, "usage_raw": None, "response_raw": None, "text": None, "parsed": None,
           "parse_error": None, "error": None}
    resp = None
    for attempt in range(len(BACKOFF) + 1):
        if attempt:
            time.sleep(BACKOFF[attempt - 1])
        rec = {"attempt": attempt + 1, "started": _now()}
        t0 = time.monotonic()
        try:
            resp = requests.post(url, headers=headers(), json=body, timeout=TIMEOUT)
        except requests.RequestException as e:            # class name only (never the message)
            rec.update(ended=_now(), seconds=round(time.monotonic() - t0, 1), status=None,
                       error=f"ERR:{type(e).__name__}")
            out["http"].append(rec)
            resp = None
            continue
        rec.update(ended=_now(), seconds=round(time.monotonic() - t0, 1), status=resp.status_code,
                   headers={h: resp.headers[h] for h in KEEP_HEADERS if h in resp.headers})
        if not resp.ok:
            rec["error"] = _error_summary(resp.status_code, resp)
        out["http"].append(rec)
        if resp.ok or resp.status_code not in TRANSIENT or "limit: 0" in rec.get("error", ""):
            break                                         # "limit: 0" = no quota at all (e.g. free tier), not a rate
    if resp is None or not resp.ok:
        out["error"] = out["http"][-1].get("error") or "no response"
        return out
    try:
        raw = resp.json()
    except ValueError:
        out["error"] = "response body is not JSON"
        return out
    out["response_raw"] = raw
    out.update(parse(raw))
    try:
        out["parsed"] = json.loads(out["text"])
    except (TypeError, ValueError) as e:
        out["parse_error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return out
