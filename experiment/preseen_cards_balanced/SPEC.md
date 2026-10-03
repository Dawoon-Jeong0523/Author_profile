# SPEC — "cards as one of the main sources" follow-up (2026 Nobel Prizes)

Second follow-up to `../preseen/` (its SPEC.md, hard rules and client invariants apply unless changed here); sibling of
`../preseen_cards_main/`. Every step is recorded in `LOG.md`.

## Question

`../preseen_cards_main/` told the forecaster that the profile cards are *the main* evidence and that other information is
only a secondary adjustment; the award-backed favourites collapsed and the forecasts followed the cards. Where does the
forecast land when the cards are *one of the main* sources, weighted comparably with prizes, news, predictions and the
prize's history, which the forecaster is asked to use actively?

## Design (per field: medicine, physics, chemistry)

- One new private question per field, definition of `../preseen/questions/<field>.json` (copied unchanged), arm `treat`.
- Context, in this order: `instruction/00_instruction.md` with `treatment=assume_true`; then the unchanged cards
  (`cards/<field>/`, copied from `../preseen/cards/`), `treatment=consider`, the client's seeded order (seed 2026).
  Differences from `../preseen_cards_main/instruction/00_instruction.md`: "one of the main sources … alongside the other
  evidence" instead of "the main evidence"; profiles get weight "comparable to that of your other main evidence"; other
  information is to be used "actively" (instead of "only as a secondary adjustment"); for "Other" and unnamed
  contributors the forecaster relies on the other evidence; the write-up names profile and other evidence. The
  "take the figures as given" sentence is unchanged.
- One run per field (`run --arms treat --reps 1`), `allow_incomplete_context=false`; no new control run (baseline: the
  five control runs of 1–2 October).
- Client: `nobel_preseen_exp.py`, an unchanged copy. Tags `nobel26-med-bal`, `nobel26-phys-bal`, `nobel26-chem-bal`;
  EXP_DIR `preseen_exp/<field>` (git-ignored).

Requested by the user on 2026-10-02 ("treat을 분야별 한개씩 다시 제출 … card 정보를 main 정보 중 하나로 활용 … 다른 정보도
활발히 활용"): 3 questions, 3 instruction notes + 101 card notes, 3 runs.

## Analysis

`../preseen_cards_main/analyze_main.py` reads this folder as the arm `balanced` (control, cards = consider, balanced,
main) and `../preseen_cards_main/build_dashboard2.py` shows it in Dashboard2: distance from the control mean against the
control runs, options outside the control range, leader and "Other", rank correlation with control, the change against
the cards' laureate comparison, where `balanced` sits between the cross-check and main arms, and the write-ups.
One run per arm: descriptive, no significance test.
