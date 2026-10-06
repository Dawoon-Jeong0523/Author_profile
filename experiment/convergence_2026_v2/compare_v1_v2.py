#!/usr/bin/env python3
"""compare_v1_v2.py: the 30 options of v1 (pooled people, top three by weight) against v2 (committee lineup with the
highest mean person score), per field.

    $PY compare_v1_v2.py [--fields medicine physics chemistry]

Both versions are built in memory with this folder's decisions.yaml, so the only difference is the rule for the people
shown. For physics and chemistry the v1 build is checked against ../convergence_2026/results/options_<field>.json (the
saved v1 list); medicine has no saved v1 list. For every committee option the plurality lineup (most support: summed
normalized Borda points of the nominations that wrote exactly that set of people) is reported next to the v2 choice.
Writes results/compare_<field>.csv, results/compare.md and the v1 lists themselves to results/v1_rule/ (v1's write();
medicine's v1 list exists only here).
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import yaml
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "convergence_2026"
sys.path.insert(0, str(V1))
sys.path.insert(0, str(HERE))
import build_options as v1  # noqa: E402
import build_options_v2 as v2  # noqa: E402

OUT = HERE / "results"
# announced laureates (nobelprize.org); chemistry is announced on 2026-10-07
OUTCOMES = {"medicine": ("optogenetics", ["Karl Deisseroth", "Peter Hegemann", "Georg Nagel"]),
            "physics": ("neutrino", ["Francis Halzen"])}


def names(o):
    return [p["name"] for p in o["shown"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", nargs="+", default=["medicine", "physics", "chemistry"])
    a = ap.parse_args()
    dec = yaml.safe_load((HERE / "decisions.yaml").read_text(encoding="utf-8"))
    md = ["# v1 vs v2: people shown on the 30 options", "",
          "v1 = people of all merged nominations pooled, top three by committee weight + convergence points. "
          "v2 = the committee lineup (the set of people one nomination wrote) with the highest mean person score. "
          "Same decisions.yaml, same option scores otherwise (committee points + convergence points of the people shown). "
          "Support share = share of the option's committee points that came from nominations writing exactly that "
          "lineup.", ""]
    for field in a.fields:
        res1 = v1.build(field, 30, 1.0, dec, [])
        t1 = res1[0]
        t2 = v2.build(field, 30, 1.0, dec, [])[0]
        v1.OUT = OUT / "v1_rule"                  # the v1 list of every field, saved here (cards for v1 read it)
        v1.write(field, *res1, 30, 1.0, [], {})
        saved = V1 / "results" / f"options_{field}.json"
        check = ""
        if saved.exists():
            s = json.loads(saved.read_text())["options"]
            same = [x["option"] for x in s] == [f"{o['discovery']} — {', '.join(names(o))}" for o in t1]
            check = "v1 rebuilt here = saved v1 list" if same else "WARNING: v1 rebuilt here differs from the saved v1 list"
        r1 = {o["discovery"]: (r, o) for r, o in enumerate(t1, 1)}
        r2 = {o["discovery"]: (r, o) for r, o in enumerate(t2, 1)}
        rows = []
        for d in list(r2) + [d for d in r1 if d not in r2]:
            (a1, o1), (a2, o2) = r1.get(d, (None, None)), r2.get(d, (None, None))
            o = o2 or o1
            cands = o2["lineup_candidates"] if o2 else []
            tot = sum(x["support"] for x in cands)
            plural = max(cands, key=lambda x: (x["support"], -len(x["people"]))) if cands else None
            rows.append({
                "discovery": d, "committee_rank": o["committee_rank"] or "",
                "v1_rank": a1 or "", "v2_rank": a2 or "",
                "v1_people": "; ".join(names(o1)) if o1 else "", "v2_people": "; ".join(names(o2)) if o2 else "",
                "v1_n": len(names(o1)) if o1 else "", "v2_n": len(names(o2)) if o2 else "",
                "v1_score": round(o1["score"], 3) if o1 else "", "v2_score": round(o2["score"], 3) if o2 else "",
                "people_changed": bool(o1 and o2 and set(names(o1)) != set(names(o2))),
                "n_lineups": len(cands) or "",
                "v2_lineup_support_share": round(cands[0]["support"] / tot, 3) if cands else "",
                "plurality_lineup": "; ".join(p["name"] for p in plural["people"]) if plural else "",
                "plurality_support_share": round(plural["support"] / tot, 3) if plural else "",
                "v2_is_plurality": (cands[0] is plural) if cands else "",
                "v1_lineup_support_share": round(next((x["support"] for x in cands if {p["name"] for p in x["people"]}
                                                      == set(names(o1))), 0) / tot, 3) if cands and o1 else "",
            })
        with open(OUT / f"compare_{field}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

        both = [x for x in rows if x["v1_rank"] and x["v2_rank"]]
        rho = spearmanr([x["v1_rank"] for x in both], [x["v2_rank"] for x in both]).statistic
        size = lambda col: {k: sum(1 for x in rows if x[col] == k) for k in (1, 2, 3)}
        changed = [x for x in both if x["people_changed"]]
        com = [x for x in rows if x["v2_rank"] and x["committee_rank"]]
        md += [f"## {field.capitalize()}", "", f"- {check}" if check else "- no saved v1 list (v1 rule built here with "
               "the same decisions.yaml)",
               f"- options in both top-30 lists: {len(both)}; in v2 only: "
               f"{[x['discovery'][:60] for x in rows if x['v2_rank'] and not x['v1_rank']] or 'none'}; in v1 only: "
               f"{[x['discovery'][:60] for x in rows if x['v1_rank'] and not x['v2_rank']] or 'none'}",
               f"- Spearman of the ranks of the shared options: {rho:.3f}",
               f"- people per option (1 / 2 / 3): v1 {size('v1_n')}, v2 {size('v2_n')}",
               f"- options whose people changed: {len(changed)} of {len(both)}",
               f"- committee options where the v2 lineup is the plurality lineup: "
               f"{sum(1 for x in com if x['v2_is_plurality'])} of {len(com)}; mean support share of the shown lineup: "
               f"v1 {sum(x['v1_lineup_support_share'] for x in com if x['v1_rank']) / max(1, sum(1 for x in com if x['v1_rank'])):.0%}"
               f", v2 {sum(x['v2_lineup_support_share'] for x in com) / len(com):.0%}", ""]
        if field in OUTCOMES:
            key, laureates = OUTCOMES[field]
            x = next(x for x in rows if key in x["discovery"].lower())
            md += [f"- announced: {', '.join(laureates)}. This option: v1 rank {x['v1_rank']} ({x['v1_people']}), "
                   f"v2 rank {x['v2_rank']} ({x['v2_people']}); plurality lineup {x['plurality_lineup']}", ""]
        md += ["| v2 # | v1 # | Discovery | v1 people | v2 people | v2 lineup share | plurality lineup (share) |",
               "|---:|---:|---|---|---|---:|---|"]
        for x in changed:
            md.append(f"| {x['v2_rank']} | {x['v1_rank']} | {x['discovery'][:70]} | {x['v1_people']} | {x['v2_people']} | "
                      f"{x['v2_lineup_support_share'] if x['v2_lineup_support_share'] == '' else format(x['v2_lineup_support_share'], '.0%')} | "
                      f"{x['plurality_lineup']}"
                      + (f" ({x['plurality_support_share']:.0%})" if x["plurality_support_share"] != "" else "") + " |")
        md.append("")
        print(f"{field}: {check or 'no saved v1'}; changed {len(changed)}/{len(both)}; rho {rho:.3f}; "
              f"sizes v1 {size('v1_n')} v2 {size('v2_n')}")
    (OUT / "compare.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
