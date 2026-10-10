"""Generator of Econ/07_people_forecast/people_candidate_prompts.ipynb (step 7a). Run with the Curvature interpreter."""
from pathlib import Path
import nbformat as nbf

OUT = Path('/project/jevans/Dawoon/Nobel Prize/Econ/07_people_forecast/people_candidate_prompts.ipynb')
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip()))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip()))

md(r'''
# Step 7a: Preseen prompt for the people question — fields, candidate combinations and defining works

Step 7a of the Econ forecast (`../README.md`). This notebook writes the context notes that list, for each field of the
candidate pool, the **candidate combinations** (one to three people with the contribution a prize would recognize)
and their **defining works**. Source: the integrated candidate lists of step 6
(`../06_candidates/committee/<field>/integrated.json`: claude-opus-5-5's integration of the nominations of the
three-model virtual committee, run of 10 October 2026, 14:19-14:29 CDT).

- **Fields**: the five fields with the highest probability in the main arm of the latest field run (second experiment,
  task 9b0a6220): Macro, Trade, Production and IO, Public, law and political economy, Equilibrium and welfare.
- **Candidates per field**: the step-6 pool (`settings.yaml` `pool`, 30 in all, in proportion to the field probability:
  7/7/6/6/4), i.e. the leading candidates by committee support, without candidates whose lineup includes a previous
  laureate or a sitting committee member.
- **Notes** (upload order = name order; all for the `assume_true` treatment of the main arm):
  - `00_instruction`: the brief: goal, how to weigh the notes, eligibility, required output;
  - `01_field_forecast`: the latest field forecast (14 fields; the five of the pool rescaled to 100 %);
  - `02_age_and_timing`: the age record of the 99 laureates (step 5) and how to read the candidates' birth years;
  - `03_awarded_prizes`: every prize already awarded in the five fields, and the prizes of the other fields since 2000;
  - `11`-`15`: per field, the candidate combinations (people with birth years, contribution [JEL], defining works);
  - `21`-`25`: per field, the virtual committee's support (score, models, members, nominations, per-person support,
    other people named) and its reasoning including reservations.
- Not used: external signals (prediction markets, other prizes), as at the field stage; collaboration networks from the
  author-profile pipeline (considered on 10 October, dropped by the user for time).
- **Question** (section 3): `questions/people30.json`, 30 options = the pool, no "Other" (conditional, annulled
  if the prize goes to none of them, as in the field question and the science questions); a variant with "Other",
  `questions/people30_other.json`, is written for comparison. Submission: `run_people.sh` (not run here).
- **Eligibility screen** (not a note): `check_living_econ.py` looks up every shown person on Wikidata
  (`living_check.csv`), `living_overrides.yaml` records the manual decisions; deceased people are left out of the
  lineups and options and noted in the candidate and committee notes (section 1).
- Each note cell **prints the note exactly as it will be uploaded** and writes it to `context/<name>.md`. Nothing is
  uploaded by this notebook.
''')

