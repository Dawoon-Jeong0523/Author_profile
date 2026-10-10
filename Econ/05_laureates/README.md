# Step 5: reference facts from the laureate record for the people stage

Before the candidates per field are discussed, the record of the 99 laureates of 1969–2025 is examined in
[`laureate_history.ipynb`](laureate_history.ipynb) for regularities that should inform the people stage (candidate
pools weighted by the Preseen field forecast of step 4b, then a forecast of the laureate set). Each section ends with
an English paragraph written to `prompt/<section>.md`, so the facts can be attached to the people question as a
context note. Sections are added as the questions come up.

## Inputs

| File | Content |
|---|---|
| `../data/econ_prizes_laureates.csv` | every laureate: share, motivation, affiliation, gender, birth and death dates, age at the award |
| `../04_field_forecast/results/prize_works_fields14.csv` | the 64 prize works with their field (14 fields of Dolton and Tol) and kind of contribution |

**Data correction.** The Nobel Prize API dates the 2022 prize (Bernanke, Diamond, Dybvig) 2011-10-10, so the crawl's
`age_at_award` is eleven years too low for them (57, 57, 56). The notebook recomputes every age from the birth date
to the announcement in the prize year (68, 68, 67) and checks the other 96 against the API; four laureates have a
birth year only (mid-year, approximate). The same correction was applied to `../02_fields/prize_history.ipynb` on
10 October (its "finance youngest, median 57" was an artefact; the finance median is 67).

## Section 1: age at the award (10 October 2026)

- 99 laureates: median 67 (bootstrap 95 % 64–69), mean 67.3, sd 8.3, middle 80 % 57–78; under 55: 4 (Duflo 47,
  Arrow 51, Merton 53, Kremer 55); 80 and over: 6 (Hurwicz 90, Shapley 89, Schelling 84, Wilson 83, Vickrey 82, Coase 81).
- One peak: Gaussian mixture BIC prefers one component, skewness +0.34, Shapiro p = 0.48; mode of the density 65
  (bootstrap 62–69). The award rate among eventual laureates (share of the not-yet-awarded awarded at each age) passes
  5 % at 61 and 10 % at 68 and peaks around 77 among ages with ten or more still unawarded; it rises mechanically as
  the pool empties. Dolton and Tol's candidate-pool logit peaks at 70–71 [P]. Reading: a broad plateau 60–77, not a
  sharp optimum.
- No trend over time (+0.13 years per decade, p = 0.80); 1969–1997 median 66 vs 1998–2025 67 (p = 0.95).
- By field (medians): Information 61, Growth 64, Equilibrium 65, Econometrics 65, Development 66, Macro 66, Finance
  67, Trade 69, Labour 70, Games 74 (Kruskal–Wallis p = 0.37 across fields with 3+ laureates). Three-way prizes 64,
  two-way 69, solo 67 (p = 0.07).
- Co-laureates of a work: age gap median 9 years; 15+ years in 4 of 26 shared works (Hurwicz–Maskin–Myerson 34,
  Roth–Shapley 29, Mirrlees–Vickrey 22, Hicks–Arrow 17).
- Survival constraint: 51 deceased laureates died at a median 86, 18 years after the prize; 7 within five years; of the
  20 awarded at 75 or older, 13 have died after a median 11 years. 48 alive (median 79; 24 aged 80+).

Outputs: `results/age_*.{png,svg}`, `results/colaureate_age_gap.*`, `results/age_at_award_summary.csv`,
`results/laureate_ages.csv`, `results/age_award_rate.csv`, `prompt/01_age_at_award.md`.

## Commands

```bash
cd "/project/jevans/Dawoon/Nobel Prize/Econ/05_laureates"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=curvature laureate_history.ipynb   # ~1 min
```
