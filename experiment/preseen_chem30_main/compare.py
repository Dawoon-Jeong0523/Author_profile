#!/usr/bin/env python3
"""compare.py: the three "cards as the main evidence" Chemistry forecasts side by side (v1, v2, Preseen's own list).

    python3 compare.py            # results/compare.csv, results/compare.md, results/tldr_<list>.md

v1 and v2 have the same 30 discoveries (only the named people differ) and are matched by the discovery text. Preseen's
list words its discoveries differently; PRESEEN_TO_V1 matches 17 of its options to a v1 discovery by hand (two Preseen
options, polymer delivery and Langer's controlled release, both map to v1's nanoparticle-delivery option and are summed);
the other 13 have no counterpart. Lists that have not finished are skipped.
"""
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
LISTS = ["v1", "v2", "preseen"]
# Preseen option number -> v1 option number (same discovery), checked by hand 2026-10-06
PRESEEN_TO_V1 = {1: 1, 2: 3, 3: 9, 4: 5, 5: 11, 6: 23, 7: 2, 11: 28, 12: 12, 14: 4, 16: 27, 17: 29, 18: 17, 21: 15,
                 24: 7, 28: 6, 30: 4}


def disc(o):
    return o.split(" — ")[0]


def people(o):
    return o.split(" — ", 1)[1] if " — " in o else ""


def load(lst):
    q = json.loads((HERE / "questions" / f"{lst}.json").read_text())
    runs = HERE / "preseen_exp" / lst / "runs.csv"
    if not runs.exists():
        return None
    row = next(r for r in csv.DictReader(open(runs)) if r["status"] == "completed")
    p = json.loads(row["forecast_data"])["payload"]["probabilities"]
    run = json.loads(next((HERE / "preseen_exp" / lst / "runs").glob("*.json")).read_text())
    return {"options": q["options"], "p": [p[o] for o in q["options"]], "write_up": run["forecast"]["write_up"],
            "started": row["created_at"], "finished": row["finished_at"]}


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: -v[i])
    r = [0] * len(v)
    for k, i in enumerate(order, 1):
        r[i] = k
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    return cov / math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))


def entropy(p):
    return -sum(x * math.log2(x) for x in p if x > 0)


def main():
    OUT.mkdir(exist_ok=True)
    R = {l: load(l) for l in LISTS}
    done = [l for l in LISTS if R[l]]
    v1 = R["v1"]
    rows = []
    for i, o in enumerate(v1["options"], 1):
        d = disc(o)
        row = {"v1_n": i, "discovery": d, "v1_people": people(o), "v1_p": v1["p"][i - 1]}
        if R["v2"]:
            j = next(k for k, x in enumerate(R["v2"]["options"]) if disc(x) == d or
                     (i == 5 and "electron transfer in proteins" in x))
            row.update(v2_people=people(R["v2"]["options"][j]), v2_p=R["v2"]["p"][j])
        if R["preseen"]:
            ks = [k for k, v in PRESEEN_TO_V1.items() if v == i]
            if ks:
                row.update(pre_n=";".join(map(str, ks)), pre_people=" | ".join(people(R["preseen"]["options"][k - 1]) for k in ks),
                           pre_p=sum(R["preseen"]["p"][k - 1] for k in ks))
        rows.append(row)
    if R["preseen"]:
        for k, o in enumerate(R["preseen"]["options"], 1):
            if k not in PRESEEN_TO_V1:
                rows.append({"discovery": disc(o), "pre_n": k, "pre_people": people(o), "pre_p": R["preseen"]["p"][k - 1]})
    key = "v2_p" if R["v2"] else "v1_p"
    rows.sort(key=lambda r: -(r.get(key) if r.get(key) is not None else -1 + r.get("pre_p", 0)))
    cols = ["discovery", "v1_n", "v1_people", "v1_p", "v2_people", "v2_p", "pre_n", "pre_people", "pre_p"]
    with open(OUT / "compare.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows([{c: r.get(c, "") for c in cols} for r in rows])

    md = ["# Chemistry 2026, cards as the main evidence: v1 vs v2 vs Preseen's list", ""]
    for l in done:
        p = R[l]["p"]
        top = sorted(range(30), key=lambda i: -p[i])[:5]
        md += [f"- **{l}** ({R[l]['started'][11:16]}-{R[l]['finished'][11:16]} UTC): top 5 "
               + "; ".join(f"{disc(R[l]['options'][i])[:60]} {100 * p[i]:.1f} %" for i in top)
               + f"; max {100 * max(p):.1f} %, entropy {entropy(p):.2f} bits (uniform {math.log2(30):.2f})"]
    if R["v2"]:
        a = [r["v1_p"] for r in rows if "v1_p" in r and "v2_p" in r]
        b = [r["v2_p"] for r in rows if "v1_p" in r and "v2_p" in r]
        md += [f"- v1 vs v2 (same 30 discoveries): Spearman {spearman(a, b):.2f}, mean |diff| "
               f"{100 * sum(abs(x - y) for x, y in zip(a, b)) / len(a):.2f} pp"]
    if R["preseen"]:
        sh = [r for r in rows if r.get("v1_n") and r.get("pre_p") is not None]
        md += [f"- Preseen's list: {sum(R['preseen']['p'][k - 1] for k in PRESEEN_TO_V1):.0%} of its probability on the 17 "
               f"options shared with v1/v2, {1 - sum(R['preseen']['p'][k - 1] for k in PRESEEN_TO_V1):.0%} on its 13 own "
               f"discoveries; v1 vs Preseen on the {len(sh)} shared discoveries: Spearman "
               f"{spearman([r['v1_p'] for r in sh], [r['pre_p'] for r in sh]):.2f}"
               + (f", v2 vs Preseen {spearman([r['v2_p'] for r in sh], [r['pre_p'] for r in sh]):.2f}" if R["v2"] else "")]
    md += ["", "| Discovery | v1 | v2 | Preseen list |", "|---|---:|---:|---:|"]
    f = lambda x: "" if x is None or x == "" else f"{100 * x:.1f}"
    for r in rows:
        md.append(f"| {r['discovery'][:80]} | {f(r.get('v1_p'))} | {f(r.get('v2_p'))} | {f(r.get('pre_p'))} |")
    (OUT / "compare.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for l in done:
        (OUT / f"write_up_{l}.md").write_text(R[l]["write_up"], encoding="utf-8")
    print("\n".join(md[:8]))
    print(f"lists done: {done}")


if __name__ == "__main__":
    main()