code(r'''
import json
import re
import sys
import textwrap
from pathlib import Path

import pandas as pd
from IPython.display import display

ECON = Path('/project/jevans/Dawoon/Nobel Prize/Econ')
HERE = ECON / '07_people_forecast'
CAND = ECON / '06_candidates'
CONTEXT = HERE / 'context'
CONTEXT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(CAND))
import virtual_committee as vc   # read-only use: settings, the integrated lists and their staleness check (no API calls)

# Knobs
POOL = {f['slug']: f['pool'] for f in vc.ASKED}   # candidates per field (step-6 settings.yaml: 7/7/6/6/4)
MAX_WORKS = 4          # defining works per candidate (the integration returned at most 4)
ORDER = 'committee'    # 'committee' = order of committee support, as in the pool; 'alphabetical' = by the first person's surname
SHOW_BORN = True       # birth years in the people line (note 02 explains how to read them)
FIELD_PCT = True       # the field's probability (rescaled over the five) in the header of each candidate note
PROVENANCE = True      # one sentence on where the list comes from
AWARDED_OTHER_SINCE = 2000   # note 03: prizes of the other nine fields from this year on (all prizes of the five fields)
OTHERS_SHOWN = 5       # notes 21-25: candidates of the field that are not in the pool, listed in one line each

# Field labels of the field question (option text: "<field> (JEL ...): keywords")
FIELD_LABEL = {}
for opt in json.loads((ECON / '04_field_forecast/questions/fields14_nobel.json').read_text())['options']:
    FIELD_LABEL[opt.split(' (JEL')[0]] = opt

INT = {f['slug']: vc.load_integrated(f['slug']) for f in vc.ASKED}   # exits if the ballots changed after the integration

# Latest field forecast: main arm of the second field experiment (question title "... Nobel Prize in Economic Sciences")
FIELD_RUN = ECON / '04_field_forecast/preseen_exp/fields14_nobel/runs.csv'
_runs = pd.read_csv(FIELD_RUN)
_main = _runs[_runs.arm == 'main'].iloc[0]
_probs = json.loads(_main.forecast_data)['payload']['probabilities']
FIELD_P = pd.Series({k.split(' (JEL')[0]: v for k, v in _probs.items()}).sort_values(ascending=False)
FIELD_P = 100 * FIELD_P / FIELD_P.sum()
FIVE = [f['name'] for f in vc.ASKED]
FIELD_P5 = 100 * FIELD_P[FIVE] / FIELD_P[FIVE].sum()
assert list(FIELD_P.index[:5]) == FIVE, 'the five asked fields are no longer the top five of the latest field run'

import yaml
CFG = yaml.safe_load((ECON / 'config.yaml').read_text())
CUTOFF = CFG['today']                                        # information cutoff stated in the notes (config.yaml: today)
ANNOUNCEMENT = 'Monday 12 October 2026, 11:45 CEST at the earliest'
QUESTIONS = HERE / 'questions'
QUESTIONS.mkdir(exist_ok=True)
W = pd.read_csv(ECON / '04_field_forecast/results/prize_works_fields14.csv')   # 64 awarded works with field and consensus code
AGE_NOTE = (ECON / '05_laureates/prompt/01_age_at_award.md').read_text()
LIVING = HERE / 'living_check.csv'
OVERRIDES = yaml.safe_load((HERE / 'living_overrides.yaml').read_text()) if (HERE / 'living_overrides.yaml').exists() else {}
pd.set_option('display.max_colwidth', 90, 'display.width', 230, 'display.max_rows', 60)

WRITTEN = {}


def emit(name, text):
    # Print the note exactly as it will be uploaded and write it to context/<name>.md.
    text = textwrap.dedent(text).strip() + '\n'
    path = CONTEXT / f'{name}.md'
    path.write_text(text)
    WRITTEN[name] = len(text)
    print(text)
    print(f'--- written {path.relative_to(ECON)} ({len(text):,} characters)')


for old in CONTEXT.glob('*.md'):   # the notes are rebuilt from scratch on every run
    old.unlink()
print('fields:', ', '.join(f"{f['name']} ({POOL[f['slug']]})" for f in vc.ASKED), '| total', sum(POOL.values()))
print('integrated lists:', ', '.join(f"{s} {d['n_candidates']} candidates ({d['integrator']}, {d['generated'][:16]})" for s, d in INT.items()))
''')

md(r'''
## 1. The selected candidates (review table, not part of the prompt)

Selection = the rule of `virtual_committee.py pool --source claude`: candidates ranked by committee score; candidates
with an empty lineup or with a previous laureate or a sitting committee member in the lineup are skipped; the first
`POOL[field]` are kept. The table shows what the prompt leaves out (score of at most 15, models, members out of 11,
nominations, birth years, flags) so that the selection can be checked. The selection is compared with
`../06_candidates/results/pool.csv`.
''')

