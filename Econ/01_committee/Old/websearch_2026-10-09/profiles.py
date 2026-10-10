#!/usr/bin/env python3
"""profiles.py: professional profiles of the 2026 economics prize committee, researched independently by three LLMs
with web search and merged into one profile per member (step 1 of the Econ forecast; see ../README.md).

    $PY profiles.py roster                                  # the members (roster.yaml)
    $PY profiles.py prompt --member john-hassler [--stage research|extract|aggregate]   # print a prompt (free)
    $PY profiles.py estimate                                # cost of the full run (from saved usage, else assumptions)
    $PY profiles.py test --member john-hassler              # one member end to end on all three models (paid)
    $PY profiles.py run [--members ...] [--providers ...] [--stages research extract aggregate] [--workers 2]
    $PY profiles.py aggregate [--members ...] [--force]     # merge again from the saved extracts
    $PY profiles.py render                                  # profiles/<slug>.md, index.csv, ALL.md from saved JSON (free)
    $PY profiles.py status                                  # what is done, failed and spent, per member x model
    $PY profiles.py check-sources [--members ...]           # HTTP status of every cited URL (free, slow)

Per member:
  1. research (one call per model; web search and page reading on): the model writes a sourced profile under nine
     fixed headings (prompts/research_*.md). The provider's own citations are turned into markers ([A3], [O5], [G2])
     next to the text they support, with a numbered source list -> runs/<provider>/<slug>/research.json, dossier.md.
  2. extract (one call per model; no tools; JSON schema): the same model turns its own profile into atomic items with
     their sources (prompts/extract_*.md). Code gives every item an id (A01, O07, G12) and checks every source: a
     citation marker or a URL the provider's search tool actually returned is "grounded"; a URL that only the model
     wrote is not -> runs/<provider>/<slug>/extract.json.
  3. aggregate (one call; no tools; JSON schema; claude-opus-5-5 unless --aggregator): the three item lists are merged
     into one profile; every merged item lists the ids it rests on, disagreements are kept as conflicts, items about a
     namesake are dropped with a reason (prompts/aggregate_*.md). Code rejects ids that do not exist, counts how many
     models support each item and attaches the sources -> profiles/<slug>.json, profiles/<slug>.md.

An existing valid record is never asked again unless --force is given; a failed or invalid one is. Every API call is
logged in logs/calls.jsonl (tokens, searches, seconds, USD). Keys: environment variables named in ../config.yaml,
read only inside llm_providers.py at request time.
"""
import argparse
import csv
import datetime as dt
import json
import re
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import jsonschema
import requests
import yaml

HERE = Path(__file__).resolve().parent
ECON = HERE.parent
sys.path.insert(0, str(ECON))
import llm_providers as llm                                     # noqa: E402  (shared provider calls, ../llm_providers.py)

CFG = yaml.safe_load((ECON / "config.yaml").read_text())
STEP = yaml.safe_load((HERE / "settings.yaml").read_text())
ROSTER = yaml.safe_load((HERE / "roster.yaml").read_text())
MEMBERS = {m["slug"]: m for m in ROSTER["members"]}
PROVIDERS = ("anthropic", "openai", "gemini")
LETTER = CFG["provider_letter"]
RUNS, PROFILES, LOGS, PROMPTS = HERE / "runs", HERE / "profiles", HERE / "logs", HERE / "prompts"
LOCK = threading.Lock()

SECTIONS = ["position", "education", "career", "research_area", "method", "publication", "prize_work", "view",
            "honour", "editorial_policy_role", "collaborator", "other"]
SECTION_TITLES = {"position": "Current positions", "education": "Education", "career": "Earlier positions",
                  "research_area": "Research areas", "method": "Methods", "publication": "Key publications",
                  "prize_work": "Work for the prize and the Academy", "view": "Documented views",
                  "honour": "Honours", "editorial_policy_role": "Editorial, advisory and policy roles",
                  "collaborator": "Collaborators and networks", "other": "Other"}

# ---------------------------------------------------------------- JSON schemas (strings only, no nulls: the three
# providers' JSON modes share this subset; "" means "not stated")

S = {"type": "string"}
SA = {"type": "array", "items": S}


