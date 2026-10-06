#!/usr/bin/env python3
"""compare.py: the Chemistry forecasts of 6 October side by side.

    python3 compare.py            # results/compare.{csv,md}, results/write_up_<run>.md: the published runs
                                  # results/all_runs/: every run (v1, v2, Preseen's list, main2 too), not pushed

Published: the treatment (arm main3, the main result), the demographic arm and the control, all on the v2 list.

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
LISTS = ["v1", "v2", "preseen", "v2_control", "v2_main2", "v2_main3", "v2_demo"]
PUBLISHED = ["v2_main3", "v2_demo", "v2_control"]
# Preseen option number -> v1 option number (same discovery), checked by hand 2026-10-06
PRESEEN_TO_V1 = {1: 1, 2: 3, 3: 9, 4: 5, 5: 11, 6: 23, 7: 2, 11: 28, 12: 12, 14: 4, 16: 27, 17: 29, 18: 17, 21: 15,
                 24: 7, 28: 6, 30: 4}


ARMS = {  # run -> (name, list, prompt, cards), versions as in the README
    "v2_main3": ("**main3**", "v2 (C3)", "P5: no measure called minor", "K1 + K3 patents"),
    "v2_demo": ("demographic", "v2 (C3)", "P6: P5 + demographic notes", "K1 + K3 patents"),
    "v2_control": ("control", "v2 (C3)", "P0: no notes", "none"),
    "v2": ("v2 main", "v2 (C3)", "P3: translation and collaboration minor", "K1"),
    "v2_main2": ("main2", "v2 (C3)", "P4: collaboration minor, patents count", "K1 + K3 patents"),
    "v1": ("v1 main", "v1 (C2)", "P3", "K1"),
    "preseen": ("Preseen list", "Preseen's own (C4)", "P3", "K1"),
}
PREFIXES = ("for the discovery and development of ", "for the development of ", "for the invention of ",
            "for the discovery of ", "for their discoveries of ", "for pioneering work on ", "for the ", "for ")


def short(d):
    return next((d[len(x):] for x in PREFIXES if d.startswith(x)), d)


def disc(o):
    return o.split(" — ")[0]


def people(o):
    return o.split(" — ", 1)[1] if " — " in o else ""


def load(lst, arm="main", sub=None):
    q = json.loads((HERE / "questions" / f"{lst}.json").read_text())
    sub = sub or lst                                       # state folder (later arms have their own: v2_main3)
    runs = HERE / "preseen_exp" / sub / "runs.csv"
    if not runs.exists():
        return None
    row = next((r for r in csv.DictReader(open(runs)) if r["status"] == "completed" and r["arm"] == arm), None)
    if row is None:
        return None
    p = json.loads(row["forecast_data"])["payload"]["probabilities"]
    run = json.loads(next((HERE / "preseen_exp" / sub / "runs").glob(f"{arm}_*.json")).read_text())
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
    R = {l: load(l) for l in LISTS[:3]}
    R["v2_control"] = load("v2", "control")
    R["v2_main2"] = load("v2", "main2")
    R["v2_main3"] = load("v2", "main3", sub="v2_main3")
    R["v2_demo"] = load("v2", "demo", sub="v2_demo")
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
            if R["v2_control"]:
                row["v2ctl_p"] = R["v2_control"]["p"][j]
            if R["v2_main2"]:
                row["v2m2_p"] = R["v2_main2"]["p"][j]
            if R["v2_main3"]:
                row["v2m3_p"] = R["v2_main3"]["p"][j]
            if R["v2_demo"]:
                row["v2demo_p"] = R["v2_demo"]["p"][j]
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
    cols = ["discovery", "v1_n", "v1_people", "v1_p", "v2_people", "v2_p", "v2m2_p", "v2m3_p", "v2demo_p", "v2ctl_p", "pre_n", "pre_people", "pre_p"]
    ALL = OUT / "all_runs"
    ALL.mkdir(exist_ok=True)
    with open(ALL / "compare_all.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows([{c: r.get(c, "") for c in cols} for r in rows])

    md = ["# Chemistry 2026: the Preseen forecasts side by side", "",
          "Seven runs, one each, on 6 October 2026. Each option is a discovery and the living people it names; v1 and v2 "
          "are the same 30 discoveries with different named people, Preseen's list words its discoveries differently "
          "(17 of its 30 options matched by hand to 16 v1/v2 discoveries, the other 13 listed at the end). Version codes (C = candidate "
          "list, P = prompt, K = cards) as in the [README](../../../README.md#what-changed-between-versions). "
          "Probabilities in %; differences of about 1 point are within the run-to-run spread.", "",
          "## The runs", "",
          "| Run | List | Prompt | Cards | Time (UTC) | Top 3 (discovery — named people, probability) | Max | Entropy (bits; uniform 4.91) |",
          "|---|---|---|---|---|---|---:|---:|"]
    for l in [x for x in ARMS if R[x]]:
        name, lst, prompt, cards = ARMS[l]
        p, opts = R[l]["p"], R[l]["options"]
        top = sorted(range(30), key=lambda i: -p[i])[:3]
        md.append(f"| {name} | {lst} | {prompt} | {cards} | {R[l]['started'][11:16]}–{R[l]['finished'][11:16]} | "
                  + "<br>".join(f"{short(disc(opts[i]))} — {people(opts[i])}, **{100 * p[i]:.1f}**" for i in top)
                  + f" | {100 * max(p):.1f} | {entropy(p):.2f} |")
    md += ["", "## Agreement between runs", ""]
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
    if R["v2_control"]:
        a = [r["v2ctl_p"] for r in rows if "v2ctl_p" in r]
        b = [r["v2_p"] for r in rows if "v2ctl_p" in r]
        c = [r["v1_p"] for r in rows if "v2ctl_p" in r]
        md += [f"- v2 control (same question, no notes) vs v2 main: Spearman {spearman(a, b):.2f}, mean |diff| "
               f"{100 * sum(abs(x - y) for x, y in zip(a, b)) / len(a):.2f} pp; vs v1 main: Spearman {spearman(a, c):.2f}"]
    if R["v2_main2"]:
        a = [r["v2m2_p"] for r in rows if "v2m2_p" in r]
        b = [r["v2_p"] for r in rows if "v2m2_p" in r]
        c = [r["v2ctl_p"] for r in rows if "v2m2_p" in r and "v2ctl_p" in r]
        md += [f"- v2 main2 (patents on the cards, translation no longer 'minor') vs v2 main: Spearman {spearman(a, b):.2f}, "
               f"mean |diff| {100 * sum(abs(x - y) for x, y in zip(a, b)) / len(a):.2f} pp"
               + (f"; vs v2 control: Spearman {spearman(a, c):.2f}" if len(c) == len(a) else "")]
    if R["v2_main3"]:
        a = [r["v2m3_p"] for r in rows if "v2m3_p" in r]
        b = [r["v2_p"] for r in rows if "v2m3_p" in r]
        md += [f"- v2 main3 (patents on the cards, no measure called minor) vs v2 main: Spearman {spearman(a, b):.2f}, mean "
               f"|diff| {100 * sum(abs(x - y) for x, y in zip(a, b)) / len(a):.2f} pp"]
    if R["v2_demo"] and R["v2_main3"]:
        a = [r["v2demo_p"] for r in rows if "v2demo_p" in r]
        b = [r["v2m3_p"] for r in rows if "v2demo_p" in r]
        md += [f"- v2 demographic arm vs v2 main3 (same notes without the demographic ones): Spearman {spearman(a, b):.2f}, "
               f"mean |diff| {100 * sum(abs(x - y) for x, y in zip(a, b)) / len(a):.2f} pp"]
    md += ["", "## All options", "",
           "Sorted by main3. People: the v2 lineup (the people named in the v2 runs); the v1 and Preseen-list columns name "
           "people only where their lineup differs from v2.", "",
           "| # | Discovery | People (v2) | main3 | demographic | control | v2 main | main2 | v1 main | People (v1, if different) | Preseen list | People (Preseen list, if different) |",
           "|---:|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|"]
    f = lambda x: "" if x is None or x == "" else f"{100 * x:.1f}"
    key2 = lambda n: (n.split()[0] + " " + n.split()[-1]).lower() if n.split() else ""   # "Henry Snaith" = "Henry J. Snaith"
    same = lambda x, y: {key2(n) for n in x.split(",")} == {key2(n) for n in y.split(",")}
    key = "v2m3_p" if R["v2_main3"] else "v2_p"
    shown = sorted([r for r in rows if r.get(key) is not None], key=lambda r: -r[key])
    shown += [r for r in rows if r.get(key) is None]                  # Preseen-only discoveries, by Preseen probability
    for k, r in enumerate(shown, 1):
        v2p = r.get("v2_people", "")
        v1p = r.get("v1_people", "")
        prp = r.get("pre_people", "")
        prp = "" if prp and v2p and all(same(x, v2p) for x in prp.split(" | ")) else prp.replace(" | ", " / ")
        m3 = f(r.get("v2m3_p"))
        md.append(f"| {k if r.get(key) is not None else ''} | {r['discovery'].removeprefix('for ')} | {v2p} | "
                  f"{'**' + m3 + '**' if m3 else ''} | {f(r.get('v2demo_p'))} | {f(r.get('v2ctl_p'))} | {f(r.get('v2_p'))} | "
                  f"{f(r.get('v2m2_p'))} | {f(r.get('v1_p'))} | {'' if not v1p or same(v1p, v2p) else v1p} | "
                  f"{f(r.get('pre_p'))} | {prp} |")
    md += ["", "Preseen-list rows that sum two of its options (polymer delivery and controlled release) name both "
               "lineups, separated by /."]
    (ALL / "compare_all.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for l in done:
        (OUT / f"write_up_{l}.md" if l in PUBLISHED else ALL / f"write_up_{l}.md").write_text(R[l]["write_up"], encoding="utf-8")
    if all(R[l] for l in PUBLISHED):
        publish(R, rows)
    print(f"lists done: {done}")


def publish(R, rows):
    """results/compare.md and compare.csv: the treatment (arm main3, the main result), the demographic arm, the control."""
    rows = sorted([r for r in rows if r.get("v2m3_p") is not None], key=lambda r: -r["v2m3_p"])
    cols = [("v2m3_p", "Treatment"), ("v2demo_p", "Demographic"), ("v2ctl_p", "Control")]
    links = {"v2_main3": "https://preseen.com/q/urrByOH0UlbPnAcF-Kk7YA",       # public Preseen pages given by the user
             "v2_demo": "https://preseen.com/q/IRgKh66nV-BgnQslZ6oM0A",
             "v2_control": "https://preseen.com/q/tV5NqBF_m70rlHecLi8aVg"}
    with open(OUT / "compare.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rank_treatment", "discovery", "people", "treatment", "demographic", "control"])
        for k, r in enumerate(rows, 1):
            w.writerow([k, r["discovery"], r["v2_people"]] + [round(r[c], 6) for c, _ in cols])
    m3, dm, ct = ([r[c] for r in rows] for c, _ in cols)
    md = ["# Chemistry 2026: the treatment and its comparison forecasts", "",
          "Three Preseen runs, one each, on 6 October 2026, on the same question: 30 discoveries (the v2 list), each with "
          "the living people it names, no \"Other\". **The treatment is the main result** (profile cards with the patents "
          "tied to each discovery as the main evidence; arm `main3` in the run files); the demographic forecast adds the "
          "demographics of past laureates to the treatment's notes, the control has no notes at all. Prompts and cards: "
          "[README](../../../README.md#chemistry-announced-7-october). Probabilities in %; differences of about one "
          "point are within the run-to-run spread.", "",
          "## The runs", "",
          "| Forecast | Notes given to the forecaster | Time (UTC) | Top 3 (discovery — named people, probability) | Max | Entropy (bits; uniform 4.91) | Preseen |",
          "|---|---|---|---|---:|---:|---|"]
    notes = {"v2_main3": "profile cards with the patents tied to the discovery as the main evidence, every card measure "
                         "important; Chemistry timing base rate; Medicine and Physics 2026 outcomes",
             "v2_demo": "the treatment's notes + the demographics of the 2000–2025 Chemistry laureates and the 2026 laureates, "
                        "with a demographic factor of 0.5–2 per option",
             "v2_control": "none"}
    for l, (_, name) in zip(PUBLISHED, cols):
        p, opts = R[l]["p"], R[l]["options"]
        top = sorted(range(30), key=lambda i: -p[i])[:3]
        md.append(f"| {'**' + name + '**' if l == 'v2_main3' else name} | {notes[l]} | "
                  f"{R[l]['started'][11:16]}–{R[l]['finished'][11:16]} | "
                  + "<br>".join(f"{short(disc(opts[i]))} — {people(opts[i])}, **{100 * p[i]:.1f}**" for i in top)
                  + f" | {100 * max(p):.1f} | {entropy(p):.2f} | [result]({links[l]}) |")
    md += ["", "## Agreement with the treatment", "",
           f"- control vs treatment: Spearman {spearman(ct, m3):.2f}, mean |difference| {100 * sum(abs(a - b) for a, b in zip(ct, m3)) / 30:.2f} points per option",
           f"- demographic vs treatment: Spearman {spearman(dm, m3):.2f}, mean |difference| {100 * sum(abs(a - b) for a, b in zip(dm, m3)) / 30:.2f} points per option",
           "", "## All 30 options", "", "Sorted by the treatment.", "",
           "| # | Discovery | Named people | Treatment | Demographic | Control |", "|---:|---|---|---:|---:|---:|"]
    for k, r in enumerate(rows, 1):
        md.append(f"| {k} | {r['discovery'].removeprefix('for ')} | {r['v2_people']} | **{100 * r['v2m3_p']:.1f}** | "
                  f"{100 * r['v2demo_p']:.1f} | {100 * r['v2ctl_p']:.1f} |")
    (OUT / "compare.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[9:15]))


if __name__ == "__main__":
    main()
