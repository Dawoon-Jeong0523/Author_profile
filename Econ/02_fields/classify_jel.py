#!/usr/bin/env python3
"""classify_jel.py: JEL codes for every prize work 1969-2025 (step 2 of the Econ forecast; see README.md). Each of the
three models of step 1 reads the prize works in batches (year, laureates with their shares, the official motivation)
and gives every work a primary JEL code and up to three secondary codes from the JEL tree in
../data/classificationTree.xml, from its own knowledge (no web search). The notebook prize_history.ipynb builds the
consensus of the three models and the field analysis.

    $PY classify_jel.py prompt [--batch 1]                   # print a prompt (free)
    $PY classify_jel.py estimate                             # cost of the run (logged usage, else assumptions)
    $PY classify_jel.py run [--providers ...] [--force]      # every batch x model (paid; valid answers are kept)
    $PY classify_jel.py export                               # jel_by_model.csv from the saved answers (free)
    $PY classify_jel.py status                               # valid / failed / spent per batch x model

A work is one motivation group of a prize year (a prize divided between two works has two), id "<year>-<group>".
Code checks every answer: the JSON schema, every work id of the batch exactly once, every code a level-3 code of the
tree, at most three secondary codes, distinct and different from the primary. An invalid answer is asked once more with
the problems listed, then recorded as invalid. A valid answer is never asked again unless --force. Every call is
logged in logs/calls.jsonl (batch, model, seconds, tokens, USD); keys are read only inside ../llm_providers.py.
"""
import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import threading
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import jsonschema
import yaml

HERE = Path(__file__).resolve().parent
ECON = HERE.parent
sys.path.insert(0, str(ECON))
import llm_providers as llm                                     # noqa: E402  (../llm_providers.py)

CFG = yaml.safe_load((ECON / "config.yaml").read_text())
SETTINGS = yaml.safe_load((HERE / "settings.yaml").read_text())
STEP = SETTINGS["jel"]
PROVIDERS = ("anthropic", "openai", "gemini")
LETTER = CFG["provider_letter"]                                 # anthropic A, openai O, gemini G
JEL_XML = ECON / "data" / "classificationTree.xml"
LAUREATES = ECON / "data" / "econ_prizes_laureates.csv"
RUNS, LOGS, PROMPTS = HERE / "runs", HERE / "logs", HERE / "prompts"
OUT = HERE / "jel_by_model.csv"
LOCK = threading.Lock()
TYPES = ["theory", "empirical", "methods", "theory_and_empirical"]

S = {"type": "string"}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["works"], "properties": {
    "works": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["id", "primary", "secondary", "contribution_type", "knows_prize", "rationale"],
        "properties": {"id": S, "primary": S, "secondary": {"type": "array", "items": S},
                       "contribution_type": {"type": "string", "enum": TYPES},
                       "knows_prize": {"type": "boolean"}, "rationale": S}}}}}


# ---------------------------------------------------------------- inputs

def jel_tree():
    """[(level, code, parent, description)] in tree order; the XML's '&bull;' separators become '•'."""
    rows = []

    def walk(node, parent):
        for c in node.findall("classification"):
            code = c.findtext("code").strip()
            rows.append((int(c.get("level")), code, parent, html.unescape(c.findtext("description").strip())))
            walk(c, code)
    walk(ET.parse(JEL_XML).getroot(), None)
    return rows


TREE = jel_tree()
CODES3 = {code for level, code, _, _ in TREE if level == 3}


def jel_list():
    return "\n".join("  " * (level - 1) + f"{code} {desc}" for level, code, _, desc in TREE)


def prize_works():
    """One entry per (year, motivation group), in award order."""
    works = {}
    with LAUREATES.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            wid = f"{r['year']}-{r['group']}"
            w = works.setdefault(wid, {"id": wid, "year": int(r["year"]), "group": int(r["group"]),
                                       "n_groups": int(r["n_groups"]), "motivation": r["motivation"],
                                       "top_motivation": r["top_motivation"], "laureates": []})
            w["laureates"].append(f"{r['laureate']} ({r['portion']})")
    return sorted(works.values(), key=lambda w: (w["year"], w["group"]))


