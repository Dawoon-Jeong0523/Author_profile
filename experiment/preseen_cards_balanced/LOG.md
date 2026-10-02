# LOG — "cards as one of the main sources" follow-up (2026 Nobel Prizes)

One entry per step: time (CDT) · field · command · outcome · decision. Key values never appear here.

## 2026-10-02
- 09:53 · all · folder created: `nobel_preseen_exp.py`, `questions/`, `cards/` copied unchanged from `../preseen_cards_main/` (diff against `../preseen/`: identical, client byte-identical) · SPEC.md written.
- 09:54 · all · `instruction/00_instruction.md` written ("one of the main sources", other evidence used actively) · decision: wording per SPEC Design.
- 09:54 · medicine / physics / chemistry · `run_field.sh <field> nobel26-{med,phys,chem}-bal` launched in parallel (tmux server `preseen3`) · questions created, context ready (1 note assume_true + 31 / 35 / 35 cards consider), treat rep01 submitted in each field; transient 429s on context upload retried by the client.
- 10:00 · all · the session that launched the runs stopped; a new session resumed (runs untouched, polling continues in tmux).
- 10:16 · all · runs in `synthesizing` · `../preseen_cards_main/analyze_main.py` and `build_dashboard2.py` extended with the arm `balanced` (read from this folder; outputs without it unchanged byte for byte).
- 10:28 · medicine / physics / chemistry · all three treat rep01 runs completed and saved (`poll` EXIT=0, `runs.csv` 1 run each) · tmux sessions ended.
- 10:30 · all · `../preseen_cards_main/analyze_main.py field --field <f>` ×3 + `pooled` · balanced run vs control mean 2.13 / 2.28 / 1.94 pp per option (2.8× / 3.2× / 3.3× a control run's distance; main-evidence run 4.67 / 3.20 / 2.86 pp); 9 / 9 / 9 of 13 options outside the control range; position on the cross-check (0) → main (1) line 0.42 / 0.50 / 0.63; leaders orexin 11.7 % (GLP-1 20.3 → 11.0 %), quantum simulation 12.8 % (clocks 14.7 → 9.3 %), sequencing-by-synthesis 10.0 % (from 19.0 %); "Other" 34.0 / 30.0 / 37.5 %.
- 10:35 · all · `results/<field>/reasoning_summary_balanced.md` written in ../preseen_cards_main from the write-ups · `build_dashboard2.py --fragment results/dashboard2_fragment.html` (4 arms) · copied to the Author_profile Pages root as `preseen_dashboard2.html`.
