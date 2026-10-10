#!/usr/bin/env python3
"""profiles.py: profiles of the 2026 economics prize committee members. Each of three LLMs describes every member from
its own knowledge (no web search); Claude merges the three answers into one profile per member (step 1 of the Econ
forecast; see README.md).

    $PY profiles.py roster                                   # the members (roster.yaml)
    $PY profiles.py prompt --member john-hassler [--stage ask|merge]   # print a prompt (free)
    $PY profiles.py estimate                                 # cost of the full run (logged usage, else assumptions)
    $PY profiles.py test --member john-hassler               # one member: three answers + merge (paid)
    $PY profiles.py run [--members ...] [--providers ...] [--stages ask merge] [--workers 3]   (paid)
    $PY profiles.py merge [--members ...] [--force]          # merge again from the saved answers (paid)
    $PY profiles.py render                                   # profiles/<slug>.md, ALL.md, index.csv (free)
    $PY profiles.py status                                   # done / failed / spent per member x model

Per member:
  1. ask (one call per model; no tools; JSON schema; prompts/ask_*.md): the member's name, affiliation, committee
     role and title go to claude-opus-5-5, gpt-5.5-2026-04-23 and gemini-3.1-pro-preview, which return an identity
     check, fields, recent interests, representative works, a persona and the limits of their knowledge
     -> runs/<provider>/<slug>.json
  2. merge (one call; claude-opus-5-5 unless --merger; JSON schema; prompts/merge_*.md): the three answers, labelled
     A / O / G, become one profile in which every field, interest and work lists the models that state it. Code
     checks the merge: support letters must belong to answers that exist, and every merged work is matched by title
     against the works of the three answers (support recomputed, a work found in no answer is flagged)
     -> profiles/<slug>.json, profiles/<slug>.md

An existing valid record is never asked again unless --force; a failed or invalid one is. Every call is logged in
logs/calls.jsonl (stage, member, model, seconds, tokens, USD). Keys: environment variables named in ../config.yaml,
read only inside ../llm_providers.py at request time.
"""
import argparse
import csv
import datetime as dt
import difflib
import json
import re
import sys
import threading
import unicodedata
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
STEP = yaml.safe_load((HERE / "settings.yaml").read_text())
ROSTER = yaml.safe_load((HERE / "roster.yaml").read_text())
MEMBERS = {m["slug"]: m for m in ROSTER["members"]}
PROVIDERS = ("anthropic", "openai", "gemini")
LETTER = CFG["provider_letter"]                                 # anthropic A, openai O, gemini G
BY_LETTER = {v: k for k, v in LETTER.items()}
RUNS, PROFILES, LOGS, PROMPTS = HERE / "runs", HERE / "profiles", HERE / "logs", HERE / "prompts"
LOCK = threading.Lock()

# ---------------------------------------------------------------- JSON schemas (strings, booleans, enums and arrays
# only, no nulls: the subset the three providers' JSON modes share; "" = not known)

S = {"type": "string"}
SA = {"type": "array", "items": S}
CONF = {"type": "string", "enum": ["high", "medium", "low"]}


