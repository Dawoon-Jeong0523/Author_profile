# LOG — "cards as main evidence" follow-up (2026 Nobel Prizes)

One entry per step: time (CDT) · field · command · outcome · decision. Key values never appear here.

## 2026-10-02

- **(10-01 evening, chat)** · all · user asked for a follow-up in which Preseen is told to use the cards as the main
  evidence, not as a secondary cross-check: control 1 + treat 1 per field, otherwise as `../preseen/`, in a separate
  experiment folder, all three fields · proposed the instruction note (pre-empting the forecaster's own stated reasons
  for discounting the cards), `assume_true` for the instruction, cards unchanged with `consider`.
- **(chat)** · all · user asked whether the cards cover every candidate Preseen considers · answer: they cover every
  person named in the 12 options (30 / 34 / 34 cards), not the other people who could share a listed discovery
  (e.g. Drucker for GLP-1, mentioned 80 times in the earlier Medicine runs; Rose, deceased, 68 times in Physics) nor
  the "Other" contenders Preseen names (cGAS–STING, OCT, SAMs, base editing) · user: add the scope sentence, run the
  experiment, make the results into a dashboard ("Dashboard2") = approval of the spending (6 questions, 104 notes, 6 runs).
- **09:02** · all · `../preseen/check_keys.py --no-models` · PRESEEN_API_KEY set, HTTP 200 (the other three also 200).
- **09:02** · all · new folder `experiment/preseen_cards_main/`: copies of `nobel_preseen_exp.py`,
  `questions/<field>.json`, `cards/` (the three field folders and the laureate reference; `_titles_cache.json` left out)
  · `cmp` / `diff -r` against `../preseen/`: identical (31 / 35 / 35 notes) · `instruction/00_instruction.md` written
  (scope sentence included); `SPEC.md`; `.gitignore` += `experiment/preseen_cards_main/preseen_exp/`.
- **09:03** · all · `run_field.sh <field> <tag>` in tmux (`tmux -L preseen2`, sessions `medicine`, `physics`,
  `chemistry`; log `preseen_exp/<field>/run.log`): create → add-context instruction (`assume_true`) → add-context cards
  (`consider`) → `run --arms control treat --reps 1` → `poll --wait` → `table` · questions created (definitions
  identical, private): medicine control `f3229999-5ab1-45d3-a9ce-f8fc5ec3f818`, treat `15972ea3-7e42-4e79-8369-2cb711ee415d`;
  physics control `802cdba2-e434-49a0-b04e-7299c09b1d3a`, treat `eb5c5a2d-65a7-4be0-a9be-4afdec16aa86`; chemistry control
  `ab1b3d82-a55f-4ca6-91d4-ab151abcc0a7`, treat `3251874b-9c0f-4afd-ae23-13435bed523c`; "treat: context ready (1 notes,
  treatment=assume_true)" in all three.
- **09:04–09:05** · all · context and runs (same tmux sessions) · Preseen returned HTTP 429 (rate_limit_error) a few
  times; the client waited and retried with the same Idempotency-Key · "treat: context ready (31 / 35 / 35 notes,
  treatment=consider)"; submitted (the order treat → control is the same in all three fields: same seed and an empty
  run list): medicine treat `6e7bff60-d8f2-44ba-865e-0ff8048104ca`, control `c8ed7572-6886-4ca3-8408-0f68cee4abf7`;
  physics treat `29ddfb0a-8473-4bb4-b12d-9efa33fef7fe`, control `e106e32c-791b-4c1a-99b6-0ad9ef8d7390`; chemistry treat
  `415b5fc5-9613-43d7-b894-8966bd4cbceb`, control `d66c3826-880f-49fd-a131-a681ae125d46`; 6 runs active, polling.
- **09:06** · all · read-only `GET /questions/<id>/context/` (paginated) for the six questions · control: 0 notes;
  treat: 32 / 36 / 36 notes = 1 `assume_true` (the instruction) + 31 / 35 / 35 `consider`; no duplicate texts despite the
  429 retries · context exactly as designed.
