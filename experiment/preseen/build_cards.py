#!/usr/bin/env python3
"""build_cards.py: profile cards for the Preseen treat arm (SPEC §9).

    $PY build_cards.py reference              # cards/laureate_reference.csv: 2000-2025 laureates of all three fields at prize time
    $PY build_cards.py check A5108093963      # headline metrics of one profile (to compare with its record)
    $PY build_cards.py cards --field medicine # cards/<field>/00_definitions.md + one card per person
    $PY build_cards.py reference --out cards_v2; $PY build_cards.py cards --field medicine --out cards_v2
                                              # the same into another folder (cards/ keeps the cards the runs used)

Headline metrics come from a profile's output/<author id>/ tables, research works (article, review, letter) published up
to the window's last year (config profiles.year_max, 2021); citing inventions and citing books over all works of the
record, undated ones included (as the records count them). For a laureate "at prize time" only works published before
the prize year count (undated works are left out), citing patents / citing books only with a citation year before the
prize year (undated book citations are left out), and own patents only when granted before the prize year.
"""
import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests
import yaml

HERE = Path(__file__).resolve().parent
CFG = yaml.safe_load((HERE / "config.yaml").read_text())
REPO = Path(CFG["repo_root"])
OUT = REPO / "output"
RESEARCH = {"article", "review", "letter"}
YEAR_MAX = CFG["profiles"]["year_max"]


def read(folder, name, **kw):
    p = folder / name
    if not p.exists():
        return None
    return pd.read_parquet(p, **kw) if p.suffix == ".parquet" else pd.read_csv(p, **kw)


def metrics(folder, before=None):
    """Headline metrics of one profile folder; `before` = a prize year (only what happened before it counts)."""
    cut = min(YEAR_MAX + 1, before) if before else YEAR_MAX + 1
    pm = read(folder, "papers_metrics.parquet", columns=["paper_id", "year", "doctype", "C_5_pctl"])
    if pm is None:
        return None
    works = pm[pm.year < cut]
    res = works[works.doctype.isin(RESEARCH)]
    c5 = res.C_5_pctl.dropna()
    m = {"n_works": len(res), "n_impact": len(c5),
         "impact_median": round(float(c5.median()), 4) if len(c5) else None,
         "top10": round(float((c5 >= 0.90).mean()), 4) if len(c5) else None,
         "top1": round(float((c5 >= 0.99).mean()), 4) if len(c5) else None}
    ids = set(works.paper_id) if before else set(pm.paper_id)   # whole record incl. undated works, as the records count
    pc = read(folder, "patents_citing_papers.csv", usecols=["paper_id", "invention_id", "cite_year"])
    if pc is not None:
        pc = pc[pc.paper_id.isin(ids)]
        if before:
            pc = pc[pc.cite_year < before]
        m["citing_inventions"] = int(pc.invention_id.nunique())
    else:
        m["citing_inventions"] = 0
    pt = read(folder, "patents_metrics.parquet", columns=["patent_type", "grant_year"])
    m["own_patents"] = int(((pt.patent_type == "utility") & (pt.grant_year < cut)).sum()) if pt is not None else 0
    cb = read(folder, "citing_books.csv", usecols=["paper_id", "book_id", "book_year"])
    if cb is not None:
        cb = cb[cb.paper_id.isin(ids)]
        if before:
            cb = cb[cb.book_year < before]
        m["book_works"] = int(cb.paper_id.nunique())
        m["citing_books"] = int(cb.book_id.nunique())
    else:
        m["book_works"] = m["citing_books"] = 0
    return m


def laureates():
    """2000-2025 laureates of the three fields with a profile: (field key, prize year, name, profile folder)."""
    t = pd.read_csv(OUT / "batch_prizeatlas" / "targets.tsv", sep="\t")
    cat_to_field = {CFG["fields"][f]["prizeatlas_category"]: f for f in CFG["order"]}
    y0, y1 = CFG["profiles"]["laureate_reference_years"]
    skip = set(CFG["profiles"]["exclude_unresolved_laureates"])
    rows = []
    for r in t.itertuples():
        for prize in str(r.prizes).split(";"):
            cat, _, year = prize.strip().rpartition(" ")
            if cat in cat_to_field and year.isdigit() and y0 <= int(year) <= y1 and r.aid not in skip:
                rows.append((cat_to_field[cat], int(year), r.name, r.aid))
    return rows


