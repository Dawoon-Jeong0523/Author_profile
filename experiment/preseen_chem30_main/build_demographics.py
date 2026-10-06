#!/usr/bin/env python3
"""build_demographics.py: the reference note of the "cards as the main evidence with demographic information" arm.

    python build_demographics.py      # -> instruction_demo/00_6_demographics.md

Chemistry laureates 2000-2025 from ../../Data/prizeatlas/prizeatlas_nobel_laureates.csv (gender = csv_sex, birth country,
citizenship, country of the affiliation at the prize; PrizeAtlas country names are Spanish and are translated here). The
area of chemistry of each prize is Claude's grouping of the official motivation (AREA below). The 2026 Physics and
Medicine laureates are not in PrizeAtlas yet and are written by hand from the announcements.
"""
from collections import Counter
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PA = HERE.parents[1] / "Data" / "prizeatlas" / "prizeatlas_nobel_laureates.csv"
EN = {"Estados Unidos": "United States", "Japón": "Japan", "Suiza": "Switzerland", "Nueva Zelanda": "New Zealand",
      "Hungría": "Hungary", "Bélgica": "Belgium", "Francia": "France", "Alemania": "Germany", "Sudáfrica": "South Africa",
      "Reino Unido": "United Kingdom", "Rumania": "Romania", "Turquía": "Turkey", "Chipre del Norte": "Northern Cyprus",
      "Suecia": "Sweden", "Países Bajos": "Netherlands", "Dinamarca": "Denmark", "Rusia": "Russia", "Túnez": "Tunisia",
      "Jordán": "Jordan", "Arabia Saudita": "Saudi Arabia", "Israel": "Israel", "India": "India", "China": "China",
      "Austria": "Austria", "Australia": "Australia"}
AREA = {  # Claude's grouping of each motivation into an area of chemistry
    2000: "materials (conducting polymers)", 2001: "synthesis and catalysis (asymmetric catalysis)",
    2002: "analytical and structural biochemistry (mass spectrometry, NMR)", 2003: "biochemistry and structural biology (membrane channels)",
    2004: "biochemistry (ubiquitin-mediated protein degradation)", 2005: "synthesis and catalysis (olefin metathesis)",
    2006: "biochemistry and structural biology (eukaryotic transcription)", 2007: "physical chemistry (surface chemistry)",
    2008: "chemical biology (green fluorescent protein)", 2009: "biochemistry and structural biology (ribosome)",
    2010: "synthesis and catalysis (palladium cross-coupling)", 2011: "materials (quasicrystals)",
    2012: "biochemistry and structural biology (G-protein-coupled receptors)", 2013: "theory and computation (multiscale models)",
    2014: "physical and analytical chemistry (super-resolution fluorescence microscopy)", 2015: "biochemistry (DNA repair)",
    2016: "synthesis and supramolecular chemistry (molecular machines)", 2017: "biochemistry and structural biology (cryo-electron microscopy)",
    2018: "chemical biology (directed evolution, phage display)", 2019: "materials and energy (lithium-ion batteries)",
    2020: "biochemistry and chemical biology (CRISPR-Cas9 genome editing)", 2021: "synthesis and catalysis (asymmetric organocatalysis)",
    2022: "synthesis and chemical biology (click and bioorthogonal chemistry)", 2023: "materials and nanoscience (quantum dots)",
    2024: "theory, computation and biochemistry (protein design, structure prediction)", 2025: "materials (metal-organic frameworks)"}
GROUP = {"biochemistry, chemical biology and structural biology": [2002, 2003, 2004, 2006, 2008, 2009, 2012, 2015, 2017, 2018, 2020],
         "synthesis and catalysis": [2001, 2005, 2010, 2016, 2021, 2022], "materials": [2000, 2011, 2019, 2023, 2025],
         "physical, analytical and theoretical chemistry": [2007, 2013, 2014, 2024]}


def en(s, sep=" and "):
    return sep.join(EN.get(x.strip(), x.strip()) for x in str(s).split(";") if x.strip() and x.strip() != "nan")


def main():
    d = pd.read_csv(PA)
    c = d[(d.category_en == "Chemistry") & d.year.between(2000, 2025)].sort_values(["year", "name"])
    c = c.assign(aff=c.affiliation_place.astype(str).str.split(",").str[-1].str.strip().map(lambda x: EN.get(x, x)))
    lines = ["# Reference: demographics of the Chemistry laureates of 2000-2025 and of the 2026 Physics and Medicine laureates", "",
             "Source: PrizeAtlas laureate records for gender, country of birth, citizenship and the country of the affiliation "
             "at the time of the prize. The area of chemistry is a grouping of each official motivation into four broad areas, "
             "made for this note.", "",
             "| Year | Area of chemistry | Laureates |", "|---|---|---|"]
    for y, g in c.groupby("year"):
        ppl = "; ".join(f"{r.name} ({r.csv_sex.lower()}, born in {en(r.birth_country)}, citizen of {en(r.citizenship)}, "
                        f"working in {r.aff})" for r in g.itertuples())
        lines.append(f"| {y} | {AREA[y]} | {ppl} |")
    people = c.drop_duplicates("name")
    sex = Counter(people.csv_sex)
    aff = Counter(c.aff)
    women = ", ".join(f"{r.name} ({r.year})" for r in c[c.csv_sex == "Female"].itertuples())
    moved = int(sum(en(r.birth_country) != r.aff for r in c.itertuples()))
    assert sorted(y for v in GROUP.values() for y in v) == list(range(2000, 2026))
    lines += ["", "Summary of the 26 prizes (68 awards to 67 people; K. Barry Sharpless was awarded twice):",
              f"- Gender: {sex.get('Male', 0)} men and {sex.get('Female', 0)} women ({women}); no woman before 2009.",
              "- Country of the affiliation at the prize (awards): " + ", ".join(f"{k} {v}" for k, v in aff.most_common()) + ".",
              f"- {moved} of the 68 awards went to a laureate working outside the country of birth.",
              f"- Median age at the prize: {int(c.age_at_prize.median())} (range {int(c.age_at_prize.min())}-{int(c.age_at_prize.max())}).",
              "- Area of chemistry (prizes): " + ", ".join(f"{k} {len(v)}" for k, v in GROUP.items())
              + ". The last six prizes: CRISPR genome editing (2020), organocatalysis (2021), click and bioorthogonal chemistry "
                "(2022), quantum dots (2023), protein design and structure prediction (2024), metal-organic frameworks (2025).",
              "", "2026 so far:",
              "- Physiology or Medicine (5 October): Karl Deisseroth (male, United States, working at Stanford University, United "
              "States), Peter Hegemann (male, Germany, working at Humboldt University of Berlin, Germany) and Georg Nagel (male, "
              "Germany, working at the University of Wurzburg, Germany), for light-gated ion channels and optogenetics.",
              "- Physics (6 October): Francis Halzen alone (male, born in Belgium, working at the University of Wisconsin-Madison, "
              "United States), for the IceCube Neutrino Observatory and high-energy astrophysical neutrinos.", ""]
    out = HERE / "instruction_demo" / "00_6_demographics.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out.relative_to(HERE)}: {len(c)} awards; {sum(sex.values())} people; {len(lines)} lines")


if __name__ == "__main__":
    main()
