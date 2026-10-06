# 30 options per field, v2: people = the committee lineup with the highest mean score

v2 of `../convergence_2026/` (v1 is unchanged). Built 2026-10-06 for medicine, physics and chemistry.

```
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY build_options_v2.py          # results/options_<field>.json/.csv, review_<field>.md
$PY compare_v1_v2.py             # results/compare_<field>.csv, compare.md
```

## What changes from v1

Only the people shown on an option the committee named.

- **v1:** the people of all nominations merged into the option are pooled, ranked by committee weight + convergence
  points, and the top three are shown. A single nomination that names three people fills the slots even when most
  nominations name one person (2026 physics: Halzen alone in 2 of 4 nominations, shown as Halzen, Karle, Kurahashi
  Neilson).
- **v2:** the candidates are the lineups the committee members actually wrote (the set of people of one nomination;
  identical sets are one lineup). Deceased people are removed from a lineup. A person scores committee weight +
  convergence points, a lineup scores the mean over its people, and the highest mean is shown. Ties: the summed
  normalized Borda points of the nominations that wrote the lineup ("support"), then the number of those nominations,
  then the names. The user's hand picks in the committee's `merges.yaml` (tie decisions of 2026-10-01) break a tie in
  mean score when they are one of the tied lineups (chemistry DNA origami).

Everything else is v1: the committee part (`../preseen/committee.py`, `merges.yaml`), the convergence voters, placement
of convergence people, eligibility, option score (committee points + convergence points of the people shown), ranking.

Consequences to keep in mind:

- A convergence person placed in a committee option (name match, attach, milestone) is shown only if a committee
  lineup holds them; otherwise the person is flagged and their points do not count (physics: Preskill, so quantum error
  correction drops from 11 to 18).
- The mean favours a small lineup of the top-weighted people: a lineup that is a subset of a larger one always has a
  higher or equal mean when the extra people weigh less. One nomination can therefore win against most of them
  (physics topological insulators: Kane, Mele from 3 % of the support against Kane, Mele, Molenkamp from 97 %). The
  plurality lineup (most support) is reported next to the choice in `review_<field>.md` and `compare_<field>.csv`.

## Files

| File | What |
|---|---|
| `build_options_v2.py` | the v2 pipeline (self-contained copy of v1 with the lineup rule) |
| `decisions.yaml` | physics and chemistry copied unchanged from v1; **medicine section new (drafted by Claude 2026-10-06, to check)** |
| `compare_v1_v2.py` | v1 and v2 built in memory with the same decisions; checks v1 against the saved v1 lists |
| `results/options_<field>.*` | the 30 options; the JSON lists every candidate lineup with mean score and support |
| `results/review_<field>.md` | table, per option detail with all lineups (→ = shown), flags, weight sensitivity |
| `results/compare.md`, `compare_<field>.csv` | v1 vs v2 per field: people per option, changed lineups, plurality lineup |

## Cards

`cards_pipeline_v2.py` (missing / dryrun / identity / living / submit / cards / check) makes a profile card for every
person shown in the v1 lists (`results/v1_rule/`, written by `compare_v1_v2.py`) and the v2 lists of all three fields:
`cards/<v1|v2>/<field>/`, `cards/index.csv`. Same steps and card template as `../convergence_2026/cards_pipeline.py`.
Identities: this folder's `people/` (new people of 2026-10-06, hand choices in `people/<field>_choices.yaml`), then
`../convergence_2026/people/` (with `overrides.yaml`), then `../preseen/people/`; across fields only when the
given-name initials agree (C. Frank Bennett is not Charles H. Bennett). `people/living_notes.yaml` lists Wikidata false
matches. `dryrun.sbatch` runs the name search on a compute node.

## Age-25 cards (chemistry)

`cards_age25_v2.py` (births / pools / reference / merge-picks / cards / check, `--field chemistry`) builds the age-25 cards
of ../convergence_2026/cards_age25.py (imported unchanged; folders and lists repointed) for the three chemistry lists
(v1, v2, Preseen's): `cards_age25/<v1|v2|preseen>/chemistry/`, 169 cards for 92 people. Births: Wikidata via
`people/living_check.csv`, else `people/births_overrides.yaml` (hand-checked; 8 estimated from the education record;
Wikidata was wrong for Brangwynne, Ritala and Winkler). Defining works: 8 LLM agents over `cards_age25/_work/pool_files/`
(`_work/picks/batch_*.yaml`; batch_9 = Claude's picks for the three re-pooled people), merged and checked by
`merge-picks` into `cards_age25/defining_works_chemistry.yaml`. Laureate reference: `laureate_reference_age25_chemistry.csv`
(61; the imported cmd_reference stops on Sharpless' duplicate author id after writing the file).

## Patents tied to the discovery (chemistry cards)

`patent_section.py` (pools / merge / apply, `--field chemistry`) adds a "Patents tied to the discovery" section to every
chemistry card (standard and age-25): up to three of the person's US utility patents granted up to 2021 most tied to the
discovery of the person's option(s), with filing and grant years, first assignee and the number of later US patents
citing them, and how many of the person's patents relate to the discovery. Chosen by 6 LLM agents from all the person's
patents (`cards_age25/_work/patent_pools/`, `_work/patent_picks/batch_*.yaml`), merged and checked into
`cards_age25/patents_tied_chemistry.yaml`. Why: inventions disclosed mainly in patents (sequencing-by-synthesis) had no
discovery evidence on the cards. `apply` is idempotent; run it again after rebuilding cards. The agents' notes flag
namesake patents in some records (Tao Zhang, Makoto Fujita, Nam-Gyu Park, Mark E. Thompson, Wolfgang A. Herrmann).

Medicine had no v1 30-option list. Its new options (OCT, CFTR modulators, MeCP2, TGF-β receptors and seven single
people) and two attachments (Moskowitz to CGRP, Saper to orexin) are Claude's drafts in `decisions.yaml`.
