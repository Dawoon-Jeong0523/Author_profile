#!/usr/bin/env python
"""Name -> OpenAlex author id -> dashboard + record, for anyone (Nobel laureate or not).

    python pipeline/profile_person.py "Geoffrey Hinton"                       # resolve, submit the Slurm job, return
    python pipeline/profile_person.py "Geoffrey Hinton" --wait                # ... and wait for the dashboard / record
    python pipeline/profile_person.py "Geoffrey Hinton" --dry-run             # only show the candidates and the choice
    python pipeline/profile_person.py "Geoffrey Hinton" --affiliation "University of Toronto"   # narrow down namesakes
    python pipeline/profile_person.py "Geoffrey Hinton" --pick 1              # take rank 1 of the printed table
    python pipeline/profile_person.py --author-id A5108093963                 # skip the name search
    python pipeline/profile_person.py --names-file people.txt --wait          # one name per line (optionally "name<TAB>affiliation")

Steps
1. Candidates: the 2026-01 OpenAlex snapshot's authors table and the live OpenAlex author search. A display name must agree
   with the query (same surname, first name equal or an initial, no conflicting middle initials); authors that agree only
   through an alternative name are listed but never chosen automatically. When the query names a PrizeAtlas Nobel laureate
   (Data/prizeatlas), the laureate's PrizeAtlas OpenAlex id and ORCID are candidates too.
2. Choice: ORCID (--orcid, or the laureate's) > the laureate's PrizeAtlas id > the only candidate at --affiliation > the
   most cited, if it has at least --dominance times the citations of the next candidate. Otherwise the table is printed
   and --pick / --author-id decides.
3. Fragments: other candidates with the same display name (case and accents ignored), at least 2 works, a shared
   institution word and no different ORCID are added (OpenAlex splits prolific people; --no-merge turns this off).
   The notebook's author id check also adds ids with the same ORCID.
4. Nobel labels: the prize year / field go into the file names only when the chosen author is linked to the laureate
   (a PrizeAtlas id or the laureate's ORCID); a namesake, or a name shared by several laureates, is profiled without
   them (files start with NA_NA_ unless --label-year / --label-field are given).
5. Run: notebook/author_profile.ipynb through jobs/author_profile.sbatch (Slurm; --local runs it in the current
   allocation instead) -> output/dashboard/<year>_<field>_<name>_<id>.html and output/record/<same name>.md.

Run it from the login node (the name search reads a 6 GB parquet with 4 threads, about 30 s); the profile itself runs on
a compute node (1-5 minutes per person once the shared caches exist). Exit status: 0 when every query was profiled
(resolved, with --dry-run; submitted, without --wait), 2 when a query needs a choice, 1 on any other failure.
"""
import argparse
import json
import os
import re
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
ACTIVE = {'PENDING', 'RUNNING', 'REQUEUED', 'REQUEUE_FED', 'REQUEUE_HOLD', 'RESIZING', 'SUSPENDED', 'CONFIGURING', 'COMPLETING', 'SIGNALING', 'STAGE_OUT'}


def laureate_by_name(name):
    """PrizeAtlas rows whose person has the same first + last name as the query (honorifics etc. removed, middle initials
    must not conflict); empty when the query has no first + last name."""
    if not name or not npc.prizeatlas_available():
        return pd.DataFrame()
    q = npc._clean_person(name)
    k = npc.name_key(q)
    if k is None:
        return pd.DataFrame()
    pa = npc.prizeatlas_table(['year', 'category_en', 'name', 'openalex_author_id', 'orcid', 'wikidata_qid', 'url'])
    clean = pa.name.map(npc._clean_person)
    hit = clean.map(lambda n: npc.name_key(n) == k and not npc.middle_conflict(n, q))
    return pa[hit.astype(bool)].sort_values('year')


def norm_author_id(a):
    """'A5108093963', '5108093963' or 'https://openalex.org/A5108093963' -> 'A5108093963'; ValueError otherwise."""
    s = str(a).strip().rstrip('/').rsplit('/', 1)[-1].upper()
    if re.fullmatch(r'\d+', s):
        s = 'A' + s
    if not re.fullmatch(r'A\d+', s):
        raise ValueError(f'not an OpenAlex author id: {a!r}')
    return s