code(r'''
if LIVING.exists():
    LV = pd.read_csv(LIVING, dtype=str).fillna('')
    DIED = {r['name']: r['died'][:4] for _, r in LV.iterrows() if r['status'].startswith('DECEASED')}
    for name, ov in OVERRIDES.items():
        if ov['status'] == 'living':
            DIED.pop(name, None)
        else:
            DIED[name] = str(ov.get('died', ''))
    look = LV[~LV.status.str.startswith('living') | (LV.n != '1')].copy()
    look['decision'] = look.name.map(lambda n: f"{OVERRIDES[n]['status']} (override)" if n in OVERRIDES else '')
    print(f"living check ({LIVING.name}): {len(LV)} rows; Wikidata DECEASED {LV.status.str.startswith('DECEASED').sum()}; "
          f"rows to look at {len(look)}; manual decisions {len(OVERRIDES)}; deceased after review: "
          + ', '.join(f'{n} ({y})' for n, y in DIED.items()))
    display(look[['field', 'k', 'name', 'born_stated', 'status', 'qid', 'label', 'description', 'died', 'decision']])
else:
    print('living_check.csv missing: run check_living_econ.py first')
    DIED = {}
DECEASED = set(DIED)


def eligible(o):
    # lineup flags only: 'named in the nominations but cannot be awarded' (e.g. Krusell, left out of a lineup) does not disqualify
    fl = [x for x in o['flags'] if not x.startswith('named in the nominations')]
    alive = [p for p in o['people'] if p['name'] not in DECEASED]
    return bool(alive) and not any('already a laureate' in x or 'member of the 2026 committee' in x for x in fl)


def without_deceased(o):
    # a copy of the candidate: deceased lineup people -> people_dead, deceased other named people -> others_dead
    return {**o, 'people': [p for p in o['people'] if p['name'] not in DECEASED],
            'people_dead': [p for p in o['people'] if p['name'] in DECEASED],
            'others_dead': [p for p in o['people_others'] if p['name'] in DECEASED],
            'people_others': [p for p in o['people_others'] if p['name'] not in DECEASED]}


SELECTED = {s: [without_deceased(o) for o in d['candidates'] if eligible(o)][:POOL[s]] for s, d in INT.items()}

rows = []
for f in vc.ASKED:
    d = INT[f['slug']]
    for k, o in enumerate(SELECTED[f['slug']], 1):
        rows.append({'field': f['name'], 'k': k, 'committee rank': o['rank'], 'score': round(o['score'], 2), 'models': o['models'],
                     'members': o['n_members'], 'noms': o['n_nominations'],
                     'people (born)': '; '.join(f"{p['name']} ({p['born'] or '?'})" for p in o['people']),
                     'deceased (left out)': '; '.join(f"{p['name']} (d. {DIED[p['name']]})" for p in o['people_dead']),
                     'contribution': o['motivation'], 'works': len(o['defining_works']),
                     'flags': ' | '.join(fl for fl in o['flags'] if not fl.startswith('named in the nominations'))})
SEL = pd.DataFrame(rows)
display(SEL)

pool_csv = pd.read_csv(CAND / 'results/pool.csv')
same = (pool_csv['contribution'].tolist() == SEL['contribution'].tolist())
print('identical to ../06_candidates/results/pool.csv:', same)
assert same, 'selection differs from the step-6 pool; rerun `virtual_committee.py pool` or check the knobs'

tail = pd.DataFrame([{'field': INT[s]['field'], 'candidates': INT[s]['n_candidates'], 'selected': len(SELECTED[s]),
                      'share of the field score selected': round(sum(o['score'] for o in SELECTED[s]) / sum(o['score'] for o in INT[s]['candidates']), 2)}
                     for s in INT])
display(tail)
''')

md(r'''
## 2. The notes

### 00 Instruction
''')

code(r'''
N_OPT = sum(len(v) for v in SELECTED.values())
emit('00_instruction', f"""
# Instruction: forecasting the contribution and laureates of the 2026 Nobel Prize in Economic Sciences

Information cutoff: {CUTOFF}, before the announcement of the 2026 prize ({ANNOUNCEMENT}).

## Goal
For each of the {N_OPT} options, give the probability that the 2026 Sveriges Riksbank Prize in Economic Sciences in Memory
of Alfred Nobel recognizes the contribution the option names. Each option is a contribution in the style of an
official motivation with the one to three people most associated with it; the options come from the five fields that
the field forecast rated most likely (note 01). The question has no "Other" option: the forecast is conditional on the
prize going to one of the listed contributions, so the probabilities sum to 100 %.

## The notes
- 01: the field forecast. Use the rescaled field probabilities as the starting weight of each field's candidates as a
  group; move a field's total away from it only for stated reasons about its candidates.
- 11-15: the candidates of each field with the people (stated years of birth) and the defining works. Judge the
  importance, maturity and influence of each contribution from its defining works and your own knowledge of them, and
  mark what comes from your own knowledge.
- 03: the prizes already awarded. A contribution that is the same as, or a re-labelling of, an awarded one is
  unlikely; weigh the overlap of each candidate with recent prizes, including prizes in other fields.
- 21-25: the support and reasoning of a simulated committee (personas of the 2026 members on three language models).
  Treat it as one input on how the contributions might be seen, including the reservations it records; it is not
  evidence of the real committee's views, and its scores are not probabilities: do not copy them.
- 02: the age record. A person's age matters mostly at the extremes; the prize is never awarded posthumously and
  co-laureates are usually of one generation.

## Eligibility
The prize goes to at most three living people; previous laureates and sitting members of the 2026 committee cannot
be awarded. The notes flag people named by the committee who cannot be awarded and people aged 85 or more. The
living status of every person in the options was screened on Wikidata before submission; people named by the committee
who have died are noted in the candidate notes and are not part of the options.

## Required output
For each option: the probability, and the main grounds for and against it (contribution and its maturity, overlap with
awarded prizes, the field's weight, the people and their ages). Report the field totals of your distribution next to
the rescaled field forecast of note 01 and explain every field that moves by more than five percentage points. The
question resolves by contribution: the people named in an option need not match the laureates exactly.
""")
''')

