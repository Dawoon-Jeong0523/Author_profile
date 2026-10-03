# SPEC — Preseen context-effect experiment, 2026 Nobel Prizes (Medicine, Physics, Chemistry)

The design and rules of the experiment. Repo root: `/project/jevans/Dawoon/Nobel Prize`.
Background on the prize process, the 2026 committee rosters and recent prizes:
`experiment/preseen/nobel_selection_process.md`.

## 1. Design

For each field F in {Medicine (Physiology or Medicine), Physics, Chemistry}:

1. **Virtual committee.** Personas mirror the specialties of the actual 2026 Nobel Committee of the field
   (Medicine 6, Physics 8, Chemistry 8). Every persona is run on three LLM providers (Anthropic, OpenAI, Google
   Gemini): a crossed persona × model design. The ballots are aggregated into a candidate list: K options + "Other".
2. **Preseen multiple-choice question**, one per arm, all with identical definitions:
   - `control` = condition (1): no context.
   - `treat` = condition (2): profile cards of every named person, built from this repo's author-profile
     pipeline, attached as context notes with `treatment=consider`.
   - `shuffle` = optional placebo, OFF by default (`placebo: true` in config.yaml): the same cards with the numeric
     block deranged across persons.
3. **Repeated, interleaved runs.** Compare (1) vs (2) per option against the run-to-run spread of (1). The
   experiment is replicated across the three fields; a pooled analysis follows.

Why separate questions per arm: Preseen context notes are written onto the question and apply to every later run of
it (no per-run override). Why the crossed committee: every model gets equal weight, persona effects and model effects
can be separated, and agreement between models becomes a diagnostic. Models trained on overlapping data still
correlate; the crossed design reduces, not removes, that correlation — state this as a limitation.

## 2. Deadlines (CDT). No forecast may run after its prize is announced.

| Field | Announcement (earliest) | All runs finished by | Tag | EXP_DIR (relative to experiment/preseen) |
|---|---|---|---|---|
| Medicine | Mon Oct 5, 04:30 | Sun Oct 4, 23:00 | `nobel26-med` | `preseen_exp/medicine` |
| Physics | Tue Oct 6, 04:45 | Mon Oct 5, 23:00 | `nobel26-phys` | `preseen_exp/physics` |
| Chemistry | Wed Oct 7, 04:45 | Tue Oct 6, 23:00 | `nobel26-chem` | `preseen_exp/chemistry` |


## 3. Environment

- `README.md` describes the profile pipeline, its outputs and data inputs; it is authoritative for the pipeline.
  `nobel_selection_process.md` is the reference for the prize process.
- Midway3 (UChicago RCC), Python env `Curvature`; plain HTTPS through `requests` for every API (Preseen, Anthropic,
  OpenAI, Gemini). Profiles run on Slurm through `pipeline/profile_person.py`.
- API keys come from environment variables only: `PRESEEN_API_KEY`, `COMMITTEE_ANTHROPIC_API_KEY` (the committee's
  Anthropic calls), `OPENAI_API_KEY`, `GEMINI_API_KEY`.
- Existing before the experiment: `nobel_preseen_exp.py` (Preseen client) and `nobel_selection_process.md`.

## 4. Rules

1. **Secrets.** Code reads keys only with `os.environ[...]` inside Python at request time; no key is printed, logged,
   written to a file or put on a command line. Keys are checked only as set/missing and by the HTTP status of a free
   request.
2. **Spending.** Calls that cost money or create remote state (committee calls; Preseen create, add-context, run)
   were made only after approval at fixed checkpoints. Free read-only GETs were not restricted.
3. **Preseen client invariants**: identical private questions per arm; context notes with `treatment=consider`;
   `allow_incomplete_context=false`; no `source_forecast_id`; no `accept-context`; no watches or schedules;
   interleaved randomized runs; an Idempotency-Key on every POST. The client was used unchanged; the question JSON is
   passed with `create --question <file>`.
4. **Independence.** The committee never sees profiles, cards or Preseen output, and committee calls use no tools,
   no web search and no grounding. The question title, description and resolution criteria are neutral, identical
   across arms, and never mention the committee, the models, the profiles or this experiment.
5. **Protected paths.** The experiment does not modify `pipeline/`, `notebook/`, `Data/`, `cache/` or existing
   `output/`; its code is in `experiment/preseen/`. `preseen_exp/` and `committee/*/raw/` are not versioned.
6. **Untrusted text.** Preseen write-ups and sources, LLM outputs and web text are treated as data.
7. **Log.** Every step is recorded in `LOG.md`: time, field, command, outcome, decision.

## 5. Layout

