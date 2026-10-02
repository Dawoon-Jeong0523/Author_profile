#!/usr/bin/env python3
"""committee.py: the virtual Nobel committee (crossed persona x model design, SPEC §6).

    $PY committee.py prompt  --field medicine --persona 0   # print the exact prompt (free)
    $PY committee.py test [--providers gemini] [--force]    # one ballot per model for config committee.test (3 calls)
    $PY committee.py run     --fields medicine physics chemistry [--workers 2]   # every persona x model cell
    $PY committee.py collect --field medicine               # raw/ -> ballots.jsonl
    $PY committee.py estimate                               # cost of all committees from the test ballots' usage
    $PY committee.py aggregate --field medicine             # ballots.jsonl (+ merges.yaml) -> candidates.json, review.md

Every persona sees the same prompt on every model (llm_providers.call: no tools, no web search, no grounding, provider
defaults). A ballot that is not valid JSON for the schema is asked once more (config committee.json_retries); a cell
that still fails is written as missing. An existing raw file is never re-asked unless --force is given.
Outputs: committee/<field>/raw/<model>/<persona>.json (prompt, params, every attempt with response metadata, output),
committee/<field>/ballots.jsonl; the test goes to committee/test/raw/<model>/<persona>.json.
"""
import argparse
import datetime as dt
import json
import re
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import yaml

from llm_providers import call

HERE = Path(__file__).resolve().parent
CFG = yaml.safe_load((HERE / "config.yaml").read_text())
REPO = Path(CFG["repo_root"])
PROVIDERS = ("anthropic", "openai", "gemini")
COMMITTEE = HERE / "committee"
PRINT_LOCK = threading.Lock()

SCHEMA = {
    "type": "object",
    "properties": {
        "nominations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer"},
                    "discovery": {"type": "string"},
                    "people": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}, "affiliation": {"type": "string"}},
                            "required": ["name", "affiliation"],
                            "additionalProperties": False,
                        },
                    },
                    "key_papers": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": ["rank", "discovery", "people", "key_papers", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["nominations"],
    "additionalProperties": False,
}
# Count limits (5 nominations, 1-3 people, 3 papers, 2 sentences) are in the prompt and checked locally; they are not in
# the schema because the providers' JSON modes support different subsets of JSON Schema.


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------------------------------------------------------------- prompt (identical for every provider)

def prior_prizes(field):
    f = CFG["fields"][field]
    y0, y1 = CFG["committee"]["prior_prizes"]
    d = pd.read_csv(REPO / "Data/prizeatlas/prizeatlas_nobel_laureates.csv")
    d = d[(d.category_en == f["prizeatlas_category"]) & d.year.between(y0, y1)]
    lines = []
    for (year, _), g in sorted(d.groupby(["year", "award_group"]), key=lambda kv: (kv[0][0], kv[1].csv_award_record_id.min())):
        g = g.sort_values("csv_award_record_id")
        mot = g.motivation.iloc[0].strip()
        if mot.endswith("'") and mot.count("'") % 2:          # unmatched closing quote in the source (2002 Medicine)
            mot = mot[:-1]
        lines.append(f"- {year}: {mot} ({', '.join(g.name)})")
    return lines


def prompt(field, persona_idx):
    f, c = CFG["fields"][field], CFG["committee"]
    specialty = f["personas"][persona_idx]
    persona = c["persona_template"].format(prize=f["prize"], specialty=specialty)
    system = (f"You are {persona}. Like the real committee, which calls on expert advisers for areas outside its "
              f"members' own fields, you use your own expertise as a lens but consider discoveries from the whole of "
              f"{f['prize'].lower()}.")
    y0, y1 = c["prior_prizes"]
    user = "\n".join([
        c["date_context"],
        "",
        "The rules that matter:",
        f"- Alfred Nobel's will: the prize rewards \"{f['will_text']}\".",
        "- A prize is awarded to at most three people, and it is not awarded posthumously: every person you name must "
        "be living.",
        "- A prize may be divided between two discoveries, each considered worthy of a prize.",
        "",
        f"Nobel Prizes in {f['prize']} {y0}-{y1}, with their official motivations. These discoveries have already been "
        "awarded; do not nominate them again.",
        *prior_prizes(field),
        "",
        f"Your task: nominate up to {c['max_nominations']} discoveries for the 2026 Nobel Prize in {f['prize']}, ranked "
        "by how strongly you would support each one (rank 1 = strongest). For each nomination give:",
        f"- \"rank\": 1 to {c['max_nominations']}, each rank used once;",
        "- \"discovery\": one line in the style of an official Nobel prize motivation (for example \"for the "
        "discovery of ...\");",
        f"- \"people\": 1 to {c['max_people']} living people most closely associated with the discovery, each with "
        "\"name\" and \"affiliation\";",
        f"- \"key_papers\": up to {c['max_key_papers']} key publications (\"first author, journal, year: title\"), only "
        "if you know them; otherwise an empty list;",
        f"- \"rationale\": at most {c['max_rationale_sentences']} sentences.",
        "",
        "Answer with one JSON object of this form and nothing else:",
        '{"nominations": [{"rank": 1, "discovery": "...", "people": [{"name": "...", "affiliation": "..."}], '
        '"key_papers": ["..."], "rationale": "..."}]}',
    ])
    return specialty, system, user