md(r'''
### 01 Field forecast
''')

code(r'''
FIELD_NOTE_ROWS = '\n'.join(
    f"| {f} | {p:.1f} |" + (f" {FIELD_P5[f]:.1f} | {POOL[vc.FIELD_BY_NAME[f]['slug']]} |" if f in FIVE else " | |")
    for f, p in FIELD_P.items())
emit('01_field_forecast', f"""
# Field forecast for the 2026 Prize in Economic Sciences (Preseen, 10 October 2026)

The candidates in the notes that follow come from the five fields with the highest probability in the latest field
forecast: the treatment arm of the Preseen question "Which field of economics will the 2026 Nobel Prize in Economic
Sciences recognize?" (14 fields of economics defined by groups of JEL codes; forecast with nine context notes on the
award record, field rotation applied strongly; finished on 10 October 2026). The probabilities below are that
forecast's.

| field | probability (%) | rescaled over the five fields of the pool (%) | candidates in the pool |
|---|---|---|---|
{FIELD_NOTE_ROWS}

The five fields hold {FIELD_P[FIVE].sum():.1f} % of the field forecast. The number of candidates per field (30 in all) is
proportional to the rescaled probabilities. The field forecast is itself a forecast, not an observed fact; it is one
input for weighing the candidates of different fields against each other.
""")
''')

md(r'''
### 02 Age and timing
''')

code(r'''
age = re.sub(r'\s*\[(?:[SPDOM](?:, )?)+\]', '', AGE_NOTE).strip()     # the evidence tags of step 5 are not defined in these notes
emit('02_age_and_timing', age + """

Reading the candidates' birth years: the candidate notes give each person's year of birth as stated by the language
models of the virtual committee (the median over nominations); the years were not checked against an external source.
""")
''')

md(r'''
### 03 Prizes already awarded
''')

code(r'''
def award_line(r):
    return f'- {r.year} {r.laureates}: "{r.motivation}" [{r.jel}]'


blocks = []
for f in FIVE:
    g = W[W.field14 == f].sort_values(['year', 'group'])
    blocks.append(f"\n{f} ({len(g)} prize work{'s' if len(g) != 1 else ''}):\n" + '\n'.join(award_line(r) for r in g.itertuples()))
other = W[~W.field14.isin(FIVE) & (W.year >= AWARDED_OTHER_SINCE)].sort_values(['year', 'group'])
blocks.append(f"\nOther fields, {AWARDED_OTHER_SINCE}-2025:\n" + '\n'.join(f"{award_line(r)} ({r.field14})" for r in other.itertuples()))
emit('03_awarded_prizes', """
# Prizes already awarded: the five fields of the pool (1969-2025) and the other fields since """ + str(AWARDED_OTHER_SINCE) + """

Official motivations (nobelprize.org) with the consensus JEL code of the awarded work, as coded by three language
models for this forecast. A candidate whose contribution is the same as, or a re-labelling of, an awarded contribution
is unlikely to be recognized again; a distinct contribution in the same area is possible.
""" + '\n'.join(blocks))
''')

