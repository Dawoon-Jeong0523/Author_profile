# Step 4a: Preseen context notes for the field forecast

The prompts that the Preseen question on the **field** of the 2026 Sveriges Riksbank Prize in Economic Sciences
receives as context notes, built by [`field_context_prompts.ipynb`](field_context_prompts.ipynb) from the data the
earlier steps completed (nothing is fetched; the notebook uploads nothing). Each note cell of the notebook prints the
full text of one note and writes it to `context/<name>.md`; [`run_field.sh`](run_field.sh) creates the question and
attaches the notes (one API note per file, in name order) with the client `nobel_preseen_exp.py` (a copy of the one
in `../../experiment/preseen_chem30_main/`).

## Design

The notes implement the design document *Forecasting the field of the 2026 prize: a design that applies field
rotation strongly* (9 October 2026, written in Korean; rendered in English in the notes). Its rules, in short:
(1) field rotation is the primary prior; (2) one classification for the record and for this year's options;
(3) operational weights from the record (awarded in 2024–2025: large penalty; 2021–2023: penalty; long wait: bonus);
(4) the 2023–2025 awards reflected exactly; (5) check that a waiting field has enough mature, unawarded work;
(6) societal context is auxiliary; (7) committee expertise is a limited adjustment; (8) the paper's numbers are not
this year's probabilities; (9) a fixed output format. Evidence tags: **[P]** Dolton and Tol (2026,
arXiv:2603.20767v1), **[M]** the project meeting of 9 October 2026, **[D]** a design choice, **[O]** official sources,
**[S]** (added here) a number computed from this project's data.

**Classification.** The design keeps a project classification when one exists; step 2 coded the record in JEL, so the
14 JEL-based fields of Dolton and Tol (Table B.7) are the options and every prize work is mapped into them through
its consensus JEL code. Codes the paper's table omits are added (C8 → Econometrics, M → Production and IO, O5 →
Development); a work whose primary code is still outside the table (Ostrom 2009, D02) takes the field most often
named by the three models' secondary codes (Public, law and political economy, 5 of 7 mentions).

```
../02_fields/results/prize_works_jel.csv ─┐
../data/econ_prizes_laureates.csv         ├─► field_context_prompts.ipynb ─► context/00_*.md, 01_*.md   (the notes)
../01_committee/profiles/*.json, roster  ─┤                              ─► questions/fields14.json     (question draft)
                                          ─┘                              ─► results/*.csv, ../record/tables/*.tex
```

## The notes

| File | Content | Tags |
|---|---|---|
| `00_1_instruction.md` | goal, evidence tags, the rotation prior, the operational weights, the required output (for the `assume_true` treatment) | P M D |
| `00_2_field_classification.md` | the 14 fields with their JEL codes, the additions, the boundary rules (growth / development / macro; information / games; institutions) | P D |
| `00_3_prize_works_by_field.md` | every prize work 1969–2025 in its field: year, laureates, share, consensus code and JEL name, fallback rule, other fields the secondary codes point to | S O |
| `00_4_prize_history_by_field.md` | per field: prizes, award years, last award, years since, median gap, prizes 2021–25 and 2016–25, operational tier, **baseline rank** from the record alone; sequence facts (repeats, O4 2024→2025, macro as a secondary code, laureates per prize) | S |
| `00_5_recent_prizes_2021_2025.md` | the seven works of 2021–2025: laureates, shares, affiliations, ages, official motivations, the three models' codes, field and weight; how to read them (technology ≠ one field; institutions boundary) | O S D |
| `00_6_unawarded_maturity.md` | what to assess (defining works, programmes, textbooks, diffusion), the paper's pool sizes per field and why they are not 2026 counts, what the project does not provide | P M D |
| `00_7_societal_context.md` | the meeting's themes (AI and jobs, trade and tariffs, war and migration, inequality, institutions and democracy) as auxiliary information | M D |
| `00_8_committee_2026.md` | roster and roles; coverage of the 14 fields by the step-1 profiles (members, 2+ models, by role, main field of); one line per member (main field, fields covered, recent interests, Dolton–Tol Table A.6 code); how to use it | O S P D |
| `00_9_paper_evidence_and_limits.md` | what Dolton and Tol report on the field (Table 2 figures read from the paper on 10 Oct 2026) and why the numbers are not 2026 probabilities | P D |

