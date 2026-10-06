# LOG: control vs cards as the main evidence, 30 options without "Other" (2026 Physics)

One entry per step: time (CDT) · field · command · outcome · decision. Key values and Preseen ids never appear here.

## 2026-10-05

- **17:15** · physics · Kurahashi Neilson and Ken'ichi Nomoto profiles run again with NP_NAME_SEARCH=off (jobs 60115070, 60115071) to remove namesakes' patents.
- **17:18** · physics · folder created: question with the 30 options of ../convergence_2026 (no Other, conditional, rule for overlapping options), instruction note as ../preseen_main_no_other, client copied unchanged; cards copied once the two profiles finish.
- **17:18** · physics · both profiles COMPLETED; cards_pipeline.py cards + check: 135 cards, 0 problems; Kurahashi Neilson 191 research works 2003-2021, 0 own patents; Ken'ichi Nomoto 666 works 1967-2021, 0 own patents.
- **17:20** · physics · cards/physics copied (00_definitions.md + 72 cards); run_field.sh physics nobel26-phys-30: control and treat questions created (identical, private, no watch), instruction note added (assume_true), cards being added (consider).
- **17:20** · physics · the driving session died during the card upload (last line "context ready (1 notes)"); no process left, 0 runs submitted.
- **17:46** · physics · resumed by re-running run_field.sh (same tag; idempotent — questions reported "already exists", notes deduplicated server-side): all 73 card notes added (one 429, retried), context ready (73 notes, consider), then both runs submitted at 17:47 on the user's instruction to submit with the pre-update cards (log: resume_run_field.out).
- **18:17** · physics · both runs completed (control 29 min, treat 30 min, 4/4 subforecasts each); runs.csv written. Treat (cards as main evidence) is much flatter and reordered vs control: leaders treat = OLED 7.9 %, quantum simulators 7.8 %, quantum error correction 7.0 %, spin qubits 5.8 %; control = negative-index metamaterials 13.1 %, topological insulators 9.1 %. Spearman(control, treat) 0.17, mean |diff| 2.7 pp — the cards move the 30-option forecast far more than they moved the 12-option one (0.97 there).