md(r'''
### 11-15 Candidates by field

The template is defined once; each field cell prints its note. Field line = the option label of the field question
(name, JEL codes, keywords) and the field's probability rescaled over the five fields. Candidate = the people of the
lineup with birth years (as written by the integration), the contribution in the style of an official motivation with
its JEL code, and the defining works (copied from the key works the nominations cite; "author(s), year: title, venue").
''')

code(r'''
PROVENANCE_TEXT = ('The {n} candidates below are combinations of one to three people with the contribution a prize would recognize. '
                   'They were nominated by a simulated committee (eleven personas reconstructed from the published research records of '
                   'the members of the 2026 prize committee, each asked on three language models without web access) and integrated '
                   'across the models; the defining works are the publications the nominations cite as establishing the contribution. '
                   'The list is a candidate set, not a statement of the real committee members\' views. Previous laureates and members '
                   'of the 2026 committee are not included; the living status of the people was screened on Wikidata, and people '
                   'named by the committee who have died are noted and left out of the lineups.')


def people_line(o):
    return ', '.join(f"{p['name']} (b. {p['born']})" if SHOW_BORN and p['born'] else p['name'] for p in o['people'])


def field_note(slug):
    f = vc.FIELD_BY_SLUG[slug]
    sel = SELECTED[slug]
    if ORDER == 'alphabetical':
        sel = sorted(sel, key=lambda o: vc.name_tokens(o['people'][0]['name'])[-1])
    lines = [f"# Candidates for the 2026 Prize in Economic Sciences: {f['name']}", '',
             f"Field: {FIELD_LABEL[f['name']]}." + (f" Field forecast: {FIELD_P5[f['name']]:.1f} % of the five fields of the pool (note 01)." if FIELD_PCT else ''), '']
    if PROVENANCE:
        lines += [PROVENANCE_TEXT.format(n=len(sel)), '']
    for i, o in enumerate(sel, 1):
        lines.append(f"{i}. {people_line(o)}")
        lines.append(f"   Contribution: {o['motivation']} [{o['jel_code']}]")
        for p in o['people_dead']:
            lines.append(f"   Note: {p['name']}, named by the committee for this contribution, died in {DIED[p['name']]} and is not eligible.")
        works = o['defining_works'][:MAX_WORKS]
        if works:
            lines.append('   Defining works:')
            lines += [f"   - {w['work']}" for w in works]
        lines.append('')
    return '\n'.join(lines)
''')

FIELD_CELLS = [('macro', 'Macro'), ('trade', 'Trade'), ('production_io', 'Production, Industrial Organization'),
               ('public', 'Public, Law, Political Economy'), ('equilibrium', 'Equilibrium, Welfare')]
for i, (slug, title) in enumerate(FIELD_CELLS, 1):
    md(f'#### {10 + i} {title}')
    code(f"emit('{10 + i}_candidates_{slug}', field_note('{slug}'))")

md(r'''
### 21-25 Committee support and reasoning by field

Per candidate, in the numbering of notes 11-15: the model-balanced Borda score (at most 15) with the points per model,
the models and members that nominated it, the number of nominations, for each person of the lineup the number of the
candidate's nominations that name them, other people named at least twice, notes on people named but not eligible, and
the committee's reasoning (written by the integration from the rationales of the nominations, including reservations).
Then the field's candidates that are not in the pool, in one line each.
''')

