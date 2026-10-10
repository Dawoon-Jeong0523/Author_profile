#!/usr/bin/env python3
"""llm_providers.py (Econ): calls to Anthropic, OpenAI and Gemini over plain HTTPS with requests.

    call_json(provider, model, system, user, schema, max_output_tokens, effort=None)
        one call in the provider's JSON mode, no tools (Anthropic output_config.format, OpenAI text.format strict
        json_schema, Gemini responseJsonSchema); the caller validates the parsed object.
    call_research(provider, model, system, user, max_output_tokens, effort=None, search=None)
        one research call with the provider's own web search and page reading (Anthropic web_search_20260209 +
        web_fetch_20260209, continued on pause_turn; OpenAI Responses web_search with the full source list; Gemini
        google_search + url_context). Returns the answer text, the provider's citations as numbered markers
        ([A3], [O5], [G2]) placed next to the text they support where the provider gives positions, the search
        queries, every page the tool returned or opened, and a "dossier" (text + numbered source list) for the
        extraction step.
    key_is_set(provider)

Both return a record: provider, model_requested, model_reported, request (url, header names, body), http (one entry
per HTTP attempt), response_raw (list: one per request of a continued Anthropic turn), stop, truncated, refused, usage
(input, output incl. reasoning, reasoning, cached_input), searches (billed search calls/queries), fetches, text,
parsed / parse_error (JSON mode), error; research records add queries, retrieved, sources_table, grounded_urls,
dossier.

Not sent: sampling parameters, model fallbacks. Effort is sent only when given (settings.yaml); None = provider default.

Secrets: each key is read with os.environ[...] when the request headers are built, sent only in a header, never
stored: `request` keeps header names only, exceptions are recorded by class name only, and the bodies of 401/403
responses are dropped (some echo a masked key). Variable names come from config.yaml `api_keys`.
"""
import datetime as dt
import json
import os
import re
import socket
import threading
import time
from pathlib import Path

import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection

KEY_VARS = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())["api_keys"]


class _KeepAlive(HTTPAdapter):
    """TCP keepalive on the API connections: a non-streaming research call can wait many minutes for its answer, and
    idle connections may be dropped by the network on the way (the providers recommend streaming or keepalive)."""
    def init_poolmanager(self, *args, **kwargs):
        opts = list(HTTPConnection.default_socket_options) + [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]
        for name, val in (("TCP_KEEPIDLE", 60), ("TCP_KEEPINTVL", 30), ("TCP_KEEPCNT", 8)):
            if hasattr(socket, name):
                opts.append((socket.IPPROTO_TCP, getattr(socket, name), val))
        kwargs["socket_options"] = opts
        super().init_poolmanager(*args, **kwargs)


_TLS = threading.local()


def _session():
    """One requests.Session per thread (a Session is not guaranteed to be thread-safe), with keepalive."""
    if not hasattr(_TLS, "session"):
        s = requests.Session()
        s.mount("https://", _KeepAlive())
        _TLS.session = s
    return _TLS.session
