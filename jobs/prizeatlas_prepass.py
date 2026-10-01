"""Pre-pass of the PrizeAtlas dashboard batch (jobs/prizeatlas_dashboards.sbatch).

1. targets: one row per OpenAlex author id of the PrizeAtlas Nobel laureates (Data/prizeatlas), with its works in the 2026-01
   snapshot, spread over the array tasks by expected load (largest first, round robin) -> output/batch_prizeatlas/targets.tsv
2. the works of the target ids, of the ids that share their ORCID and of the Li et al. bridge ids (one authorship scan)
3. their titles from the snapshot's works table (one scan) -> cache/titles_prizeatlas.parquet (id, title), read by the
   notebook through NP_TITLES_TABLE instead of a 205 GB scan per author
4. titles of the works missing from the snapshot from the OpenAlex API -> cache/openalex_api_titles.parquet
"""
import json
import os
import sys
import time

sys.path.insert(0, '/project/jevans/Dawoon/Nobel Prize/notebook')
import numpy as np
import pandas as pd
import np_common as npc

N_TASKS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
B = npc.NP / 'output' / 'batch_prizeatlas'
B.mkdir(parents=True, exist_ok=True)
TITLES_PQ = npc.CACHE / 'titles_prizeatlas.parquet'
t0 = time.time()
con = npc.duck()
log = {}

W = npc.prizeatlas_table()
W['aid'] = W.openalex_author_id.fillna('').str.split(';').str[0].str.strip().replace('', np.nan)
print('pages without an OpenAlex id (not profiled):', W[W.aid.isna()][['name', 'year', 'category_en']].to_dict('records'))
P = (W.dropna(subset=['aid']).sort_values('year')
     .groupby('aid').agg(name=('name', 'first'), people=('person_key', 'nunique'), prizes=('year', lambda s: ''),
                         orcid=('orcid', 'first'), url=('url', 'first')).reset_index())
P['prizes'] = P.aid.map(W.dropna(subset=['aid']).assign(p=lambda x: x.category_en + ' ' + x.year.astype(str)).groupby('aid').p.agg('; '.join))
print(f'{len(P)} distinct author ids for {W.person_key.nunique()} people; ids on several people: {P[P.people > 1][["aid", "prizes"]].to_dict("records")}')

A = f"read_parquet('{npc.OA_AUTHORS_PQ}')"
con.register('tids', pd.DataFrame({'author_id': P.aid.str[1:].astype('int64')}))
wc = con.sql(f'SELECT author_id, works_count, orcid FROM {A} WHERE author_id IN (SELECT author_id FROM tids)').df()
P['works_count'] = P.aid.str[1:].astype('int64').map(wc.set_index('author_id').works_count).fillna(0).astype(int)
log['ids_without_snapshot_works'] = int((P.works_count < 5).sum())
print(f"ids with fewer than 5 works in the snapshot (resolved by the notebook's id check): {log['ids_without_snapshot_works']}")

# candidate ids for the titles: target ids, same-ORCID ids, Li et al. bridge ids
orc = sorted(set(P.orcid.dropna()) | set(wc.orcid.dropna()))
sib = con.sql(f'SELECT author_id FROM {A} WHERE orcid IN ({npc.sql_list(orc)}) AND works_count > 0').df().author_id if orc else pd.Series(dtype='int64')
bridge = pd.Series(dtype='int64')
if npc.PRIZEATLAS_LINK.exists() and npc.LAUREATE_BRIDGE.exists():
    lk = pd.read_csv(npc.PRIZEATLAS_LINK, usecols=['LaureateID', 'url']).dropna()
    br = pd.read_csv(npc.LAUREATE_BRIDGE, usecols=['LaureateID', 'primary_author_id'], dtype={'primary_author_id': str}).dropna()
    bridge = br[br.LaureateID.isin(lk.LaureateID)].primary_author_id.str[1:].astype('int64')
cand = sorted(set(P.aid.str[1:].astype('int64')) | set(sib.astype('int64')) | set(bridge))
log['candidate_author_ids'] = len(cand)
con.register('cand', pd.DataFrame({'author_id': pd.Series(cand, dtype='int64')}))
t1 = time.time()
works = con.sql(f'''SELECT DISTINCT work_id FROM read_parquet('{npc.AUTHORSHIPS}/bucket=*/*.parquet', hive_partitioning = true)
                    WHERE author_id IN (SELECT author_id FROM cand)''').df()
ids = pd.DataFrame({'id': ('W' + works.work_id.astype('int64').astype(str)).astype('string')})
log['works'] = len(ids); log['authorship_scan_s'] = round(time.time() - t1)
print(f'{len(cand)} candidate author ids -> {len(ids):,} works ({time.time() - t1:.0f}s)')

t1 = time.time()
con.register('wids', ids)
titles = con.sql(f'''SELECT id, any_value(title) AS title FROM read_parquet('{npc.OA_RAW}/works/works/*.parquet')
                     WHERE id IN (SELECT id FROM wids) GROUP BY 1''').df()
tmp = f'{TITLES_PQ}.{os.getpid()}.tmp'
titles.to_parquet(tmp, index=False); os.replace(tmp, TITLES_PQ)
log['snapshot_titles'] = int(titles.title.notna().sum()); log['title_scan_s'] = round(time.time() - t1)
print(f'snapshot titles: {log["snapshot_titles"]:,} of {len(ids):,} works ({time.time() - t1:.0f}s) -> {TITLES_PQ}')

t1 = time.time()
missing = sorted(set(ids.id) - set(titles.dropna(subset=['title']).id))
got = npc.api_titles(missing)
log['api_titles'] = len(got); log['api_missing'] = len(missing); log['api_s'] = round(time.time() - t1)
print(f'OpenAlex API titles: {len(got):,} of {len(missing):,} works missing from the snapshot ({time.time() - t1:.0f}s)')

P = P.sort_values('works_count', ascending=False).reset_index(drop=True)
P['task'] = np.arange(len(P)) % N_TASKS
P[['aid', 'task', 'name', 'prizes', 'works_count', 'people', 'orcid', 'url']].to_csv(B / 'targets.tsv', sep='\t', index=False)
log.update(targets=len(P), n_tasks=N_TASKS, seconds=round(time.time() - t0), finished=time.strftime('%Y-%m-%d %H:%M:%S'))
(B / 'prepass_manifest.json').write_text(json.dumps(log, indent=1))
print(json.dumps(log, indent=1))
