# Candidate profiles and Preseen forecasts, 2026 Nobel questions

Dawoon Jeong, 3 October 2026

Two folders, kept apart so the inputs can be fed to a model and varied without touching the outputs:

- `context/` is everything the forecaster was given, one unit per line, so any piece can be left out.
- `forecasts/` is what Preseen returned under each of the four conditions we ran on 1–2 October.

## context/

| File | Count | What |
|---|---:|---|
| `questions/<field>.json` | 3 | the question posted in every condition: 12 named discoveries and "Other" |
| `definitions.jsonl` | 3 | one per field; explains the measures on the cards |
| `profile_cards_used_in_runs.jsonl` | 98 | one card per person named in an option, as posted in the runs |
| `profile_cards_current.jsonl` | 98 | the same cards rebuilt on 3 October; only the patent lines differ (67 cards) |
| `instruction_notes.jsonl` | 2 | the notes that made the cards "one main source" or "the main evidence" |
| `conditions.json` | | which notes each condition posted, in which order, with which `treatment` |
| `records/` | 94 | the long form of each profile, written for an agent to read; `index.csv` maps people to options and files |

Each JSONL line carries `id`, `field`, `treatment`, `source_file` and `text`; card lines add `order` (the position in
the runs), `person`, `options` (option numbers in the question) and `openalex_author_ids`. 94 people have 98 cards
because four of them are named in two fields.

## forecasts/

| File | Rows | What |
|---|---:|---|
| `runs.csv` | 390 | probability of each of the 13 options in each of the 30 runs |
| `subforecasts.csv` | 1,560 | the same for the 4 subforecasts behind each run |
| `writeups.jsonl` | 30 | Preseen's write-up and its 4 subforecast write-ups for each run |
| `by_condition.csv` | 39 | mean probability and rank of each option under each condition |

## The four conditions

Same question in all four ([conditions.md](conditions.md) has the exact settings and both instruction notes):

| Condition | Notes posted to the question | Runs per field |
|---|---|---:|
| `control` | none | 5 |
| `cards_as_context` | definitions note, then the cards, all with `treatment: consider` | 3 |
| `cards_one_main_source` | instruction note (`assume_true`), then the definitions note and cards (`consider`) | 1 |
| `cards_main_evidence` | the other instruction note (`assume_true`), then the definitions note and cards (`consider`) | 1 |

`post_notes.py` posts the notes of one condition to a Preseen question in the same order and with the same
`treatment` as the runs:

```
export PRESEEN_API_KEY=...
python post_notes.py --question <question id> --field medicine --condition cards_as_context
```

## What the forecasts show

How far one run moved the forecast: the average distance of an option from the control mean, in percentage points.
The first column is one control run against the other control runs, i.e. the noise.

| Field | Control run | Cards as context | One main source | Main evidence |
|---|---:|---:|---:|---:|
| Medicine | 0.75 | 0.69 | 2.13 | 4.67 |
| Physics | 0.71 | 0.84 | 2.28 | 3.20 |
| Chemistry | 0.59 | 0.62 | 1.94 | 2.86 |

Leading named option under each condition:

| Field | Control | Cards as context | One main source | Main evidence |
|---|---|---|---|---|
| Medicine | GLP-1 20.3 % | GLP-1 19.6 % | orexin 11.7 % | optogenetics 7.9 % |
| Physics | optical lattice clocks 14.7 % | optical lattice clocks 15.4 % | quantum simulators 12.8 % | quantum simulators 13.3 % |
| Chemistry | sequencing-by-synthesis 19.0 % | sequencing-by-synthesis 19.2 % | sequencing-by-synthesis 10.0 % | organic LEDs 9.4 % |

All options: [results.md](results.md).

Attached as ordinary context, the cards moved the forecast about as much as one control run differs from the
others. Preseen's own write-up says so: "The user-provided bibliometrics were used as a secondary cross-check."
(medicine, cards as context). With an instruction note the forecast moved about three times the noise (one main
source) and four and a half to six times (main evidence); under the main-evidence note the three control leaders fell
to a fraction of their control probability (GLP-1 20.3 % to 3.0 %, optical lattice clocks 14.7 % to 4.5 %,
sequencing-by-synthesis 19.0 % to 5.5 %). My reading, not a measurement: the cards carry information the
forecaster does not otherwise weigh much, and they should not decide a forecast on their own.

## Where a card comes from

The numbers on a card are computed by code from OpenAlex (January 2026 snapshot), PatentsView (31 December 2025),
Reliance on Science (patent-to-paper citations) and the citation metrics of our Science of Science project. No
language model writes them. The people, though, were chosen by language models: the options and the names in them
came from a virtual committee of three LLMs. [provenance.md](provenance.md) says what was measured, what an LLM wrote,
what Preseen produced, and what we decided.

## When the cards help

- The options name scientists, and the outcome turns on how their work has been received: prizes, awards, credit for
  a discovery.
- As context notes with `treatment: consider`. An instruction to treat them as the main evidence is a much stronger
  intervention.
- For a known list of names. A new profile is a batch job of a few minutes on our cluster with local copies of the
  datasets, not a live call.

They help less for people outside academic publishing, for early-career researchers, for anything after 2021 (the
profiles stop there) and for patents outside the US.

## Caveats

- Two conditions have a single run per field; the comparisons are descriptive. Log scores against the actual prizes
  (5–7 October) are not computed yet.
- The conditions were not randomized together. The two instruction notes were written after the 1 October result,
  and Preseen reads the web when it forecasts, so the run date is part of each condition.
- OpenAlex sometimes merges two people with the same name; the profile then mixes them (Michael V. Berry's rebuilt
  card counts one patent of a Michael J. Berry). Emmanuel Mignot's card undercounts him.
- The reference lines ("higher than X % of the field's 2000–2025 laureates at prize time") leave out 18 of the 199
  laureates, whose profiles sit under a different OpenAlex id.
- `context/` and `forecasts/` hold no Preseen question or run ids. The experiment logs elsewhere in this repository
  do (`experiment/*/LOG.md`, `experiment/*/results/*/runs_long.csv`).

`build_handoff.py` rebuilds everything in this folder from the experiment files.
