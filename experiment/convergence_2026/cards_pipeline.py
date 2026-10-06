#!/usr/bin/env python3
"""cards_pipeline.py: profile cards for every person shown in the 30-option lists (results/options_<field>.json).

    $PY cards_pipeline.py missing              # shown people without an identity row in ../preseen/people/
    $PY cards_pipeline.py dryrun               # name search for people/<field>.txt -> people/<field>_dryrun.log (Slurm job)
    $PY cards_pipeline.py identity             # -> people/<field>_identity.csv (people/<field>_choices.yaml decides by hand)
    $PY cards_pipeline.py living               # Wikidata living check of every shown person -> people/living_check.csv
    $PY cards_pipeline.py submit [--dry-run]   # one Slurm profile per new id set; existing profiles are reused
    $PY cards_pipeline.py cards                # cards/<field>/00_definitions.md + one card per shown person
    $PY cards_pipeline.py check                # every shown person has an identity, a profile and a card built from it

The steps are those of ../preseen/ (dryrun_fast.py, people.py identity, check_living.py, submit_profiles.py,
build_cards.py cards), imported or followed line by line, with this folder's inputs and outputs: ../preseen/ is only
read. A person already profiled for ../preseen/ keeps that identity and profile, except where people/overrides.yaml
names other ids (a fix of a known identity problem). The cards say "Listed under" the options of the 30-option list
and compare with the laureate reference of ../preseen/cards/ (the profiles of 3 October).
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PRESEEN = HERE.parent / "preseen"
PEOPLE = HERE / "people"
FIELDS = ["physics", "chemistry"]
for var in yaml.safe_load((PRESEEN / "config.yaml").read_text())["api_keys"].values():
    os.environ.pop(var, None)                  # profile jobs need none of the experiment's keys (sbatch --export=ALL)
os.environ["LD_LIBRARY_PATH"] = "/project/jevans/Dawoon/env/Curvature/lib"
sys.path.insert(0, str(PRESEEN))
import committee as cm  # noqa: E402  (same_person)


def shown(field):
    """[(person, [option texts])] in option order, from results/options_<field>.json."""
    d = json.loads((HERE / "results" / f"options_{field}.json").read_text(encoding="utf-8"))
    out = {}
    for o in d["options"]:
        for p in o["people"]:
            out.setdefault(p["name"], []).append(o["option"])
    return list(out.items())


def preseen_identity():
    """{person: identity row} from ../preseen/people/<field>_identity.csv of all three fields."""
    rows = {}
    for f in ["medicine", "physics", "chemistry"]:
        for r in csv.DictReader(open(PRESEEN / "people" / f"{f}_identity.csv", encoding="utf-8")):
            rows.setdefault(r["person"], r)
    return rows


def find_row(name, rows):
    return next((rows[k] for k in rows if cm.same_person(k, name)), None)


def own_identity(field):
    p = PEOPLE / f"{field}_identity.csv"
    return {r["person"]: r for r in csv.DictReader(open(p, encoding="utf-8"))} if p.exists() else {}


def overrides():
    p = PEOPLE / "overrides.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None) or {}


def identity_of(field, name):
    """(openalex ids, affiliation, prior Nobel, source) of a shown person."""
    ov = overrides().get(name)
    own = own_identity(field).get(name)
    old = find_row(name, preseen_identity())
    row = own or old
    if row is None:
        return None
    ids = (ov["author_id"] if ov else row["openalex_ids"]).split(";")
    src = "overrides.yaml" if ov else ("people/" if own else "../preseen/people/")
    return ids, row["institution"] or row["affiliation_given"], row["prior_nobel"], src


def cmd_missing(a):
    old = preseen_identity()
    for f in FIELDS:
        miss = [n for n, _ in shown(f) if find_row(n, old) is None]
        print(f"{f}: {len(shown(f))} shown people, {len(miss)} without an identity row in ../preseen/people/")
        for n in miss:
            print(f"  {n}")


def cmd_dryrun(a):
    sys.path.insert(0, str(REPO / "pipeline"))
    import profile_person as pp                # noqa: E402
    npc = pp.npc
    qs = {}
    for f in FIELDS:
        qs[f] = [tuple((ln.split("\t") + [""])[:2]) for ln in (PEOPLE / f"{f}.txt").read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith("#")]
    subset = PEOPLE / "_authors_subset.parquet"
    con = npc.duck(a.threads, "48GB")
    lasts = sorted({npc._raw_name_tokens(npc._clean_person(n))[-1] for q in qs.values() for n, _ in q})
    pat = "|".join(re.escape(x) for x in lasts)
    t0 = time.time()
    con.execute(f"""COPY (SELECT * FROM read_parquet('{npc.OA_AUTHORS_PQ}')
                          WHERE works_count >= 1
                            AND (regexp_matches(lower(strip_accents(display_name)), '{pat}')
                                 OR regexp_matches(lower(strip_accents(coalesce(display_name_alternatives, ''))), '{pat}')))
                    TO '{subset}' (FORMAT parquet)""")
    print(f"subset for {len(lasts)} surnames in {time.time() - t0:.0f} s", flush=True)
    npc.OA_AUTHORS_PQ = subset
    args = SimpleNamespace(author_id=None, orcid=None, pick=None, dominance=3.0, no_merge=False, no_api=False,
                           label_year=None, label_field=None, affiliation=None)
    for f, q in qs.items():
        lines = [time.strftime("%H:%M:%S start (cards_pipeline.py dryrun: profile_person.resolve on the authors subset)")]
        log = lambda s, lines=lines: lines.append(str(s))
        for name, aff in q:
            lines += ["", f"=== {name}"]
            args.affiliation = aff.strip() or None
            try:
                ids, labels, text, needs = pp.resolve(con, name.strip(), args, log=log)
            except ValueError as e:
                ids, text = None, str(e)
            if ids is None:
                lines.append(f"NOT RESOLVED: {text}")
        (PEOPLE / f"{f}_dryrun.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{f}: {len(q)} people -> people/{f}_dryrun.log", flush=True)


def cmd_identity(a):
    import duckdb
    import people as pe                         # ../preseen/people.py: blocks, parse, oa, PQRS
    con = duckdb.connect()
    con.execute("SET threads = 2")
    for f in FIELDS:
        bl = pe.blocks((PEOPLE / f"{f}_dryrun.log").read_text(encoding="utf-8"))
        choices = (yaml.safe_load((PEOPLE / f"{f}_choices.yaml").read_text(encoding="utf-8"))
                   if (PEOPLE / f"{f}_choices.yaml").exists() else None) or {}
        rank = {n: "; ".join(o.split(" — ")[0][:60] for o in opts) for n, opts in shown(f)}
        rows = []
        for ln in (PEOPLE / f"{f}.txt").read_text(encoding="utf-8").splitlines():
            if not ln.strip() or ln.startswith("#"):
                continue
            name, aff = (ln.split("\t") + [""])[:2]
            r = pe.parse(bl.get(name, ""))
            if name in choices:
                r = {**r, "ids": choices[name]["author_id"].split(";"), "how": "chosen by hand: " + choices[name]["reason"],
                     "note": (r["note"] + "; " if r["note"] else "") + "dry-run: " + (", ".join(pe.parse(bl.get(name, ""))["ids"]) or "no pick")}
            row = {"field": f, "options": rank.get(name, ""), "person": name, "affiliation_given": aff,
                   "status": "resolved" if r["ids"] else "needs a choice", "openalex_ids": ";".join(r["ids"]),
                   "choice": r["how"], "prior_nobel": r["laureate"], "note": r["note"], "display_name": "", "orcid": "",
                   "institution": "", "works": "", "citations": "", "top_works": "", "inventor_source_expected": "",
                   "pqrs_inventors": ""}
            if r["ids"]:
                au = pe.oa(f"/authors/{r['ids'][0]}")
                row.update(display_name=au.get("display_name", ""), orcid=(au.get("orcid") or "").rsplit("/", 1)[-1],
                           institution="; ".join(i.get("display_name", "") for i in (au.get("last_known_institutions") or [])[:2]),
                           works=au.get("works_count", ""), citations=au.get("cited_by_count", ""))
                w = pe.oa("/works", {"filter": "author.id:" + "|".join(r["ids"]), "sort": "cited_by_count:desc", "per-page": 3,
                                     "select": "title,publication_year,cited_by_count"})
                row["top_works"] = w.get("_error") or " | ".join(
                    f"{x.get('title')} ({x.get('publication_year')}; {x.get('cited_by_count')} cit.)" for x in w.get("results", []))
                ids_sql = ", ".join(f"'{i}'" for i in r["ids"])
                q = con.sql(f"SELECT inventor_id, round(confidence, 2) FROM read_parquet('{pe.PQRS}') "
                            f"WHERE author_id IN ({ids_sql}) AND confidence >= 0.5 ORDER BY confidence DESC").fetchall()
                row["pqrs_inventors"] = "; ".join(f"{i} ({c})" for i, c in q)
                row["inventor_source_expected"] = "pqrs crosswalk" if q else "PatentsView name search (no pqrs inventor)"
                time.sleep(0.2)
            rows.append(row)
        with open(PEOPLE / f"{f}_identity.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"{f}: people/{f}_identity.csv: {len(rows)} people; needs a choice: "
              f"{[r['person'] for r in rows if r['status'] != 'resolved']}")
        for r in rows:
            print(f"  {r['person']:<26} {r['openalex_ids'][:38]:<38} {r['display_name'][:24]:<24} orcid={r['orcid'] or '-':<19} "
                  f"{str(r['works']):>5}w {str(r['citations']):>7}c | {r['institution'][:40]} | {r['choice'][:50]}"
                  f"{' | Nobel: ' + r['prior_nobel'] if r['prior_nobel'] else ''}{' | ' + r['note'][:100] if r['note'] else ''}")


def cmd_living(a):
    import check_living as cl                   # ../preseen/check_living.py (cache in ../preseen/committee/)
    cache = json.loads(cl.CACHE.read_text()) if cl.CACHE.exists() else {}
    rows = []
    for f in FIELDS:
        for name, opts in shown(f):
            r = cache.get(name)
            if r is None or r["status"] in ("no match", "lookup failed"):
                try:
                    r = cl.lookup(name)
                except cl.LookupFailed as e:
                    r = {"status": "lookup failed", "qid": "", "label": "", "description": str(e), "born": "", "died": "", "n": 0}
                cache[name] = r
                cl.CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
            rows.append({"field": f, "person": name, **{k: r.get(k, "") for k in ("status", "qid", "label", "description",
                                                                                    "born", "died", "n", "others")}})
    with open(PEOPLE / "living_check.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"people/living_check.csv: {len(rows)} people; needs a look:")
    for r in rows:
        if not r["status"].startswith("living") or r["n"] != 1:
            print(f"  {r['field']:<9} {r['person']:<28} {r['status']:<45} {r['qid']} {r['label']} | {r['description'][:60]} | "
                  f"b.{r['born']} d.{r['died']} | {str(r.get('others', ''))[:140]}")


def cmd_submit(a):
    sys.path.insert(0, str(REPO / "pipeline"))
    import profile_person as pp                # noqa: E402
    npc = pp.npc
    sets = {}
    for f in FIELDS:
        for name, _ in shown(f):
            got = identity_of(f, name)
            if got is None:
                print(f"no identity for {name} ({f}); run identity first")
                continue
            sets.setdefault(";".join(got[0]), name)
    if a.force and not a.only:
        sys.exit("--force needs --only")
    if a.no_name_search:
        os.environ["NP_NAME_SEARCH"] = "off"         # read by the notebook in the job (sbatch --export=ALL)
    con = npc.duck(8, "16GB")
    rows = []
    todo = {}
    for key, name in sets.items():
        if a.only and name not in a.only:
            continue
        if not a.force and __import__("build_cards").find_profile(key.split(";")) is not None:   # profiled before
            rows.append({"person": name, "ids": key, "job": "reused", "submitted": ""})
            continue
        todo[key] = name
    print(f"{len(sets)} id sets: {len(sets) - len(todo)} with a profile, {len(todo)} to run")
    if todo:
        subset = PEOPLE / "_authors_ids_subset.parquet"
        all_ids = sorted({int(i[1:]) for k in todo for i in k.split(";")})
        con.execute(f"COPY (SELECT * FROM read_parquet('{npc.OA_AUTHORS_PQ}') WHERE author_id IN ({', '.join(map(str, all_ids))})) "
                    f"TO '{subset}' (FORMAT parquet)")
        npc.OA_AUTHORS_PQ = subset
    for key, name in todo.items():
        args = SimpleNamespace(author_id=key, orcid=None, pick=None, dominance=3.0, no_merge=False, no_api=True,
                               label_year=None, label_field=None, affiliation=None, year_max=2021, titles="api",
                               local=False, wait=False, mem="64G", cpus=8)
        got, labels, text, _ = pp.resolve(con, name, args, log=lambda m: None)
        if a.dry_run:
            print(f"would submit {name:<26} {got} {labels}")
            continue
        res = pp.run(got, labels, name, text, args, log=lambda m: print("    " + str(m)))
        print(f"{'submitted' if res.get('ok') else 'FAILED'} {name:<26} {key} job {res.get('job')}", flush=True)
        rows.append({"person": name, "ids": key, "job": res.get("job") or "failed",
                     "submitted": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    if rows and not a.dry_run:
        out = PEOPLE / "profile_jobs.csv"
        new = not out.exists()
        with open(out, "a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)


def cmd_cards(a):
    import pandas as pd
    import build_cards as bc                   # ../preseen/build_cards.py: card(), DEFINITIONS, find_profile
    cards = HERE / "cards"
    cards.mkdir(exist_ok=True)
    bc.TITLE_CACHE = cards / "_titles_cache.json"
    seed = PRESEEN / "cards" / "_titles_cache.json"
    if not bc.TITLE_CACHE.exists() and seed.exists():
        bc.TITLE_CACHE.write_text(seed.read_text())
    ref = pd.read_csv(PRESEEN / "cards" / "laureate_reference.csv")
    y0, y1 = bc.CFG["profiles"]["laureate_reference_years"]
    index = []
    for f in FIELDS:
        out = cards / f
        out.mkdir(exist_ok=True)
        (out / "00_definitions.md").write_text(bc.DEFINITIONS.format(year_max=bc.YEAR_MAX, field_name=bc.CFG["fields"][f]["prize"],
                                                                     y0=y0, y1=y1))
        for name, opts in shown(f):
            got = identity_of(f, name)
            if got is None:
                index.append({"field": f, "person": name, "card": "", "profile": "NO IDENTITY", "identity_from": ""})
                continue
            ids, aff, prior, src = got
            text, folder = bc.card(f, name, ids, opts, aff, prior, ref)
            path = out / f"{bc.person_slug(name)}.md"
            path.write_text(text, encoding="utf-8")
            index.append({"field": f, "person": name, "card": f"{f}/{path.name}", "openalex_ids": ";".join(ids),
                          "profile": folder.name if folder else "NO PROFILE", "identity_from": src})
    with open(cards / "index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["field", "person", "card", "openalex_ids", "profile", "identity_from"])
        w.writeheader()
        w.writerows(index)
    for f in FIELDS:
        rows = [r for r in index if r["field"] == f]
        bad = [r["person"] for r in rows if r["profile"] in ("NO PROFILE", "NO IDENTITY")]
        print(f"{f}: {len(rows)} cards in cards/{f}/; without profile: {bad}")


def cmd_check(a):
    """Every shown person: identity, profile, card file, card built from a profile, card lists the person's options."""
    import build_cards as bc
    living = {(r["field"], r["person"]): r for r in csv.DictReader(open(PEOPLE / "living_check.csv", encoding="utf-8"))} \
        if (PEOPLE / "living_check.csv").exists() else {}
    no_profile_text = bc.CFG["profiles"]["no_profile_card"].strip()[:40]
    problems, n = [], 0
    for f in FIELDS:
        for name, opts in shown(f):
            n += 1
            got = identity_of(f, name)
            if got is None:
                problems.append((f, name, "no identity"))
                continue
            if bc.find_profile(got[0]) is None:
                problems.append((f, name, f"no profile for {';'.join(got[0])}"))
            card = HERE / "cards" / f / f"{bc.person_slug(name)}.md"
            if not card.exists():
                problems.append((f, name, "no card file"))
                continue
            text = card.read_text(encoding="utf-8")
            if no_profile_text in text or "## Impact" not in text:
                problems.append((f, name, "card has no profile data"))
            if any(o not in text for o in opts):
                problems.append((f, name, "card does not list all of the person's options"))
            if living.get((f, name), {}).get("status", "").startswith("DECEASED"):
                problems.append((f, name, "shown although deceased per the living check"))
    print(f"{n} shown people checked (physics + chemistry); problems: {len(problems)}")
    for f, name, why in problems:
        print(f"  {f:<9} {name:<28} {why}")
    return 1 if problems else 0


def main():
    ap = argparse.ArgumentParser(description="Profile cards for the 30-option lists.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("missing")
    s = sub.add_parser("dryrun"); s.add_argument("--threads", type=int, default=8)
    sub.add_parser("identity")
    sub.add_parser("living")
    s = sub.add_parser("submit"); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--only", nargs="+", help="submit only these people (one job first rebuilds stale shared caches)")
    s.add_argument("--force", action="store_true", help="run again although a profile exists (with --only)")
    s.add_argument("--no-name-search", action="store_true",
                   help="NP_NAME_SEARCH=off: no PatentsView name search (people whose name search finds a namesake)")
    sub.add_parser("cards")
    sub.add_parser("check")
    a = ap.parse_args()
    PEOPLE.mkdir(exist_ok=True)
    {"missing": cmd_missing, "dryrun": cmd_dryrun, "identity": cmd_identity, "living": cmd_living,
     "submit": cmd_submit, "cards": cmd_cards, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
