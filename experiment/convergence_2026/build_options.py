#!/usr/bin/env python3
"""build_options.py: 30 discovery + people options per field from the virtual committee and Data/convergence_2026.csv.

    $PY build_options.py [--fields physics chemistry] [--k 30] [--weight 1.0]

The committee part is unchanged from ../preseen/committee.py: nominations from committee/<field>/ballots.jsonl with the
hand corrections of committee/<field>/merges.yaml, joined into one option when they share a person, scored by Borda
points 5..1 per ballot with each model's points divided by its number of valid ballots. Nothing in ../preseen/ is
written; the committee's candidates.json, clusters.json and review.md stay as they are.

The convergence file adds voters. Each evidence family (clarivate_2026, kalshi, high_ppv_prize, milestone_passed,
swedish_proximity, symposium_dossier, web_2026, insider_x) is one approval vote for every person it names: 1 point,
except kalshi, which gives the person's market price divided by the highest price in the field. Only rows with
status "alive" are used. The approval points of a field are scaled so that their total equals --weight times the
committee's total points, and each person's points go to the option that holds the person:

- a person the committee named joins that option (same first initial + surname, middle initials kept apart as in
  committee.py); a person in two options splits the points by their committee weight in each;
- a person the committee did not name joins an option through decisions.yaml (attach), joins the other people of a
  shared milestone, or forms a new option with the people listed with it in decisions.yaml (groups), else alone.

An option's score = committee points + the convergence points of the people shown (at most three living people,
ranked by committee weight + convergence points). The committee's top 12 options are kept even if they would fall
below rank K (none does with the default settings; a flag says so if it happens). Writes results/options_<field>.json,
results/options_<field>.csv and results/review_<field>.md.
"""
import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "preseen"))
import committee as cm  # noqa: E402  (ballots, clusters, Borda score, names, laureate table)

CONVERGENCE = REPO / "Data" / "convergence_2026.csv"
DECISIONS = HERE / "decisions.yaml"
OUT = HERE / "results"
FAMILIES = ["clarivate_2026", "kalshi", "high_ppv_prize", "milestone_passed", "swedish_proximity",
            "symposium_dossier", "web_2026", "insider_x"]
KEEP_TOP = 12                                   # the committee's question options are always kept
MIN_FAMILIES_NEW = 2                            # an option the committee did not name needs two evidence families
MAX_PEOPLE = cm.CFG["committee"]["max_people"]


def details(text):
    out = {}
    for part in str(text).split(" | "):
        k, _, v = part.partition(": ")
        if k.strip():
            out[k.strip()] = v.strip()
    return out


def committee_options(field):
    """The committee's options with their Borda score and people (committee weights), as committee.py builds them."""
    manual = cm.load_manual(field)
    ballots, noms = cm.load_ballots(field, manual["aliases"])
    clusters = cm.make_clusters(noms, manual)
    everything = lambda x: True
    nv = cm.n_valid(ballots, everything)
    order = cm.top_k(clusters, ballots, everything, k=len(clusters))
    dead = list(manual["deceased"])
    opts = []
    for rank, i in enumerate(order, 1):
        c = clusters[i]
        total, _ = cm.score(c, nv, everything)
        discovery, people = cm.describe(c, nv, {w["id"] for w in manual["wording_from"]})
        chosen = next((w for w in manual["people"] if w["id"] in {n["id"] for n in c}), None)
        people = [dict(p, committee=p["weight"], convergence=0.0, families={},
                       deceased=any(cm.same_person(d, p["name"]) for d in dead)) for p in people]
        opts.append({"id": f"committee-{rank}", "committee_rank": rank, "discovery": discovery,
                     "discovery_source": "committee (LLM ballots)", "committee": total,
                     "n_models": len({n["provider"] for n in c}), "people": people,
                     "chosen": chosen["names"] if chosen else None})
    return opts, manual


def match_keys(name, manual, opts):
    """Committee option indices and person keys that hold this convergence name."""
    name = manual["aliases"].get(name, name)
    key, mid = cm.person_key(name), "".join(cm.middles(name))
    hits = []
    for i, o in enumerate(opts):
        for p in o["people"]:
            if p["key"] == key or (mid and p["key"] == f"{key} {mid}"):
                hits.append((i, p["key"]))
    return hits


