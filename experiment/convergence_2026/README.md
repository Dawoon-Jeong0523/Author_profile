# 30 options per field: committee + convergence signals (2026 physics and chemistry)

`build_options.py` makes 30 discovery + people options for physics and for chemistry from two sources:

- the virtual committee of `../preseen/` (LLM ballots, merged and Borda-scored exactly as in `committee.py`), and
- `Data/convergence_2026.csv`, person-level evidence: Clarivate 2026, Kalshi markets, recent major prizes,
  milestones, Swedish proximity, Nobel Symposium dossiers, web sources, insider posts.

Nothing in `../preseen/` is changed; the committee's 12-option lists (`committee/<field>/candidates.json`) stay as
they are, and all 12 of them are among the 30 here.

```
LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib /project/jevans/Dawoon/env/Curvature/bin/python build_options.py
```

## How the two are combined

- Each evidence family is one approval vote for every person it names (Kalshi: the person's price divided by the
  highest price in the field). Only rows with status `alive` are used. The approval points are scaled so that their
  total equals the committee's total points (`--weight 1`).
- A person the committee named takes the points into that option (first initial + surname, as in `committee.py`;
  someone in two options splits them by committee weight). Anyone else joins an option through `decisions.yaml`, a
  shared milestone, a group in `decisions.yaml`, or forms an option alone.
- An option the committee did not name needs at least two evidence families, so a single web or symposium mention
  does not make an option.
- Score = committee points + the convergence points of the shown people (at most three living, ranked by committee
  weight + convergence points). Ties: committee points, number of evidence items, committee rank.

## Files

| File | What |
|---|---|
| `decisions.yaml` | hand decisions (attachments, new groups, discovery wording, notes), each with its reason; drafted by Claude |
| `results/options_<field>.json` | the 30 options with scores, people, per-family points and flags |
| `results/options_<field>.csv` | the same, one row per option |
| `results/review_<field>.md` | table, per-option detail, sensitivity to `--weight` (0.5 and 2), name matches, notes |

The discovery text of an option the committee did not name is Claude's wording in `decisions.yaml`; where a prize
citation exists (2025 Wolf, 2024 Wolf, 2025 and 2026 Shaw) it follows that citation. Check those texts before using
them in a question.
