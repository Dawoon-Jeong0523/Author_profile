#!/usr/bin/env python3
"""cards_age25.py: age-filtered profile cards (works and patents from age 25 on, defining works tied to the discovery).

    $PY cards_age25.py births                  # people/living_check.csv + people/births_overrides.yaml -> cards_age25/births_physics.csv
                                               # and the laureate birth years (PrizeAtlas) -> cards_age25/births_laureates_physics.csv
    $PY cards_age25.py pools                   # 60 most-cited research works per person, titles from OpenAlex (batched)
                                               # -> cards_age25/_work/pools_physics.json
    $PY cards_age25.py reference               # age-25-filtered laureate reference -> cards_age25/laureate_reference_age25.csv
    $PY cards_age25.py cards                   # cards_age25/physics/00_definitions.md + one card per shown person
    $PY cards_age25.py check                   # births complete, defining works valid, no pre-age-25 work on any card

Differences from cards/ (built by cards_pipeline.py cards): (1) only works published, and US utility patents filed, in
the year the person turned 25 or later count (collaboration lines too) — this drops early-career namesake contamination in merged OpenAlex
author records; the laureate reference is rebuilt with the same filter; (2) the three defining works are the works
most tied to the discovery of the person's option (an LLM review over the 80 most-cited works from age 25 on, live OpenAlex included; choices and reasons in
cards_age25/defining_works_physics.yaml), not simply the most cited. Identities, profiles, options and the card format
are those of cards_pipeline.py. Physics only by default (--field).
"""
import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PRESEEN = HERE.parent / "preseen"
sys.path.insert(0, str(PRESEEN))
import build_cards as bc  # noqa: E402  (read, metrics helpers, slugs, laureate reference machinery)

sys.path.insert(0, str(HERE))
import cards_pipeline as cp  # noqa: E402  (shown, identity_of)

OUT = HERE / "cards_age25"
WORK = OUT / "_work"
POOL_SIZE = 80
AGE_MIN = 25
MAX_TEAM = 50                 # the profile notebook's MAX_TEAM_SIZE: larger works are consortia
RESEARCH = bc.RESEARCH
YEAR_MAX = bc.YEAR_MAX


# ---------------------------------------------------------------- births

