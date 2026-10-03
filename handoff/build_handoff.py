"""Rebuild the data files of handoff/ from the experiment folders and the profile outputs.

    LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib /project/jevans/Dawoon/env/Curvature/bin/python handoff/build_handoff.py

context/   what the forecaster was given, one unit per line, so pieces can be fed in or left out one at a time
    questions/<field>.json           the question as posted (the same file in every condition)
    definitions.jsonl                the definitions note of each field (3)
    profile_cards_used_in_runs.jsonl the cards as posted in the October runs (98)
    profile_cards_current.jsonl      the same cards rebuilt on 3 October (98; only patent lines differ)
    instruction_notes.jsonl          the two instruction notes (main evidence, one main source)
    conditions.json                  which of these each condition posted, in which order, with which treatment
    records/                         the long, agent-readable record of each person, and index.csv
forecasts/ what Preseen returned
    runs.csv                         probability of every option in every run (ids left out)
    subforecasts.csv                 the same for each of the 4 subforecasts of a run
    writeups.jsonl                   Preseen's write-up and subforecast write-ups of every run
    by_condition.csv                 mean probability and rank of every option per condition
results.md                           the by_condition tables, readable
"""
import csv
import json
import random
import shutil
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
EXP = REPO / 'experiment'
sys.path.insert(0, str(EXP / 'preseen'))
import build_cards as bc  # noqa: E402  (person_slug, find_profile)

FIELDS = ['medicine', 'physics', 'chemistry']
CONDITION = {'control': 'control', 'cards': 'cards_as_context', 'balanced': 'cards_one_main_source', 'main': 'cards_main_evidence'}
ARMS = [('control', 'control_mean'), ('cards_as_context', 'cards_mean'), ('cards_one_main_source', 'balanced_p'),
        ('cards_main_evidence', 'main_p')]
SEED = 2026          # nobel_preseen_exp.py add-context: 00_* first, the rest shuffled with random.Random(2026)
CTX, FC = HERE / 'context', HERE / 'forecasts'


def jsonl(path, rows):
    with open(path, 'w') as fh:
        fh.writelines(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)


def records():
    """context/records/: the record of every candidate (output/record/, current pipeline) and index.csv."""
    (CTX / 'records').mkdir(parents=True, exist_ok=True)
    rows = []
    for f in FIELDS:
        options = {}
        for o in json.loads((EXP / 'preseen' / 'committee' / f / 'candidates.json').read_text())['options']:
            for p in o.get('people', []):
                options.setdefault(p['name'], []).append(str(o['rank']))
        for r in csv.DictReader(open(EXP / 'preseen' / 'people' / f'{f}_identity.csv')):
            man = json.loads((bc.find_profile(r['openalex_ids'].split(';')) / 'manifest.json').read_text())
            rec = REPO / man['record']
            shutil.copy2(rec, CTX / 'records' / rec.name)
            slug = bc.person_slug(r['person'])
            rows.append({'field': f, 'option': ';'.join(options.get(r['person'], [])), 'person': r['person'],
                         'openalex_author_ids': ';'.join(man['author_id_check']['author_ids']), 'record': rec.name,
                         'card_file': f'{slug}.md', 'prior_nobel': r['prior_nobel']})
    idx = pd.DataFrame(rows)
    idx.to_csv(CTX / 'records' / 'index.csv', index=False)
    return idx


