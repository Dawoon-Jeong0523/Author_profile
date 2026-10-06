# LOG: "Cards as the main evidence" on three 2026 Chemistry 30-option lists

One entry per step: time (CDT) · list · command · outcome · decision. Key values and Preseen ids never appear here.

## 2026-10-06

- **12:40** · all · user request: submit "Cards as the main evidence" forecasts for the three 30-option lists (v1, v2 of
  ../convergence_2026_v2, and Preseen's own list in ../preseen_generated30), with the Medicine and Physics 2026 outcomes
  in the context. Design: the v2 main-evidence notes of ../preseen_30_main_v2 adapted to chemistry (00_1 instruction:
  Physics references -> Chemistry, both 2026 outcomes, chemistry reference values for patents; 00_2 = the standard
  card definitions, since age-25 cards and option blocks exist only for physics; 00_3 chemistry timing base rate,
  approximate, counted by Claude from the motivations; 00_4 Medicine 2026 unchanged; 00_5 Physics 2026 new), all
  assume_true; person cards (standard format) of each list, consider; one main rep per list; client copied unchanged.
- **12:55** · v1, v2 · questions/<list>.json from the saved lists (same title/description/resolution as the physics
  30-option question, Chemistry wording); cards/v1 (63), cards/v2 (51) from ../convergence_2026_v2/cards/<v>/chemistry.
- **12:55** · preseen · 27 people without profiles: identities in ../convergence_2026_v2/people/chemistry_* (hand
  choices for Torchilin, Tomalia, Sarpong, Dennis Lo; Preseen's "Richard Sarpong" corrected to Richmond Sarpong in
  ../preseen_generated30/chemistry/options.json), profile jobs 60175294-60175364 running.
- **13:20** · preseen · 27 profile jobs COMPLETED; cards_pipeline_v2.py cards + check: 423 cards, 0 problems (v1/v2 chemistry
  cards identical to the submitted ones); cards/preseen (55) copied; run_list.sh preseen nobel26-chem-30-pre-main launched
  (tmux -L chem30, session pre). Card caveats: pre-age-25 works on some new records (Collins 1945, Jacobsen 1950, Stubbe
  1953); Tao Zhang's 50 own patents may include namesakes; Mark Levin 22 works.
- **14:25** · all · v1 done 13:59 (75 min), Preseen list 14:12, v2 14:22 (98 min); compare.py -> results/compare.csv,
  compare.md, write_up_<list>.md. Leaders: v1/v2 proteomics 9.1/8.7 %, dye-sensitized cells 8.9/8.5 %, nanopores
  6.5/7.9 %; Preseen list flexible electronics 7.7 %, gene circuits 7.3 %, Norskov 7.1 %. v1 vs v2 Spearman 0.95 (mean
  |diff| 0.51 pp; options with unchanged people moved up to 1.4 pp = single-run noise); lineup effect largest for OLEDs
  (Thompson dropped: 3.0 -> 0.8 %); v2's Gray-alone option got no discovery evidence because the standard card shows
  his most-cited works. Preseen list: 47 % on its own 13 discoveries; v1 puts 55 % on discoveries Preseen did not list.