def cmd_births(a):
    OUT.mkdir(exist_ok=True)
    ov = {}
    ovp = HERE / "people" / "births_overrides.yaml"
    if ovp.exists():
        ov = yaml.safe_load(ovp.read_text(encoding="utf-8")) or {}
    lv = {r["person"]: r for r in csv.DictReader(open(HERE / "people" / "living_check.csv", encoding="utf-8"))
          if r["field"] == a.field}
    rows, missing = [], []
    for name, _ in cp.shown(a.field):
        o = ov.get(name)
        r = lv.get(name, {})
        ambiguous = "candidates" in r.get("status", "")
        if o:
            rows.append({"person": name, "birth_year": int(o["birth_year"]), "birth_date": o.get("birth_date", ""),
                         "source": o.get("source", "overrides"), "source_detail": o.get("source_detail", ""),
                         "confidence": o.get("confidence", "")})
        elif r.get("born", "").strip() and not ambiguous:
            rows.append({"person": name, "birth_year": int(r["born"][:4]), "birth_date": r["born"],
                         "source": "wikidata", "source_detail": r.get("qid", ""), "confidence": "high"})
        else:
            missing.append(name)
    with open(OUT / f"births_{a.field}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["person", "birth_year", "birth_date", "source", "source_detail", "confidence"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda x: x["person"]))
    print(f"cards_age25/births_{a.field}.csv: {len(rows)} people; missing (need people/births_overrides.yaml): {missing}")
    # laureate births from PrizeAtlas, joined to the unfiltered reference (author id first, then name + prize year)
    ref = pd.read_csv(PRESEEN / "cards" / "laureate_reference.csv")
    ref = ref[ref.field == a.field]
    pa = pd.read_csv(REPO / "Data/prizeatlas/prizeatlas_nobel_laureates.csv",
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


def births(field):
    p = OUT / f"births_{field}.csv"
    return {r["person"]: r for r in csv.DictReader(open(p, encoding="utf-8"))}


# ---------------------------------------------------------------- pools (candidate works with titles)

def fetch_titles(ids):
    """{work id: title} for the ids missing from every local cache, 50 per OpenAlex call."""
    cache_paths = [OUT / "_titles_cache.json", HERE / "cards" / "_titles_cache.json", PRESEEN / "cards" / "_titles_cache.json"]
    cache = {}
    for p in reversed(cache_paths):
        if p.exists():
            cache.update(json.loads(p.read_text()))
    todo = sorted({i for i in ids if not cache.get(i)})
    print(f"titles: {len(ids)} works, {len(todo)} to fetch")
    for k in range(0, len(todo), 50):
        chunk = todo[k:k + 50]
        try:
            r = requests.get("https://api.openalex.org/works",
                             params={"filter": "openalex_id:" + "|".join(chunk), "select": "id,title", "per-page": 50},
                             headers=bc.UA, timeout=60)
            for w in (r.json().get("results", []) if r.ok else []):
                cache[w["id"].rsplit("/", 1)[-1]] = w.get("title") or None
        except requests.RequestException as e:
            print(f"  batch {k // 50}: {e}")
        if k % 1000 == 0 and k:
            print(f"  {k}/{len(todo)}", flush=True)
        time.sleep(0.15)
    OUT.mkdir(exist_ok=True)
    (OUT / "_titles_cache.json").write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    return cache


def profile_of(field):
    """{person: profile folder name} from cards/index.csv (built by cards_pipeline.py cards)."""
    return {r["person"]: r["profile"] for r in csv.DictReader(open(HERE / "cards" / "index.csv", encoding="utf-8"))
            if r["field"] == field and r["profile"] not in ("", "NO PROFILE", "NO IDENTITY")}


def api_top(ids):
    """The person's most-cited works in the live OpenAlex (cached in _work/api/): paper_id, title, year, type, citations."""
    d = WORK / "api"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{'_'.join(ids)}.json"
    if not f.exists():
        r = requests.get("https://api.openalex.org/works", headers=bc.UA, timeout=60,
                         params={"filter": "author.id:" + "|".join(ids), "sort": "cited_by_count:desc", "per-page": POOL_SIZE,
                                 "select": "id,title,publication_year,type,cited_by_count"})
        r.raise_for_status()
        f.write_text(json.dumps(r.json().get("results", []), ensure_ascii=False))
        time.sleep(0.15)
    return [{"paper_id": w["id"].rsplit("/", 1)[-1], "title": w.get("title"), "year": w.get("publication_year"),
             "type": w.get("type"), "cited_by_count": w.get("cited_by_count") or 0} for w in json.loads(f.read_text())]


def cmd_pools(a):
    """Candidate works per person: research works from age AGE_MIN to YEAR_MAX of the profile, plus the person's most-cited
    works in the live OpenAlex (works the metrics tables miss, and works OpenAlex credited to the person after the
    January 2026 snapshot), ranked by citations; the POOL_SIZE most cited are kept, each flagged `metrics`/`in_profile`."""
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "pool_files").mkdir(exist_ok=True)
    b = births(a.field)
    pools, all_ids = {}, set()
    for name, opts in cp.shown(a.field):
        ids = cp.identity_of(a.field, name)[0]
        folder = bc.find_profile(ids)
        if folder is None:                     # an identity fix whose profile job has not finished: the old profile
            folder = REPO / "output" / profile_of(a.field)[name]
            print(f"  {name}: no profile for {';'.join(ids)} yet; works of {folder.name} plus the live OpenAlex")
        lo = int(b[name]["birth_year"]) + AGE_MIN
        pm = pd.read_parquet(folder / "papers_metrics.parquet", columns=["paper_id", "year", "year_display", "doctype",
                                                                         "cited_by_count", "C_5_pctl", "title"])
        pm = pm.drop_duplicates("paper_id")
        cand = {}
        for r in pm[pm.doctype.isin(RESEARCH) & (pm.year <= YEAR_MAX) & (pm.year >= lo)].itertuples():
            cand[r.paper_id] = {"paper_id": r.paper_id, "year": int(r.year),
                                "cited_by_count": int(r.cited_by_count) if pd.notna(r.cited_by_count) else 0,
                                "title": r.title.strip() if isinstance(r.title, str) and r.title.strip() else None,
                                "metrics": bool(pd.notna(r.C_5_pctl)), "in_profile": True}
        prof = pm.set_index("paper_id")
        for w in api_top(ids):
            if w["paper_id"] in cand or w["type"] not in RESEARCH:
                continue
            y, in_prof, has_m = w["year"], w["paper_id"] in prof.index, False
            if in_prof:
                row = prof.loc[w["paper_id"]]
                y = next((int(v) for v in (row.year, row.year_display) if pd.notna(v)), y)
                has_m = bool(pd.notna(row.C_5_pctl))
            if not y or y < lo or y > YEAR_MAX:
                continue
            cand[w["paper_id"]] = {"paper_id": w["paper_id"], "year": int(y), "cited_by_count": int(w["cited_by_count"]),
                                   "title": (w["title"] or "").strip() or None, "metrics": has_m, "in_profile": in_prof}
        works = sorted(cand.values(), key=lambda w: (-w["cited_by_count"], w["paper_id"]))[:POOL_SIZE]
        pools[name] = {"profile": folder.name, "ids": ids, "options": opts, "birth_year": lo - AGE_MIN, "cutoff_year": lo,
                       "works": works}
        all_ids |= {w["paper_id"] for w in works if not w["title"]}
    titles = fetch_titles(all_ids)
    n_missing = 0
    for name, p in pools.items():
        for w in p["works"]:
            if not w["title"]:
                w["title"] = titles.get(w["paper_id"]) or None
                n_missing += w["title"] is None
        (WORK / "pool_files" / f"{bc.person_slug(name)}.json").write_text(
            json.dumps({"person": name, **p}, indent=1, ensure_ascii=False))
    (WORK / f"pools_{a.field}.json").write_text(json.dumps(pools, indent=1, ensure_ascii=False))
    n_api = sum(not w["metrics"] for p in pools.values() for w in p["works"])
    print(f"_work/pools_{a.field}.json + pool_files/: {len(pools)} people x <= {POOL_SIZE} works ({n_api} without metrics, "
          f"{sum(not w['in_profile'] for p in pools.values() for w in p['works'])} outside the profile); "
          f"titles still missing: {n_missing}")


# ---------------------------------------------------------------- age-filtered metrics and reference

def metrics_age(folder, born, before=None):
    """bc.metrics with the age window: works published, and patents filed (the co-inventor network's year; grant year
    where there is no filing year), from the year the person turned AGE_MIN; patents still granted before `cut`."""
    cut = min(YEAR_MAX + 1, before) if before else YEAR_MAX + 1
    lo = born + AGE_MIN
    pm = bc.read(folder, "papers_metrics.parquet", columns=["paper_id", "year", "doctype", "C_5_pctl"])
    if pm is None:
        return None
    works = pm[(pm.year < cut) & (pm.year >= lo)]
    res = works[works.doctype.isin(RESEARCH)]
    c5 = res.C_5_pctl.dropna()
    m = {"n_works": len(res), "n_impact": len(c5),
         "impact_median": round(float(c5.median()), 4) if len(c5) else None,
         "top10": round(float((c5 >= 0.90).mean()), 4) if len(c5) else None,
         "top1": round(float((c5 >= 0.99).mean()), 4) if len(c5) else None,
         "first_year": int(res.year.min()) if len(res) else None}
    ids = set(works.paper_id)                   # dated, age-filtered works only (unlike cards/, no undated works)
    pc = bc.read(folder, "patents_citing_papers.csv", usecols=["paper_id", "invention_id", "cite_year"])
    if pc is not None:
        pc = pc[pc.paper_id.isin(ids)]
        if before:
            pc = pc[pc.cite_year < before]
        m["citing_inventions"] = int(pc.invention_id.nunique())
    else:
        m["citing_inventions"] = 0
    pt = bc.read(folder, "patents_metrics.parquet", columns=["patent_type", "grant_year", "filing_year"])
    if pt is not None:
        filed = pd.to_numeric(pt.filing_year, errors="coerce").fillna(pd.to_numeric(pt.grant_year, errors="coerce"))
        m["own_patents"] = int(((pt.patent_type == "utility") & (pt.grant_year < cut) & (filed >= lo)).sum())
    else:
        m["own_patents"] = 0
    cb = bc.read(folder, "citing_books.csv", usecols=["paper_id", "book_id", "book_year"])
    if cb is not None:
        cb = cb[cb.paper_id.isin(ids)]
        if before:
            cb = cb[cb.book_year < before]
        m["book_works"] = int(cb.paper_id.nunique())
        m["citing_books"] = int(cb.book_id.nunique())
    else:
        m["book_works"] = m["citing_books"] = 0
    return m


_LUT = None


def laureate_lut():
    """{OpenAlex author id: {(laureate name, "<category> <year>")}} as build_cards.nobel_coauthors builds it."""
    global _LUT
    if _LUT is None:
        pa = pd.read_csv(REPO / "Data/prizeatlas/prizeatlas_nobel_laureates.csv",
                         usecols=["year", "category_en", "name", "openalex_author_id"])
        t = pd.read_csv(REPO / "output" / "batch_prizeatlas" / "targets.tsv", sep="\t", usecols=["aid", "name", "prizes"])
        lut = {}
        for r in pa.dropna(subset=["openalex_author_id"]).itertuples():
            lut.setdefault(r.openalex_author_id, set()).add((r.name, f"{r.category_en} {r.year}"))
        for r in t.itertuples():
            for prize in str(r.prizes).split(";"):
                lut.setdefault(r.aid, set()).add((r.name, prize.strip()))
        _LUT = lut
    return _LUT


def coauthors_age(folder, own_ids, lo):
    """{co-author id: works with at most MAX_TEAM authors shared from year lo on} (coauthor_nodes.csv n_shared_small, the
    definition the cards state), from the profile's per-work co-author cache. Years are year_display, the year the profile's co-author network uses (`year` is
    empty for works without metrics)."""
    cache = sorted((folder / "_cache").glob("coauthor_rows.*.parquet"))
    if not cache:
        return None
    rows = pd.read_parquet(cache[-1], columns=["work_id", "author_id"]).dropna()
    rows["paper_id"] = "W" + rows.work_id.astype("int64").astype(str)
    rows["author_id"] = "A" + rows.author_id.astype("int64").astype(str)
    team = rows.groupby("paper_id").author_id.nunique()
    yr = bc.read(folder, "papers_metrics.parquet", columns=["paper_id", "year_display"]).dropna(subset=["year_display"])
    keep = set(yr.loc[yr.year_display >= lo, "paper_id"]) & set(team[team <= MAX_TEAM].index)
    rows = rows[rows.paper_id.isin(keep) & ~rows.author_id.isin(own_ids)]
    return rows.groupby("author_id").paper_id.nunique().to_dict()


def nobel_coauthors_age(shared):
    lut = laureate_lut()
    hits = {}
    for aid, k in shared.items():
        for name, prize in lut.get(aid, ()):
            hits[name] = (prize, int(k))
    return sorted(hits.items(), key=lambda kv: (kv[1][0].split()[-1], -kv[1][1]))


def overlap_age(folder, shared, lo):
    """People on both sides: a collaborators_overlap.csv row counts when the co-author shares a work from year lo on and
    the co-inventor a patent from year lo on (coinventor_nodes.csv last_year)."""
    ov = bc.read(folder, "collaborators_overlap.csv")
    if ov is None or ov.empty:
        return 0
    ci = bc.read(folder, "coinventor_nodes.csv")
    late = set(ci.loc[ci.last_year >= lo, "id"].astype(str)) if ci is not None and len(ci) else set()
    return int((ov.author_id.astype(str).isin(set(shared)) & ov.inventor_id.astype(str).isin(late)).sum())


def cmd_reference(a):
    ref = pd.read_csv(PRESEEN / "cards" / "laureate_reference.csv")
    ref = ref[ref.field == a.field]
    born = pd.read_csv(OUT / f"births_laureates_{a.field}.csv").set_index(["name", "prize_year"]).birth_year.to_dict()
    rows, miss = [], []
    for r in ref.itertuples():
        y = born.get((r.name, r.prize_year))
        if y is None:
            miss.append(r.name)
            continue
        m = metrics_age(REPO / "output" / r.author_id, int(y), before=r.prize_year)
        rows.append({"field": a.field, "prize_year": r.prize_year, "name": r.name, "author_id": r.author_id,
                     "birth_year": int(y), **m})
    df = pd.DataFrame(rows).sort_values(["prize_year", "name"])
    df.to_csv(OUT / f"laureate_reference_age25_{a.field}.csv", index=False)
    print(f"cards_age25/laureate_reference_age25_{a.field}.csv: {len(df)} laureates; without birth year (left out): {miss}")
    old = ref.set_index("author_id")
    ch = [(r.name, int(old.loc[r.author_id, "n_works"]) - r.n_works) for r in df.itertuples()
          if r.author_id in old.index and old.loc[r.author_id, "n_works"] != r.n_works]
    print(f"laureates whose work count changed under the age filter: {len(ch)}; largest: "
          f"{sorted(ch, key=lambda x: -x[1])[:8]}")


# ---------------------------------------------------------------- cards

DEFINITIONS = bc.DEFINITIONS.rstrip() + """

**This folder (cards_age25) differs from cards/ in two ways.** (1) *Age window*: only research works published, and US
utility patents filed (and granted up to {year_max}), in the year the person turned {age} or later count; citing
inventions and citing books are
counted over those works only, and Nobel laureate co-authors and people on both sides over the works and patents of
those years. Birth years come from Wikidata and public bios; where none is published the year is estimated from the
education record and the note says so. The reference lines apply the same age-{age} filter to every laureate's record
before the prize year (laureate birth years from PrizeAtlas). The filter removes early-career namesake contamination
in merged OpenAlex author records. (2) *Defining
works*: the three works most tied to the discovery of the person's option — chosen by an LLM review of the person's 80
most-cited research works from age {age} on against the option text (choices and reasons in defining_works_physics.yaml)
— rather than the three most-cited works; where fewer than three works match the discovery, the most-cited remaining
works fill in. The candidates include works that the metrics tables miss, and works that OpenAlex credited to the
person after its January 2026 snapshot; such a work is listed without impact, disruption and Foundation values.
"""


FIRST_PUBLISHED = {     # landmark records whose OpenAlex year is a later reprint or record date
    "W2015179126": (1984, "reprint of the 1984 conference paper"),
    "W2168676717": (1994, "OpenAlex date of the 1994 conference paper"),
}


def work_line(prefix, title, year, r, wid=None):
    """One work as the cards print it; r = the profile's papers_metrics row, None when the work is outside the record."""
    if wid in FIRST_PUBLISHED:
        year = f"{year}; {FIRST_PUBLISHED[wid][1]}"
    if r is None:
        return (f"{prefix}\"{title}\" ({year}): outside the profile's record (OpenAlex credited it to the person after its "
                f"January 2026 snapshot), so no impact, disruption or Foundation values.")
    if pd.isna(r.C_5_pctl):
        inv = "" if pd.isna(r.n_citing_inventions) else f"; cited by {bc.plural(r.n_citing_inventions, 'invention')}"
        return (f"{prefix}\"{title}\" ({year}): no impact, disruption or Foundation values (the work is missing from the "
                f"metrics tables){inv}.")
    return (f"{prefix}\"{title}\" ({year}): impact percentile {bc.fmt_p(r.C_5_pctl)}, disruption percentile "
            f"{bc.fmt_p(r.CD_5_rpctl_mid)}, Foundation share {bc.fmt_p(r.F_5)}, cited by "
            f"{bc.plural(r.n_citing_inventions, 'invention')} and {bc.plural(r.n_books, 'book')}.")


def card_age25(field, person, ids, options, aff, prior, ref, born_row, defining, pool):
    folder = bc.find_profile(ids)
    head = [f"# {person}", "", f"Affiliation: {aff or 'not available'}.",
            "Listed under: " + "; ".join(f"option \"{o}\"" for o in options) + ".",
            f"Prior Nobel Prize: {prior or 'none'}.", ""]
    if folder is None:
        return "\n".join(head + [bc.CFG["profiles"]["no_profile_card"]]) + "\n", None, []
    born = int(born_row["birth_year"])
    m = metrics_age(folder, born)
    L = ref
    n, fname = len(L), bc.CFG["fields"][field]["prize"]
    lo = born + AGE_MIN
    pm = bc.read(folder, "papers_metrics.parquet", columns=["paper_id", "year", "year_display", "doctype", "title",
                                                            "cited_by_count", "C_5_pctl", "CD_5_rpctl_mid", "F_5",
                                                            "n_citing_inventions", "n_books"]).drop_duplicates("paper_id")
    res = pm[pm.doctype.isin(RESEARCH) & (pm.year <= YEAR_MAX) & (pm.year >= lo)]
    chosen = [p for p in (defining or {}).get("picks", []) if p.get("year") and lo <= int(p["year"]) <= YEAR_MAX]
    flags = []
    if not chosen:
        flags.append("no defining-works selection; most-cited works used")
    elif len(chosen) < 3:
        flags.append(f"only {len(chosen)} discovery-related picks; most-cited works fill in")
    ids_chosen = [p["paper_id"] for p in chosen]
    top_up = res[~res.paper_id.isin(ids_chosen)].sort_values(["cited_by_count", "C_5_pctl"], ascending=False)
    picks = ids_chosen + top_up.paper_id.head(max(0, 3 - len(ids_chosen))).tolist()
    year_of = {p["paper_id"]: int(p["year"]) for p in chosen}
    titles = {w["paper_id"]: w["title"] for w in pool.get("works", []) if w.get("title")}
    titles.update({p["paper_id"]: p["title"] for p in chosen if p.get("title")})
    prof = pm.set_index("paper_id")
    tit = {**bc.titles_for({w: (prof.title.get(w) if w in prof.index else None) for w in picks if w not in titles}), **titles}
    works = []
    for k, wid in enumerate(picks, 1):
        r = prof.loc[wid] if wid in prof.index else None
        y = year_of.get(wid) or next(int(v) for v in (r.year, r.year_display) if pd.notna(v))
        works.append(work_line(f"{k}. ", tit.get(wid, "(title not available)"), y, r, wid))
    shared = coauthors_age(folder, set(ids), born + AGE_MIN)
    if shared is None:
        flags.append("no co-author cache; collaboration over the whole record")
        co = bc.nobel_coauthors(folder, set(ids))
        ov = bc.read(folder, "collaborators_overlap.csv")
        both = 0 if ov is None else len(ov)
    else:
        co = nobel_coauthors_age(shared)
        both = overlap_age(folder, shared, born + AGE_MIN)
    rl = lambda v, c: bc.ref_line(v, L[c].dropna().tolist(), fname, n)
    born_txt = (f"born c. {born}, estimated from the education record" if born_row.get("source") == "estimated"
                else f"born {born}")
    body = [
        "## Impact",
        f"- Research works analysed: {m['n_works']} (published {m['first_year'] or '-'}-{YEAR_MAX}, from age {AGE_MIN} on; "
        f"{born_txt}).",
        f"- Median impact percentile: {bc.fmt_p(m['impact_median'])} ({rl(m['impact_median'], 'impact_median')}).",
        f"- Works in the cohort top 10 %: {bc.fmt_pct(m['top10'])} ({rl(m['top10'], 'top10')}); "
        f"top 1 %: {bc.fmt_pct(m['top1'])} ({rl(m['top1'], 'top1')}).",
        "",
        "## Three defining works (research works tied to the listed discovery)",
        *works,
        "",
        "## Technological translation",
        f"- Distinct citing inventions: {m['citing_inventions']:,} ({rl(m['citing_inventions'], 'citing_inventions')}).",
        f"- Own US utility patents: {m['own_patents']} ({rl(m['own_patents'], 'own_patents')}).",
        "",
        "## Textbook reach",
        f"- Works cited by books: {m['book_works']:,} ({rl(m['book_works'], 'book_works')}).",
        f"- Distinct citing books: {m['citing_books']:,} ({rl(m['citing_books'], 'citing_books')}).",
        "",
        "## Collaboration",
        "- Nobel laureate co-authors: " + ("; ".join(f"{x} ({b}; {k} shared work{'s' if k != 1 else ''})" for x, (b, k) in co)
                                           if co else "none") + ".",
        f"- People who are both co-authors and co-inventors: {both}.",
    ]
    return "\n".join(head + body) + "\n", folder, flags


def cmd_cards(a):
    bc.TITLE_CACHE = OUT / "_titles_cache.json"
    ref = pd.read_csv(OUT / f"laureate_reference_age25_{a.field}.csv")
    b = births(a.field)
    defining = yaml.safe_load((OUT / f"defining_works_{a.field}.yaml").read_text(encoding="utf-8")) \
        if (OUT / f"defining_works_{a.field}.yaml").exists() else {}
    pools = json.loads((WORK / f"pools_{a.field}.json").read_text(encoding="utf-8"))
    outdir = OUT / a.field
    outdir.mkdir(parents=True, exist_ok=True)
    y0, y1 = bc.CFG["profiles"]["laureate_reference_years"]
    (outdir / "00_definitions.md").write_text(
        DEFINITIONS.format(year_max=YEAR_MAX, field_name=bc.CFG["fields"][a.field]["prize"], y0=y0, y1=y1, age=AGE_MIN))
    index = []
    for name, opts in cp.shown(a.field):
        got = cp.identity_of(a.field, name)
        ids, aff, prior, src = got
        if name not in b:
            print(f"  NO BIRTH YEAR for {name} — skipped")
            index.append({"field": a.field, "person": name, "card": "", "openalex_ids": ";".join(ids),
                          "profile": "NO BIRTH YEAR", "flags": ""})
            continue
        text, folder, flags = card_age25(a.field, name, ids, opts, aff, prior, ref, b[name], defining.get(name), pools.get(name, {}))
        path = outdir / f"{bc.person_slug(name)}.md"
        path.write_text(text, encoding="utf-8")
        words = len(re.findall(r"\S+", text))
        index.append({"field": a.field, "person": name, "card": f"{a.field}/{path.name}", "openalex_ids": ";".join(ids),
                      "profile": folder.name if folder else "NO PROFILE", "flags": "; ".join(flags)})
        flag = "" if 300 <= words <= 500 else " <-- outside 300-500 words"
        print(f"  {path.name:<34} {words:>4} words{flag}{('  [' + '; '.join(flags) + ']') if flags else ''}")
    with open(OUT / "index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["field", "person", "card", "openalex_ids", "profile", "flags"])
        w.writeheader()
        w.writerows(index)
    print(f"{a.field}: {len(index)} cards in cards_age25/{a.field}/")


def cmd_check(a):
    b = births(a.field)
    defining = yaml.safe_load((OUT / f"defining_works_{a.field}.yaml").read_text(encoding="utf-8"))
    pools = json.loads((WORK / f"pools_{a.field}.json").read_text(encoding="utf-8"))
    problems = []
    for name, opts in cp.shown(a.field):
        if name not in b:
            problems.append((name, "no birth year"))
            continue
        born = int(b[name]["birth_year"])
        card = OUT / a.field / f"{bc.person_slug(name)}.md"
        if not card.exists():
            problems.append((name, "no card"))
            continue
        text = card.read_text(encoding="utf-8")
        if "## Impact" not in text:
            problems.append((name, "no profile data"))
        if any(o not in text for o in opts):
            problems.append((name, "card does not list all options"))
        yrs = [int(y) for y in re.findall(r'" \((\d{4})\):', text)]
        if any(y < born + AGE_MIN for y in yrs):
            problems.append((name, f"defining work before age {AGE_MIN} (born {born}: {yrs})"))
        d = defining.get(name)
        if d:
            pool_ids = {w["paper_id"] for w in pools.get(name, {}).get("works", [])}
            bad = [p["paper_id"] for p in d.get("picks", []) if p["paper_id"] not in pool_ids]
            if bad:
                problems.append((name, f"defining pick outside the pool: {bad}"))
    print(f"{len(b)} people with births; problems: {len(problems)}")
    for name, why in problems:
        print(f"  {name:<30} {why}")
    return 1 if problems else 0


# ---------------------------------------------------------------- option blocks (one consider note per option)

LEVEL = {"high": 2, "medium": 1, "low": 0}


def option_people(o):
    """(option text, [named people]) of a question option ('<discovery> — Name, Name')."""
    text = o if isinstance(o, str) else (o.get("text") or o.get("label") or o.get("option"))
    return text, [n.strip() for n in text.partition(" — ")[2].split(",") if n.strip()]


def fmt_mean_max(vals, kind):
    vals = [v for v in vals if v is not None and not pd.isna(v)]
    if not vals:
        return "n/a"
    mean, mx = sum(vals) / len(vals), max(vals)
    if kind == "p":
        return f"{mean:.2f} / {mx:.2f}"
    if kind == "%":
        return f"{100 * mean:.0f} % / {100 * mx:.0f} %"
    return f"{mean:,.0f} / {mx:,.0f}"


def cmd_blocks(a):
    """One note per option of a question (00_<nn>_<slug>.md, option order): option summary line, anchor works and
    maturity line, attribution confidence, then the age-25 profile note of each named person (printed once, under the
    first option that names the person)."""
    bc.TITLE_CACHE = OUT / "_titles_cache.json"
    q = json.loads(Path(a.question).read_text(encoding="utf-8"))
    q = q.get("question", q)
    opts = [option_people(o) for o in q["options"]]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("00_*.md"):
        f.unlink()
    ref = pd.read_csv(OUT / f"laureate_reference_age25_{a.field}.csv")
    b = births(a.field)
    defining = yaml.safe_load((OUT / f"defining_works_{a.field}.yaml").read_text(encoding="utf-8"))
    anchors = yaml.safe_load((OUT / f"anchor_works_{a.field}.yaml").read_text(encoding="utf-8")) \
        if (OUT / f"anchor_works_{a.field}.yaml").exists() else {}
    pools = json.loads((WORK / f"pools_{a.field}.json").read_text(encoding="utf-8"))
    lags = pd.read_csv(OUT / f"laureate_lags_{a.field}.csv") \
        if (OUT / f"laureate_lags_{a.field}.csv").exists() and not a.no_lags else None
    over = cp.overrides()
    names_in = {}
    for i, (text, people) in enumerate(opts, 1):
        for p in people:
            names_in.setdefault(p, []).append(text)
    info, works_of = {}, {}
    for p, its in names_in.items():
        ids, aff, prior, _ = cp.identity_of(a.field, p)
        text, folder, flags = card_age25(a.field, p, ids, its, aff, prior, ref, b[p], defining.get(p), pools.get(p, {}))
        born = int(b[p]["birth_year"])
        prof = bc.read(folder, "papers_metrics.parquet", columns=["paper_id", "year", "year_display", "C_5_pctl",
                                                                  "CD_5_rpctl_mid", "F_5", "n_citing_inventions",
                                                                  "n_books"]).drop_duplicates("paper_id").set_index("paper_id")
        picks = (defining.get(p) or {}).get("picks", [])
        outside = [x for x in picks if x["paper_id"] not in prof.index]
        reasons = []
        if b[p].get("source") == "estimated":
            reasons.append(f"{p}'s birth year is estimated, so the age-25 cut-off may be off by a few years")
        if p in over:
            reasons.append(f"{p}'s author record was merged by hand from two OpenAlex records")
        if outside:
            reasons.append(f"{len(outside)} of {p}'s defining works {'is' if len(outside) == 1 else 'are'} missing from the "
                           f"January 2026 author record")
        level = "low" if len(outside) >= 2 else ("medium" if reasons else "high")
        info[p] = {"card": text, "m": metrics_age(folder, born), "prof": prof, "level": level, "reasons": reasons}
        works_of[p] = {x["paper_id"]: x for x in picks}
    disc_lags = real_lags = None
    if lags is not None:
        disc_lags = (lags.prize_year - lags.discovery_year)[lags.discovery_year > 0].tolist()
        real_lags = (lags.prize_year - lags.realization_year)[lags.realization_year > 0].tolist()
    opt_works = []
    for text, people in opts:
        ws = {w for p in people for w in works_of[p]}
        ws |= {x["paper_id"] for x in (anchors.get(text.partition(" — ")[0]) or {}).get("anchors", [])}
        opt_works.append(ws)
    printed = {}
    for i, (text, people) in enumerate(opts, 1):
        disc = text.partition(" — ")[0]
        ms = [info[p]["m"] for p in people]
        shared = []
        for j, ws in enumerate(opt_works, 1):
            if j != i and opt_works[i - 1] & ws:
                shared.append(f"option {j} ({len(opt_works[i - 1] & ws)} work{'s' if len(opt_works[i - 1] & ws) != 1 else ''})")
        summary = (f"Option summary: {len(people)} named {'person' if len(people) == 1 else 'people'}. Mean / max across them: "
                   f"research works {fmt_mean_max([m['n_works'] for m in ms], 'n')}; median impact percentile "
                   f"{fmt_mean_max([m['impact_median'] for m in ms], 'p')}; works in the top 10 % "
                   f"{fmt_mean_max([m['top10'] for m in ms], '%')}; top 1 % {fmt_mean_max([m['top1'] for m in ms], '%')}; "
                   f"citing inventions {fmt_mean_max([m['citing_inventions'] for m in ms], 'n')}; own US utility patents "
                   f"{fmt_mean_max([m['own_patents'] for m in ms], 'n')}; works cited by books "
                   f"{fmt_mean_max([m['book_works'] for m in ms], 'n')}; citing books "
                   f"{fmt_mean_max([m['citing_books'] for m in ms], 'n')}. Defining or anchor works shared with other "
                   f"options: {', '.join(shared) if shared else 'none'}.")
        lines = [f"# Option {i} of {len(opts)}: {text}", "", summary]
        anc = (anchors.get(disc) or {}).get("anchors", [])
        mat = []
        if anc:
            lines += ["", "Anchor works:"]
            for x in anc:
                who = x.get("from_person")
                r = info[who]["prof"].loc[x["paper_id"]] if who in info and x["paper_id"] in info[who]["prof"].index else None
                lines.append(work_line(f"- {x['label']} ({who}): ", x["title"], int(x["year"]), r, x["paper_id"]))
                y0 = FIRST_PUBLISHED.get(x["paper_id"], (int(x["year"]),))[0]
                yrs = 2026 - y0
                pool_ = disc_lags if x["label"].startswith("discovery") else real_lags
                if pool_:
                    share = 100 * sum(l >= yrs for l in pool_) / len(pool_)
                    mat.append(f"{x['label']} work {y0}, {yrs} years before 2026 ({share:.0f} % of the 2000-2025 "
                               f"Physics laureates waited at least as long from their {x['label']} work to the prize)")
                else:
                    mat.append(f"{x['label']} work {y0}, {yrs} years before 2026")
            lines.append("Maturity: " + "; ".join(mat) + ".")
        level = min((info[p]["level"] for p in people), key=LEVEL.get)
        reasons = [r for p in people for r in info[p]["reasons"]]
        lines += ["", f"Attribution confidence: {level}" + (f" ({'; '.join(reasons)})." if reasons else
                                                             " (no estimated birth year, hand-merged record or missing landmark work).")]
        lines += ["", "## Profile notes"]
        for p in people:
            if p in printed:
                lines += ["", f"### {p}", f"Profile note printed under option {printed[p]}; it counts fully here as well."]
                continue
            printed[p] = i
            card = info[p]["card"].replace("\n## ", "\n#### ")
            lines += ["", "###" + card[1:] if card.startswith("# ") else card]
        path = out / f"00_{i:02d}_{bc.person_slug(disc)[:50]}.md"
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        print(f"  {path.name:<62} {len(path.read_text()):>6} chars  attribution {level}  anchors {len(anc)}")
    print(f"{len(opts)} option blocks in {out}")


def main():
    ap = argparse.ArgumentParser(description="Age-filtered, discovery-focused profile cards (cards_age25/).")
    ap.add_argument("--field", default="physics")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ["births", "pools", "reference", "cards", "check"]:
        sub.add_parser(c)
    s = sub.add_parser("blocks")
    s.add_argument("--question", required=True, help="question JSON whose options become the blocks")
    s.add_argument("--out", required=True, help="folder for the 00_<nn>_<slug>.md notes")
    s.add_argument("--no-lags", action="store_true",
                   help="maturity lines without laureate shares (as the 10-05 v2 runs, whose notes define them so)")
    a = ap.parse_args()
    sys.exit({"births": cmd_births, "pools": cmd_pools, "reference": cmd_reference,
              "cards": cmd_cards, "check": cmd_check, "blocks": cmd_blocks}[a.cmd](a) or 0)


if __name__ == "__main__":
    main()
