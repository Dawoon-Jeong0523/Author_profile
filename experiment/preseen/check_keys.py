#!/usr/bin/env python3
"""check_keys.py: are the API keys set, and does one free read-only request work with each?

    python check_keys.py              # status table + model ids of the three LLM providers
    python check_keys.py --no-models  # status table only

Prints, per API: the environment variable name, set / missing, and the HTTP status of one free read-only GET.
For Anthropic, OpenAI and Gemini it also prints the ids of the available models (ids only).
The variable names come from config.yaml `api_keys`; the Anthropic key is COMMITTEE_ANTHROPIC_API_KEY, never
ANTHROPIC_API_KEY (that one stays unset: Claude Code uses it for its own login). A key works if its GET returns 200.
It never prints, logs or writes a key value: keys are read with os.environ[...] at the moment of each request and sent
only in request headers (never in a URL), and errors are reported by exception class name only.
"""
import argparse
import os
import sys

from pathlib import Path

import requests
import yaml

TIMEOUT = 30
KEY_VARS = yaml.safe_load(Path(__file__).with_name("config.yaml").read_text())["api_keys"]


def get(url, header_fn, params=None):
    """(status, json or None) of one GET; header_fn builds the headers at call time. Errors -> ('ERR:<Class>', None)."""
    try:
        r = requests.get(url, headers=header_fn(), params=params, timeout=TIMEOUT)
    except Exception as e:                       # class name only: never the message (it could echo the request)
        return f"ERR:{type(e).__name__}", None
    try:
        body = r.json() if r.ok else None
    except ValueError:
        body = None
    return r.status_code, body


def preseen(var):
    status, _ = get("https://preseen.com/api/v1/external/forecasts/", lambda: {
        "Authorization": f"Bearer {os.environ[var]}", "Accept": "application/json"},
        params={"limit": 1, "fields": "numeric"})
    return status, None


def anthropic(var):
    ids, after, status = [], None, None
    for _ in range(20):
        params = {"limit": 1000, **({"after_id": after} if after else {})}
        status, body = get("https://api.anthropic.com/v1/models", lambda: {
            "x-api-key": os.environ[var], "anthropic-version": "2023-06-01"}, params=params)
        if body is None:
            break
        ids += [m.get("id") for m in body.get("data", [])]
        if not body.get("has_more"):
            break
        after = body.get("last_id")
    return status, (ids if status == 200 else None)


def openai(var):
    status, body = get("https://api.openai.com/v1/models", lambda: {"Authorization": f"Bearer {os.environ[var]}"})
    return status, [m.get("id") for m in (body or {}).get("data", [])] if body is not None else None


def gemini(var):
    ids, token, status = [], None, None
    for _ in range(20):
        params = {"pageSize": 1000, **({"pageToken": token} if token else {})}
        status, body = get("https://generativelanguage.googleapis.com/v1beta/models",
                           lambda: {"x-goog-api-key": os.environ[var]}, params=params)
        if body is None:
            break
        ids += [m.get("name", "").removeprefix("models/") for m in body.get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])]
        token = body.get("nextPageToken")
        if not token:
            break
    return status, (ids if status == 200 else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--no-models", action="store_true", help="do not print the model ids")
    a = ap.parse_args()

    checks = [("Preseen", KEY_VARS["preseen"], preseen), ("Anthropic", KEY_VARS["anthropic"], anthropic),
              ("OpenAI", KEY_VARS["openai"], openai), ("Gemini", KEY_VARS["gemini"], gemini)]

    print(f"{'API':<10} {'variable':<28} {'key':<8} HTTP")
    models = {}
    for api, var, fn in checks:
        is_set = var in os.environ and bool(os.environ[var].strip())
        status, ids = fn(var) if is_set else ("-", None)
        print(f"{api:<10} {var:<28} {'set' if is_set else 'missing':<8} {status}")
        if ids is not None:
            models[api] = ids

    if not a.no_models:
        for api, ids in models.items():
            print(f"\n{api} models ({len(ids)}" + (", generateContent only" if api == "Gemini" else "") + "):")
            for i in sorted(ids):
                print(f"  {i}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