def resolve(con, name, args, log=print):
    """(author_ids, labels, resolution text, needs_choice) for one query; author_ids is None when nothing is profiled."""
    nobel = laureate_by_name(name)
    laureate, several = None, False
    if len(nobel):
        if nobel.wikidata_qid.fillna(nobel.name).nunique() > 1:
            several = True
            who = '; '.join(dict.fromkeys(nobel.name + ' (' + nobel.category_en + ' ' + nobel.year.astype(str) + ', PrizeAtlas id '
                                          + nobel.openalex_author_id.fillna('-') + ')'))
            log(f'the name matches several Nobel laureates: {who}. No prize label is set; add a middle initial, --orcid or --author-id.')
        else:
            laureate = nobel
            log(f"Nobel laureate: {nobel.name.iloc[0]}, {', '.join(nobel.category_en + ' ' + nobel.year.astype(str))} (PrizeAtlas)")
    prize_ids = sorted({str(i).strip() for i in (laureate.openalex_author_id.dropna() if laureate is not None else []) if str(i).strip()})
    prize_orcid = laureate.orcid.dropna().iloc[0] if laureate is not None and laureate.orcid.notna().any() else None

    if args.author_id:
        ids = list(dict.fromkeys(norm_author_id(a) for a in args.author_id.split(';') if a.strip()))
        info = con.sql(f"""SELECT 'A' || CAST(author_id AS VARCHAR) AS author_id, display_name, orcid, works_count, cited_by_count
                           FROM read_parquet('{npc.OA_AUTHORS_PQ}') WHERE author_id IN ({', '.join(i[1:] for i in ids)})""").df()
        with pd.option_context('display.width', 200):
            log(info.to_string(index=False) if len(info) else 'none of the ids is in the 2026-01 snapshot (the notebook\'s id check looks them up)')
        miss = [i for i in ids if i not in set(info.author_id)]
        if len(info) and miss:
            log(f'not in the 2026-01 snapshot: {", ".join(miss)}')
        picked_orcids, why = set(info.orcid.dropna()), 'author id given'
        text = f'author id given: {";".join(ids)}'
    else:
        try:
            C = npc.find_author_candidates(con, name, affiliation=args.affiliation, orcid=args.orcid or prize_orcid,
                                           prize_ids=prize_ids, use_api=not args.no_api, log=log)
        except ValueError as e:                     # a single token, or initials only
            return None, {}, f'{e}; or use --author-id', False
        if C.empty:
            return None, {}, f'no OpenAlex author named like {name!r}: try another spelling (e.g. initials), --orcid or --author-id', False
        show = C.assign(rank=range(1, len(C) + 1), institutions=C.institutions.fillna('').str.slice(0, 60))
        with pd.option_context('display.width', 220, 'display.max_colwidth', 60):
            log(show[['rank', 'author_id', 'display_name', 'orcid', 'works_count', 'cited_by_count', 'match', 'affiliation_match',
                      'source', 'institutions']].to_string(index=False))
        if args.pick is not None:
            if not 1 <= args.pick <= len(C):
                return None, {}, f'--pick must be between 1 and {len(C)}', True
            row, why = C.iloc[args.pick - 1], f'--pick {args.pick}'
        else:
            row, why = npc.pick_author(C, dominance=args.dominance)
            if several and row is not None and not (row.orcid_match or row.affiliation_match):
                row, why = None, 'the name is shared by several Nobel laureates'
        if row is None:
            return None, {}, f'{why}. Choose with --pick N (the rank above), --affiliation, --orcid or --author-id.', True
        ids = [row.author_id] + ([] if args.no_merge else npc.same_person_fragments(C, row))
        picked_orcids = set(C.loc[C.author_id.isin(ids), 'orcid'].dropna())
        text = f'query {name!r}: picked {row.author_id} {row.display_name} [{why}]' + (f'; same-name fragments {", ".join(ids[1:])}' if len(ids) > 1 else '')

    # prize labels only when the profiled ids belong to the laureate the query names
    labels = {'NP_NOBEL_LOOKUP': 'ids'}
    if laureate is not None:
        if set(ids) & set(prize_ids) or (prize_orcid and prize_orcid in picked_orcids):
            labels = {'NP_PRIZE_YEAR': '-'.join(dict.fromkeys(laureate.year.astype(str))),
                      'NP_PRIZE_FIELD': '-'.join(dict.fromkeys(laureate.category_en)), 'NP_NOBEL_LOOKUP': 'auto'}
        else:
            log(f'WARNING: the chosen author is not linked to the laureate {laureate.name.iloc[0]} (neither the PrizeAtlas id '
                f'{", ".join(prize_ids) or "-"} nor the ORCID {prize_orcid or "-"}): profiled without prize labels')
    if args.label_year:
        labels['NP_PRIZE_YEAR'] = args.label_year
    if args.label_field:
        labels['NP_PRIZE_FIELD'] = args.label_field
    log(text)
    return ids, labels, text, False