WORKS = prize_works()


def batches():
    """Consecutive years, about batch_size works each; the works of one year always share a batch."""
    out, cur = [], []
    for i, w in enumerate(WORKS):
        cur.append(w)
        year_done = i + 1 == len(WORKS) or WORKS[i + 1]["year"] != w["year"]
        if year_done and len(cur) >= STEP["batch_size"]:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- helpers

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def fill(template, **kw):
    """Replace {{key}} placeholders (no str.format, so braces in the prompts are safe)."""
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(kw[m.group(1)]), template)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def model_of(provider):
    return CFG["models"][provider]


def usd(provider, usage):
    p = CFG["pricing"][model_of(provider)]
    u = usage or {}
    return round(((u.get("input") or 0) * p["input"] + (u.get("output") or 0) * p["output"]) / 1e6, 4)


def log_call(batch, provider, rec):
    row = {"time": now(), "stage": "jel", "batch": batch, "provider": provider, "model": model_of(provider),
           "model_reported": rec.get("model_reported"), "ok": not rec.get("error"), "stop": rec.get("stop"),
           "seconds": round(sum(h.get("seconds") or 0 for h in rec.get("http", [])), 1),
           "usage": rec.get("usage"), "usd": usd(provider, rec.get("usage")), "error": rec.get("error")}
    with LOCK:
        LOGS.mkdir(exist_ok=True)
        with (LOGS / "calls.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def say(*parts):
    with LOCK:
        print(*parts, flush=True)


def norm_code(c):
    """'d82', 'D82 Asymmetric ...' -> 'D82'; anything else is returned stripped (and fails the check)."""
    c = (c or "").strip().upper()
    m = re.match(r"^([A-Z]\d\d)\b", c)
    return m.group(1) if m else c


# ---------------------------------------------------------------- prompt, checks, one call

def work_block(w):
    lines = [f"- id {w['id']} | {w['year']} | " + "; ".join(w["laureates"]),
             f"  motivation: {w['motivation']}"]
    if w["n_groups"] > 1:
        others = ", ".join(x["id"] for x in WORKS if x["year"] == w["year"] and x["id"] != w["id"])
        lines.append(f"  (the {w['year']} prize was divided between {w['n_groups']} works; the other: {others})")
        if w["top_motivation"]:
            lines.append(f"  overall motivation of the year: {w['top_motivation']}")
    return "\n".join(lines)


def prompt(k):
    b = batches()[k - 1]
    system = fill((PROMPTS / "jel_system.md").read_text(encoding="utf-8").strip(),
                  max_secondary=STEP["max_secondary"], jel_list=jel_list())
    user = fill((PROMPTS / "jel_user.md").read_text(encoding="utf-8").strip(), first_year=b[0]["year"],
                last_year=b[-1]["year"], n=len(b), works="\n\n".join(work_block(w) for w in b))
    return system, user


def check(parsed, k):
    """Problems with an answer (empty = valid); normalises the codes in place."""
    errs = [f"{'/'.join(map(str, e.path)) or '(top)'}: {e.message[:200]}"
            for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(parsed)][:10]
    if errs:
        return errs
    want = [w["id"] for w in batches()[k - 1]]
    got = [w["id"].strip() for w in parsed["works"]]
    if missing := [i for i in want if i not in got]:
        errs.append(f"work ids missing: {missing}")
    if extra := sorted({i for i in got if i not in want}):
        errs.append(f"work ids not in this batch: {extra}")
    if dup := sorted({i for i in got if got.count(i) > 1}):
        errs.append(f"work ids given more than once: {dup}")
    for w in parsed["works"]:
        w["id"] = w["id"].strip()
        w["primary"] = norm_code(w["primary"])
        w["secondary"] = [norm_code(x) for x in w["secondary"]]
        if w["primary"] not in CODES3:
            errs.append(f"{w['id']}: primary {w['primary']!r} is not a level-3 code of the list")
        if bad := [x for x in w["secondary"] if x not in CODES3]:
            errs.append(f"{w['id']}: secondary {bad} not level-3 codes of the list")
        if len(w["secondary"]) > STEP["max_secondary"]:
            errs.append(f"{w['id']}: more than {STEP['max_secondary']} secondary codes")
        if w["primary"] in w["secondary"] or len(set(w["secondary"])) < len(w["secondary"]):
            errs.append(f"{w['id']}: secondary codes repeat the primary or each other")
    return errs


def run_path(provider, k):
    return RUNS / provider / f"batch_{k}.json"


def valid(rec):
    return bool(rec) and rec.get("valid") is True


def run_batch(k, provider, force=False):
    path = run_path(provider, k)
    old = read_json(path)
    if valid(old) and not force:
        return old, "exists"
    system, user = prompt(k)
    attempts, errs, parsed, ask = [], ["not asked"], None, user
    for _ in range(1 + STEP["json_retries"]):
        res = llm.call_json(provider, model_of(provider), system, ask, SCHEMA,
                            max_output_tokens=STEP["max_output_tokens"], effort=STEP["effort"].get(provider))
        log_call(k, provider, res)
        if res.get("error"):
            errs, parsed = [f"HTTP: {res['error']}"], None
            attempts.append(dict(res, errors=errs))
            break                                           # HTTP failures were already retried inside call_json
        parsed = res.get("parsed")
        errs = check(parsed, k) if parsed is not None else [res.get("parse_error") or "no JSON text"]
        if res.get("truncated"):
            errs.append(f"truncated (stop={res.get('stop')})")
        if res.get("refused"):
            errs.append(f"refused (stop={res.get('stop')})")
        attempts.append(dict(res, errors=errs))
        if not errs:
            break
        ask = (user + "\n\nAn earlier answer to this request was rejected for these problems: " + "; ".join(errs)
               + ". Use only level-3 codes from the list and return every work id exactly once.")
    rec = {"stage": "jel", "batch": k, "provider": provider, "model": model_of(provider), "written": now(),
           "work_ids": [w["id"] for w in batches()[k - 1]], "prompt": {"system": system, "user": user},
           "schema": SCHEMA, "settings": {x: STEP[x] for x in ("batch_size", "max_output_tokens", "json_retries",
                                                                 "max_secondary")}
           | {"effort": STEP["effort"].get(provider)},
           "attempts": attempts, "valid": not errs, "errors": errs,
           "model_reported": attempts[-1].get("model_reported") if attempts else None,
           "answer": parsed if not errs else None}
    if errs and valid(old):                     # --force failed: keep the valid answer, file the failure beside it
        write_json(path.with_name(f"batch_{k}.failed.json"), rec)
        return old, f"new call INVALID ({errs[:1]}); kept the earlier valid answer"
    write_json(path, rec)
    return rec, ("valid" if not errs else f"INVALID: {errs[:2]}")


# ---------------------------------------------------------------- commands

def calls_log():
    if not (LOGS / "calls.jsonl").exists():
        return []
    return [json.loads(x) for x in (LOGS / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def cmd_prompt(a):
    system, user = prompt(a.batch)
    print(f"## system ({len(system):,} characters)\n{system}\n\n## user\n{user}")


def cmd_estimate(a):
    calls, total, n = calls_log(), 0.0, len(batches())
    print(f"{'model':<24} {'calls':>5} {'USD/call':>9} {'USD':>7}  basis")
    for p in PROVIDERS:
        seen = [c["usd"] for c in calls if c["provider"] == p and c["ok"]]
        if seen:
            per, basis = sum(seen) / len(seen), f"mean of {len(seen)} logged calls"
        else:
            ass = SETTINGS["estimate_assumptions"]["jel"]
            per, basis = usd(p, ass), f"assumption {ass}"
        total += per * n
        print(f"{model_of(p):<24} {n:>5} {per:>9.3f} {per * n:>7.2f}  {basis}")
    print(f"{'total (' + str(len(WORKS)) + ' works in ' + str(n) + ' batches, one attempt per call)':<40} {total:>7.2f}")


def cmd_run(a):
    if missing := [p for p in a.providers if not llm.key_is_set(p)]:
        sys.exit("missing API key environment variable(s): " + ", ".join(CFG["api_keys"][p] for p in missing))
    pools = {p: ThreadPoolExecutor(a.workers) for p in a.providers}
    futs = {(k, p): pools[p].submit(run_batch, k, p, a.force)
            for k in range(1, len(batches()) + 1) for p in a.providers}
    for (k, p), f in futs.items():
        try:
            rec, how = f.result()
            say(f"batch {k} {p:<9} [{how}]")
        except Exception as e:                                   # a crashed cell writes nothing; a re-run retries it
            say(f"batch {k} {p:<9} CRASHED: {type(e).__name__}: {str(e)[:200]}")
    for pool in pools.values():
        pool.shutdown()
    cmd_export(a)
    cmd_status(a)


def cmd_export(a=None):
    """jel_by_model.csv: one row per work x model with a valid answer."""
    meta = {w["id"]: w for w in WORKS}
    rows = []
    for p in PROVIDERS:
        for k in range(1, len(batches()) + 1):
            rec = read_json(run_path(p, k))
            if not valid(rec):
                continue
            for w in rec["answer"]["works"]:
                rows.append({"work_id": w["id"], "year": meta[w["id"]]["year"], "group": meta[w["id"]]["group"],
                             "provider": p, "letter": LETTER[p], "model": rec["model"], "primary": w["primary"],
                             "secondary": ";".join(w["secondary"]), "contribution_type": w["contribution_type"],
                             "knows_prize": w["knows_prize"], "rationale": w["rationale"], "written": rec["written"]})
    rows.sort(key=lambda r: (r["year"], r["group"], "AOG".index(r["letter"])))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["work_id"])
        wr.writeheader()
        wr.writerows(rows)
    print(f"{OUT.name}: {len(rows)} rows ({len({r['work_id'] for r in rows})} of {len(WORKS)} works)")


def cmd_status(a=None):
    calls = calls_log()
    spent = defaultdict(float)
    for c in calls:
        spent[(c["batch"], c["provider"])] += c.get("usd") or 0
    print(f"\n{'batch':<22} " + " ".join(f"{p:<16}" for p in PROVIDERS))
    for k, b in enumerate(batches(), 1):
        cells = []
        for p in PROVIDERS:
            r = read_json(run_path(p, k))
            s = "-" if r is None else ("ok" if valid(r) else "FAILED")
            cells.append(f"{s} ${spent[(k, p)]:.2f}")
        print(f"{k} ({b[0]['id']}..{b[-1]['id']})".ljust(22) + " " + " ".join(f"{c:<16}" for c in cells))
    print(f"spent so far ${sum(c.get('usd') or 0 for c in calls):.2f} over {len(calls)} calls (logs/calls.jsonl)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("prompt")
    s.add_argument("--batch", type=int, default=1, choices=range(1, len(batches()) + 1))
    sub.add_parser("estimate")
    s = sub.add_parser("run")
    s.add_argument("--providers", nargs="+", default=list(PROVIDERS), choices=PROVIDERS)
    s.add_argument("--workers", type=int, default=2, help="concurrent calls per provider")
    s.add_argument("--force", action="store_true", help="ask again even when a valid answer exists (paid)")
    sub.add_parser("export")
    sub.add_parser("status")
    a = ap.parse_args()
    {"prompt": cmd_prompt, "estimate": cmd_estimate, "run": cmd_run, "export": cmd_export,
     "status": cmd_status}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
