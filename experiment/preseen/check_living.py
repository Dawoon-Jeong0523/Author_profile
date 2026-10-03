#!/usr/bin/env python3
"""check_living.py: are the people shown in the committee's candidate lists alive? (Wikidata, free read-only API)

    $PY check_living.py [--fields medicine physics chemistry] [--all-people]

For every person shown in committee/<field>/candidates.json (top 3 per option; --all-people: everyone named), search
Wikidata by name (full name, then without middle names / initials), keep candidates whose description names a
scientific or medical occupation, and read date of birth (P569) and date of death (P570). Writes
committee/<field>/living_check.csv and prints the people that need a look: deceased, no match, or ambiguous.
Wikidata can lag behind very recent deaths and a same-name person can be matched; the CSV is a screen, not proof.
Requests are paced and honour 429 Retry-After; results are cached in committee/living_cache.json (failed lookups and
no-matches are asked again on the next run). No API key is involved.
"""
import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
API = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "nobel-preseen-living-check/0.1 (academic research; python-requests)"}
CACHE = HERE / "committee" / "living_cache.json"
PACE = 1.5                                     # seconds between requests
SCIENCE = re.compile(r"scien|physic|chemi|biolog|engineer|research|professor|immunolog|geneti|physician|pharmac|"
                     r"astronom|cosmolog|endocrin|oncolog|mathemat|crystallograph|material|academic|neuro|psychiat|"
                     r"cardiolog|rheumatolog|epidemiolog|medic|virolog|microbiolog|biochem|biophys|inventor", re.I)


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def variants(name):
    toks = name.replace(".", ". ").split()
    toks = [t for t in toks if t.lower().strip(".") not in {"iii", "jr", "sr", "ii"}]
    out = [" ".join(toks)]
    full = [t for t in toks if len(t.strip(".")) > 1]          # drop initials ("J. Ignacio Cirac" -> "Ignacio Cirac")
    if len(full) >= 2:
        out.append(f"{full[0]} {full[-1]}")
        out.append(" ".join(full))
    return list(dict.fromkeys(v for v in out if v))


class LookupFailed(Exception):
    pass


def get(params):
    last = "network error"
    for attempt in range(6):
        time.sleep(PACE)
        try:
            r = requests.get(API, params={**params, "format": "json"}, headers=UA, timeout=30)
        except requests.RequestException as e:
            last = type(e).__name__
            time.sleep(10)
            continue
        if r.ok:
            return r.json()
        last = f"HTTP {r.status_code}"
        if r.status_code != 429 and r.status_code < 500:
            break
        ra = r.headers.get("Retry-After", "")
        time.sleep(int(ra) if ra.isdigit() else 15 * (attempt + 1))
    raise LookupFailed(last)


def claim_date(entity, prop):
    for c in entity.get("claims", {}).get(prop, []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(v, dict) and v.get("time"):
            return v["time"].lstrip("+")[:10]
    return ""


def lookup(name):
    seen, cands = set(), []
    for q in variants(name):
        res = get({"action": "wbsearchentities", "search": q, "language": "en", "uselang": "en", "type": "item",
                   "limit": 7})
        for h in res.get("search", []):
            if h["id"] not in seen and SCIENCE.search(h.get("description", "")):
                seen.add(h["id"])
                cands.append(h)
        if cands:
            break
    if not cands:
        return {"status": "no match", "qid": "", "label": "", "description": "", "born": "", "died": "", "n": 0}
    ents = get({"action": "wbgetentities", "ids": "|".join(h["id"] for h in cands), "props": "claims",
                "languages": "en"}).get("entities", {})
    surname = fold(name.split()[-1])
    rows = []
    for h in cands:
        if surname not in fold(h.get("label", "")) and not any(surname in fold(a) for a in h.get("aliases", [])):
            continue
        e = ents.get(h["id"], {})
        rows.append({"qid": h["id"], "label": h.get("label", ""), "description": h.get("description", ""),
                     "born": claim_date(e, "P569"), "died": claim_date(e, "P570")})
    if not rows:
        return {"status": "no match", "qid": "", "label": "", "description": "", "born": "", "died": "", "n": 0}
    exact = {fold(v) for v in variants(name)}
    rows.sort(key=lambda r: (fold(r["label"]) not in exact,                    # exact name first,
                             bool(r["born"]) and r["born"][:4] < "1925"))      # then not born before 1925
    best = rows[0]
    status = "DECEASED" if best["died"] else "living (no date of death)"
    if len(rows) > 1:
        status += f"; {len(rows)} candidates, first taken"
    return {"status": status, **best, "n": len(rows),
            "others": "; ".join(f"{r['qid']} {r['label']} ({r['description']}) d.{r['died'] or '-'}" for r in rows[1:])}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fields", nargs="+", default=["medicine", "physics", "chemistry"])
    ap.add_argument("--all-people", action="store_true", help="everyone named in the top options, not only the shown 3")
    a = ap.parse_args()
    attention = []
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for field in a.fields:
        d = json.loads((HERE / "committee" / field / "candidates.json").read_text())
        rows = []
        for o in d["options"][:-1]:
            for p in o["people_all" if a.all_people else "people"]:
                r = cache.get(p["name"])
                if r is None or r["status"] in ("no match", "lookup failed"):
                    try:
                        r = lookup(p["name"])
                    except LookupFailed as e:
                        r = {"status": "lookup failed", "qid": "", "label": "", "description": str(e), "born": "",
                             "died": "", "n": 0}
                    cache[p["name"]] = r
                    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
                rows.append({"field": field, "option": o["rank"], "name": p["name"], "affiliation": p["affiliation"],
                             **{k: r.get(k, "") for k in ("status", "qid", "label", "description", "born", "died", "n",
                                                           "others")}})
                if not r["status"].startswith("living") or r["n"] != 1:
                    attention.append(rows[-1])
        out = HERE / "committee" / field / "living_check.csv"
        with out.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        n_dead = sum(r["status"].startswith("DECEASED") for r in rows)
        print(f"{field}: {len(rows)} people -> {out.relative_to(HERE)}; deceased per Wikidata: {n_dead}")
    print("\nneeds a look (deceased, no match, or more than one candidate):")
    for r in attention:
        print(f"  {r['field']:<9} #{r['option']:<2} {r['name']:<28} {r['status']:<45} {r['qid']} {r['label']} | "
              f"{r['description'][:60]} | b.{r['born']} d.{r['died']} | {r.get('others', '')[:160]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