TIMEOUT = (30, 1800)                     # connect, read (s); non-streaming, so the read waits for the whole answer
TRANSIENT = {408, 429, 500, 502, 503, 504, 529}
BACKOFF = (15, 60, 180)                  # waits before HTTP attempts 2..4 on a transient status or network error
KEEP_HEADERS = ("request-id", "x-request-id", "openai-processing-ms", "retry-after")
MAX_CONTINUATIONS = 6                    # Anthropic pause_turn continuations per research call
LETTER = {"anthropic": "A", "openai": "O", "gemini": "G"}
URLS = {"anthropic": "https://api.anthropic.com/v1/messages",
        "openai": "https://api.openai.com/v1/responses",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"}
HEADER_NAMES = {"anthropic": ["x-api-key", "anthropic-version: 2023-06-01", "content-type"],
                "openai": ["Authorization: Bearer", "Content-Type"],
                "gemini": ["x-goog-api-key", "Content-Type"]}


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


def _record(provider, model, url, body):
    return {"provider": provider, "model_requested": model, "model_reported": None,
            "request": {"url": url, "header_names": HEADER_NAMES[provider], "body": body},
            "http": [], "response_raw": [], "response_id": None, "stop": None, "truncated": False, "refused": False,
            "usage": None, "usage_raw": None, "searches": 0, "fetches": 0, "text": None, "parsed": None,
            "parse_error": None, "error": None}


# ---------------------------------------------------------------- usage

def _anthropic_usage(us):
    tot = {"input": 0, "output": 0, "reasoning": None, "cached_input": 0}
    searches = fetches = 0
    for u in us:
        tot["input"] += (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        tot["cached_input"] += u.get("cache_read_input_tokens") or 0
        tot["output"] += u.get("output_tokens") or 0
        st = u.get("server_tool_use") or {}
        searches += st.get("web_search_requests") or 0
        fetches += st.get("web_fetch_requests") or 0
    tot["input"] += tot["cached_input"]                      # billed at a discount; counted in full here (upper bound)
    return tot, searches, fetches


def _openai_usage(u):
    return {"input": u.get("input_tokens"), "output": u.get("output_tokens"),
            "reasoning": (u.get("output_tokens_details") or {}).get("reasoning_tokens"),
            "cached_input": (u.get("input_tokens_details") or {}).get("cached_tokens")}


def _gemini_usage(u):
    cand, thoughts = u.get("candidatesTokenCount") or 0, u.get("thoughtsTokenCount") or 0
    return {"input": (u.get("promptTokenCount") or 0) + (u.get("toolUsePromptTokenCount") or 0),
            "output": cand + thoughts, "reasoning": thoughts, "cached_input": u.get("cachedContentTokenCount")}


# ---------------------------------------------------------------- JSON mode (no tools)

def call_json(provider, model, system, user, schema, max_output_tokens, effort=None):
    if provider == "anthropic":
        oc = {"format": {"type": "json_schema", "schema": schema}}
        if effort:
            oc["effort"] = effort
        body = {"model": model, "max_tokens": max_output_tokens, "system": system,
                "messages": [{"role": "user", "content": user}], "output_config": oc}
        url = URLS["anthropic"]
    elif provider == "openai":
        body = {"model": model, "instructions": system, "input": [{"role": "user", "content": user}],
                "text": {"format": {"type": "json_schema", "name": "result", "schema": schema, "strict": True}},
                "max_output_tokens": max_output_tokens, "store": False}
        if effort:
            body["reasoning"] = {"effort": effort}
        url = URLS["openai"]
    else:
        gc = {"responseMimeType": "application/json", "responseJsonSchema": schema,
              "maxOutputTokens": max_output_tokens}
        if effort:
            gc["thinkingConfig"] = {"thinkingLevel": effort}
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": gc}
        url = URLS["gemini"].format(model=model)
    out = _record(provider, model, url, body)
    raw, err = _post(provider, url, body, out["http"])
    if err:
        out["error"] = err
        return out
    out["response_raw"].append(raw)
    if provider == "anthropic":
        _anthropic_finish(out, [raw], raw.get("content") or [])
    elif provider == "openai":
        _openai_finish(out, raw)
    else:
        _gemini_finish(out, raw)
    try:
        out["parsed"] = json.loads(out["text"])
    except (TypeError, ValueError) as e:
        out["parse_error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return out


# ---------------------------------------------------------------- research (web search on)

def call_research(provider, model, system, user, max_output_tokens, effort=None, search=None):
    search = search or {}
    fn = {"anthropic": _research_anthropic, "openai": _research_openai, "gemini": _research_gemini}[provider]
    out = fn(model, system, user, max_output_tokens, effort, search)
    if not out.get("error"):
        out["dossier"] = _dossier(provider, out)
    return out


def _sources_add(table, index, url, title, letter):
    """Number a cited source once (by URL); returns its marker."""
    if not url:
        return None
    if url not in index:
        index[url] = f"{letter}{len(index) + 1}"
        table.append({"marker": index[url], "url": url, "title": title})
    return index[url]


def _dossier(provider, out):
    lines = [(out.get("text_marked") or out.get("text") or "").strip(), "", "---", "",
             f"Sources cited by the {provider} search tool (markers in the text above):"]
    for s in out.get("sources_table", []):
        lines.append(f"[{s['marker']}] {s.get('title') or ''} <{s['url']}>")
    if not out.get("sources_table"):
        lines.append("(none)")
    return "\n".join(lines) + "\n"


def _norm(u):
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
    try:
        s = urlsplit(u.strip())
    except ValueError:
        return u
    if not s.scheme.startswith("http"):
        return u
    q = urlencode([(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True)
                   if not re.match(r"^(utm_|fbclid$|gclid$|mc_)", k)])
    return urlunsplit(("https", s.netloc.lower().removeprefix("www."), s.path.rstrip("/"), q, ""))


# Anthropic -------------------------------------------------------------------------------------------------------

def _research_anthropic(model, system, user, max_out, effort, search):
    tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": search.get("max_searches", 20)}]
    if search.get("max_fetches", 0):
        tools.append({"type": "web_fetch_20260209", "name": "web_fetch", "max_uses": search["max_fetches"]})
    body = {"model": model, "max_tokens": max_out, "system": system,
            "messages": [{"role": "user", "content": user}], "tools": tools}
    if effort:
        body["output_config"] = {"effort": effort}
    out = _record("anthropic", model, URLS["anthropic"], body)
    content, raws = [], []
    for _ in range(MAX_CONTINUATIONS + 1):
        req = dict(body)
        if content:                                       # pause_turn: resend the user turn + the assistant so far
            req["messages"] = [{"role": "user", "content": user}, {"role": "assistant", "content": content}]
        raw, err = _post("anthropic", URLS["anthropic"], req, out["http"])
        if err:
            out["error"] = err
            break
        raws.append(raw)
        out["response_raw"].append(raw)
        content = content + (raw.get("content") or [])
        if raw.get("stop_reason") != "pause_turn":
            break
    if not raws:
        return out
    _anthropic_finish(out, raws, content)
    if out["stop"] == "pause_turn":
        out["error"] = f"still paused after {MAX_CONTINUATIONS} continuations"
    # citations -> markers after the text block they support; every page the tools returned
    table, index, parts, queries, retrieved = [], {}, [], [], []
    for b in content:
        t = b.get("type")
        if t == "text":
            marks = []
            for c in b.get("citations") or []:
                m = _sources_add(table, index, c.get("url"), c.get("title"), "A")
                if m and m not in marks:
                    marks.append(m)
            parts.append(b.get("text", "") + ("".join(f" [{m}]" for m in marks) if marks else ""))
        elif t == "server_tool_use" and b.get("name") == "web_search":
            queries.append((b.get("input") or {}).get("query"))
        elif t == "server_tool_use" and b.get("name") == "web_fetch":
            retrieved.append({"url": (b.get("input") or {}).get("url"), "title": None, "kind": "fetch requested"})
        elif t == "web_search_tool_result":
            res = b.get("content")
            if isinstance(res, list):
                for r in res:
                    retrieved.append({"url": r.get("url"), "title": r.get("title"), "kind": "search result",
                                      "page_age": r.get("page_age")})
            else:
                retrieved.append({"url": None, "title": None, "kind": f"search error: {(res or {}).get('error_code')}"})
        elif t == "web_fetch_tool_result":
            res = b.get("content") or {}
            if res.get("type") == "web_fetch_result":
                doc = res.get("content") or {}
                retrieved.append({"url": res.get("url"), "title": doc.get("title"), "kind": "fetched page",
                                  "retrieved_at": res.get("retrieved_at")})
            else:
                retrieved.append({"url": None, "title": None, "kind": f"fetch error: {res.get('error_code')}"})
    out["text_marked"] = "".join(parts)
    out.update(queries=queries, retrieved=retrieved, sources_table=table)
    out["grounded_urls"] = sorted({_norm(x["url"]) for x in retrieved
                                   if x.get("url") and x["kind"] in ("search result", "fetched page")} |
                                  {_norm(s["url"]) for s in table})
    return out


def _anthropic_finish(out, raws, content):
    last = raws[-1]
    usage, searches, fetches = _anthropic_usage([r.get("usage") or {} for r in raws])
    stop = last.get("stop_reason")
    out.update(text="".join(b.get("text", "") for b in content if b.get("type") == "text"),
               model_reported=last.get("model"), response_id=last.get("id"), stop=stop,
               truncated=stop == "max_tokens", refused=stop == "refusal", stop_details=last.get("stop_details"),
               usage=usage, usage_raw=[r.get("usage") for r in raws], searches=searches, fetches=fetches,
               n_requests=len(raws))


# OpenAI ----------------------------------------------------------------------------------------------------------

def _research_openai(model, system, user, max_out, effort, search):
    body = {"model": model, "instructions": system, "input": [{"role": "user", "content": user}],
            "tools": [{"type": "web_search"}], "include": ["web_search_call.action.sources"],
            "max_output_tokens": max_out, "store": False}
    if search.get("max_tool_calls"):
        body["max_tool_calls"] = search["max_tool_calls"]
    if effort:
        body["reasoning"] = {"effort": effort}
    out = _record("openai", model, URLS["openai"], body)
    raw, err = _post("openai", URLS["openai"], body, out["http"])
    if err:
        out["error"] = err
        return out
    out["response_raw"].append(raw)
    _openai_finish(out, raw)
    table, index, queries, retrieved, n_search = [], {}, [], [], 0
    for item in raw.get("output", []):
        if item.get("type") == "web_search_call":
            act = item.get("action") or {}
            kind = act.get("type")
            if kind == "search":
                n_search += 1
                qs = act.get("queries") or ([act.get("query")] if act.get("query") else [])
                queries += qs
                for s in act.get("sources") or []:
                    retrieved.append({"url": s.get("url"), "title": s.get("title"), "kind": "search source"})
            elif kind in ("open_page", "find_in_page"):
                retrieved.append({"url": act.get("url"), "title": None, "kind": kind})
        elif item.get("type") == "message":
            for c in item.get("content", []):
                for an in c.get("annotations") or []:
                    if an.get("type") == "url_citation":
                        _sources_add(table, index, an.get("url"), an.get("title"), "O")
    out.update(queries=queries, retrieved=retrieved, sources_table=table, searches=n_search,
               fetches=sum(1 for x in retrieved if x["kind"] in ("open_page", "find_in_page")))
    out["text_marked"] = out["text"]                       # the text already carries the cited links inline
    out["grounded_urls"] = sorted({_norm(x["url"]) for x in retrieved if x.get("url")} |
                                  {_norm(s["url"]) for s in table})
    return out


def _openai_finish(out, raw):
    texts, refused = [], False
    for item in raw.get("output", []):
        if item.get("type") != "message":
            continue
        for c in item.get("content", []):
            if c.get("type") == "output_text":
                texts.append(c.get("text", ""))
            elif c.get("type") == "refusal":
                refused = True
    inc = (raw.get("incomplete_details") or {}).get("reason")
    status = raw.get("status")
    out.update(text="".join(texts), model_reported=raw.get("model"), response_id=raw.get("id"),
               stop=(status + (f":{inc}" if inc else "")) if status else inc,
               truncated=inc == "max_output_tokens", refused=refused,
               reasoning_effort=(raw.get("reasoning") or {}).get("effort"),
               usage=_openai_usage(raw.get("usage") or {}), usage_raw=raw.get("usage"))
    if status and status not in ("completed",) and not out.get("error") and not out["truncated"]:
        out["error"] = f"status {status}" + (f" ({inc})" if inc else "")


# Gemini ----------------------------------------------------------------------------------------------------------

_REDIRECTS = {}
_REDIRECT_LOCK = threading.Lock()


def resolve_redirect(uri):
    """Original page of a Gemini grounding link (vertexaisearch.cloud.google.com/grounding-api-redirect/...): the
    Location header of one GET without following it. No key is sent. Returns the input when it is not a redirect."""
    if not uri or "grounding-api-redirect" not in uri:
        return uri
    with _REDIRECT_LOCK:
        if uri in _REDIRECTS:
            return _REDIRECTS[uri]
    final = uri
    try:
        r = requests.get(uri, allow_redirects=False, timeout=20,
                         headers={"User-Agent": "KnowledgeLab-NobelResearch/1.0"})
        if 300 <= r.status_code < 400 and r.headers.get("Location"):
            final = r.headers["Location"]
        r.close()
    except requests.RequestException:
        pass
    with _REDIRECT_LOCK:
        _REDIRECTS[uri] = final
    time.sleep(0.2)
    return final


def _research_gemini(model, system, user, max_out, effort, search):
    tools = [{"google_search": {}}]
    if search.get("url_context", True):
        tools.append({"url_context": {}})
    gc = {"maxOutputTokens": max_out}
    if effort:
        gc["thinkingConfig"] = {"thinkingLevel": effort}
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}], "tools": tools, "generationConfig": gc}
    url = URLS["gemini"].format(model=model)
    out = _record("gemini", model, url, body)
    raw, err = _post("gemini", url, body, out["http"])
    if err:
        out["error"] = err
        return out
    out["response_raw"].append(raw)
    _gemini_finish(out, raw)
    cand = (raw.get("candidates") or [{}])[0]
    gm = cand.get("groundingMetadata") or {}
    um = cand.get("urlContextMetadata") or {}
    chunks = []
    for ch in gm.get("groundingChunks") or []:
        w = ch.get("web") or {}
        chunks.append({"uri": w.get("uri"), "title": w.get("title"), "url": resolve_redirect(w.get("uri"))})
    table, index, marks_at = [], {}, []
    text = out["text"] or ""
    for sup in gm.get("groundingSupports") or []:
        seg = sup.get("segment") or {}
        marks = []
        for i in sup.get("groundingChunkIndices") or []:
            if 0 <= i < len(chunks):
                m = _sources_add(table, index, chunks[i]["url"], chunks[i]["title"], "G")
                if m and m not in marks:
                    marks.append(m)
        pos = _segment_end(text, seg)
        if marks and pos is not None:
            marks_at.append((pos, marks))
    out["text_marked"] = _insert_marks(text, marks_at)
    retrieved = [{"url": c["url"], "title": c["title"], "kind": "grounding chunk", "redirect": c["uri"]}
                 for c in chunks]
    for m in um.get("urlMetadata") or []:
        retrieved.append({"url": m.get("retrievedUrl"), "title": None,
                          "kind": f"url context: {m.get('urlRetrievalStatus')}"})
    queries = gm.get("webSearchQueries") or []
    out.update(queries=queries, retrieved=retrieved, sources_table=table, searches=len(queries),
               fetches=len(um.get("urlMetadata") or []), search_entry_point=bool(gm.get("searchEntryPoint")))
    ok_kinds = ("grounding chunk", "url context: URL_RETRIEVAL_STATUS_SUCCESS")
    out["grounded_urls"] = sorted({_norm(x["url"]) for x in retrieved if x.get("url") and x["kind"] in ok_kinds} |
                                  {_norm(s["url"]) for s in table})
    return out


