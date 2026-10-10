#!/usr/bin/env python3
"""crawl_econ_prizes.py: every Sveriges Riksbank Prize in Economic Sciences in Memory of Alfred Nobel, with its
laureates and prize motivations, from the nobelprize.org list page, cross-checked against the Nobel Prize API.

    python crawl_econ_prizes.py             # fetch the three sources, parse, check, write the outputs
    python crawl_econ_prizes.py --offline   # re-parse the newest saved raw files (no network)

Sources (saved under raw/ with the fetch date; three requests, one second apart):
  - the list page in its "All Years" view, https://www.nobelprize.org/prizes/lists/all-prizes-in-economic-sciences/all/
    (the default view of .../all-prizes-in-economic-sciences/ shows 2020-2025 only)
  - the Nobel Prize API 2.1, prizes:    https://api.nobelprize.org/2.1/nobelPrizes?nobelPrizeCategory=eco
  - the Nobel Prize API 2.1, laureates: https://api.nobelprize.org/2.1/laureates?nobelPrizeCategory=eco

The list page gives, per prize year, the motivation groups (a year with two motivations was divided between two
works) with the laureates of each group and the overall ("top") motivation where there is one. The API adds each
laureate's share of the prize, affiliation at the time of the prize, gender, birth and death. Every laureate on the page
is matched to an API record (same year, same file name or same name) and the two motivation texts are compared.

Outputs (this folder):
  - econ_prizes_laureates.csv   one row per prize year x laureate
  - econ_prizes_by_year.csv     one row per prize year
  - econ_prizes.md              the readable document: every prize by decade, the checks
  - crawl_report.json           fetch metadata, counts and every check result

Licences: the API data are free to use under CC0 (terms linked in every API response); the list page is
(c) Nobel Prize Outreach. The raw page copy stays local (see ../.gitignore); the tables and the document are built from
facts that the CC0 API carries as well and cite both sources.
"""
import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
LIST_URL = "https://www.nobelprize.org/prizes/lists/all-prizes-in-economic-sciences/all/"
API_PRIZES = "https://api.nobelprize.org/2.1/nobelPrizes"
API_LAUREATES = "https://api.nobelprize.org/2.1/laureates"
UA = {"User-Agent": "KnowledgeLab-NobelResearch/1.0 (one-off research crawl; University of Chicago)"}
PRIZE_NAME = "Sveriges Riksbank Prize in Economic Sciences in Memory of Alfred Nobel"


# ---------------------------------------------------------------- fetch

