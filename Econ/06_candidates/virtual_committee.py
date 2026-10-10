#!/usr/bin/env python3
"""virtual_committee.py: the Econ virtual committee (step 6). Eleven personas = the members of the real 2026 committee,
reconstructed from the step-1 profiles; three models; the 14 fields of the field question in three batches (5/5/4
fields); one call per member x model x batch, up to five ranked nominations per field. settings.yaml batches_to_ask
selects the batches asked (10 Oct 2026: batch 1 only, the five leading fields of the latest field forecast; 33 calls).

    $PY virtual_committee.py prompt --member john-hassler [--batch 1]   # the exact prompt (free), also written to prompts/
    $PY virtual_committee.py test --member john-hassler [--batch 1] [--providers ...]   # one call per model (paid)
    $PY virtual_committee.py estimate                            # cost of the 99 calls (logged calls, else assumptions)
    $PY virtual_committee.py run [--members ...] [--providers ...] [--batches ...] [--workers 3] [--force]   # (paid)
    $PY virtual_committee.py collect                             # raw/ -> committee/<field>/ballots.jsonl
    $PY virtual_committee.py aggregate [--fields ...]            # ballots (+ merges.yaml) -> candidates.json, review.md
    $PY virtual_committee.py integrate [--fields ...] [--force] [--dry-run]   # Claude integrates the A/O/G nominations (paid)
    $PY virtual_committee.py context                             # integrated candidates -> context/ notes for Preseen
    $PY virtual_committee.py pool [--source claude|rule]         # top options per field, pool sizes 7/6/6/6/5 -> results/
    $PY virtual_committee.py status

Design (same as the 1 October committees of ../../experiment/preseen/committee.py, with the real members as personas):
every call of a batch sees the same user prompt (date, rules incl. the age record, the list of all 14 fields, the
batch's fields with their definitions and already-awarded works, the task) and a system prompt built from the member's
merged profile. (A first run on the five leading fields only, 10 Oct 13:05-13:47, is in Old/five_fields_2026-10-10/.)
No tools, no web search, provider defaults, a 32,000-token output cap. A ballot that is not valid is asked once more; a cell that still fails is recorded as missing.
Aggregation per field: Borda 5..1 per ballot, each model's points divided by its number of valid ballots in that field
and summed over models; nominations sharing a person are merged (first initial + surname), with a reviewed merges.yaml
per field. The nominations are a simulation: inferences from the members' published records, not the real members'
views. Keys come from the environment (names in ../config.yaml); every call is logged in logs/calls.jsonl.

Integration (`integrate`, 10 Oct, the user's choice over the rule-based clusters and a hand-made merges.yaml): one
claude-opus-5-5 call per field gets every valid nomination of the three models (anonymous ids, ballot labels, rank,
code, contribution, people, key works, rationale) and returns distinct candidates: the nomination ids it groups, a
motivation line, the lineup (1-3 people named in those nominations, ineligible people left out), the case from the
rationales and a grouping note. Claude does not rank or score; scores, supporters, per-person support and flags are
computed locally from the assignment. `context` writes the Preseen context notes from the integrated lists.
"""
import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
import sys
import threading
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ECON = HERE.parent
sys.path.insert(0, str(ECON))
import llm_providers as llm  # noqa: E402  (the Econ JSON-mode client: no tools, no web search)

CFG = yaml.safe_load((ECON / "config.yaml").read_text())
SET = yaml.safe_load((HERE / "settings.yaml").read_text())
PROVIDERS = ("anthropic", "openai", "gemini")
SHORT = {"anthropic": "A", "openai": "O", "gemini": "G"}
MODEL = CFG["models"]
COMMITTEE, RAW, LOGS, RESULTS, PROMPTS = HERE / "committee", HERE / "committee" / "raw", HERE / "logs", HERE / "results", HERE / "prompts"
INTEGRATED_RAW, CONTEXT = HERE / "committee" / "integrated_raw", HERE / "context"
LOCK = threading.Lock()
ROSTER = yaml.safe_load((ECON / "01_committee/roster.yaml").read_text())["members"]
MEMBERS = {m["slug"]: m for m in ROSTER}
FIELDS = SET["fields"]
FIELD_BY_NAME = {f["name"]: f for f in FIELDS}
FIELD_BY_SLUG = {f["slug"]: f for f in FIELDS}
BATCHES = sorted({f["batch"] for f in FIELDS})
BATCH_FIELDS = {b: [f for f in FIELDS if f["batch"] == b] for b in BATCHES}
ASK_BATCHES = sorted(SET.get("batches_to_ask") or BATCHES)      # the batches that are asked (10 Oct: batch 1 only)
ASKED = [f for f in FIELDS if f["batch"] in ASK_BATCHES]          # all of FIELDS still define the boundary list
C = SET["committee"]
ROLE_SHORT = {"chair": "chair", "member": "member", "co-opted member": "co-opted", "secretary": "secretary"}