def set_out(name):
    """Cards folder of this call (default cards/); a new folder starts its title cache from the one in cards/."""
    global TITLE_CACHE
    d = HERE / name
    d.mkdir(exist_ok=True)
    TITLE_CACHE = d / "_titles_cache.json"
    seed = HERE / "cards" / "_titles_cache.json"
    if not TITLE_CACHE.exists() and seed.exists():
        TITLE_CACHE.write_text(seed.read_text())
    return d


def cmd_reference(a):
    cards = set_out(a.out)
    rows, missing = [], []
    for field, year, name, aid in laureates():
        m = metrics(OUT / aid, before=year)
        if m is None:
            missing.append((field, year, name, aid))
            continue
        rows.append({"field": field, "prize_year": year, "name": name, "author_id": aid, **m})
    df = pd.DataFrame(rows).sort_values(["field", "prize_year", "name"])
    out = cards / "laureate_reference.csv"
    df.to_csv(out, index=False)
    (cards / "laureate_reference_missing.json").write_text(json.dumps(missing, indent=1, ensure_ascii=False))
    print(f"{out.relative_to(HERE)}: {len(df)} laureates with a profile; {len(missing)} without (laureate_reference_missing.json)")
    print(df.groupby("field").agg(n=("name", "size"), impact_median=("impact_median", "median"), top10=("top10", "median"),
                                  citing_inventions=("citing_inventions", "median"), own_patents=("own_patents", "median"),
                                  citing_books=("citing_books", "median")).to_string())


# ---------------------------------------------------------------- cards (SPEC §9)

TITLE_CACHE = HERE / "cards" / "_titles_cache.json"
UA = {"User-Agent": "nobel-preseen-cards/0.1 (academic research; python-requests)"}
DEFINITIONS = """# Definitions used in the profile notes

Each profile note describes one person named in an option, from the OpenAlex 2026-01 snapshot (works, citations,
book citations), PatentsView 2025-12-31 (US patents) and Reliance on Science (patent-to-paper citations). The window
is works published, and patents granted, up to {year_max}.

- **Research works**: articles, reviews and letters.
- **Impact percentile**: a work's 5-year citation count compared with all OpenAlex works of the same publication year
  and field: 0 = lowest, 0.5 = typical, 1 = highest. "Top 10 %" / "top 1 %" = percentile at least 0.90 / 0.99.
- **Disruption percentile**: the 5-year disruption index (CD) of a work, as a percentile of the same cohort: high
  when the works citing it do not also cite its references. Works without references have no value.
- **Foundation share**: the share of the works citing a work within 5 years that build on the work itself rather
  than on its references.
- **Citing inventions**: distinct inventions (US patents and pre-grant publications) whose front-page or in-text
  references cite the person's works; **own patents**: US utility patents with the person as an inventor.
- **Textbook reach**: citations from books, book chapters and reference entries; "citing books" counts distinct books.
- **Nobel laureate co-authors**: co-authors (works with at most 50 authors) who are Nobel laureates in physics,
  chemistry or physiology or medicine; **people on both sides**: people who are both a co-author and a co-inventor.
- **Reference lines** compare a person's value with the {field_name} laureates of {y0}-{y1} measured at the time of
  their prize: only their works published before the prize year, and only patent and book citations dated before
  it (undated works and citations left out). The person's own values cover the whole record up to {year_max}.

These are descriptive bibliometric measures, not forecasts.
"""


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def person_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", fold(name)).strip("-")


def find_profile(ids):
    """output/<id>/ of a profile run for these ids (the notebook's author id check may have moved it to another id)."""
    first = REPO / "output" / ids[0]
    if (first / "manifest.json").exists():
        return first
    for man in (REPO / "output").glob("A*/manifest.json"):
        try:
            if ids[0] in json.loads(man.read_text()).get("author_id_check", {}).get("input_ids", []):
                return man.parent
        except ValueError:
            continue
    return None


