#!/usr/bin/env python3
"""patent_section.py: a "Patents tied to the discovery" section on the cards of one field (chemistry).

    $PY patent_section.py pools --field chemistry   # each person's US utility patents (granted up to 2021) with titles,
                                                    #   years, assignee and later-patent citations
                                                    #   -> cards_age25/_work/patent_pools/<slug>.json
    $PY patent_section.py merge --field chemistry   # _work/patent_picks/batch_*.yaml (LLM agents) ->
                                                    #   cards_age25/patents_tied_<field>.yaml, checked against the pools
    $PY patent_section.py apply --field chemistry   # insert the section into cards/<list>/<field>/*.md and
                                                    #   cards_age25/<list>/<field>/*.md (idempotent; run after the
                                                    #   card builders, which rewrite the cards without it) and add its
                                                    #   definition to every 00_definitions.md of the field

Why: an invention disclosed mainly in patents (sequencing-by-synthesis: reversible-terminator nucleotides, cluster
amplification) had no discovery evidence on the cards, which list papers only and give patents as a count. The picks are
up to three of the person's patents most tied to the discovery of the person's option(s), chosen like the defining works
(LLM review of the titles); the section also says how many of the person's patents relate to the discovery. On the
age-25 cards only patents filed from age 25 on are shown.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cards_age25_v2 as c25  # noqa: E402  (lists, identities, births; puts ../preseen and ../convergence_2026 on the path)
import build_cards as bc  # noqa: E402

YEAR_MAX = bc.YEAR_MAX
WORK = c25.OUT / "_work"
HEAD = "## Patents tied to the discovery"
DEFINITION = (
    "- **Patents tied to the discovery**: up to three of the person's US utility patents (granted up to {year_max}) most "
    "tied to the discovery of the option the person is listed under, chosen by a language-model review of the titles of "
    "all the person's patents (inventions disclosed mainly in patents have little other discovery evidence on a card); "
    "each with its filing and grant year, first assignee and the number of later US patents citing it. The line above "
    "them says how many of the person's patents relate to the discovery. On the age-25 cards only patents filed from "
    "age 25 on are shown.")


def patents(name, field):
    ids = c25.cp2.identity_of(name, field=field)[0]
    pt = bc.read(bc.find_profile(ids), "patents_metrics.parquet",
                 columns=["patent_id", "patent_type", "patent_title", "filing_year", "grant_year", "assignee_list", "C_all"])
    if pt is None or pt.empty:
        return []
    pt = pt[(pt.patent_type == "utility") & (pd.to_numeric(pt.grant_year, errors="coerce") <= YEAR_MAX)]
    pt = pt.drop_duplicates("patent_id")
    nodes = bc.read(bc.find_profile(ids), "patents_assignee_nodes.csv")       # PatentsView assignee id -> organization
    org = dict(zip(nodes.id.astype(str), nodes.name.astype(str))) if nodes is not None and len(nodes) else {}
    out = []
    for r in pt.itertuples():
        fy = pd.to_numeric(r.filing_year, errors="coerce")
        a = [x for x in re.split(r"[;|]", str(r.assignee_list or "")) if x and x != "None"]
        names = [org.get(x, "") for x in a]
        out.append({"patent_id": str(r.patent_id), "title": (r.patent_title or "").strip(),
                    "filing_year": None if pd.isna(fy) else int(fy), "grant_year": int(r.grant_year),
                    "assignee": next((n for n in names if n and n != "nan"), ""),
                    "cited_by_patents": int(r.C_all) if pd.notna(r.C_all) else 0})
    return sorted(out, key=lambda p: (-p["cited_by_patents"], p["patent_id"]))


def cmd_pools(a):
    d = WORK / "patent_pools"
    d.mkdir(parents=True, exist_ok=True)
    b = c25.ca.births(a.field)
    n, sizes = 0, []
    for name, opts in c25._Lists.shown(a.field):
        ps = patents(name, a.field)
        (d / f"{bc.person_slug(name)}.json").write_text(json.dumps(
            {"person": name, "options": opts, "birth_year": int(b[name]["birth_year"]), "patents": ps},
            indent=1, ensure_ascii=False), encoding="utf-8")
        n += 1
        sizes.append((len(ps), name))
    print(f"_work/patent_pools/: {n} people; with patents: {sum(1 for s, _ in sizes if s)}; largest: "
          f"{sorted(sizes, reverse=True)[:6]}")


def cmd_merge(a):
    pools = {json.loads(f.read_text())["person"]: json.loads(f.read_text())
             for f in (WORK / "patent_pools").glob("*.json")}
    merged, problems = {}, []
    for f in sorted((WORK / "patent_picks").glob("batch_*.yaml")):
        for name, v in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).items():
            if name in merged:
                problems.append(f"{name}: in two batches")
            merged[name] = v
    for name, p in pools.items():
        if not p["patents"]:
            merged[name] = {"picks": [], "n_related": 0, "note": "no US utility patents in the record"}
            continue
        d = merged.get(name)
        if d is None:
            problems.append(f"{name}: missing")
            continue
        by_id = {x["patent_id"]: x for x in p["patents"]}
        picks = d.get("picks") or []
        if len(picks) > 3:
            problems.append(f"{name}: {len(picks)} picks")
        for k in picks:
            x = by_id.get(str(k.get("patent_id")))
            if x is None:
                problems.append(f"{name}: pick {k.get('patent_id')} not in the pool")
            else:
                k.update({"patent_id": x["patent_id"], **{f: x[f] for f in ("title", "filing_year", "grant_year",
                                                                               "assignee", "cited_by_patents")}})
        if d.get("n_related") is None or int(d["n_related"]) < len(picks):
            problems.append(f"{name}: n_related {d.get('n_related')} < {len(picks)} picks")
    problems += [f"{n}: not in the pools" for n in merged if n not in pools]
    head = (f"# Patents tied to the discovery per {a.field} person (patent_section.py apply reads this). Chosen 2026-10-06 by\n"
            "# LLM agents from all the person's US utility patents granted up to 2021 (cards_age25/_work/patent_pools/):\n"
            "# up to three patents most tied to the discovery of the person's option(s); n_related = how many relate.\n")
    (c25.OUT / f"patents_tied_{a.field}.yaml").write_text(
        head + yaml.safe_dump({n: merged[n] for n in sorted(merged) if n in pools}, allow_unicode=True, sort_keys=False,
                              width=120), encoding="utf-8")
    k = [len((merged.get(n) or {}).get("picks") or []) for n in pools]
    print(f"patents_tied_{a.field}.yaml: {len(pools)} people; picks per person {({i: k.count(i) for i in range(4)})}; "
          f"problems: {len(problems)}")
    for x in problems:
        print("  ", x)
    return 1 if problems else 0


def section(name, d, pool, lo=None):
    """The card lines; lo = first filing year shown (age-25 cards)."""
    pats = pool["patents"]
    if lo is not None:
        pats = [p for p in pats if p["filing_year"] is None or p["filing_year"] >= lo]
    picks = [p for p in (d or {}).get("picks") or [] if lo is None or p["filing_year"] is None or p["filing_year"] >= lo]
    win = f"granted up to {YEAR_MAX}" + (f", filed from age 25 on" if lo is not None else "")
    if not pats:
        return [HEAD, f"- No US utility patents in the record ({win})."]
    rel = min(int((d or {}).get("n_related") or 0), len(pats))
    if not picks:
        return [HEAD, f"- None of the person's {len(pats)} US utility patents ({win}) is tied to the listed discovery."]
    lines = [HEAD, f"- About {rel} of the person's {len(pats)} US utility patents ({win}) relate to the listed discovery; "
                   f"the {'one' if len(picks) == 1 else len(picks)} most tied to it:"]
    for k, p in enumerate(picks, 1):
        num = f"US {int(p['patent_id']):,}" if p["patent_id"].isdigit() else f"US {p['patent_id']}"
        yrs = (f"filed {p['filing_year']}, granted {p['grant_year']}" if p["filing_year"] else f"granted {p['grant_year']}")
        asg = f"; assignee {p['assignee']}" if p["assignee"] else ""
        lines.append(f"{k}. {num} \"{p['title']}\" ({yrs}{asg}): cited by {p['cited_by_patents']:,} later US "
                     f"patent{'s' if p['cited_by_patents'] != 1 else ''}.")
    return lines


def insert(text, lines):
    """Replace an existing section, else put it after the defining-works section (before Technological translation)."""
    text = re.sub(r"\n## Patents tied to the discovery\n(?:(?!\n## ).)*", "", text, flags=re.S)
    m = re.search(r"\n## Technological translation", text)
    block = "\n" + "\n".join(lines) + "\n"
    return text[:m.start()] + block + text[m.start():] if m else text.rstrip("\n") + "\n" + block


def cmd_apply(a):
    tied = yaml.safe_load((c25.OUT / f"patents_tied_{a.field}.yaml").read_text(encoding="utf-8")) or {}
    pools = {json.loads(f.read_text())["person"]: json.loads(f.read_text())
             for f in (WORK / "patent_pools").glob("*.json")}
    b = c25.ca.births(a.field)
    n, miss = 0, []
    for (v, f) in c25.cp2.LISTS:
        if f != a.field:
            continue
        for base, age in ((HERE / "cards" / v / f, False), (c25.OUT / v / f, True)):
            if not base.exists():
                continue
            for name, _ in c25.cp2.shown(v, f):
                card = base / f"{bc.person_slug(name)}.md"
                if not card.exists() or name not in pools:
                    miss.append(f"{v} {name} ({'age-25' if age else 'standard'})")
                    continue
                lo = int(b[name]["birth_year"]) + 25 if age else None
                card.write_text(insert(card.read_text(encoding="utf-8"), section(name, tied.get(name), pools[name], lo)),
                                encoding="utf-8")
                n += 1
            dfile = base / "00_definitions.md"
            if dfile.exists():
                t = dfile.read_text(encoding="utf-8")
                t = re.sub(r"\n- \*\*Patents tied to the discovery\*\*:[^\n]*", "", t)
                t = t.replace("\n- **Textbook reach**", "\n" + DEFINITION.format(year_max=YEAR_MAX) + "\n- **Textbook reach**", 1)
                dfile.write_text(t, encoding="utf-8")
    print(f"section written on {n} cards; missing: {miss}")
    return 1 if miss else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["pools", "merge", "apply"])
    ap.add_argument("--field", default="chemistry")
    a = ap.parse_args()
    sys.exit({"pools": cmd_pools, "merge": cmd_merge, "apply": cmd_apply}[a.cmd](a))


if __name__ == "__main__":
    main()
