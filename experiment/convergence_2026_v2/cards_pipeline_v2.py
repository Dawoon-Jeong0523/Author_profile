#!/usr/bin/env python3
"""cards_pipeline_v2.py: profile cards for every person shown in the v1 and v2 30-option lists of all three fields.

    $PY cards_pipeline_v2.py missing [--write]    # shown people without an identity; --write -> people/<field>.txt
    $PY cards_pipeline_v2.py dryrun               # name search for people/<field>.txt -> people/<field>_dryrun.log (Slurm job)
    $PY cards_pipeline_v2.py identity             # -> people/<field>_identity.csv (people/<field>_choices.yaml decides by hand)
    $PY cards_pipeline_v2.py living               # Wikidata living check of every shown person -> people/living_check.csv
    $PY cards_pipeline_v2.py submit [--dry-run]   # one Slurm profile per id set without a profile; others are reused
    $PY cards_pipeline_v2.py cards                # cards/<version>/<field>/00_definitions.md + one card per shown person
    $PY cards_pipeline_v2.py check                # every shown person has an identity, a profile and a card built from it

The lists: v2 = results/options_<field>.json, v1 = results/v1_rule/options_<field>.json (written by compare_v1_v2.py;
for physics and chemistry identical to ../convergence_2026/results/), and the Preseen-generated chemistry list
../preseen_generated30/chemistry/options.json (version "preseen"). The steps are those of
../convergence_2026/cards_pipeline.py (and through it ../preseen/), with this folder's inputs and outputs; ../preseen/ and
../convergence_2026/ are only read (except the shared Wikidata cache ../preseen/committee/living_cache.json, as in v1).
A person who already has an identity keeps it: this folder's people/ first, then ../convergence_2026/people/ (with its
overrides.yaml), then ../preseen/people/, any field. Cards say "Listed under" the options of their own list and compare
with the laureate reference of ../preseen/cards/ (the profiles of 3 October), as in v1.
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
V1 = HERE.parent / "convergence_2026"
PEOPLE = HERE / "people"
FIELDS = ["medicine", "physics", "chemistry"]
LISTS = {("v2", f): HERE / "results" / f"options_{f}.json" for f in FIELDS} | \
        {("v1", f): HERE / "results" / "v1_rule" / f"options_{f}.json" for f in FIELDS} | \
        {("preseen", "chemistry"): HERE.parent / "preseen_generated30" / "chemistry" / "options.json"}
for var in yaml.safe_load((PRESEEN / "config.yaml").read_text())["api_keys"].values():
    os.environ.pop(var, None)                  # profile jobs need none of the experiment's keys (sbatch --export=ALL)
os.environ["LD_LIBRARY_PATH"] = "/project/jevans/Dawoon/env/Curvature/lib"
sys.path.insert(0, str(PRESEEN))
import committee as cm  # noqa: E402  (same_person)

# affiliations for the name search of people the committee did not name (the committee's own are taken from its ballots)
AFFILIATION = {
    "James G. Fujimoto": "Massachusetts Institute of Technology", "David Huang": "Oregon Health & Science University",
    "Eric A. Swanson": "Massachusetts Institute of Technology", "Michael J. Welsh": "University of Iowa",
    "Paul A. Negulescu": "Vertex Pharmaceuticals", "Adrian Bird": "University of Edinburgh",
    "Huda Zoghbi": "Baylor College of Medicine", "Carl-Henrik Heldin": "Uppsala University",
    "Kohei Miyazono": "University of Tokyo", "Eric Olson": "University of Texas Southwestern Medical Center",
    "Timothy A. Springer": "Harvard Medical School", "Michelle Monje": "Stanford University",
    "Pamela J. Bjorkman": "California Institute of Technology",
    # people of the Preseen-generated chemistry list (../preseen_generated30/), 2026-10-06
    "Jacob Sagiv": "Weizmann Institute of Science", "Tao Zhang": "Dalian Institute of Chemical Physics",
    "Mark Levin": "University of Chicago", "Richard Sarpong": "University of California, Berkeley",
    "Bill Morandi": "ETH Zurich", "Clifford P. Brangwynne": "Princeton University",
    "Anthony A. Hyman": "Max Planck Institute of Molecular Cell Biology and Genetics",
    "Michael K. Rosen": "University of Texas Southwestern Medical Center", "James J. Collins": "Massachusetts Institute of Technology",
    "Michael Elowitz": "California Institute of Technology", "Stanislas Leibler": "Rockefeller University",
    "Vladimir P. Torchilin": "Northeastern University", "Karen L. Wooley": "Texas A&M University",
    "Zhenan Bao": "Stanford University", "Daniel G. Nocera": "Harvard University", "Makoto Fujita": "University of Tokyo",
    "William L. Jorgensen": "Yale University", "Charles T. Kresge": "Mobil Research and Development Corporation",
    "Ryong Ryoo": "Korea Advanced Institute of Science and Technology", "Galen D. Stucky": "University of California, Santa Barbara",
    "Jean M. J. Fréchet": "University of California, Berkeley", "Donald A. Tomalia": "Central Michigan University",
    "John E. Bercaw": "California Institute of Technology", "Jens K. Nørskov": "Technical University of Denmark",
    "Eric N. Jacobsen": "Harvard University", "JoAnne Stubbe": "Massachusetts Institute of Technology",
    "Dennis Lo Yuk-Ming": "Chinese University of Hong Kong",
}


def shown(version, field):
    """[(person, [option texts])] in option order."""
    d = json.loads(LISTS[(version, field)].read_text(encoding="utf-8"))
    out = {}
    for o in d["options"]:
        for p in o["people"]:
            out.setdefault(p["name"], []).append(o["option"])
    return list(out.items())


def all_shown():
    """{(field, person): [(version, options)]}"""
    out = {}
    for (v, f) in LISTS:
        for name, opts in shown(v, f):
            out.setdefault((f, name), []).append((v, opts))
    return out


def identity_rows():
    """[(source, row)] of every identity file, this folder first; rows without ids are skipped."""
    rows = []
    for src in (PEOPLE, V1 / "people", PRESEEN / "people"):
        for f in FIELDS:
            p = src / f"{f}_identity.csv"
            if p.exists():
                rows += [(src, r) for r in csv.DictReader(open(p, encoding="utf-8")) if r["openalex_ids"].strip()]
    return rows


def overrides():
    out = {}
    for p in (V1 / "people" / "overrides.yaml", PEOPLE / "overrides.yaml"):
        if p.exists():
            out.update(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    return out


def initials(name):
    """All given-name initials in order: 'C. Frank Bennett' -> ('c', 'f'), 'Franz-Ulrich Hartl' -> ('f', 'u')."""
    import unicodedata
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    t = [x for x in re.split(r"[\s\-\.]+", s) if x and x not in ("jr", "ii", "iii", "iv")]
    return tuple(x[0] for x in t[:-1])


def same_identity(row, name, field):
    """committee.py's same_person; across fields the given-name initials must also agree (C. Frank Bennett is not
    Charles H. Bennett, F. Ulrich Hartl is Franz-Ulrich Hartl)."""
    return cm.same_person(row["person"], name) and (row["field"] == field or initials(row["person"]) == initials(name))


def identity_of(name, rows=None, ov=None, field=None):
    """(openalex ids, affiliation, prior Nobel, source) of a shown person, or None."""
    rows = identity_rows() if rows is None else rows
    ov = overrides() if ov is None else ov
    hit = next(((s, r) for s, r in rows if r["person"] == name), None) or \
        next(((s, r) for s, r in rows if same_identity(r, name, field)), None)
    if hit is None:
        return None
    src, row = hit
    o = next((v for k, v in ov.items() if cm.same_person(k, name)), None)
    ids = (o["author_id"] if o else row["openalex_ids"]).split(";")
    where = "overrides.yaml" if o else str(src.relative_to(HERE.parent))
    return ids, row["institution"] or row["affiliation_given"], row["prior_nobel"], where


def committee_affiliation(field, name):
    import build_options_v2 as b2
    opts, _ = b2.committee_options(field)
    for o in opts:
        for p in o["people"]:
            if cm.same_person(p["name"], name):
                return p.get("affiliation", "")
    return ""


def cmd_missing(a):
    rows, ov = identity_rows(), overrides()
    need = {}
    for (f, name), lists in all_shown().items():
        if identity_of(name, rows, ov, f) is None:
            need.setdefault(f, []).append((name, sorted({v for v, _ in lists})))
    for f in FIELDS:
        print(f"{f}: {len(need.get(f, []))} shown people without an identity")
        for name, vs in need.get(f, []):
            print(f"  {name:<28} in {', '.join(vs)}")
    if a.write:
        PEOPLE.mkdir(exist_ok=True)
        for f, items in need.items():
            lines = [f"{n}\t{committee_affiliation(f, n) or AFFILIATION.get(n, '')}" for n, _ in items]
            (PEOPLE / f"{f}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"-> people/{f}.txt ({len(lines)} people)")


def queries(fields=None):
    return {f: [tuple((ln.split("\t") + [""])[:2]) for ln in (PEOPLE / f"{f}.txt").read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")] for f in (fields or FIELDS) if (PEOPLE / f"{f}.txt").exists()}


def cmd_dryrun(a):
    sys.path.insert(0, str(REPO / "pipeline"))
    import profile_person as pp                # noqa: E402
    npc = pp.npc
    qs = queries(a.fields)
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
        lines = [time.strftime("%H:%M:%S start (cards_pipeline_v2.py dryrun: profile_person.resolve on the authors subset)")]
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
    where = {(f, n): "; ".join(f"{v}: " + " | ".join(o.split(" — ")[0][:50] for o in opts) for v, opts in lists)
             for (f, n), lists in all_shown().items()}
    for f, q in queries(a.fields).items():
        bl = pe.blocks((PEOPLE / f"{f}_dryrun.log").read_text(encoding="utf-8"))
        choices = (yaml.safe_load((PEOPLE / f"{f}_choices.yaml").read_text(encoding="utf-8"))
                   if (PEOPLE / f"{f}_choices.yaml").exists() else None) or {}
        rows = []
        for name, aff in q:
            r = pe.parse(bl.get(name, ""))
            if name in choices:
                r = {**r, "ids": choices[name]["author_id"].split(";"), "how": "chosen by hand: " + choices[name]["reason"],
                     "note": (r["note"] + "; " if r["note"] else "") + "dry-run: " + (", ".join(pe.parse(bl.get(name, ""))["ids"]) or "no pick")}
            row = {"field": f, "options": where.get((f, name), ""), "person": name, "affiliation_given": aff,
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
                qq = con.sql(f"SELECT inventor_id, round(confidence, 2) FROM read_parquet('{pe.PQRS}') "
                             f"WHERE author_id IN ({ids_sql}) AND confidence >= 0.5 ORDER BY confidence DESC").fetchall()
                row["pqrs_inventors"] = "; ".join(f"{i} ({c})" for i, c in qq)
                row["inventor_source_expected"] = "pqrs crosswalk" if qq else "PatentsView name search (no pqrs inventor)"
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
                  f"{' | Nobel: ' + r['prior_nobel'] if r['prior_nobel'] else ''}{' | ' + r['note'][:100] if r['note'] else ''}"
                  f"\n      top: {r['top_works'][:230]}")


def cmd_living(a):
    import check_living as cl                   # ../preseen/check_living.py (cache in ../preseen/committee/)
    cache = json.loads(cl.CACHE.read_text()) if cl.CACHE.exists() else {}
    rows = []
    for (f, name) in all_shown():
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
    PEOPLE.mkdir(exist_ok=True)
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
    import build_cards as bc
    npc = pp.npc
    rows_id, ov = identity_rows(), overrides()
    sets = {}
    for (f, name) in all_shown():
        got = identity_of(name, rows_id, ov, f)
        if got is None:
            print(f"no identity for {name} ({f}); run identity first")
            continue
        sets.setdefault(";".join(got[0]), name)
    if a.no_name_search:
        os.environ["NP_NAME_SEARCH"] = "off"         # read by the notebook in the job (sbatch --export=ALL)
    con = npc.duck(8, "16GB")
    rows, todo = [], {}
    for key, name in sets.items():
        if a.only and name not in a.only:
            continue
        if not a.force and bc.find_profile(key.split(";")) is not None:   # profiled before
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
    if rows:
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
    seed = V1 / "cards" / "_titles_cache.json"
    if not bc.TITLE_CACHE.exists() and seed.exists():
        bc.TITLE_CACHE.write_text(seed.read_text())
    ref = pd.read_csv(PRESEEN / "cards" / "laureate_reference.csv")
    y0, y1 = bc.CFG["profiles"]["laureate_reference_years"]
    rows_id, ov = identity_rows(), overrides()
    index = []
    for (v, f) in LISTS:
        out = cards / v / f
        out.mkdir(parents=True, exist_ok=True)
        (out / "00_definitions.md").write_text(bc.DEFINITIONS.format(year_max=bc.YEAR_MAX, field_name=bc.CFG["fields"][f]["prize"],
                                                                     y0=y0, y1=y1))
        for name, opts in shown(v, f):
            got = identity_of(name, rows_id, ov, f)
            if got is None:
                index.append({"version": v, "field": f, "person": name, "card": "", "profile": "NO IDENTITY", "identity_from": ""})
                continue
            ids, aff, prior, src = got
            text, folder = bc.card(f, name, ids, opts, aff, prior, ref)
            path = out / f"{bc.person_slug(name)}.md"
            path.write_text(text, encoding="utf-8")
            index.append({"version": v, "field": f, "person": name, "card": f"{v}/{f}/{path.name}", "openalex_ids": ";".join(ids),
                          "profile": folder.name if folder else "NO PROFILE", "identity_from": src})
    with open(cards / "index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["version", "field", "person", "card", "openalex_ids", "profile", "identity_from"])
        w.writeheader()
        w.writerows(index)
    for (v, f) in LISTS:
        rows = [r for r in index if r["field"] == f and r["version"] == v]
        bad = [r["person"] for r in rows if r["profile"] in ("NO PROFILE", "NO IDENTITY")]
        print(f"{v} {f}: {len(rows)} cards in cards/{v}/{f}/; without profile: {bad}")


def cmd_check(a):
    """Every shown person: identity, profile, card file, card built from a profile, card lists the person's options."""
    import build_cards as bc
    living = {(r["field"], r["person"]): r for r in csv.DictReader(open(PEOPLE / "living_check.csv", encoding="utf-8"))} \
        if (PEOPLE / "living_check.csv").exists() else {}
    no_profile_text = bc.CFG["profiles"]["no_profile_card"].strip()[:40]
    notes = (yaml.safe_load((PEOPLE / "living_notes.yaml").read_text(encoding="utf-8"))
             if (PEOPLE / "living_notes.yaml").exists() else None) or {}
    rows_id, ov = identity_rows(), overrides()
    problems, n = [], 0
    for (v, f) in LISTS:
        for name, opts in shown(v, f):
            n += 1
            got = identity_of(name, rows_id, ov, f)
            if got is None:
                problems.append((v, f, name, "no identity"))
                continue
            if bc.find_profile(got[0]) is None:
                problems.append((v, f, name, f"no profile for {';'.join(got[0])}"))
            card = HERE / "cards" / v / f / f"{bc.person_slug(name)}.md"
            if not card.exists():
                problems.append((v, f, name, "no card file"))
                continue
            text = card.read_text(encoding="utf-8")
            if no_profile_text in text or "## Impact" not in text:
                problems.append((v, f, name, "card has no profile data"))
            if any(o not in text for o in opts):
                problems.append((v, f, name, "card does not list all of the person's options"))
            if living.get((f, name), {}).get("status", "").startswith("DECEASED") and name not in notes:
                problems.append((v, f, name, "shown although deceased per the living check"))
    print(f"{n} shown person-cards checked (v1 + v2, three fields); problems: {len(problems)}")
    for v, f, name, why in problems:
        print(f"  {v} {f:<9} {name:<28} {why}")
    return 1 if problems else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("missing"); s.add_argument("--write", action="store_true")
    s = sub.add_parser("dryrun"); s.add_argument("--threads", type=int, default=8); s.add_argument("--fields", nargs="+")
    s = sub.add_parser("identity"); s.add_argument("--fields", nargs="+")
    sub.add_parser("living")
    s = sub.add_parser("submit"); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--only", nargs="+"); s.add_argument("--force", action="store_true")
    s.add_argument("--no-name-search", action="store_true", help="NP_NAME_SEARCH=off: no patent name search")
    sub.add_parser("cards")
    sub.add_parser("check")
    a = ap.parse_args()
    sys.exit({"missing": cmd_missing, "dryrun": cmd_dryrun, "identity": cmd_identity, "living": cmd_living,
              "submit": cmd_submit, "cards": cmd_cards, "check": cmd_check}[a.cmd](a))


if __name__ == "__main__":
    main()
