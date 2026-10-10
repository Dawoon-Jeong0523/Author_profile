# Step 6: the Econ virtual committee — candidates for the five leading fields

Candidates (contribution + the people most responsible for it + defining works + reasoning) for the five fields with
the highest probability in the Preseen main arm of the latest field run (step 4b, second experiment, "Nobel Prize in
Economic Sciences" title), nominated by a virtual committee whose eleven personas are the members of the real 2026
committee as reconstructed in step 1, integrated across the three models by claude-opus-5-5, and written as Preseen
context notes for the people question.
[`virtual_committee.py`](virtual_committee.py) is written for the Econ pipeline and imports nothing from
`../../experiment/`; the parts of the earlier committee script (`experiment/preseen/committee.py`, 1 October) that
apply unchanged were copied in (see *Reuse* below).

## Design

| | the 1 October committees (Med / Phys / Chem) | Econ (this step) |
|---|---|---|
| personas | specialties of the real committee, anonymous | the 11 real members, from `../01_committee/profiles/<slug>.json` (persona summary, research lens, methods, what they value, questions they would raise, fields, recent interests) |
| cells | persona × model, one ballot per field | member × model, **one call covers the five fields** (33 cells; chosen by the user over 165 per-field cells) |
| nominations | ≤ 5 ranked per ballot | ≤ 5 ranked per field, so ≤ 25 per cell |
| nomination | discovery line, 1–3 living people with affiliation, ≤ 3 key papers, rationale ≤ 2 sentences | same + `jel_code` (level-3, inside the field's groups) and `born` per person |
| models | claude-opus-5-5, gpt-5.5-2026-04-23, gemini-3.1-pro-preview; no tools, no web search, provider defaults, 32k output cap | same (`../config.yaml`) |
| validation | schema; one retry; count limits as warnings | same, plus every field present once, and a warning when a code lies outside the field |
| aggregation | model-balanced Borda 5..1; person-key clustering; `merges.yaml` | model-balanced Borda 5..1 per field; **claude-opus-5-5 groups the nominations into candidates** (`integrate`); supporters by member and role, per-person support and flags (laureates, committee members, age ≥ 85, resemblance to an awarded motivation) computed locally. The rule-based clustering (`aggregate`) is kept for comparison |
| output | top-K options → Preseen question | Preseen context notes `context/06_00`–`06_05` (candidates with lineup, defining works, reasoning, support); pool of 30 in proportion to the main-arm probability: Macro 7, Trade 7, Production/IO 6, Public 6, Equilibrium 4 |

**Fields** (`settings.yaml`): Macro 16.9 %, Trade 15.6 %, Production and IO 14.0 %, Public, law and political
economy 13.3 %, Equilibrium and welfare 9.5 % (main arm of the latest field run, task 9b0a6220, 10 October 13:51 CDT;
the first experiment had the same five). Each field carries a definition with its boundary rules (from note 00_2) and
the list of works already awarded in it (from `../04_field_forecast/results/prize_works_fields14.csv`, official
motivations), which the committee must not nominate again. The other nine of the 14 fields are defined in
`settings.yaml` too (batches 2 and 3, from a short-lived plan to ask all 14) but `batches_to_ask: [1]` asks only the
five; the nine enter the prompt only in the list of the 14 fields with their codes.

**Prompt** (`virtual_committee.py prompt --member <slug> --batch 1` prints it; `prompts/example_john-hassler__b1.md`,
14.3k characters). System: "You take the perspective of {name}, {role} of the Committee ... reconstructed from the member's
public research record ... a simulation, and your nominations are inferences from that record, not the real person's
views", followed by the profile, then "nominate from the whole of each field, not only from the areas closest to this
member's work". User: the date (9 October 2026, before the announcement); the rules (outstanding contribution, at most
three living people, no previous laureate, divided prizes possible, awarded contributions excluded, the age record of
step 5 as context on maturity, not as a filter: median 67, yearly award rate among eventual laureates, Dolton-Tol
maximum at 70-71, no trend, no reliable field difference, co-laureates of one generation, 20 awards at 75+, never
posthumous); the list of the 14 fields; the five fields with definitions and awarded works; the task (per nomination:
contribution, JEL code, 1-3 living people with birth year, up to 3 defining publications, a rationale of up to 3
sentences with the main reservation) and the JSON form.

**Integration** (`integrate`): one claude-opus-5-5 call per field with every valid nomination (anonymous ids and
ballot labels, rank, code, contribution, people, key works, rationale) and the named people who cannot be awarded.
Claude returns distinct candidates (one contribution that one motivation could award to at most three people; no
umbrella candidates; same-ballot nominations joined only if plainly the same): ids, motivation, code, lineup (1-3 named
people, ineligible ones left out), up to 4 defining works copied from the nominations, reasoning (<= 3 sentences incl.
the main reservation), grouping note. It does not rank or score. Checked locally (every id exactly once, lineup and
works from the candidate's nominations); scores and support are computed from the assignment. Input stamp: a stale
integration is refused by `context` and `pool`.

**Independence.** The committee sees no Preseen output, no field probabilities, no external signals (Kalshi,
Clarivate, prizes) and no profiles of candidates.

**Reuse.** Copied unchanged from `experiment/preseen/committee.py`: `fold`, `name_tokens`, `person_key`, `middles`,
`assign_identities`, `same_person`, `content_words`, `jaccard`, `make_clusters`, the model-balanced Borda scoring
(`n_valid`, `score`) and the shape of `describe`, `load_manual` and the `merges.yaml` conventions (split, merge,
aliases, wording_from, people, deceased, person_notes). New for Econ: the five-field ballot and its validation, the
persona built from a profile, `collect` (one raw cell → five field ballots), the field definitions and awarded works
from the Econ steps, the flags for committee members and age, and `pool`.

## Commands

```bash
cd "/project/jevans/Dawoon/Nobel Prize/Econ/06_candidates"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY virtual_committee.py prompt --member john-hassler --batch 1   # the exact prompt (free)
$PY virtual_committee.py test --member john-hassler          # 3 paid calls -> committee/test/raw/
$PY virtual_committee.py estimate                            # cost from logged calls (else assumptions)
$PY virtual_committee.py run [--providers gemini] [--workers 9]    # 33 calls (paid; existing valid calls kept)
$PY virtual_committee.py status
$PY virtual_committee.py collect
$PY virtual_committee.py integrate [--dry-run] [--force]     # Claude, one call per field (paid; dry run writes prompts/integrate_*.md)
$PY virtual_committee.py context && $PY virtual_committee.py pool     # Preseen notes, pool (--source claude|rule)
$PY virtual_committee.py aggregate                           # rule-based clusters, for comparison
# all of it from a terminal with valid keys:  bash run_all.sh   (log run_all.out)
```

## Outputs

| File | Content |
|---|---|
| `committee/raw/<model>/<member>__b1.json` | one call: prompt, schema, every attempt (response metadata, usage), the validated nominations by field (local) |
| `committee/<field>/ballots.jsonl` | one ballot per member x model and field (member, role, model, nominations, warnings) |
| `committee/<field>/integrated.json`, `integrated.md` | Claude's candidates with locally computed support, defining works, reasoning, flags; the review listing every candidate's nominations |
| `committee/integrated_raw/<field>.json` | the integration call: prompt, attempts, id map, ineligible people |
| `context/06_00_committee_method.md`, `06_01_macro.md` ... `06_05_equilibrium.md` | the Preseen context notes (English) |
| `committee/<field>/candidates.json`, `review.md` | rule-based clusters (`aggregate`), for comparison |
| `results/pool.csv`, `pool.md` | the 30-option pool by field, with cross-field duplicates |
| `Old/five_fields_2026-10-10/` | the first run (one-line age record, 2-sentence rationale, 31/33 valid), archived |
| `logs/calls.jsonl` | every call (member, model, seconds, tokens, USD) |

## Status (10 October 2026)

- 14:19-14:29 CDT second run (`run_all.sh`, from the user's terminal): 33/33 calls valid at the first attempt ($8.30);
  integration valid at the first attempt in all five fields, no warnings ($2.33); notes `context/06_00`-`06_05`
  (about 127k characters with every candidate), pool 30 (7/7/6/6/4). Candidates per field: Macro 26, Trade 18,
  Production/IO 28, Public 22, Equilibrium 24. Living status of the shown people not yet checked. The first run (below)
  is archived in `Old/five_fields_2026-10-10/`.

First run:

- 13:05 CDT test, member Hassler: gemini-3.1-pro valid (25 nominations, 90 s, $0.16); claude-opus-5-5 and
  gpt-5.5 failed with an authentication error (401) — `check_keys.py` shows the same 401 for both keys while Preseen
  and Gemini answer 200. The step-1 and step-2 calls of 9 October worked, so the two keys changed after that. Cells
  are re-asked automatically once valid keys are in the environment (`run` skips existing valid cells).
- Gemini cells for all eleven members launched 13:10 CDT (`run_gemini.out`); Anthropic and OpenAI cells pending the keys.
- Estimated cost of the 33 cells about $8 (Gemini measured $0.16 per cell).

## Known limits

- The personas are reconstructions from published research (models' knowledge, no web search, training data to
  about 2024); the nominations are a simulation and must not be reported as the members' views.
- No candidate-level data (citations, living status) enters the committee; the living status of the shown people is to
  be screened afterwards (Wikidata, as `experiment/preseen/check_living.py` did) before any Preseen question.
- Members of the 2026 committee nominated by a persona (for example Krusell for heterogeneous-agent macro in the Hassler
  test cell) are flagged and left out of the pool: a sitting member is not awarded.