def obj(props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


ITEM = obj({"section": {"type": "string", "enum": SECTIONS}, "statement": S, "institution": S, "role_or_title": S,
            "years": S, "venue": S, "coauthors": SA, "quote": S, "doi_or_url": S, "source_refs": SA,
            "unsourced": {"type": "boolean"}})
EXTRACT_SCHEMA = obj({
    "identity": obj({"full_name": S, "current_positions": S, "homepage_url": S, "orcid": S, "repec_or_scholar": S,
                     "identity_evidence": S, "namesakes_ruled_out": S}),
    "items": {"type": "array", "items": ITEM},
    "open_questions": SA})
AGG_SCHEMA = obj({
    "identity": obj({"full_name": S, "current_positions": S, "identity_evidence": S, "support_ids": SA}),
    "items": {"type": "array", "items": obj({"section": {"type": "string", "enum": SECTIONS}, "statement": S,
                                              "years": S, "support_ids": SA, "conflict_ids": SA, "conflict": S})},
    "summary": {"type": "array", "items": obj({"sentence": S, "support_ids": SA})},
    "open_questions": SA,
    "dropped": {"type": "array", "items": obj({"id": S, "reason": S})}})


# ---------------------------------------------------------------- small helpers

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def fill(template, **kw):
    """Replace {{key}} placeholders (no str.format, so braces in prompts are safe); every placeholder must be given."""
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: str(kw[m.group(1)]), template)
    return out


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def model_of(provider):
    return CFG["models"][provider]


def usd(provider, usage, searches):
    p = CFG["pricing"][model_of(provider)]
    u = usage or {}
    return round(((u.get("input") or 0) * p["input"] + (u.get("output") or 0) * p["output"]) / 1e6
                 + (searches or 0) * p["search_per_1k"] / 1000, 4)


