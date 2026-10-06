#!/usr/bin/env python3
"""cards_age25_v2.py: age-25 profile cards (works and patents from age 25 on, defining works tied to the discovery) for
every person of the lists of cards_pipeline_v2.py, one field at a time (chemistry: v1, v2 and the Preseen list).

    $PY cards_age25_v2.py births --field chemistry     # people/living_check.csv + people/births_overrides.yaml
                                                       #   -> cards_age25/births_<field>.csv (+ laureate births, PrizeAtlas)
    $PY cards_age25_v2.py pools --field chemistry      # 80 most-cited research works from age 25 on per person
                                                       #   -> cards_age25/_work/pools_<field>.json, pool_files/<slug>.json
    $PY cards_age25_v2.py reference --field chemistry  # age-25-filtered laureate reference
    $PY cards_age25_v2.py merge-picks --field chemistry  # _work/picks/batch_*.yaml (LLM agents) -> defining_works_<field>.yaml
    $PY cards_age25_v2.py cards --field chemistry      # cards_age25/<list>/<field>/ (00_definitions.md + one card per person)
    $PY cards_age25_v2.py check --field chemistry      # births, picks inside the pools, no pre-age-25 defining work

The card text, the age filter, the reference rebuild and the pool rule are those of ../convergence_2026/cards_age25.py
(imported; only its folders, list and identity functions are pointed at this folder). The defining works are chosen
outside this script (an LLM review of each pool against the person's options, cards_age25/defining_works_<field>.yaml).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "convergence_2026"
sys.path.insert(0, str(HERE))
import cards_pipeline_v2 as cp2  # noqa: E402  (lists, identities; also puts ../preseen on the path)
sys.path.insert(0, str(V1))
import cards_age25 as ca  # noqa: E402
import build_cards as bc  # noqa: E402

OUT = HERE / "cards_age25"
ca.OUT, ca.WORK = OUT, OUT / "_work"


class _Lists:
    """cards_pipeline.py's shown() / identity_of() interface over the v2 lists: a person's options are the union over
    the lists of the field (in list order), so one pool and one defining-works choice serve every list."""

    @staticmethod
    def shown(field):
        out = {}
        for (v, f) in cp2.LISTS:
            if f == field:
                for name, opts in cp2.shown(v, f):
                    out.setdefault(name, [])
                    out[name] += [o for o in opts if o not in out[name]]
        return list(out.items())

    @staticmethod
    def identity_of(field, name):
        return cp2.identity_of(name, field=field)

    @staticmethod
    def overrides():
        return cp2.overrides()


ca.cp = _Lists
ca.DEFINITIONS = ca.DEFINITIONS.replace("defining_works_physics.yaml", "defining_works_{field_slug}.yaml")


def cmd_births(a):
    """ca.cmd_births with this folder's living check and overrides."""
    OUT.mkdir(exist_ok=True)
    ovp = HERE / "people" / "births_overrides.yaml"
    ov = (yaml.safe_load(ovp.read_text(encoding="utf-8")) or {}) if ovp.exists() else {}
    ov = (ov.get(a.field) or {}) if any(k in ov for k in ("medicine", "physics", "chemistry")) else ov
    lv = {r["person"]: r for r in csv.DictReader(open(HERE / "people" / "living_check.csv", encoding="utf-8"))
          if r["field"] == a.field}
    rows, missing = [], []
    for name, _ in _Lists.shown(a.field):
        o, r = ov.get(name), lv.get(name, {})
        ambiguous = "candidates" in r.get("status", "")
        if o:
            rows.append({"person": name, "birth_year": int(o["birth_year"]), "birth_date": o.get("birth_date", ""),
                         "source": o.get("source", "overrides"), "source_detail": o.get("source_detail", ""),
                         "confidence": o.get("confidence", "")})
        elif r.get("born", "").strip() and not ambiguous:
            rows.append({"person": name, "birth_year": int(r["born"][:4]), "birth_date": r["born"],
                         "source": "wikidata", "source_detail": r.get("qid", ""), "confidence": "high"})
        else:
            missing.append((name, r.get("status", "")[:70], r.get("label", ""), r.get("description", "")[:60], r.get("born", "")))
    with open(OUT / f"births_{a.field}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["person", "birth_year", "birth_date", "source", "source_detail", "confidence"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda x: x["person"]))
    print(f"cards_age25/births_{a.field}.csv: {len(rows)} people; missing (need people/births_overrides.yaml): {len(missing)}")
    for m in missing:
        print("  ", " | ".join(str(x) for x in m))
    # laureate births (PrizeAtlas), exactly as ca.cmd_births
    ref = pd.read_csv(ca.PRESEEN / "cards" / "laureate_reference.csv")
    ref = ref[ref.field == a.field]
    pa = pd.read_csv(ca.REPO / "Data/prizeatlas/prizeatlas_nobel_laureates.csv",
                     usecols=["category_en", "year", "name", "openalex_author_id", "birth_year", "birth_date"])
    pa = pa[(pa.category_en == bc.CFG["fields"][a.field]["prizeatlas_category"]) & pa.birth_year.notna()]
    by_id = pa.dropna(subset=["openalex_author_id"]).set_index("openalex_author_id").birth_year.to_dict()
    by_name = pa.set_index(["name", "year"]).birth_year.to_dict()
    date_by_name = pa.set_index(["name", "year"]).birth_date.to_dict()
    out, miss = [], []
    for r in ref.itertuples():
        y = by_id.get(r.author_id) or by_name.get((r.name, r.prize_year))
        if y is None or pd.isna(y):
            miss.append(r.name)
            continue
        out.append({"name": r.name, "prize_year": r.prize_year, "author_id": r.author_id, "birth_year": int(y),
                    "birth_date": date_by_name.get((r.name, r.prize_year), "")})
    pd.DataFrame(out).to_csv(OUT / f"births_laureates_{a.field}.csv", index=False)
    print(f"cards_age25/births_laureates_{a.field}.csv: {len(out)} laureates; without birth year: {miss}")
    return 1 if (missing or miss) else 0


def cmd_merge_picks(a):
    """_work/picks/batch_*.yaml (one LLM agent per batch of pool files) -> defining_works_<field>.yaml, checked against the
    pools: every person present, at most three picks, each pick in the person's pool and from age 25 on."""
    pools = json.loads((ca.WORK / f"pools_{a.field}.json").read_text(encoding="utf-8"))
    merged, problems = {}, []
    for f in sorted((ca.WORK / "picks").glob("batch_*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for name, v in d.items():
            if name in merged:
                problems.append(f"{name}: in two batches")
            merged[name] = v
    for name, p in pools.items():
        d = merged.get(name)
        if d is None:
            problems.append(f"{name}: missing")
            continue
        works = {w["paper_id"]: w for w in p["works"]}
        picks = d.get("picks") or []
        if len(picks) > 3:
            problems.append(f"{name}: {len(picks)} picks")
        for k in picks:
            w = works.get(k.get("paper_id"))
            if w is None:
                problems.append(f"{name}: pick {k.get('paper_id')} not in the pool")
            elif int(k.get("year") or 0) != w["year"] or w["year"] < p["cutoff_year"]:
                problems.append(f"{name}: pick {k['paper_id']} year {k.get('year')} vs pool {w['year']} (cutoff {p['cutoff_year']})")
            else:                                  # copy the pool's fields, so a typo in a title cannot reach a card
                k.update({x: w[x] for x in ("year", "title", "metrics", "in_profile")})
    extra = [n for n in merged if n not in pools]
    problems += [f"{n}: not in the pools" for n in extra]
    head = (f"# Defining works per {a.field} person (cards_age25_v2.py cards reads this). Chosen 2026-10-06 by LLM agents\n"
            "# (one per batch of _work/pool_files/<slug>.json) from the 80 most-cited research works from age 25 on, live\n"
            "# OpenAlex included: up to three works most tied to the discovery of the person's option(s), landmark originals\n"
            "# first; the card fills missing slots with the most-cited remaining works. 'note' = the agent's concerns.\n")
    (OUT / f"defining_works_{a.field}.yaml").write_text(
        head + yaml.safe_dump({n: merged[n] for n in sorted(merged) if n in pools}, allow_unicode=True, sort_keys=False,
                              width=120), encoding="utf-8")
    n_picks = [len((merged.get(n) or {}).get("picks") or []) for n in pools]
    print(f"defining_works_{a.field}.yaml: {sum(1 for n in pools if n in merged)}/{len(pools)} people; picks per person: "
          f"{ {k: n_picks.count(k) for k in range(4)} }; problems: {len(problems)}")
    for x in problems:
        print("  ", x)
    return 1 if problems else 0


def cmd_cards(a):
    bc.TITLE_CACHE = OUT / "_titles_cache.json"
    ref = pd.read_csv(OUT / f"laureate_reference_age25_{a.field}.csv")
    b = ca.births(a.field)
    dp = OUT / f"defining_works_{a.field}.yaml"
    defining = (yaml.safe_load(dp.read_text(encoding="utf-8")) or {}) if dp.exists() else {}
    pools = json.loads((ca.WORK / f"pools_{a.field}.json").read_text(encoding="utf-8"))
    y0, y1 = bc.CFG["profiles"]["laureate_reference_years"]
    index = []
    for (v, f) in cp2.LISTS:
        if f != a.field:
            continue
        outdir = OUT / v / f
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "00_definitions.md").write_text(ca.DEFINITIONS.format(
            year_max=ca.YEAR_MAX, field_name=bc.CFG["fields"][f]["prize"], y0=y0, y1=y1, age=ca.AGE_MIN, field_slug=f))
        for name, opts in cp2.shown(v, f):
            ids, aff, prior, src = cp2.identity_of(name, field=f)
            if name not in b:
                index.append({"version": v, "field": f, "person": name, "card": "", "profile": "NO BIRTH YEAR", "flags": ""})
                continue
            text, folder, flags = ca.card_age25(f, name, ids, opts, aff, prior, ref, b[name], defining.get(name),
                                                pools.get(name, {}))
            path = outdir / f"{bc.person_slug(name)}.md"
            path.write_text(text, encoding="utf-8")
            index.append({"version": v, "field": f, "person": name, "card": f"{v}/{f}/{path.name}",
                          "profile": folder.name if folder else "NO PROFILE", "flags": "; ".join(flags)})
        rows = [r for r in index if r["version"] == v]
        print(f"{v} {f}: {len(rows)} cards in cards_age25/{v}/{f}/; flagged: "
              f"{[(r['person'], r['flags']) for r in rows if r['flags'] or r['profile'] in ('NO PROFILE', 'NO BIRTH YEAR')]}")
    with open(OUT / f"index_{a.field}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["version", "field", "person", "card", "profile", "flags"])
        w.writeheader()
        w.writerows(index)


def cmd_check(a):
    b = ca.births(a.field)
    defining = yaml.safe_load((OUT / f"defining_works_{a.field}.yaml").read_text(encoding="utf-8")) or {}
    pools = json.loads((ca.WORK / f"pools_{a.field}.json").read_text(encoding="utf-8"))
    problems, n = [], 0
    for (v, f) in cp2.LISTS:
        if f != a.field:
            continue
        for name, opts in cp2.shown(v, f):
            n += 1
            if name not in b:
                problems.append((v, name, "no birth year"))
                continue
            born = int(b[name]["birth_year"])
            card = OUT / v / f / f"{bc.person_slug(name)}.md"
            if not card.exists():
                problems.append((v, name, "no card"))
                continue
            text = card.read_text(encoding="utf-8")
            if "## Impact" not in text:
                problems.append((v, name, "no profile data"))
            if any(o not in text for o in opts):
                problems.append((v, name, "card does not list all options"))
            yrs = [int(y) for y in re.findall(r'" \((\d{4})[);]', text)]
            if any(y < born + ca.AGE_MIN for y in yrs):
                problems.append((v, name, f"defining work before age {ca.AGE_MIN} (born {born}: {yrs})"))
            d = defining.get(name)
            if not d:
                problems.append((v, name, "no defining-works entry"))
            else:
                pool_ids = {w["paper_id"] for w in pools.get(name, {}).get("works", [])}
                bad = [p["paper_id"] for p in d.get("picks", []) if p["paper_id"] not in pool_ids]
                if bad:
                    problems.append((v, name, f"defining pick outside the pool: {bad}"))
    print(f"{n} cards checked ({a.field}); problems: {len(problems)}")
    for v, name, why in problems:
        print(f"  {v:<8} {name:<30} {why}")
    return 1 if problems else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["births", "pools", "reference", "merge-picks", "cards", "check"])
    ap.add_argument("--field", default="chemistry")
    a = ap.parse_args()
    fn = {"births": cmd_births, "pools": ca.cmd_pools, "reference": ca.cmd_reference, "merge-picks": cmd_merge_picks,
          "cards": cmd_cards,
          "check": cmd_check}[a.cmd]
    sys.exit(fn(a))


if __name__ == "__main__":
    main()
