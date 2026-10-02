#!/usr/bin/env python3
"""submit_profiles.py: submit the Slurm profile of every person in people/<field>_identity.csv (SPEC §8).

    $PY submit_profiles.py [--fields medicine physics chemistry] [--dry-run]

Same steps as `pipeline/profile_person.py --author-id "<ids>"` per person (its resolve() and run(), imported unchanged):
the chosen OpenAlex ids, the person's name as the query, no --wait. The CLI's --author-id path scans the 6 GB authors table
once per person; here one scan writes the rows of all ids to a subset that resolve() reads instead. One job per distinct
id set (a person listed in two fields is profiled once). A profile that already exists in output/<first id>/ with the
same ids and window is reused, never re-run (SPEC rule 5). The API keys of this experiment are removed from the
environment of this process before submitting, so `sbatch --export=ALL` does not copy them into the jobs.
Writes people/profile_jobs.csv (person, fields, ids, job id or "reused").
"""
import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CFG = yaml.safe_load((HERE / "config.yaml").read_text())
for var in CFG["api_keys"].values():                  # the profile jobs need none of the experiment's keys
    os.environ.pop(var, None)
sys.path.insert(0, str(REPO / "pipeline"))
os.environ["LD_LIBRARY_PATH"] = "/project/jevans/Dawoon/env/Curvature/lib"
import profile_person as pp            # noqa: E402
npc = pp.npc
SUBSET = HERE / "people" / "_authors_ids_subset.parquet"


def existing(ids):
    man = REPO / "output" / ids[0] / "manifest.json"
    if not man.exists():
        return None
    m = json.loads(man.read_text())
    same = m.get("author_id_check", {}).get("input_ids") == ids
    ym = (m.get("parameters") or {}).get("YEAR_MAX")
    return {"record": m.get("record"), "same_ids": same, "year_max": ym}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fields", nargs="+", default=CFG["order"])
    ap.add_argument("--dry-run", action="store_true", help="list what would be submitted")
    ap.add_argument("--only", nargs="+", help="submit only these people (e.g. one job first, to rebuild stale shared caches)")
    a = ap.parse_args()
    sets = {}
    for f in a.fields:
        for r in csv.DictReader(open(HERE / "people" / f"{f}_identity.csv")):
            s = sets.setdefault(r["openalex_ids"], {"person": r["person"], "fields": []})
            s["fields"].append(f)
    con = npc.duck(8, "16GB")
    all_ids = sorted({int(i[1:]) for k in sets for i in k.split(";")})
    t0 = time.time()
    con.execute(f"COPY (SELECT * FROM read_parquet('{npc.OA_AUTHORS_PQ}') WHERE author_id IN ({', '.join(map(str, all_ids))})) "
                f"TO '{SUBSET}' (FORMAT parquet)")
    print(f"subset of {len(all_ids)} ids written in {time.time() - t0:.0f} s")
    npc.OA_AUTHORS_PQ = SUBSET
    rows = []
    for key, s in sets.items():
        if a.only and s["person"] not in a.only:
            continue
        ids = key.split(";")
        ex = existing(ids)
        if ex and ex["same_ids"] and str(ex["year_max"]) == str(CFG["profiles"]["year_max"]):
            print(f"reused  {s['person']:<26} {key}  ({ex['record']})")
            rows.append({"person": s["person"], "fields": ";".join(s["fields"]), "ids": key, "job": "reused",
                         "submitted": "", "record": ex["record"]})
            continue
        if ex:
            print(f"STOP: {s['person']} {key}: output/{ids[0]} exists with other ids or window ({ex}); not touched")
            rows.append({"person": s["person"], "fields": ";".join(s["fields"]), "ids": key, "job": "exists-different",
                         "submitted": "", "record": ex["record"]})
            continue
        args = SimpleNamespace(author_id=key, orcid=None, pick=None, dominance=3.0, no_merge=False, no_api=True,
                               label_year=None, label_field=None, affiliation=None, year_max=CFG["profiles"]["year_max"],
                               titles=CFG["profiles"]["titles"], local=False, wait=False, mem="64G", cpus=8)
        lines = []
        got, labels, text, _ = pp.resolve(con, s["person"], args, log=lines.append)
        if a.dry_run:
            print(f"would submit {s['person']:<26} {got} {labels}")
            continue
        res = pp.run(got, labels, s["person"], text, args, log=lambda m: print("    " + str(m)))
        print(f"{'submitted' if res.get('ok') else 'FAILED'} {s['person']:<26} {key} job {res.get('job')}", flush=True)
        rows.append({"person": s["person"], "fields": ";".join(s["fields"]), "ids": key, "job": res.get("job") or "failed",
                     "submitted": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "record": ""})
    if rows:
        out = HERE / "people" / "profile_jobs.csv"
        new = not out.exists()
        with open(out, "a", newline="") as fh:                  # appended: one row per submission or reuse
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"people/profile_jobs.csv: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