SCHEMA = {
    "type": "object",
    "properties": {
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "nominations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rank": {"type": "integer"},
                                "contribution": {"type": "string"},
                                "jel_code": {"type": "string"},
                                "people": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}, "affiliation": {"type": "string"},
                                                       "born": {"type": "string"}},
                                        "required": ["name", "affiliation", "born"],
                                        "additionalProperties": False,
                                    },
                                },
                                "key_works": {"type": "array", "items": {"type": "string"}},
                                "rationale": {"type": "string"},
                            },
                            "required": ["rank", "contribution", "jel_code", "people", "key_works", "rationale"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["field", "nominations"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["fields"],
    "additionalProperties": False,
}
# Count limits (5 nominations, 1-3 people, 3 works, 2 sentences) are in the prompt and checked locally, not in the
# schema: the providers' JSON modes support different subsets of JSON Schema.


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------------------------------------------------------------- data for the prompt

def awarded_works():
    """Works of each field from the step-4a mapping (year, laureates, official motivation, consensus code)."""
    w = pd.read_csv(ECON / "04_field_forecast/results/prize_works_fields14.csv")
    out = {}
    for f in FIELDS:
        g = w[w.field14 == f["name"]].sort_values(["year", "group"])
        out[f["name"]] = [f"- {r.year} {r.laureates}: \"{r.motivation}\" [{r.jel}]" for r in g.itertuples()]
    return out


def laureate_names():
    return pd.read_csv(ECON / "data/econ_prizes_laureates.csv")["laureate"].tolist()


def persona_text(member_slug):
    p = json.loads((ECON / "01_committee/profiles" / f"{member_slug}.json").read_text())
    prof, m = p["profile"], MEMBERS[member_slug]
    per = prof["persona"]
    fields = "; ".join(f"{f['field']} ({', '.join(f['jel_codes'][:4])})" for f in prof["fields"])
    interests = "; ".join(i["topic"] for i in prof["recent_interests"][:5])
    questions = " ".join(per.get("likely_questions_in_deliberation") or [])
    return m, "\n".join([
        f"You take the perspective of {m['name']}, {m['role']} of the Committee for the Prize in Economic Sciences in "
        f"Memory of Alfred Nobel 2026 ({m['title']}, {m['affiliation']}). The perspective is reconstructed from the "
        "member's public research record, not from any statement by the member; it is a simulation, and your "
        "nominations are inferences from that record, not the real person's views.",
        "",
        f"Profile. {per['summary']}",
        f"Research lens: {per['research_lens']}",
        f"Methods and evidence: {per['methods_and_evidence']}",
        f"What this member values in a contribution: {per['what_they_value_in_contributions']}",
        f"Questions this member would raise in deliberation: {questions}",
        f"Research fields: {fields}.",
        f"Recent interests: {interests}.",
        "",
        "Use this lens when you judge contributions. But, as the real committee does with the expert advisers it "
        "consults for areas outside its members' own fields, nominate from the whole of each field, not only from "
        "the areas closest to this member's work.",
    ])


def prompt(member_slug, batch):
    m, system = persona_text(member_slug)
    works = awarded_works()
    fields = BATCH_FIELDS[batch]
    k = len(fields)
    lines = [SET["date_context"], "",
             "The rules that matter:",
             "- The prize rewards a contribution of outstanding importance to economic sciences. It is awarded to at most "
             "three people and never posthumously: every person you name must be living on 9 October 2026, and no previous "
             "laureate of this prize may be named.",
             "- A prize may be divided between two contributions, each considered worthy of a prize. A recent prize in a "
             "field does not exclude it.",
             "- A nomination is a contribution, in the style of an official motivation (\"for ...\"), with the one to three "
             "living people most responsible for it. Name the people by the authorship of the decisive work, not by fame.",
             "- Contributions that have already been awarded are listed under each field; do not nominate them again, and do "
             "not re-label an awarded contribution as a new one. A distinct contribution in the same area is allowed.",
             "- Age, as context on maturity and not as a filter (the record of the 99 laureates, 1969-2025): the median "
             "laureate was 67 at the award, the middle 80 % between 57 and 78; 4 of 99 were under 55 and 6 of 99 were 80 or "
             "older (long-recognized theoretical work, such as Hurwicz at 90 and Shapley at 89). Among eventual laureates the "
             "chance of the award in a given year of age stays under 5 % before 61 and passes 10 % at 68; a model of the whole "
             "candidate pool (Dolton and Tol 2026) puts the chance of winning at its maximum at about 70-71. There is no trend "
             "in age since 1969 and no reliable difference between fields. Co-laureates are usually of one generation: the "
             "gap between the oldest and the youngest has a median of 9 years and was 15 years or more in 4 of the 26 shared "
             "awards. The prize has gone to people aged 75 or older 20 times; it is never awarded posthumously.",
             "",
             "This forecast divides economics into 14 fields, each defined by groups of JEL codes: "
             + "; ".join(f"{g['name']} ({g['jel']})" for g in FIELDS) + ". "
             f"This request covers {k} of them. For each of "
             f"the {k} fields below, the definition fixes the boundaries with neighbouring fields, and the prizes already "
             "awarded in it (1969-2025) are listed with their official motivations and the consensus JEL code of the awarded work."]
    for i, f in enumerate(fields, 1):
        lines += ["", f"Field {i}: {f['name']}", f["definition"], "Already awarded in this field:"] + (works[f["name"]] or ["- (none)"])
    lines += ["",
              f"Your task: for each of the {k} fields above, nominate up to {C['max_nominations']} contributions for the 2026 prize, "
              "ranked by how strongly you would support each one within that field (rank 1 = strongest). Consider the whole "
              "field, not only your own areas. For each nomination give:",
              f"- \"rank\": 1 to {C['max_nominations']}, each rank used once within the field;",
              "- \"contribution\": one line in the style of an official motivation (for example \"for the analysis of ...\");",
              "- \"jel_code\": the JEL level-3 code of the core of the contribution, inside the field's code groups;",
              f"- \"people\": 1 to {C['max_people']} living people most closely associated with the contribution, each with "
              "\"name\", \"affiliation\" and \"born\" (the year of birth as a string, or \"unknown\");",
              f"- \"key_works\": up to {C['max_key_works']} defining publications, the works that established the contribution "
              "(\"author(s), year: title, venue\"), only if you know them; otherwise an empty list;",
              f"- \"rationale\": at most {C['max_rationale_sentences']} sentences, from this member's lens: why this contribution "
              "and these people, and the main reservation, if any.",
              "",
              f"Answer with one JSON object of this form and nothing else, with the {k} field names exactly as written above. "
              f"The object must contain {k} field blocks, one for each of the {k} fields, in the order given; an answer "
              f"with fewer than {k} blocks is invalid and will be discarded:",
              '{"fields": [{"field": "' + fields[0]["name"] + '", "nominations": [{"rank": 1, "contribution": "...", "jel_code": "'
              + fields[0]["prefixes"][0] + '..", "people": [{"name": "...", "affiliation": "...", "born": "1955"}], '
              '"key_works": ["..."], "rationale": "..."}]}, {"field": "' + fields[1]["name"] + '", "nominations": [...]}, ...]}']
    return m, system, "\n".join(lines)


# ---------------------------------------------------------------- local validation

def sentences(text):
    return len([s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])", text.strip()) if s])


def match_field(name):
    s = str(name).strip().lower().replace("behavioral", "behavioural").replace("labor", "labour").replace("organisation", "organization")
    for f in FIELDS:
        if s == f["name"].lower() or s.startswith(f["name"].split(",")[0].lower()) or s == f["slug"]:
            return f["name"]
    return None


def code_in_field(code, fname):
    code = str(code or "").strip().upper()
    return any(code.startswith(p) for p in FIELD_BY_NAME[fname]["prefixes"])


def validate(obj, fields):
    """(valid, errors, warnings, {field name: clean nominations}). Hard errors: structure, types, every field of the
    batch present once with at least one nomination, no field of another batch. Count limits, ranks and codes outside
    the field are warnings."""
    asked = {f["name"] for f in fields}
    if not isinstance(obj, dict) or not isinstance(obj.get("fields"), list):
        return False, ["top level must be an object with a 'fields' list"], [], {}
    errs, warns, clean = [], [], {}
    seen = {}
    for i, blk in enumerate(obj["fields"], 1):
        if not isinstance(blk, dict) or "field" not in blk or not isinstance(blk.get("nominations"), list):
            errs.append(f"block {i}: not an object with 'field' and a 'nominations' list")
            continue
        fname = match_field(blk["field"])
        if fname is None or fname not in asked:
            errs.append(f"block {i}: field '{blk['field']}' was not asked in this request")
            continue
        if fname in seen:
            errs.append(f"field {fname} appears twice")
            continue
        seen[fname] = blk["nominations"]
    missing = [f["name"] for f in fields if f["name"] not in seen]
    if missing:
        errs.append(f"fields missing: {missing}")
    if errs:
        return False, errs, [], {}
    for fname, noms in seen.items():
        if not noms:
            errs.append(f"{fname}: no nominations")
            continue
        for i, n in enumerate(noms, 1):
            if not isinstance(n, dict):
                errs.append(f"{fname} nomination {i}: not an object")
                continue
            miss = [k for k in ("rank", "contribution", "jel_code", "people", "key_works", "rationale") if k not in n]
            if miss:
                errs.append(f"{fname} nomination {i}: missing {miss}")
                continue
            if not isinstance(n["rank"], int) or isinstance(n["rank"], bool):
                errs.append(f"{fname} nomination {i}: rank is not an integer")
            if not isinstance(n["contribution"], str) or not n["contribution"].strip():
                errs.append(f"{fname} nomination {i}: empty contribution")
            if not isinstance(n["people"], list) or not all(
                    isinstance(p, dict) and isinstance(p.get("name"), str) and p["name"].strip()
                    and isinstance(p.get("affiliation"), str) and isinstance(p.get("born"), str) for p in n["people"]):
                errs.append(f"{fname} nomination {i}: people must be a list of {{name, affiliation, born}}")
            if not isinstance(n["key_works"], list) or not all(isinstance(x, str) for x in n["key_works"]):
                errs.append(f"{fname} nomination {i}: key_works must be a list of strings")
            if not isinstance(n["rationale"], str) or not isinstance(n["jel_code"], str):
                errs.append(f"{fname} nomination {i}: rationale and jel_code must be strings")
    if errs:
        return False, errs, [], {}
    for fname, noms in seen.items():
        order = sorted(range(len(noms)), key=lambda i: (noms[i]["rank"], i))
        stated = [n["rank"] for n in noms]
        if sorted(stated) != list(range(1, len(noms) + 1)):
            warns.append(f"{fname}: ranks {stated} are not 1..{len(noms)}: re-ranked by stated rank, then position")
        if len(noms) > C["max_nominations"]:
            warns.append(f"{fname}: {len(noms)} nominations: ranks above {C['max_nominations']} get no points")
        out = []
        for new_rank, i in enumerate(order, 1):
            n = noms[i]
            k = len(n["people"])
            if not 1 <= k <= C["max_people"]:
                warns.append(f"{fname} rank {new_rank}: {k} people")
            if len(n["key_works"]) > C["max_key_works"]:
                warns.append(f"{fname} rank {new_rank}: {len(n['key_works'])} key works")
            if sentences(n["rationale"]) > C["max_rationale_sentences"]:
                warns.append(f"{fname} rank {new_rank}: rationale has {sentences(n['rationale'])} sentences")
            if not code_in_field(n["jel_code"], fname):
                warns.append(f"{fname} rank {new_rank}: code {n['jel_code']} outside the field's groups ({FIELD_BY_NAME[fname]['jel']})")
            out.append({"rank": new_rank, "rank_stated": n["rank"], "contribution": n["contribution"].strip(),
                        "jel_code": n["jel_code"].strip().upper(),
                        "people": [{"name": p["name"].strip(), "affiliation": p["affiliation"].strip(), "born": p["born"].strip()}
                                   for p in n["people"]],
                        "key_works": n["key_works"], "rationale": n["rationale"].strip()})
        clean[fname] = out
    return True, [], warns, clean


# ---------------------------------------------------------------- calls, logging, one cell = one member on one model

def usd(provider, usage):
    p = CFG["pricing"][MODEL[provider]]
    u = usage or {}
    return round(((u.get("input") or 0) * p["input"] + (u.get("output") or 0) * p["output"]) / 1e6, 4)


def log_call(stage, member_slug, provider, rec):
    row = {"time": now(), "stage": stage, "member": member_slug, "provider": provider, "model": MODEL[provider],
           "model_reported": rec.get("model_reported"), "ok": not rec.get("error"), "stop": rec.get("stop"),
           "seconds": round(sum(h.get("seconds") or 0 for h in rec.get("http", [])), 1),
           "usage": rec.get("usage"), "usd": usd(provider, rec.get("usage")), "error": rec.get("error")}
    with LOCK:
        LOGS.mkdir(exist_ok=True)
        with (LOGS / "calls.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def raw_path(provider, member_slug, batch, base=None):
    return (base or RAW) / MODEL[provider] / f"{member_slug}__b{batch}.json"


def run_cell(member_slug, provider, batch, base=None, force=False, stage="ballot"):
    path = raw_path(provider, member_slug, batch, base)
    if path.exists() and not force:
        old = json.loads(path.read_text())
        if old["final"]["valid"]:                       # a valid cell is never re-asked without --force;
            return old, "exists (not re-asked)"         # a missing (failed) cell is asked again
    m, system, user = prompt(member_slug, batch)
    attempts, ok, warns, clean = [], False, [], {}
    for _ in range(1 + C["json_retries"]):
        res = llm.call_json(provider, MODEL[provider], system, user, SCHEMA, C["max_output_tokens"], effort=C["effort"].get(provider))
        log_call(stage, f"{member_slug}__b{batch}", provider, res)
        res = {k: v for k, v in res.items() if k != "request"}        # the prompt is stored once below
        if res["error"]:
            res.update(valid=False, errors=[f"HTTP: {res['error']}"], warnings=[])
            attempts.append(res)
            break
        if res["parsed"] is None:
            ok, errs, warns, clean = False, [res["parse_error"] or "no JSON text"], [], {}
        else:
            ok, errs, warns, clean = validate(res["parsed"], BATCH_FIELDS[batch])
        if res["truncated"] and not ok:
            errs = errs + [f"truncated (stop={res['stop']})"]
        if res["refused"] and not ok:
            errs = errs + [f"refused (stop={res['stop']})"]
        res.update(valid=ok, errors=errs, warnings=warns)
        attempts.append(res)
        if ok:
            break
    rec = {"member": member_slug, "name": m["name"], "role": m["role"], "provider": provider, "model": MODEL[provider],
           "batch": batch, "fields": [f["name"] for f in BATCH_FIELDS[batch]], "written": now(), "prompt": {"system": system, "user": user}, "schema": SCHEMA,
           "params": {"max_output_tokens": C["max_output_tokens"], "effort": C["effort"].get(provider), "tools": None},
           "attempts": attempts,
           "final": {"valid": ok, "n_attempts": len(attempts), "nominations": clean if ok else {},
                     "warnings": warns if ok else [], "missing_reason": None if ok else attempts[-1]["errors"],
                     "model_reported": attempts[-1].get("model_reported")}}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
    tmp.replace(path)
    return rec, "asked"


def cell_line(rec, how):
    a = rec["attempts"][-1] if rec["attempts"] else {}
    u = a.get("usage") or {}
    secs = sum(h.get("seconds") or 0 for x in rec["attempts"] for h in x.get("http", []))
    n = sum(len(v) for v in rec["final"]["nominations"].values()) if rec["final"]["valid"] else 0
    return (f"{rec['model']:<22} {rec['name']:<24} b{rec.get('batch', '?')} {'valid' if rec['final']['valid'] else 'MISSING':<7} "
            f"att={rec['final']['n_attempts']} noms={n} stop={a.get('stop')} in={u.get('input')} out={u.get('output')} "
            f"(reasoning={u.get('reasoning')}) ${usd(rec['provider'], u):.2f} {secs:.0f}s  [{how}]")


# ---------------------------------------------------------------- aggregation per field (as committee.py)

TITLES = {"sir", "dame", "dr", "prof", "professor", "jr", "sr", "ii", "iii", "md", "phd"}
STOPWORDS = set("""for the a an of and in on to by its their his her as with from into via which that this these
    analysis analyses theory theories development developing developed contribution contributions role roles new use
    based economic economics economy""".split())


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def name_tokens(name):
    return [t for t in re.split(r"[^a-z]+", fold(name)) if t and t not in TITLES]


def person_key(name):
    t = name_tokens(name)
    return None if not t else (f"{t[0][0]} {t[-1]}" if len(t) > 1 else t[0])


def middles(name):
    return tuple(t[0] for t in name_tokens(name)[1:-1])


def assign_identities(noms):
    mids = {}
    for n in noms:
        for p in n["people"]:
            k = person_key(p["name"])
            if k:
                mids.setdefault(k, set()).add(middles(p["name"]))
    for n in noms:
        pids = []
        for j, p in enumerate(n["people"]):
            k, m = person_key(p["name"]), middles(p["name"])
            if k is None:
                pids.append(None)
            elif len({x for x in mids[k] if x}) <= 1:
                pids.append(k)
            else:
                pids.append(f"{k} {''.join(m)}" if m else f"{k} ?{n['id']}/{j}")
        n["pids"] = pids
        n["keys"] = sorted({x for x in pids if x})


def same_person(a, b):
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb or ta[-1] != tb[-1]:
        return False
    fa, fb = ta[0], tb[0]
    return fa == fb or (min(len(fa), len(fb)) == 1 and fa[0] == fb[0])


STOPWORDS |= {"study", "studies", "research", "work", "works", "modern", "fundamental", "foundations", "pioneering"}


def content_words(text):
    """Content words of a contribution line, cut to six characters so that 'heterogeneity' and 'heterogeneous' or
    'firm' and 'firms' coincide."""
    return {w[:6] for w in re.findall(r"[a-z0-9]+", fold(text)) if len(w) > 2 and w not in STOPWORDS}


def compatible(a, b):
    """Two nominations that share a person are linked only if they share two or more people or their contribution
    lines overlap in content words (Jaccard >= committee.link_min_overlap): a shared person alone chained distinct
    contributions (New Keynesian theory with credit frictions, Melitz with Eaton-Kortum) in the first aggregation."""
    if len(set(a["keys"]) & set(b["keys"])) >= 2:
        return True
    return jaccard(content_words(a["contribution"]), content_words(b["contribution"])) >= C.get("link_min_overlap", 0.15)


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def field_dir(fslug):
    return COMMITTEE / fslug


def flag_people(people, laureates, committee_names, notes=None):
    """Flags for shown people: previous laureate, sitting committee member, a note from merges.yaml, age >= 85."""
    flags = []
    for p in people:
        for name in laureates:
            if same_person(p["name"], name):
                flags.append(f"{p['name']}: already a laureate of this prize ({name})")
        for name in committee_names:
            if same_person(p["name"], name):
                flags.append(f"{p['name']}: member of the 2026 committee ({name}); not eligible while serving")
        note = (notes or {}).get(p["name"])
        if note:
            flags.append(f"{p['name']}: {note}")
        if p["born"] and 2026 - p["born"] >= 85:
            flags.append(f"{p['name']}: born {p['born']} (age {2026 - p['born']} in 2026)")
    return flags


def flag_awarded(texts, fname):
    """Word overlap (Jaccard >= 0.35) of any of the texts with an official motivation already awarded in the field."""
    flags = []
    for ln in awarded_works()[fname]:
        mot = ln.split('"')[1] if '"' in ln else ln
        j = max(jaccard(content_words(t), content_words(mot)) for t in texts)
        if j >= 0.35:
            flags.append(f"resembles an awarded motivation: {ln.strip('- ')[:90]} (word overlap {j:.2f})")
    return flags


def load_ballots(fslug, aliases=None):
    aliases = aliases or {}
    ballots = [json.loads(l) for l in (field_dir(fslug) / "ballots.jsonl").read_text().splitlines() if l.strip()]
    pts = C["borda_points"]
    noms = []
    for b in ballots:
        if not b["valid"]:
            continue
        for n in b["nominations"]:
            if n["rank"] > len(pts):
                continue
            people = [{**p, "name": aliases.get(p["name"], p["name"])} for p in n["people"]]
            noms.append({**n, "people": people, "id": f"{b['provider']}/{b['member']}/#{n['rank']}",
                         "provider": b["provider"], "member": b["member"], "name": b["name"], "role": b["role"],
                         "points": pts[n["rank"] - 1]})
    assign_identities(noms)
    return ballots, noms


def load_manual(fslug):
    path = field_dir(fslug) / "merges.yaml"
    m = (yaml.safe_load(path.read_text()) if path.exists() else None) or {}
    return {"split": m.get("split") or [], "merge": m.get("merge") or [], "person_notes": m.get("person_notes") or {},
            "aliases": m.get("aliases") or {}, "wording_from": m.get("wording_from") or [],
            "people": m.get("people") or [], "deceased": m.get("deceased") or {}}


def make_clusters(noms, manual):
    ids = {n["id"]: k for k, n in enumerate(noms)}
    for g in manual["split"] + manual["merge"] + [{"ids": [w["id"]]} for w in manual["wording_from"] + manual["people"]]:
        bad = [i for i in g["ids"] if i not in ids]
        if bad:
            sys.exit(f"merges.yaml: unknown nomination ids {bad}")
    parent = list(range(len(noms)))

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def union(a, b):
        parent[find(a)] = find(b)

    split_ids = {i for g in manual["split"] for i in g["ids"]}
    by_key = {}
    for k, n in enumerate(noms):
        if n["id"] not in split_ids:
            for key in n["keys"]:
                by_key.setdefault(key, []).append(k)
    for ks in by_key.values():
        for i in ks:
            for j in ks:
                if i < j and compatible(noms[i], noms[j]):
                    union(i, j)
    for g in manual["split"] + manual["merge"]:
        ks = [ids[i] for i in g["ids"]]
        for k in ks[1:]:
            union(ks[0], k)
    groups = {}
    for k in range(len(noms)):
        groups.setdefault(find(k), []).append(noms[k])
    return list(groups.values())


def n_valid(ballots):
    return {p: sum(1 for b in ballots if b["valid"] and b["provider"] == p) for p in PROVIDERS}


def score(members, nv):
    per = {p: 0.0 for p in PROVIDERS}
    for n in members:
        if nv[n["provider"]]:
            per[n["provider"]] += n["points"] / nv[n["provider"]]
    return sum(per.values()), per


def describe(c, nv, wording_from=()):
    w, cnt, forms, affs, born = {}, {}, {}, {}, {}
    for n in c:
        wn = n["points"] / nv[n["provider"]]
        for p, key in zip(n["people"], n["pids"]):
            if key is None:
                continue
            w[key] = w.get(key, 0) + wn
            cnt[key] = cnt.get(key, 0) + 1
            forms.setdefault(key, {}).setdefault(p["name"], 0)
            forms[key][p["name"]] += 1
            affs.setdefault(key, {}).setdefault(p["affiliation"], 0)
            affs[key][p["affiliation"]] += 1
            if p.get("born", "").isdigit():
                born.setdefault(key, []).append(int(p["born"]))
    people = [{"name": max(forms[k], key=lambda s: (forms[k][s], len(s))),
               "affiliation": max(affs[k], key=lambda s: (affs[k][s], len(s))),
               "born": (sorted(born[k])[len(born[k]) // 2] if born.get(k) else None),
               "key": k, "weight": round(w[k], 4), "n_nominations": cnt[k]}
              for k in sorted(w, key=lambda k: (-w[k], -cnt[k], k))]
    chosen = [n for n in c if n["id"] in wording_from]
    best = chosen[0] if chosen else max(c, key=lambda n: (n["points"] / nv[n["provider"]], -PROVIDERS.index(n["provider"]), n["member"]))
    codes = {}
    for n in c:
        codes[n["jel_code"]] = codes.get(n["jel_code"], 0) + 1
    return best["contribution"], people, max(codes, key=codes.get)


def cmd_collect(a):
    if not list(RAW.glob("*/*__b*.json")):
        sys.exit("no raw cells; run first")
    for f in ASKED:
        d = field_dir(f["slug"])
        d.mkdir(parents=True, exist_ok=True)
        n = nv = 0
        with (d / "ballots.jsonl").open("w", encoding="utf-8") as fh:
            for p in PROVIDERS:
                for m in MEMBERS:
                    path = raw_path(p, m, f["batch"])
                    if path.exists():
                        r = json.loads(path.read_text())
                        fin = r["final"]
                        row = {"provider": r["provider"], "model": r["model"], "member": r["member"], "name": r["name"],
                               "role": r["role"], "batch": f["batch"], "valid": fin["valid"],
                               "nominations": fin["nominations"].get(f["name"], []) if fin["valid"] else [],
                               "warnings": [w for w in fin["warnings"] if w.startswith(f["name"])],
                               "missing_reason": fin["missing_reason"], "model_reported": fin["model_reported"]}
                    else:
                        row = {"provider": p, "model": MODEL[p], "member": m, "name": MEMBERS[m]["name"], "role": MEMBERS[m]["role"],
                               "batch": f["batch"], "valid": False, "nominations": [], "warnings": [],
                               "missing_reason": ["not asked"], "model_reported": None}
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    n += 1
                    nv += row["valid"]
        print(f"{f['slug']:<14} batch {f['batch']}: {n} ballots -> committee/{f['slug']}/ballots.jsonl ({nv} valid)")


def cmd_aggregate(a):
    laureates = laureate_names()
    committee_names = [m['name'] for m in ROSTER]
    for fslug in (a.fields or [f["slug"] for f in ASKED]):
        f = FIELD_BY_SLUG[fslug]
        manual = load_manual(fslug)
        ballots, noms = load_ballots(fslug, manual["aliases"])
        clusters = make_clusters(noms, manual)
        nv = n_valid(ballots)
        ranked = sorted(range(len(clusters)), key=lambda i: (-score(clusters[i], nv)[0],
                                                             -len({n["provider"] for n in clusters[i]}),
                                                             -len({n["member"] for n in clusters[i]}), clusters[i][0]["id"]))
        opts = []
        for rank, i in enumerate(ranked, 1):
            c = clusters[i]
            total, per = score(c, nv)
            contribution, people, code = describe(c, nv, {w["id"] for w in manual["wording_from"]})
            dead = {q["name"]: note for q in people for name, note in manual["deceased"].items() if same_person(name, q["name"])}
            people = [q for q in people if q["name"] not in dead] + [q for q in people if q["name"] in dead]
            flags = [f"{name}: deceased ({note}); not shown" for name, note in dead.items()]
            flags += flag_people(people[:C["max_people"]], laureates, committee_names, manual["person_notes"])
            flags += flag_awarded([n["contribution"] for n in c], f["name"])
            if not code_in_field(code, f["name"]):
                flags.append(f"most frequent code {code} is outside the field's groups")
            supporters = sorted({(n["name"], ROLE_SHORT[n["role"]], SHORT[n["provider"]]) for n in c})
            by_member = {}
            for n in c:
                by_member.setdefault(n["name"], set()).add(SHORT[n["provider"]])
            opts.append({"rank": rank, "field": f["name"],
                         "option": f"{contribution} — {', '.join(p['name'] for p in people[:C['max_people']] if p['name'] not in dead)}",
                         "contribution": contribution, "jel_code": code, "score": round(total, 4),
                         "points_per_model": {MODEL[p]: round(per[p], 4) for p in PROVIDERS},
                         "n_models": len({n["provider"] for n in c}), "n_members": len(by_member),
                         "n_nominations": len(c),
                         "supporters": [f"{name} ({', '.join(sorted(ms))})" for name, ms in sorted(by_member.items())],
                         "roles": sorted({ROLE_SHORT[n["role"]] for n in c}),
                         "people": [{k: p[k] for k in ("name", "affiliation", "born", "weight", "n_nominations", "key")} for p in people[:C["max_people"]]],
                         "people_all": [{k: p[k] for k in ("name", "affiliation", "born", "weight", "n_nominations", "key")} for p in people],
                         "nomination_ids": [n["id"] for n in c], "flags": flags})
        out = {"field": f["name"], "slug": fslug, "generated": now(), "models": MODEL,
               "valid_ballots_per_model": {MODEL[p]: nv[p] for p in PROVIDERS},
               "normalization": "Borda 5..1 per ballot; each model's points divided by its number of valid ballots in the field, summed over models",
               "options": opts}
        (field_dir(fslug) / "candidates.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        write_review(fslug, ballots, noms, clusters, opts, manual)
        print(f"{fslug}: {len(noms)} nominations -> {len(clusters)} options; committee/{fslug}/candidates.json, review.md")
        for o in opts[:8]:
            print(f"  {o['rank']:>2}. {o['score']:.3f} m={o['n_models']} members={o['n_members']} {o['option'][:110]}")


def write_review(fslug, ballots, noms, clusters, opts, manual):
    f = FIELD_BY_SLUG[fslug]
    L = [f"# Virtual committee review — {f['name']} (2026 economics prize)", "",
         f"Generated {now()} by `virtual_committee.py aggregate` from `ballots.jsonl`. Score = model-balanced Borda "
         "(5..1 per ballot, each model's points divided by its number of valid ballots in this field). Supporters = "
         "members whose ballots (on the models in brackets) contain a nomination of the option. The nominations are a "
         "simulation reconstructed from the members' published records, not the members' views.", "",
         "## Ballots", "", "| model | valid | missing | ballots with warnings |", "|---|---|---|---|"]
    for p in PROVIDERS:
        bs = [b for b in ballots if b["provider"] == p]
        L.append(f"| {MODEL[p]} | {sum(b['valid'] for b in bs)} | {sum(not b['valid'] for b in bs)} | {sum(bool(b.get('warnings')) for b in bs)} |")
    miss = [b for b in ballots if not b["valid"]]
    if miss:
        L += ["", "Missing cells: " + "; ".join(f"{b['model']} / {b['name']}: {b['missing_reason']}" for b in miss)]
    warn = [(b, w) for b in ballots if b["valid"] for w in b.get("warnings", [])]
    if warn:
        L += ["", "Warnings: " + "; ".join(f"{SHORT[b['provider']]} / {b['name']}: {w}" for b, w in warn)]
    L += ["", f"## Options ({len(opts)}; {len(noms)} nominations)", ""]
    for o in opts:
        L += [f"### {o['rank']}. {o['option']}", "",
              f"score {o['score']:.3f} (per model {', '.join(f'{SHORT[p]} {o['points_per_model'][MODEL[p]]:.2f}' for p in PROVIDERS)}); "
              f"{o['n_models']} models, {o['n_members']} members ({', '.join(o['roles'])}), {o['n_nominations']} nominations; code {o['jel_code']}",
              "", "supporters: " + "; ".join(o["supporters"]), ""]
        if o["people_all"]:
            L += ["people: " + "; ".join(f"{p['name']} ({p['affiliation']}; b. {p['born'] or '?'}; w {p['weight']:.2f}, n {p['n_nominations']})" for p in o["people_all"]), ""]
        for n in sorted([n for n in noms if n["id"] in set(o["nomination_ids"])], key=lambda n: (-n["points"], n["id"])):
            L.append(f"- `{n['id']}` {n['name']} ({ROLE_SHORT[n['role']]}, {SHORT[n['provider']]}) rank {n['rank']} [{n['jel_code']}]: "
                     f"\"{n['contribution']}\" — {', '.join(p['name'] for p in n['people'])}. {n['rationale']}")
        for fl in o["flags"]:
            L.append(f"- FLAG: {fl}")
        L.append("")
    if any(manual[k] for k in ("split", "merge", "aliases", "wording_from", "people", "deceased", "person_notes")):
        L += ["## merges.yaml", "", "```yaml", yaml.safe_dump(manual, sort_keys=False, allow_unicode=True).strip(), "```", ""]
    (field_dir(fslug) / "review.md").write_text("\n".join(L))


def cmd_pool(a):
    rows = []
    for f in ASKED:
        if a.source == "claude":
            d = load_integrated(f["slug"])
            opts = [{**o, "contribution": o["motivation"], "option": f"{o['motivation']} — {', '.join(p['name'] for p in o['people'])}",
                     "flags": [x for x in o["flags"] if not x.startswith("named in the nominations but cannot")], "field_rank": o["rank"]}
                    for o in d["candidates"]]
        else:
            path = field_dir(f["slug"]) / "candidates.json"
            if not path.exists():
                sys.exit(f"{path} missing; aggregate first")
            opts = json.loads(path.read_text())["options"]
        shown = [o for o in opts if o["people"] and not any("already a laureate" in fl or "member of the 2026 committee" in fl for fl in o["flags"])]
        for k, o in enumerate(shown[:f["pool"]], 1):
            rows.append({"field": f["name"], "main_pct": f["main_pct"], "pool": f["pool"], "rank_in_field": k,
                         "option": o["option"], "contribution": o["contribution"], "jel_code": o["jel_code"],
                         "people": "; ".join(p["name"] for p in o["people"]),
                         "born": "; ".join(str(p["born"] or "?") for p in o["people"]),
                         "score": o["score"], "n_models": o["n_models"], "n_members": o["n_members"],
                         "roles": ", ".join(o["roles"]), "flags": " | ".join(o["flags"]), "field_rank": o["rank"]})
    P = pd.DataFrame(rows)
    RESULTS.mkdir(exist_ok=True)
    P.to_csv(RESULTS / "pool.csv", index=False)
    dup = {}
    for r in rows:
        for name in r["people"].split("; "):
            k = person_key(name)
            if k:
                dup.setdefault(k, []).append((r["field"], r["rank_in_field"], name))
    L = [f"# Candidate pool for the people question ({len(P)} options; source {a.source}; generated {now()})", "",
         f"Pool sizes in proportion to the Preseen main-arm probability of the field (total {SET['pool_total']}): "
         + ", ".join(f"{f['name']} {f['pool']} ({f['main_pct']} %)" for f in ASKED) + ".", ""]
    for f in ASKED:
        L += [f"## {f['name']} ({f['pool']} options)", ""]
        for r in [r for r in rows if r["field"] == f["name"]]:
            L.append(f"{r['rank_in_field']}. {r['option']}  — score {r['score']:.2f}, {r['n_models']} models, {r['n_members']} members"
                     + (f"; FLAGS: {r['flags']}" if r["flags"] else ""))
        L.append("")
    cross = {k: v for k, v in dup.items() if len({x[0] for x in v}) > 1}
    if cross:
        L += ["## People in options of more than one field", ""] + [f"- {v[0][2]}: " + "; ".join(f"{fld} #{rk}" for fld, rk, _ in v) for v in cross.values()] + [""]
    (RESULTS / "pool.md").write_text("\n".join(L))
    print(P[["field", "rank_in_field", "score", "n_models", "n_members", "option"]].to_string(max_colwidth=90))
    print(f"written results/pool.csv, pool.md ({len(P)} options; {len(cross)} people in more than one field)")


# ---------------------------------------------------------------- integration by Claude (one call per field)

INTEGRATE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nominations": {"type": "array", "items": {"type": "string"}},
                    "motivation": {"type": "string"},
                    "jel_code": {"type": "string"},
                    "people": {"type": "array", "items": {"type": "string"}},
                    "defining_works": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"work": {"type": "string"}, "people": {"type": "array", "items": {"type": "string"}}},
                            "required": ["work", "people"],
                            "additionalProperties": False,
                        },
                    },
                    "reasoning": {"type": "string"},
                    "grouping_note": {"type": "string"},
                },
                "required": ["nominations", "motivation", "jel_code", "people", "defining_works", "reasoning", "grouping_note"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["candidates"],
    "additionalProperties": False,
}

INTEGRATE_SYSTEM = """You integrate the nominations of a virtual prize committee for one field of economics. Eleven personas, each a reconstruction of a member of the 2026 Committee for the Prize in Economic Sciences in Memory of Alfred Nobel, submitted ranked ballots independently on three different language models; each ballot nominated up to five contributions in the field, each with one to three people. You merge these nominations into one list of distinct candidates, as a committee secretary would before the deliberation. You do not rank or score the candidates: support is counted afterwards from the nominations you assign to each.

- Use only what the nominations say. Do not add contributions, people, works or facts from your own knowledge. Defining works come only from the key works listed in the candidate's own nominations, copied as written there.
- A candidate is one contribution that a single prize motivation could award to at most three people. Put nominations into the same candidate when they describe the same body of work, even if they word it differently or name a different subset of its people.
- Keep nominations apart when they describe different contributions, even if they share a person; the same person may appear in several candidates. Do not build umbrella candidates that join distinct contributions of the field (for example two research programmes that only share one author).
- Nominations on the same ballot were submitted as different contributions. Put two of them into one candidate only if they plainly describe the same contribution.
- A nomination that spans two candidates goes to the one that matches its core contribution and its lead people.
- Every nomination id appears in exactly one candidate. A nomination that matches no other forms a candidate of its own."""


def integrate_inputs(fslug):
    """Valid nominations of the field with short ids (n001..) and anonymous ballot labels (b01..), the input stamp, and
    the named people who cannot be awarded (sitting committee members, previous laureates)."""
    ballots, noms = load_ballots(fslug)
    labels = {}
    for k, n in enumerate(noms, 1):
        n["sid"] = f"n{k:03d}"
        n["ballot"] = labels.setdefault((n["provider"], n["member"]), f"b{len(labels) + 1:02d}")
    stamp = hashlib.sha256(json.dumps([(n["id"], n["contribution"], [p["name"] for p in n["people"]]) for n in noms],
                                      ensure_ascii=False).encode()).hexdigest()[:16]
    laureates, committee_names = laureate_names(), [m["name"] for m in ROSTER]
    inel = {}
    for n in noms:
        for p in n["people"]:
            for name in committee_names:
                if same_person(p["name"], name):
                    inel[p["name"]] = "member of the 2026 committee; cannot be awarded while serving"
            for name in laureates:
                if same_person(p["name"], name):
                    inel[p["name"]] = f"previous laureate of this prize ({name})"
    return ballots, noms, stamp, inel


def integrate_prompt(fslug, noms, inel):
    f = FIELD_BY_SLUG[fslug]

    def line(n):
        ppl = "; ".join(f"{p['name']} ({p['affiliation']}, b. {p['born']})" for p in n["people"])
        works = "; ".join(n["key_works"]) or "none given"
        return (f"{n['sid']} | ballot {n['ballot']} | rank {n['rank']} | {n['jel_code']} | {n['contribution']} | "
                f"people: {ppl} | key works: {works} | rationale: {n['rationale']}")
    lines = [SET["date_context"], "",
             f"Field: {f['name']}", f["definition"], "",
             f"Nominations: {len(noms)} from {len({n['ballot'] for n in noms})} ballots. Each line gives the id, the "
             "ballot, the rank on that ballot (1 = strongest), the JEL code, the contribution, the people (affiliation, "
             "year of birth as stated), the key works and the rationale.", ""]
    lines += [line(n) for n in noms]
    lines += ["", "People named in the nominations who cannot be awarded (leave them out of every lineup and mention "
              "them in the grouping note of the candidate):"]
    lines += [f"- {name}: {why}" for name, why in sorted(inel.items())] or ["- (none)"]
    lines += ["", "For every candidate give:",
              "- \"nominations\": the ids of its nominations;",
              "- \"motivation\": one line in the style of an official motivation (\"for ...\") that states what its "
              "nominations share;",
              "- \"jel_code\": the JEL level-3 code of its core, from the codes its nominations use;",
              f"- \"people\": the lineup of one to {C['max_people']} people that its nominations support most, chosen only "
              "from the people they name and spelled as there; leave out the people listed above as unable to be "
              "awarded (an empty list only if its nominations name no one else);",
              f"- \"defining_works\": up to {SET['integrate']['max_defining_works']} works that define the contribution, chosen "
              "from the key works of its nominations (prefer those listed by several nominations and those that show "
              "the contribution of each person in the lineup) and copied exactly as written there, each with \"people\": "
              "the people of the lineup whose work it is; an empty list only if its nominations list no works;",
              "- \"reasoning\": at most three sentences, drawn from the rationales: why the nominations support the "
              "candidate and the main reservation they raise, if any;",
              "- \"grouping_note\": one sentence on what was joined and on any tension (rival lineups, a broad "
              "nomination that also touches another candidate, a person left out of the lineup); \"\" for a candidate "
              "with a single nomination.",
              "",
              "Answer with one JSON object of this form and nothing else, listing every nomination id exactly once:",
              '{"candidates": [{"nominations": ["n001", "n017"], "motivation": "for ...", "jel_code": "E52", '
              '"people": ["...", "..."], "defining_works": [{"work": "Author(s), year: title, venue", "people": ["..."]}], '
              '"reasoning": "...", "grouping_note": "..."}, ...]}']
    return INTEGRATE_SYSTEM, "\n".join(lines)


def work_title(w):
    """Normalized title of a key work written as 'Author(s), year: title, venue' (whole string if no colon)."""
    t = w.split(":", 1)[1] if ":" in w else w
    return " ".join(re.findall(r"[a-z0-9]+", fold(t)))


def same_work(a, b):
    ta, tb = work_title(a), work_title(b)
    if not ta or not tb:
        return False
    head = lambda t: " ".join(t.split()[:6])
    return head(ta) == head(tb) or difflib.SequenceMatcher(None, ta, tb).ratio() >= 0.8


def validate_integration(obj, noms, inel):
    """(errors, warnings). Errors: every id exactly once, no unknown ids, a motivation, 0-3 people each named in the
    candidate's nominations (0 only if all of them are unable to be awarded), works as a list. Warnings: an ineligible
    person in a lineup, a defining work that is not among the key works of the candidate's nominations."""
    sid = {n["sid"]: n for n in noms}
    cands = obj.get("candidates") if isinstance(obj, dict) else None
    if not isinstance(cands, list) or not cands:
        return ["top level must be an object with a non-empty 'candidates' list"], []
    errs, warns, seen = [], [], {}
    for i, c in enumerate(cands, 1):
        ids = c.get("nominations") if isinstance(c, dict) else None
        if not isinstance(ids, list) or not ids:
            errs.append(f"candidate {i}: no nominations")
            continue
        for x in ids:
            if x not in sid:
                errs.append(f"candidate {i}: unknown nomination id {x!r}")
            elif x in seen:
                errs.append(f"nomination {x} is in candidates {seen[x]} and {i}")
            else:
                seen[x] = i
        if not str(c.get("motivation", "")).strip():
            errs.append(f"candidate {i}: empty motivation")
        named = [p["name"] for x in ids if x in sid for p in sid[x]["people"]]
        eligible = [q for q in named if not any(same_person(q, b) for b in inel)]
        people = c.get("people")
        if not isinstance(people, list) or len(people) > C["max_people"] or (not people and eligible):
            errs.append(f"candidate {i}: people must list 1 to {C['max_people']} names")
            continue
        for name in people:
            if not any(same_person(name, q) for q in named):
                errs.append(f"candidate {i}: {name!r} is not named in its nominations")
            elif any(same_person(name, b) for b in inel):
                warns.append(f"candidate {i}: {name} is in the lineup but cannot be awarded")
        works = c.get("defining_works")
        listed = [w for x in ids if x in sid for w in sid[x]["key_works"]]
        if not isinstance(works, list) or (not works and listed):
            errs.append(f"candidate {i}: defining_works must list 1 to {SET['integrate']['max_defining_works']} works from its nominations")
            continue
        for w in works:
            if not any(same_work(w.get("work", ""), v) for v in listed):
                warns.append(f"candidate {i}: defining work not among its nominations' key works: {w.get('work', '')[:80]}")
    missing = [x for x in sid if x not in seen]
    if missing:
        errs.append(f"{len(missing)} nomination ids in no candidate: {', '.join(missing[:25])}{' ...' if len(missing) > 25 else ''}")
    return errs[:30], warns


def integrated_path(fslug):
    return field_dir(fslug) / "integrated.json"


def run_integration(fslug, force=False, dry_run=False):
    ballots, noms, stamp, inel = integrate_inputs(fslug)
    path = integrated_path(fslug)
    if path.exists() and not force and not dry_run:
        old = json.loads(path.read_text())
        if old.get("stamp") == stamp:
            return old, "exists (ballots unchanged; not re-asked)"
    system, user = integrate_prompt(fslug, noms, inel)
    if dry_run:
        PROMPTS.mkdir(exist_ok=True)
        (PROMPTS / f"integrate_{fslug}.md").write_text(f"# System\n\n{system}\n\n# User\n\n{user}\n")
        return None, f"dry run: {len(noms)} nominations, {len(system) + len(user):,} characters -> prompts/integrate_{fslug}.md"
    provider = SET["integrate"]["provider"]
    attempts, errs, warns, parsed, ask = [], ["not asked"], [], None, user
    for _ in range(1 + SET["integrate"]["json_retries"]):
        res = llm.call_json(provider, MODEL[provider], system, ask, INTEGRATE_SCHEMA, SET["integrate"]["max_output_tokens"],
                            effort=SET["integrate"]["effort"])
        log_call("integrate", fslug, provider, res)
        res = {k: v for k, v in res.items() if k != "request"}
        if res["error"]:
            errs, parsed = [f"HTTP: {res['error']}"], None
            attempts.append({**res, "errors": errs})
            break
        parsed = res["parsed"]
        errs, warns = validate_integration(parsed, noms, inel) if parsed is not None else ([res["parse_error"] or "no JSON text"], [])
        if res["truncated"]:
            errs = errs + [f"truncated (stop={res['stop']})"]
        attempts.append({**res, "errors": errs, "warnings": warns, "retry_note": ask != user})
        if not errs:
            break
        ask = (user + "\n\nYour previous answer was invalid for these reasons:\n" + "\n".join(f"- {e}" for e in errs)
               + "\nAnswer again in full, following every instruction.")
    raw = {"field": FIELD_BY_SLUG[fslug]["name"], "slug": fslug, "written": now(), "stamp": stamp,
           "model": MODEL[provider], "prompt": {"system": system, "user": user}, "schema": INTEGRATE_SCHEMA,
           "ids": {n["sid"]: n["id"] for n in noms}, "ineligible": inel, "attempts": attempts,
           "valid": not errs, "errors": errs, "warnings": warns}
    INTEGRATED_RAW.mkdir(parents=True, exist_ok=True)
    (INTEGRATED_RAW / f"{fslug}.json").write_text(json.dumps(raw, indent=1, ensure_ascii=False))
    if errs:
        return None, f"INVALID after {len(attempts)} attempt(s): {'; '.join(errs[:4])}"
    out = build_integrated(fslug, ballots, noms, stamp, inel, parsed, warns, attempts, provider)
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    write_integrated_review(fslug, out, noms)
    return out, f"asked ({len(attempts)} attempt(s), ${sum(usd(provider, a.get('usage')) for a in attempts):.2f})"


def build_integrated(fslug, ballots, noms, stamp, inel, parsed, warns, attempts, provider):
    """Local support for Claude's grouping: model-balanced Borda score, models, members, per-person support, flags."""
    f = FIELD_BY_SLUG[fslug]
    nv, sid = n_valid(ballots), {n["sid"]: n for n in noms}
    laureates, committee_names = laureate_names(), [m["name"] for m in ROSTER]
    cands = []
    for c in parsed["candidates"]:
        group = [sid[x] for x in c["nominations"]]
        total, per = score(group, nv)
        _, people_all, code_mode = describe(group, nv)
        lineup = []
        for name in c["people"]:
            hits = [(n, p) for n in group for p in n["people"] if same_person(name, p["name"])]
            borns = sorted(int(p["born"]) for _, p in hits if p["born"].isdigit())
            affs = Counter(p["affiliation"] for _, p in hits)
            lineup.append({"name": name, "born": borns[len(borns) // 2] if borns else None,
                           "affiliation": affs.most_common(1)[0][0] if affs else "",
                           "n_nominations": len({n["id"] for n, _ in hits}),
                           "models": " ".join(SHORT[q] for q in PROVIDERS if any(n["provider"] == q for n, _ in hits)),
                           "weight": round(sum(n["points"] / nv[n["provider"]] for n, _ in {n["id"]: (n, p) for n, p in hits}.values()), 4)})
        others = [p for p in people_all if not any(same_person(p["name"], q["name"]) for q in lineup)]
        works = []
        for w in c["defining_works"][:SET["integrate"]["max_defining_works"]]:
            cited = [n for n in group if any(same_work(w["work"], v) for v in n["key_works"])]
            works.append({"work": w["work"].strip(), "people": w["people"], "n_nominations": len(cited),
                          "models": " ".join(SHORT[q] for q in PROVIDERS if any(n["provider"] == q for n in cited)),
                          "in_nominations": bool(cited)})
        flags = flag_people(lineup, laureates, committee_names)
        flags += [f"named in the nominations but cannot be awarded: {name} ({why})" for name, why in inel.items()
                  if any(same_person(name, p["name"]) for n in group for p in n["people"])]
        flags += flag_awarded([c["motivation"]] + [n["contribution"] for n in group], f["name"])
        flags += [f"defining work not found in the nominations: {w['work'][:80]}" for w in works if not w["in_nominations"]]
        by_member = {}
        for n in group:
            by_member.setdefault(n["name"], set()).add(SHORT[n["provider"]])
        cands.append({"motivation": c["motivation"].strip(), "jel_code": c["jel_code"].strip().upper(), "jel_code_mode": code_mode,
                      "score": round(total, 4), "points_per_model": {MODEL[q]: round(per[q], 4) for q in PROVIDERS},
                      "models": " ".join(SHORT[q] for q in PROVIDERS if per[q] > 0),
                      "n_models": len({n["provider"] for n in group}), "n_members": len(by_member), "n_nominations": len(group),
                      "nominations_per_model": {SHORT[q]: sum(n["provider"] == q for n in group) for q in PROVIDERS},
                      "supporters": [f"{name} ({', '.join(sorted(ms))})" for name, ms in sorted(by_member.items())],
                      "roles": sorted({ROLE_SHORT[n["role"]] for n in group}),
                      "people": lineup,
                      "people_others": [{k: p[k] for k in ("name", "affiliation", "born", "weight", "n_nominations")} for p in others],
                      "defining_works": works, "reasoning": c["reasoning"].strip(), "grouping_note": c["grouping_note"].strip(),
                      "nomination_ids": [n["id"] for n in group], "flags": flags})
    cands.sort(key=lambda o: (-o["score"], -o["n_models"], -o["n_members"], o["nomination_ids"][0]))
    for k, o in enumerate(cands, 1):
        o["rank"] = k
    return {"field": f["name"], "slug": fslug, "generated": now(), "integrator": MODEL[provider], "stamp": stamp,
            "models": MODEL, "valid_ballots_per_model": {MODEL[q]: nv[q] for q in PROVIDERS},
            "n_nominations": len(noms), "n_candidates": len(cands),
            "normalization": "Borda 5..1 per ballot; each model's points divided by its number of valid ballots in the field, summed over models (max 15)",
            "warnings": warns,
            "call": {"attempts": len(attempts), "usd": round(sum(usd(provider, a.get("usage")) for a in attempts), 4),
                     "usage": [a.get("usage") for a in attempts]},
            "candidates": [{"rank": o.pop("rank"), **o} for o in cands]}


def fmt_person(p, n_group=None):
    born = f"b. {p['born']}" if p.get("born") else "birth year not stated"
    aff = f", {p['affiliation']}" if p.get("affiliation") else ""
    sup = f"; named in {p['n_nominations']} of {n_group} nominations" if n_group else ""
    return f"{p['name']} ({born}{aff}{sup})"


def write_integrated_review(fslug, out, noms):
    by_id = {n["id"]: n for n in noms}
    L = [f"# Integrated candidates — {out['field']} (2026 economics prize)", "",
         f"Generated {out['generated']} by `virtual_committee.py integrate`: {out['integrator']} grouped {out['n_nominations']} "
         f"nominations of the three models into {out['n_candidates']} candidates (motivation, lineup, defining works, reasoning, grouping note); "
         "scores, supporters, per-person support and flags are computed locally. Valid ballots per model: "
         + ", ".join(f"{m} {k}" for m, k in out["valid_ballots_per_model"].items()) + ".", ""]
    if out["warnings"]:
        L += ["Warnings: " + "; ".join(out["warnings"]), ""]
    for o in out["candidates"]:
        L += [f"## {o['rank']}. {o['motivation']} [{o['jel_code']}]", "",
              f"score {o['score']:.2f} (A {o['points_per_model'][MODEL['anthropic']]:.2f}, O {o['points_per_model'][MODEL['openai']]:.2f}, "
              f"G {o['points_per_model'][MODEL['gemini']]:.2f}); models {o['models']}; {o['n_members']} members; {o['n_nominations']} nominations",
              "", "lineup: " + "; ".join(fmt_person(p, o["n_nominations"]) for p in o["people"]),
              "", "others named: " + ("; ".join(f"{p['name']} ({p['n_nominations']})" for p in o["people_others"]) or "none"),
              "", "defining works: " + ("; ".join(f"{w['work']} [{', '.join(w['people']) or '-'}; listed by {w['n_nominations']}]" for w in o["defining_works"]) or "none"),
              "", f"reasoning: {o['reasoning']}", "", f"grouping note: {o['grouping_note'] or '-'}", ""]
        for i in o["nomination_ids"]:
            n = by_id[i]
            L.append(f"- `{i}` {n['name']} ({SHORT[n['provider']]}) rank {n['rank']} [{n['jel_code']}]: \"{n['contribution']}\" — "
                     + ", ".join(p["name"] for p in n["people"]))
        L += [f"- FLAG: {fl}" for fl in o["flags"]] + [""]
    (field_dir(fslug) / "integrated.md").write_text("\n".join(L))


def load_integrated(fslug):
    """integrated.json if it exists and was built from the current ballots, else exit with the reason."""
    path = integrated_path(fslug)
    if not path.exists():
        sys.exit(f"{path} missing; run integrate first")
    d = json.loads(path.read_text())
    stamp = integrate_inputs(fslug)[2]
    if d["stamp"] != stamp:
        sys.exit(f"{path} was built from other ballots (stamp {d['stamp']} vs {stamp}); run integrate again")
    return d


def cmd_integrate(a):
    fslugs = a.fields or [f["slug"] for f in ASKED]
    with ThreadPoolExecutor(max_workers=SET["integrate"]["workers"]) as ex:
        res = dict(zip(fslugs, ex.map(lambda s: run_integration(s, force=a.force, dry_run=a.dry_run), fslugs)))
    for s, (out, how) in res.items():
        print(f"{s}: {how}")
        if out:
            for o in out["candidates"][:8]:
                print(f"  {o['rank']:>2}. {o['score']:5.2f} {o['models']:<5} m={o['n_members']:>2} n={o['n_nominations']:>3} "
                      f"{o['motivation'][:70]} — {', '.join(p['name'] for p in o['people'])}")
    if not a.dry_run and any(out is None for out, _ in res.values()):
        sys.exit("some fields are not integrated")


def cmd_context(a):
    """Preseen context notes in English: 06_00 = how the lists were made, 06_<ii> = the integrated candidates of field ii
    (the order of settings.yaml)."""
    data = {f["slug"]: load_integrated(f["slug"]) for f in ASKED}
    nv_all = {MODEL[q]: sum(1 for m in MEMBERS for b in ASK_BATCHES if raw_path(q, m, b).exists()
                            and json.loads(raw_path(q, m, b).read_text())["final"]["valid"]) for q in PROVIDERS}
    roster = ", ".join(f"{m['name']}" + (f" ({m['role']})" if m["role"] in ("chair", "secretary") else "") for m in ROSTER)
    CONTEXT.mkdir(exist_ok=True)
    for old in CONTEXT.glob("06_*.md"):
        old.unlink()
    method = [
        "# Virtual committee candidates for the 2026 Prize in Economic Sciences: how the lists were made", "",
        f"The notes 06_01 to 06_{len(ASKED):02d} list candidate contributions and people for the {len(ASKED)} fields that the "
        "latest field forecast (10 October 2026, Preseen main arm) rated most likely: "
        + ", ".join(f"{f['name']} ({f['main_pct']} %)" for f in ASKED) + "; one note per field.", "",
        f"- Source: a simulated committee. Eleven personas, each reconstructed from the published research record of one member "
        f"of the real 2026 prize committee ({roster}), nominated on three language models without web access "
        f"(A = {MODEL['anthropic']}, O = {MODEL['openai']}, G = {MODEL['gemini']}), "
        + ("one request covering these fields" if len(ASK_BATCHES) == 1 else f"{len(ASK_BATCHES)} requests of four or five fields each")
        + ": up to five ranked contributions per field, "
        "each with one to three living people, excluding previous laureates and contributions already awarded. The nominations "
        "are inferences from the members' records, not the members' views; nobody on the real committee was consulted.",
        f"- Requests: {sum(nv_all.values())} of {len(MEMBERS) * len(PROVIDERS) * len(ASK_BATCHES)} member-model requests "
        "answered validly (" + ", ".join(f"{SHORT[q]} {nv_all[MODEL[q]]}" for q in PROVIDERS) + "); the valid ballots of "
        "each field are counted in its note.",
        f"- Integration: {data[ASKED[0]['slug']]['integrator']} grouped the nominations of the three models that propose the "
        "same contribution into one candidate, wrote one motivation line, and chose the lineup (at most three people) that its "
        "nominations support most, the defining works (taken from the key publications the nominations list; 'listed by' = how "
        "many of the candidate's nominations list the work) and the committee's reasoning (from the rationales of the "
        "nominations, including reservations). It used only the nominations, and it left sitting committee members and "
        "previous laureates out of the lineups.",
        "- Support is counted, not judged: score = Borda points 5 to 1 by rank on each ballot, each model's points divided by "
        "its number of valid ballots in the field and summed over the three models (maximum 15, reached only if every ballot "
        "of every model ranks the candidate first). Models = which of A, O and G nominated it; members = how many of the eleven "
        "personas nominated it on at least one model; for each person, the number of the candidate's nominations that name "
        "that person.",
        "- Birth years are the ones the models stated, taken as the median over nominations; they and the living status of the "
        "people were not checked against an external source. A member of the 2026 committee cannot be awarded while serving.",
    ]
    (CONTEXT / "06_00_committee_method.md").write_text("\n".join(method) + "\n")
    for i, f in enumerate(ASKED, 1):
        d = data[f["slug"]]
        L = [f"# Virtual committee candidates: {f['name']} (JEL {f['jel']})", "",
             f"Field forecast (latest Preseen field run, main arm, 10 October 2026): {f['main_pct']} %. {f['definition']}", "",
             f"{d['n_nominations']} nominations on {sum(d['valid_ballots_per_model'].values())} valid ballots ("
             + ", ".join(f"{SHORT[q]} {d['valid_ballots_per_model'][MODEL[q]]}" for q in PROVIDERS)
             + f") integrated into {d['n_candidates']} candidates, ranked by support score (maximum 15).", ""]
        for o in d["candidates"]:
            npm = o["nominations_per_model"]
            L += [f"{o['rank']}. {o['motivation']} [{o['jel_code']}]",
                  "   People: " + ("; ".join(fmt_person(p, o["n_nominations"]) for p in o["people"]) or "none eligible"),
                  f"   Support: score {o['score']:.2f}; models {o['models']}; {o['n_members']} of {len(MEMBERS)} members; "
                  f"{o['n_nominations']} nominations (" + ", ".join(f"{k} {v}" for k, v in npm.items()) + ")"]
            others = [p for p in o["people_others"] if p["n_nominations"] >= 2][:4]
            if others:
                L.append("   Also named: " + "; ".join(f"{p['name']} ({p['n_nominations']})" for p in others))
            for w in o["defining_works"]:
                L.append(f"   Defining work: {w['work']}" + (f" ({', '.join(w['people'])})" if w["people"] else "")
                         + f"; listed by {w['n_nominations']} of its nominations")
            L.append(f"   Committee's reasoning: {o['reasoning']}")
            fl = [x for x in o["flags"] if not x.startswith("resembles")]
            if fl:
                L.append("   Notes: " + "; ".join(fl))
            L.append("")
        (CONTEXT / f"06_{i:02d}_{f['slug']}.md").write_text("\n".join(L))
    sizes = {p.name: len(p.read_text()) for p in sorted(CONTEXT.glob("06_*.md"))}
    for k, v in sizes.items():
        print(f"context/{k}: {v:,} characters")


# ---------------------------------------------------------------- commands: prompt, test, run, estimate, status

def cmd_prompt(a):
    m, system, user = prompt(a.member, a.batch)
    PROMPTS.mkdir(exist_ok=True)
    (PROMPTS / f"example_{a.member}__b{a.batch}.md").write_text(f"# System\n\n{system}\n\n# User\n\n{user}\n")
    print("SYSTEM\n" + system + "\n\nUSER\n" + user)
    print(f"\n[{len(system) + len(user):,} characters; written to prompts/example_{a.member}__b{a.batch}.md]")


def cmd_test(a):
    base = COMMITTEE / "test" / "raw"
    for p in a.providers:
        rec, how = run_cell(a.member, p, a.batch, base=base, force=a.force, stage="test")
        print(cell_line(rec, how))
        if rec["final"]["valid"]:
            for fname, noms in rec["final"]["nominations"].items():
                print(f"  {fname}: " + " | ".join(f"#{n['rank']} {n['contribution'][:60]} — {', '.join(p['name'] for p in n['people'])}" for n in noms))
        if rec["final"]["warnings"]:
            print("  warnings:", "; ".join(rec["final"]["warnings"]))


def cmd_run(a):
    members = a.members or list(MEMBERS)
    batches = a.batches or ASK_BATCHES
    cells = [(m, p, b) for b in batches for m in members for p in a.providers]    # providers interleaved
    print(f"{len(cells)} calls ({len(members)} members x {len(a.providers)} models x {len(batches)} batches), {a.workers} workers", flush=True)

    def work(cell):
        m, p, b = cell
        rec, how = run_cell(m, p, b, force=a.force)
        with LOCK:
            print(cell_line(rec, how), flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        recs = list(ex.map(work, cells))
    print(f"valid {sum(r['final']['valid'] for r in recs)} / {len(recs)}")


def calls():
    if not (LOGS / "calls.jsonl").exists():
        return []
    return [json.loads(x) for x in (LOGS / "calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


def cmd_estimate(a):
    cs = calls()
    n_cells = len(MEMBERS) * len(ASK_BATCHES)
    total = 0
    print(f"{'model':<24} {'per call':>9} {'basis':<34} {'x cells':>8} {'USD':>8}")
    for p in PROVIDERS:
        seen = [c["usd"] for c in cs if c["provider"] == p and c["ok"] and c["stage"] in ("ballot", "test") and "__b" in c["member"]]
        if seen:
            per, basis = sum(seen) / len(seen), f"mean of {len(seen)} logged call(s)"
        else:
            per, basis = usd(p, SET["estimate_assumptions"]), f"assumption {SET['estimate_assumptions']}"
        total += per * n_cells
        print(f"{MODEL[p]:<24} {per:>9.3f} {basis:<34} {n_cells:>8} {per * n_cells:>8.2f}")
    print(f"total for {n_cells * len(PROVIDERS)} calls: ${total:.2f}; spent so far ${sum(c.get('usd') or 0 for c in cs):.2f} over {len(cs)} logged calls")


def cmd_status(a):
    rows = []
    for m in MEMBERS:
        for p in PROVIDERS:
            for b in ASK_BATCHES:
                path = raw_path(p, m, b)
                st = "-"
                if path.exists():
                    r = json.loads(path.read_text())
                    st = "valid" if r["final"]["valid"] else "MISSING"
                rows.append({"member": m, "call": f"{SHORT[p]}{b}", "cell": st})
    t = pd.DataFrame(rows).pivot(index="member", columns="call", values="cell")
    t = t[[f"{SHORT[p]}{b}" for p in PROVIDERS for b in ASK_BATCHES]]
    print(t.to_string())
    print(f"valid calls: {(t == 'valid').sum().sum()} / {t.size}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("prompt"); s.add_argument("--member", required=True); s.add_argument("--batch", type=int, choices=BATCHES, default=1)
    s.set_defaults(fn=cmd_prompt)
    s = sub.add_parser("test"); s.add_argument("--member", required=True); s.add_argument("--batch", type=int, choices=BATCHES, default=1)
    s.add_argument("--providers", nargs="+", default=list(PROVIDERS)); s.add_argument("--force", action="store_true"); s.set_defaults(fn=cmd_test)
    s = sub.add_parser("run"); s.add_argument("--members", nargs="*"); s.add_argument("--providers", nargs="+", default=list(PROVIDERS))
    s.add_argument("--batches", nargs="*", type=int, choices=BATCHES)
    s.add_argument("--workers", type=int, default=3); s.add_argument("--force", action="store_true"); s.set_defaults(fn=cmd_run)
    s = sub.add_parser("collect"); s.set_defaults(fn=cmd_collect)
    s = sub.add_parser("aggregate"); s.add_argument("--fields", nargs="*"); s.set_defaults(fn=cmd_aggregate)
    s = sub.add_parser("integrate"); s.add_argument("--fields", nargs="*"); s.add_argument("--force", action="store_true")
    s.add_argument("--dry-run", action="store_true"); s.set_defaults(fn=cmd_integrate)
    s = sub.add_parser("context"); s.set_defaults(fn=cmd_context)
    s = sub.add_parser("pool"); s.add_argument("--source", choices=["claude", "rule"], default="claude"); s.set_defaults(fn=cmd_pool)
    s = sub.add_parser("estimate"); s.set_defaults(fn=cmd_estimate)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    a = p.parse_args()
    for m in getattr(a, "members", None) or ([a.member] if getattr(a, "member", None) else []):
        if m not in MEMBERS:
            sys.exit(f"unknown member {m}; members: {', '.join(MEMBERS)}")
    a.fn(a)


if __name__ == "__main__":
    main()