def log_call(stage, slug, provider, rec, extra=None):
    row = {"time": now(), "stage": stage, "member": slug, "provider": provider, "model": model_of(provider),
           "model_reported": rec.get("model_reported"), "ok": not rec.get("error"), "stop": rec.get("stop"),
           "seconds": round(sum(h.get("seconds") or 0 for h in rec.get("http", [])), 1),
           "usage": rec.get("usage"), "searches": rec.get("searches"), "fetches": rec.get("fetches"),
           "usd": usd(provider, rec.get("usage"), rec.get("searches")), "error": rec.get("error")}
    row.update(extra or {})
    with LOCK:
        LOGS.mkdir(exist_ok=True)
        with (LOGS / "calls.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def say(*parts):
    with LOCK:
        print(*parts, flush=True)


UTM = re.compile(r"^(utm_|fbclid$|gclid$|mc_)")


def norm_url(u):
    """Comparable form of a URL: lower-case scheme and host, no 'www.', no fragment, no tracking parameters, no
    trailing slash."""
    try:
        s = urlsplit(u.strip().strip("<>").rstrip(").,;"))
    except ValueError:
        return u.strip()
    if not s.scheme.startswith("http"):
        return u.strip()
    host = s.netloc.lower().removeprefix("www.")
    q = urlencode([(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True) if not UTM.match(k)])
    path = s.path.rstrip("/") or ""
    return urlunsplit(("https", host, path, q, ""))


LINK = re.compile(r"\[([^\]]{0,300})\]\((https?://[^)\s]+)\)")
BARE = re.compile(r"(?<![\(\[])\bhttps?://[^\s)\]>\"']+")
MARK = re.compile(r"^\[?\s*([AOG])\s*(\d+)\s*\]?$")


def urls_in(text):
    urls = [m.group(2) for m in LINK.finditer(text or "")]
    urls += [m.group(0) for m in BARE.finditer(text or "")]
    return urls


# ---------------------------------------------------------------- prompts

def long_date(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def research_prompt(slug):
    m = MEMBERS[slug]
    system = (PROMPTS / "research_system.md").read_text(encoding="utf-8").strip()
    user = fill((PROMPTS / "research_user.md").read_text(encoding="utf-8").strip(),
                today_long=long_date(CFG["today"]),
                announcement_long=long_date(CFG["announcement"]) + ", 11:45 CEST at the earliest",
                name=m["name"], role=m["role"], title=m["title"], committee=ROSTER["committee"],
                awarding_body=ROSTER["awarding_body"])
    return system, user


def extract_prompt(slug, dossier):
    m = MEMBERS[slug]
    system = (PROMPTS / "extract_system.md").read_text(encoding="utf-8").strip()
    user = fill((PROMPTS / "extract_user.md").read_text(encoding="utf-8").strip(), name=m["name"], role=m["role"],
                title=m["title"], dossier=dossier)
    return system, user


# ---------------------------------------------------------------- stage 1: research

def cell_dir(provider, slug):
    return RUNS / provider / slug


def research_ok(rec):
    return bool(rec) and not rec.get("error") and bool((rec.get("text") or "").strip()) and not rec.get("truncated")


def run_research(slug, provider, force=False):
    path = cell_dir(provider, slug) / "research.json"
    old = read_json(path)
    if research_ok(old) and not force:
        return old, "exists"
    system, user = research_prompt(slug)
    r = STEP["research"]
    rec = llm.call_research(provider, model_of(provider), system, user, max_output_tokens=r["max_output_tokens"],
                            effort=r["effort"].get(provider), search=r["search"].get(provider, {}))
    rec.update(stage="research", member=slug, written=now(), prompt={"system": system, "user": user},
               settings={"max_output_tokens": r["max_output_tokens"], "effort": r["effort"].get(provider),
                         "search": r["search"].get(provider, {})})
    write_json(path, rec)
    if rec.get("dossier"):
        (path.parent / "dossier.md").write_text(rec["dossier"], encoding="utf-8")
    row = log_call("research", slug, provider, rec)
    return rec, f"asked ({row['seconds']:.0f}s, ${row['usd']:.2f})"


# ---------------------------------------------------------------- stage 2: extract

def validate_extract(obj_):
    v = jsonschema.Draft202012Validator(EXTRACT_SCHEMA)
    errs = [f"{'/'.join(map(str, e.path))}: {e.message[:200]}" for e in v.iter_errors(obj_)][:10]
    if not errs and not obj_["items"]:
        errs.append("no items")
    if not errs and not any(x["statement"].strip() for x in obj_["items"]):
        errs.append("all statements empty")
    return errs


def source_table(research):
    return {s["marker"]: s for s in research.get("sources_table", [])}


def resolve_sources(item, research, profile_urls):
    """Every source_ref of an extracted item -> {url, title, grounded, via}. grounded = the provider's search tool
    returned or cited this page; a URL that only appears as a link the model wrote is not grounded."""
    table = source_table(research)
    grounded = set(research.get("grounded_urls", []))
    out, seen = [], set()
    refs = list(item.get("source_refs") or [])
    if item.get("doi_or_url", "").startswith("http"):
        refs.append(item["doi_or_url"])
    for ref in refs:
        ref = (ref or "").strip()
        if not ref:
            continue
        m = MARK.match(ref)
        if m:
            s = table.get(f"{m.group(1)}{m.group(2)}")
            if s is None:
                out.append({"ref": ref, "url": None, "title": None, "grounded": False, "via": "unknown marker"})
                continue
            url, title, via = s["url"], s.get("title"), "citation"
        else:
            urls = urls_in(ref) or ([ref] if ref.startswith("http") else [])
            if not urls:
                out.append({"ref": ref, "url": None, "title": None, "grounded": False, "via": "not a source"})
                continue
            url, title = urls[0], None
            via = "link in profile" if norm_url(url) in profile_urls else "link not in profile"
        key = norm_url(url)
        if key in seen:
            continue
        seen.add(key)
        out.append({"ref": ref, "url": url, "title": title, "grounded": key in grounded, "via": via})
    return out


def extract_ok(rec):
    return bool(rec) and rec.get("valid") is True


def run_extract(slug, provider, force=False):
    path = cell_dir(provider, slug) / "extract.json"
    old = read_json(path)
    if extract_ok(old) and not force:
        return old, "exists"
    research = read_json(cell_dir(provider, slug) / "research.json")
    if not research_ok(research):
        return None, "no valid research record"
    system, user = extract_prompt(slug, research["dossier"])
    e = STEP["extract"]
    attempts, errs, parsed = [], ["not asked"], None
    for _ in range(1 + e["json_retries"]):
        res = llm.call_json(provider, model_of(provider), system, user, EXTRACT_SCHEMA,
                            max_output_tokens=e["max_output_tokens"], effort=e["effort"].get(provider))
        log_call("extract", slug, provider, res)
        if res.get("error"):
            errs = [f"HTTP: {res['error']}"]
            attempts.append(strip_raw(res, errs))
            break
        parsed = res.get("parsed")
        errs = validate_extract(parsed) if parsed is not None else [res.get("parse_error") or "no JSON"]
        if res.get("truncated"):
            errs.append(f"truncated (stop={res.get('stop')})")
        attempts.append(strip_raw(res, errs))
        if not errs:
            break
    rec = {"stage": "extract", "member": slug, "provider": provider, "model": model_of(provider), "written": now(),
           "prompt": {"system": system, "user_chars": len(user)}, "schema": EXTRACT_SCHEMA,
           "attempts": attempts, "valid": not errs, "errors": errs}
    if not errs:
        profile_urls = {norm_url(u) for u in urls_in(research["dossier"])}
        items = []
        for i, it in enumerate(parsed["items"], 1):
            it = dict(it, id=f"{LETTER[provider]}{i:02d}")
            it["sources"] = resolve_sources(it, research, profile_urls)
            it["grounded"] = any(s["grounded"] for s in it["sources"])
            items.append(it)
        rec.update(identity=parsed["identity"], items=items, open_questions=parsed["open_questions"],
                   checks=extract_checks(items))
    write_json(path, rec)
    return rec, ("valid" if not errs else f"INVALID: {errs[:2]}")


def strip_raw(res, errs):
    """Keep the call record without the full raw response text duplicated (the parsed object is kept once)."""
    keep = {k: v for k, v in res.items() if k not in ("response_raw",)}
    keep["errors"] = errs
    return keep


def extract_checks(items):
    c = Counter()
    for it in items:
        c["items"] += 1
        c["grounded"] += it["grounded"]
        c["unsourced"] += bool(it["unsourced"])
        c["no_source"] += not it["sources"]
        c["link_not_in_profile"] += any(s["via"] == "link not in profile" for s in it["sources"])
        c["unknown_marker"] += any(s["via"] == "unknown marker" for s in it["sources"])
    return dict(c)


# ---------------------------------------------------------------- stage 3: aggregate

def aggregate_inputs(slug):
    ex = {p: read_json(cell_dir(p, slug) / "extract.json") for p in PROVIDERS}
    ex = {p: e for p, e in ex.items() if extract_ok(e)}
    return ex


def aggregate_prompt(slug, ex):
    m = MEMBERS[slug]
    ident = "\n".join(f"{LETTER[p]}: " + json.dumps(e["identity"], ensure_ascii=False) for p, e in ex.items())
    lines = []
    for p, e in ex.items():
        for it in e["items"]:
            lines.append(json.dumps({"id": it["id"], "section": it["section"], "statement": it["statement"],
                                     "institution": it["institution"], "role_or_title": it["role_or_title"],
                                     "years": it["years"], "venue": it["venue"], "coauthors": it["coauthors"],
                                     "quote": it["quote"], "unsourced": it["unsourced"], "grounded": it["grounded"],
                                     "sources": [s["url"] for s in it["sources"] if s["url"]]},
                                    ensure_ascii=False))
    oq = "\n".join(f"{LETTER[p]}: {q}" for p, e in ex.items() for q in e["open_questions"]) or "(none)"
    system = (PROMPTS / "aggregate_system.md").read_text(encoding="utf-8").strip()
    user = fill((PROMPTS / "aggregate_user.md").read_text(encoding="utf-8").strip(), name=m["name"], role=m["role"],
                title=m["title"], identities=ident, items="\n".join(lines), open_questions=oq)
    return system, user


def validate_aggregate(out, known):
    v = jsonschema.Draft202012Validator(AGG_SCHEMA)
    errs = [f"{'/'.join(map(str, e.path))}: {e.message[:200]}" for e in v.iter_errors(out)][:10]
    if errs:
        return errs, [], set()
    used = set()
    unknown = set()
    for it in out["items"]:
        for i in it["support_ids"] + it["conflict_ids"]:
            (used if i in known else unknown).add(i)
    for s in out["summary"]:
        unknown |= {i for i in s["support_ids"] if i not in known}
    unknown |= {i for i in out["identity"]["support_ids"] if i not in known}
    dropped = {d["id"] for d in out["dropped"]}
    unknown |= {i for i in dropped if i not in known}
    if unknown:
        errs.append(f"{len(unknown)} ids that are not input ids: {sorted(unknown)[:10]}")
    unaccounted = sorted(known - used - dropped)
    if not out["items"]:
        errs.append("no merged items")
    return errs, unaccounted, unknown


def run_aggregate(slug, aggregator=None, force=False):
    path = PROFILES / f"{slug}.json"
    old = read_json(path)
    if old and old.get("valid") and not force:
        return old, "exists"
    ex = aggregate_inputs(slug)
    if not ex:
        return None, "no valid extract"
    provider = aggregator or STEP["aggregate"]["provider"]
    system, user = aggregate_prompt(slug, ex)
    known = {it["id"]: (p, it) for p, e in ex.items() for it in e["items"]}
    a = STEP["aggregate"]
    attempts, errs, out, unaccounted = [], ["not asked"], None, []
    for _ in range(1 + a["json_retries"]):
        res = llm.call_json(provider, model_of(provider), system, user, AGG_SCHEMA,
                            max_output_tokens=a["max_output_tokens"], effort=a["effort"].get(provider))
        log_call("aggregate", slug, provider, res)
        if res.get("error"):
            errs = [f"HTTP: {res['error']}"]
            attempts.append(strip_raw(res, errs))
            break
        out = res.get("parsed")
        if out is None:
            errs, unaccounted = [res.get("parse_error") or "no JSON"], []
        else:
            errs, unaccounted, _ = validate_aggregate(out, set(known))
        if res.get("truncated"):
            errs.append(f"truncated (stop={res.get('stop')})")
        attempts.append(strip_raw(res, errs))
        if not errs:
            break
    rec = {"stage": "aggregate", "member": slug, "name": MEMBERS[slug]["name"], "role": MEMBERS[slug]["role"],
           "title_as_listed": MEMBERS[slug]["title"], "aggregator": model_of(provider), "written": now(),
           "inputs": {p: {"model": model_of(p), "items": len(e["items"]), "written": e["written"]}
                      for p, e in ex.items()},
           "missing_inputs": [p for p in PROVIDERS if p not in ex],
           "prompt": {"system": system, "user_chars": len(user)}, "attempts": attempts,
           "valid": not errs, "errors": errs}
    if not errs:
        rec.update(merge_details(out, known, unaccounted))
    write_json(path, rec)
    if not errs:
        render_member(rec)
    return rec, ("valid" if not errs else f"INVALID: {errs[:2]}")


def merge_details(out, known, unaccounted):
    """Attach providers, sources and fields to each merged item from the input items it cites."""
    items = []
    for it in out["items"]:
        sup = [known[i] for i in it["support_ids"] if i in known]
        if not sup:
            continue
        providers = sorted({LETTER[p] for p, _ in sup}, key="AOG".index)
        srcs = {}
        for p, x in sup:
            for s in x["sources"]:
                if not s["url"]:
                    continue
                k = norm_url(s["url"])
                d = srcs.setdefault(k, {"url": s["url"], "title": s.get("title"), "grounded_by": [], "cited_by": []})
                d["cited_by"] = sorted(set(d["cited_by"]) | {LETTER[p]}, key="AOG".index)
                if s["grounded"]:
                    d["grounded_by"] = sorted(set(d["grounded_by"]) | {LETTER[p]}, key="AOG".index)
                d["title"] = d["title"] or s.get("title")
        fields = {}
        for f in ("institution", "role_or_title", "venue", "doi_or_url", "quote"):
            vals = [x[f] for _, x in sup if x.get(f)]
            fields[f] = Counter(vals).most_common(1)[0][0] if vals else ""
        coauthors = []
        for _, x in sup:
            coauthors += [c for c in x["coauthors"] if c not in coauthors]
        items.append(dict(it, providers=providers, n_providers=len(providers),
                          grounded=any(d["grounded_by"] for d in srcs.values()),
                          unsourced_only=all(x["unsourced"] or not x["sources"] for _, x in sup),
                          sources=list(srcs.values()), fields=fields, coauthors=coauthors))
    n = Counter(it["n_providers"] for it in items)
    stats = {"items": len(items), "by_n_providers": {str(k): n.get(k, 0) for k in (3, 2, 1)},
             "grounded_items": sum(it["grounded"] for it in items),
             "conflicts": sum(bool(it["conflict"]) for it in items), "dropped": len(out["dropped"]),
             "unaccounted_input_ids": unaccounted, "input_items": len(known)}
    return {"identity": out["identity"], "items": items, "summary": out["summary"],
            "open_questions": out["open_questions"], "dropped": out["dropped"], "stats": stats}


# ---------------------------------------------------------------- rendering

def badge(providers):
    return "[" + " ".join(x if x in providers else "·" for x in "AOG") + "]"


def render_member(rec):
    m = MEMBERS[rec["member"]]
    lines = [f"# {m['name']}", "",
             f"**{m['role'].capitalize()}**, {ROSTER['committee']} {ROSTER['year']} · {m['title']} (as listed)", "",
             f"Researched independently by {', '.join(f'{LETTER[p]} = {model_of(p)}' for p in PROVIDERS)} with web "
             f"search; merged by {rec['aggregator']} on {rec['written'][:10]}. "
             f"Badges show which researchers state an item; ✓ = at least one source was returned by a researcher's "
             f"search tool; *unsourced* = no researcher gave a source.", ""]
    if rec["missing_inputs"]:
        lines += [f"> Missing researcher(s): {', '.join(rec['missing_inputs'])}", ""]
    st = rec["stats"]
    lines += [f"Items: {st['items']} (3 researchers {st['by_n_providers']['3']}, 2: {st['by_n_providers']['2']}, "
              f"1: {st['by_n_providers']['1']}); grounded {st['grounded_items']}; conflicts {st['conflicts']}; "
              f"dropped input items {st['dropped']}.", "", "## Summary", ""]
    for s in rec["summary"]:
        lines.append(f"- {s['sentence']} <sub>{', '.join(s['support_ids'])}</sub>")
    idn = rec["identity"]
    lines += ["", "## Identity", "", f"- Name: {idn['full_name']}", f"- Current positions: {idn['current_positions']}",
              f"- How confirmed: {idn['identity_evidence']} <sub>{', '.join(idn['support_ids'])}</sub>"]
    src_index = {}
    for sec in SECTIONS:
        its = [it for it in rec["items"] if it["section"] == sec]
        if not its:
            continue
        lines += ["", f"## {SECTION_TITLES[sec]}", ""]
        its.sort(key=lambda it: (-it["n_providers"], it["years"]))
        for it in its:
            refs = []
            for s in it["sources"]:
                k = norm_url(s["url"])
                if k not in src_index:
                    src_index[k] = (len(src_index) + 1, s)
                refs.append(f"[{src_index[k][0]}]({s['url']})" + ("✓" if s["grounded_by"] else ""))
            tail = " ".join(refs) if refs else "*unsourced*"
            yrs = f" ({it['years']})" if it["years"] else ""
            lines.append(f"- `{badge(it['providers'])}` {it['statement']}{yrs} — {tail} <sub>{', '.join(it['support_ids'])}</sub>")
            if it["conflict"]:
                lines.append(f"  - ⚠ conflict: {it['conflict']} <sub>{', '.join(it['conflict_ids'])}</sub>")
    if rec["open_questions"]:
        lines += ["", "## Open questions", ""] + [f"- {q}" for q in rec["open_questions"]]
    if rec["dropped"]:
        lines += ["", "## Dropped input items", ""] + [f"- {d['id']}: {d['reason']}" for d in rec["dropped"]]
    if st["unaccounted_input_ids"]:
        lines += ["", f"Input items the merge did not account for: {', '.join(st['unaccounted_input_ids'])}"]
    lines += ["", "## Sources", ""]
    for k, (n, s) in sorted(src_index.items(), key=lambda kv: kv[1][0]):
        g = f"returned by the search of {', '.join(s['grounded_by'])}" if s["grounded_by"] else "link written by the model only"
        lines.append(f"{n}. [{s['title'] or s['url']}]({s['url']}) — cited by {', '.join(s['cited_by'])}; {g}")
    PROFILES.mkdir(exist_ok=True)
    (PROFILES / f"{rec['member']}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_render(a):
    rows, parts = [], [f"# {ROSTER['committee']} {ROSTER['year']}: merged member profiles", "",
                       "One section per member: role, summary and the merged item counts. Full profiles: "
                       "`profiles/<slug>.md`.", ""]
    for slug, m in MEMBERS.items():
        rec = read_json(PROFILES / f"{slug}.json")
        if not rec or not rec.get("valid"):
            rows.append({"slug": slug, "name": m["name"], "role": m["role"], "status": "missing"})
            parts += [f"## {m['name']} ({m['role']})", "", "*Not merged yet.*", ""]
            continue
        render_member(rec)
        st = rec["stats"]
        rows.append({"slug": slug, "name": m["name"], "role": m["role"], "status": "merged",
                     "researchers": len(rec["inputs"]), "items": st["items"],
                     "items_3": st["by_n_providers"]["3"], "items_2": st["by_n_providers"]["2"],
                     "items_1": st["by_n_providers"]["1"], "grounded_items": st["grounded_items"],
                     "conflicts": st["conflicts"], "dropped": st["dropped"],
                     "unaccounted": len(st["unaccounted_input_ids"]), "aggregator": rec["aggregator"],
                     "written": rec["written"]})
        parts += [f"## {m['name']} ({m['role']})", "", f"{m['title']} · [full profile]({slug}.md)", ""]
        parts += [f"- {s['sentence']}" for s in rec["summary"]]
        parts += ["", f"Items {st['items']} (3/2/1 researchers: {st['by_n_providers']['3']}/"
                      f"{st['by_n_providers']['2']}/{st['by_n_providers']['1']}), conflicts {st['conflicts']}.", ""]
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
        sys.exit("missing API key environment variable(s): "
                 + ", ".join(CFG["api_keys"][p] for p in missing) + " (export them in this shell; values are never read here)")


def pick_members(names):
    if not names or names == ["all"]:
        return list(MEMBERS)
    bad = [n for n in names if n not in MEMBERS]
    if bad:
        sys.exit(f"unknown member slug(s): {bad}; see `profiles.py roster`")
    return names


def cmd_roster(a):
    for slug, m in MEMBERS.items():
        print(f"{slug:<24} {m['role']:<16} {m['name']:<24} {m['title']}")


def cmd_prompt(a):
    if a.stage == "research":
        system, user = research_prompt(a.member)
    elif a.stage == "extract":
        rec = read_json(cell_dir(a.provider, a.member) / "research.json")
        if not research_ok(rec):
            sys.exit(f"no valid research record for {a.member} / {a.provider}")
        system, user = extract_prompt(a.member, rec["dossier"])
    else:
        ex = aggregate_inputs(a.member)
        if not ex:
            sys.exit(f"no valid extract for {a.member}")
        system, user = aggregate_prompt(a.member, ex)
    print(f"## system\n{system}\n\n## user\n{user}")


def one_member(slug, providers, stages, force, aggregator, pools):
    """research -> extract per provider (in the provider's pool), then aggregate once both are done."""
    def chain(p):
        if "research" in stages:
            rec, how = run_research(slug, p, force)
            say(f"{slug:<24} {p:<9} research  {status_of(rec)}  [{how}]")
            if not research_ok(rec):
                return
        if "extract" in stages:
            rec, how = run_extract(slug, p, force)
            say(f"{slug:<24} {p:<9} extract   [{how}]" + (f" items={len(rec['items'])} {rec['checks']}" if rec and rec.get("valid") else ""))
    futs = [pools[p].submit(chain, p) for p in providers]
    for f in futs:
        try:
            f.result()
        except Exception as e:                                  # one crashed cell must not stop the others
            say(f"{slug:<24} CRASHED: {type(e).__name__}: {str(e)[:200]}")
    if "aggregate" in stages:
        rec, how = run_aggregate(slug, aggregator, force)
        say(f"{slug:<24} merged    [{how}]" + (f" {rec['stats']['by_n_providers']} conflicts={rec['stats']['conflicts']}" if rec and rec.get("valid") else ""))


def status_of(rec):
    if not rec:
        return "MISSING"
    if rec.get("error"):
        return f"ERROR {rec['error'][:80]}"
    if rec.get("truncated"):
        return f"TRUNCATED stop={rec.get('stop')}"
    return (f"ok stop={rec.get('stop')} searches={rec.get('searches')} fetches={rec.get('fetches')} "
            f"cited={len(rec.get('sources_table', []))} chars={len(rec.get('text') or '')}")


def cmd_run(a, members=None):
    members = members or pick_members(a.members)
    stages = a.stages
    providers = a.providers
    if any(s in stages for s in ("research", "extract")):
        need_keys(providers)
    if "aggregate" in stages:
        need_keys([a.aggregator or STEP["aggregate"]["provider"]])
    pools = {p: ThreadPoolExecutor(a.workers) for p in providers}
    outer = ThreadPoolExecutor(max(1, a.workers * 2))
    futs = [outer.submit(one_member, s, providers, stages, a.force, a.aggregator, pools) for s in members]
    for f in futs:
        f.result()
    outer.shutdown()
    for p in pools.values():
        p.shutdown()
    cmd_render(a)
    cmd_status(a)


def cmd_test(a):
    a.members, a.stages = [a.member], ["research", "extract", "aggregate"]
    cmd_run(a, members=[a.member])


def cmd_aggregate(a):
    members = pick_members(a.members)
    need_keys([a.aggregator or STEP["aggregate"]["provider"]])
    for slug in members:
        rec, how = run_aggregate(slug, a.aggregator, a.force)
        say(f"{slug:<24} merged [{how}]")
    cmd_render(a)


def cmd_status(a):
    calls = []
    if (LOGS / "calls.jsonl").exists():
        calls = [json.loads(x) for x in (LOGS / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    spent = defaultdict(float)
    for c in calls:
        spent[(c["member"], c["provider"])] += c.get("usd") or 0
    print(f"{'member':<24} " + " ".join(f"{p:<22}" for p in PROVIDERS) + " merged")
    for slug in MEMBERS:
        cells = []
        for p in PROVIDERS:
            r = read_json(cell_dir(p, slug) / "research.json")
            e = read_json(cell_dir(p, slug) / "extract.json")
            rs = "-" if r is None else ("R" if research_ok(r) else "r!")
            es = "-" if e is None else (f"E{len(e['items'])}" if extract_ok(e) else "e!")
            cells.append(f"{rs}/{es} ${spent[(slug, p)]:.2f}")
        g = read_json(PROFILES / f"{slug}.json")
        gs = "-" if g is None else ("ok" if g.get("valid") else "INVALID")
        print(f"{slug:<24} " + " ".join(f"{c:<22}" for c in cells) + f" {gs}")
    tot = sum(c.get("usd") or 0 for c in calls)
    print(f"\nR = research ok, E<n> = extract ok with n items, r!/e! = failed; spent so far ${tot:.2f} over "
          f"{len(calls)} calls (logs/calls.jsonl)")


def cmd_estimate(a):
    """Full-run cost: per provider and stage, the mean logged cost of successful calls; else settings assumptions."""
    calls = []
    if (LOGS / "calls.jsonl").exists():
        calls = [json.loads(x) for x in (LOGS / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    n = len(MEMBERS)
    total = 0.0
    print(f"{'stage':<10} {'model':<24} {'calls':>5} {'USD/call':>9} {'USD':>8}  basis")
    for stage in ("research", "extract", "aggregate"):
        provs = PROVIDERS if stage != "aggregate" else (STEP["aggregate"]["provider"],)
        for p in provs:
            seen = [c["usd"] for c in calls if c["stage"] == stage and c["provider"] == p and c["ok"]]
            if seen:
                per, basis = sum(seen) / len(seen), f"mean of {len(seen)} logged calls"
            else:
                ass = STEP["estimate_assumptions"][stage]
                per = usd(p, {"input": ass["input"], "output": ass["output"]}, ass.get("searches", 0)
                          if stage == "research" else 0)
                basis = f"assumption {ass}"
            total += per * n
            print(f"{stage:<10} {model_of(p):<24} {n:>5} {per:>9.3f} {per * n:>8.2f}  {basis}")
    print(f"{'total for ' + str(n) + ' members (one attempt per call)':<50} {total:>8.2f}")


def cmd_check_sources(a):
    """GET every distinct cited URL once (no key, 1 request per second) and record the HTTP status."""
    out = PROFILES / "source_check.csv"
    urls = {}
    for slug in pick_members(a.members):
        rec = read_json(PROFILES / f"{slug}.json")
        if not rec or not rec.get("valid"):
            continue
        for it in rec["items"]:
            for s in it["sources"]:
                urls.setdefault(norm_url(s["url"]), (slug, s["url"]))
    rows = []
    for i, (k, (slug, url)) in enumerate(sorted(urls.items())):
        if i:
            time.sleep(1.0)
        try:
            r = requests.get(url, timeout=20, allow_redirects=True, stream=True,
                             headers={"User-Agent": "KnowledgeLab-NobelResearch/1.0 (link check)"})
            status, final = r.status_code, r.url
            r.close()
        except requests.RequestException as e:
            status, final = f"ERR:{type(e).__name__}", ""
        rows.append({"member": slug, "url": url, "status": status, "final_url": final})
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["member", "url", "status", "final_url"])
        w.writeheader()
        w.writerows(rows)
    bad = [r for r in rows if r["status"] != 200]
    print(f"{out.relative_to(HERE)}: {len(rows)} URLs, {len(bad)} not HTTP 200")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster")
    s = sub.add_parser("prompt"); s.add_argument("--member", required=True, choices=list(MEMBERS))
    s.add_argument("--stage", default="research", choices=["research", "extract", "aggregate"])
    s.add_argument("--provider", default="anthropic", choices=PROVIDERS)
    sub.add_parser("estimate")
    for name in ("test", "run"):
        s = sub.add_parser(name)
        if name == "test":
            s.add_argument("--member", required=True, choices=list(MEMBERS))
        else:
            s.add_argument("--members", nargs="+", default=["all"])
            s.add_argument("--stages", nargs="+", default=["research", "extract", "aggregate"],
                           choices=["research", "extract", "aggregate"])
        s.add_argument("--providers", nargs="+", default=list(PROVIDERS), choices=PROVIDERS)
        s.add_argument("--workers", type=int, default=2, help="concurrent calls per provider")
        s.add_argument("--aggregator", choices=PROVIDERS, default=None)
        s.add_argument("--force", action="store_true", help="ask again even when a valid record exists (paid)")
    s = sub.add_parser("aggregate"); s.add_argument("--members", nargs="+", default=["all"])
    s.add_argument("--aggregator", choices=PROVIDERS, default=None); s.add_argument("--force", action="store_true")
    sub.add_parser("render")
    sub.add_parser("status")
    s = sub.add_parser("check-sources"); s.add_argument("--members", nargs="+", default=["all"])
    a = ap.parse_args()
    {"roster": cmd_roster, "prompt": cmd_prompt, "estimate": cmd_estimate, "test": cmd_test, "run": cmd_run,
     "aggregate": cmd_aggregate, "render": cmd_render, "status": cmd_status,
     "check-sources": cmd_check_sources}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