def context(idx):
    (CTX / 'questions').mkdir(parents=True, exist_ok=True)
    for f in FIELDS:
        shutil.copy2(EXP / 'preseen' / 'questions' / f'{f}.json', CTX / 'questions' / f'{f}.json')
    defs = [{'id': f'definitions-{f}', 'field': f, 'treatment': 'consider',
             'source_file': f'experiment/preseen/cards_v1/{f}/00_definitions.md',
             'text': (EXP / 'preseen' / 'cards_v1' / f / '00_definitions.md').read_text()} for f in FIELDS]
    jsonl(CTX / 'definitions.jsonl', defs)
    for name, folder in (('profile_cards_used_in_runs.jsonl', 'cards_v1'), ('profile_cards_current.jsonl', 'cards')):
        out = []
        for f in FIELDS:
            rest = sorted(c for c in (EXP / 'preseen' / folder / f).glob('*.md') if not c.name.startswith('00_'))
            random.Random(SEED).shuffle(rest)
            who = {r.card_file: r for r in idx[idx.field == f].itertuples()}
            for k, c in enumerate(rest, 1):
                r = who[c.name]
                out.append({'id': f'{f}-{c.stem}', 'field': f, 'order': k, 'person': r.person,
                            'options': [int(x) for x in r.option.split(';') if x],
                            'openalex_author_ids': r.openalex_author_ids.split(';'), 'treatment': 'consider',
                            'source_file': str(c.relative_to(REPO)), 'text': c.read_text()})
        jsonl(CTX / name, out)
    instr = [{'id': cid, 'condition': cid, 'treatment': 'assume_true', 'source_file': str(p.relative_to(REPO)), 'text': p.read_text()}
             for cid, p in (('cards_main_evidence', EXP / 'preseen_cards_main' / 'instruction' / '00_instruction.md'),
                            ('cards_one_main_source', EXP / 'preseen_cards_balanced' / 'instruction' / '00_instruction.md'))]
    jsonl(CTX / 'instruction_notes.jsonl', instr)
    cards = {'file': 'profile_cards_used_in_runs.jsonl', 'select': 'same field, by order', 'treatment': 'consider'}
    definitions = {'file': 'definitions.jsonl', 'select': 'same field', 'treatment': 'consider'}
    recipe = {
        'note': 'Notes are posted to the question in the order listed; a note stays on the question for every later run. '
                'Every condition used the same question file (questions/<field>.json).',
        'conditions': {
            'control': {'notes': [], 'runs_per_field': 5, 'dates': '4 runs on 2026-10-01, 1 on 2026-10-02'},
            'cards_as_context': {'notes': [definitions, cards], 'runs_per_field': 3, 'dates': '2026-10-01'},
            'cards_one_main_source': {'notes': [{'file': 'instruction_notes.jsonl', 'select': 'id = cards_one_main_source',
                                                 'treatment': 'assume_true'}, definitions, cards],
                                      'runs_per_field': 1, 'dates': '2026-10-02'},
            'cards_main_evidence': {'notes': [{'file': 'instruction_notes.jsonl', 'select': 'id = cards_main_evidence',
                                               'treatment': 'assume_true'}, definitions, cards],
                                    'runs_per_field': 1, 'dates': '2026-10-02'}}}
    (CTX / 'conditions.json').write_text(json.dumps(recipe, indent=1) + '\n')


def option_texts():
    out = {}
    for f in FIELDS:
        for k, o in enumerate(json.loads((EXP / 'preseen' / 'questions' / f'{f}.json').read_text())['options'], 1):
            out[(f, k)] = o if isinstance(o, str) else o.get('text', str(o))
    return out


def forecasts():
    FC.mkdir(exist_ok=True)
    opt = option_texts()
    runs, subs, writes = [], [], []
    for f in FIELDS:
        r = pd.read_csv(EXP / 'preseen_cards_main' / 'results' / f / 'runs_long.csv')
        runs.append(pd.DataFrame({'field': f, 'condition': r.arm.map(CONDITION), 'run': r.rep, 'date': r.created_at.str[:10],
                                  'created_at_utc': r.created_at, 'option': r.option, 'probability': r.p}))
        s = pd.read_csv(EXP / 'preseen_cards_main' / 'results' / f / 'subforecasts.csv')
        subs.append(pd.DataFrame({'field': f, 'condition': s.arm.map(CONDITION), 'run': s.rep, 'subforecast': s['sub'] + 1,
                                  'option': s.option, 'probability': s.p}))
        for w in json.loads((EXP / 'preseen_cards_main' / 'results' / f / 'writeups.json').read_text()):
            writes.append({'field': f, 'condition': CONDITION[w['arm']], 'run': w['rep'], 'created_at_utc': w['created_at'],
                           'write_up': w['write_up'], 'subforecast_write_ups': w['sub_write_ups']})
    R = pd.concat(runs, ignore_index=True)
    R.insert(6, 'option_text', [opt[(f, o)] for f, o in zip(R.field, R.option)])
    R.to_csv(FC / 'runs.csv', index=False)
    pd.concat(subs, ignore_index=True).to_csv(FC / 'subforecasts.csv', index=False)
    jsonl(FC / 'writeups.jsonl', writes)
    frames = []
    for f in FIELDS:
        e = pd.read_csv(EXP / 'preseen_cards_main' / 'results' / f / 'effects.csv')
        named = e.option_text.str.strip() != 'Other'
        parts = e.option_text.str.split(' — ', n=1, expand=True)
        t = pd.DataFrame({'field': f, 'option': e.option, 'discovery': parts[0].str.strip(), 'people': parts[1].fillna('').str.strip()})
        for arm, col in ARMS:
            t[f'p_{arm}'] = e[col].round(6)
            t[f'rank_{arm}'] = e.loc[named, col].rank(ascending=False, method='min').astype('Int64').reindex(e.index)
        t['p_control_min'], t['p_control_max'] = e.control_min.round(6), e.control_max.round(6)
        frames.append(t.sort_values(['rank_control', 'option'], na_position='last'))
    pd.concat(frames).to_csv(FC / 'by_condition.csv', index=False)


