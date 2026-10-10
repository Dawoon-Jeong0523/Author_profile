#!/usr/bin/env python3
"""check_living_econ.py: are the people of the step-6 candidate pool alive? (Wikidata, free read-only API, no key)

    $PY check_living_econ.py            # people of ../06_candidates/results/pool.csv -> living_check.csv

Reuses the lookup of ../../experiment/preseen/check_living.py (name variants, wbsearchentities, P569/P570, pacing,
429 handling) with an occupation filter widened to economists, political scientists and legal scholars. Cache in
living_cache.json (no-matches and failed lookups are asked again). Wikidata can lag behind very recent deaths and a
same-name person can be matched: the CSV is a screen, not proof; rows that need a look are printed.
"""
import csv
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = HERE.parent / "06_candidates" / "results" / "pool.csv"
SRC = HERE.parent.parent / "experiment" / "preseen" / "check_living.py"
spec = importlib.util.spec_from_file_location("check_living", SRC)
cl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cl)
cl.SCIENCE = re.compile(r"econom|financ|political scien|politolog|statistic|law|legal|jurist|judge|scien|professor|"
                        r"academic|scholar|research|historian|mathemat", re.I)
CACHE = HERE / "living_cache.json"


def main():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    rows, attention = [], []
    with POOL.open() as fh:
        pool = list(csv.DictReader(fh))
    for o in pool:
        for name, born in zip(o["people"].split("; "), o["born"].split("; ")):
            r = cache.get(name)
            if r is None or r["status"] in ("no match", "lookup failed"):
                try:
                    r = cl.lookup(name)
                except cl.LookupFailed as e:
                    r = {"status": "lookup failed", "qid": "", "label": "", "description": str(e), "born": "", "died": "", "n": 0}
                cache[name] = r
                CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
            row = {"field": o["field"], "k": o["rank_in_field"], "name": name, "born_stated": born,
                   **{k: r.get(k, "") for k in ("status", "qid", "label", "description", "born", "died", "n", "others")}}
            rows.append(row)
            year_ok = not (row["born"] and born.isdigit() and abs(int(row["born"][:4]) - int(born)) > 1)
            if not r["status"].startswith("living") or r["n"] != 1 or not year_ok:
                attention.append({**row, "year_mismatch": not year_ok})
    out = HERE / "living_check.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} people ({len({r['name'] for r in rows})} distinct) -> {out.name}; "
          f"deceased per Wikidata: {sum(r['status'].startswith('DECEASED') for r in rows)}")
    print("needs a look (deceased, no match, several candidates, or birth year differs from the stated one by > 1):")
    for r in attention:
        print(f"  {r['field'][:14]:<14} #{r['k']:<2} {r['name']:<28} {r['status'][:44]:<44} {r['qid']:<10} {r['label'][:28]:<28} "
              f"| {r['description'][:50]} | b.{r['born'][:4]} (stated {r['born_stated']}) d.{r['died']}"
              + (" | YEAR MISMATCH" if r["year_mismatch"] else "") + (f" | {r['others'][:120]}" if r.get("others") else ""))


if __name__ == "__main__":
    main()
