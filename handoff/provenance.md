# What was measured, what an LLM wrote, what Preseen produced

| Label | Meaning |
|---|---|
| measured | computed by code from the bibliographic and patent data; no language model involved |
| LLM-written | text written by a language model, which the forecaster then saw or which decided who is on the cards |
| Preseen output | what Preseen returned: probabilities (numbers) and write-ups (text) |
| our decision | a choice made in the project; when Claude proposed it and I approved it, that is said |
| our interpretation | summaries and readings from our analysis sessions, written by Claude (claude-opus-5-5) |

## context/

| Piece | Label | How it was produced |
|---|---|---|
| the 12 options and the people in them | LLM-written | A virtual committee: one persona per specialty of the real 2026 Nobel committees, each run on claude-opus-5-5, gpt-5.5-2026-04-23 and gemini-3.1-pro-preview (66 ballots, 330 nominations, no tools or web search). Code combined the ballots with a Borda count that gives each model equal weight. Claude drafted the merges of near-duplicate nominations; I approved them. |
| question wording around the options | our decision | a fixed template (`experiment/preseen/build_question.py`), posted unchanged |
| every number on a card | measured | `experiment/preseen/build_cards.py` from the profile tables; no model is called |
| name, "Listed under" and, on 6 cards, the affiliation | LLM-written | the committee's text; the affiliation on the other 92 cards is OpenAlex's last known institution |
| which OpenAlex author a card describes | measured, 16 by decision | 82 automatic (pipeline rules: ORCID, then affiliation, then citations; 25 of the 82 matched on the affiliation the committee wrote); 16 proposed by Claude with a written reason each (`experiment/preseen/people/<field>_choices.yaml`) and approved by me as a batch |
| own US patents on a card | measured | PatentsView inventor ids linked to the author by code, no manual overrides. The cards used in the runs took the ids from an author-inventor crosswalk (pqrs), with a name search when it had none; the current cards use the refined linking of 3 October (repository README, "Inventor linking"). |
| definitions note | LLM-written | wording by Claude in our session, as a fixed text |
| instruction notes | LLM-written | wording by Claude; I reviewed the main-evidence note before it ran; the one-main-source note ran without a separate review of its wording |
| records | measured | `notebook/author_profile.ipynb`, same data as the cards |

## forecasts/

| Piece | Label | How it was produced |
|---|---|---|
| `runs.csv`, `subforecasts.csv` | Preseen output | probabilities copied from Preseen's responses; each run is Preseen's ensemble of 4 subforecasts |
| `by_condition.csv` | Preseen output | means of `runs.csv`, computed by our scripts |
| `writeups.jsonl` | Preseen output | Preseen's text, unchanged. Statements in it about recent events are Preseen's claims; we did not check them |

Preseen's responses do not say which model it runs.

## Elsewhere in the repository

| Piece | Label |
|---|---|
| `experiment/*/results/*/reasoning_summary*.md`, `summary_ko.md`, `checks/*/result.md` | our interpretation (Claude). The dashboards show these as "Summary of the reasoning" without saying so. |
| narrative text of the dashboards, `experiment/*/README.md`, `experiment/*/LOG.md` | our interpretation (Claude) |
| `experiment/preseen/SPEC.md` | our decision (written by me) |
| `experiment/preseen/committee/*/raw/` (not in git) | LLM-written: the committee's raw answers |

The analysis sessions ran on claude-opus-5-5, the same model as one of the three committee members.

## Data behind the measured parts

- OpenAlex, January 2026 snapshot: works, authorships, citations, citing books.
- PatentsView, 31 December 2025 release: US granted patents, inventors, assignees.
- Reliance on Science: citations from US patents and pre-grant publications to papers (our copy has no version label).
- Science of Science metric tables built from the above: citation and disruption percentiles within year and field.
- PrizeAtlas, crawled 30 September 2026: prior Nobel Prizes and the laureates behind the reference lines.
- OpenAlex live API, 1 October 2026: the affiliation line and some paper titles.
