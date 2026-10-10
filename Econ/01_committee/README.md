# Step 1: profiles of the 2026 committee members

The 11 members of the Committee for the Prize in Economic Sciences in Memory of Alfred Nobel 2026
([`roster.yaml`](roster.yaml); names, roles and titles from the
[nobelprize.org committee page](https://www.nobelprize.org/about/the-economic-sciences-prize-committee/), saved in
`source/`; affiliations checked against each person's university profile on 9 October 2026, with the link in
`affiliation_source`):

| Member | Role | Affiliation |
|---|---|---|
| John Hassler | chair | IIES, Stockholm University |
| Tommy Andersson | member | Department of Economics, Lund University |
| Anna Dreber Almenberg | member | Department of Economics, Stockholm School of Economics |
| Peter Fredriksson | member | Department of Economics, Uppsala University |
| Per Strömberg | member | Stockholm School of Economics (Swedish House of Finance) |
| Timo Boppart | co-opted member | IIES, Stockholm University |
| Kerstin Enflo | co-opted member | Department of Economic History, Lund University |
| Richard Friberg | co-opted member | Department of Economics, Stockholm School of Economics |
| Randi Hjalmarsson | co-opted member | Department of Economics, University of Gothenburg |
| Jan Teorell | co-opted member | Department of Political Science, Stockholm University |
| Per Krusell | secretary | IIES, Stockholm University |

## Design

Each of the three models of the 1 October virtual committees describes every member **from its own knowledge, without
web search**; Claude then merges the three answers into one profile, which is the committee profile used for the
member personas and their discussion.

```
roster.yaml ─► ask: claude-opus-5-5 ─┐
  (name, affiliation,  gpt-5.5-2026-04-23 ─┼─► merge: claude-opus-5-5 ─► profiles/<slug>.json, <slug>.md, ALL.md, index.csv
   role, title)        gemini-3.1-pro-preview ┘   (A / O / G support per item; works checked by title in code)
                       runs/<provider>/<slug>.json
```

| Stage | Calls | Prompt | Returns |
|---|---|---|---|
| ask | 1 per member × model; no tools; JSON schema | [`prompts/ask_system.md`](prompts/ask_system.md), [`prompts/ask_user.md`](prompts/ask_user.md) | identity check (recognized, confidence), **fields** (with JEL codes), **recent interests** (period, basis), up to 8 **representative works** (title, year, venue, coauthors, contribution, confidence), **persona** (summary, research lens, methods and evidence, what they value in contributions, questions they would raise, committee experience), knowledge limits |
| merge | 1 per member; no tools; JSON schema | [`prompts/merge_system.md`](prompts/merge_system.md), [`prompts/merge_user.md`](prompts/merge_user.md) | the same sections, every field, interest and work with `support` (A = Claude, O = OpenAI, G = Gemini) and conflicts; an integrated persona with a note where the models differ; disagreements; caveats |

Rules in the prompts: professional information only (no private life); accuracy over completeness, so a model that
does not recognize the person says so instead of guessing from the name; a work is listed only when the model is
confident the title exists; the persona is grounded in the person's record and does not predict whom the member will
support. The merge may use only what the three answers say.

**Checks in code.** Every answer and the merge must validate against its JSON schema (one retry on invalid JSON).
Support letters in the merge must belong to answers that exist (otherwise the merge is asked again, then recorded as
invalid). Every merged work is matched by title (normalised, similarity ≥ 0.85) against each model's own list: the
rendered badge is this checked support, a work that no model listed is marked ⚠, and a difference from the merge's
own claim is shown.

## Commands

```bash
cd "/project/jevans/Dawoon/Nobel Prize/Econ/01_committee"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY profiles.py roster
$PY profiles.py prompt --member john-hassler            # the exact question (free)
$PY profiles.py estimate                                # cost: logged calls, else assumptions
$PY profiles.py test --member john-hassler              # one member: three answers + merge (paid)
$PY profiles.py run                                     # every member (paid; valid records are kept)
$PY profiles.py run --members per-krusell --providers gemini --stages ask
$PY profiles.py merge --members john-hassler --force    # merge again
$PY profiles.py render && $PY profiles.py status
```

An existing valid record is never asked again unless `--force`; failed or invalid records are. Every call is logged
in `logs/calls.jsonl` (stage, member, model, seconds, tokens, USD).

## Outputs

| File | Content |
|---|---|
| `profiles/<slug>.md` | the committee profile: recognition by each model, persona, fields, recent interests, representative works with `[A O G]` badges, disagreements, caveats, each model's own persona summary and knowledge limits |
| `profiles/<slug>.json` | the same as data (`profile`, `per_model`, `inputs`, `stats`, the merge call record) |
| `profiles/ALL.md`, `profiles/index.csv` | all members on one page / one row per member (recognition, counts, works found by all three models, by one, by none) |
| `runs/<provider>/<slug>.json` | each model's answer with the prompt, settings and call record (not versioned) |

## Settings and cost

[`settings.yaml`](settings.yaml): answers with the provider-default effort (as the 1 October committee) and a 16,000
token cap; the merge on `claude-opus-5-5` at effort `high`; no tools, no sampling parameters, no model fallbacks.
44 calls in all (33 answers, 11 merges), about $5-7 by the assumptions in `settings.yaml`; `profiles.py estimate`
switches to the logged cost after the first calls.

## Known limits

- No web search: what a model knows stops at its training data, so recent roles and papers can be missing or
  outdated, and a model can confuse a less-known member with a namesake. The recognition flags, confidence fields,
  `[A O G]` badges and caveats show where to check.
- A work listed by all three models is likely real; a single-model work needs checking (for example against the
  person's OpenAlex record with `../../pipeline/profile_person.py`).
- The earlier web-search version of this step (built, tested offline, not run) is in `Old/websearch_2026-10-09/`.