def titles_for(ids_titles):
    """{work id: title}, filling empty titles with single-work OpenAlex lookups (cached in cards/_titles_cache.json)."""
    cache = json.loads(TITLE_CACHE.read_text()) if TITLE_CACHE.exists() else {}
    out = {}
    for wid, t in ids_titles.items():
        if isinstance(t, str) and t.strip():
            out[wid] = t.strip()
            continue
        if wid not in cache:
            try:
                r = requests.get(f"https://api.openalex.org/works/{wid}", params={"select": "title"}, headers=UA, timeout=30)
                cache[wid] = (r.json().get("title") if r.ok else None) or None
            except requests.RequestException:
                cache[wid] = None
            TITLE_CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
            time.sleep(0.2)
        out[wid] = cache[wid] or "(title not available)"
    return out


def nobel_coauthors(folder, own_ids):
    co = read(folder, "coauthor_nodes.csv", usecols=["id", "name", "n_shared"])
    if co is None or co.empty:
        return []
    pa = pd.read_csv(REPO / "Data/prizeatlas/prizeatlas_nobel_laureates.csv", usecols=["year", "category_en", "name", "openalex_author_id"])
    t = pd.read_csv(OUT / "batch_prizeatlas" / "targets.tsv", sep="\t", usecols=["aid", "name", "prizes"])
    lut = {}
    for r in pa.dropna(subset=["openalex_author_id"]).itertuples():
        lut.setdefault(r.openalex_author_id, set()).add((r.name, f"{r.category_en} {r.year}"))
    for r in t.itertuples():
        for prize in str(r.prizes).split(";"):
            lut.setdefault(r.aid, set()).add((r.name, prize.strip()))
    hits = {}
    for r in co.itertuples():
        if r.id in lut and r.id not in own_ids:
            for name, prize in lut[r.id]:
                hits[name] = (prize, int(r.n_shared))
    return sorted(hits.items(), key=lambda kv: kv[1][0].split()[-1])


def ref_line(v, values, field_name, n):
    if v is None or not len(values):
        return "no laureate reference"
    below = sum(x < v for x in values) + 0.5 * sum(x == v for x in values)
    share = 100 * below / len(values)
    who = f"{n} {field_name} laureates of 2000-2025 at prize time"
    if share >= 99.5:
        return f"higher than all {who}"
    if share <= 0.5:
        return f"lower than all {who}"
    return f"higher than {share:.0f} % of the {who}"


def plural(x, word):
    n = 0 if x is None or pd.isna(x) else int(x)
    return f"{n:,} {word}{'' if n == 1 else 's'}"


def fmt_pct(x):
    return "n/a" if x is None or pd.isna(x) else f"{100 * x:.0f} %"


def fmt_p(x):
    return "n/a" if x is None or pd.isna(x) else f"{x:.2f}"