# ---------------------------------------------------------------- local validation

def sentences(text):
    return len([s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"(])", text.strip()) if s])


def validate(obj):
    """(valid, errors, warnings, nominations). Hard errors: structure and types. Count limits are warnings only."""
    c = CFG["committee"]
    if not isinstance(obj, dict) or not isinstance(obj.get("nominations"), list):
        return False, ["top level must be an object with a 'nominations' list"], [], []
    noms = obj["nominations"]
    if not noms:
        return False, ["no nominations"], [], []
    errs = []
    for i, n in enumerate(noms, 1):
        if not isinstance(n, dict):
            errs.append(f"nomination {i}: not an object")
            continue
        miss = [k for k in ("rank", "discovery", "people", "key_papers", "rationale") if k not in n]
        if miss:
            errs.append(f"nomination {i}: missing {miss}")
            continue
        if not isinstance(n["rank"], int) or isinstance(n["rank"], bool):
            errs.append(f"nomination {i}: rank is not an integer")
        if not isinstance(n["discovery"], str) or not n["discovery"].strip():
            errs.append(f"nomination {i}: empty discovery")
        if not isinstance(n["people"], list) or not all(
                isinstance(p, dict) and isinstance(p.get("name"), str) and p["name"].strip()
                and isinstance(p.get("affiliation"), str) for p in n["people"]):
            errs.append(f"nomination {i}: people must be a list of {{name, affiliation}}")
        if not isinstance(n["key_papers"], list) or not all(isinstance(x, str) for x in n["key_papers"]):
            errs.append(f"nomination {i}: key_papers must be a list of strings")
        if not isinstance(n["rationale"], str):
            errs.append(f"nomination {i}: rationale is not a string")
    if errs:
        return False, errs, [], []

    warns = []
    order = sorted(range(len(noms)), key=lambda i: (noms[i]["rank"], i))
    stated = [n["rank"] for n in noms]
    if sorted(stated) != list(range(1, len(noms) + 1)):
        warns.append(f"ranks {stated} are not 1..{len(noms)}: re-ranked by stated rank, then position")
    if len(noms) > c["max_nominations"]:
        warns.append(f"{len(noms)} nominations: ranks above {c['max_nominations']} get no points")
    clean = []
    for new_rank, i in enumerate(order, 1):
        n = noms[i]
        k = len(n["people"])
        if not 1 <= k <= c["max_people"]:
            warns.append(f"rank {new_rank}: {k} people")
        if len(n["key_papers"]) > c["max_key_papers"]:
            warns.append(f"rank {new_rank}: {len(n['key_papers'])} key papers")
        if sentences(n["rationale"]) > c["max_rationale_sentences"]:
            warns.append(f"rank {new_rank}: rationale has {sentences(n['rationale'])} sentences")
        clean.append({"rank": new_rank, "rank_stated": n["rank"], "discovery": n["discovery"].strip(),
                      "people": [{"name": p["name"].strip(), "affiliation": p["affiliation"].strip()}
                                 for p in n["people"]],
                      "key_papers": n["key_papers"], "rationale": n["rationale"].strip()})
    return True, [], warns, clean


# ---------------------------------------------------------------- one cell = one persona on one model (one rep)

def raw_path(base, provider, persona_idx, field, rep):
    name = slug(CFG["fields"][field]["personas"][persona_idx]) + ("" if rep == 1 else f"_r{rep}")
    return base / "raw" / CFG["models"][provider] / f"{name}.json"