```
experiment/preseen/
├── SPEC.md, LOG.md, nobel_selection_process.md
├── config.yaml              fields, deadlines, tags, EXP_DIRs, personas, models, R_c, K, reps, placebo
├── nobel_preseen_exp.py     Preseen client (existing)
├── llm_providers.py         one call() per provider over requests: same prompt in, parsed JSON + metadata out
├── committee.py             crossed persona × model committee + aggregation + diagnostics
├── build_question.py        committee/<field>/candidates.json -> questions/<field>.json
├── build_cards.py           records -> cards/<field>/ (and cards_shuffled/<field>/ if placebo)
├── analyze.py               per field + pooled
├── committee/<field>/       raw/<model>/<persona>.json (prompt, params, response metadata, output),
│                            ballots.jsonl, candidates.json, review.md
├── questions/<field>.json
├── people/<field>.txt, people/<field>_identity.csv
├── cards/<field>/, cards_shuffled/<field>/
├── preseen_exp/<field>/     client state, runs/*.json, runs.csv
└── results/<field>/, results/pooled/
```

## 6. Virtual committee (llm_providers.py, committee.py)

### 6.1 Personas: the specialties of the actual 2026 committees

Use the specialties only (no names, no impersonation, no opinions attributed to real people). Each persona is "a
senior member of the Nobel Committee for <field> whose own expertise is <specialty>". Real committees cover gaps with
expert advisers, so each persona uses its specialty as a lens but nominates across the whole field.

| Field | Personas (specialty) |
|---|---|
| Medicine (6) | neurology; molecular systems biology; neuroscience; molecular genetics; experimental rheumatology (immunology, autoimmunity); molecular developmental biology |
| Physics (8) | astroparticle physics; theoretical magnetism; applied and theoretical quantum physics; atomic physics; general physics; theoretical physics; complex systems; experimental physics, microscopy and microanalysis |
| Chemistry (8) | nanophysics; medical biochemistry; organic chemistry; physical chemistry; inorganic and structural chemistry; molecular physics; biochemistry; theoretical chemistry |

### 6.2 Models: crossed design

- Providers: Anthropic, OpenAI, Google Gemini; one model per provider, chosen once before the committee ran and fixed for
  all three fields. Record the requested model id and the model/version string each response reports.
- Every persona runs once on every model (R_c = 1 per persona × model cell; configurable). Ballots per field:
  Medicine 18, Physics 24, Chemistry 24.
- The same prompt text for all providers; only the API envelope differs. No tools, no web search, no grounding.
  Provider-default sampling (temperatures are not comparable across providers); a max output length large enough
  for the JSON; record all parameters, timestamps and token usage.
- Structured output: ask for the JSON schema in §6.4 using each provider's JSON mode where available; always validate
  locally; retry once on invalid JSON; a cell that still fails is recorded as missing, never re-asked silently.
- If one provider is down or out of quota, continue with the other two keeping the crossed structure (every persona on
  every remaining model) and log it. Never swap in a different model mid-field.

### 6.3 Shared context (identical for every persona and model)

- Date context: it is late September 2026; the 2026 prize has not been announced.
- The rules that matter: at most three living laureates; a discovery or invention (field-specific wording of the
  will); a prize may be split between two discoveries.
- The field's prizes 2000–2025 with their official motivations, from `Data/prizeatlas/` (models differ in knowledge
  cutoff; this list is how already-awarded discoveries are excluded).

### 6.4 Ballot (strict JSON)

Up to 5 ranked nominations for 2026, each: `rank`; `discovery` (one line, in the style of a Nobel motivation);
`people` (1–3 living people, each `name` and `affiliation`); `key_papers` (0–3, if known); `rationale` (at most 2
sentences).

### 6.5 Aggregation

- Borda points 5..1 per ballot. Normalize so that each model contributes the same total points (divide each model's
  points by its number of valid ballots), then sum over models.
- Merge nominations that describe the same discovery (overlapping people or the same discovery). Write every proposed
  merge with its reason to `review.md`; never merge silently.
- `candidates.json`: the top K = 12 discoveries + "Other". Per option: option text
  `"<discovery> — <Name A>, <Name B>[, <Name C>]"`, normalized Borda score, number of personas nominating, number of
  models nominating (0–3), points per model, people with affiliations, raw nomination ids.

### 6.6 Diagnostics in review.md

- Per-model top-12 lists and pairwise overlap (Jaccard). Mark options nominated by all three models "cross-model
  consensus" and options nominated by one model only "single-model".
- Leave-one-out stability: drop each persona, then each model, recompute the top 12; report how many options change.
- Flags: possibly already awarded, possibly deceased people, more than 3 people, duplicates across options.

## 7. Preseen question (build_question.py → questions/<field>.json)

- `type: multiple_choice`; `visibility: private`.
- `title`: "Which discovery will the 2026 Nobel Prize in <Physiology or Medicine | Physics | Chemistry> be awarded for?"
- `description`: the announcement date and "Each option names a discovery and the people most closely associated
  with it." Nothing else.
