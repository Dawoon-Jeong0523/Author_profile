#!/usr/bin/env python
"""Name -> OpenAlex author id -> dashboard + record, for anyone (Nobel laureate or not).

    python pipeline/profile_person.py "Geoffrey Hinton"                       # resolve, submit the Slurm job, return
    python pipeline/profile_person.py "Geoffrey Hinton" --wait                # ... and wait for the dashboard / record
    python pipeline/profile_person.py "James Evans" --affiliation "University of Chicago"   # narrow down namesakes
    python pipeline/profile_person.py "James Evans" --pick 2                  # take the 2nd candidate of the printed table
    python pipeline/profile_person.py --author-id A5076633756                 # skip the name search
    python pipeline/profile_person.py "Jennifer Doudna" --dry-run             # only show the candidates and the choice
    python pipeline/profile_person.py --names-file people.txt --wait          # one name per line (optionally "name<TAB>affiliation")

Steps
1. Candidates: the 2026-01 OpenAlex snapshot's authors table (display and alternative names) and the live OpenAlex author
   search; first + last name must agree with the query (initials allowed, middle initials must not conflict).
2. Choice: ORCID (--orcid) > the only candidate at --affiliation > the most cited, if it has at least --dominance times the
   citations of the next candidate. Otherwise the table is printed and --pick / --author-id decides.
3. Fragments: other candidates with the same full display name and a shared institution are added (OpenAlex splits
   prolific people; --no-merge turns this off). The notebook's author id check also adds ids with the same ORCID.
4. Nobel: a query that names a PrizeAtlas laureate (Data/prizeatlas) is labelled with the prize year / field; for anybody
   else the notebook matches prizes on ids and ORCID only (no name match), and the files start with NA_NA_ unless
   --label-year / --label-field are given.
5. Run: notebook/author_profile.ipynb through jobs/author_profile.sbatch (Slurm; --local runs it in the current
   allocation instead) -> output/dashboard/<year>_<field>_<name>_<id>.html and output/record/<same name>.md.

Run it from the login node (the name search reads a 6 GB parquet with 4 threads, about 30 s); the profile itself runs on
a compute node (1-5 minutes per person once the shared caches exist).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

NP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(NP / 'notebook'))
import pandas as pd            # noqa: E402
import np_common as npc        # noqa: E402

PY = '/project/jevans/Dawoon/env/Curvature/bin/python'
LD = '/project/jevans/Dawoon/env/Curvature/lib'
SBATCH = NP / 'jobs' / 'author_profile.sbatch'
NOTEBOOK = NP / 'notebook' / 'author_profile.ipynb'


def laureate_by_name(name):
    """PrizeAtlas rows whose person has the same first + last name as the query (honorifics etc. removed)."""
    if not npc.prizeatlas_available():
        return pd.DataFrame()
    pa = npc.prizeatlas_table(['year', 'category_en', 'name', 'openalex_author_id', 'orcid', 'url'])
    q = npc._clean_person(name)
    k = npc.name_key(q)
    m = pa[pa.name.map(lambda n: npc.name_key(npc._clean_person(n)) == k and not npc.middle_conflict(npc._clean_person(n), q)).astype(bool)]
    return m.sort_values('year')


def resolve(con, name, args, log=print):
    """(author_ids, labels, resolution text) for one query, or (None, ..., reason) when the user has to choose."""
    labels = {}
    nobel = laureate_by_name(name) if name else pd.DataFrame()
    if len(nobel):
        labels = {'NP_PRIZE_YEAR': '-'.join(dict.fromkeys(nobel.year.astype(str))),
                  'NP_PRIZE_FIELD': '-'.join(dict.fromkeys(nobel.category_en)), 'NP_NOBEL_LOOKUP': 'auto'}
        log(f"Nobel laureate: {nobel.name.iloc[0]}, {', '.join(nobel.category_en + ' ' + nobel.year.astype(str))} (PrizeAtlas)")
    else:
        labels = {'NP_NOBEL_LOOKUP': 'ids'}
    if args.label_year:
        labels['NP_PRIZE_YEAR'] = args.label_year
    if args.label_field:
        labels['NP_PRIZE_FIELD'] = args.label_field
    if args.author_id:
        ids = [a.strip() for a in args.author_id.split(';') if a.strip()]
        return ids, labels, f'author id given: {";".join(ids)}'
    orcid = args.orcid or (nobel.orcid.dropna().iloc[0] if len(nobel) and nobel.orcid.notna().any() else None)
    C = npc.find_author_candidates(con, name, affiliation=args.affiliation, orcid=orcid, use_api=not args.no_api, log=log)
    if C.empty:
        return None, labels, f'no OpenAlex author named like {name!r}: try another spelling (e.g. initials), --orcid or --author-id'
    show = C.assign(rank=range(1, len(C) + 1))[['rank', 'author_id', 'display_name', 'orcid', 'works_count', 'cited_by_count', 'source',
                                                 'affiliation_match', 'institutions']]
    with pd.option_context('display.width', 220, 'display.max_colwidth', 70):
        log(show.to_string(index=False))
    if args.pick:
        if not 1 <= args.pick <= len(C):
            return None, labels, f'--pick must be between 1 and {len(C)}'
        row, why = C.iloc[args.pick - 1], f'--pick {args.pick}'
    else:
        row, why = npc.pick_author(C, dominance=args.dominance)
    if row is None:
        return None, labels, f'{why}. Choose with --pick N (the rank above), --affiliation, --orcid or --author-id.'
    ids = [row.author_id] + ([] if args.no_merge else npc.same_person_fragments(C, row))
    text = f'query {name!r}: picked {row.author_id} {row.display_name} [{why}]' + (f'; same-name fragments {", ".join(ids[1:])}' if len(ids) > 1 else '')
    log(text)
    return ids, labels, text


def run(ids, labels, query, resolution, args, log=print):
    env = dict(os.environ, LD_LIBRARY_PATH=LD, NP_AUTHOR_ID=ids[0], NP_EXTRA_AUTHOR_IDS=';'.join(ids[1:]), NP_FETCH_TITLES='1',
               NP_TITLES_TABLE=args.titles, NP_QUERY=query or '', NP_RESOLUTION=resolution, NP_YEAR_MAX=str(args.year_max), **labels)
    out = NP / 'output' / ids[0]
    if args.local:
        out.mkdir(parents=True, exist_ok=True)
        cmd = [PY, '-m', 'jupyter', 'nbconvert', '--to', 'notebook', '--execute', '--ExecutePreprocessor.timeout=-1',
               '--ExecutePreprocessor.kernel_name=curvature', '--output', f'author_profile_{ids[0]}.ipynb', '--output-dir', str(out), str(NOTEBOOK)]
        log('running the notebook here: ' + ' '.join(cmd[:4]) + ' ...')
        t0 = time.time()
        ok = subprocess.run(cmd, env=env, cwd=NP / 'notebook').returncode == 0
        return report(out, ok, log, since=t0)
    t0 = time.time()
    cmd = ['sbatch', '--parsable', '--export=ALL', f'--mem={args.mem}', f'--cpus-per-task={args.cpus}', f'--job-name=profile_{ids[0]}', str(SBATCH)]
    job = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1].split(';')[0]
    log(f'submitted Slurm job {job} for {ids} (log: jobs/logs/profile_{ids[0]}_{job}.out)')
    if not args.wait:
        return {'job': job, 'author_id': ids[0]}
    while True:
        st = subprocess.run(['sacct', '-j', job, '-X', '-n', '-o', 'State'], capture_output=True, text=True).stdout.split()
        if st and st[0] in ('COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL'):
            break
        time.sleep(20)
    return report(out, st[0] == 'COMPLETED', log, job, since=t0)


def report(out, ok, log, job=None, since=None):
    man = out / 'manifest.json'
    if ok and (not man.exists() or (since and man.stat().st_mtime < since)):
        # the notebook's author id check may have moved the profile to another id (more works under the same ORCID)
        cands = [m for m in (NP / 'output').glob('A*/manifest.json') if since is None or m.stat().st_mtime >= since]
        cands = [m for m in cands if out.name in json.loads(m.read_text()).get('author_id_check', {}).get('input_ids', [])]
        man = max(cands, key=lambda m: m.stat().st_mtime) if cands else man
    if ok and man.exists():
        m = json.loads(man.read_text())
        log(f"dashboard: {NP / m['dashboard']}\nrecord:    {NP / m['record']}")
        return {'job': job, 'ok': True, 'dashboard': m['dashboard'], 'record': m['record']}
    log(f'the profile failed; see jobs/logs/*{job or ""}*.out' if job else 'the profile failed; see the notebook output')
    return {'job': job, 'ok': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('name', nargs='?', help='the person\'s name, e.g. "Geoffrey Hinton"')
    ap.add_argument('--affiliation', help='an institution of the person (narrows down namesakes)')
    ap.add_argument('--orcid', help='the person\'s ORCID')
    ap.add_argument('--author-id', help='OpenAlex author id(s), ";"-separated: skip the name search')
    ap.add_argument('--pick', type=int, help='take this rank of the candidate table')
    ap.add_argument('--dominance', type=float, default=3.0, help='automatic choice: citations of the top / the next candidate (default 3)')
    ap.add_argument('--no-merge', action='store_true', help='do not add same-name fragments of the chosen author')
    ap.add_argument('--no-api', action='store_true', help='snapshot candidates only (no live OpenAlex author search)')
    ap.add_argument('--label-year', help='first file-name part (default: Nobel prize year, else NA)')
    ap.add_argument('--label-field', help='second file-name part (default: Nobel field, else NA)')
    ap.add_argument('--year-max', type=int, default=2021, help='last publication / grant year analysed (default 2021)')
    ap.add_argument('--titles', default='api', help="'api' (default), a shared (id, title) parquet, or '' for the snapshot scan (205 GB)")
    ap.add_argument('--names-file', help='several people: one name per line, optionally "name<TAB>affiliation"')
    ap.add_argument('--dry-run', action='store_true', help='only resolve: show the candidates and the choice')
    ap.add_argument('--local', action='store_true', help='run the notebook in this allocation instead of submitting a Slurm job')
    ap.add_argument('--wait', action='store_true', help='wait for the Slurm job and print the dashboard and record paths')
    ap.add_argument('--mem', default='64G'); ap.add_argument('--cpus', type=int, default=8)
    args = ap.parse_args()
    if not (args.name or args.author_id or args.names_file):
        ap.error('give a name, --author-id or --names-file')
    os.environ['LD_LIBRARY_PATH'] = LD
    con = npc.duck(4, '6GB')
    queries = [(args.name, args.affiliation)]
    if args.names_file:
        queries = [tuple((ln.rstrip('\n').split('\t') + [None])[:2]) for ln in open(args.names_file) if ln.strip() and not ln.startswith('#')]
    results, cli_aff = [], args.affiliation
    for name, aff in queries:
        print(f'\n=== {name or args.author_id}')
        args.affiliation = aff or cli_aff               # a file line's affiliation applies to that line only
        ids, labels, text = resolve(con, name, args)
        if ids is None:
            print('NOT RESOLVED:', text); results.append({'query': name, 'ok': False, 'reason': text}); continue
        if args.dry_run:
            results.append({'query': name, 'author_ids': ids, 'labels': labels}); continue
        results.append({'query': name, 'author_ids': ids, **run(ids, labels, name, text, args)})
    if len(results) > 1 or args.names_file:
        print('\n' + pd.DataFrame(results).to_string(index=False))


if __name__ == '__main__':
    main()