def build(field, k, weight, decisions, log):
    opts, manual = committee_options(field)
    total_committee = sum(o["committee"] for o in opts)
    dec = decisions.get(field) or {}
    for o in opts:                                # decisions.yaml deceased: people the committee's living check missed
        for p in o["people"]:
            for name, note in (dec.get("deceased") or {}).items():
                if cm.same_person(name, p["name"]):
                    p["deceased"], p["deceased_note"] = True, note
    conv = pd.read_csv(CONVERGENCE)
    conv = conv[(conv.primary_field == field)]
    dropped = conv[conv.status != "alive"]
    conv = conv[conv.status == "alive"]

    # approval points per person and family
    kalshi = {r.name: float(details(r.details)["kalshi"].split()[-1]) for r in conv.itertuples() if "kalshi" in r.families}
    top_price = max(kalshi.values()) if kalshi else 1.0
    approvals = {}
    for r in conv.itertuples():
        fams = {}
        for f in r.families.split(";"):
            fams[f] = kalshi[r.name] / top_price if f == "kalshi" else 1.0
        approvals[r.name] = fams
    unit = weight * total_committee / sum(sum(f.values()) for f in approvals.values())
    info = {r.name: details(r.details) for r in conv.itertuples()}
    items = {n: sum(len([x for x in v.split(",") if x.strip()]) for v in d.values()) for n, d in info.items()}

    # place every person: committee option, attach, milestone partner, group, or alone
    attach = dec.get("attach") or {}
    groups = dec.get("groups") or []
    in_group = {n: g for g in groups for n in g["people"]}
    unknown = [n for n in list(attach) + list(in_group) if n not in approvals]
    if unknown:
        sys.exit(f"decisions.yaml ({field}): not an alive {field} person in the convergence file: {unknown}")
    placed = {}                                   # name -> [(option index, person dict, share)]

    def newcomer(name, why=None):
        return {"name": name, "key": cm.person_key(name), "committee": 0.0, "convergence": 0.0, "families": {},
                "deceased": False, "attached": why}

    for name in approvals:
        hits = match_keys(name, manual, opts)
        if hits:
            people = [next(p for p in opts[i]["people"] if p["key"] == key) for i, key in hits]
            w = [max(p["committee"], 1e-9) for p in people]
            placed[name] = [(i, p, x / sum(w)) for (i, _), p, x in zip(hits, people, w)]
    for name, target in attach.items():
        i = next((j for j, o in enumerate(opts) if any(cm.same_person(target["with"], p["name"]) for p in o["people"])
                  and (not target.get("discovery_has") or target["discovery_has"].lower() in o["discovery"].lower())), None)
        if i is None:
            sys.exit(f"decisions.yaml attach: no option holds {target['with']!r} for {name}")
        opts[i]["people"].append(newcomer(name, target["reason"]))
        placed[name] = [(i, opts[i]["people"][-1], 1.0)]
    # milestone partners of unplaced people
    by_milestone = defaultdict(list)
    for name, d in info.items():
        if "milestone_passed" in d:
            by_milestone[d["milestone_passed"]].append(name)
    for name in approvals:
        if name in placed or name in in_group:
            continue
        m = info[name].get("milestone_passed")
        homes = {i for other in by_milestone.get(m, []) if other in placed for i, _, _ in placed[other]}
        if len(homes) == 1:
            i = homes.pop()
            opts[i]["people"].append(newcomer(name, f"shares the milestone '{m}'"))
            placed[name] = [(i, opts[i]["people"][-1], 1.0)]
        elif len(homes) > 1:
            log.append(f"{name}: milestone '{m}' is shared with people of {len(homes)} options; left alone "
                       "(decide in decisions.yaml)")
    for g in groups:
        opts.append({"id": f"new-{g['people'][0]}", "committee_rank": None, "discovery": g["discovery"],
                     "discovery_source": "decisions.yaml (Claude)", "committee": 0.0, "n_models": 0,
                     "people": [newcomer(n) for n in g["people"]], "group_reason": g["reason"], "chosen": None})
        for p in opts[-1]["people"]:
            placed[p["name"]] = [(len(opts) - 1, p, 1.0)]
    alone_text = dec.get("discovery") or {}
    for name in approvals:
        if name not in placed:
            opts.append({"id": f"new-{name}", "committee_rank": None,
                         "discovery": alone_text.get(name, {}).get("discovery"),
                         "discovery_source": "decisions.yaml (Claude)" if name in alone_text else None,
                         "group_reason": alone_text.get(name, {}).get("reason"),
                         "committee": 0.0, "n_models": 0, "chosen": None, "people": [newcomer(name)]})
            placed[name] = [(len(opts) - 1, opts[-1]["people"][0], 1.0)]

    # convergence points onto people
    for name, homes in placed.items():
        for i, p, share in homes:
            p["convergence"] += unit * sum(approvals[name].values()) * share
            for f, a in approvals[name].items():
                p["families"][f] = round(p["families"].get(f, 0) + unit * a * share, 4)

    for rank, r in (dec.get("rename") or {}).items():
        o = next(o for o in opts if o["committee_rank"] == int(rank))
        o["renamed"] = f"committee wording \"{o['discovery']}\" replaced: {r['reason']}"
        o["discovery"], o["discovery_source"] = r["discovery"], "committee, wording edited in decisions.yaml (Claude)"

    # shown people, option score, flags
    notes = dec.get("notes") or {}
    laureates = cm.laureate_table()
    motivations = cm.field_motivations(field)
    for o in opts:
        living = [p for p in o["people"] if not p["deceased"]]
        living.sort(key=lambda p: (-(p["committee"] + p["convergence"]), p["name"]))
        if o["chosen"]:                           # merges.yaml people: the committee's hand choice of the shown people
            picked = [next(p for p in living if cm.same_person(n, p["name"])) for n in o["chosen"]]
            living = picked + [p for p in living if p not in picked]
        o["shown"] = living[:MAX_PEOPLE]
        o["convergence"] = sum(p["convergence"] for p in o["shown"])
        o["score"] = o["committee"] + o["convergence"]
        o["families"] = sorted({f for p in o["people"] for f in p["families"]})
        o["items"] = sum(items.get(p.get("name"), 0) for p in o["shown"])
        o["eligible"] = o["committee_rank"] is not None or len(o["families"]) >= MIN_FAMILIES_NEW
        flags = [o["renamed"]] if o.get("renamed") else []
        flags += [f"{n}: {t}" for n, t in notes.items() if any(p["name"] == n for p in o["people"])]
        for p in o["people"]:
            if p["deceased"]:
                flags.append(f"{p['name']}: deceased ({p.get('deceased_note') or 'merges.yaml'}); not shown")
        for p in o["shown"]:
            for nm, year, cat, death in laureates:
                if cm.same_person(p["name"], nm):
                    flags.append(f"{p['name']}: Nobel laureate ({cat} {year})" + (f", died {death}" if death else ""))
        if o["discovery"]:
            for year, mot in motivations:
                if cm.jaccard(cm.content_words(o["discovery"]), cm.content_words(mot)) >= 0.35:
                    flags.append(f"possibly already awarded: resembles {year} \"{mot}\"")
        else:
            flags.append("no discovery text yet (add it to decisions.yaml)")
        if o["chosen"]:
            flags.append("shown people chosen by hand in the committee's merges.yaml")
        o["flags"] = flags

    log.append(f"{sum(not o['eligible'] for o in opts)} options of people the committee did not name are left out: "
               f"fewer than {MIN_FAMILIES_NEW} evidence families")
    order = sorted((i for i, o in enumerate(opts) if o["eligible"]),
                   key=lambda i: (-opts[i]["score"], -opts[i]["committee"], -opts[i]["items"],
                                  opts[i]["committee_rank"] or 999, opts[i]["id"]))
    top = order[:k]
    if len(order) > k and abs(opts[order[k - 1]]["score"] - opts[order[k]]["score"]) < 1e-9:
        log.append(f"rank {k} and {k + 1} have the same score ({opts[order[k]]['score']:.3f}); the tie is broken by "
                   "committee points, the number of evidence items, then the committee's own rank")
    for i in order[k:]:
        if (opts[i]["committee_rank"] or 99) <= KEEP_TOP:
            top.append(i)
            opts[i]["flags"].append(f"kept although ranked below {k}: a committee top-{KEEP_TOP} option")
    return [opts[i] for i in top], opts, order, unit, total_committee, dropped, approvals


