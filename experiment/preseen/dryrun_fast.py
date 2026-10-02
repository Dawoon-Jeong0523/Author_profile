#!/usr/bin/env python3
"""dryrun_fast.py: the dry-run of `pipeline/profile_person.py --names-file ... --dry-run`, faster.

    $PY dryrun_fast.py --fields medicine physics chemistry [--no-api]

The CLI scans the 6 GB snapshot authors table once per person (about 1-1.5 min each). This script calls the same
`profile_person.resolve()` (imported, unchanged) for every line of people/<field>.txt, but first writes one subset of
cache/openalex_authors.parquet with the rows the name search can return for these people (works_count >= 1 and the
surname inside display_name or display_name_alternatives, the same `contains` test as np_common.find_author_candidates)
and points np_common.OA_AUTHORS_PQ at it. Candidates and choices are therefore the same as the CLI's. Output: the CLI's
log format in people/<field>_dryrun_fast.log (one "=== name" block per person).
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "pipeline"))
os.environ["LD_LIBRARY_PATH"] = "/project/jevans/Dawoon/env/Curvature/lib"
import profile_person as pp            # noqa: E402  (also puts notebook/ on sys.path and imports np_common)
npc = pp.npc
SUBSET = HERE / "people" / "_authors_subset.parquet"


def queries(field):
    out = []
    for ln in (HERE / "people" / f"{field}.txt").read_text(encoding="utf-8").splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in ln.split("\t")]
        out.append((parts[0], parts[1] if len(parts) > 1 and parts[1] else None))
    return out


def build_subset(con, names):
    lasts = sorted({npc._raw_name_tokens(npc._clean_person(n))[-1] for n in names})
    pat = "|".join(re.escape(x) for x in lasts)
    t0 = time.time()
    con.execute(f"""COPY (SELECT * FROM read_parquet('{npc.OA_AUTHORS_PQ}')
                          WHERE works_count >= 1
                            AND (regexp_matches(lower(strip_accents(display_name)), '{pat}')
                                 OR regexp_matches(lower(strip_accents(coalesce(display_name_alternatives, ''))), '{pat}')))
                    TO '{SUBSET}' (FORMAT parquet)""")
    n = con.sql(f"SELECT count(*) FROM read_parquet('{SUBSET}')").fetchone()[0]
    print(f"subset: {n:,} author rows for {len(lasts)} surnames in {time.time() - t0:.0f} s -> {SUBSET.relative_to(HERE)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fields", nargs="+", default=["medicine", "physics", "chemistry"])
    ap.add_argument("--no-api", action="store_true", help="snapshot candidates only (no live OpenAlex author search)")
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    con = npc.duck(a.threads, "16GB")
    allq = {f: queries(f) for f in a.fields}
    build_subset(con, [n for qs in allq.values() for n, _ in qs])
    npc.OA_AUTHORS_PQ = SUBSET                      # read by find_author_candidates at call time
    args = SimpleNamespace(author_id=None, orcid=None, pick=None, dominance=3.0, no_merge=False, no_api=a.no_api,
                           label_year=None, label_field=None, affiliation=None)
    for field, qs in allq.items():
        lines = [time.strftime("%H:%M:%S start (dryrun_fast.py: profile_person.resolve on the authors subset)")]
        log = lambda s, lines=lines: lines.append(str(s))
        n_ok = n_choice = 0
        for name, aff in qs:
            lines += ["", f"=== {name}"]
            args.affiliation = aff
            try:
                ids, labels, text, needs = pp.resolve(con, name, args, log=log)
            except ValueError as e:
                ids, text, needs = None, str(e), False
            if ids is None:
                lines.append(f"NOT RESOLVED: {text}")
                n_choice += needs
            else:
                n_ok += 1
        lines.append(f"EXIT={0 if n_ok == len(qs) else (2 if n_choice else 1)}")
        (HERE / "people" / f"{field}_dryrun_fast.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{field}: {len(qs)} people, {n_ok} resolved, {n_choice} need a choice -> people/{field}_dryrun_fast.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