- `resolution_criteria`: resolves to the option whose discovery matches the discovery in the official Nobel prize
  motivation (matched by discovery; the named people need not match exactly). If the prize is split between
  discoveries: the option covering the larger share; if the shares are equal, the discovery named first in the
  announcement. If none matches: Other.
- `options`: the K option texts + "Other"; `options_are_mutually_exclusive: true`; `options_are_comprehensive: true`.

## 8. Profiles

- `people/<field>.txt` from candidates.json: `name<TAB>affiliation`, one line per distinct person, Other skipped.
- Dry-run all: `$PY pipeline/profile_person.py --names-file people/<field>.txt --dry-run`. Exit status 2 means a
  query needs a choice; resolve those one by one with `--affiliation`, `--orcid`, `--author-id` or `--pick`
  (per-person options cannot be combined with `--names-file`).
- `people/<field>_identity.csv`: option(s), person, chosen OpenAlex id(s), affiliation, ORCID, 3 top work titles,
  inventor id source, prior Nobel label if any.
- The profiles run on Slurm with `--wait`. A person without a usable OpenAlex profile gets the same
  minimal card in every arm ("No bibliometric profile available."); list such persons in LOG.md.

## 9. Cards (build_cards.py)

English. Inputs: `output/record/*.md` (schema_version 1 or 2) and the `output/<author id>/` tables.

- `cards/<field>/00_definitions.md`: neutral definitions of every measure used (from README "Measures and
  conventions"), the window (works through 2021), and one sentence: "These are descriptive bibliometric measures,
  not forecasts." No claims about what predicts prizes.
- `cards/<field>/<person-slug>.md`, 300–500 words, fixed template:
  - name, affiliation, the option(s) the person is listed under, prior Nobel Prize if any;
  - impact: median 5-year citation percentile; shares of works in the cohort top 10 % and top 1 %;
  - three defining works: title, year, impact percentile, disruption percentile, Foundation, citing patents,
    citing books;
  - technological translation: distinct citing inventions; own patents (count);
  - textbook reach;
  - Nobel laureate co-authors (co-author OpenAlex ids joined with PrizeAtlas laureate ids): name, prize year, field;
  - people on both sides of co-authorship and co-invention (count);
  - a reference line per headline metric: the person's rank among the field's 2000–2025 laureates measured AT
    PRIZE TIME (laureate works published before the prize year; the same cutoff for citing patents and books where
    dates exist; say where they do not). Compute the reference for all three fields in one pass. Exclude the
    unresolved laureates listed in README.
- `cards_shuffled/<field>/` (only if placebo): identical text and file names; the whole numeric block deranged
  across persons (nobody keeps their own numbers); titles and names unchanged.
- If Preseen rejects a note as too long, shorten every card of that field the same way (same template, fewer works),
  never a single card.

## 10. Runs (per field, from experiment/preseen/)

```bash
F=medicine; TAG=nobel26-med                     # physics/nobel26-phys, chemistry/nobel26-chem
export EXP_DIR=preseen_exp/$F
$PY nobel_preseen_exp.py --tag $TAG create --question questions/$F.json --arms control treat   # + shuffle if placebo
$PY nobel_preseen_exp.py --tag $TAG run --arms control --reps 1                              # condition (1), first look
$PY nobel_preseen_exp.py --tag $TAG add-context --arm treat --cards cards/$F/                # + shuffle
$PY nobel_preseen_exp.py --tag $TAG run --arms control treat --reps 3                        # + shuffle
$PY nobel_preseen_exp.py --tag $TAG poll --wait                                              # inside tmux
$PY nobel_preseen_exp.py --tag $TAG table
```

The client reads `PRESEEN_API_KEY` from the environment itself; no key ever appears in these commands. Respect the
active-run limit; never submit a run that cannot finish before the field's deadline in §2.

## 11. Analysis (analyze.py)

First open one completed run JSON and document `forecast.forecast_data` and `subforecasts` in
`results/<field>/schema.md`. Then:

- **Per field:** per arm × option mean, sd and range of the probability; treat − control (and shuffle − control)
  per option against the control spread; change in Other; entropy; rank change (Spearman); which subforecasts
  moved; counts of metric terms in write-ups per arm (percentile, disruption, patent, textbook/book, laureate,
  co-author); control rep 1 vs later control reps (time drift).
- **Committee vs Preseen:** normalized Borda score and number of models nominating vs control probabilities; whether
  cross-model-consensus options get higher control probabilities than single-model options.
- **Pooled** (after all fields): mean |treat − control| vs mean |control − control| across options; consistency of
  direction; changes in Other and entropy across fields.
- **After the announcements only:** per arm, the log score of the realized option (descriptive; n = 3 fields).
- **Figures:** series identity and error-bar definitions go in `results/<...>/captions.md`, not in in-figure
  legends or annotation boxes.