def person_out(p):
    return {"name": p["name"], "committee_weight": round(p["committee"], 4), "convergence_points": round(p["convergence"], 4),
            "convergence_families": p["families"], "attached": p.get("attached")}


def write(field, top, opts, order, unit, total_committee, dropped, approvals, k, weight, log, alt):
    OUT.mkdir(exist_ok=True)
    rows = []
    for r, o in enumerate(top, 1):
        rows.append({"rank": r, "option": f"{o['discovery']} — {', '.join(p['name'] for p in o['shown'])}",
                     "discovery": o["discovery"], "discovery_source": o["discovery_source"],
                     "score": round(o["score"], 4), "committee_points": round(o["committee"], 4),
                     "convergence_points": round(o["convergence"], 4), "committee_rank": o["committee_rank"],
                     "n_models": o["n_models"], "people": [person_out(p) for p in o["shown"]],
                     "not_shown": [person_out(p) for p in o["people"] if p not in o["shown"]],
                     "group_reason": o.get("group_reason"), "flags": o["flags"]})
    meta = {"field": field, "k": k, "convergence_weight": weight, "committee_total_points": round(total_committee, 4),
            "convergence_point_per_approval": round(unit, 6), "people_used": len(approvals),
            "rows_left_out_not_alive": dropped.name.tolist(),
            "method": __doc__.split("\n\n", 2)[2].strip()}
    (OUT / f"options_{field}.json").write_text(json.dumps({**meta, "options": rows}, indent=1, ensure_ascii=False) + "\n",
                                               encoding="utf-8")
    with open(OUT / f"options_{field}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rank", "discovery", "people", "score", "committee_points", "convergence_points", "committee_rank",
                    "discovery_source", "flags"])
        for x in rows:
            w.writerow([x["rank"], x["discovery"], "; ".join(p["name"] for p in x["people"]), x["score"],
                        x["committee_points"], x["convergence_points"], x["committee_rank"] or "",
                        x["discovery_source"], " | ".join(x["flags"])])
    lines = [f"# {field.capitalize()}: {len(rows)} options", "",
             f"Committee total {total_committee:.2f} points; convergence weight {weight} (one approval = {unit:.4f} "
             f"points); {len(approvals)} alive people from the convergence file; left out (status not alive): "
             f"{', '.join(dropped.name) or 'none'}.", "",
             "| # | Discovery | People | Score | Committee | Convergence | Committee rank |", "|---:|---|---|---:|---:|---:|---:|"]
    for x in rows:
        lines.append(f"| {x['rank']} | {x['discovery']} | {', '.join(p['name'] for p in x['people'])} | {x['score']:.2f} | "
                     f"{x['committee_points']:.2f} | {x['convergence_points']:.2f} | {x['committee_rank'] or 'new'} |")
    lines += ["", "## Per option", ""]
    for x in rows:
        lines.append(f"**{x['rank']}. {x['discovery']}** ({x['discovery_source']})")
        for p in x["people"]:
            fam = ", ".join(f"{f} {v:.2f}" for f, v in p["convergence_families"].items())
            lines.append(f"- {p['name']}: committee {p['committee_weight']:.2f}, convergence {p['convergence_points']:.2f}"
                         + (f" ({fam})" if fam else "") + (f"; joined: {p['attached']}" if p["attached"] else ""))
        if x["not_shown"]:
            lines.append("- not shown: " + ", ".join(f"{p['name']} ({p['committee_weight'] + p['convergence_points']:.2f})"
                                                    for p in x["not_shown"]))
        if x["group_reason"]:
            lines.append(f"- grouped by hand: {x['group_reason']}")
        for fl in x["flags"]:
            lines.append(f"- flag: {fl}")
        lines.append("")
    lines += ["## Sensitivity to the convergence weight", ""]
    base = {x["discovery"] for x in rows}
    for wt, names in alt.items():
        lines.append(f"- weight {wt}: {len(base & names)} of {len(rows)} options the same; "
                     f"in: {sorted(names - base) or 'none'}; out: {sorted(base - names) or 'none'}")
    matched = sorted((p["name"], o["committee_rank"]) for o in opts if o["committee_rank"] for p in o["people"]
                     if p["families"] and not p.get("attached"))
    lines += ["", "## Convergence people matched to committee options by name", "",
              ", ".join(f"{n} (committee option {r})" for n, r in matched) or "none"]
    lines += ["", "## Notes", ""] + [f"- {x}" for x in log] + ["",
              "Next below the cut: " + "; ".join(f"{opts[i]['discovery'] or opts[i]['people'][0]['name']} "
                                                 f"({opts[i]['score']:.2f})" for i in order[len(rows):len(rows) + 8])]
    (OUT / f"review_{field}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="30 discovery + people options per field (committee + convergence).")
    ap.add_argument("--fields", nargs="+", default=["physics", "chemistry"])
    ap.add_argument("--k", type=int, default=30)
    ap.add_argument("--weight", type=float, default=1.0, help="convergence points as a multiple of the committee's")
    a = ap.parse_args()
    decisions = yaml.safe_load(DECISIONS.read_text(encoding="utf-8")) if DECISIONS.exists() else {}
    for field in a.fields:
        log = []
        res = build(field, a.k, a.weight, decisions, log)
        alt = {}
        for wt in (a.weight / 2, a.weight * 2):
            t = build(field, a.k, wt, decisions, [])[0]
            alt[wt] = {o["discovery"] for o in t}
        write(field, *res, a.k, a.weight, log, alt)
        top = res[0]
        print(f"{field}: {len(top)} options -> results/options_{field}.json, .csv, review_{field}.md")
        for r, o in enumerate(top, 1):
            print(f"  {r:>2}. {o['score']:5.2f} (c {o['committee']:.2f} + v {o['convergence']:.2f}) "
                  f"{'new' if o['committee_rank'] is None else 'c' + str(o['committee_rank']):>4} "
                  f"{(o['discovery'] or '??')[:60]} | {', '.join(p['name'] for p in o['shown'])}")
        for x in log:
            print("  note:", x)


if __name__ == "__main__":
    main()
