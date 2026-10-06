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
- **14:48** · v2 · user: "submit a control forecast with the v2 list" -> run_control.sh v2 nobel26-chem-30-v2-main: a
  "control" arm in the v2 experiment (same question, no notes at all: no instruction, no Medicine/Physics outcomes, no
  cards), one rep (log run_v2_control.out, tmux -L chem30 session v2ctl); question definitions identical across arms.
- **15:22** · v2 · control rep01 completed (34 min, 4/4 subforecasts); compare.py now has a v2-control column and
  write_up_v2_control.md. Control: sequencing-by-synthesis 17.3 %, perovskites 7.9, controlled radical polymerization
  6.2; vs v2 main Spearman 0.14 (mean |diff| 2.66 pp). Main vs control: SBS -14.8 pp; dye-sensitized cells +7.9,
  proteomics +5.9, nanopores +5.4, DFT +4.1, nuclear receptors +3.9; Gray-alone electron transfer -3.7.
- **16:30** · all · user: add the patents tied to the discovery to the chemistry cards and drop "technological translation
  is minor" from the main-evidence prompt. ../convergence_2026_v2/patent_section.py (pools / merge / apply; 6 LLM agents
  chose up to 3 patents per person from all US utility patents granted up to 2021; patents_tied_chemistry.yaml, 0
  problems) put a "Patents tied to the discovery" section on all 338 chemistry cards (standard and age-25) and its
  definition into every 00_definitions.md; cards/<list>/ here refreshed. instruction/00_1: translation no longer
  "minor", patents tied to the discovery count as discovery-relevant works; 00_2 = the new definitions. The notes of
  the 6 October runs are kept in instruction_used_2026-10-06/ (not uploaded by any script).
- **16:45** · all · user: new arm "cards as the main evidence with demographic information". instruction_demo/:
  00_6_demographics.md (build_demographics.py: gender, birth country, citizenship, country of work of the 2000-2025
  Chemistry laureates from PrizeAtlas, area of chemistry per prize grouped by Claude, the 2026 Physics and Medicine
  laureates) and 00_7_demographic_instruction.md (weigh the demographic distribution with an explicit factor 0.5-2 per
  option, reported apart). run_arm.sh <list> <main2|demo> <tag> adds an updated main arm (main2) or the demographic arm
  (main2 + instruction_demo/). Prepared, not submitted.