def obj(props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


PERSONA = {"summary": S, "research_lens": S, "methods_and_evidence": S, "what_they_value_in_contributions": S,
           "likely_questions_in_deliberation": SA, "committee_experience": S}
ASK_SCHEMA = obj({
    "identity": obj({"recognized": {"type": "boolean"}, "confidence": CONF, "note": S}),
    "fields": {"type": "array", "items": obj({"field": S, "jel_codes": SA, "confidence": CONF})},
    "recent_interests": {"type": "array", "items": obj({"topic": S, "period": S, "basis": S, "confidence": CONF})},
    "representative_works": {"type": "array", "items": obj({"title": S, "year": S, "venue": S, "coauthors": SA,
                                                             "contribution": S, "confidence": CONF})},
    "persona": obj(PERSONA),
    "knowledge_limits": S})
MERGE_SCHEMA = obj({
    "identity": obj({"name": S, "affiliation": S, "recognized_by": SA, "note": S}),
    "fields": {"type": "array", "items": obj({"field": S, "jel_codes": SA, "support": SA, "note": S})},
    "recent_interests": {"type": "array", "items": obj({"topic": S, "period": S, "support": SA, "note": S})},
    "representative_works": {"type": "array", "items": obj({"title": S, "year": S, "venue": S, "coauthors": SA,
                                                             "contribution": S, "support": SA, "conflict": S})},
    "persona": obj(dict(PERSONA, support_note=S)),
    "disagreements": SA,
    "caveats": SA})


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


def log_call(stage, slug, provider, rec):
    row = {"time": now(), "stage": stage, "member": slug, "provider": provider, "model": model_of(provider),
           "model_reported": rec.get("model_reported"), "ok": not rec.get("error"), "stop": rec.get("stop"),
           "seconds": round(sum(h.get("seconds") or 0 for h in rec.get("http", [])), 1),
           "usage": rec.get("usage"), "usd": usd(provider, rec.get("usage")), "error": rec.get("error")}
    with LOCK:
        LOGS.mkdir(exist_ok=True)
        with (LOGS / "calls.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def say(*parts):
    with LOCK:
        print(*parts, flush=True)


def long_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def same_title(a, b):
    a, b = norm_title(a), norm_title(b)
    if not a or not b:
        return False
    if a == b or (min(len(a), len(b)) >= 20 and (a in b or b in a)):
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= STEP["title_match"]


def ask_with_retries(stage, slug, provider, system, user, schema, cfg, validate):
    """One call in JSON mode plus cfg['json_retries'] retries on invalid output; returns (attempts, errors, parsed)."""
    attempts, errs, parsed = [], ["not asked"], None
    for _ in range(1 + cfg["json_retries"]):
        res = llm.call_json(provider, model_of(provider), system, user, schema,
                            max_output_tokens=cfg["max_output_tokens"], effort=cfg["effort"].get(provider))
        log_call(stage, slug, provider, res)
        if res.get("error"):
            errs, parsed = [f"HTTP: {res['error']}"], None
            attempts.append(dict(res, errors=errs))
            break                                           # HTTP failures were already retried inside call_json
        parsed = res.get("parsed")
        errs = validate(parsed) if parsed is not None else [res.get("parse_error") or "no JSON text"]
        if res.get("truncated"):
            errs.append(f"truncated (stop={res.get('stop')})")
        if res.get("refused"):
            errs.append(f"refused (stop={res.get('stop')})")
        attempts.append(dict(res, errors=errs))
        if not errs:
            break
    return attempts, errs, parsed


def schema_errors(schema, obj_):
    v = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.path)) or '(top)'}: {e.message[:200]}" for e in v.iter_errors(obj_)][:10]


# ---------------------------------------------------------------- stage 1: ask

def ask_prompt(slug):
    m = MEMBERS[slug]
    system = (PROMPTS / "ask_system.md").read_text(encoding="utf-8").strip()
    user = fill((PROMPTS / "ask_user.md").read_text(encoding="utf-8").strip(),
                today_long=long_date(CFG["today"]),
                announcement_long=long_date(CFG["announcement"]) + ", 11:45 CEST at the earliest",
                name=m["name"], affiliation=m["affiliation"], role=m["role"], title=m["title"],
                max_works=STEP["ask"]["max_works"])
    return system, user


def validate_ask(a):
    errs = schema_errors(ASK_SCHEMA, a)
    if not errs and not a["persona"]["summary"].strip():
        errs.append("empty persona summary")
    return errs


def ask_path(provider, slug):
    return RUNS / provider / f"{slug}.json"


def ask_ok(rec):
    return bool(rec) and rec.get("valid") is True


def run_ask(slug, provider, force=False):
    path = ask_path(provider, slug)
    old = read_json(path)
    if ask_ok(old) and not force:
        return old, "exists"
    system, user = ask_prompt(slug)
    attempts, errs, parsed = ask_with_retries("ask", slug, provider, system, user, ASK_SCHEMA, STEP["ask"],
                                              validate_ask)
    rec = {"stage": "ask", "member": slug, "provider": provider, "model": model_of(provider), "written": now(),
           "prompt": {"system": system, "user": user}, "schema": ASK_SCHEMA,
           "settings": {k: STEP["ask"][k] for k in ("max_output_tokens", "json_retries", "max_works")}
           | {"effort": STEP["ask"]["effort"].get(provider)},
           "attempts": attempts, "valid": not errs, "errors": errs,
           "model_reported": attempts[-1].get("model_reported") if attempts else None,
           "answer": parsed if not errs else None}
    if errs and ask_ok(old):                    # --force failed: keep the valid answer, file the failure beside it
        write_json(path.with_name(f"{slug}.failed.json"), rec)
        return old, f"new call INVALID ({errs[:1]}); kept the earlier valid answer"
    write_json(path, rec)
    return rec, ("valid" if not errs else f"INVALID: {errs[:2]}")