def card(field, person, ids, options, aff, prior, ref):
    folder = find_profile(ids)
    f = CFG["fields"][field]
    head = [f"# {person}", "", f"Affiliation: {aff or 'not available'}.",
            "Listed under: " + "; ".join(f"option \"{o}\"" for o in options) + ".",
            f"Prior Nobel Prize: {prior or 'none'}.", ""]
    if folder is None:
        return "\n".join(head + [CFG["profiles"]["no_profile_card"]]) + "\n", None
    m = metrics(folder)
    L = ref[ref.field == field]
    n, fname = len(L), f["prize"]
    pm = read(folder, "papers_metrics.parquet", columns=["paper_id", "year", "doctype", "title", "cited_by_count", "C_5_pctl",
                                                         "CD_5_rpctl_mid", "F_5", "n_citing_inventions", "n_books"])
    res = pm[pm.doctype.isin(RESEARCH) & (pm.year <= YEAR_MAX)].sort_values(["cited_by_count", "C_5_pctl"], ascending=False)
    top = res.head(CFG["profiles"]["defining_works"])
    tit = titles_for(dict(zip(top.paper_id, top.title)))
    works = []
    for k, r in enumerate(top.itertuples(), 1):
        works.append(f"{k}. \"{tit[r.paper_id]}\" ({int(r.year)}): impact percentile {fmt_p(r.C_5_pctl)}, disruption percentile "
                     f"{fmt_p(r.CD_5_rpctl_mid)}, Foundation share {fmt_p(r.F_5)}, cited by {plural(r.n_citing_inventions, 'invention')} "
                     f"and {plural(r.n_books, 'book')}.")
    co = nobel_coauthors(folder, set(ids))
    ov = read(folder, "collaborators_overlap.csv")
    both = 0 if ov is None else len(ov)
    body = [
        "## Impact",
        f"- Research works analysed: {m['n_works']} (published {int(res.year.min()) if len(res) else '-'}-{YEAR_MAX}).",
        f"- Median impact percentile: {fmt_p(m['impact_median'])} ({ref_line(m['impact_median'], L.impact_median.dropna().tolist(), fname, n)}).",
        f"- Works in the cohort top 10 %: {fmt_pct(m['top10'])} ({ref_line(m['top10'], L.top10.dropna().tolist(), fname, n)}); "
        f"top 1 %: {fmt_pct(m['top1'])} ({ref_line(m['top1'], L.top1.dropna().tolist(), fname, n)}).",
        "",
        "## Three defining works (most cited research works)",
        *works,
        "",
        "## Technological translation",
        f"- Distinct citing inventions: {m['citing_inventions']:,} ({ref_line(m['citing_inventions'], L.citing_inventions.tolist(), fname, n)}).",
        f"- Own US utility patents: {m['own_patents']} ({ref_line(m['own_patents'], L.own_patents.tolist(), fname, n)}).",
        "",
        "## Textbook reach",
        f"- Works cited by books: {m['book_works']:,} ({ref_line(m['book_works'], L.book_works.tolist(), fname, n)}).",
        f"- Distinct citing books: {m['citing_books']:,} ({ref_line(m['citing_books'], L.citing_books.tolist(), fname, n)}).",
        "",
        "## Collaboration",
        "- Nobel laureate co-authors: " + ("; ".join(f"{a} ({b}; {k} shared work{'s' if k != 1 else ''})" for a, (b, k) in co)
                                           if co else "none") + ".",
        f"- People who are both co-authors and co-inventors: {both}.",
    ]
    return "\n".join(head + body) + "\n", folder


def cmd_cards(a):
    field = a.field
    cards = set_out(a.out)
    ref = pd.read_csv(cards / "laureate_reference.csv")
    cand = json.loads((HERE / "committee" / field / "candidates.json").read_text())
    options = {}
    for o in cand["options"]:
        for p in o.get("people", []):
            options.setdefault(p["name"], []).append(o["option"])
    ident = list(csv.DictReader(open(HERE / "people" / f"{field}_identity.csv")))
    outdir = cards / field
    outdir.mkdir(parents=True, exist_ok=True)
    y0, y1 = CFG["profiles"]["laureate_reference_years"]
    (outdir / "00_definitions.md").write_text(DEFINITIONS.format(year_max=YEAR_MAX, field_name=CFG["fields"][field]["prize"],
                                                                 y0=y0, y1=y1))
    rows = []
    for r in ident:
        text, folder = card(field, r["person"], r["openalex_ids"].split(";"), options.get(r["person"], []),
                            r["institution"] or r["affiliation_given"], r["prior_nobel"], ref)
        path = outdir / f"{person_slug(r['person'])}.md"
        path.write_text(text)
        words = len(re.findall(r"\S+", text))
        rows.append((r["person"], path.name, words, folder.name if folder else "NO PROFILE"))
    for p, fn, w, fo in rows:
        flag = "" if 300 <= w <= 500 else "  <-- outside 300-500 words"
        print(f"  {fn:<34} {w:>4} words  {fo}{flag}")
    print(f"{field}: {len(rows)} cards + 00_definitions.md in {a.out}/{field}/; without profile: "
          f"{[p for p, _, _, fo in rows if fo == 'NO PROFILE']}")


def cmd_check(a):
    print(json.dumps(metrics(OUT / a.author_id), indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("reference"); s.add_argument("--out", default="cards", help="cards folder (default cards/)")
    s = sub.add_parser("check"); s.add_argument("author_id")
    s = sub.add_parser("cards"); s.add_argument("--field", required=True)
    s.add_argument("--out", default="cards", help="cards folder (default cards/)")
    a = ap.parse_args()
    {"reference": cmd_reference, "check": cmd_check, "cards": cmd_cards}[a.cmd](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