code(r'''
SUPPORT_HEAD = ('How to read: the virtual committee is the simulation described in the candidate notes. Each of its 33 '
                'ballots (11 personas x 3 models: A = claude-opus-5-5, O = gpt-5.5, G = gemini-3.1-pro) ranked up to five '
                'contributions in the field; rank 1 earns 5 points, rank 5 earns 1, each model\'s points are divided by its '
                'number of valid ballots and summed over the three models, so the score is at most 15 (every ballot of every '
                'model ranking the candidate first). Members = personas that nominated the candidate on at least one model. '
                'The reasoning summarizes the personas\' rationales, including their reservations; it is simulated, not the '
                'real committee\'s view.')


def support_note(slug):
    f = vc.FIELD_BY_SLUG[slug]
    d = INT[slug]
    sel = SELECTED[slug]
    if ORDER == 'alphabetical':
        sel = sorted(sel, key=lambda o: vc.name_tokens(o['people'][0]['name'])[-1])
    total = sum(o['score'] for o in d['candidates'])
    lines = [f"# Virtual committee support and reasoning: {f['name']}", '', SUPPORT_HEAD, '',
             f"{d['n_nominations']} nominations in this field, integrated into {d['n_candidates']} candidates; the {len(sel)} "
             f"candidates of the pool hold {100 * sum(o['score'] for o in sel) / total:.0f} % of the field's total score.", '']
    for i, o in enumerate(sel, 1):
        ppm = o['points_per_model']
        lines.append(f"{i}. {', '.join(p['name'] for p in o['people'])}: {o['motivation']}")
        lines.append(f"   Support: score {o['score']:.2f} of 15 (A {ppm[vc.MODEL['anthropic']]:.2f}, O {ppm[vc.MODEL['openai']]:.2f}, "
                     f"G {ppm[vc.MODEL['gemini']]:.2f}); {o['n_members']} of 11 members; {o['n_nominations']} nominations "
                     f"({', '.join(f'{k} {v}' for k, v in o['nominations_per_model'].items())})")
        lines.append('   Named in its nominations: ' + '; '.join(f"{p['name']} {p['n_nominations']}" for p in o['people'])
                     + ''.join(f"; also {p['name']} {p['n_nominations']}" for p in o['people_others'] if p['n_nominations'] >= 2))
        notes = [fl.replace('named in the nominations but cannot be awarded: ', '') for fl in o['flags'] if fl.startswith('named in the nominations')]
        notes += [f"{p['name']} (named in {p['n_nominations']}; died in {DIED[p['name']]})" for p in o['people_dead'] + o['others_dead']]
        if notes:
            lines.append('   Named but not eligible: ' + '; '.join(notes))
        lines.append(f"   Reasoning: {o['reasoning']}")
        lines.append('')
    in_pool = {o['nomination_ids'][0] for o in sel}
    rest = [without_deceased(o) for o in d['candidates'] if o['nomination_ids'][0] not in in_pool][:OTHERS_SHOWN]
    if rest:
        lines.append(f"Other candidates nominated in this field (not in the pool; the {OTHERS_SHOWN} with the highest score):")
        lines += [f"- {o['motivation']} ({', '.join(p['name'] for p in o['people']) or 'no eligible person'}): score "
                  f"{o['score']:.2f}, {o['n_members']} members" for o in rest]
    return '\n'.join(lines)
''')

for i, (slug, title) in enumerate(FIELD_CELLS, 1):
    md(f'#### {20 + i} {title}')
    code(f"emit('{20 + i}_committee_{slug}', support_note('{slug}'))")

md(r'''
## 3. Draft of the Preseen question

A multiple-choice question over the 30 candidates, in the format `nobel_preseen_exp.py create --question` reads.
Option = "<contribution> — <people> (<field>)". Resolution by contribution, as in the science questions of 1-7
October; no "Other" (conditional). The variant with "Other" makes the options comprehensive.
''')

code(r'''
OPTIONS = []
for f in vc.ASKED:
    for o in SELECTED[f['slug']]:
        OPTIONS.append(f"{o['motivation']} — {', '.join(p['name'] for p in o['people'])} ({f['name']})")
assert len(OPTIONS) == len(set(OPTIONS)) == N_OPT

question = {
    'type': 'multiple_choice',
    'title': 'Which contribution will the 2026 Nobel Prize in Economic Sciences be awarded for?',
    'description': (f'The 2026 Sveriges Riksbank Prize in Economic Sciences in Memory of Alfred Nobel is scheduled to be announced on '
                    f'{ANNOUNCEMENT}. Each option names a contribution, in the style of an official motivation, the people most closely '
                    'associated with it, and its field of economics. The forecast is conditional on the prize going to one of the listed '
                    'contributions; there is no "Other" option.'),
    'resolution_criteria': (
        'Resolves to the option whose contribution matches the contribution recognized by the official motivation of the 2026 Nobel Prize '
        'in Economic Sciences, as published at nobelprize.org. Options are matched by contribution; the people named in an option need not '
        'match the laureates exactly. If the prize is divided between two contributions, the contribution with the larger share counts; if '
        'the shares are equal, the contribution named first in the announcement counts. If more than one option matches, the option whose '
        'people include the most laureates counts, then the option that names the recognized contribution most specifically. If no option '
        'matches, the question is annulled (the forecast is conditional on one of the listed contributions).'),
    'fine_print': ('The options were built before the announcement from a candidate pool of five fields (Macro; Trade; Production and '
                   'industrial organization; Public economics, law and political economy; Equilibrium and welfare), with more options for '
                   'the fields with higher forecast probability. The field in brackets is informative only; resolution depends on the '
                   'contribution.'),
    'options': OPTIONS,
    'options_are_mutually_exclusive': True,
    'options_are_comprehensive': True,
}
(QUESTIONS / 'people30.json').write_text(json.dumps(question, indent=2, ensure_ascii=False) + '\n')
variant = dict(question,
               description=question['description'].replace('The forecast is conditional on the prize going to one of the listed '
                                                           'contributions; there is no "Other" option.',
                                                           'The last option, "Other", covers any contribution not listed.'),
               resolution_criteria=question['resolution_criteria'].replace(
                   'If no option matches, the question is annulled (the forecast is conditional on one of the listed contributions).',
                   'If no listed contribution matches, the question resolves to "Other".'),
               options=OPTIONS + ['Other: a contribution not listed above'])
(QUESTIONS / 'people30_other.json').write_text(json.dumps(variant, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k: v for k, v in question.items() if k != 'options'}, indent=2, ensure_ascii=False))
print(f'options ({len(OPTIONS)}):')
for i, o in enumerate(OPTIONS, 1):
    print(f'{i:>2}. {o}')
print('written:', QUESTIONS / 'people30.json', 'and', QUESTIONS / 'people30_other.json')
''')

