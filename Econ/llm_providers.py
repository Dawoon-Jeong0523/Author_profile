#!/usr/bin/env python3
"""llm_providers.py (Econ): one call per provider (Anthropic, OpenAI, Gemini) over plain HTTPS with requests.

    from llm_providers import call_json, key_is_set
    rec = call_json("anthropic", "claude-opus-5-5", system, user, schema, max_output_tokens=16000, effort=None)

The same system text, user text and JSON schema go to every provider; only the envelope differs. The provider's JSON
mode is used (Anthropic output_config.format, OpenAI text.format strict json_schema, Gemini responseJsonSchema); the
caller validates the parsed object. Nothing else is sent: no tools, no web search, no grounding, no sampling
parameters and no model fallbacks. `effort` is sent only when given (Anthropic output_config.effort, OpenAI
reasoning.effort, Gemini thinkingConfig.thinkingLevel); None = the provider's default.

`call_json` returns a record: provider, model_requested, model_reported, request (url, header names, body), http (one
entry per HTTP attempt), response_raw, response_id, stop, truncated, refused, usage (input, output incl. reasoning,
reasoning, cached_input), usage_raw, text, parsed, parse_error, error.

Secrets: each key is read with os.environ[...] when the request headers are built, sent only in a header, never
stored: `request` keeps header names only, exceptions are recorded by class name only, and the bodies of 401/403
responses are dropped (some echo a masked key). Variable names come from config.yaml `api_keys`.
(The web-search version of this module, not used now, is kept in 01_committee/Old/websearch_2026-10-09/.)
"""
import datetime as dt
import json
import os
import socket
import threading
import time
from pathlib import Path

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection

KEY_VARS = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())["api_keys"]
TIMEOUT = (30, 1200)                     # connect, read (s); non-streaming, so the read waits for the whole answer
TRANSIENT = {408, 429, 500, 502, 503, 504, 529}
BACKOFF = (15, 60, 180)                  # waits before HTTP attempts 2..4 on a transient status or network error
KEEP_HEADERS = ("request-id", "x-request-id", "openai-processing-ms", "retry-after")
URLS = {"anthropic": "https://api.anthropic.com/v1/messages",
        "openai": "https://api.openai.com/v1/responses",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"}
HEADER_NAMES = {"anthropic": ["x-api-key", "anthropic-version: 2023-06-01", "content-type"],
                "openai": ["Authorization: Bearer", "Content-Type"],
                "gemini": ["x-goog-api-key", "Content-Type"]}


class _KeepAlive(HTTPAdapter):
    """TCP keepalive: a non-streaming call waits minutes for its answer, and idle connections can be dropped."""
    def init_poolmanager(self, *args, **kwargs):
        opts = list(HTTPConnection.default_socket_options) + [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
        for name, val in (("TCP_KEEPIDLE", 60), ("TCP_KEEPINTVL", 30), ("TCP_KEEPCNT", 8)):
            if hasattr(socket, name):
                opts.append((socket.IPPROTO_TCP, getattr(socket, name), val))
        kwargs["socket_options"] = opts
        super().init_poolmanager(*args, **kwargs)


_TLS = threading.local()


def _session():
    """One requests.Session per thread (a Session is not guaranteed to be thread-safe)."""
    if not hasattr(_TLS, "session"):
        s = requests.Session()
        s.mount("https://", _KeepAlive())
        _TLS.session = s
    return _TLS.session


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def key_is_set(provider):
    var = KEY_VARS[provider]
    return var in os.environ and bool(os.environ[var].strip())


def _headers(provider):
    if provider == "anthropic":
        return {"x-api-key": os.environ[KEY_VARS["anthropic"]], "anthropic-version": "2023-06-01",
                "content-type": "application/json"}
    if provider == "openai":
        return {"Authorization": f"Bearer {os.environ[KEY_VARS['openai']]}", "Content-Type": "application/json"}
    return {"x-goog-api-key": os.environ[KEY_VARS["gemini"]], "Content-Type": "application/json"}


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


def _post(provider, url, body, http_log):
    """POST with the transient retries; returns (json or None, error or None); every attempt goes to http_log."""
    resp = None
    for attempt in range(len(BACKOFF) + 1):
        if attempt:
            time.sleep(BACKOFF[attempt - 1])
        rec = {"attempt": attempt + 1, "started": _now()}
        t0 = time.monotonic()
        try:
            resp = _session().post(url, headers=_headers(provider), json=body, timeout=TIMEOUT)
        except requests.RequestException as e:            # class name only (never the message)
            rec.update(ended=_now(), seconds=round(time.monotonic() - t0, 1), status=None,
                       error=f"ERR:{type(e).__name__}")
            http_log.append(rec)
            resp = None
            continue
        rec.update(ended=_now(), seconds=round(time.monotonic() - t0, 1), status=resp.status_code,
                   headers={h: resp.headers[h] for h in KEEP_HEADERS if h in resp.headers})
        if not resp.ok:
            rec["error"] = _error_summary(resp.status_code, resp)
        http_log.append(rec)
        if resp.ok or resp.status_code not in TRANSIENT or "limit: 0" in rec.get("error", ""):
            break                                         # "limit: 0" = no quota at all (e.g. free tier), not a rate
    if resp is None or not resp.ok:
        return None, (http_log[-1].get("error") if http_log else None) or "no response"
    try:
        return resp.json(), None
    except ValueError:
        return None, "response body is not JSON"


# ---------------------------------------------------------------- request envelopes and response parsers

def _body(provider, model, system, user, schema, max_out, effort):
    if provider == "anthropic":
        oc = {"format": {"type": "json_schema", "schema": schema}}
        if effort:
            oc["effort"] = effort
        return {"model": model, "max_tokens": max_out, "system": system,
                "messages": [{"role": "user", "content": user}], "output_config": oc}
    if provider == "openai":
        body = {"model": model, "instructions": system, "input": [{"role": "user", "content": user}],
                "text": {"format": {"type": "json_schema", "name": "result", "schema": schema, "strict": True}},
                "max_output_tokens": max_out, "store": False}       # store=False: no response kept on OpenAI's side
        if effort:
            body["reasoning"] = {"effort": effort}
        return body
    gc = {"responseMimeType": "application/json", "responseJsonSchema": schema, "maxOutputTokens": max_out}
    if effort:
        gc["thinkingConfig"] = {"thinkingLevel": effort}
    return {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": gc}


def _anthropic_parse(r):
    u = r.get("usage") or {}
    stop = r.get("stop_reason")
    cached = u.get("cache_read_input_tokens") or 0
    return {"text": "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text"),
            "model_reported": r.get("model"), "response_id": r.get("id"),
            "stop": stop, "truncated": stop in ("max_tokens", "model_context_window_exceeded"),
            "refused": stop == "refusal", "stop_details": r.get("stop_details"),
            "usage": {"input": (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0) + cached,
                      "output": u.get("output_tokens"),
                      "reasoning": (u.get("output_tokens_details") or {}).get("thinking_tokens"),
                      "cached_input": cached},
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
    status = r.get("status")
    return {"text": "".join(texts), "model_reported": r.get("model"), "response_id": r.get("id"),
            "stop": (status + (f":{inc}" if inc else "")) if status else inc,
            "truncated": inc == "max_output_tokens", "refused": refused,
            "reasoning_effort": (r.get("reasoning") or {}).get("effort"),
            "usage": {"input": u.get("input_tokens"), "output": u.get("output_tokens"),
                      "reasoning": (u.get("output_tokens_details") or {}).get("reasoning_tokens"),
                      "cached_input": (u.get("input_tokens_details") or {}).get("cached_tokens")},
            "usage_raw": u}


def _gemini_parse(r):
    u = r.get("usageMetadata") or {}
    c = (r.get("candidates") or [{}])[0]
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


PARSE = {"anthropic": _anthropic_parse, "openai": _openai_parse, "gemini": _gemini_parse}


def call_json(provider, model, system, user, schema, max_output_tokens, effort=None):
    url = URLS[provider].format(model=model)
    body = _body(provider, model, system, user, schema, max_output_tokens, effort)
    out = {"provider": provider, "model_requested": model, "model_reported": None,
           "request": {"url": url, "header_names": HEADER_NAMES[provider], "body": body},
           "http": [], "response_raw": None, "response_id": None, "stop": None, "truncated": False,
           "refused": False, "usage": None, "usage_raw": None, "text": None, "parsed": None, "parse_error": None,
           "error": None}
    raw, err = _post(provider, url, body, out["http"])
    if err:
        out["error"] = err
        return out
    out["response_raw"] = raw
    out.update(PARSE[provider](raw))
    if provider == "openai" and raw.get("status") not in (None, "completed") and not out["truncated"]:
        out["error"] = f"status {raw.get('status')}"
    try:
        out["parsed"] = json.loads(out["text"])
    except (TypeError, ValueError) as e:
        out["parse_error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return out