def run(ids, labels, query, resolution, args, log=print):
    env = dict(os.environ, LD_LIBRARY_PATH=LD, NP_AUTHOR_ID=ids[0], NP_EXTRA_AUTHOR_IDS=';'.join(ids[1:]), NP_FETCH_TITLES='1',
               NP_TITLES_TABLE=args.titles, NP_QUERY=query or '', NP_RESOLUTION=resolution, NP_YEAR_MAX=str(args.year_max), **labels)
    out = NP / 'output' / ids[0]
    t0 = time.time()
    if args.local:
        out.mkdir(parents=True, exist_ok=True)
        cmd = [PY, '-m', 'jupyter', 'nbconvert', '--to', 'notebook', '--execute', '--ExecutePreprocessor.timeout=-1',
               '--ExecutePreprocessor.kernel_name=curvature', '--output', f'author_profile_{ids[0]}.ipynb', '--output-dir', str(out), str(NOTEBOOK)]
        log('running the notebook in this allocation ...')
        ok = subprocess.run(cmd, env=env, cwd=NP / 'notebook').returncode == 0
        return report(out, ok, log, since=t0)
    cmd = ['sbatch', '--parsable', '--export=ALL', f'--mem={args.mem}', f'--cpus-per-task={args.cpus}', f'--job-name=profile_{ids[0]}', str(SBATCH)]
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if p.returncode != 0:
        log(f'sbatch failed: {(p.stderr or p.stdout).strip()}')
        return {'job': None, 'ok': False, 'reason': 'sbatch failed'}
    job = p.stdout.strip().splitlines()[-1].split(';')[0]
    log(f'submitted Slurm job {job} for {ids} (log: jobs/logs/profile_{ids[0]}_{job}.out)')
    if not args.wait:
        return {'job': job, 'ok': True, 'status': 'submitted'}
    while True:
        st = subprocess.run(['sacct', '-j', job, '-X', '-n', '-P', '-o', 'State'], capture_output=True, text=True).stdout.split()
        state = st[0].split()[0] if st else ''
        if state and state not in ACTIVE:           # COMPLETED, FAILED, CANCELLED by ..., TIMEOUT, OUT_OF_MEMORY, NODE_FAIL, ...
            break
        time.sleep(20)
    if state != 'COMPLETED':
        log(f'job {job} ended {state}')
    return report(out, state == 'COMPLETED', log, job, since=t0)