def fetch(today):
    """Fetch the three sources and save them as raw files; returns the fetch metadata."""
    RAW.mkdir(exist_ok=True)
    meta = []
    jobs = [("list_all.html", LIST_URL, None),
            ("api_nobelPrizes_eco.json", API_PRIZES, {"nobelPrizeCategory": "eco", "limit": 200, "sort": "asc"}),
            ("api_laureates_eco.json", API_LAUREATES, {"nobelPrizeCategory": "eco", "limit": 300})]
    for i, (name, url, params) in enumerate(jobs):
        if i:
            time.sleep(1.0)
        r = requests.get(url, params=params, headers=UA, timeout=60)
        r.raise_for_status()
        path = RAW / f"{today}_{name}"
        path.write_text(r.text, encoding="utf-8")
        meta.append({"file": path.name, "url": r.url, "status": r.status_code, "bytes": len(r.content),
                     "fetched_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    (RAW / f"{today}_fetch_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")   # for --offline
    return meta


def newest_raw(name):
    files = sorted(RAW.glob(f"*_{name}"))
    if not files:
        sys.exit(f"no raw file *_{name} in {RAW}; run without --offline first")
    return files[-1]


# ---------------------------------------------------------------- parse the list page

def clean(text):
    """Collapse whitespace and strip the typographic quotes around a motivation."""
    text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
    return text.strip("“”\"").strip()


def fold(name):
    """Accent- and punctuation-free lower-case name, for matching page names with API names."""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", "", name.lower().replace("-", " ")).split()


def parse_list(page_html):
    soup = BeautifulSoup(page_html, "html.parser")
    intro = None
    for p in soup.find_all("p"):
        t = clean(p.get_text(" "))
        if re.search(r"has been awarded \d+ times to \d+ laureates", t):
            intro = t
            break
    prizes = []
    for card in soup.select("div.card-prize"):
        a = card.select_one("h3 a")
        if a is None:
            continue
        title = clean(a.get_text(" "))
        m = re.search(r"(\d{4})$", title)
        if not m:
            continue
        year = int(m.group(1))
        top = card.select_one("blockquote.card-prize--top-motivation")
        groups = []
        for links in card.select("div.card-prize--laureates--links"):
            box = links.parent
            people = [{"name": clean(x.get_text(" ")), "facts_url": x.get("href")}
                      for x in links.select("a.card-prize--laureates--links--link")]
            mot = box.select_one("blockquote.card-prize--laureates--motivation")
            groups.append({"laureates": people, "motivation": clean(mot.get_text(" ")) if mot else None})
        prizes.append({"year": year, "title": title, "summary_url": a.get("href"),
                       "top_motivation": clean(top.get_text(" ")) if top else None, "groups": groups})
    return intro, prizes


# ---------------------------------------------------------------- the API records

def en(x):
    return (x or {}).get("en") if isinstance(x, dict) else x


def api_tables(prizes_json, laureates_json):
    """{year: prize record} and {laureate id: laureate record} from the two API files."""
    by_year = {}
    for p in prizes_json["nobelPrizes"]:
        by_year[int(p["awardYear"])] = p
    people = {lau["id"]: lau for lau in laureates_json["laureates"]}
    return by_year, people


def affiliation_text(aff):
    parts = [en(aff.get("name")), en(aff.get("city")), en(aff.get("country"))]
    return ", ".join(x for x in parts if x)


# ---------------------------------------------------------------- build the tables and checks

def birth_day(date, year):
    """(birth date, precision): the API writes an unknown month and day as YYYY-00-00; keep only the year then."""
    if date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) and "-00" not in date[4:]:
        return date, "day"
    return (str(year), "year") if str(year).isdigit() else (None, None)


def age_at(bdate, precision, year_of_birth, awarded, prize_year):
    """(age on the award date, approximate?): exact from the birth date and the date awarded, else the year difference."""
    try:
        aw = dt.date.fromisoformat(awarded) if awarded else None
    except ValueError:
        aw = None
    if precision == "day" and aw:
        b = dt.date.fromisoformat(bdate)
        return aw.year - b.year - ((aw.month, aw.day) < (b.month, b.day)), False
    if str(year_of_birth).isdigit():
        return prize_year - int(year_of_birth), True
    return None, None


def build(intro, page, api_prizes, api_people):
    rows, years, checks, notes = [], [], [], []
    for prize in sorted(page, key=lambda p: p["year"]):
        y = prize["year"]
        ap = api_prizes.get(y)
        if ap is None:
            checks.append({"year": y, "check": "api prize record", "ok": False, "detail": "missing in API"})
            continue
        api_laur = ap.get("laureates") or []
        api_top = clean(en(ap.get("topMotivation"))) or None
        if api_top or prize["top_motivation"]:
            checks.append({"year": y, "check": "top motivation page = API", "ok": api_top == prize["top_motivation"],
                           "detail": f"page: {prize['top_motivation']!r} | api: {api_top!r}"})
        used = set()
        for gi, g in enumerate(prize["groups"], 1):
            for person in g["laureates"]:
                slug = (person["facts_url"] or "").rstrip("/").split("/")[-2] if person["facts_url"] else ""
                match = None
                for la in api_laur:
                    rec = api_people.get(la["id"], {})
                    if la["id"] in used:
                        continue
                    if slug and rec.get("fileName") == slug:
                        match = la
                        break
                if match is None:                       # fall back to the name
                    for la in api_laur:
                        if la["id"] not in used and fold(en(la.get("knownName")) or en(la.get("fullName")) or "") == fold(person["name"]):
                            match = la
                            break
                if match is None:
                    checks.append({"year": y, "check": "laureate matched to API", "ok": False, "detail": person["name"]})
                    rows.append(row_without_api(prize, gi, g, person))
                    continue
                used.add(match["id"])
                rec = api_people.get(match["id"], {})
                pz = next((n for n in rec.get("nobelPrizes", []) if int(n.get("awardYear", 0)) == y
                           and en(n.get("category")) == "Economic Sciences"), {})
                if not rec or not pz:
                    checks.append({"year": y, "check": "API laureate record with this prize", "ok": False,
                                   "detail": f"{person['name']}: " + ("no laureate record" if not rec else
                                                                      "no economics prize entry in the record")})
                api_mot = clean(en(match.get("motivation")) or en(pz.get("motivation")))
                mot_ok = api_mot == g["motivation"]
                if not mot_ok:
                    checks.append({"year": y, "check": "motivation page = API", "ok": False,
                                   "detail": f"{person['name']}: page {g['motivation']!r} | api {api_mot!r}"})
                birth = rec.get("birth") or {}
                death = rec.get("death") or {}
                by = (birth.get("year") or (birth.get("date") or "")[:4])
                bdate, bprec = birth_day(birth.get("date"), by)
                age, age_approx = age_at(bdate, bprec, by, pz.get("dateAwarded") or ap.get("dateAwarded"), y)
                affs = pz.get("affiliations") or []
                for a in affs:                          # source quirks worth a note (e.g. two names run together)
                    nm = en(a.get("name")) or ""
                    if re.search(r"[a-z]{3,}[A-Z][a-z]{2,}", nm):
                        notes.append(f"{y}, {person['name']}: the API affiliation name reads \"{nm}\" (kept as given)")
                rows.append({
                    "year": y, "prize": PRIZE_NAME, "group": gi, "group_size": len(g["laureates"]),
                    "n_groups": len(prize["groups"]), "laureate": person["name"],
                    "full_name": en(rec.get("fullName")) or en(match.get("fullName")),
                    "family_name": en(rec.get("familyName")),
                    "portion": match.get("portion") or pz.get("portion"),
                    "motivation": g["motivation"], "motivation_api": api_mot, "motivation_matches_api": mot_ok,
                    "top_motivation": prize["top_motivation"],
                    "affiliations": " ; ".join(affiliation_text(a) for a in affs),
                    "affiliations_short": " / ".join(", ".join(x for x in (en(a.get("name")), en(a.get("city"))) if x)
                                                     for a in affs),
                    "affiliation_countries": " ; ".join(dict.fromkeys(en(a.get("countryNow")) or en(a.get("country")) or "" for a in affs)),
                    "gender": rec.get("gender"), "birth_date": bdate, "birth_date_precision": bprec,
                    "birth_country_now": en((birth.get("place") or {}).get("countryNow")),
                    "death_date": death.get("date"),
                    "date_awarded": pz.get("dateAwarded") or ap.get("dateAwarded"),
                    "age_at_award": age, "age_approximate": age_approx,
                    "api_laureate_id": match["id"], "wikidata_id": (rec.get("wikidata") or {}).get("id"),
                    "facts_url": person["facts_url"], "summary_url": prize["summary_url"]})
        left = [la for la in api_laur if la["id"] not in used]
        if left:
            checks.append({"year": y, "check": "every API laureate on the page", "ok": False,
                           "detail": ", ".join(en(la.get("knownName")) or la["id"] for la in left)})
        yr = [r for r in rows if r["year"] == y]
        years.append({
            "year": y, "prize": PRIZE_NAME, "n_laureates": len(yr), "n_groups": len(prize["groups"]),
            "laureates": "; ".join(f"{r['laureate']} ({r['portion']})" for r in yr),
            "top_motivation": prize["top_motivation"],
            "motivations": " | ".join(g["motivation"] or "" for g in prize["groups"]),
            "summary_url": prize["summary_url"]})
    api_years = sorted(y for y, p in api_prizes.items() if p.get("laureates"))
    page_years = sorted(p["year"] for p in page)
    checks.append({"check": "prize years page = API", "ok": api_years == page_years,
                   "detail": f"page {len(page_years)} years, API {len(api_years)} awarded years"})
    n_api_laur = sum(len(p.get("laureates") or []) for p in api_prizes.values())
    checks.append({"check": "laureate count page = API", "ok": len(rows) == n_api_laur,
                   "detail": f"page {len(rows)}, API {n_api_laur}"})
    m = re.search(r"awarded (\d+) times to (\d+) laureates between (\d{4}) and (\d{4})", intro or "")
    if m:
        ok = (int(m.group(1)), int(m.group(2))) == (len(years), len(rows))
        checks.append({"check": "counts = page intro", "ok": ok, "detail": intro})
    else:
        checks.append({"check": "counts = page intro", "ok": False, "detail": "intro sentence not found"})
    checks.append({"check": "every page motivation equals the API text",
                   "ok": all(r.get("motivation_matches_api") for r in rows),
                   "detail": f"{sum(bool(r.get('motivation_matches_api')) for r in rows)} of {len(rows)} equal"})
    return rows, years, checks, notes


def row_without_api(prize, gi, g, person):
    return {"year": prize["year"], "prize": PRIZE_NAME, "group": gi, "group_size": len(g["laureates"]),
            "n_groups": len(prize["groups"]), "laureate": person["name"], "full_name": None, "family_name": None,
            "portion": None,
            "motivation": g["motivation"], "motivation_api": None, "motivation_matches_api": False,
            "top_motivation": prize["top_motivation"], "affiliations": None, "affiliations_short": None,
            "affiliation_countries": None,
            "gender": None, "birth_date": None, "birth_date_precision": None, "birth_country_now": None,
            "death_date": None, "date_awarded": None, "age_at_award": None, "age_approximate": None,
            "api_laureate_id": None, "wikidata_id": None, "facts_url": person["facts_url"],
            "summary_url": prize["summary_url"]}


# ---------------------------------------------------------------- write

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def md_escape(s):
    return (s or "").replace("|", "\\|")


def write_md(path, rows, years, checks, notes, meta, intro, crawled):
    n_split = sum(1 for y in years if y["n_groups"] > 1)
    n_women = sum(1 for r in rows if r["gender"] == "female")
    lines = [
        f"# {PRIZE_NAME}: every prize, {years[0]['year']}–{years[-1]['year']}",
        "",
        f"Laureates and prize motivations of all {len(years)} prizes ({len(rows)} laureates), crawled {crawled} from the "
        f"nobelprize.org list [All prizes in economic sciences]({LIST_URL}) and cross-checked against the "
        "[Nobel Prize API](https://api.nobelprize.org/2.1/nobelPrizes?nobelPrizeCategory=eco) (CC0), which also gives "
        "each laureate's share and affiliation at the time of the prize. Built by `crawl_econ_prizes.py`; tables: "
        "`econ_prizes_by_year.csv`, `econ_prizes_laureates.csv`.",
        "",
        f"- The page says: *{intro}*" if intro else "- The page's count sentence was not found.",
        f"- {n_split} prizes were divided between two works (two motivations in the year); {n_women} laureates are women.",
        "- **Share** is the laureate's portion of the prize; **motivation** is the official wording; where a year has "
        "two works, the overall motivation (if the page gives one) is shown above them.",
        "- **Affiliation** is at the time of the prize (API: institution, city); a laureate can have several; – = none "
        "recorded.",
        "",
    ]
    by_year = {}
    for r in rows:
        by_year.setdefault(r["year"], []).append(r)
    decade = None
    for y in years:
        d = y["year"] // 10 * 10
        if d != decade:
            decade = d
            lines += ["", f"## {d}s", "", "| Year | Laureates (share) | Motivation | Affiliation at the prize |",
                      "|---|---|---|---|"]
        yr = by_year[y["year"]]
        groups = sorted({r["group"] for r in yr})
        first = True
        if y["top_motivation"]:
            lines.append(f"| **{y['year']}** | | *overall:* {md_escape(y['top_motivation'])} | |")
            first = False
        for g in groups:
            people = [r for r in yr if r["group"] == g]
            names = ", ".join(f"{md_escape(r['laureate'])} ({r['portion'] or '?'})" for r in people)
            affs = "; ".join(f"{md_escape(r['family_name'] or r['laureate'].split()[-1])}: "
                             f"{md_escape(r['affiliations_short'] or '–')}"
                             for r in people) if len(people) > 1 else md_escape(people[0]["affiliations_short"] or "–")
            ycell = f"**{y['year']}**" if first else ""
            first = False
            lines.append(f"| {ycell} | {names} | {md_escape(people[0]['motivation'])} | {affs} |")
    lines += ["", "## Checks", "", "| Check | Result | Detail |", "|---|---|---|"]
    for c in checks:
        label = c["check"] + (f" ({c['year']})" if "year" in c else "")
        lines.append(f"| {md_escape(label)} | {'ok' if c['ok'] else '**FAILED**'} | {md_escape(str(c.get('detail', '')))} |")
    if notes:
        lines += ["", "## Notes on the source data", ""] + [f"- {md_escape(n)}" for n in notes]
    lines += ["", "## Sources", ""]
    for m in meta:
        lines.append(f"- `{m['file']}`: {m['url']} (HTTP {m['status']}, {m['bytes']:,} bytes, fetched {m['fetched_utc']})")
    lines += ["", "Data: Nobel Prize API, CC0 "
              "(https://www.nobelprize.org/about/terms-of-use-for-api-nobelprize-org-and-data-nobelprize-org/). "
              "List page: © Nobel Prize Outreach, https://www.nobelprize.org.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--offline", action="store_true", help="re-parse the newest saved raw files, no network")
    a = ap.parse_args()
    today = dt.date.today().isoformat()
    if a.offline:
        files = {n: newest_raw(n) for n in ("list_all.html", "api_nobelPrizes_eco.json", "api_laureates_eco.json")}
        crawled = files["list_all.html"].name[:10]
        saved = RAW / f"{crawled}_fetch_meta.json"
        if saved.exists():                                  # the metadata written when these files were fetched
            meta = json.loads(saved.read_text(encoding="utf-8"))
        else:
            meta = [{"file": p.name, "url": {"list_all.html": LIST_URL, "api_nobelPrizes_eco.json": API_PRIZES,
                                             "api_laureates_eco.json": API_LAUREATES}[n], "status": "saved",
                     "bytes": p.stat().st_size, "fetched_utc": p.name[:10]} for n, p in files.items()]
    else:
        meta = fetch(today)
        files = {n: RAW / f"{today}_{n}" for n in ("list_all.html", "api_nobelPrizes_eco.json", "api_laureates_eco.json")}
        crawled = today
    intro, page = parse_list(files["list_all.html"].read_text(encoding="utf-8"))
    api_prizes, api_people = api_tables(json.loads(files["api_nobelPrizes_eco.json"].read_text(encoding="utf-8")),
                                        json.loads(files["api_laureates_eco.json"].read_text(encoding="utf-8")))
    rows, years, checks, notes = build(intro, page, api_prizes, api_people)
    write_csv(HERE / "econ_prizes_laureates.csv", rows)
    write_csv(HERE / "econ_prizes_by_year.csv", years)
    write_md(HERE / "econ_prizes.md", rows, years, checks, notes, meta, intro, crawled)
    report = {"crawled": crawled, "sources": meta, "page_intro": intro, "n_prizes": len(years),
              "n_laureates": len(rows), "checks": checks, "source_notes": notes}
    (HERE / "crawl_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    failed = [c for c in checks if not c["ok"]]
    print(f"{len(years)} prizes, {len(rows)} laureates; checks: {len(checks) - len(failed)} ok, {len(failed)} failed")
    for c in failed:
        print("  FAILED:", c)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
