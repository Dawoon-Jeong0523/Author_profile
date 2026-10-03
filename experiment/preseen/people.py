#!/usr/bin/env python3
"""people.py: identity table of the people in the candidate lists (SPEC §8).

    $PY people.py identity --field medicine     # people/<field>_dryrun.log -> people/<field>_identity.csv

Reads the dry-run log of `pipeline/profile_person.py --names-file people/<field>.txt --dry-run` (one "=== name" block
per person: Nobel laureate line, candidate table, "picked ..." or "NOT RESOLVED"). For every chosen OpenAlex id it adds,
from the free OpenAlex API, the display name, ORCID, last known institution, works and citations, and the three most
cited works (a list query: without an API key it fails while this IP's daily budget is used up; re-run later); from the pqrs crosswalk (cache/pqrs_dataset.parquet, confidence >= 0.5, as the pipeline) whether an
inventor id is expected from pqrs or from the PatentsView name search (the final source is in the profile's record).
People that need a choice are listed with the reason; resolve them one by one with profile_person.py --affiliation,
--orcid, --author-id or --pick.
"""
import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import duckdb
import requests
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OA = "https://api.openalex.org"
UA = {"User-Agent": "nobel-preseen-identity/0.1 (academic research; python-requests)"}
PQRS = REPO / "cache" / "pqrs_dataset.parquet"


def blocks(log):
    """{query name: block text} from a dry-run log."""
    out, name, buf = {}, None, []
    for ln in log.splitlines():
        if ln.startswith("=== "):
            if name:
                out[name] = "\n".join(buf)
            name, buf = ln[4:].strip(), []
        elif name:
            buf.append(ln)
    if name:
        out[name] = "\n".join(buf)
    return out


def parse(block):
    picked = re.search(r"^query .*?: picked (A\d+) (.*?) \[(.*?)\](?:; same-name fragments (.*))?$", block, re.M)
    given = re.search(r"^author id given: (.*)$", block, re.M)
    laureate = re.search(r"^Nobel laureate: (.*?) \(PrizeAtlas\)$", block, re.M)
    several = re.search(r"^the name matches several Nobel laureates: (.*)$", block, re.M)
    unlinked = re.search(r"^WARNING: the chosen author is not linked to the laureate (.*)$", block, re.M)
    failed = re.search(r"^NOT RESOLVED: (.*)$", block, re.M)
    if picked:
        ids = [picked.group(1)] + [x.strip() for x in (picked.group(4) or "").split(",") if x.strip()]
        how = picked.group(3)
    elif given:
        ids, how = [x for x in given.group(1).split(";") if x], "author id given"
    else:
        ids, how = [], ""
    return {"ids": ids, "how": how, "laureate": laureate.group(1) if laureate else "",
            "note": "; ".join(x for x in [several and f"several laureates: {several.group(1)}",
                                          unlinked and f"not linked to laureate {unlinked.group(1)}",
                                          failed and f"NOT RESOLVED: {failed.group(1)}"] if x)}


def oa(path, params=None):
    for attempt in range(4):
        try:
            r = requests.get(OA + path, params=params, headers=UA, timeout=30)
            if r.ok:
                return r.json()
            if r.status_code == 429 and "budget" in r.text.lower():
                return {"_error": "OpenAlex 429: daily budget of this IP used up (resets 00:00 UTC)"}
            if r.status_code in (429, 500, 502, 503):
                time.sleep(5 * (attempt + 1))
                continue
            return {}
        except requests.RequestException:
            time.sleep(5)
    return {}