- **09:06** · all · `analyze_main.py` written (arms control = 4 runs of 1 Oct + 1 of 2 Oct, cards = the 3 treat runs of
  1 Oct, main = the new treat run; noise = pairwise control spread as before, plus a single-run yardstick: each run's
  mean |run − control mean| with a control run left out of its own mean; card alignment from
  `../preseen/results/<field>/card_strength_vs_effect.csv`).
- **09:08** · all · `build_dashboard2.py` written (Dashboard2: reuses the CSS/JS/SVG helpers of `../preseen/build_dashboard.py`;
  fields without `results/<field>/summary.json` are shown as pending).
- **09:18** · all · new Claude Code session takes over (the previous one was suspended at about 09:17; no client process
  of it left except the three tmux polls) · re-read `SPEC.md`, `../preseen/SPEC.md`, this log · state: medicine treat
  synthesizing, the other five runs running subforecasts · dry build of `build_dashboard2.py` into the session scratchpad
  with no results: OK (all three fields pending) · waiting for the polls.
- **09:20–09:45** · (other task) · the user asked for an unrelated dashboard in the same session; the polls kept running in tmux.
- **≈09:40** · medicine · both runs completed and saved (`poll` EXIT=0, `runs.csv` 2 runs) · treat (main) `6e7bff60-…`,
  control `c8ed7572-…`.
- **09:44** · medicine · `$PY analyze_main.py field --field medicine` → `results/medicine/` · main run vs control mean
  4.67 pp per option (control runs vs the other four: 0.60–1.01 pp, mean 0.75; cards-as-cross-check runs 0.60–0.82);
  13 of 13 options outside the five-run control range; GLP-1 20.3 % → 3.0 %, orexin 12.1 % → 4.8 %, Other 31.0 % →
  40.0 %; named leaders optogenetics 7.9 %, Wnt 7.7 %; rank correlation with control −0.03; change vs the cards'
  impact comparison Spearman +0.64 (p = 0.03, n = 12; cross-check arm +0.51); the 2 Oct control run is 0.73 pp from
  the 1 Oct control mean (4 options outside the 1 Oct range). The write-up builds an explicit profile score (81
  weight specifications, 10 % uniform component) and states it accepts the premises "without a vintage or attribution
  penalty". Physics and Chemistry control runs still synthesizing.
- **≈09:45** · physics · both runs completed and saved · `analyze_main.py field --field physics`: main 3.20 pp per option
  from the control mean (control runs 0.52–1.15, mean 0.71; cross-check 0.36–1.19); 11 of 13 options outside the
  control range; optical lattice clocks 14.7 % → 4.5 %; quantum simulators 5.4 % → 13.4 % (new named leader); Other
  33.5 % → 38.0 %; rank correlation with control 0.67; change vs impact comparison +0.32 (cross-check +0.15).
- **09:46** · chemistry · both runs completed and saved · `analyze_main.py field --field chemistry`: main 2.86 pp
  (control 0.51–0.67, mean 0.59; cross-check 0.56–0.67); 9 of 13 outside; sequencing-by-synthesis 19.1 % → 5.5 %;
  OLEDs 3.7 % → 9.4 % (new named leader); Other 33.6 % → 38.0 %; rank correlation 0.52; change vs impact +0.34
  (cross-check +0.12). `analyze_main.py pooled` → `results/pooled.csv`.
- **09:50** · all · `results/<field>/reasoning_summary.md` (English, read from the main write-ups; model output treated as
  data) and `results/summary_ko.md` written · `build_dashboard2.py --fragment results/dashboard2_fragment.html` →
  `results/dashboard2.html` (447,627 bytes, all three fields) · fragment published as a private Artifact
  (https://claude.ai/artifact/CwmSWZ9yDDRjxaifcUCQjQ) · the tmux server `preseen2` had already exited with the run scripts.
  Left: log scores after the announcements (`analyze_main.py score --field <f> --option <n>`, then rebuild Dashboard2).