# ---------------------------------------------------------------- stage 2: merge

def merge_inputs(slug):
    return {p: r for p in PROVIDERS if ask_ok(r := read_json(ask_path(p, slug)))}


def merge_prompt(slug, answers):
    m = MEMBERS[slug]
    blocks = []
    for p, r in answers.items():
        blocks.append(f"Profile {LETTER[p]}:\n" + json.dumps(r["answer"], ensure_ascii=False, indent=1))
    missing = [LETTER[p] for p in PROVIDERS if p not in answers]
    if missing:
        blocks.append(f"(No valid profile from {', '.join(missing)}: do not use those letters.)")
    system = (PROMPTS / "merge_system.md").read_text(encoding="utf-8").strip()
    user = fill((PROMPTS / "merge_user.md").read_text(encoding="utf-8").strip(), name=m["name"],
                affiliation=m["affiliation"], role=m["role"], title=m["title"], profiles="\n\n".join(blocks))
    return system, user


def validate_merge(out, letters):
    errs = schema_errors(MERGE_SCHEMA, out)
    if errs:
        return errs
    bad = set()
    for sec in ("fields", "recent_interests", "representative_works"):
        for it in out[sec]:
            bad |= {x for x in it["support"] if x not in letters}
            if not it["support"]:
                errs.append(f"{sec}: an entry without support")
    bad |= {x for x in out["identity"]["recognized_by"] if x not in letters}
    if bad:
        errs.append(f"support letters without a valid input profile: {sorted(bad)}")
    if not out["persona"]["summary"].strip():
        errs.append("empty persona summary")
    return errs


def check_works(out, answers):
    """Match every merged work by title against the works of the input answers: recompute the support, flag works that
    appear in no answer (added by the merge)."""
    rows = []
    for w in out["representative_works"]:
        found = [LETTER[p] for p, r in answers.items()
                 if any(same_title(w["title"], x["title"]) for x in r["answer"]["representative_works"])]
        rows.append(dict(w, support_checked=sorted(found, key="AOG".index), in_inputs=bool(found),
                         support_matches=sorted(found) == sorted(w["support"])))
    return rows


def input_stamps(answers):
    return {LETTER[p]: r["written"] for p, r in answers.items()}


def run_merge(slug, merger=None, force=False):
    path = PROFILES / f"{slug}.json"
    old = read_json(path)
    answers = merge_inputs(slug)
    if not answers:
        return None, "no valid answer"
    current = old and old.get("valid") and {k: v["written"] for k, v in old["inputs"].items()} == input_stamps(answers)
    if current and not force:
        return old, "exists"
    provider = merger or STEP["merge"]["provider"]
    system, user = merge_prompt(slug, answers)
    letters = {LETTER[p] for p in answers}
    attempts, errs, out = ask_with_retries("merge", slug, provider, system, user, MERGE_SCHEMA, STEP["merge"],
                                           lambda o: validate_merge(o, letters))
    m = MEMBERS[slug]
    rec = {"stage": "merge", "member": slug, "name": m["name"], "role": m["role"], "title": m["title"],
           "affiliation": m["affiliation"], "merger": model_of(provider), "written": now(),
           "inputs": {LETTER[p]: {"model": model_of(p), "written": r["written"],
                                  "recognized": r["answer"]["identity"]["recognized"],
                                  "confidence": r["answer"]["identity"]["confidence"]} for p, r in answers.items()},
           "missing_inputs": [p for p in PROVIDERS if p not in answers],
           "prompt": {"system": system, "user_chars": len(user)}, "attempts": attempts,
           "valid": not errs, "errors": errs}
    if not errs:
        works = check_works(out, answers)
        rec["profile"] = dict(out, representative_works=works)
        rec["per_model"] = {LETTER[p]: {"persona_summary": r["answer"]["persona"]["summary"],
                                        "identity_note": r["answer"]["identity"]["note"],
                                        "knowledge_limits": r["answer"]["knowledge_limits"]}
                            for p, r in answers.items()}
        rec["stats"] = {"fields": len(out["fields"]), "interests": len(out["recent_interests"]),
                        "works": len(works), "works_all_models": sum(len(w["support_checked"]) == 3 for w in works),
                        "works_one_model": sum(len(w["support_checked"]) == 1 for w in works),
                        "works_not_in_inputs": sum(not w["in_inputs"] for w in works),
                        "works_support_differs": sum(w["in_inputs"] and not w["support_matches"] for w in works),
                        "disagreements": len(out["disagreements"]), "caveats": len(out["caveats"])}
    write_json(path, rec)
    if not errs:
        render_member(rec)
    return rec, ("valid" if not errs else f"INVALID: {errs[:2]}")