def _segment_end(text, seg):
    """Character position where a grounded segment ends. The API's endIndex is located by finding the segment text
    (byte and character offsets differ for non-ASCII text); the occurrence closest to endIndex wins."""
    s = seg.get("text")
    if not s:
        return None
    hits = [m.end() for m in re.finditer(re.escape(s), text)]
    if not hits:
        return None
    target = seg.get("endIndex") or 0
    return min(hits, key=lambda h: abs(h - target))


def _insert_marks(text, marks_at):
    merged = {}
    for pos, marks in marks_at:
        cur = merged.setdefault(pos, [])
        cur += [m for m in marks if m not in cur]
    out = text
    for pos in sorted(merged, reverse=True):
        out = out[:pos] + "".join(f" [{m}]" for m in merged[pos]) + out[pos:]
    return out


def _gemini_finish(out, raw):
    cands = raw.get("candidates") or [{}]
    c = cands[0]
    parts = (c.get("content") or {}).get("parts") or []
    stop = c.get("finishReason") or (raw.get("promptFeedback") or {}).get("blockReason")
    out.update(text="".join(p.get("text", "") for p in parts if not p.get("thought")),
               model_reported=raw.get("modelVersion"), response_id=raw.get("responseId"), stop=stop,
               truncated=stop == "MAX_TOKENS",
               refused=stop in {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION", "OTHER"},
               usage=_gemini_usage(raw.get("usageMetadata") or {}), usage_raw=raw.get("usageMetadata"))
