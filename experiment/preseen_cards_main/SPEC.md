# SPEC — "cards as main evidence" follow-up to the Preseen context experiment (2026 Nobel Prizes)

Follow-up to `../preseen/` (its SPEC.md, hard rules and client invariants apply unless changed here). Every step is
recorded in `LOG.md`.

## Question

In `../preseen/` the profile cards, added with `treatment=consider`, moved the forecasts by less than the control
run-to-run spread, and the forecaster said it used them "as a secondary cross-check" (reasons it gave: percentiles
among past laureates are not calibrated selection probabilities; author attribution cannot be audited; the records end
in 2021; outside recognition is the better signal). Does the forecast move — and move the way the cards point — when
the forecaster is told to use the cards as the main evidence?

## Design (per field: medicine, physics, chemistry)

- Two new private questions with the definition of `../preseen/questions/<field>.json` (copied unchanged to
  `questions/`): `control` (no context) and `treat`.
- `treat` context, in this order:
  1. `instruction/00_instruction.md` with `treatment=assume_true` (the premise that the profiles are the main
     evidence; scope: the profiles cover only the named people, "Other" judged as otherwise; a premise note with
     `assume_true` was applied in `../preseen/checks/medicine_exclude_mojsov/`);
  2. the unchanged `../preseen/cards/<field>/` (copied to `cards/`): `00_definitions.md` first, then the cards in the
     client's seeded order (seed 2026), `treatment=consider` as before.
  The only difference from the earlier treat arm is the instruction note.
- One run per arm (`run --arms control treat --reps 1`, randomised order), `allow_incomplete_context=false`.
- Client: `nobel_preseen_exp.py`, an unchanged copy. Tags `nobel26-med-main`, `nobel26-phys-main`, `nobel26-chem-main`;
  EXP_DIR `preseen_exp/<field>` (git-ignored).
- Deadlines as in `../preseen/SPEC.md` §2 (Medicine Sun 4 Oct 23:00, Physics Mon 5 Oct 23:00, Chemistry Tue 6 Oct
  23:00 CDT).

Approved on 2026-10-02:
6 questions, 3 instruction notes + 101 card notes, 6 runs.

## Analysis (`analyze_main.py` → `results/`; dashboard `build_dashboard2.py` → `results/dashboard2.html`)

Baselines from `../preseen/`: control runs (4 per field) and treat runs (cards, `consider`; 3 per field).

- Noise band: control run-to-run spread over all control runs (earlier 4 + new 1); the new control run vs the
  earlier control mean (drift between 1 and 2 October).
- Effect of the instruction: new treat − control mean per option, against the noise band and the control range;
  new treat − earlier treat mean; leader, "Other", entropy, rank correlation.
- Direction: Spearman correlation of the per-option change with the cards' laureate comparison (mean share of past
  laureates the option's people exceed on impact median, and on citing inventions), as in `../preseen/analyze.py`.
- Uptake: the write-ups' statements on how the profiles were used (quotes), term counts (inflated by the
  instruction's request to name the profile evidence; not compared as an effect).
- One run per arm: descriptive, no significance test.