Sizes 1.1k–9.7k characters (44k in all); the earlier Preseen notes of this project were 1.2k–4.5k, the longest cards
about 6k. All nine are attached with `treatment=assume_true`: 00_1 is the brief, 00_2–00_3 the definitions the
resolution depends on, 00_4–00_5 the record, 00_6–00_9 the rest of the design. A tenth, optional note with external
2026 signals about named people (Kalshi prices, Clarivate 2026, recent prizes, from `Data/convergence_2026.csv`, fields
assigned by the forecast's author) was built on 10 October and dropped on the user's decision; `run_field.sh` refuses
to run unless `context/` holds exactly the nine `00_` notes.

## Question (`questions/fields14.json`)

Multiple choice, 14 options `"<field> (JEL <codes>): <three or four keywords>"`, mutually exclusive and comprehensive,
no Other. Resolves to the field that contains the primary JEL code of the awarded contribution, determined by the same
procedure that coded 1969–2025 (three models code the official motivation, consensus letter → two-digit field → code,
mapped by the code groups of the labels). A prize divided between fields resolves by its overall motivation when the
announcement gives one (as in 2025), otherwise by the larger share, then by the contribution named first; a primary
code outside the 14 fields resolves by the majority of the secondary codes; if no field can be assigned the question
is annulled. The fine print fixes the conventions (O43 → Growth, D82 → Information, D44/C78 → Games, …) and says the
keywords are illustrative.

## Preseen run (step 4b)

`run_field.sh [tag]` (default tag `nobel26-econ-fields`, state in `preseen_exp/fields14/`): creates two identical
private questions (arms `control` = no context, `main` = the nine notes as `assume_true`), runs one rep per arm,
polls until both finish and writes `preseen_exp/fields14/runs.csv` (`runs/*.json` hold the full task envelopes).
Submitted 10 October 2026 12:00 CDT from a detached `tmux -L econ` session (log `run_fields.out`); both runs
completed by 12:44 (control 27 min, main 44 min; 4 subforecasts each).

### Results (10 October 2026)

| Field | Baseline rank | Control % | Main % |
|---|---|---|---|
| Macro | 2 | 14.5 | 16.8 |
| Trade | 3 | 6.8 | 14.0 |
| Production, Industrial Organization | 5 | 14.6 | 13.9 |
| Public, Law, Political Economy | 4 | 3.4 | 12.8 |
| Equilibrium, Welfare | 1 | 3.7 | 10.3 |
| Information | 6 | 8.2 | 6.5 |
| Resources, Environment | 8 | 3.8 | 6.3 |
| Behavioural, Experimental | 7 | 6.3 | 5.8 |
| Games, Market Structure | 9 | 7.5 | 4.4 |
| Econometrics | 10 | 12.3 | 3.1 |
| Labour | 12 | 9.5 | 2.3 |
| Finance | 11 | 3.8 | 2.2 |
| Development, Economic History | 13 | 2.7 | 0.9 |
| Growth | 14 | 2.8 | 0.7 |

Spearman main vs control 0.43; main vs the record-only baseline order 0.94; control vs baseline 0.27. The five
bonus-tier fields hold 67.8 % in main against 43.0 % in control; the 2021–2025 fields 9.2 % against 31.1 %. The main
write-up reports the record-only, after-maturity and submitted distributions with its factors (maturity: Production/IO
1.75, Macro 1.60, Trade 1.45, Public 1.40, Equilibrium 0.85, Growth 0.90). Files: `results/preseen_fields14_results.{csv,md}`,
`results/write_up_{control,main}.md`, `preseen_exp/fields14/runs/*.json` (full envelopes, local).

## Results of the record alone (10 October 2026)

Baseline rank by years since the last award: Equilibrium and welfare (last 1998, 28 years), Macro (2006, 20), Trade
(2008, 18), Public, law and political economy (2009, 17), Production and IO (2014, 12), Information (2016), Behavioural
(2017), Resources (2018), Games (2020), Econometrics (2021), Finance (2022), Labour (2023), Development and economic
history (2025), Growth (2025; 1.5 prizes in 2024–25, 2.0 in 2016–25). The same field followed itself in 3 of 56
transitions (1973, 1985, 2025). Committee coverage: Labour 9 members, Public 8, Econometrics / Equilibrium /
Information / Macro / Development / Growth 5 each, Trade 1 (Friberg). Tables: `results/fields14_history.csv`,
`results/committee_fields14_coverage.csv`, `results/committee_members_fields14.csv`.

## Commands

```bash
cd "/project/jevans/Dawoon/Nobel Prize/Econ/04_field_forecast"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=curvature field_context_prompts.ipynb   # ~2 min
# submit (PRESEEN_API_KEY in the environment; the script never prints it):
tmux -L econ new-session -d -s fields -c "$PWD" 'bash run_field.sh nobel26-econ-fields > run_fields.out 2>&1'
tail -f run_fields.out                                   # created ... context ready (9 notes) ... submitted ... saved
EXP_DIR=preseen_exp/fields14 $PY nobel_preseen_exp.py --tag nobel26-econ-fields poll   # status without waiting
```

## Data correction after the upload

The Nobel Prize API dates the 2022 prize (Bernanke, Diamond, Dybvig) 2011-10-10, so the crawl's `age_at_award` is
eleven years too low for these three laureates (57, 57, 56 instead of 68, 68, 67). The notes uploaded on 10 October
12:00 CDT carry the API ages in `00_5` (the ages are incidental to the field question; nothing else is affected). The
exact uploaded texts and the question are preserved in `uploaded_2026-10-10/`; the notebook now computes ages from the
prize year, so the live `context/00_5_recent_prizes_2021_2025.md` differs from the uploaded one in those three ages
only.

## Known limits

- The notes render the Korean design document in English; check the rendering against the original before use.
- The meeting transcript cited as [M] is not in the repository; its content enters only through the design document.
- The paper's Table 2, B.7, A.6 and E.12 figures were read from the arXiv PDF on 10 October 2026; the "39 years after
  the PhD" figure of the design document was not checked there and is not quoted in the notes.
- `00_3` lists codes and JEL names, not the motivations (kept the note under 10k characters); the motivations of
  2021–2025 are in `00_5`, all others in `../data/econ_prizes.md`.