md(r'''
## 4. Check

Sizes of the notes (earlier Preseen notes of this project: 1,200-9,000 characters), people who appear in more than one
candidate, and the points to settle before a question is created. Nothing is uploaded by this notebook.
''')

code(r'''
sizes = pd.Series(WRITTEN, name='characters').to_frame()
sizes['words'] = [len((CONTEXT / f'{n}.md').read_text().split()) for n in sizes.index]
assert sorted(p.stem for p in CONTEXT.glob('*.md')) == sorted(sizes.index)
display(sizes)
print(f"total {sizes.characters.sum():,} characters in {len(sizes)} notes; {sum(len(v) for v in SELECTED.values())} candidates")
dead_shown = [(f['name'], k, p['name']) for f in vc.ASKED for k, o in enumerate(SELECTED[f['slug']], 1) for p in o['people'] if p['name'] in DECEASED]
assert not dead_shown, 'a deceased person is still in a lineup'
print('deceased people left out of lineups:', '; '.join(f"{f['name']} #{k} {p['name']} (d. {DIED[p['name']]})" for f in vc.ASKED
      for k, o in enumerate(SELECTED[f['slug']], 1) for p in o['people_dead']) or 'none')
print('living check:', 'done (living_check.csv + living_overrides.yaml)' if LIVING.exists() else 'NOT RUN (living_check.csv missing)')
big = sizes[sizes.characters > 9000]
print('notes above 9,000 characters:', ', '.join(big.index) if len(big) else 'none')

multi = {}
for f in vc.ASKED:
    for k, o in enumerate(SELECTED[f['slug']], 1):
        for p in o['people']:
            multi.setdefault(vc.person_key(p['name']), []).append(f"{f['name']} #{k}")
multi = {k: v for k, v in multi.items() if len(v) > 1}
print('people in more than one candidate:', '; '.join(f'{k}: {", ".join(v)}' for k, v in multi.items()) or 'none')
old = [(f['name'], p['name'], p['born']) for f in vc.ASKED for o in SELECTED[f['slug']] for p in o['people'] if p['born'] and 2026 - p['born'] >= 85]
print('people aged 85 or more in 2026 (birth years as stated by the models):', '; '.join(f'{n} {b} ({fl})' for fl, n, b in old) or 'none')
print(textwrap.dedent(f"""
Submit (from this folder, PRESEEN_API_KEY in the environment; not done by this notebook): bash run_people.sh
  = create the private arms control (no notes) and main ({len(sizes)} notes of context/, assume_true, name order) from
    questions/people30.json, run one rep per arm, poll, write preseen_exp/people30/runs.csv.
"""))
''')

nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec': {'display_name': 'Python (Curvature)', 'language': 'python', 'name': 'curvature'},
                                                  'language_info': {'name': 'python'}})
nbf.write(nb, OUT)
print('written', OUT, len(cells), 'cells')