def report(out, ok, log, job=None, since=None):
    man = out / 'manifest.json'
    if ok and (not man.exists() or (since and man.stat().st_mtime < since)):
        # the notebook's author id check may have moved the profile to another id (more works under the same ORCID)
        cands = [m for m in (NP / 'output').glob('A*/manifest.json') if since is None or m.stat().st_mtime >= since]
        cands = [m for m in cands if out.name in json.loads(m.read_text()).get('author_id_check', {}).get('input_ids', [])]
        man = max(cands, key=lambda m: m.stat().st_mtime) if cands else man
    if ok and man.exists() and (since is None or man.stat().st_mtime >= since):
        m = json.loads(man.read_text())
        log(f"dashboard: {NP / m['dashboard']}\nrecord:    {NP / m['record']}")
        return {'job': job, 'ok': True, 'dashboard': m['dashboard'], 'record': m['record']}
    log(f'the profile failed; see jobs/logs/profile_{out.name}_{job}.out' if job else 'the profile failed; see the notebook output')
    return {'job': job, 'ok': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('name', nargs='?', help='the person\'s name, e.g. "Geoffrey Hinton"')
    ap.add_argument('--affiliation', help='an institution of the person (narrows down namesakes)')
    ap.add_argument('--orcid', help='the person\'s ORCID')
    ap.add_argument('--author-id', help='OpenAlex author id(s), ";"-separated: skip the name search')
    ap.add_argument('--pick', type=int, help='take this rank of the candidate table (1 = first)')
    ap.add_argument('--dominance', type=float, default=3.0, help='automatic choice: citations of the top / the next candidate (default 3)')
    ap.add_argument('--no-merge', action='store_true', help='do not add same-name fragments of the chosen author')
    ap.add_argument('--no-api', action='store_true', help='snapshot candidates only (no live OpenAlex author search)')
    ap.add_argument('--label-year', help='first file-name part (default: the Nobel prize year when linked, else NA)')
    ap.add_argument('--label-field', help='second file-name part (default: the Nobel field when linked, else NA)')
    ap.add_argument('--year-max', type=int, default=2021, help='last publication / grant year analysed (default 2021)')
    ap.add_argument('--titles', default='api', help="'api' (default), a shared (id, title) parquet, or '' for the snapshot scan (205 GB)")
    ap.add_argument('--names-file', help='several people: one name per line, optionally "name<TAB>affiliation"; blank lines and # comments are skipped')
    ap.add_argument('--dry-run', action='store_true', help='only resolve: show the candidates and the choice')
    ap.add_argument('--local', action='store_true', help='run the notebook in this allocation instead of submitting a Slurm job')
    ap.add_argument('--wait', action='store_true', help='wait for the Slurm job and print the dashboard and record paths')
    ap.add_argument('--mem', default='64G'); ap.add_argument('--cpus', type=int, default=8)
    args = ap.parse_args()
    if not (args.name or args.author_id or args.names_file):
        ap.error('give a name, --author-id or --names-file')
    if args.names_file and (args.name or args.author_id or args.orcid or args.pick is not None or args.label_year or args.label_field):
        ap.error('--names-file takes per-person options from the file only: a name, --author-id, --orcid, --pick and --label-* '
                 'apply to a single person')
    os.environ['LD_LIBRARY_PATH'] = LD
    con = npc.duck(4, '6GB')
    queries = [(args.name, args.affiliation)]
    if args.names_file:
        queries = []
        for ln in open(args.names_file, encoding='utf-8'):
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            parts = [p.strip() for p in ln.rstrip('\n').split('\t')]
            if parts[0]:
                queries.append((parts[0], parts[1] if len(parts) > 1 and parts[1] else None))
    results, cli_aff = [], args.affiliation
    for name, aff in queries:
        print(f'\n=== {name or args.author_id}')
        args.affiliation = aff or cli_aff               # a file line's affiliation applies to that line only
        try:
            ids, labels, text, needs_choice = resolve(con, name, args)
        except ValueError as e:                          # a malformed --author-id
            ids, labels, text, needs_choice = None, {}, str(e), False
        if ids is None:
            print('NOT RESOLVED:', text)
            results.append({'query': name, 'ok': False, 'needs_choice': needs_choice, 'reason': text}); continue
        if args.dry_run:
            results.append({'query': name, 'ok': True, 'author_ids': ids, 'labels': labels}); continue
        results.append({'query': name, 'author_ids': ids, **run(ids, labels, name, text, args)})
    if len(results) > 1 or args.names_file:
        with pd.option_context('display.width', 220, 'display.max_colwidth', 80):
            print('\n' + pd.DataFrame(results).to_string(index=False))
    if all(r.get('ok') for r in results):
        sys.exit(0)
    sys.exit(2 if any(r.get('needs_choice') for r in results) else 1)


if __name__ == '__main__':
    main()
