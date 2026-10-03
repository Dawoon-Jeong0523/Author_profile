# The four conditions, exactly as run

All runs were made through Preseen's external API (`https://preseen.com/api/v1/external`) with
[`experiment/preseen/nobel_preseen_exp.py`](../experiment/preseen/nobel_preseen_exp.py). Each condition is its own
private Preseen question. A context note stays on its question, so the only way to give runs different context was
to give them different questions.

## The question

One question per field, created from the same file in every condition:
[`medicine.json`](../experiment/preseen/questions/medicine.json),
[`physics.json`](../experiment/preseen/questions/physics.json),
[`chemistry.json`](../experiment/preseen/questions/chemistry.json). The copies in
`experiment/preseen_cards_main/questions/` and `experiment/preseen_cards_balanced/questions/` are byte-identical.

- Multiple choice, 13 options: 12 named discoveries, each with the people who would share the prize, and "Other".
  Options are mutually exclusive and together cover every outcome.
- Example title: "Which discovery will the 2026 Nobel Prize in Physiology or Medicine be awarded for?"
- The 12 options per field came from a virtual committee before any profile existed (see
  [provenance.md](provenance.md)); the profiles describe the people those options name.

## What each condition attached

| Condition | Notes on the question, in the order they were added | `treatment` | Runs per field | Dates |
|---|---|---|---|---|
| Control | none | – | 5 | 4 on 1 Oct, 1 on 2 Oct |
| Cards as context | definitions note, then one card per named person (30 medicine, 34 physics, 34 chemistry) | `consider` for every note | 3 | 1 Oct |
| Cards as one main source | instruction note B (below), then the same definitions note and cards | `assume_true` for the instruction, `consider` for the rest | 1 | 2 Oct |
| Cards as the main evidence | instruction note A (below), then the same definitions note and cards | `assume_true` for the instruction, `consider` for the rest | 1 | 2 Oct |

Details:

- Control on 1 October: one run before any card was attached, then three runs interleaved with the three
  cards-as-context runs. The client submits runs in rounds and shuffles the order of the questions within a round
  with a seeded random generator. On 2 October a second control question got one run next to the main-evidence run,
  to check for drift between the two days.
- The cards are the files in [`experiment/preseen/cards_v1/<field>/`](../experiment/preseen/cards_v1/), one note per
  file. `00_definitions.md` went first; the person cards followed in a fixed shuffled order: file names sorted, then
  `random.Random(2026).shuffle`. The order was the same in every condition, and `context/profile_cards_used_in_runs.jsonl`
  gives it in the `order` column. The run logs of 2 October confirm it note by note.
- Notes were added with `POST /questions/{id}/context/` (`{"text": ..., "treatment": ...}`), and the client waited
  for `GET /questions/{id}/context/ready/` before any run. Each run is `POST /questions/{id}/forecasts/` with
  `{"allow_incomplete_context": false}`.
- The 2 October conditions were run with [`run_field.sh`](../experiment/preseen_cards_main/run_field.sh) in each
  follow-up folder; the commands are in the script.
- The client also offers `treatment: look_into`; we did not use it.

The notes are also in `context/` as JSONL (`definitions.jsonl`, `profile_cards_used_in_runs.jsonl`,
`instruction_notes.jsonl`), and `context/conditions.json` lists which ones each condition posted, in order, with the
`treatment` used. `post_notes.py` replays a condition on a new question.

Question and run ids are not in `context/` or `forecasts/`. They do appear in the experiment logs
(`experiment/*/LOG.md`) and in `experiment/*/results/*/runs_long.csv`. The raw API responses are not in the
repository.

## Other things worth knowing

- In all: 30 runs on 15 Preseen questions with 309 notes, every run with 4 of 4 subforecasts.
- The conditions were not randomized together. Control and cards-as-context ran interleaved on 1 October; the two
  instruction notes were written after that result (the one-main-source note also after the main-evidence run) and
  ran once each on 2 October, on new questions.