def pct(x):
    return '' if pd.isna(x) else f'{100 * x:.1f}'


def results_md():
    """results.md: forecasts/by_condition.csv as Markdown tables, and how far each condition moved the forecast."""
    body = ['# Results by condition', '',
            'The probability Preseen gave each option under each condition, in percent. Control is the mean of 5 runs',
            '(4 on 1 October, 1 on 2 October), cards as context the mean of 3 runs on 1 October; the two note conditions',
            'are single runs on 2 October. The rank (in brackets) is among the 12 named options; "Other" has none, though it',
            'is the largest single entry under every condition. Unrounded values: `forecasts/by_condition.csv`; every run:',
            '`forecasts/runs.csv`.', '',
            'The two note conditions have one run per field, so their numbers carry the run-to-run noise shown below. All',
            'comparisons are descriptive; no significance tests. Log scores against the actual prizes (announced 5-7',
            'October) are not computed yet.', '',
            '## How far each condition moved the forecast', '',
            'For one run, the average distance of each option from the mean of the control runs, in percentage points. For a',
            'control run the comparison is with the mean of the other control runs, so the first column is how much the',
            'forecast moves when nothing changes.', '',
            '| Field | Control run | Cards as context | Cards as one main source | Cards as the main evidence |',
            '|---|---:|---:|---:|---:|']
    n_rows = []
    for f in FIELDS:
        s = json.loads((EXP / 'preseen_cards_main' / 'results' / f / 'summary.json').read_text())
        dev = {a: sum(v) / len(v) for a, v in s['single_run_dev'].items()}
        body.append(f"| {f.capitalize()} | {100 * dev['control']:.2f} | {100 * dev['cards']:.2f} | "
                    f"{100 * dev['balanced']:.2f} | {100 * dev['main']:.2f} |")
        n_rows.append(f"| {f.capitalize()} | {s['cards']['options_outside_control_range']} | "
                      f"{s['balanced']['options_outside_control_range']} | {s['main']['options_outside_control_range']} |")
    body += ['', 'Options (of 13) whose probability falls outside the range of the control runs:', '',
             '| Field | Cards as context | Cards as one main source | Cards as the main evidence |', '|---|---:|---:|---:|'] + n_rows
    t = pd.read_csv(FC / 'by_condition.csv')
    for f in FIELDS:
        body += ['', f'## {f.capitalize()}', '',
                 '| # | Discovery | People named | Control | Control range | Cards as context | Cards as one main source | Cards as the main evidence |',
                 '|---:|---|---|---:|---:|---:|---:|---:|']
        for r in t[t.field == f].itertuples():
            def cell(a):
                p, k = getattr(r, f'p_{a}'), getattr(r, f'rank_{a}')
                return pct(p) + ('' if pd.isna(k) else f' ({int(k)})')
            body.append(f'| {r.option} | {r.discovery} | {"" if pd.isna(r.people) else r.people} | {cell("control")} | '
                        f'{pct(r.p_control_min)}–{pct(r.p_control_max)} | {cell("cards_as_context")} | '
                        f'{cell("cards_one_main_source")} | {cell("cards_main_evidence")} |')
    (HERE / 'results.md').write_text('\n'.join(body) + '\n')


if __name__ == '__main__':
    for old in ('sdk', 'results', 'records'):                       # earlier layout of this folder
        shutil.rmtree(HERE / old, ignore_errors=True)
    idx = records()
    context(idx)
    forecasts()
    results_md()
    print('handoff rebuilt:', ', '.join(str(p.relative_to(HERE)) for p in sorted(HERE.rglob('*')) if p.is_file() and 'records/' not in str(p)))
