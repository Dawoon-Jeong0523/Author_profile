# Step 2: the fields of the prize, 1969–2025

Which areas of economics the prize has gone to, in the JEL classification
([`../data/classificationTree.xml`](../data/classificationTree.xml): 20 letters, 139 level-2 and 856 level-3 codes),
as the basis for the field options of the 2026 forecast. The analysis notebook
[`prize_history.ipynb`](prize_history.ipynb) also covers the laureates (counts, sharing, affiliations), the field
sequence in award order, gender and age.

## Design

A **work** is one motivation group of a prize year: the 57 prizes, 7 of them divided between two works, give 64
works. Each of the three models of step 1 gives every work JEL codes from its own knowledge (no web search); the
notebook builds the consensus.

```
../data/econ_prizes_laureates.csv ─► classify_jel.py: claude-opus-5-5 ─┐
  (year, laureates and shares,        gpt-5.5-2026-04-23  ─┼─► jel_by_model.csv ─► prize_history.ipynb: consensus,
   official motivation)               gemini-3.1-pro-preview┘    (192 rows)          fields, sequence, gender, age
../data/classificationTree.xml ─► the JEL list in the prompt; every returned code checked against the tree
```

| Stage | Calls | Prompt | Returns |
|---|---|---|---|
| code | 4 batches of consecutive years × 3 models; no tools; JSON schema | [`prompts/jel_system.md`](prompts/jel_system.md) (rules and the full JEL list), [`prompts/jel_user.md`](prompts/jel_user.md) | per work: **primary** level-3 code (the core of the recognized contribution), up to 3 **secondary** codes, kind of contribution (theory, theory and empirical, empirical, methods), whether the model knows the prize beyond the motivation, a one-sentence rationale |

Rules in the prompt: code the contribution the prize recognized, not the laureates' careers; level-3 codes from the
list only; a tool that others apply (econometric, experimental, mathematical) goes under C with its first field as a
secondary code. The works of a divided prize are always in the same batch.

**Checks in code.** The JSON schema; every work id of the batch exactly once; every code a level-3 code of the tree,
at most three secondary codes, distinct and not the primary. An invalid answer is asked once more with the problems
listed. All 12 answers were valid at the first attempt (9 October 2026, $1.52).

**Consensus** (notebook, section 3), level by level (letter, then level 2 within it, then level 3 within that): the
code that at least two of the three primary codes share; otherwise the highest score (2 per primary, 1 per model that
lists it as secondary); a remaining tie goes to the first model in the order A, O, G. All three models agree on the
letter for 58 of the 64 works and on the level-2 field for 51; no work lacks a two-model majority at these two levels.

## Results (9 October 2026)

| Letter | Field | Works | Prizes (share-weighted) | Years |
|---|---|---|---|---|
| D | Microeconomics | 18 | 16.5 | 1972 … 2020 |
| C | Mathematical and Quantitative Methods | 16 | 13 | 1969 … 2021 |
| E | Macroeconomics and Monetary Economics | 8 | 8 | 1974 … 2006 |
| O | Development, Innovation, Technological Change, and Growth | 7 | 6 | 1971, 1979, 1987, 2018, 2019, 2024, 2025 |
| G | Financial Economics | 4 | 4 | 1990, 1997, 2013, 2022 |
| F | International Economics | 3 | 3 | 1977, 1999, 2008 |
| J | Labor and Demographic Economics | 3 | 2.5 | 2010, 2021, 2023 |
| L | Industrial Organization | 2 | 2 | 1982, 2014 |
| N | Economic History | 2 | 1.5 | 1993, 2025 |
| Q | Agricultural, Natural Resource and Environmental Economics | 1 | 0.5 | 2018 |

Never the main field: A, B, H, I, K, M, P, R, Y, Z. The 35 awarded level-2 fields, with every award, are in
[`results/awarded_jel_fields.md`](results/awarded_jel_fields.md). The notebook's section 10 summarizes the other
results (sequence, shifts, gender, age).

## Commands

```bash
cd "/project/jevans/Dawoon/Nobel Prize/Econ/02_fields"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY classify_jel.py prompt --batch 1     # the exact prompt (free)
$PY classify_jel.py estimate             # cost (logged calls, else assumptions)
$PY classify_jel.py run                  # every batch x model (paid; valid answers are kept unless --force)
$PY classify_jel.py export && $PY classify_jel.py status
$PY -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=curvature prize_history.ipynb
```

## Outputs

| File | Content |
|---|---|
| `jel_by_model.csv` | one row per work × model: primary, secondary codes, kind of contribution, knows_prize, rationale |
| `prize_history.ipynb` | the analysis, executed |
| `results/prize_works_jel.csv` | one row per work: laureates, share, motivation, consensus code at three levels, agreement, each model's codes |
| `results/awarded_jel_fields.csv`, `.md` | every level-2 field that is the consensus field of a work, with years and laureates |
| `results/field_gaps_letter.csv`, `field_gaps_level2.csv` | award years, gaps, years since the last award (to 2026) per field |
| `results/*.svg`, `*.png` | the notebook's figures |
| `runs/<provider>/batch_<k>.json`, `logs/calls.jsonl` | the full answers and the call log (not versioned) |

## Known limits

- The codes come from the models' knowledge of the prize works, not from the committee's scientific backgrounds; a
  work that spans fields gets one main code (the secondary codes and the "any mention" count in section 4 show the
  rest). Six works divide the models at the letter level: 1984 Stone (E/C), 1997 Merton–Scholes (G/C), 2009 Ostrom
  (D/Q), 2010 Diamond–Mortensen–Pissarides (J/D), 2019 Banerjee–Duflo–Kremer (O/C), 2025 Mokyr (N/O).
- The API record of Oliver E. Williamson has no death date (he died on 21 May 2020); the notebook adds it, and the
  crawled files stay as fetched.