- Preseen searches the web when it forecasts (one medicine control run listed 297 sources), so the run date is part
  of each condition, and "control" pools two questions and two days. The 2 October control run sat 0.73 / 0.71 /
  0.67 percentage points per option from the 1 October control mean (medicine / physics / chemistry), outside the
  1 October range on 4 / 4 / 7 of the 13 options. One sentence on the published dashboard says it stayed inside that
  range; the numbers here are the right ones.
- In chemistry the 1 October runs were resumed after a pause in a slightly different order (control, then the second
  and third cards-as-context runs).
- Separate from the four conditions, one check on 1 October tested whether a context note reaches the forecast at
  all: a medicine question with one `assume_true` note, "Svetlana Mojsov will not be among the laureates of the 2026
  Nobel Prize in Physiology or Medicine. Exclude her from consideration as a possible laureate when you estimate the
  probabilities." GLP-1 fell to 7.3 % (1 October control mean 21.0 %, range 18.0–22.6 %) and orexin became the
  leading named option at 15.4 %. One run; details in
  [`experiment/preseen/checks/medicine_exclude_mojsov/result.md`](../experiment/preseen/checks/medicine_exclude_mojsov/result.md).

## Instruction note A: cards as the main evidence

[`experiment/preseen_cards_main/instruction/00_instruction.md`](../experiment/preseen_cards_main/instruction/00_instruction.md),
verbatim:

> Assumption for this forecast: the profile notes attached to this question are the main evidence for comparing the
> named options.
>
> - The profiles cover only the people named in the options. Judge each named option by the profiles of its named
>   people; judge "Other" as you otherwise would, and use the profiles mainly to divide the remaining probability
>   among the named options.
> - Base the relative probabilities of the named options primarily on these profiles: the measures they report
>   (impact, defining works, technological translation, textbook reach, collaboration) and the reference lines that
>   compare each person with past laureates at the time of their prize. How to weigh these measures, and the people
>   within an option, is your judgment.
> - Take the figures as given. Do not discount a profile because author attribution cannot be audited, because the
>   record ends in 2021, or because percentiles among past laureates are not calibrated selection probabilities;
>   translating the profiles into probabilities is part of the task.
> - Use other information (prizes and awards, recent news, published predictions, the history of the prize) only as a
>   secondary adjustment, not as the main basis for the ranking.
> - In the write-up, state for each leading option which profile evidence drove its probability.

## Instruction note B: cards as one main source

[`experiment/preseen_cards_balanced/instruction/00_instruction.md`](../experiment/preseen_cards_balanced/instruction/00_instruction.md),
verbatim:

> Assumption for this forecast: the profile notes attached to this question are one of the main sources of evidence
> for comparing the named options, alongside the other evidence you would normally use.
>
> - Give the profiles substantial weight, comparable to that of your other main evidence: the measures they report
>   (impact, defining works, technological translation, textbook reach, collaboration) and the reference lines that
>   compare each person with past laureates at the time of their prize. How to weigh these measures, and the people
>   within an option, is your judgment.
> - Use other information actively as well: prizes and awards, recent news, published predictions, the history and
>   patterns of the prize, and your knowledge of the field. The profiles do not replace this evidence, and this
>   evidence does not replace the profiles.
> - The profiles cover only the people named in the options. For "Other", and for contributors who are not named in
>   an option, rely on the other evidence.
> - Take the figures as given. Do not discount a profile because author attribution cannot be audited, because the
>   record ends in 2021, or because percentiles among past laureates are not calibrated selection probabilities;
>   translating the profiles into probabilities is part of the task.
> - In the write-up, state for each leading option which profile evidence and which other evidence drove its
>   probability.

## Which cards

The runs used the cards in `experiment/preseen/cards_v1/`. On 3 October I rebuilt them after improving how the
pipeline links a scientist to their patents; the new versions are in `experiment/preseen/cards/`. Only two lines can
differ (own US patents, and people who are both co-authors and co-inventors); 67 of the 98 cards changed, listed in
[`cards/CHANGES.md`](../experiment/preseen/cards/CHANGES.md). The results in [results.md](results.md) are for the
`cards_v1` versions.