def cmd_identity(a):
    field = a.field
    cand = json.loads((HERE / "committee" / field / "candidates.json").read_text())
    options = {}
    for o in cand["options"]:
        for p in o.get("people", []):
            options.setdefault(p["name"], []).append(o["rank"])
    log = (HERE / "people" / (a.log or f"{field}_dryrun.log")).read_text()
    bl = blocks(log)
    people = [ln.split("\t") for ln in (HERE / "people" / f"{field}.txt").read_text().splitlines()
              if ln.strip() and not ln.startswith("#")]
    cpath = HERE / "people" / f"{field}_choices.yaml"
    choices = (yaml.safe_load(cpath.read_text()) if cpath.exists() else None) or {}
    con = duckdb.connect()
    con.execute("SET threads = 2")
    rows = []
    for parts in people:
        name, aff = parts[0], (parts[1] if len(parts) > 1 else "")
        r = parse(bl.get(name, ""))
        if name in choices:                                  # people/<field>_choices.yaml: decided by hand
            r = {**r, "ids": choices[name]["author_id"].split(";"), "how": "chosen by hand: " + choices[name]["reason"],
                 "note": (r["note"] + "; " if r["note"] else "") + "dry-run: " + (", ".join(parse(bl.get(name, ""))["ids"]) or "no pick")}
        row = {"field": field, "options": ";".join(map(str, options.get(name, []))), "person": name,
               "affiliation_given": aff, "status": "resolved" if r["ids"] else ("needs a choice" if "NOT RESOLVED" in r["note"] else "missing in log"),
               "openalex_ids": ";".join(r["ids"]), "choice": r["how"], "prior_nobel": r["laureate"], "note": r["note"],
               "display_name": "", "orcid": "", "institution": "", "works": "", "citations": "",
               "top_works": "", "inventor_source_expected": "", "pqrs_inventors": ""}
        if r["ids"]:
            au = oa(f"/authors/{r['ids'][0]}")
            row.update(display_name=au.get("display_name", ""), orcid=(au.get("orcid") or "").rsplit("/", 1)[-1],
                       institution="; ".join(i.get("display_name", "") for i in (au.get("last_known_institutions") or [])[:2]),
                       works=au.get("works_count", ""), citations=au.get("cited_by_count", ""))
            w = oa("/works", {"filter": "author.id:" + "|".join(r["ids"]), "sort": "cited_by_count:desc", "per-page": 3,
                              "select": "title,publication_year,cited_by_count"})
            row["top_works"] = w.get("_error") or " | ".join(
                f"{x.get('title')} ({x.get('publication_year')}; {x.get('cited_by_count')} cit.)" for x in w.get("results", []))
            ids_sql = ", ".join(f"'{i}'" for i in r["ids"])
            q = con.sql(f"SELECT inventor_id, round(confidence, 2) AS c FROM read_parquet('{PQRS}') "
                        f"WHERE author_id IN ({ids_sql}) AND confidence >= 0.5 ORDER BY confidence DESC").fetchall()
            row["pqrs_inventors"] = "; ".join(f"{i} ({c})" for i, c in q)
            row["inventor_source_expected"] = "pqrs crosswalk" if q else "PatentsView name search (no pqrs inventor)"
            time.sleep(0.2)
        rows.append(row)
    out = HERE / "people" / f"{field}_identity.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    n = {s: sum(r["status"] == s for r in rows) for s in ("resolved", "needs a choice", "missing in log")}
    print(f"{field}: {out.relative_to(HERE)}: {len(rows)} people; {n}")
    for r in rows:
        flag = "" if r["status"] == "resolved" else "  <-- " + r["status"]
        print(f"  [{r['options']:>5}] {r['person']:<26} {r['openalex_ids'][:40]:<40} {r['display_name'][:24]:<24} "
              f"orcid={r['orcid'] or '-':<19} {str(r['works']):>5}w {str(r['citations']):>7}c {r['choice'][:40]}"
              f"{' | Nobel: ' + r['prior_nobel'] if r['prior_nobel'] else ''}{' | ' + r['note'][:120] if r['note'] else ''}{flag}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("identity")
    s.add_argument("--field", required=True)
    s.add_argument("--log", help="dry-run log in people/ (default <field>_dryrun.log)")
    a = ap.parse_args()
    {"identity": cmd_identity}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