def run_cell(field, persona_idx, provider, rep, base, force=False):
    path = raw_path(base, provider, persona_idx, field, rep)
    if path.exists() and not force:
        d = json.loads(path.read_text())
        return d, "exists (not re-asked)"
    c = CFG["committee"]
    model = CFG["models"][provider]
    specialty, system, user = prompt(field, persona_idx)
    attempts, ok, warns, clean = [], False, [], []
    for _ in range(1 + c["json_retries"]):
        res = call(provider, model, system, user, SCHEMA, c["max_output_tokens"])
        if res["error"]:                                    # HTTP failure after the transient retries: not re-asked
            res.update(valid=False, errors=[f"HTTP: {res['error']}"], warnings=[])
            attempts.append(res)
            break
        if res["parsed"] is None:
            ok, errs, warns, clean = False, [res["parse_error"] or "no JSON text"], [], []
        else:
            ok, errs, warns, clean = validate(res["parsed"])
        if res["truncated"]:
            errs = errs + [f"truncated (stop={res['stop']})"] if not ok else errs
        if res["refused"] and not ok:
            errs = errs + [f"refused (stop={res['stop']})"]
        res.update(valid=ok, errors=errs, warnings=warns)
        attempts.append(res)
        if ok:
            break
    rec = {"field": field, "provider": provider, "model": model, "persona_idx": persona_idx,
           "specialty": specialty, "rep": rep, "written": now(),
           "prompt": {"system": system, "user": user}, "schema": SCHEMA,
           "params": {"max_output_tokens": c["max_output_tokens"], "sampling": c["sampling"],
                      "reasoning": c["reasoning"], "tools": c["tools"], "fallbacks": c["fallbacks"]},
           "attempts": attempts,
           "final": {"valid": ok, "n_attempts": len(attempts), "nominations": clean if ok else [],
                     "warnings": warns if ok else [],
                     "missing_reason": None if ok else attempts[-1]["errors"],
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
    return (f"{rec['field']:<9} {rec['model']:<22} {rec['specialty'][:38]:<38} "
            f"{'valid' if rec['final']['valid'] else 'MISSING':<7} att={rec['final']['n_attempts']} "
            f"noms={len(rec['final']['nominations'])} stop={a.get('stop')} in={u.get('input')} out={u.get('output')} "
            f"(reasoning={u.get('reasoning')}) {secs:.0f}s  [{how}]")


# ---------------------------------------------------------------- aggregation (SPEC §6.5) and diagnostics (§6.6)

TITLES = {"sir", "dame", "dr", "prof", "professor", "jr", "sr", "ii", "iii", "md", "phd"}
STOPWORDS = set("""for the a an of and in on to by its their his her as with from into via which that this these
    discovery discoveries discovered development developing developed invention inventions role roles mechanism
    mechanisms new use based""".split())
SHORT = {"anthropic": "A", "openai": "O", "gemini": "G"}


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def name_tokens(name):
    return [t for t in re.split(r"[^a-z]+", fold(name)) if t and t not in TITLES]


def person_key(name):
    """First initial + surname ('Jens Juul Holst' -> 'j holst'): the people-overlap merge key."""
    t = name_tokens(name)
    return None if not t else (f"{t[0][0]} {t[-1]}" if len(t) > 1 else t[0])


def middles(name):
    return tuple(t[0] for t in name_tokens(name)[1:-1])


def assign_identities(noms):
    """Person identity of every named person: the key (first initial + surname), split by middle initials when one key
    carries two different ones (Charles H. Bennett vs Charles L. Bennett). Under such a key a name without middle
    initials is ambiguous and gets an identity of its own (not linked). Sets n["pids"] (aligned with n["people"]) and
    n["keys"] (the set used for automatic merging)."""
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
    """Stricter check for laureate flags: same surname and compatible first names (an initial matches a full name)."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb or ta[-1] != tb[-1]:
        return False
    fa, fb = ta[0], tb[0]
    return fa == fb or (min(len(fa), len(fb)) == 1 and fa[0] == fb[0])


def content_words(text):
    return {w for w in re.findall(r"[a-z0-9]+", fold(text)) if len(w) > 2 and w not in STOPWORDS}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def load_ballots(field, aliases=None):
    aliases = aliases or {}
    ballots = [json.loads(l) for l in (COMMITTEE / field / "ballots.jsonl").read_text().splitlines() if l.strip()]
    pts = CFG["committee"]["borda_points"]
    noms = []
    for b in ballots:
        if not b["valid"]:
            continue
        for n in b["nominations"]:
            if n["rank"] > len(pts):
                continue
            people = [{**p, "name": aliases.get(p["name"], p["name"])} for p in n["people"]]
            noms.append({**n, "people": people,
                         "id": f"{b['provider']}/{slug(b['specialty'])}/r{b['rep']}/#{n['rank']}",
                         "provider": b["provider"], "persona_idx": b["persona_idx"], "specialty": b["specialty"],
                         "rep": b["rep"], "points": pts[n["rank"] - 1]})
    assign_identities(noms)
    return ballots, noms


def load_manual(field):
    path = COMMITTEE / field / "merges.yaml"
    m = (yaml.safe_load(path.read_text()) if path.exists() else None) or {}
    return {"split": m.get("split") or [], "merge": m.get("merge") or [], "person_notes": m.get("person_notes") or {},
            "aliases": m.get("aliases") or {}, "wording_from": m.get("wording_from") or [],
            "people": m.get("people") or [], "deceased": m.get("deceased") or {}}


def make_clusters(noms, manual):
    """Auto: nominations sharing a person key are linked (graph components). Manual (merges.yaml), in this order:
    split = these ids leave their auto cluster and form one option of their own; merge = the clusters holding these
    ids become one option."""
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
        for k in ks[1:]:
            union(ks[0], k)
    for g in manual["split"] + manual["merge"]:
        ks = [ids[i] for i in g["ids"]]
        for k in ks[1:]:
            union(ks[0], k)
    groups = {}
    for k in range(len(noms)):
        groups.setdefault(find(k), []).append(noms[k])
    return list(groups.values())


def n_valid(ballots, keep):
    return {p: sum(1 for b in ballots if b["valid"] and b["provider"] == p and keep(b)) for p in PROVIDERS}


def score(members, nv, keep):
    per = {p: 0.0 for p in PROVIDERS}
    for n in members:
        if keep(n) and nv[n["provider"]]:
            per[n["provider"]] += n["points"] / nv[n["provider"]]
    return sum(per.values()), per


def top_k(clusters, ballots, keep=lambda x: True, k=None):
    k = k or CFG["question"]["K"]
    nv = n_valid(ballots, keep)
    s = [(-score(c, nv, keep)[0], -len({n["provider"] for n in c if keep(n)}), -len(c), c[0]["id"], i)
         for i, c in enumerate(clusters)]       # ties: more models, then more nominations, then id
    return [x[-1] for x in sorted(s) if x[0] < 0][:k]


def describe(c, nv, wording_from=()):
    """Option wording (from the member named in merges.yaml wording_from, else the member with the most normalized
    points) and people ranked by normalized points."""
    w, cnt, forms, affs = {}, {}, {}, {}
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
    people = [{"name": max(forms[k], key=lambda s: (forms[k][s], len(s))),
               "affiliation": max(affs[k], key=lambda s: (affs[k][s], len(s))),
               "key": k, "weight": round(w[k], 4), "n_nominations": cnt[k]}
              for k in sorted(w, key=lambda k: (-w[k], -cnt[k], k))]
    chosen = [n for n in c if n["id"] in wording_from]
    best = chosen[0] if chosen else max(
        c, key=lambda n: (n["points"] / nv[n["provider"]], -PROVIDERS.index(n["provider"]), -n["persona_idx"]))
    return best["discovery"], people


def laureate_table():
    d = pd.read_csv(REPO / "Data/prizeatlas/prizeatlas_nobel_laureates.csv")
    return [(r.name, int(r.year), r.category_en, r.death_date if isinstance(r.death_date, str) else None)
            for r in d.itertuples()]


def field_motivations(field):
    f = CFG["fields"][field]
    y0, y1 = CFG["committee"]["prior_prizes"]
    d = pd.read_csv(REPO / "Data/prizeatlas/prizeatlas_nobel_laureates.csv")
    d = d[(d.category_en == f["prizeatlas_category"]) & d.year.between(y0, y1)].drop_duplicates(["year", "award_group"])
    return [(int(r.year), r.motivation) for r in d.itertuples()]


def cmd_aggregate(a):
    field = a.field
    K, max_people = CFG["question"]["K"], CFG["committee"]["max_people"]
    manual = load_manual(field)
    ballots, noms = load_ballots(field, manual["aliases"])
    clusters = make_clusters(noms, manual)
    everything = lambda x: True
    nv = n_valid(ballots, everything)
    order = top_k(clusters, ballots, everything, k=len(clusters))
    top = order[:K]
    laureates = laureate_table()
    motivations = field_motivations(field)

    def option(i, rank):
        c = clusters[i]
        total, per = score(c, nv, everything)
        discovery, people = describe(c, nv, {w["id"] for w in manual["wording_from"]})
        chosen = next((w for w in manual["people"] if w["id"] in {n["id"] for n in c}), None)
        if chosen:                                          # merges.yaml people: shown people chosen by hand
            picked = []
            for name in chosen["names"]:
                hit = [q for q in people if same_person(name, q["name"])]
                if len(hit) != 1:
                    sys.exit(f"merges.yaml people: '{name}' matches {len(hit)} people of the option of {chosen['id']}")
                picked.append(hit[0])
            people = picked + [q for q in people if q not in picked]
        dead = {q["name"]: note for q in people for name, note in manual["deceased"].items() if same_person(name, q["name"])}
        if chosen and any(q["name"] in dead for q in people[:max_people]):
            sys.exit(f"merges.yaml people for {chosen['id']} names a deceased person")
        people = [q for q in people if q["name"] not in dead] + [q for q in people if q["name"] in dead]
        models = sorted({n["provider"] for n in c}, key=PROVIDERS.index)
        flags = [f"{name}: deceased ({note}); not shown, next living person by weight shown instead"
                 for name, note in dead.items()]
        for p in people[:max_people]:
            for name, year, cat, death in laureates:
                if same_person(p["name"], name):
                    flags.append(f"{p['name']}: Nobel laureate ({cat} {year})" + (f", died {death}" if death else ""))
            note = manual["person_notes"].get(p["name"])
            if note:
                flags.append(f"{p['name']}: {note}")
        for year, mot in motivations:
            j = max(jaccard(content_words(n["discovery"]), content_words(mot)) for n in c)
            if j >= 0.35:
                flags.append(f"possibly already awarded: resembles {year} \"{mot}\" (word overlap {j:.2f})")
        if not chosen and len(people) - len(dead) > max_people and abs(people[max_people - 1]["weight"] - people[max_people]["weight"]) < 1e-9:
            tied = [q["name"] for q in people if abs(q["weight"] - people[max_people - 1]["weight"]) < 1e-9]
            flags.append(f"tie for the last shown person (weight {people[max_people - 1]['weight']:.3f}): "
                         f"{', '.join(tied)}; shown by alphabetical order of the key, needs a decision")
        if len(people) > max_people:
            flags.append(f"{len(people)} people named across nominations; shown: top {max_people}; also: "
                         + ", ".join(f"{p['name']} ({p['weight']:.2f})" for p in people[max_people:]))
        return {"rank": rank, "option": f"{discovery} — {', '.join(p['name'] for p in people[:max_people])}",
                "discovery": discovery, "score": round(total, 4),
                "points_per_model": {CFG["models"][p]: round(per[p], 4) for p in PROVIDERS},
                "n_models": len(models), "models": [CFG["models"][p] for p in models],
                "n_personas": len({n["specialty"] for n in c}), "n_ballots": len({(n["provider"], n["persona_idx"], n["rep"]) for n in c}),
                "consensus": "cross-model consensus" if len(models) == len(PROVIDERS) else ("single-model" if len(models) == 1 else ""),
                "people": [{k: p[k] for k in ("name", "affiliation", "weight", "n_nominations", "key")} for p in people[:max_people]],
                "people_all": [{k: p[k] for k in ("name", "affiliation", "weight", "n_nominations", "key")} for p in people],
                "nomination_ids": [n["id"] for n in c], "flags": flags}

    opts = [option(i, r) for r, i in enumerate(order, 1)]
    top_opts = opts[:K]
    # duplicates across options: one person in two of the top-K options
    seen = {}
    for o in top_opts:
        for p in o["people"]:
            seen.setdefault(p["key"], []).append(o["rank"])
    for key, ranks in seen.items():
        if len(ranks) > 1:
            for o in top_opts:
                if o["rank"] in ranks:
                    o["flags"].append(f"person '{key}' also in option(s) {[r for r in ranks if r != o['rank']]}")
    out = {"field": field, "generated": now(), "K": K, "models": CFG["models"],
           "valid_ballots_per_model": {CFG["models"][p]: nv[p] for p in PROVIDERS},
           "normalization": "Borda 5..1 per ballot; each model's points divided by its number of valid ballots, summed over models",
           "options": top_opts + [{"rank": K + 1, "option": CFG["question"]["other_option"]}]}
    (COMMITTEE / field / "candidates.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    (COMMITTEE / field / "clusters.json").write_text(json.dumps(opts, indent=1, ensure_ascii=False))
    write_review(field, ballots, noms, clusters, order, opts, manual)
    print(f"{field}: {len(noms)} nominations -> {len(clusters)} options; top {K} written to "
          f"committee/{field}/candidates.json, review.md, clusters.json")
    for o in top_opts:
        print(f"  {o['rank']:>2}. {o['score']:.3f} m={o['n_models']} p={o['n_personas']} {o['option'][:110]}")


def write_review(field, ballots, noms, clusters, order, opts, manual):
    K = CFG["question"]["K"]
    f = CFG["fields"][field]
    cl_rank = {i: r for r, i in enumerate(order, 1)}
    L = [f"# Committee review — {f['prize']} 2026", "",
         f"Generated {now()} by `committee.py aggregate --field {field}` from `ballots.jsonl`. Every merge is listed "
         "below with its reason. Option = top-K discovery; score = normalized Borda (each model contributes equally).", ""]

    L += ["## Ballots", "", "| model | valid | missing | reported model(s) | ballots with warnings |", "|---|---|---|---|---|"]
    for p in PROVIDERS:
        bs = [b for b in ballots if b["provider"] == p]
        rep = sorted({b.get("model_reported") or "-" for b in bs if b["valid"]})
        L.append(f"| {CFG['models'][p]} | {sum(b['valid'] for b in bs)} | {sum(not b['valid'] for b in bs)} | "
                 f"{', '.join(rep)} | {sum(bool(b.get('warnings')) for b in bs)} |")
    miss = [b for b in ballots if not b["valid"]]
    if miss:
        L += ["", "Missing cells: " + "; ".join(f"{b['model']} / {b['specialty']}: {b['missing_reason']}" for b in miss)]
    warn = [(b, w) for b in ballots if b["valid"] for w in b.get("warnings", [])]
    if warn:
        L += ["", "Warnings: " + "; ".join(f"{SHORT[b['provider']]} / {b['specialty']}: {w}" for b, w in warn)]

    L += ["", f"## Candidate list (top {K} + Other)", "",
          "| # | option | score | models | personas | ballots | " + " | ".join(SHORT[p] for p in PROVIDERS) + " | consensus |",
          "|---|---|---|---|---|---|" + "---|" * len(PROVIDERS) + "---|"]
    for o in opts[:K]:
        L.append(f"| {o['rank']} | {o['option']} | {o['score']:.3f} | {o['n_models']} | {o['n_personas']} | {o['n_ballots']} | "
                 + " | ".join(f"{o['points_per_model'][CFG['models'][p]]:.3f}" for p in PROVIDERS) + f" | {o['consensus']} |")
    L += [f"| {K + 1} | {CFG['question']['other_option']} | | | | |" + " |" * len(PROVIDERS) + " |", "",
          "A / O / G = normalized points from " + ", ".join(f"{SHORT[p]} = {CFG['models'][p]}" for p in PROVIDERS) + "."]
    if len(opts) > K and abs(opts[K - 1]["score"] - opts[K]["score"]) < 1e-9:
        tied = [o for o in opts if abs(o["score"] - opts[K - 1]["score"]) < 1e-9]
        L += ["", f"Tie at the cut-off (score {opts[K - 1]['score']:.3f}), broken by number of models, then number of "
              "nominations: " + "; ".join(f"{o['rank']}. {o['option']} ({o['n_models']} models, "
                                          f"{len(o['nomination_ids'])} nominations)" for o in tied)]

    L += ["", "## Flags (top options)", ""]
    for o in opts[:K]:
        for fl in o["flags"]:
            L.append(f"- #{o['rank']}: {fl}")
    if not any(o["flags"] for o in opts[:K]):
        L.append("- none")
    L += ["", "Deceased people are only detected for Nobel laureates (PrizeAtlas death_date) and through "
          "`merges.yaml` person_notes; every name in the top options still needs a check that the person is living."]

    L += ["", "## Merges", "", "### Automatic: nominations that share a person (first initial + surname)", ""]
    split_ids = {i for g in manual["split"] for i in g["ids"]}
    for i in order:
        c = clusters[i]
        if len(c) < 2:
            continue
        keys = {}
        for n in c:
            if n["id"] in split_ids:
                continue
            for k in n["keys"]:
                keys[k] = keys.get(k, 0) + 1
        shared = sorted(k for k, v in keys.items() if v > 1)
        L.append(f"- **option {cl_rank[i]}** ({len(c)} nominations; shared: {', '.join(shared) or 'manual only'})")
        for n in sorted(c, key=lambda n: (PROVIDERS.index(n["provider"]), n["persona_idx"], n["rank"])):
            best = max(jaccard(content_words(n["discovery"]), content_words(m["discovery"])) for m in c if m is not n)
            odd = f" **[check: wording overlap with the rest only {best:.2f}]**" if best < 0.25 else ""
            L.append(f"  - `{n['id']}`: {n['discovery']} — {', '.join(p['name'] for p in n['people'])}{odd}")
    L += ["", "### Manual (merges.yaml)", ""]
    for kind in ("split", "merge"):
        for g in manual[kind]:
            L.append(f"- {kind}: {', '.join(f'`{i}`' for i in g['ids'])} — {g.get('reason', '(no reason given)')}")
    for w in manual["wording_from"]:
        L.append(f"- wording from `{w['id']}` — {w.get('reason', '(no reason given)')}")
    for name, note in manual["deceased"].items():
        L.append(f"- deceased: {name} — {note}")
    for w in manual["people"]:
        L.append(f"- people shown for the option of `{w['id']}`: {', '.join(w['names'])} — {w.get('reason', '(no reason given)')}")
    for variant, canonical in manual["aliases"].items():
        L.append(f"- alias: \"{variant}\" read as \"{canonical}\"")
    if not any(manual[k] for k in ("split", "merge", "aliases", "wording_from", "people", "deceased")):
        L.append("- none")

    L += ["", "### Possibly the same discovery, not merged (for review)", ""]
    pairs = []
    nv = n_valid(ballots, lambda b: True)
    cand = order[: 3 * K]
    for x in range(len(cand)):
        for y in range(x + 1, len(cand)):
            ca, cb = clusters[cand[x]], clusters[cand[y]]
            j = max(jaccard(content_words(n["discovery"]), content_words(m["discovery"])) for n in ca for m in cb)
            if j >= 0.4:
                pairs.append((j, cand[x], cand[y]))
    for j, x, y in sorted(pairs, reverse=True):
        L.append(f"- options {cl_rank[x]} and {cl_rank[y]} (word overlap {j:.2f}): "
                 f"\"{describe(clusters[x], nv)[0]}\" / \"{describe(clusters[y], nv)[0]}\"")
    if not pairs:
        L.append("- none")

    L += ["", f"## Per-model top {K} and overlap", ""]
    sets = {}
    for p in PROVIDERS:
        keep = lambda x, p=p: x["provider"] == p
        t = top_k(clusters, ballots, keep)
        sets[p] = set(t)
        L.append(f"- **{CFG['models'][p]}**: " + "; ".join(f"{cl_rank[i]}" for i in t)
                 + f" (option numbers of the pooled list; {len(t)} options)")
    L += ["", "| pair | Jaccard of top-" + str(K) + " sets |", "|---|---|"]
    for x in range(len(PROVIDERS)):
        for y in range(x + 1, len(PROVIDERS)):
            a, b = sets[PROVIDERS[x]], sets[PROVIDERS[y]]
            L.append(f"| {SHORT[PROVIDERS[x]]}–{SHORT[PROVIDERS[y]]} | {jaccard(a, b):.2f} |")
    n3 = sum(1 for o in opts[:K] if o["consensus"] == "cross-model consensus")
    n1 = sum(1 for o in opts[:K] if o["consensus"] == "single-model")
    L += ["", f"Top {K}: {n3} cross-model consensus (nominated by all three models), {n1} single-model."]

    L += ["", "## Leave-one-out stability", "", f"Options of the top {K} that change when one persona (all its ballots) "
          "or one model is dropped and the list is recomputed (merges fixed).", "", "| dropped | options changed |", "|---|---|"]
    base = set(order[:K])
    for i, spec in enumerate(f["personas"]):
        t = set(top_k(clusters, ballots, lambda x, i=i: x["persona_idx"] != i))
        L.append(f"| persona: {spec} | {len(base - t)} |")
    for p in PROVIDERS:
        t = set(top_k(clusters, ballots, lambda x, p=p: x["provider"] != p))
        L.append(f"| model: {CFG['models'][p]} | {len(base - t)} |")
    (COMMITTEE / field / "review.md").write_text("\n".join(L) + "\n")


# ---------------------------------------------------------------- commands

def cmd_prompt(a):
    specialty, system, user = prompt(a.field, a.persona)
    print(f"# field={a.field} persona={a.persona} ({specialty})\n\n## system\n{system}\n\n## user\n{user}")


def cmd_test(a):
    t = CFG["committee"]["test"]
    base = COMMITTEE / "test"
    with ThreadPoolExecutor(len(a.providers)) as ex:
        futs = {p: ex.submit(run_cell, t["field"], t["persona"], p, 1, base, a.force) for p in a.providers}
    for p in a.providers:
        rec, how = futs[p].result()
        print(cell_line(rec, how))
        for x in rec["attempts"]:
            if not x["valid"]:
                print(f"    attempt invalid: {x['errors']}")
        for w in rec["final"]["warnings"]:
            print(f"    warning: {w}")


def cmd_run(a):
    reps = range(1, CFG["committee"]["R_c"] + 1)
    for field in a.fields:
        base = COMMITTEE / field
        jobs = [(field, i, p, r) for p in PROVIDERS for i in range(len(CFG["fields"][field]["personas"])) for r in reps]
        print(f"{field}: {len(jobs)} cells")
        pools = {p: ThreadPoolExecutor(a.workers) for p in PROVIDERS}   # per provider, so one slow API does not block
        futs = [pools[p].submit(run_cell, f, i, p, r, base, a.force) for f, i, p, r in jobs]
        for (f, i, p, r), fut in zip(jobs, futs):
            try:
                rec, how = fut.result()
            except Exception as e:                          # no raw file is written: a plain re-run retries the cell
                print(f"{f:<9} {CFG['models'][p]:<22} persona {i} rep {r}: CRASHED ({type(e).__name__}), not written",
                      flush=True)
                continue
            with PRINT_LOCK:
                print(cell_line(rec, how), flush=True)
        for pool in pools.values():
            pool.shutdown()
        collect(field)


def collect(field):
    base = COMMITTEE / field
    rows = []
    for p in PROVIDERS:
        for i, specialty in enumerate(CFG["fields"][field]["personas"]):
            for r in range(1, CFG["committee"]["R_c"] + 1):
                path = raw_path(base, p, i, field, r)
                if not path.exists():
                    rows.append({"field": field, "provider": p, "model": CFG["models"][p], "persona_idx": i,
                                 "specialty": specialty, "rep": r, "valid": False, "missing_reason": ["not run"],
                                 "nominations": []})
                    continue
                d = json.loads(path.read_text())
                u = [x.get("usage") or {} for x in d["attempts"]]
                rows.append({"field": field, "provider": p, "model": d["model"], "persona_idx": i,
                             "specialty": specialty, "rep": r, "valid": d["final"]["valid"],
                             "missing_reason": d["final"]["missing_reason"], "n_attempts": d["final"]["n_attempts"],
                             "model_reported": d["final"]["model_reported"],
                             "input_tokens": sum(x.get("input") or 0 for x in u),
                             "output_tokens": sum(x.get("output") or 0 for x in u),
                             "warnings": d["final"]["warnings"], "nominations": d["final"]["nominations"]})
    out = base / "ballots.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    n_ok = sum(r["valid"] for r in rows)
    print(f"{field}: {out.relative_to(HERE)}: {len(rows)} cells, {n_ok} valid, {len(rows) - n_ok} missing")


def cmd_collect(a):
    collect(a.field)


def cmd_estimate(a):
    """Cost of every committee cell from the test ballots' token usage (one call per model, so a rough estimate)."""
    t = CFG["committee"]["test"]
    base = COMMITTEE / "test"
    price = CFG["pricing"]
    _, s0, u0 = prompt(t["field"], t["persona"])
    n_test = len(s0) + len(u0)
    total = 0.0
    usage = {}
    for p in PROVIDERS:
        path = raw_path(base, p, t["persona"], t["field"], 1)
        rec = json.loads(path.read_text()) if path.exists() else None
        if rec and rec["final"]["valid"]:
            usage[p] = rec["attempts"][-1]["usage"]
    proxy = {"input": max(u["input"] for u in usage.values()), "output": max(u["output"] for u in usage.values())}
    print(f"{'model':<24} {'field':<10} {'cells':>5} {'in/cell':>8} {'out/cell':>8} {'USD':>8}")
    for p in PROVIDERS:
        model = CFG["models"][p]
        u = usage.get(p, proxy)
        if p not in usage:
            print(f"{model}: no valid test ballot; proxy = the largest input and output of the other models")
        pin, pout = price[model]["input"], price[model]["output"]
        for field in CFG["order"]:
            k = len(CFG["fields"][field]["personas"]) * CFG["committee"]["R_c"]
            _, s, us = prompt(field, 0)
            tin = u["input"] * (len(s) + len(us)) / n_test           # input scales with the prompt length
            usd = k * (tin * pin + u["output"] * pout) / 1e6
            total += usd
            print(f"{model:<24} {field:<10} {k:>5} {tin:>8.0f} {u['output']:>8} {usd:>8.2f}")
    print(f"{'total (one attempt per cell)':<58} {total:>8.2f}")
    print(f"{'upper bound if every cell needed its JSON retry':<58} {2 * total:>8.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("prompt"); s.add_argument("--field", default="medicine"); s.add_argument("--persona", type=int, default=0)
    s = sub.add_parser("test"); s.add_argument("--force", action="store_true", help="re-ask an existing test cell")
    s.add_argument("--providers", nargs="+", choices=PROVIDERS, default=list(PROVIDERS))
    s = sub.add_parser("run"); s.add_argument("--fields", nargs="+", default=CFG["order"])
    s.add_argument("--workers", type=int, default=2, help="concurrent calls per provider")
    s.add_argument("--force", action="store_true", help="re-ask existing cells (needs the user's OK)")
    s = sub.add_parser("collect"); s.add_argument("--field", required=True)
    sub.add_parser("estimate")
    s = sub.add_parser("aggregate"); s.add_argument("--field", required=True)
    a = ap.parse_args()
    {"prompt": cmd_prompt, "test": cmd_test, "run": cmd_run, "collect": cmd_collect, "estimate": cmd_estimate,
     "aggregate": cmd_aggregate}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
