# cards — profile cards rebuilt with the inventor linking of 2026-10-03

The same 98 profile cards as `../cards_v1/` (same people, template, file names and `00_definitions.md`), rebuilt after the
author-profile pipeline gained `np_common.link_inventors` (LINK_VERSION 1; see "Inventor linking" in the repository
README). Built as `cards_v2/` and renamed to `cards/` on 2026-10-03; the cards the 1–2 October Preseen runs used moved
unchanged to `../cards_v1/`, which `analyze.py`, `build_dashboard.py` and `../build_dashboard_all.py` read (the follow-up
folders keep their own copies of those cards).

## How it was built (2026-10-03)

1. Profiles re-run with the current `notebook/author_profile.ipynb`, overwriting their `output/<author id>/` folders,
   dashboards and records:
   - the 94 OpenAlex id sets of `people/<field>_identity.csv` (same calls and parameters as `submit_profiles.py`:
     the person's name as query, the chosen ids, year_max 2021, titles from the API; Slurm jobs 59955397–59955490);
   - the 199 physics / chemistry / medicine laureates of 2000–2025 behind the laureate reference (same environment as
     `jobs/prizeatlas_dashboards.sbatch`; array 59955357, `output/batch_relink_2026-10-03/`);
   - Geoffrey Hinton once more through `pipeline/profile_person.py "Geoffrey Hinton"` (job 59955959), so that
     `output/A5108093963/` again holds the README example with his OpenAlex fragment A5110248343, as before.
2. `$PY build_cards.py reference --out cards_v2` and `$PY build_cards.py cards --field <field> --out cards_v2`
   (`--out` is new; the default is `cards/`), then the folder renamed to `cards/`.

## What changed

Only the patent lines: the person's own US utility patents, the people who are both co-authors and co-inventors, and
the reference phrase of the own-patents line (the laureates' own patents changed too). Every other line and every
other column of `laureate_reference.csv` is identical. Per-card details: `CHANGES.md`.

## Known limits

- Linking evidence comes from the OpenAlex author record. Where OpenAlex merged a namesake into the record, that
  namesake's patents look linked: Michael V. Berry's card now shows 1 own patent (US 5,779,696, 1998, inventor
  "Michael J. Berry", Sunrise Technologies, co-inventor David R. Hennings, who co-authors one 1997 work in the record).
- 18 of the 199 reference laureates are missing from the reference, as in `../cards_v1/`: `build_cards.py reference` reads
  `output/<PrizeAtlas id>/`, and their profiles live under another id after the notebook's author id check (e.g.
  Doudna, Baker, Moerner, Feringa, Grubbs, Novoselov, Kajita). Listed in `laureate_reference_missing.json`.
- 28 cards are shorter than the 300–500 words of SPEC §9 (29 in `../cards_v1/`); the template is unchanged.