# ---------------------------------------------------------------- rendering

def badge(support):
    return "[" + " ".join(x if x in support else "·" for x in "AOG") + "]"


def render_member(rec):
    p = rec["profile"]
    per = p["persona"]
    rec_line = " · ".join(f"{k}: {'recognized' if v['recognized'] else 'NOT recognized'} ({v['confidence']})"
                          for k, v in rec["inputs"].items())
    lines = [f"# {rec['name']}", "",
             f"**{rec['role'].capitalize()}**, {ROSTER['committee']} {ROSTER['year']} · {rec['title']} · "
             f"{rec['affiliation']}", "",
             "Profiles written from their own knowledge (no web search) by "
             + ", ".join(f"{LETTER[q]} = {model_of(q)}" for q in PROVIDERS)
             + f"; merged by {rec['merger']} on {rec['written'][:10]}. `[A O G]` = the models that state an item "
             "(for works: checked by title against each model's own list); ⚠ = a work no model listed.", "",
             f"Recognition: {rec_line}"]
    if rec["missing_inputs"]:
        lines.append(f"Missing answers: {', '.join(rec['missing_inputs'])}")
    lines += ["", "## Persona", "", per["summary"], "",
              f"- **Research lens:** {per['research_lens']}",
              f"- **Methods and evidence:** {per['methods_and_evidence']}",
              f"- **What they value in contributions:** {per['what_they_value_in_contributions']}",
              f"- **Committee experience:** {per['committee_experience'] or '–'}",
              "- **Questions they would raise:**"]
    lines += [f"  - {q}" for q in per["likely_questions_in_deliberation"]] or ["  - –"]
    if per["support_note"]:
        lines.append(f"- **Where the models differ:** {per['support_note']}")
    lines += ["", "## Fields", ""]
    for f in p["fields"]:
        jel = f" ({', '.join(f['jel_codes'])})" if f["jel_codes"] else ""
        note = f" — {f['note']}" if f["note"] else ""
        lines.append(f"- `{badge(f['support'])}` {f['field']}{jel}{note}")
    lines += ["", "## Recent interests", ""]
    for r in p["recent_interests"]:
        per_ = f" ({r['period']})" if r["period"] else ""
        note = f" — {r['note']}" if r["note"] else ""
        lines.append(f"- `{badge(r['support'])}` {r['topic']}{per_}{note}")
    lines += ["", "## Representative works", ""]
    for w in p["representative_works"]:
        sup = w["support_checked"] if w["in_inputs"] else w["support"]
        meta = ", ".join(x for x in (w["year"], w["venue"]) if x)
        co = f"; with {', '.join(w['coauthors'])}" if w["coauthors"] else ""
        flag = "" if w["in_inputs"] else " ⚠ *not in any model's list*"
        if w["in_inputs"] and not w["support_matches"]:
            flag = f" *(merge said {''.join(w['support'])})*"
        conflict = f"\n  - conflict: {w['conflict']}" if w["conflict"] else ""
        lines.append(f"- `{badge(sup)}` *{w['title']}*" + (f" ({meta})" if meta else "") + co
                     + (f" — {w['contribution']}" if w["contribution"] else "") + flag + conflict)
    if p["disagreements"]:
        lines += ["", "## Disagreements between the models", ""] + [f"- {d}" for d in p["disagreements"]]
    if p["caveats"]:
        lines += ["", "## Caveats", ""] + [f"- {c}" for c in p["caveats"]]
    lines += ["", "## Each model's own persona summary and knowledge limits", ""]
    for k, v in rec["per_model"].items():
        lines += [f"**{k} ({model_of(BY_LETTER[k])})** — {v['persona_summary']}",
                  f"*Identity:* {v['identity_note'] or '–'} *Limits:* {v['knowledge_limits'] or '–'}", ""]
    PROFILES.mkdir(exist_ok=True)
    (PROFILES / f"{rec['member']}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_render(a=None):
    rows = []
    parts = [f"# {ROSTER['committee']} {ROSTER['year']}: member profiles", "",
             "Each profile merges three answers written from the models' own knowledge (no web search): A = "
             f"{model_of('anthropic')}, O = {model_of('openai')}, G = {model_of('gemini')}. Full profiles: "
             "`<slug>.md` in this folder.", ""]
    for slug, m in MEMBERS.items():
        rec = read_json(PROFILES / f"{slug}.json")
        if not rec or not rec.get("valid"):
            rows.append({"slug": slug, "name": m["name"], "role": m["role"], "affiliation": m["affiliation"],
                         "status": "missing"})
            parts += [f"## {m['name']} ({m['role']})", "", "*Not merged yet.*", ""]
            continue
        render_member(rec)
        p, st = rec["profile"], rec["stats"]
        rows.append({"slug": slug, "name": m["name"], "role": m["role"], "affiliation": m["affiliation"],
                     "status": "merged", **{f"recognized_{k}": v["recognized"] for k, v in rec["inputs"].items()},
                     **st, "merger": rec["merger"], "written": rec["written"]})
        parts += [f"## {m['name']} ({m['role']})", "", f"{m['affiliation']} · [full profile]({slug}.md)", "",
                  p["persona"]["summary"], "",
                  "Fields: " + "; ".join(f"{f['field']} {badge(f['support'])}" for f in p["fields"]), "",
                  "Works: " + "; ".join(f"{w['title']} ({w['year']}) {badge(w['support_checked'] or w['support'])}"
                                        for w in p["representative_works"][:5]), ""]
    PROFILES.mkdir(exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with (PROFILES / "index.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    (PROFILES / "ALL.md").write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"profiles/index.csv, profiles/ALL.md: {sum(r['status'] == 'merged' for r in rows)} of {len(rows)} merged")


# ---------------------------------------------------------------- commands

def need_keys(providers):
    missing = [p for p in providers if not llm.key_is_set(p)]
    if missing:
        sys.exit("missing API key environment variable(s): " + ", ".join(CFG["api_keys"][p] for p in missing))


def pick_members(names):
    if not names or names == ["all"]:
        return list(MEMBERS)
    bad = [n for n in names if n not in MEMBERS]
    if bad:
        sys.exit(f"unknown member slug(s): {bad}; see `profiles.py roster`")
    return names


def cmd_roster(a):
    for slug, m in MEMBERS.items():
        print(f"{slug:<24} {m['role']:<16} {m['name']:<24} {m['affiliation']}")


def cmd_prompt(a):
    if a.stage == "ask":
        system, user = ask_prompt(a.member)
    else:
        answers = merge_inputs(a.member)
        if not answers:
            sys.exit(f"no valid answer for {a.member} yet")
        system, user = merge_prompt(a.member, answers)
    print(f"## system\n{system}\n\n## user\n{user}")


def cmd_run(a, members=None):
    members = members or pick_members(a.members)
    if "ask" in a.stages:
        need_keys(a.providers)
    if "merge" in a.stages:
        need_keys([a.merger or STEP["merge"]["provider"]])
    pools = {p: ThreadPoolExecutor(a.workers) for p in a.providers}
    futs = {}
    if "ask" in a.stages:
        for s in members:
            for p in a.providers:
                futs[(s, p)] = pools[p].submit(run_ask, s, p, a.force)
    for (s, p), f in futs.items():
        try:
            rec, how = f.result()
            n = len(rec["answer"]["representative_works"]) if rec.get("valid") else 0
            rcg = rec["answer"]["identity"] if rec.get("valid") else {}
            say(f"{s:<24} {p:<9} ask   [{how}]" + (f" recognized={rcg.get('recognized')} ({rcg.get('confidence')}) "
                                                   f"works={n}" if rec.get("valid") else ""))
        except Exception as e:                                   # a crashed cell writes nothing; a re-run retries it
            say(f"{s:<24} {p:<9} ask   CRASHED: {type(e).__name__}: {str(e)[:200]}")
    for pool in pools.values():
        pool.shutdown()
    if "merge" in a.stages:
        with ThreadPoolExecutor(a.workers) as ex:
            mf = {s: ex.submit(run_merge, s, a.merger, a.force) for s in members}
            for s, f in mf.items():
                try:
                    rec, how = f.result()
                    say(f"{s:<24} merged      [{how}]" + (f" {rec['stats']}" if rec and rec.get("valid") else ""))
                except Exception as e:
                    say(f"{s:<24} merged      CRASHED: {type(e).__name__}: {str(e)[:200]}")
    cmd_render()
    cmd_status(a)


def cmd_test(a):
    a.stages = ["ask", "merge"]
    cmd_run(a, members=[a.member])


def cmd_merge(a):
    members = pick_members(a.members)
    need_keys([a.merger or STEP["merge"]["provider"]])
    for s in members:
        rec, how = run_merge(s, a.merger, a.force)
        say(f"{s:<24} merged [{how}]" + (f" {rec['stats']}" if rec and rec.get("valid") else ""))
    cmd_render()


def calls_log():
    if not (LOGS / "calls.jsonl").exists():
        return []
    return [json.loads(x) for x in (LOGS / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def cmd_status(a):
    calls = calls_log()
    spent = defaultdict(float)
    for c in calls:
        spent[(c["member"], c["provider"])] += c.get("usd") or 0
    print(f"\n{'member':<24} " + " ".join(f"{p:<16}" for p in PROVIDERS) + " merged")
    for slug in MEMBERS:
        cells = []
        for p in PROVIDERS:
            r = read_json(ask_path(p, slug))
            s = "-" if r is None else ("ok" if ask_ok(r) else "FAILED")
            cells.append(f"{s} ${spent[(slug, p)]:.2f}")
        g = read_json(PROFILES / f"{slug}.json")
        gs = "-" if g is None else ("ok" if g.get("valid") else "INVALID")
        print(f"{slug:<24} " + " ".join(f"{c:<16}" for c in cells) + f" {gs}")
    print(f"spent so far ${sum(c.get('usd') or 0 for c in calls):.2f} over {len(calls)} calls (logs/calls.jsonl)")


def cmd_estimate(a):
    """Full-run cost: the mean logged cost of successful calls per stage and model; else the settings assumptions."""
    calls = calls_log()
    n, total = len(MEMBERS), 0.0
    print(f"{'stage':<7} {'model':<24} {'calls':>5} {'USD/call':>9} {'USD':>7}  basis")
    for stage, provs in (("ask", PROVIDERS), ("merge", (STEP["merge"]["provider"],))):
        for p in provs:
            seen = [c["usd"] for c in calls if c["stage"] == stage and c["provider"] == p and c["ok"]]
            if seen:
                per, basis = sum(seen) / len(seen), f"mean of {len(seen)} logged calls"
            else:
                ass = STEP["estimate_assumptions"][stage]
                per, basis = usd(p, ass), f"assumption {ass}"
            total += per * n
            print(f"{stage:<7} {model_of(p):<24} {n:>5} {per:>9.3f} {per * n:>7.2f}  {basis}")
    print(f"{'total for ' + str(n) + ' members (one attempt per call)':<48} {total:>7.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster")
    s = sub.add_parser("prompt"); s.add_argument("--member", required=True, choices=list(MEMBERS))
    s.add_argument("--stage", default="ask", choices=["ask", "merge"])
    sub.add_parser("estimate")
    for name in ("test", "run"):
        s = sub.add_parser(name)
        if name == "test":
            s.add_argument("--member", required=True, choices=list(MEMBERS))
        else:
            s.add_argument("--members", nargs="+", default=["all"])
            s.add_argument("--stages", nargs="+", default=["ask", "merge"], choices=["ask", "merge"])
        s.add_argument("--providers", nargs="+", default=list(PROVIDERS), choices=PROVIDERS)
        s.add_argument("--workers", type=int, default=3, help="concurrent calls per provider")
        s.add_argument("--merger", choices=PROVIDERS, default=None)
        s.add_argument("--force", action="store_true", help="ask again even when a valid record exists (paid)")
    s = sub.add_parser("merge"); s.add_argument("--members", nargs="+", default=["all"])
    s.add_argument("--merger", choices=PROVIDERS, default=None); s.add_argument("--force", action="store_true")
    sub.add_parser("render")
    sub.add_parser("status")
    a = ap.parse_args()
    {"roster": cmd_roster, "prompt": cmd_prompt, "estimate": cmd_estimate, "test": cmd_test, "run": cmd_run,
     "merge": cmd_merge, "render": cmd_render, "status": cmd_status}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
