"""Shared paths, plot style, caches and metric assembly for the Nobel Prize notebooks.

Both notebooks attach the Science of Science metrics to sets of OpenAlex works / PatentsView patents;
keeping the joins and the metric conventions here guarantees that a document carries the same numbers
in author_profile.ipynb and in nobel_laureate_papers.ipynb.

    import np_common as npc
    con = npc.duck()
    con.register('ids', pd.DataFrame({'paper_id': [...]}))
    P = npc.assemble_paper_metrics(con, 'ids')          # raw joins (cacheable)
    P = npc.finish_paper_metrics(con, P, 'ids')         # DA, CD with-reference percentiles, masks

Conventions (documented in the notebooks' vocabulary tables):
* window metrics (C_W, pctl_cW, CD/F/E/G/n*_W, pcs_C_W) are blanked when the window has not closed
  (year + W > OBS_END_YEAR); the all-time columns are kept and have unequal exposure;
* the disruption family is blanked for documents without any reference (CD = 1 by construction), and
  the paper CD percentiles are recomputed among papers with references (CD_W_rpctl*);
* DA follows the Atypicality notebooks (z of raw PPPL within scoring year x first FoS / filing year x
  CPC section); because raw-PPPL cohorts are heavy-tailed, the log-PPPL z (DA_log) and the within-cohort
  percentile (DA_pctl) are provided next to it and are the ones to compare across cohorts.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------------------------
ROOT = Path('/project/jevans/Dawoon')
NP = ROOT / 'Nobel Prize'
CACHE = NP / 'cache'                                   # shared caches (all notebooks, all authors)
SOS = ROOT / 'Science of Science'
OA = SOS / 'OpenAlex' / 'output'
PV = SOS / 'PatentView' / 'output'
PCSDIR = SOS / 'pcs'
ATYP = SOS / 'Atypicality' / 'Data'
PQRS_TSV = ROOT / 'Scientist_Inventor' / 'Data' / 'pqrs_dataset.tsv'
PQRS_RELEASE = '20230330'                              # PatentsView disambiguation release of the pqrs inventor ids
GREEDY_MAP = ROOT / 'Scientist_Inventor' / 'Data' / 'scientist_inventor_mapping' / 'scientist_inventor_mapping.parquet'
AUTHORSHIPS = ROOT / 'Scientist_Inventor' / 'Data' / 'authorships_parquet'   # bucket=NNN/part-*.parquet, work_id % 64
OA_RAW = Path('/project/jevans/renli_shared/OpenAlex_2026_Jan_16_Renly_parquet')
PAPER_DA_CACHE = ATYP / '_traj_cache' / 'paper_year_DA' / 'all_years' / 'paper_metrics.parquet'
PATENT_MASTER = ATYP / 'rev' / 'patent_master.parquet'            # the rev build (NOTEBOOKS.md); DA inputs identical to the pre-rev file
PPP_MASTER = ATYP / 'ppp_master_rev.parquet'
PCS_CSV = PCSDIR / 'pcs_oa_uspto.csv'
SSN_PAPERS = SOS / 'OpenAlex' / 'sciscinet_papers_fos_feg.parquet'     # SciSciNet (MAG) paper metrics, paperid = 'W' + MAG id
OBS_END_YEAR = 2025                                    # last complete year of the 2026-01 snapshots
RESEARCH_DOCTYPES = ('article', 'review', 'letter')    # headline statistics; the DA population is 'article' only

for _d in (CACHE, CACHE / 'duckdb_tmp'):
    _d.mkdir(parents=True, exist_ok=True)


def granted(name: str) -> Path:
    """A PatentsView granted bulk file: the Science-of-Science copy first, the project copy as fallback."""
    for base in (SOS / 'PatentView' / 'Granted', ROOT / 'PatentView' / 'Granted'):
        if (base / name).exists():
            return base / name
    raise FileNotFoundError(name)


def pregranted(name: str) -> Path:
    p = SOS / 'PatentView' / 'Pregranted' / name
    if not p.exists():
        raise FileNotFoundError(p)
    return p


# ---------------------------------------------------------------------------------------------
# DuckDB, caches, JSON
# ---------------------------------------------------------------------------------------------
def resources():
    """(threads, DuckDB memory limit) from the Slurm allocation, conservative defaults elsewhere."""
    threads = int(os.environ.get('SLURM_CPUS_PER_TASK', '4'))
    mem_mb = os.environ.get('SLURM_MEM_PER_NODE')
    if not mem_mb and os.environ.get('SLURM_MEM_PER_CPU'):
        mem_mb = str(int(os.environ['SLURM_MEM_PER_CPU']) * threads)
    mem = f"{max(2, int(int(mem_mb) * 0.6 / 1024))}GB" if mem_mb else '4GB'
    return threads, mem


def duck(threads: int | None = None, mem: str | None = None):
    import duckdb
    t, m = resources()
    con = duckdb.connect()
    con.execute(f"SET threads = {threads or t}")
    con.execute(f"SET memory_limit = '{mem or m}'")
    con.execute(f"SET temp_directory = '{CACHE / 'duckdb_tmp'}'")
    con.execute("SET preserve_insertion_order = false")
    return con


def sql_list(values) -> str:
    """A SQL IN-list of string literals."""
    return ', '.join("'" + str(v).replace("'", "''") + "'" for v in values) or "''"


def fresh(path: Path, sources) -> bool:
    """A cache file is valid while it exists and none of its source files is newer than it."""
    path = Path(path)
    if not path.exists():
        return False
    mt = path.stat().st_mtime
    return all(Path(s).stat().st_mtime < mt for s in sources if Path(s).exists())


shared_cache_fresh = fresh      # older name


def copy_atomic(con, sql: str, dst: Path):
    """COPY (sql) TO dst through a temporary file, so an interrupted or concurrent build never leaves a
    partial file that a later freshness check would accept."""
    dst = Path(dst)
    tmp = f'{dst}.{os.getpid()}.tmp'
    con.execute(f"COPY ({sql}) TO '{tmp}' (FORMAT PARQUET)")
    os.replace(tmp, dst)


def key_hash(key) -> str:
    return hashlib.sha1(json.dumps(key, sort_keys=True, default=str).encode()).hexdigest()[:10]


class Cache:
    """Parquet cache of heavy intermediate results. A file is reused only when its key (the inputs that
    define it: ids, parameters, a version) hashes to the same name and no source file is newer."""

    def __init__(self, directory: Path, version: int, rebuild: bool = False):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.version, self.rebuild, self.log = version, rebuild, []

    def __call__(self, name, builder, key=(), sources=()):
        path = self.dir / f'{name}.{key_hash([self.version, key])}.parquet'
        if not self.rebuild and fresh(path, sources):
            df = pd.read_parquet(path)
            self.log.append({'name': name, 'file': path.name, 'rows': len(df), 'status': 'reused'})
            print(f'[{name}] cached: {len(df):,} rows')
            return df
        t0 = time.time()
        df = builder()
        tmp = f'{path}.{os.getpid()}.tmp'
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
        self.log.append({'name': name, 'file': path.name, 'rows': len(df), 'status': 'built', 'seconds': round(time.time() - t0, 1)})
        print(f'[{name}] built: {len(df):,} rows in {time.time() - t0:.0f}s')
        return df


def clean_json(o):
    """Recursively replace NaN / inf / NA by None and numpy scalars by Python ones (strict JSON)."""
    if isinstance(o, dict):
        return {str(k): clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [clean_json(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if o is pd.NA or o is pd.NaT:
        return None
    return o


def write_json(path: Path, obj):
    Path(path).write_text(json.dumps(clean_json(obj), indent=2, default=str, allow_nan=False))


def fingerprint(p):
    p = Path(p)
    if not p.exists():
        return None
    st = p.stat()
    return {'path': str(p), 'bytes': st.st_size, 'mtime': pd.Timestamp(st.st_mtime, unit='s').isoformat()}


def semi(con, file, cols, key='paper_id', table='ego_p', rename=None):
    """Rows of a parquet file whose key is in a registered id table (one row per key)."""
    sel = ', '.join([key] + list(cols))
    df = con.sql(f"SELECT {sel} FROM read_parquet('{file}') WHERE {key} IN (SELECT {key} FROM {table})").df()
    if rename:
        df = df.rename(columns=rename)
    return df.drop_duplicates(key)


# ---------------------------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------------------------
TRANSLIT = {'æ': 'ae', 'ø': 'o', 'œ': 'oe', 'ß': 'ss', 'ł': 'l', 'đ': 'd', 'ð': 'd', 'þ': 'th', 'ı': 'i'}   # not decomposed by NFKD


def fold(s) -> str:
    """Lower case, ligatures transliterated, accents removed, apostrophes dropped."""
    s = str(s).lower()
    for k, v in TRANSLIT.items():
        s = s.replace(k, v)
    s = ''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))
    return re.sub(r"['’′`]", '', s)


def name_tokens(s) -> list:
    """Letter tokens of a person name longer than one letter: "Mitchell Ray O'Connell" -> ['mitchell', 'ray', 'oconnell']."""
    return [t for t in re.split(r'[^a-z]+', fold(s)) if len(t) > 1]


def names_agree(a, b) -> bool:
    """Two person names share a token (handles 'Doudna Cate', 'Paez-Espino', reordered names)."""
    return bool(set(name_tokens(a)) & set(name_tokens(b)))


def name_key(s):
    """(first token, last token) of a person name, or None for single-token names."""
    t = name_tokens(s)
    return (t[0], t[-1]) if len(t) >= 2 else None


def middle_initials(s) -> set:
    """First letters of the tokens between the first and the last one ('Robert H. Brown' -> {'h'})."""
    raw = [t for t in re.split(r'[^a-z]+', fold(s)) if t]
    return {t[0] for t in raw[1:-1]} if len(raw) > 2 else set()


def middle_conflict(a, b) -> bool:
    """Both names carry middle initials and none agrees ('Robert H. Brown' vs 'Robert A. Brown')."""
    ma, mb = middle_initials(a), middle_initials(b)
    return bool(ma) and bool(mb) and not (ma & mb)


# ---------------------------------------------------------------------------------------------
# Plot style (validated categorical slots: blue / orange / aqua pass all-pairs CVD checks)
# ---------------------------------------------------------------------------------------------
SCI, TECH, LINK = '#2a78d6', '#eb6834', '#1baf7a'      # papers, patents, patent->paper links
GREY, INK, INK2, GRID = '#8c8b86', '#0b0b0b', '#52514e', '#e6e5e1'
FIELD_COLORS = {'Physics': SCI, 'Chemistry': TECH, 'Medicine': LINK}
FIELDS = ['Physics', 'Chemistry', 'Medicine']


def style():
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        'figure.dpi': 110, 'savefig.dpi': 150, 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#b9b8b3',
        'axes.labelcolor': INK2, 'axes.titlecolor': INK, 'xtick.color': INK2, 'ytick.color': INK2,
        'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': .6, 'grid.linestyle': '-',
        'lines.linewidth': 2, 'lines.markersize': 6, 'legend.frameon': False,
        'text.parse_math': False,      # titles such as '$GL_n(\mathbb C)$' are text, not mathtext (an unknown macro raises)
    })


# ---------------------------------------------------------------------------------------------
# Paper metrics
# ---------------------------------------------------------------------------------------------
WINDOWS = ('3', '5', '10', 'all')
CD_COLS = [f'{m}_{w}' for w in WINDOWS for m in ('CD', 'F', 'E', 'G', 'ni', 'nj', 'nk')]
# CD_W_pctl = share of the cohort strictly below (minimum rank); CD_W_pctl_cume = share at or below (ties inclusive).
CD_PCTL_COLS = [f'CD_{w}_pctl{s}' for w in WINDOWS for s in ('', '_cume')]
PCS_WINDOW_COLS = ['pcs_C_3', 'pcs_C_5', 'pcs_C_10', 'pcs_C_all', 'pcs_C_examiner_all', 'pcs_C_non_examiner_all']
PCS_TOTAL_COLS = ['pcs_C_total', 'pcs_C_examiner_total', 'pcs_C_non_examiner_total']


def assemble_paper_metrics(con, table='ego_p', with_sciscinet=True):
    """One row per paper_id of `table` with the raw Science of Science paper metrics (cacheable: no masks,
    no DA). finish_paper_metrics() completes it."""
    P = con.sql(f"SELECT DISTINCT paper_id FROM {table}").df()
    P = P.merge(semi(con, OA / 'paper_metadata.parquet',
                     ['year', 'doctype', 'ref_count', 'journal', 'is_journal', 'FoS_0', 'FoS_rep', 'domain',
                      'primary_topic_field', 'primary_topic_subfield', 'cited_by_count', 'is_retracted'], table=table), how='left')
    P = P.merge(semi(con, OA / 'paper_citation.parquet', ['C_3', 'C_5', 'C_10', 'C_all'], table=table), how='left')
    P = P.merge(semi(con, OA / 'paper_hit_probability.parquet', ['FoS', 'pctl_c3', 'pctl_c5', 'pctl_c10', 'pctl_call'],
                     rename={'FoS': 'pctl_FoS'}, table=table), how='left')
    P = P.merge(semi(con, OA / 'paper_disruption.parquet', CD_COLS + CD_PCTL_COLS, table=table), how='left')
    P = P.merge(semi(con, OA / 'paper_z_score.parquet', ['Z_median', 'Z_10pct', 'Z_min', 'n_pairs'], table=table), how='left')
    P = P.merge(semi(con, OA / 'paper_sb.parquet', ['SB_B', 'SB_T', 'n_cite'], table=table), how='left')
    P = P.merge(semi(con, OA / 'paper_author_country.parquet', ['team_size', 'n_located', 'n_countries', 'countries', 'is_international',
                                                                'first_author_country', 'last_author_country'], table=table), how='left')
    pcs_cols = ['C_3', 'C_5', 'C_10', 'C_all', 'C_examiner_all', 'C_non_examiner_all', 'C_total', 'C_examiner_total', 'C_non_examiner_total']
    P = P.merge(semi(con, PCSDIR / 'output' / 'pcs_citation.parquet', pcs_cols, table=table,
                     rename={c: f'pcs_{c}' for c in pcs_cols}), how='left')
    P = P.merge(semi(con, PCSDIR / 'output' / 'pcs_hit_probability.parquet', ['pctl_c5', 'pctl_call'], table=table,
                     rename={'pctl_c5': 'pcs_pctl_c5', 'pctl_call': 'pcs_pctl_call'}), how='left')
    ppp = con.sql(f'''SELECT paper_id, any_value(sci_DA_year_cohort) AS ppp_sci_DA_year, any_value(sci_DA_year_field_cohort) AS ppp_sci_DA_year_field,
                             any_value(pap_pppl) AS ppp_pap_pppl, count(*) AS n_ppp_pairs,
                             count(*) FILTER (WHERE coalesce(pap_id_mislink_suspected, false)) AS n_ppp_pairs_mislink,
                             string_agg(DISTINCT patent_id, ';') AS ppp_patent_ids
                      FROM read_parquet('{PPP_MASTER}') WHERE paper_id IN (SELECT paper_id FROM {table}) GROUP BY paper_id''').df()
    P = P.merge(ppp, on='paper_id', how='left')
    if with_sciscinet:
        P = P.merge(_sciscinet(con, table), on='paper_id', how='left')
    return P


def _sciscinet(con, table):
    """SciSciNet (MAG snapshot) metrics of the same papers, prefixed ssn_, for cross-checks and a display-year fallback."""
    cols = ['year', 'doi', 'C5', 'C10', 'disruption', 'Atyp_Median_Z', 'Atyp_10pct_Z', 'SB_B', 'team_size', 'patent_count', 'f_y5', 'e_y5', 'g_y5']
    df = con.sql(f'''SELECT paperid AS paper_id, {', '.join(cols)} FROM read_parquet('{SSN_PAPERS}')
                     WHERE paperid IN (SELECT paper_id FROM {table})''').df().drop_duplicates('paper_id')
    return df.rename(columns={c: f'ssn_{c}' for c in cols})


def finish_paper_metrics(con, P, table, cd_windows=('5', '10'), require_refs=True, obs_end=OBS_END_YEAR):
    """Post-cache steps on the raw frame: types, zero-fills, DA, CD with-reference percentiles, the
    no-reference and open-window masks, country and research flags, a display-year fallback."""
    P = P.copy()
    P['year'] = pd.to_numeric(P.year, errors='coerce').astype('Int64')
    P['has_metadata'] = P.year.notna()
    P['fos1'] = P.FoS_0.astype('string').str.split(';').str[0].str.strip().replace('', pd.NA)
    # pcs_citation lists only papers cited by a patent: absent = 0. Windowed counts need the paper year
    # (zero-filled only with metadata); the year-free totals are zero-filled for every paper.
    for c in PCS_WINDOW_COLS:
        P[c] = pd.to_numeric(P[c], errors='coerce').fillna(0).astype('Int64').where(P.has_metadata)
    for c in PCS_TOTAL_COLS:
        P[c] = pd.to_numeric(P[c], errors='coerce').fillna(0).astype('Int64')
    P['in_ppp'] = P.n_ppp_pairs.notna()
    loc = pd.to_numeric(P.n_located, errors='coerce').fillna(0) > 0       # countries only where an author was located
    for c in ['n_countries', 'is_international', 'first_author_country', 'last_author_country', 'countries']:
        P[c] = P[c].where(loc)
    P['research'] = P.doctype.isin(RESEARCH_DOCTYPES)
    P = add_paper_da(con, P, table)
    if require_refs:
        P = mask_cd_without_refs(P)
    P = add_cd_ref_percentiles(con, P, table, windows=cd_windows)
    P = mask_open_windows(P, 'year', obs_end, paper_window_cols)
    ssn_year = pd.to_numeric(P.ssn_year, errors='coerce') if 'ssn_year' in P else pd.Series(np.nan, index=P.index)
    P['year_display'] = P.year.astype('Float64').fillna(ssn_year.astype('Float64')).astype('Int64')
    P['year_display_source'] = np.where(P.year.notna(), 'openalex', np.where(P.year_display.notna(), 'sciscinet', 'none'))
    return P


def paper_window_cols(w):
    cols = [f'C_{w}', f'pctl_c{w}', f'pcs_C_{w}'] + [f'{m}_{w}' for m in ('CD', 'F', 'E', 'G', 'ni', 'nj', 'nk')]
    cols += [f'{m}_{w}_pctl{s}' for m in ('C', 'F', 'E', 'G', 'pcs_C') for s in ('', '_cume')]
    return cols + [f'CD_{w}_{k}{s}' for k in ('pctl', 'rpctl') for s in ('', '_cume', '_mid')]


def patent_window_cols(w):
    cols = [f'{c}_{w}' for c in ('C', 'appC', 'uniqueC', 'CD', 'F', 'E', 'G', 'ni', 'nj', 'nk')]
    cols += [f'pctl_uniqueC_{w}', f'pctl_C_{w}', f'pctl_appC_{w}'] + [f'CD_{w}_{k}{s}' for k in ('pctl', 'rpctl') for s in ('', '_cume', '_mid')]
    cols += [f'{m}_{w}_pctl{s}' for m in ('uniqueC', 'F', 'E', 'G') for s in ('', '_cume')]
    return cols + [f'C_{k}_{w}' for k in ('examiner', 'non_examiner', 'unknown')]


# ---------------------------------------------------------------------------------------------
# Cohort percentiles of every measure (shared population tables)
# ---------------------------------------------------------------------------------------------
# Convention of these tables: <m>_pctl = mid-rank percentile ((share strictly below + share at or below) / 2),
# <m>_pctl_cume = share at or below (for "top x %" thresholds), within the cohort of documents that have the measure.
# Papers: publication year x first FoS (paper_metadata), as the Science of Science percentiles.
# Patents: grant year x CPC Section: every patent measure is anchored on the grant year (citation windows, CD, SB), so
# the documents of a cohort share the same (possibly truncated) window. Patent DA stays within filing year x Section.
PAPER_PCTL_FAMILIES = {                 # family: (source file, measures, papers with references only)
    'cit': ('paper_citation.parquet', ['C_5', 'C_10'], False),
    'z': ('paper_z_score.parquet', ['Z_median', 'Z_10pct'], False),
    'sb': ('paper_sb.parquet', ['SB_B'], False),
    'feg': ('paper_disruption.parquet', ['F_5', 'E_5', 'G_5'], True),
}


def _pctl_cols(cols, part):
    out = []
    for c in cols:
        p = f'PARTITION BY {part}, ({c} IS NULL)'
        out.append(f'''CASE WHEN {c} IS NOT NULL THEN ((rank() OVER ({p} ORDER BY {c}) - 1)::DOUBLE / count(*) OVER ({p})
                                                   + cume_dist() OVER ({p} ORDER BY {c})) / 2 END AS {c}_pctl''')
        out.append(f'CASE WHEN {c} IS NOT NULL THEN cume_dist() OVER ({p} ORDER BY {c}) END AS {c}_pctl_cume')
    return ',\n'.join(out)


def paper_pctl_tables(con, log=print):
    """Build (once) the paper percentile tables cache/paper_pctl_<family>.v1.parquet and the patent-citation
    tables. Returns their paths. About 5 minutes on 8 cores for the whole population (run on a compute node)."""
    meta = OA / 'paper_metadata.parquet'
    paths = {fam: CACHE / f'paper_pctl_{fam}.v1.parquet' for fam in PAPER_PCTL_FAMILIES}
    pcs_pos, pcs_coh = CACHE / 'paper_pctl_pcs.v1.parquet', CACHE / 'paper_pctl_pcs_cohorts.v1.parquet'
    pcs_src = PCSDIR / 'output' / 'pcs_citation.parquet'
    todo = [f for f, (src, _, _) in PAPER_PCTL_FAMILIES.items() if not fresh(paths[f], [meta, OA / src])]
    need_pcs = not (fresh(pcs_pos, [meta, pcs_src]) and fresh(pcs_coh, [meta, pcs_src]))
    if todo or need_pcs:
        t0 = time.time()
        base = CACHE / f'_paper_meta_base.{os.getpid()}.parquet'
        con.execute(f'''COPY (SELECT paper_id, year, nullif(trim(split_part(FoS_0, ';', 1)), '') AS fos1, ref_count
                              FROM read_parquet('{meta}') WHERE year IS NOT NULL) TO '{base}' (FORMAT PARQUET)''')
        for fam in todo:
            t1 = time.time()
            src, cols, refs = PAPER_PCTL_FAMILIES[fam]
            where = 'm.fos1 IS NOT NULL' + (' AND m.ref_count >= 1' if refs else '')
            copy_atomic(con, f'''SELECT paper_id, {_pctl_cols(cols, 'year, fos1')}
                                 FROM (SELECT m.paper_id, m.year, m.fos1, {', '.join('d.' + c for c in cols)}
                                       FROM read_parquet('{base}') m JOIN read_parquet('{OA / src}') d USING (paper_id) WHERE {where})''',
                        paths[fam])
            log(f'[paper percentiles] {fam}: {time.time() - t1:.0f}s')
        if need_pcs:
            # patent citations: most papers are never cited by a patent and are absent from pcs_citation, so the ranks
            # of the cited papers are shifted by the cohort's zeros and the zeros get (z0 / n) / 2 at join time
            copy_atomic(con, f'''SELECT year, fos1, count(*) AS n FROM read_parquet('{base}') WHERE fos1 IS NOT NULL GROUP BY ALL''', pcs_coh)
            parts = []
            for c in ('C_5', 'C_total'):
                parts.append(f'''(WITH pos AS (SELECT m.paper_id, m.year, m.fos1, p.{c} AS v
                                               FROM read_parquet('{base}') m JOIN read_parquet('{pcs_src}') p USING (paper_id)
                                               WHERE m.fos1 IS NOT NULL AND p.{c} > 0),
                                      r AS (SELECT paper_id, year, fos1, rank() OVER w AS rk, cume_dist() OVER w AS cd,
                                                   count(*) OVER (PARTITION BY year, fos1) AS npos
                                            FROM pos WINDOW w AS (PARTITION BY year, fos1 ORDER BY v))
                                  SELECT r.paper_id, '{c}' AS measure, r.npos, c.n,
                                         ((c.n - r.npos + r.rk - 1)::DOUBLE / c.n + (c.n - r.npos + r.cd * r.npos) / c.n) / 2 AS pctl,
                                         (c.n - r.npos + r.cd * r.npos) / c.n AS pctl_cume
                                  FROM r JOIN read_parquet('{pcs_coh}') c USING (year, fos1))''')
            copy_atomic(con, ' UNION ALL '.join(f'SELECT * FROM {p}' for p in parts), pcs_pos)
            npos = con.sql(f"SELECT m.year, m.fos1, p.measure, count(*) AS npos FROM read_parquet('{pcs_pos}') p "
                           f"JOIN read_parquet('{base}') m USING (paper_id) GROUP BY ALL").df()
            coh = pd.read_parquet(pcs_coh)
            for c in ('C_5', 'C_total'):
                coh = coh.merge(npos[npos.measure == c].drop(columns='measure').rename(columns={'npos': f'npos_{c}'}), on=['year', 'fos1'], how='left')
                coh[f'npos_{c}'] = coh[f'npos_{c}'].fillna(0).astype('int64')
            tmp = f'{pcs_coh}.{os.getpid()}.tmp'
            coh.to_parquet(tmp, index=False); os.replace(tmp, pcs_coh)
            log(f'[paper percentiles] patent citations: done')
        base.unlink(missing_ok=True)
        log(f'[paper percentiles] built in {time.time() - t0:.0f}s')
    return paths, pcs_pos, pcs_coh


def add_paper_percentiles(con, P, table):
    """Attach <m>_pctl / <m>_pctl_cume for C_5, C_10, Z_median, Z_10pct, SB_B, F_5, E_5, G_5, pcs_C_5, pcs_C_total,
    and the novelty percentile (1 - rank of Z_10pct: high = atypical journal combinations)."""
    paths, pcs_pos, pcs_coh = paper_pctl_tables(con)
    P = P.drop(columns=[c for c in P.columns if c.endswith(('_pctl', '_pctl_cume')) and not c.startswith(('CD_', 'DA'))
                        and c not in ('pcs_pctl_c5', 'pcs_pctl_call')], errors='ignore')
    for fam, path in paths.items():
        cols = [f'{c}{s}' for c in PAPER_PCTL_FAMILIES[fam][1] for s in ('_pctl', '_pctl_cume')]
        P = P.merge(semi(con, path, cols, table=table), on='paper_id', how='left')
    pos = con.sql(f"SELECT paper_id, measure, pctl, pctl_cume FROM read_parquet('{pcs_pos}') WHERE paper_id IN (SELECT paper_id FROM {table})").df()
    coh = pd.read_parquet(pcs_coh)
    key = P[['paper_id', 'year', 'fos1']].assign(year=lambda x: pd.to_numeric(x.year, errors='coerce').astype('float'))
    key = key.merge(coh.assign(year=coh.year.astype(float)), on=['year', 'fos1'], how='left')
    for c in ('C_5', 'C_total'):
        pc = pos[pos.measure == c].set_index('paper_id')
        z0 = (key.n - key[f'npos_{c}']) / key.n
        P[f'pcs_{c}_pctl'] = P.paper_id.map(pc.pctl).fillna(pd.Series((z0 / 2).values, index=P.index))
        P[f'pcs_{c}_pctl_cume'] = P.paper_id.map(pc.pctl_cume).fillna(pd.Series(z0.values, index=P.index))
    lo = 2 * P.Z_10pct_pctl - P.Z_10pct_pctl_cume                   # share strictly below
    P['novelty_pctl'] = 1 - P.Z_10pct_pctl
    P['novelty_pctl_cume'] = 1 - lo                                  # share of the cohort at or below in novelty
    return P


BOOK_TYPES = ('book', 'book-chapter', 'book-section', 'reference-entry')
REFS_W_YEAR = OA / 'referenced_works_w_year'                 # citing work -> referenced work, with years (1,334 parts, 21 GB)
BOOK_CITES = CACHE / 'paper_book_cites.v1.parquet'
BOOK_COHORTS = CACHE / 'paper_book_cites_cohorts.v1.parquet'


def book_citation_tables(con, log=print):
    """How often every paper is cited by books: citing works with an OpenAlex type in BOOK_TYPES (books, book chapters,
    reference entries). One row per cited paper with at least one book citation: n_book_cites (distinct citing books /
    chapters / entries), n_books, n_chapters, n_reference_entries, first / last citing-book year, and the mid-rank percentile
    of n_book_cites within publication year x first FoS (the never-book-cited majority is the zero block: it gets
    (n - npos) / (2 n) at join time from the cohort table). Built once, a few minutes on 8 cores."""
    meta = OA / 'paper_metadata.parquet'
    srcs = [meta] + sorted(REFS_W_YEAR.glob('*.parquet'))[:1]
    if not (fresh(BOOK_CITES, srcs) and fresh(BOOK_COHORTS, srcs)):
        t0 = time.time()
        types = sql_list(BOOK_TYPES)
        base = CACHE / f'_paper_meta_base_b.{os.getpid()}.parquet'
        con.execute(f'''COPY (SELECT paper_id, year, nullif(trim(split_part(FoS_0, ';', 1)), '') AS fos1, doctype
                              FROM read_parquet('{meta}') WHERE year IS NOT NULL) TO '{base}' (FORMAT PARQUET)''')
        copy_atomic(con, f"SELECT year, fos1, count(*) AS n FROM read_parquet('{base}') WHERE fos1 IS NOT NULL GROUP BY ALL", BOOK_COHORTS)
        copy_atomic(con, f'''
            WITH b AS (SELECT paper_id AS work_id, doctype FROM read_parquet('{base}') WHERE doctype IN ({types})),
                 e AS (SELECT r.referenced_work_id AS paper_id, r.work_id, r.work_year, b.doctype
                       FROM read_parquet('{REFS_W_YEAR}/*.parquet') r JOIN b USING (work_id)),
                 c AS (SELECT paper_id, count(DISTINCT work_id) AS n_book_cites,
                              count(DISTINCT work_id) FILTER (WHERE doctype = 'book') AS n_books,
                              count(DISTINCT work_id) FILTER (WHERE doctype IN ('book-chapter', 'book-section')) AS n_chapters,
                              count(DISTINCT work_id) FILTER (WHERE doctype = 'reference-entry') AS n_reference_entries,
                              min(work_year) AS first_book_cite_year, max(work_year) AS last_book_cite_year
                       FROM e GROUP BY 1),
                 k AS (SELECT c.*, m.year, m.fos1 FROM c JOIN read_parquet('{base}') m USING (paper_id) WHERE m.fos1 IS NOT NULL),
                 r AS (SELECT *, rank() OVER w AS rk, cume_dist() OVER w AS cd, count(*) OVER (PARTITION BY year, fos1) AS npos
                       FROM k WINDOW w AS (PARTITION BY year, fos1 ORDER BY n_book_cites))
            SELECT r.paper_id, r.n_book_cites, r.n_books, r.n_chapters, r.n_reference_entries, r.first_book_cite_year, r.last_book_cite_year,
                   r.npos, ((h.n - r.npos + r.rk - 1)::DOUBLE / h.n + (h.n - r.npos + r.cd * r.npos) / h.n) / 2 AS book_cites_pctl,
                   (h.n - r.npos + r.cd * r.npos) / h.n AS book_cites_pctl_cume
            FROM r JOIN read_parquet('{BOOK_COHORTS}') h USING (year, fos1)''', BOOK_CITES)
        npos = con.sql(f"SELECT m.year, m.fos1, count(*) AS npos FROM read_parquet('{BOOK_CITES}') b JOIN read_parquet('{base}') m USING (paper_id) GROUP BY ALL").df()
        coh = pd.read_parquet(BOOK_COHORTS).merge(npos, on=['year', 'fos1'], how='left')
        coh['npos'] = coh.npos.fillna(0).astype('int64')
        tmp = f'{BOOK_COHORTS}.{os.getpid()}.tmp'
        coh.to_parquet(tmp, index=False); os.replace(tmp, BOOK_COHORTS)
        base.unlink(missing_ok=True)
        log(f'[book citations] population tables built in {time.time() - t0:.0f}s')
    return BOOK_CITES, BOOK_COHORTS


def add_book_citations(con, P, table):
    """Attach n_book_cites (0 when never cited by a book), the split by type and book_cites_pctl / _cume."""
    bc, bh = book_citation_tables(con)
    cols = ['n_book_cites', 'n_books', 'n_chapters', 'n_reference_entries', 'first_book_cite_year', 'last_book_cite_year',
            'book_cites_pctl', 'book_cites_pctl_cume']
    P = P.drop(columns=[c for c in cols if c in P])
    P = P.merge(semi(con, bc, cols, table=table), on='paper_id', how='left')
    coh = pd.read_parquet(bh)
    key = P[['year', 'fos1']].assign(year=lambda x: pd.to_numeric(x.year, errors='coerce').astype(float))
    key = key.merge(coh.assign(year=coh.year.astype(float)), on=['year', 'fos1'], how='left')
    z0 = pd.Series(((key.n - key.npos) / key.n).values, index=P.index)
    has = P.year.notna()
    for c in ['n_book_cites', 'n_books', 'n_chapters', 'n_reference_entries']:
        P[c] = pd.to_numeric(P[c], errors='coerce').fillna(0).where(has)
    P['book_cites_pctl'] = P.book_cites_pctl.fillna(z0 / 2)
    P['book_cites_pctl_cume'] = P.book_cites_pctl_cume.fillna(z0)
    return P


PATENT_PCTL_TABLE = CACHE / 'patent_pctl_population.v2.parquet'


def patent_pctl_table(con, obs_end=OBS_END_YEAR, log=print):
    """Percentiles of every patent measure within grant year x CPC Section over the utility patents of
    patent_metadata: uniqueC_5, CD_5 / F_5 / E_5 / G_5 (references >= 1), Kim Z_median / Z_10pct, SB_B and n_paper_refs
    (papers cited by the patent in Reliance on Science, 0 when none)."""
    pcs = CACHE / 'pcs_oa_uspto.v2.parquet'
    srcs = [PV / f for f in ('patent_metadata.parquet', 'patent_citation.parquet', 'patent_disruption.parquet', 'patent_z_score.parquet',
                             'patent_sb.parquet')] + [pcs]
    if not fresh(PATENT_PCTL_TABLE, srcs):
        t0 = time.time()
        closed = 'TRUE'
        copy_atomic(con, f'''
            WITH m AS (SELECT patent_id, CAST(grant_year AS INTEGER) AS year, substr(cpc_code, 1, 1) AS section, ref_count, grant_year
                       FROM read_parquet('{PV / 'patent_metadata.parquet'}') WHERE grant_year IS NOT NULL AND cpc_code IS NOT NULL),
                 r AS (SELECT patent_id, count(DISTINCT oaid) AS n_paper_refs FROM read_parquet('{pcs}') WHERE doc_kind = 'grant' GROUP BY 1),
                 b AS (SELECT m.patent_id, m.year, m.section,
                              CASE WHEN {closed} THEN coalesce(c.uniqueC_5, 0) END AS uniqueC_5,
                              CASE WHEN {closed} AND m.ref_count >= 1 THEN d.CD_5 END AS CD_5,
                              CASE WHEN {closed} AND m.ref_count >= 1 THEN d.F_5 END AS F_5,
                              CASE WHEN {closed} AND m.ref_count >= 1 THEN d.E_5 END AS E_5,
                              CASE WHEN {closed} AND m.ref_count >= 1 THEN d.G_5 END AS G_5,
                              z.Z_median, z.Z_10pct, s.SB_B, coalesce(r.n_paper_refs, 0) AS n_paper_refs
                       FROM m LEFT JOIN read_parquet('{PV / 'patent_citation.parquet'}') c USING (patent_id)
                              LEFT JOIN read_parquet('{PV / 'patent_disruption.parquet'}') d USING (patent_id)
                              LEFT JOIN read_parquet('{PV / 'patent_z_score.parquet'}') z USING (patent_id)
                              LEFT JOIN read_parquet('{PV / 'patent_sb.parquet'}') s USING (patent_id)
                              LEFT JOIN r USING (patent_id))
            SELECT patent_id, {_pctl_cols(['uniqueC_5', 'CD_5', 'F_5', 'E_5', 'G_5', 'Z_median', 'Z_10pct', 'SB_B', 'n_paper_refs'], 'year, section')}
            FROM b''', PATENT_PCTL_TABLE)
        log(f'[patent percentiles] built in {time.time() - t0:.0f}s')
    return PATENT_PCTL_TABLE


def add_patent_percentiles(con, T, table, obs_end=OBS_END_YEAR):
    path = patent_pctl_table(con, obs_end)
    cols = [f'{c}{s}' for c in ['uniqueC_5', 'CD_5', 'F_5', 'E_5', 'G_5', 'Z_median', 'Z_10pct', 'SB_B', 'n_paper_refs'] for s in ('_pctl', '_pctl_cume')]
    ren = {'CD_5_pctl': 'CD_5_rpctl_mid', 'CD_5_pctl_cume': 'CD_5_rpctl_cume'}   # same names as the paper side; the SoS CD_5_pctl stays
    new_cols = [ren.get(c, c) for c in cols]
    T = T.drop(columns=[c for c in new_cols + ['novelty_pctl', 'novelty_pctl_cume'] if c in T])
    T = T.merge(semi(con, path, cols, key='patent_id', table=table, rename=ren), on='patent_id', how='left')
    lo = 2 * T.Z_10pct_pctl - T.Z_10pct_pctl_cume
    T['novelty_pctl'] = 1 - T.Z_10pct_pctl
    T['novelty_pctl_cume'] = 1 - lo
    return T


def mask_open_windows(P, year_col, obs_end, cols_fn, windows=('3', '5', '10')):
    """Blank window-W metrics of documents whose window had not closed by obs_end (year + W > obs_end),
    as the Atypicality DA-vs-metrics notebooks do; eligible_W records the rule."""
    P = P.copy()
    y = pd.to_numeric(P[year_col], errors='coerce')
    for w in windows:
        elig = (y + int(w) <= obs_end).fillna(False).astype(bool)
        P[f'eligible_{w}'] = elig
        for c in [c for c in cols_fn(w) if c in P]:
            P[c] = P[c].where(elig)
    return P


CD_FAMILY = [f'{m}_{w}' for w in WINDOWS for m in ('CD', 'F', 'E', 'G', 'ni', 'nj', 'nk')] + \
            [f'CD_{w}_{k}{s}' for w in WINDOWS for k in ('pctl', 'rpctl') for s in ('', '_cume', '_mid')]


def mask_cd_without_refs(P: pd.DataFrame, year_col='year') -> pd.DataFrame:
    """Blank the disruption family (CD, F/E/G, n_i/n_j/n_k and CD percentiles) of documents without any
    reference. With no reference, n_j = n_k = 0 by construction and every citer is an n_i, so CD = 1 and
    F = 1 whatever the document did: an artefact of a missing reference list (more than half of the
    pre-1930 papers, about 5 % of papers after 2000). cd_no_refs flags the blanked documents."""
    P = P.copy()
    P['cd_no_refs'] = pd.to_numeric(P.ref_count, errors='coerce').fillna(0).lt(1) & P[year_col].notna()
    cols = [c for c in CD_FAMILY if c in P]
    P.loc[P.cd_no_refs, cols] = np.nan
    return P


def cd_ref_percentiles(con, windows=('5', '10'), log=print):
    """Cohort percentiles of CD among papers WITH references (shared cache, built once for the whole population).

    paper_disruption's CD_W_pctl / _cume rank a paper among all papers of its publication year x first FoS,
    including papers without references, whose CD = 1 fills the top of every old cohort: a paper with references
    could then never reach the top decile. These tables rank CD_W among papers with ref_count >= 1 only, with the
    same cohort keys and conventions: CD_W_rpctl = share strictly below (minimum rank), CD_W_rpctl_cume = share at
    or below. One parquet per window, cache/cd_rpctl_<W>.parquet (about 1 minute on 8 cores)."""
    sources = [OA / 'paper_metadata.parquet', OA / 'paper_disruption.parquet']
    todo = [w for w in windows if not fresh(CACHE / f'cd_rpctl_{w}.parquet', sources)]
    if todo:
        t0 = time.time()
        base = CACHE / f'_cd_withrefs_base.{os.getpid()}.parquet'
        con.execute(f'''COPY (SELECT d.paper_id, m.year, m.fos1, {', '.join(f'd.CD_{w}' for w in todo)}
                              FROM (SELECT paper_id, year, nullif(trim(split_part(FoS_0, ';', 1)), '') AS fos1
                                    FROM read_parquet('{OA / 'paper_metadata.parquet'}') WHERE ref_count >= 1 AND year IS NOT NULL) m
                              JOIN read_parquet('{OA / 'paper_disruption.parquet'}') d USING (paper_id)
                              WHERE m.fos1 IS NOT NULL)
                        TO '{base}' (FORMAT PARQUET)''')
        log(f'[cd_rpctl] base table of papers with references written in {time.time() - t0:.0f}s')
        for w in todo:
            t1 = time.time()
            copy_atomic(con, f'''SELECT paper_id,
                                        (rank() OVER (PARTITION BY year, fos1 ORDER BY CD_{w}) - 1)::DOUBLE
                                            / count(*) OVER (PARTITION BY year, fos1) AS CD_{w}_rpctl,
                                        cume_dist() OVER (PARTITION BY year, fos1 ORDER BY CD_{w}) AS CD_{w}_rpctl_cume
                                 FROM read_parquet('{base}') WHERE CD_{w} IS NOT NULL''', CACHE / f'cd_rpctl_{w}.parquet')
            log(f'[cd_rpctl] window {w}: {time.time() - t1:.0f}s')
        base.unlink(missing_ok=True)
    return {w: CACHE / f'cd_rpctl_{w}.parquet' for w in windows}


def add_cd_ref_percentiles(con, P, table, windows=('5', '10')):
    """Attach CD_W_rpctl, CD_W_rpctl_cume and their mid-point CD_W_rpctl_mid (and CD_W_pctl_mid for the
    all-paper percentiles) to the papers of `table`."""
    paths = cd_ref_percentiles(con, windows)
    P = P.drop(columns=[c for c in P.columns if '_rpctl' in c])
    for w, path in paths.items():
        P = P.merge(semi(con, path, [f'CD_{w}_rpctl', f'CD_{w}_rpctl_cume'], table=table), on='paper_id', how='left')
        P[f'CD_{w}_rpctl_mid'] = (P[f'CD_{w}_rpctl'] + P[f'CD_{w}_rpctl_cume']) / 2
        if 'cd_no_refs' in P:
            P.loc[P.cd_no_refs, [f'CD_{w}_rpctl', f'CD_{w}_rpctl_cume', f'CD_{w}_rpctl_mid']] = np.nan
    for w in WINDOWS:
        if f'CD_{w}_pctl' in P and f'CD_{w}_pctl_cume' in P:
            P[f'CD_{w}_pctl_mid'] = (P[f'CD_{w}_pctl'] + P[f'CD_{w}_pctl_cume']) / 2
    return P


# ---------------------------------------------------------------------------------------------
# Discursive atypicality (DA): shared population tables
# ---------------------------------------------------------------------------------------------
PAPER_DA_TABLE = CACHE / 'paper_da_population.v1.parquet'
PATENT_DA_TABLE = CACHE / 'patent_da_population.v1.parquet'
DA_COLS = ['DA', 'DA_year', 'DA_log', 'DA_pctl']


def paper_da_table(con, log=print):
    """Every paper of the census DA population (scored, article, not retracted, finite PPPL > 0, n_tokens > 0)
    with, keyed on the scoring file's own year and first FoS (the cohort of paper_year_DA_vs_metrics.ipynb):
      DA        z of raw PPPL within year x fos1 (sample sd)      -- the Atypicality definition
      DA_year   z of raw PPPL within year
      DA_log    z of mean NLL (= log PPPL) within year x fos1     -- robust to the heavy PPPL tail
      DA_pctl   mid-rank percentile of PPPL within year x fos1    -- 0..1, comparable across cohorts
    Built once (about a minute) from Atypicality/Data/_traj_cache/paper_year_DA/all_years/paper_metrics.parquet."""
    if not fresh(PAPER_DA_TABLE, [PAPER_DA_CACHE]):
        t0 = time.time()
        copy_atomic(con, f'''
            WITH pop AS (
                SELECT paper_id, year AS da_year, nullif(trim(split_part(FoS_0, ';', 1)), '') AS da_fos1, pppl, mean_nll,
                       n_tokens AS da_n_tokens, model_year AS da_model_year
                FROM read_parquet('{PAPER_DA_CACHE}')
                WHERE doctype = 'article' AND NOT coalesce(is_retracted, false) AND isfinite(pppl) AND pppl > 0 AND n_tokens > 0)
            SELECT paper_id, da_year, da_fos1, pppl, mean_nll, da_n_tokens, da_model_year,
                   CASE WHEN da_fos1 IS NOT NULL THEN (pppl - avg(pppl) OVER f) / stddev_samp(pppl) OVER f END AS DA,
                   (pppl - avg(pppl) OVER y) / stddev_samp(pppl) OVER y AS DA_year,
                   CASE WHEN da_fos1 IS NOT NULL THEN (mean_nll - avg(mean_nll) OVER f) / stddev_samp(mean_nll) OVER f END AS DA_log,
                   CASE WHEN da_fos1 IS NOT NULL THEN ((rank() OVER fo - 1)::DOUBLE / count(*) OVER f + cume_dist() OVER fo) / 2 END AS DA_pctl,
                   CASE WHEN da_fos1 IS NOT NULL THEN count(*) OVER f END AS da_cohort_n
            FROM pop
            WINDOW y AS (PARTITION BY da_year), f AS (PARTITION BY da_year, da_fos1), fo AS (PARTITION BY da_year, da_fos1 ORDER BY pppl)''',
                    PAPER_DA_TABLE)
        log(f'[paper DA] population table built in {time.time() - t0:.0f}s')
    return PAPER_DA_TABLE


def add_paper_da(con, P, table):
    """Attach the DA columns (population members only) with da_scored / da_in_population / da_clip_ok flags."""
    path = paper_da_table(con)
    P = P.drop(columns=[c for c in P.columns if c in DA_COLS or c.startswith('da_') or c in ('pppl', 'mean_nll')])
    da = semi(con, path, ['da_year', 'da_fos1', 'pppl', 'mean_nll', 'da_n_tokens', 'da_model_year', 'DA', 'DA_year', 'DA_log',
                          'DA_pctl', 'da_cohort_n'], table=table)
    P = P.merge(da, on='paper_id', how='left')
    scored = con.sql(f"SELECT DISTINCT paper_id FROM read_parquet('{PAPER_DA_CACHE}') WHERE paper_id IN (SELECT paper_id FROM {table})").df()
    P['da_scored'] = P.paper_id.isin(scored.paper_id)
    P['da_in_population'] = P.da_year.notna()
    P['da_clip_ok'] = P.DA.abs().le(4).where(P.DA.notna())     # the Atypicality analyses keep |DA| <= 4 (CLIP)
    return P


def patent_da_table(con, log=print):
    """Every scored patent of the rev patent master, keyed on filing year x CPC Section (the cohort of
    patent_year_DA_vs._metrics.ipynb): DA (raw-PPPL z within year x Section), DA_year (within filing year, over
    all scored patents = the master's tech_DA_bertbase_filing_lag1), DA_log (mean-NLL z within year x Section) and
    DA_pctl (mid-rank percentile within year x Section). Patents without a Section keep DA_year only."""
    if not fresh(PATENT_DA_TABLE, [PATENT_MASTER]):
        t0 = time.time()
        copy_atomic(con, f'''
            WITH pop AS (
                SELECT patent_id, filing_year AS da_year, cpc_section AS da_section, pat_pppl AS pppl, pat_mean_nll AS mean_nll,
                       pat_n_tokens AS da_n_tokens, pat_ckpt_year AS da_model_year
                FROM read_parquet('{PATENT_MASTER}') WHERE isfinite(pat_pppl) AND pat_pppl > 0 AND pat_n_tokens > 0)
            SELECT *,
                   CASE WHEN da_section IS NOT NULL THEN (pppl - avg(pppl) OVER f) / stddev_samp(pppl) OVER f END AS DA,
                   (pppl - avg(pppl) OVER y) / stddev_samp(pppl) OVER y AS DA_year,
                   CASE WHEN da_section IS NOT NULL THEN (mean_nll - avg(mean_nll) OVER f) / stddev_samp(mean_nll) OVER f END AS DA_log,
                   CASE WHEN da_section IS NOT NULL THEN ((rank() OVER fo - 1)::DOUBLE / count(*) OVER f + cume_dist() OVER fo) / 2 END AS DA_pctl,
                   CASE WHEN da_section IS NOT NULL THEN count(*) OVER f END AS da_cohort_n
            FROM pop
            WINDOW y AS (PARTITION BY da_year), f AS (PARTITION BY da_year, da_section), fo AS (PARTITION BY da_year, da_section ORDER BY pppl)''',
                    PATENT_DA_TABLE)
        log(f'[patent DA] population table built in {time.time() - t0:.0f}s')
    return PATENT_DA_TABLE


def add_patent_da(con, T, table):
    path = patent_da_table(con)
    T = T.drop(columns=[c for c in T.columns if c in DA_COLS or c.startswith('da_') or c in ('pppl', 'mean_nll')])
    da = semi(con, path, ['da_year', 'da_section', 'pppl', 'mean_nll', 'da_n_tokens', 'da_model_year', 'DA', 'DA_year', 'DA_log',
                          'DA_pctl', 'da_cohort_n'], key='patent_id', table=table)
    T = T.merge(da, on='patent_id', how='left')
    T['da_scored'] = T.pppl.notna()
    T['da_clip_ok'] = T.DA.abs().le(4).where(T.DA.notna())
    return T


# ---------------------------------------------------------------------------------------------
# PatentsView inventor ids across disambiguation releases
# ---------------------------------------------------------------------------------------------
def inventor_release_map(old=PQRS_RELEASE, new=None, log=print):
    """(id_old, id_new, n_rows, share_of_old) from g_persistent_inventor: which current inventor ids carry the
    patent rows that an old-release id carried. PatentsView relabels disambiguated ids between releases and the
    pqrs crosswalk uses the 20230330 release; new = the latest release column (that of g_inventor_disambiguated).
    Built once (a few minutes, 1 GB zip streamed in chunks)."""
    src = granted('g_persistent_inventor.tsv.zip')
    header = pd.read_csv(src, sep='\t', nrows=0).columns
    releases = sorted(c.rsplit('_', 1)[1] for c in header if c.startswith('disamb_inventor_id_'))
    new = new or releases[-1]
    path = CACHE / f'inventor_release_map_{old}_{new}.parquet'
    if not fresh(path, [src]):
        t0 = time.time()
        cols = [f'disamb_inventor_id_{old}', f'disamb_inventor_id_{new}']
        parts = []
        for ch in pd.read_csv(src, sep='\t', usecols=cols, dtype=str, keep_default_na=False, chunksize=2_000_000):
            ch = ch[(ch[cols[0]] != '') & (ch[cols[1]] != '')]
            parts.append(ch.groupby(cols).size().reset_index(name='n_rows'))
        m = pd.concat(parts).groupby(cols, as_index=False).n_rows.sum()
        m.columns = ['id_old', 'id_new', 'n_rows']
        m['share_of_old'] = m.n_rows / m.groupby('id_old').n_rows.transform('sum')
        tmp = f'{path}.{os.getpid()}.tmp'
        m.to_parquet(tmp, index=False)
        os.replace(tmp, path)
        log(f'[inventor ids] {old} -> {new} map built in {time.time() - t0:.0f}s ({len(m):,} pairs)')
    return pd.read_parquet(path), old, new


# ---------------------------------------------------------------------------------------------
# Population series and small helpers
# ---------------------------------------------------------------------------------------------
def population_p2p_by_year(con):
    """Paper->paper citations made per citing year over the whole OpenAlex graph (paper_citation_trend): the
    reference coverage of the latest snapshot years is incomplete, so every citing count drops after 2022."""
    path = CACHE / 'p2p_population_by_year.parquet'
    src = OA / 'paper_citation_trend.parquet'
    if not fresh(path, [src]):
        copy_atomic(con, f"SELECT cite_year, sum(p2p) AS p2p_population FROM read_parquet('{src}') GROUP BY 1 ORDER BY 1", path)
    return pd.read_parquet(path)


def random_pctl(lo, hi, seed=0):
    """A percentile drawn uniformly inside a tie block [share below, share at or below]: exactly uniform over the
    cohort, so an ECDF of it can be read against the diagonal even for tie-heavy metrics."""
    lo, hi = pd.to_numeric(lo, errors='coerce'), pd.to_numeric(hi, errors='coerce')
    u = np.random.default_rng(seed).random(len(lo))
    return lo + u * (hi - lo)


def share_at_least(s, thr):
    """Share of documents at or above a threshold, among documents that have a value."""
    s = pd.to_numeric(s, errors='coerce').dropna()
    return float((s >= thr).mean()) if len(s) else np.nan


def share_below(s, thr=0.0):
    s = pd.to_numeric(s, errors='coerce').dropna()
    return float((s < thr).mean()) if len(s) else np.nan


def h_index(citations) -> int:
    c = np.sort(pd.to_numeric(pd.Series(citations), errors='coerce').dropna().to_numpy())[::-1]
    return int((c >= np.arange(1, len(c) + 1)).sum())


# ---------------------------------------------------------------------------------------------
# Lookups shared by both notebooks (PatentsView tables as parquet, PCS rows with PatentsView ids)
# ---------------------------------------------------------------------------------------------
PQRS_PQ = CACHE / 'pqrs_dataset.parquet'
PCS_PQ = CACHE / 'pcs_oa_uspto.v2.parquet'


def _tsv_zip_to_parquet(src, dst, usecols, chunksize=2_000_000):
    import pyarrow as pa
    import pyarrow.parquet as pq
    t0 = time.time(); writer = None; n = 0
    schema = pa.schema([(c, pa.string()) for c in usecols])
    tmp = f'{dst}.{os.getpid()}.tmp'
    for ch in pd.read_csv(src, usecols=usecols, chunksize=chunksize, sep='\t', dtype=str, keep_default_na=False, na_values=['']):
        tbl = pa.Table.from_pandas(ch[usecols], schema=schema, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(tmp, schema, compression='zstd')
        writer.write_table(tbl); n += len(ch)
    writer.close(); os.replace(tmp, dst)
    print(f'{Path(dst).name}: {n:,} rows in {time.time() - t0:.0f}s')


def ensure_lookups(con):
    """Build (once) the shared lookup tables and register the views pqrs, inv, gpat, pginv, pgx, asg, pcs."""
    lookups = {
        'g_inventor_disambiguated.parquet': (granted('g_inventor_disambiguated.tsv.zip'),
            ['patent_id', 'inventor_sequence', 'inventor_id', 'disambig_inventor_name_first', 'disambig_inventor_name_last', 'gender_code', 'location_id']),
        'g_patent_min.parquet': (granted('g_patent.tsv.zip'), ['patent_id', 'patent_type', 'patent_date', 'patent_title', 'num_claims', 'withdrawn']),
        'pg_inventor_disambiguated.parquet': (pregranted('pg_inventor_disambiguated.tsv.zip'),
            ['pgpub_id', 'inventor_sequence', 'inventor_id', 'disambig_inventor_name_first', 'disambig_inventor_name_last']),
        'pg_granted_pgpubs_crosswalk.parquet': (pregranted('pg_granted_pgpubs_crosswalk.tsv.zip'), ['pgpub_id', 'application_id', 'patent_id']),
        'g_assignee_disambiguated.parquet': (granted('g_assignee_disambiguated.tsv.zip'),
            ['patent_id', 'assignee_sequence', 'assignee_id', 'disambig_assignee_individual_name_first', 'disambig_assignee_individual_name_last',
             'disambig_assignee_organization', 'assignee_type']),
    }
    for name, (src, cols) in lookups.items():
        if not fresh(CACHE / name, [src]):
            _tsv_zip_to_parquet(src, CACHE / name, cols)
    if not fresh(PQRS_PQ, [PQRS_TSV]):
        copy_atomic(con, f'''SELECT inventor_id, author_id, "number of comparison" AS n_comparison, "number of match" AS n_match,
                                    scientist_name, inventor_name, name_similarity, flag,
                                    "number of papers" AS n_papers_pqrs, "number of patents" AS n_patents_pqrs, confidence
                             FROM read_csv('{PQRS_TSV}', delim = '\t', header = true)''', PQRS_PQ)
    pcs_table(con)
    con.execute(f"CREATE OR REPLACE VIEW pqrs AS SELECT * FROM read_parquet('{PQRS_PQ}')")
    con.execute(f'''CREATE OR REPLACE VIEW inv AS SELECT patent_id, TRY_CAST(inventor_sequence AS INTEGER) AS inventor_sequence, inventor_id,
                           disambig_inventor_name_first AS name_first, disambig_inventor_name_last AS name_last, gender_code
                    FROM read_parquet('{CACHE / 'g_inventor_disambiguated.parquet'}')''')
    con.execute(f'''CREATE OR REPLACE VIEW gpat AS SELECT patent_id, regexp_replace(patent_id, '^H0+', 'H') AS patent_key, patent_type,
                           TRY_CAST(patent_date AS DATE) AS patent_date, patent_title, TRY_CAST(num_claims AS INTEGER) AS num_claims
                    FROM read_parquet('{CACHE / 'g_patent_min.parquet'}')''')
    con.execute(f"CREATE OR REPLACE VIEW pginv AS SELECT pgpub_id, inventor_id FROM read_parquet('{CACHE / 'pg_inventor_disambiguated.parquet'}')")
    con.execute(f'''CREATE OR REPLACE VIEW pgx AS SELECT DISTINCT pgpub_id, patent_id FROM read_parquet('{CACHE / 'pg_granted_pgpubs_crosswalk.parquet'}')
                    WHERE pgpub_id IS NOT NULL AND patent_id IS NOT NULL''')
    con.execute(f"CREATE OR REPLACE VIEW asg AS SELECT * FROM read_parquet('{CACHE / 'g_assignee_disambiguated.parquet'}')")
    con.execute(f"CREATE OR REPLACE VIEW pcs AS SELECT * FROM read_parquet('{PCS_PQ}')")


def pcs_table(con):
    """Reliance-on-Science rows with PatentsView ids: utility digits, RE / D / PP (incl. pre-2001 plant '-p'), H padded to
    6 digits, pre-grant publications (kinds a1 / a2 / a9 / p1) as 11-digit pgpub ids; non-US rows get NULL."""
    if not fresh(PCS_PQ, [PCS_CSV]):
        copy_atomic(con, f'''
            WITH r AS (SELECT reftype, TRY_CAST(confscore AS INTEGER) AS confscore, TRY_CAST(oaid AS BIGINT) AS oaid, patent, wherefound,
                              regexp_matches(patent, '^us-[a-z]*[0-9]+-[a-z0-9]+$') AS ok,
                              regexp_extract(patent, '^us-([a-z]*)[0-9]+-', 1) AS pre,
                              regexp_extract(patent, '^us-[a-z]*([0-9]+)-', 1) AS digits,
                              regexp_extract(patent, '-([a-z0-9]+)$', 1) AS kind
                       FROM read_csv('{PCS_CSV}', header = true, all_varchar = true))
            SELECT reftype, confscore, oaid, patent, wherefound, kind,
                   CASE WHEN NOT ok OR pre NOT IN ('', 're', 'd', 'pp', 'h') THEN NULL
                        WHEN kind IN ('a1', 'a2', 'a9', 'p1') THEN 'pgpub' ELSE 'grant' END AS doc_kind,
                   CASE WHEN NOT ok OR pre NOT IN ('', 're', 'd', 'pp', 'h') THEN NULL
                        WHEN kind IN ('a1', 'a2', 'a9', 'p1') THEN substr(digits, 1, 4) || lpad(substr(digits, 5), 7, '0')
                        WHEN pre = '' AND kind LIKE 'p%' THEN 'PP' || ltrim(digits, '0')
                        WHEN pre = 'h' THEN 'H' || lpad(ltrim(digits, '0'), 6, '0')
                        WHEN pre = '' THEN ltrim(digits, '0')
                        ELSE upper(pre) || ltrim(digits, '0') END AS patent_id
            FROM r''', PCS_PQ)
    return PCS_PQ


# ---------------------------------------------------------------------------------------------
# Inventors of a set of people and their patents (shared by both notebooks)
# ---------------------------------------------------------------------------------------------
def resolve_inventors(con, people, min_confidence=0.5, min_release_share=0.2):
    """people: DataFrame(group, author_id, ref_name). pqrs candidates of the author ids with confidence >= min_confidence,
    translated from the PatentsView 2023-03-30 release to the current one (ids carrying >= min_release_share of the old
    id's rows), kept when the current inventor name shares a token with ref_name or the pqrs names. Returns one row per
    (group, current inventor id)."""
    con.register('ppl', people.astype({'author_id': 'string'}))
    cand = con.sql(f'''SELECT p.grp, q.inventor_id AS id_old, q.author_id, q.confidence, q.n_match, q.scientist_name, q.inventor_name AS pqrs_inventor_name,
                              p.ref_name
                       FROM pqrs q JOIN (SELECT "group" AS grp, author_id, ref_name FROM ppl) p USING (author_id)
                       WHERE q.confidence >= {min_confidence}''').df()
    rmap, old, new = inventor_release_map()
    cand = cand.merge(rmap[rmap.share_of_old >= min_release_share][['id_old', 'id_new', 'share_of_old']], on='id_old')
    if not len(cand):
        return pd.DataFrame(columns=['group', 'inventor_id', 'id_old', 'confidence', 'current_name', 'name_agrees'])
    con.register('cand_ids', pd.DataFrame({'inventor_id': cand.id_new.astype('string').unique()}))
    names = con.sql('''SELECT inventor_id, mode(trim(coalesce(name_first, '') || ' ' || coalesce(name_last, ''))) AS current_name
                       FROM inv WHERE inventor_id IN (SELECT inventor_id FROM cand_ids) GROUP BY 1''').df().set_index('inventor_id').current_name
    cand['current_name'] = cand.id_new.map(names)
    cand['name_agrees'] = [names_agree(c, r) or names_agree(c, s) or names_agree(c, i)
                           for c, r, s, i in zip(cand.current_name.fillna(''), cand.ref_name.fillna(''), cand.scientist_name.fillna(''),
                                                 cand.pqrs_inventor_name.fillna(''))]
    out = (cand[cand.name_agrees].sort_values('confidence', ascending=False)
           .drop_duplicates(['grp', 'id_new']).rename(columns={'grp': 'group', 'id_new': 'inventor_id'}))
    return out[['group', 'inventor_id', 'id_old', 'author_id', 'confidence', 'current_name', 'name_agrees']]


def assemble_patent_metrics(con, table='ego_t'):
    """One row per patent_id of `table` (utility patents) with the PatentView metrics, the patent DA inputs and PPP fields (cacheable)."""
    T = con.sql(f"SELECT DISTINCT patent_id FROM {table}").df().astype(object)
    k = dict(key='patent_id', table=table)
    T = T.merge(semi(con, PV / 'patent_metadata.parquet', ['grant_year', 'filing_year', 'ref_count', 'cpc_code', 'cpc_code_list', 'assignee_list'], **k), how='left')
    cit = [f'{c}_{w}' for w in WINDOWS for c in ('C', 'appC', 'uniqueC')] + [f'C_{s}_{w}' for w in WINDOWS for s in ('examiner', 'non_examiner', 'unknown')]
    T = T.merge(semi(con, PV / 'patent_citation.parquet', cit, **k), how='left')
    T = T.merge(semi(con, PV / 'patent_hit_probability.parquet', ['wipo_sector'] + [f'pctl_uniqueC_{w}' for w in WINDOWS] +
                     ['pctl_C_5', 'pctl_C_all', 'pctl_appC_5'], **k), how='left')
    T = T.merge(semi(con, PV / 'patent_disruption.parquet', CD_COLS + CD_PCTL_COLS + ['pctl_year', 'pctl_group'], **k), how='left')
    T = T.merge(semi(con, PV / 'patent_z_score.parquet', ['Z_median', 'Z_10pct', 'Z_min', 'n_pairs'], **k), how='left')
    T = T.merge(semi(con, PV / 'patent_sb.parquet', ['SB_B', 'SB_T', 'n_cite'], **k), how='left')
    T = T.merge(semi(con, PV / 'patent_inventor_country.parquet', ['n_inventors', 'n_located', 'n_countries', 'countries', 'is_international',
                                                               'first_inventor_country', 'assignee_countries'], **k), how='left')
    ppp = con.sql(f'''SELECT patent_id, any_value(tech_DA_year_cohort) AS ppp_tech_DA_year, any_value(tech_DA_year_section_cohort) AS ppp_tech_DA_year_section,
                             count(*) AS n_ppp_pairs, string_agg(DISTINCT paper_id, ';') AS ppp_paper_ids
                      FROM read_parquet('{PPP_MASTER}') WHERE patent_id IN (SELECT patent_id FROM {table}) GROUP BY patent_id''').df()
    refs = con.sql(f'''SELECT patent_id, count(DISTINCT oaid) AS n_paper_refs FROM pcs WHERE doc_kind = 'grant' AND patent_id IN (SELECT patent_id FROM {table})
                       GROUP BY 1''').df()
    return T.merge(ppp, on='patent_id', how='left').merge(refs, on='patent_id', how='left')


def finish_patent_metrics(con, T, table, window_end, require_refs=True):
    """Zero-fills, DA, the no-reference CD mask, the percentile columns of every measure and the open-window mask."""
    T = T.copy()
    for c in ['grant_year', 'filing_year']:
        T[c] = pd.to_numeric(T[c], errors='coerce').astype('Int64') if c in T else pd.Series(pd.NA, index=T.index, dtype='Int64')
    cnt = [f'{c}_{w}' for w in WINDOWS for c in ('C', 'appC', 'uniqueC')] + [f'C_{s}_{w}' for w in WINDOWS for s in ('examiner', 'non_examiner', 'unknown')]
    for c in [c for c in cnt if c in T]:
        T[c] = pd.to_numeric(T[c], errors='coerce').fillna(0).astype('Int64').where(T.grant_year.notna())
    T['n_paper_refs'] = pd.to_numeric(T.get('n_paper_refs'), errors='coerce').fillna(0).astype(int)
    T['cpc_section'] = T.get('cpc_code', pd.Series(pd.NA, index=T.index)).astype('string').str[:1]
    T['in_ppp'] = T.get('n_ppp_pairs', pd.Series(np.nan, index=T.index)).notna()
    T = add_patent_da(con, T, table)
    if require_refs and 'ref_count' in T:
        T = mask_cd_without_refs(T, year_col='grant_year')
    for w in WINDOWS:
        if f'CD_{w}_pctl' in T:
            T[f'CD_{w}_pctl_mid'] = (T[f'CD_{w}_pctl'] + T[f'CD_{w}_pctl_cume']) / 2
    T = add_patent_percentiles(con, T, table)
    return mask_open_windows(T, 'grant_year', window_end, patent_window_cols)


PAPER_MEASURES = [   # key, label, mid-rank percentile column
    ('impact5', 'Impact: citations, 5 years', 'C_5_pctl'),
    ('impact10', 'Impact: citations, 10 years', 'C_10_pctl'),
    ('techlink', 'Cited by patents within 5 years', 'pcs_C_5_pctl'),
    ('disruption', 'Disruption (CD, 5 years)', 'CD_5_rpctl_mid'),
    ('F', 'Foundation share (5 years)', 'F_5_pctl'),
    ('E', 'Extension share (5 years)', 'E_5_pctl'),
    ('G', 'Generalization share (5 years)', 'G_5_pctl'),
    ('novelty', 'Novelty (atypical pairs, low Z_10pct)', 'novelty_pctl'),
    ('conventionality', 'Conventionality (Z_median)', 'Z_median_pctl'),
    ('DA', 'Discursive atypicality (DA)', 'DA_pctl'),
    ('SB', 'Sleeping beauty (SB_B)', 'SB_B_pctl'),
    ('books', 'Cited by books (textbook reach)', 'book_cites_pctl'),
]
PATENT_MEASURES = [
    ('impact5', 'Impact: citations, 5 years (uniqueC)', 'uniqueC_5_pctl'),
    ('techlink', 'Science linkage: papers cited', 'n_paper_refs_pctl'),
    ('disruption', 'Disruption (CD, 5 years)', 'CD_5_rpctl_mid'),
    ('F', 'Foundation share (5 years)', 'F_5_pctl'),
    ('E', 'Extension share (5 years)', 'E_5_pctl'),
    ('G', 'Generalization share (5 years)', 'G_5_pctl'),
    ('novelty', 'Novelty (atypical CPC pairs, low Z_10pct)', 'novelty_pctl'),
    ('conventionality', 'Conventionality (Z_median)', 'Z_median_pctl'),
    ('DA', 'Discursive atypicality (DA)', 'DA_pctl'),
    ('SB', 'Sleeping beauty (SB_B)', 'SB_B_pctl'),
]


def save_plotly_html(fig, path, written=None):
    """Interactive page next to the PNGs; plotly.min.js is written once into the same directory (offline)."""
    fig.update_layout(template='plotly_white', font=dict(family='Arial, Helvetica, sans-serif', size=12, color=INK),
                      margin=dict(l=70, r=40, t=90, b=60))
    fig.write_html(path, include_plotlyjs='directory', config={'displaylogo': False, 'scrollZoom': True,
                                                              'toImageButtonOptions': {'format': 'png', 'scale': 2}})
    if written is not None:
        written.append(Path(path))


# ---------------------------------------------------------------------------------------------
# Networks (PNG + interactive HTML) and the dashboard page (used by nobel_laureate_papers.ipynb)
# ---------------------------------------------------------------------------------------------
def entity_graph(rows, doc_col, ent_col, name_map=None, year_map=None):
    """Nodes = entities on the documents (n_shared = documents), edges = two entities on the same document."""
    import networkx as nx
    rows = rows.dropna(subset=[ent_col]).drop_duplicates([doc_col, ent_col]).copy()
    rows['year'] = rows[doc_col].map(year_map).astype(float) if year_map is not None else np.nan
    nodes = (rows.groupby(ent_col).agg(n_shared=(doc_col, 'nunique'), first_year=('year', 'min'), last_year=('year', 'max'))
             .reset_index().rename(columns={ent_col: 'id'}))
    nodes['name'] = nodes.id.map(name_map or {}).fillna(nodes.id).astype(str)
    nodes = nodes.sort_values(['n_shared', 'last_year', 'id'], ascending=[False, False, True], kind='mergesort', na_position='last').reset_index(drop=True)
    pr = rows[[doc_col, ent_col]]
    pairs = pr.merge(pr, on=doc_col)
    pairs = pairs[pairs[f'{ent_col}_x'] < pairs[f'{ent_col}_y']]
    edges = pairs.groupby([f'{ent_col}_x', f'{ent_col}_y']).size().reset_index(name='weight')
    edges.columns = ['source', 'target', 'weight']
    G = nx.Graph()
    for r in nodes.itertuples():
        a = {'name': r.name, 'n_shared': int(r.n_shared)}
        if pd.notna(r.first_year):
            a['first_year'] = int(r.first_year)
        G.add_node(r.id, **a)
    G.add_weighted_edges_from(edges.itertuples(index=False, name=None))
    return nodes, edges, G


def hub_layout(H, weight='weight', seed=7):
    import networkx as nx
    Hl = H.copy(); hub = '__hub__'
    Hl.add_edges_from((hub, n, {'weight': 1}) for n in H)
    pos = nx.spring_layout(Hl, weight=weight, k=1.4 / math.sqrt(max(H.number_of_nodes(), 2)), seed=seed, iterations=300)
    pos.pop(hub)
    return pos


def _ramp(cmap):
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    return ListedColormap(plt.get_cmap(cmap)(np.linspace(.3, 1, 256)))


def draw_network(G, nodes, top_k, title, cmap, png_path, html_path=None, html_top_k=150, label_top=12, subtitle='', written=None):
    """PNG of the top_k nodes and an interactive page of the top html_top_k nodes (hover: name, id, documents, first year)."""
    import matplotlib.pyplot as plt
    import networkx as nx
    import plotly.graph_objects as go
    from matplotlib.colors import to_hex
    ids = nodes[nodes.id.isin(set(G.nodes))].head(top_k).id.tolist()
    H = G.subgraph(ids).copy()
    if H.number_of_nodes() == 0:
        return None
    fig, ax = plt.subplots(figsize=(11, 9))
    pos = hub_layout(H)
    w = np.array([d['weight'] for _, _, d in H.edges(data=True)], dtype=float)
    if len(w):
        nx.draw_networkx_edges(H, pos, ax=ax, width=0.4 + 3.0 * w / w.max(), alpha=.3, edge_color=GREY)
    nmax = max(H.nodes[n]['n_shared'] for n in H)
    ns = {n: 60 + 900 * H.nodes[n]['n_shared'] / nmax for n in H}
    dated = [n for n in H if 'first_year' in H.nodes[n]]; undated = [n for n in H if n not in dated]
    if undated:
        nx.draw_networkx_nodes(H, pos, nodelist=undated, ax=ax, node_size=[ns[n] for n in undated], node_color=GREY, edgecolors='white', linewidths=.6)
    if dated:
        fy = np.array([H.nodes[n]['first_year'] for n in dated], dtype=float)
        sc = nx.draw_networkx_nodes(H, pos, nodelist=dated, ax=ax, node_size=[ns[n] for n in dated], node_color=fy, cmap=_ramp(cmap),
                                    vmin=fy.min(), vmax=max(fy.max(), fy.min() + 1), edgecolors='white', linewidths=.6, alpha=.92)
        fig.colorbar(sc, ax=ax, fraction=.03, pad=.01).set_label('first year')
    for n in ids[:label_top]:
        x, y = pos[n]
        ax.annotate(H.nodes[n]['name'], (x, y), xytext=(0, 4 + math.sqrt(ns[n]) / 2), textcoords='offset points', ha='center', fontsize=7.5, color=INK)
    ax.set_title(title + (f'\n{subtitle}' if subtitle else ''), fontsize=10)
    ax.axis('off'); ax.grid(False)
    fig.savefig(png_path, bbox_inches='tight'); plt.close(fig)
    if written is not None:
        written.append(Path(png_path))
    if html_path is None:
        return None
    ids = nodes[nodes.id.isin(set(G.nodes))].head(html_top_k).id.tolist()
    H = G.subgraph(ids).copy(); pos = hub_layout(H)
    info = nodes.set_index('id')
    ws = [d['weight'] for _, _, d in H.edges(data=True)] or [1]
    hf = go.Figure()
    for lo, hi in [(0, .15), (.15, .35), (.35, .65), (.65, 1.01)]:
        xs, ys = [], []
        for a, b, d in H.edges(data=True):
            if lo <= d['weight'] / max(ws) < hi:
                xs += [pos[a][0], pos[b][0], None]; ys += [pos[a][1], pos[b][1], None]
        if xs:
            hf.add_trace(go.Scatter(x=xs, y=ys, mode='lines', line=dict(color=GREY, width=.6 + 5 * hi), opacity=.25 + .35 * hi, hoverinfo='skip', showlegend=False))
    nmax = max(H.nodes[n]['n_shared'] for n in H)
    cm = _ramp(cmap)
    hf.add_trace(go.Scatter(
        x=[pos[n][0] for n in H], y=[pos[n][1] for n in H], mode='markers+text',
        text=[H.nodes[n]['name'] if n in ids[:label_top] else '' for n in H], textposition='top center', textfont=dict(size=10),
        hovertext=[f"<b>{info.loc[n, 'name']}</b><br>{n}<br>documents: {int(info.loc[n, 'n_shared'])}"
                   + (f"<br>first year: {int(info.loc[n, 'first_year'])}" if pd.notna(info.loc[n, 'first_year']) else '') for n in H],
        hoverinfo='text', showlegend=False,
        marker=dict(size=[7 + 30 * math.sqrt(H.nodes[n]['n_shared'] / nmax) for n in H],
                    color=[H.nodes[n].get('first_year', np.nan) for n in H], colorscale=[[t, to_hex(cm(t))] for t in np.linspace(0, 1, 11)],
                    showscale=True, colorbar=dict(title='first<br>year'), line=dict(color='white', width=1))))
    hf.update_xaxes(visible=False); hf.update_yaxes(visible=False, scaleanchor='x')
    hf.update_layout(title=f'{title}<br><sup>{subtitle}; scroll to zoom, hover for details</sup>', height=880, dragmode='pan', plot_bgcolor='white')
    save_plotly_html(hf, html_path, written)
    return hf


DASHBOARD_CSS = '''
:root { --ground:#f4f6f5; --surface:#ffffff; --ink:#16201c; --muted:#5a6761; --rule:#dce3df; --soft:#eef2f0;
        --works:#2a78d6; --patents:#eb6834; --links:#1baf7a; color-scheme: light; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --ground:#111614; --surface:#18201c; --ink:#e6ebe8; --muted:#9daea6;
        --rule:#2b3631; --soft:#1f2924; --works:#3987e5; --patents:#d95926; --links:#199e70; color-scheme: dark; } }
:root[data-theme="dark"] { --ground:#111614; --surface:#18201c; --ink:#e6ebe8; --muted:#9daea6; --rule:#2b3631; --soft:#1f2924;
        --works:#3987e5; --patents:#d95926; --links:#199e70; color-scheme: dark; }
html, body { margin: 0; }
body { background: var(--ground); color: var(--ink); font: 15px/1.5 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.wrap { max-width: 1280px; margin: 0 auto; padding-inline: 20px; padding-block: 28px 48px; display: grid; gap: 22px; }
header { display: grid; gap: 6px; }
.eyebrow { font: 500 12px 'IBM Plex Mono', ui-monospace, monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
h1 { font: 600 clamp(28px, 4vw, 40px)/1.1 'Source Serif 4', Georgia, serif; margin: 0; text-wrap: balance; }
.ids { font: 13px 'IBM Plex Mono', ui-monospace, monospace; color: var(--muted); display: flex; flex-wrap: wrap; gap: 6px 16px; }
.ids a { color: inherit; }
.scope { color: var(--muted); max-width: 80ch; margin: 0; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.tile { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 16px; display: grid; gap: 2px; align-content: start; }
.tlabel { font-size: 12px; letter-spacing: .04em; text-transform: uppercase; color: var(--muted); }
.tvalue { font: 600 28px/1.15 'IBM Plex Sans', sans-serif; font-variant-numeric: tabular-nums; }
.tnote { font-size: 12.5px; color: var(--muted); }
html { scroll-behavior: smooth; }
nav.toc { position: sticky; top: 0; z-index: 10; display: flex; gap: 2px; overflow-x: auto; background: var(--ground);
          border-bottom: 1px solid var(--rule); padding-block: 6px; }
nav.toc a { font: 500 14px 'IBM Plex Sans', sans-serif; color: var(--muted); text-decoration: none; padding: 8px 12px; border-radius: 6px; white-space: nowrap; }
nav.toc a:hover, nav.toc a:focus-visible { color: var(--ink); background: var(--soft); outline: none; }
input:focus-visible { outline: 2px solid var(--works); outline-offset: 2px; }
.section { display: grid; gap: 18px; scroll-margin-top: 64px; }
.section > h2 { margin: 18px 0 0; font: 600 22px 'Source Serif 4', Georgia, serif; }
.card { background: var(--surface); border: 1px solid var(--rule); border-radius: 10px; padding: 16px 18px; min-width: 0; }
.card h3 { margin: 0 0 2px; font: 600 17px 'IBM Plex Sans', sans-serif; }
.cap { margin: 0 0 10px; color: var(--muted); font-size: 13.5px; max-width: 95ch; }
.plot { width: 100%; min-height: 360px; }
.tablewrap { overflow-x: auto; max-height: 640px; overflow-y: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font-weight: 500; color: var(--muted); font-size: 12px; letter-spacing: .03em; text-transform: uppercase; position: sticky; top: 0; background: var(--surface); }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.muted { color: var(--muted); }
.id { font: 11.5px 'IBM Plex Mono', monospace; color: var(--muted); }
td a { color: var(--ink); text-decoration-color: var(--rule); }
.pbar { display: inline-block; width: 56px; height: 6px; margin-right: 8px; vertical-align: middle; background: var(--soft); border-radius: 3px; overflow: hidden; }
.pbar i { display: block; height: 100%; background: var(--works); }
.filter { font: 14px 'IBM Plex Sans', sans-serif; color: var(--ink); background: var(--surface); border: 1px solid var(--rule); border-radius: 8px;
          padding: 8px 12px; width: min(420px, 100%); margin-bottom: 10px; }
footer { color: var(--muted); font-size: 12.5px; max-width: 95ch; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
'''

DASHBOARD_JS = '''
(function () {
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const drawn = new Set();
  function themed(layout) {
    const L = Object.assign({}, layout);
    L.paper_bgcolor = 'rgba(0,0,0,0)'; L.plot_bgcolor = 'rgba(0,0,0,0)';
    L.font = Object.assign({}, L.font || {}, { color: css('--ink'), family: "'IBM Plex Sans', system-ui, sans-serif" });
    L.hoverlabel = { bgcolor: css('--surface'), bordercolor: css('--rule'), font: { color: css('--ink') } };
    L.legend = Object.assign({}, L.legend || {}, { bgcolor: 'rgba(0,0,0,0)' });
    Object.keys(L).forEach(k => { if (/^[xy]axis\\d*$/.test(k)) L[k] = Object.assign({}, L[k], { gridcolor: css('--rule'), zerolinecolor: css('--rule'), linecolor: css('--rule') }); });
    (L.annotations || []).forEach(a => { a.font = Object.assign({}, a.font || {}, { color: css('--ink') }); });
    L.autosize = true; delete L.width;
    return L;
  }
  function draw(el) {
    if (drawn.has(el.id) || !window.Plotly) return;
    const src = document.getElementById('f-' + el.dataset.fig);
    if (!src) return;
    try {
      const fig = JSON.parse(src.textContent);
      el.style.minHeight = ((fig.layout && fig.layout.height) || 420) + 'px';
      Plotly.newPlot(el, fig.data, themed(fig.layout || {}), { responsive: true, displaylogo: false, scrollZoom: false });
      drawn.add(el.id);
    } catch (e) { el.textContent = 'This figure could not be drawn: ' + e.message; }
  }
  function retheme() { drawn.forEach(id => { const el = document.getElementById(id); const f = JSON.parse(document.getElementById('f-' + el.dataset.fig).textContent);
                                            Plotly.relayout(el, themed(f.layout || {})); }); }
  document.querySelectorAll('input.filter').forEach(inp => inp.addEventListener('input', () => {
    const q = inp.value.trim().toLowerCase();
    document.querySelectorAll('#' + inp.dataset.table + ' tbody tr').forEach(tr => { tr.hidden = q && !tr.textContent.toLowerCase().includes(q); });
  }));
  const plots = Array.from(document.querySelectorAll('.plot'));   // every figure is drawn at load: no tab has to be clicked
  if (!window.Plotly) plots.forEach(el => { el.textContent = 'plotly.js did not load.'; });
  if (window.Plotly) plots.forEach(draw);          // every figure is drawn at load, synchronously: nothing waits for a click or a timer
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', retheme);
  new MutationObserver(retheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
})();
'''


def render_dashboard(path, title, eyebrow, heading, scope_html, tiles, tabs, figs, footer_html, ids_html='', standalone=True):
    """Write a standalone dashboard page. tiles: [(label, value, note)]; tabs: [(key, label, [block, ...])] where a block is
    ('fig', name, title, caption) or ('html', title, caption, html); figs: {name: plotly figure}. standalone=True embeds
    plotly.js in the page (one file that works offline, ~4 MB more); False loads html/plotly.min.js next to the page
    (jsDelivr when that file is missing)."""
    import html as _h
    import plotly
    import plotly.graph_objects as go
    e = lambda x: _h.escape('' if x is None else str(x))
    tiles_html = ''.join(f'<div class="tile"><div class="tlabel">{e(a)}</div><div class="tvalue">{e(b)}</div><div class="tnote">{e(c)}</div></div>'
                         for a, b, c in tiles)
    nav = ''.join(f'<a href="#sec-{k}">{e(lab)}</a>' for k, lab, _ in tabs)     # plain links: no script needed
    panels, scripts = [], []
    for k, lab, blocks in tabs:
        cards = []
        for b in blocks:
            if b[0] == 'fig':
                _, name, t, cap = b
                if name not in figs:
                    continue
                cards.append(f'<section class="card"><h3>{e(t)}</h3><p class="cap">{e(cap)}</p><div class="plot" id="p-{name}" data-fig="{name}"></div></section>')
                f = go.Figure(figs[name])     # the card title names the figure: its own title is dropped (subplot titles stay)
                f.update_layout(title=None, margin=dict(t=50 if f.layout.annotations else 20))
                scripts.append(f'<script type="application/json" id="f-{name}">{f.to_json().replace("</", "<" + chr(92) + "/")}</script>')
            else:
                _, t, cap, body = b
                cards.append(f'<section class="card"><h3>{e(t)}</h3>' + (f'<p class="cap">{e(cap)}</p>' if cap else '') + f'{body}</section>')
        panels.append(f'<section class="section" id="sec-{k}"><h2>{e(lab)}</h2>{"".join(cards) or "<p class=muted>No data for this view.</p>"}</section>')
    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600&display=swap">
<style>{DASHBOARD_CSS}</style>
</head>
<body>
<div class="wrap">
<header><div class="eyebrow">{e(eyebrow)}</div><h1>{e(heading)}</h1>{ids_html}<p class="scope">{scope_html}</p></header>
<div class="tiles">{tiles_html}</div>
<nav class="toc" aria-label="Sections">{nav}</nav>
{"".join(panels)}
<footer>{footer_html}</footer>
</div>
{"".join(scripts)}
{plotly_tag(standalone)}
<script>{DASHBOARD_JS}</script>
</body>
</html>
'''
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(f'{path}.{os.getpid()}.tmp')
    tmp.write_text(page, encoding='utf-8'); os.replace(tmp, path)
    return Path(path)


def clip_years(fig, last, first=1800):
    """For a dashboard figure: drop the points of calendar-year x axes after `last` and end those axes at `last`, so the
    incomplete recent years (citations still accruing, reference coverage gaps) do not show as a decline. A trace counts
    as a year trace when every x is a whole number between `first` and 2100; horizontal bars are left alone."""
    lows = {}
    for tr in fig.data:
        if getattr(tr, 'orientation', None) == 'h' or getattr(tr, 'x', None) is None:
            continue
        x = pd.to_numeric(pd.Series(list(tr.x)), errors='coerce')
        xv = x.dropna()
        if xv.empty or not xv.between(first, 2100).all() or (xv % 1 != 0).any():
            continue
        keep = (x.isna() | (x <= last)).to_numpy()
        n = len(x)
        for attr in ('x', 'y', 'customdata', 'hovertext', 'text'):
            v = getattr(tr, attr, None)
            if v is not None and not isinstance(v, str) and hasattr(v, '__len__') and len(v) == n:
                setattr(tr, attr, [a for a, k in zip(list(v), keep) if k])
        m = getattr(tr, 'marker', None)
        if m is not None:
            for attr in ('color', 'size'):
                v = getattr(m, attr, None)
                if v is not None and not isinstance(v, str) and hasattr(v, '__len__') and len(v) == n:
                    setattr(m, attr, [a for a, k in zip(list(v), keep) if k])
        ax = 'xaxis' + (tr.xaxis[1:] if getattr(tr, 'xaxis', None) not in (None, 'x') else '')
        if keep.any() and x[keep].notna().any():
            lows[ax] = min(lows.get(ax, x[keep].min()), x[keep].min())
    for ax, lo in lows.items():
        fig.layout[ax].range = [lo - .5, last + .5]
    return fig


def plotly_tag(standalone=True):
    """The <script> that provides Plotly to a dashboard: plotly.js itself (standalone) or html/plotly.min.js + a CDN fallback."""
    import plotly
    if standalone:
        return f'<script>{plotly.offline.get_plotlyjs()}</script>'
    ver = plotly.offline.get_plotlyjs_version()
    return ('<script src="html/plotly.min.js"></script>\n'
            f"<script>window.Plotly || document.write('<script src=\"https://cdn.jsdelivr.net/npm/plotly.js-dist-min@{ver}/plotly.min.js\"><' + '/script>');</script>")


# ---------------------------------------------------------------------------------------------
# Dashboard folder: output/dashboard/<year>_<field>_<name>_<id>.html (standalone pages)
# ---------------------------------------------------------------------------------------------
DASHBOARD_DIR = NP / 'output' / 'dashboard'
PRIZEATLAS_LAUREATES = NP / 'Data' / 'prizeatlas' / 'prizeatlas_nobel_laureates.parquet'
LAUREATE_BRIDGE = NP / 'output' / 'nobel_laureates' / 'laureate_author_map.csv'


_TRANSLIT_TABLE = str.maketrans({**TRANSLIT, **{k.upper(): v.capitalize() for k, v in TRANSLIT.items() if len(k.upper()) == 1}})


def prizeatlas_available() -> bool:
    return PRIZEATLAS_LAUREATES.exists() or PRIZEATLAS_LAUREATES.with_suffix('.csv').exists()


def prizeatlas_table(columns=None) -> pd.DataFrame:
    """The PrizeAtlas laureate table (notebook/prizeatlas_crawl.ipynb): the parquet when present, else its CSV twin (the git
    repository keeps no parquet file)."""
    if PRIZEATLAS_LAUREATES.exists():
        return pd.read_parquet(PRIZEATLAS_LAUREATES, columns=columns)
    csv = PRIZEATLAS_LAUREATES.with_suffix('.csv')
    if csv.exists():
        return pd.read_csv(csv, usecols=columns, dtype={'openalex_author_id': str, 'orcid': str, 'wikidata_qid': str, 'ror': str})
    return pd.DataFrame(columns=columns or [])


def file_part(s, empty='NA') -> str:
    """One part of a dashboard file name: ASCII letters and digits joined by '-' ('_' separates the parts)."""
    s = '' if s is None or (isinstance(s, float) and math.isnan(s)) else str(s)
    s = unicodedata.normalize('NFKD', s.translate(_TRANSLIT_TABLE)).encode('ascii', 'ignore').decode()
    return re.sub(r'[^A-Za-z0-9]+', '-', s).strip('-') or empty


def dashboard_path(year, field, name, ident) -> Path:
    """output/dashboard/<year>_<field>_<name>_<id>.html; missing parts become 'NA'."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    parts = [file_part(year)[:40].rstrip('-') or 'NA', file_part(field)[:40].rstrip('-') or 'NA', file_part(name)[:80].rstrip('-') or 'NA', file_part(ident)]
    return DASHBOARD_DIR / ('_'.join(parts) + '.html')      # the id stays whole: names are unique by it


def nobel_identity(author_ids, name=None, orcids=(), log=print, use_name=True) -> dict:
    """Prize year(s), field(s) and name of a Nobel laureate, for the dashboard file name and header. Looked up in the
    PrizeAtlas crawl (Data/prizeatlas) by OpenAlex author id, then ORCID, then a unique first + last name without
    conflicting middle initials (PrizeAtlas often lists another OpenAlex fragment of the same person); else in the
    laureate notebook's author bridge (Li et al. laureates 1902-2016). {} when nothing matches. Several prizes are
    joined with '-' (e.g. year '1956-1972')."""
    ids = {str(a).strip() for a in author_ids if a}
    orcids = {str(o).rstrip('/').rsplit('/', 1)[-1] for o in orcids if o}
    if prizeatlas_available():
        pa = prizeatlas_table(['year', 'category_en', 'name', 'openalex_author_id', 'orcid', 'wikidata_qid', 'url'])
        oa = pa.openalex_author_id.fillna('').str.split(r';\s*')
        hit, rule = pa[oa.apply(lambda l: bool(ids & set(l)))], 'PrizeAtlas OpenAlex id'
        if hit.wikidata_qid.nunique() > 1:                         # one OpenAlex id on two laureates' pages (G. E. / G. P. Smith)
            by_orcid = hit[hit.orcid.isin(orcids)] if orcids else hit.iloc[0:0]
            by_name = hit[hit.name.apply(lambda n: bool(_clean_person(n) and name and name_key(_clean_person(n)) == name_key(_clean_person(name))
                                         and not middle_conflict(_clean_person(n), _clean_person(name)))).astype(bool)]
            hit = by_orcid if by_orcid.wikidata_qid.nunique() == 1 else by_name if by_name.wikidata_qid.nunique() == 1 else hit.iloc[0:0]
            rule = 'PrizeAtlas OpenAlex id shared by several laureates; ' + ('ORCID' if len(by_orcid) else 'name') + ' decides'
            if hit.empty:
                log('the OpenAlex id is on several laureates\' PrizeAtlas pages and neither ORCID nor name decides')
        if hit.empty and orcids:
            hit, rule = pa[pa.orcid.fillna('').isin(orcids)], 'PrizeAtlas ORCID'
        if hit.empty and use_name and name and name_key(_clean_person(name)):   # use_name=False: ids and ORCID only (non-laureates)
            k = name_key(_clean_person(name))
            m = pa[pa.name.apply(lambda n: name_key(_clean_person(n)) == k and not middle_conflict(_clean_person(n), _clean_person(name))).astype(bool)]
            if orcids:                                             # an ORCID on both sides that differs rules the page out
                m = m[m.orcid.isna() | m.orcid.isin(orcids)]
            if m.wikidata_qid.nunique() == 1:                      # one person, possibly several prizes
                hit, rule = m, 'PrizeAtlas name (unverified)'
        if len(hit):
            hit = hit.sort_values('year')
            out = {'year': '-'.join(dict.fromkeys(hit.year.astype(int).astype(str))), 'field': '-'.join(dict.fromkeys(hit.category_en.astype(str))),
                   'name': str(hit.name.iloc[0]), 'rule': rule, 'wikidata_qid': hit.wikidata_qid.iloc[0],
                   'prizeatlas_openalex_id': '; '.join(dict.fromkeys(hit.openalex_author_id.dropna())), 'prizeatlas_url': hit.url.iloc[0],
                   'prizes': list(dict.fromkeys(f'{c} {int(y)}' for c, y in zip(hit.category_en, hit.year)))}
            log(f"Nobel laureate: {out['name']}, {', '.join(out['prizes'])} ({rule})")
            return out
    else:
        log(f'{PRIZEATLAS_LAUREATES} not found (notebook/prizeatlas_crawl.ipynb); trying the laureate author bridge')
    if LAUREATE_BRIDGE.exists():
        b = pd.read_csv(LAUREATE_BRIDGE, dtype=str)
        frag = b.fragment_ids.fillna('').str.split(';')
        hit = b[b.primary_author_id.isin(ids) | frag.apply(lambda l: bool(ids & set(l)))].sort_values('prize_year')
        if hit.name.nunique() > 1 and name:                        # fragments shared by namesakes: keep the one whose name agrees
            hit = hit[hit.name.map(lambda n: names_agree(n, name)).astype(bool)]
        if len(hit) and hit.name.nunique() == 1:
            out = {'year': '-'.join(dict.fromkeys(hit.prize_year)), 'field': '-'.join(dict.fromkeys(hit.field)), 'name': name or hit.name.iloc[0],
                   'rule': 'laureate author bridge (Li et al.)', 'prizes': list(dict.fromkeys(f'{f} {y}' for f, y in zip(hit.field, hit.prize_year)))}
            log(f"Nobel laureate: {out['name']}, {', '.join(out['prizes'])} ({out['rule']})")
            return out
    log('not found among the Nobel laureates')
    return {}


def _clean_person(s) -> str:
    """A person name without honorifics, suffixes, maiden names and parentheses ('Sir J. Fraser Stoddart' -> 'J. Fraser Stoddart',
    'Marie Curie, née Sklodowska' -> 'Marie Curie', 'Lord (Alexander R.) Todd' -> 'Todd')."""
    if not isinstance(s, str):
        return ''
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.split(r'(?:,\s*|\s+)(?:née|nee|born)\b', s, flags=re.I)[0]
    s = re.sub(r'^\s*(?:(?:sir|lord|lady|dame|baron|baroness|prof\.?|professor|dr\.?)\s+)+', '', s, flags=re.I)
    s = re.sub(r'[,\s]+(?:jr\.?|sr\.?|ii|iii|iv)\s*$', '', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip()


# ---------------------------------------------------------------------------------------------
# Inventor search by name in PatentsView (fallback when pqrs has no inventor for an author)
# ---------------------------------------------------------------------------------------------
LOCATION_PQ = CACHE / 'g_location_disambiguated.parquet'
ORG_STOP = {'university', 'universite', 'universitat', 'universita', 'universidad', 'universidade', 'college', 'institute', 'institut',
            'instituto', 'istituto', 'school', 'department', 'faculty', 'center', 'centre', 'hospital', 'laboratory', 'laboratories', 'research',
            'foundation', 'national', 'company', 'corporation', 'limited', 'gmbh', 'technologies', 'technology', 'regents', 'trustees',
            'board', 'society', 'medical', 'medicine', 'sciences', 'science', 'united', 'kingdom', 'states', 'america', 'group', 'holdings',
            'international', 'incorporated', 'the', 'and', 'health', 'system', 'systems', 'services', 'fellows', 'president', 'california',
            'york', 'texas', 'massachusetts', 'japan', 'china', 'germany', 'france', 'london', 'paris', 'tokyo', 'city', 'state'}


def org_tokens(s) -> set:
    """Distinctive tokens of an organisation name ('DeepMind Technologies Limited' -> {'deepmind'}); generic words and
    place names that many organisations share are left out."""
    return {t for t in re.split(r'[^a-z0-9]+', fold(s)) if len(t) >= 4 and t not in ORG_STOP} if isinstance(s, str) else set()


def _raw_name_tokens(s) -> list:
    """Letter tokens of a name including initials ('J. A. Doudna' -> ['j', 'a', 'doudna'])."""
    return [t for t in re.split(r'[^a-z]+', fold(s)) if t] if isinstance(s, str) else []


def _first_compatible(a: str, b: str) -> bool:
    """Two first-name tokens agree: equal, or one is the initial of the other."""
    return a == b or (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b))


def inventor_name_search(con, author_names, coauthor_names=(), work_ints=(), affiliations=(), countries=(), years=(),
                         max_same_name=2, log=print) -> pd.DataFrame:
    """Candidate PatentsView inventor ids (current release, g_inventor_disambiguated) for a person searched by name, with
    the evidence that a candidate is the same person. Used when pqrs has no inventor for the author.

    A candidate's last name contains the author's family name and its first name agrees with the author's (equal, or an
    initial), without conflicting middle initials. Evidence per candidate: co-inventors whose name equals a co-author's
    (`coauthor_names`, small teams), patents citing the author's works (Reliance on Science, `work_ints`), assignees sharing
    a distinctive word with the author's affiliations, inventor countries among the affiliation countries, patent years
    overlapping the publication years, and how many inventor ids carry the same first + last name. A candidate is
    selected when its years overlap and, for a rare name (<= max_same_name ids), it has a co-author co-inventor, or
    patents citing the works together with an assignee / country / rare-name signal, or an assignee match; for a common
    name, evidence on at least half of its patents and two co-author co-inventors or two patents citing the works."""
    variants = [n for n in dict.fromkeys(author_names) if isinstance(n, str) and n.strip()]
    keys = set()
    for n in variants:
        t = _raw_name_tokens(n)
        if len(t) >= 2 and len(t[-1]) >= 2:
            keys.add((t[0], t[-1]))
    lasts = sorted({k[1] for k in keys if len(k[1]) >= 3})
    empty = pd.DataFrame(columns=['inventor_id', 'name', 'n_patents', 'first_year', 'last_year', 'n_ids_same_name', 'n_coauthor_coinventors',
                                  'coauthor_coinventors', 'n_patents_citing_works', 'n_works_cited', 'n_patents_assignee_match',
                                  'assignees_matched', 'n_patents_with_evidence', 'share_patents_with_evidence', 'inventor_countries',
                                  'country_match', 'years_overlap', 'selected', 'select_reason',
                                  'patent_ids'])
    if not lasts:
        log(f'no usable family name in {variants[:3]}')
        return empty
    cond = ' OR '.join(f"contains(regexp_replace(lower(strip_accents(disambig_inventor_name_last)), '[^a-z]', '', 'g'), '{l}')" for l in lasts)
    rows = con.sql(f'''SELECT i.inventor_id, i.patent_id, i.disambig_inventor_name_first AS name_first, i.disambig_inventor_name_last AS name_last,
                              i.location_id, year(TRY_CAST(g.patent_date AS DATE)) AS grant_year
                       FROM read_parquet('{CACHE / 'g_inventor_disambiguated.parquet'}') i
                       LEFT JOIN read_parquet('{CACHE / 'g_patent_min.parquet'}') g USING (patent_id)
                       WHERE {cond}''').df()
    rows['full'] = (rows.name_first.fillna('') + ' ' + rows.name_last.fillna('')).str.strip()

    def matches(first, last, full):
        ft, lt = _raw_name_tokens(first), _raw_name_tokens(last)
        if not ft or not lt:
            return False
        return any(k[1] in lt and _first_compatible(k[0], ft[0]) and not any(middle_conflict(v, full) for v in variants) for k in keys)
    names_u = rows[['name_first', 'name_last', 'full']].drop_duplicates()
    names_u['hit'] = [matches(f, l, u) for f, l, u in names_u.itertuples(index=False)]
    rows = rows.merge(names_u, on=['name_first', 'name_last', 'full'])
    same_key = rows.assign(k=[(_raw_name_tokens(f) or [''])[0] + ' ' + (_raw_name_tokens(l) or [''])[-1] for f, l in zip(rows.name_first, rows.name_last)])
    ids_per_key = same_key.groupby('k').inventor_id.nunique()
    hits = same_key[same_key.hit.astype(bool)]
    if hits.empty:
        log(f'no PatentsView inventor named like {variants[:3]}')
        return empty
    C = (hits.groupby('inventor_id')
         .agg(name=('full', lambda s: s.mode().iloc[0]), n_patents=('patent_id', 'nunique'), first_year=('grant_year', 'min'),
              last_year=('grant_year', 'max'), key=('k', lambda s: s.mode().iloc[0]),
              patent_ids=('patent_id', lambda s: ';'.join(sorted(set(s)))))
         .reset_index())
    C['n_ids_same_name'] = C.key.map(ids_per_key).astype(int)
    pats = hits[['inventor_id', 'patent_id']].drop_duplicates()
    con.register('ns_pat', pd.DataFrame({'patent_id': pats.patent_id.astype('string').unique()}))

    # (1) co-inventors whose name equals a co-author's name
    own = {k for k in (name_key(v) for v in variants) if k}
    co_by_key = {}
    for n in dict.fromkeys(n for n in coauthor_names if isinstance(n, str)):
        k = name_key(n)
        if k and k not in own:
            co_by_key.setdefault(k, []).append(n)

    def is_coauthor(n):                       # same first + last name as a co-author, middle initials not in conflict
        return any(not middle_conflict(n, c) for c in co_by_key.get(name_key(n), []))
    others = con.sql(f'''SELECT patent_id, inventor_id AS co_id, trim(coalesce(disambig_inventor_name_first, '') || ' ' ||
                                coalesce(disambig_inventor_name_last, '')) AS co_name
                         FROM read_parquet('{CACHE / 'g_inventor_disambiguated.parquet'}') WHERE patent_id IN (SELECT patent_id FROM ns_pat)''').df()
    co = pats.merge(others, on='patent_id')
    co = co[co.inventor_id != co.co_id]
    co = co[co.co_name.map(is_coauthor).astype(bool)]        # astype: an empty object mask would select columns
    ev = [co[['inventor_id', 'patent_id']]]                 # patents with at least one piece of evidence
    agg = co.groupby('inventor_id').co_name.agg(lambda s: '; '.join(sorted(set(s))))
    C['coauthor_coinventors'] = C.inventor_id.map(agg)
    C['n_coauthor_coinventors'] = C.coauthor_coinventors.fillna('').map(lambda s: len(s.split('; ')) if s else 0)
    # (2) patents citing the author's works (Reliance on Science)
    if len(work_ints):
        con.register('ns_w', pd.DataFrame({'oaid': pd.Series(sorted(set(int(w) for w in work_ints)), dtype='int64')}))
        cit = con.sql(f'''SELECT patent_id, oaid FROM read_parquet('{PCS_PQ}')
                          WHERE patent_id IN (SELECT patent_id FROM ns_pat) AND oaid IN (SELECT oaid FROM ns_w)''').df()
        cit = pats.merge(cit, on='patent_id')
        ev.append(cit[['inventor_id', 'patent_id']])
        C['n_patents_citing_works'] = C.inventor_id.map(cit.groupby('inventor_id').patent_id.nunique()).fillna(0).astype(int)
        C['n_works_cited'] = C.inventor_id.map(cit.groupby('inventor_id').oaid.nunique()).fillna(0).astype(int)
    else:
        C['n_patents_citing_works'] = 0; C['n_works_cited'] = 0
    # (3) assignees sharing a distinctive word with the author's affiliations
    aff_tok = set().union(*[org_tokens(a) for a in affiliations]) if len(affiliations) else set()
    asg = con.sql(f'''SELECT patent_id, disambig_assignee_organization AS org FROM read_parquet('{CACHE / 'g_assignee_disambiguated.parquet'}')
                      WHERE patent_id IN (SELECT patent_id FROM ns_pat) AND disambig_assignee_organization IS NOT NULL''').df()
    asg = pats.merge(asg, on='patent_id')
    asg = asg[asg.org.map(lambda o: bool(org_tokens(o) & aff_tok)).astype(bool)]
    ev.append(asg[['inventor_id', 'patent_id']])
    evp = pd.concat(ev).drop_duplicates()
    C['n_patents_with_evidence'] = C.inventor_id.map(evp.groupby('inventor_id').patent_id.nunique()).fillna(0).astype(int)
    C['share_patents_with_evidence'] = C.n_patents_with_evidence / C.n_patents.clip(lower=1)
    C['n_patents_assignee_match'] = C.inventor_id.map(asg.groupby('inventor_id').patent_id.nunique()).fillna(0).astype(int)
    C['assignees_matched'] = C.inventor_id.map(asg.groupby('inventor_id').org.agg(lambda s: '; '.join(sorted(set(s))[:5])))
    # (4) inventor countries
    if not fresh(LOCATION_PQ, [granted('g_location_disambiguated.tsv.zip')]):
        _tsv_zip_to_parquet(granted('g_location_disambiguated.tsv.zip'), LOCATION_PQ, ['location_id', 'disambig_city', 'disambig_state', 'disambig_country'])
    loc = pd.read_parquet(LOCATION_PQ, columns=['location_id', 'disambig_country']).drop_duplicates('location_id').set_index('location_id').disambig_country
    hc = hits.assign(country=hits.location_id.map(loc)).dropna(subset=['country'])
    C['inventor_countries'] = C.inventor_id.map(hc.groupby('inventor_id').country.agg(lambda s: ';'.join(s.value_counts().index)))
    auth_c = {str(c).upper() for c in countries if isinstance(c, str) and c}
    C['country_match'] = C.inventor_countries.fillna('').map(lambda s: bool(set(s.split(';')) & auth_c) if s else False)
    # (5) years
    yrs = pd.to_numeric(pd.Series(list(years)), errors='coerce').dropna()
    lo, hi = (yrs.min() - 5, yrs.max() + 15) if len(yrs) else (-np.inf, np.inf)
    C['years_overlap'] = (C.last_year.fillna(-1) >= lo) & (C.first_year.fillna(1e9) <= hi)

    co_ok, cite = C.n_coauthor_coinventors >= 1, C.n_patents_citing_works >= 1
    asg_ok, rare = C.n_patents_assignee_match >= 1, C.n_ids_same_name <= max_same_name
    # a rare name needs one signal; a common name (more than max_same_name ids) needs evidence on at least half of the
    # candidate's patents and two co-author co-inventors or two patents citing the works (one chance match is common
    # when the author has thousands of co-authors, and PatentsView ids of common names mix people)
    rare_rule = co_ok | (cite & (asg_ok | C.country_match | rare)) | (asg_ok & rare)
    common_rule = (C.share_patents_with_evidence >= .5) & ((C.n_coauthor_coinventors >= 2) | (C.n_patents_citing_works >= 2))
    C['selected'] = C.years_overlap & np.where(rare, rare_rule, common_rule)
    reason = []
    for r in C.itertuples(index=False):
        parts = [f'{r.n_coauthor_coinventors} co-author co-inventor(s)'] if r.n_coauthor_coinventors else []
        parts += [f'{r.n_patents_citing_works} patent(s) citing the works'] if r.n_patents_citing_works else []
        parts += [f'{r.n_patents_assignee_match} patent(s) with an affiliation assignee'] if r.n_patents_assignee_match else []
        parts += ['inventor country among the affiliation countries'] if r.country_match else []
        parts += [f'{r.n_patents_with_evidence} of {r.n_patents} patents with evidence']
        parts += [f'name carried by {r.n_ids_same_name} inventor id(s)' + ('' if r.n_ids_same_name <= max_same_name else ' (common name: stricter rule)')]
        parts += [] if r.years_overlap else ['patent years outside the publication years']
        reason.append('; '.join(parts))
    C['select_reason'] = reason
    C = C.drop(columns=['key']).sort_values(['selected', 'n_coauthor_coinventors', 'n_patents_citing_works', 'n_patents_assignee_match', 'n_patents'],
                                            ascending=False).reset_index(drop=True)
    log(f'{len(C)} PatentsView inventor ids named like {variants[:3]}; {int(C.selected.sum())} selected by the evidence rule')
    return C[empty.columns]


# ---------------------------------------------------------------------------------------------
# Author id check: an id without works in the 2026-01 snapshot (e.g. a newer OpenAlex id from PrizeAtlas) is resolved
# through the snapshot's authors table (OA_RAW/authors.csv.gz)
# ---------------------------------------------------------------------------------------------
OA_AUTHORS_PQ = CACHE / 'openalex_authors.parquet'
RECORD_DIR = NP / 'output' / 'record'              # <same name as the dashboard>.md: the dashboard's content for agents
PRIZEATLAS_LINK = NP / 'Data' / 'prizeatlas' / 'prizeatlas_sciscinet_laureate_link.csv'


def build_openalex_authors(con=None, log=print):
    """cache/openalex_authors.parquet from the snapshot's authors.csv.gz (about 100 M rows, streamed with pyarrow: the DuckDB
    CSV reader runs out of memory on this single-member gzip; ~15 minutes, once)."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.csv as pv
    import pyarrow.parquet as pq
    src = OA_RAW / 'authors.csv.gz'
    if fresh(OA_AUTHORS_PQ, [src]):
        return OA_AUTHORS_PQ
    log(f'building {OA_AUTHORS_PQ.name} from {src} ...')
    t0 = time.time()
    keep = ['id', 'orcid', 'display_name', 'display_name_alternatives', 'works_count', 'cited_by_count', 'last_known_institution',
            'last_known_institutions']
    reader = pv.open_csv(src, read_options=pv.ReadOptions(block_size=1 << 26),
                         parse_options=pv.ParseOptions(newlines_in_values=True),
                         convert_options=pv.ConvertOptions(include_columns=keep, column_types={c: pa.string() for c in keep}))
    schema = pa.schema([('author_id', pa.int64()), ('orcid', pa.string()), ('display_name', pa.string()), ('display_name_alternatives', pa.string()),
                        ('works_count', pa.int64()), ('cited_by_count', pa.int64()), ('last_known_institution', pa.string()),
                        ('last_known_institutions', pa.string())])
    tmp = f'{OA_AUTHORS_PQ}.{os.getpid()}.tmp'
    writer, n = pq.ParquetWriter(tmp, schema, compression='zstd'), 0
    for batch in reader:
        t = pa.Table.from_batches([batch])
        num = lambda c: pc.cast(pc.if_else(pc.equal(t[c], ''), None, t[c]), pa.int64())
        out = pa.table({'author_id': pc.cast(pc.replace_substring(t['id'], 'https://openalex.org/A', ''), pa.int64()),
                        'orcid': pc.if_else(pc.equal(t['orcid'], ''), None, pc.replace_substring(t['orcid'], 'https://orcid.org/', '')),
                        'display_name': t['display_name'], 'display_name_alternatives': t['display_name_alternatives'],
                        'works_count': num('works_count'), 'cited_by_count': num('cited_by_count'),
                        'last_known_institution': pc.replace_substring(t['last_known_institution'], 'https://openalex.org/', ''),
                        'last_known_institutions': t['last_known_institutions']}, schema=schema)
        writer.write_table(out); n += len(out)
    writer.close(); os.replace(tmp, OA_AUTHORS_PQ)
    log(f'{OA_AUTHORS_PQ.name}: {n:,} authors in {time.time() - t0:.0f}s')
    return OA_AUTHORS_PQ


def laureate_hints(author_ids) -> dict:
    """What the PrizeAtlas crawl knows about the person behind these OpenAlex ids: name, ORCID, the OpenAlex id of the
    prize-time institution, and the Li et al. (SciSciNet) author bridge ids of the same laureate."""
    out = {'name': None, 'orcids': [], 'institution_ids': [], 'bridge_ids': [], 'prizeatlas_urls': []}
    if not prizeatlas_available():
        return out
    pa = prizeatlas_table()
    ids = {str(a) for a in author_ids}
    hit = pa[pa.openalex_author_id.fillna('').str.split(r';\s*').apply(lambda l: bool(ids & set(l)))]
    if hit.empty:
        return out
    out['name'] = str(hit.name.iloc[0])
    out['orcids'] = sorted(set(hit.orcid.dropna()))
    if 'csv_institution_openalex_id' in hit:
        out['institution_ids'] = sorted(set(hit.csv_institution_openalex_id.dropna()))
    out['prizeatlas_urls'] = hit.url.tolist()
    if PRIZEATLAS_LINK.exists() and LAUREATE_BRIDGE.exists():
        lk = pd.read_csv(PRIZEATLAS_LINK, usecols=['LaureateID', 'url'])
        lids = set(lk[lk.url.isin(hit.url)].LaureateID)
        b = pd.read_csv(LAUREATE_BRIDGE, usecols=['LaureateID', 'primary_author_id'], dtype={'primary_author_id': str})
        out['bridge_ids'] = sorted(set(b[b.LaureateID.isin(lids)].primary_author_id.dropna()))
    return out


def resolve_author_ids(con, author_ids, min_works=5, name=None, orcids=(), institution_ids=(), bridge_ids=(), log=print) -> dict:
    """Check the OpenAlex author ids against the 2026-01 snapshot (the authorship dataset is built from it) and resolve them.

    * ids with at least `min_works` works are kept, and other ids carrying the same ORCID are added (OpenAlex splits people);
    * otherwise (an id created after the snapshot, a merged or an empty id) the person is looked up by ORCID, then by the
      Li et al. laureate bridge, then by name: authors with the same first + last name (no conflicting middle initials) and
      at least `min_works` works, ranked by the prize-time institution among their last known institutions and by
      citations; the top one is taken when it is at least twice as cited as the next (else flagged 'ambiguous').
    Returns {'author_ids': [primary, ...], 'input_ids', 'rule', 'changed', 'table'}; the primary has the most works."""
    build_openalex_authors(con, log)
    ints = sorted({int(str(a)[1:]) for a in author_ids})
    cols = 'author_id, orcid, display_name, works_count, cited_by_count, last_known_institutions'
    A = f"read_parquet('{OA_AUTHORS_PQ}')"
    given = (con.sql(f'SELECT {cols} FROM {A} WHERE author_id IN ({", ".join(map(str, ints))})').df() if ints
             else con.sql(f'SELECT {cols} FROM {A} LIMIT 0').df()).assign(source='input id')
    n_given = int(given.works_count.fillna(0).sum())
    orc = {o for o in orcids if o} | set(given.orcid.dropna())
    name = name or (given.display_name.dropna().iloc[0] if given.display_name.notna().any() else None)
    parts = [given]
    if orc:
        parts.append(con.sql(f'SELECT {cols} FROM {A} WHERE orcid IN ({sql_list(sorted(orc))}) AND works_count > 0').df().assign(source='same ORCID'))
    bints = sorted({int(str(b)[1:]) for b in bridge_ids if b})
    if bints:
        parts.append(con.sql(f'SELECT {cols} FROM {A} WHERE author_id IN ({", ".join(map(str, bints))})').df().assign(source='laureate bridge'))
    T = pd.concat(parts, ignore_index=True)
    rule = 'input ids have works'
    if n_given >= min_works:
        keep = T[(T.source == 'input id') | ((T.source == 'same ORCID') & (T.works_count > 0))]
        if set(keep.author_id) - set(ints):
            rule = 'input ids have works; ids with the same ORCID added'
    else:
        keep = T[(T.source == 'same ORCID') & (T.works_count >= 1)]
        rule = 'same ORCID'
        if keep.works_count.sum() < min_works:
            keep, rule = T[(T.source == 'laureate bridge') & (T.works_count >= 1)], 'laureate bridge (Li et al.)'
        if keep.works_count.sum() < min_works and name and name_key(_clean_person(name)):
            first, last = name_key(_clean_person(name))
            c = con.sql(f'''SELECT {cols} FROM {A} WHERE works_count >= {int(min_works)}
                            AND contains(lower(strip_accents(display_name)), '{last.replace("'", "''")}')''').df()
            c = c[c.display_name.map(lambda n: name_key(_clean_person(n)) == (first, last) and not middle_conflict(_clean_person(n), _clean_person(name))).astype(bool)]
            inst = {str(i) for i in institution_ids if i}
            c['institution_match'] = c.last_known_institutions.fillna('').map(lambda s: any(i in s for i in inst)) if inst else False
            c = c.sort_values(['institution_match', 'cited_by_count'], ascending=False).assign(source='same name')
            T = pd.concat([T, c], ignore_index=True)
            if len(c):
                top = c.iloc[0]
                second = c.cited_by_count.iloc[1] if len(c) > 1 else 0
                dominant = bool(top.institution_match) or top.cited_by_count >= 2 * max(second, 1)
                keep = c.iloc[:1]
                rule = 'same name, ' + ('prize-time institution' if top.institution_match else 'most cited') + ('' if dominant else ' (ambiguous: check the table)')
        if keep.empty:
            keep, rule = given, 'unresolved: no works, no ORCID / bridge / name match'
    keep = keep.drop_duplicates('author_id').sort_values('works_count', ascending=False)
    ids_out = [f'A{int(a)}' for a in keep.author_id]
    changed = ids_out != [f'A{i}' for i in ints]
    T = T.drop(columns=['last_known_institutions']).drop_duplicates(['author_id', 'source'])
    T['author_id'] = 'A' + T.author_id.astype('int64').astype(str)
    T['kept'] = T.author_id.isin(ids_out)
    log(f'author id check: input {[f"A{i}" for i in ints]} ({n_given} works in the snapshot) -> {ids_out} [{rule}]')
    return {'author_ids': ids_out, 'input_ids': [f'A{i}' for i in ints], 'rule': rule, 'changed': changed, 'table': T}


# ---------------------------------------------------------------------------------------------
# Titles of works missing from the 2026-01 snapshot (OpenAlex API, cached)
# ---------------------------------------------------------------------------------------------
API_TITLES_PQ = CACHE / 'openalex_api_titles.parquet'


def api_titles(ids, fetch=True, batch=50, timeout=20, log=print) -> dict:
    """{work id: title} for OpenAlex works, from cache/openalex_api_titles.parquet and, for ids not cached yet, the OpenAlex
    API (api.openalex.org, 50 ids per request). Used for works that are not in the snapshot's works table; needs internet
    (the login node), elsewhere only the cache is read. Ids the API does not return are cached with an empty title."""
    import urllib.parse
    import urllib.request
    ids = sorted({str(i) for i in ids if isinstance(i, str) and re.fullmatch(r'W\d+', str(i))})
    cached = pd.read_parquet(API_TITLES_PQ) if API_TITLES_PQ.exists() else pd.DataFrame({'paper_id': pd.Series(dtype=str), 'title': pd.Series(dtype=str),
                                                                                          'fetched': pd.Series(dtype=str)})
    todo = [i for i in ids if i not in set(cached.paper_id)]
    if todo and fetch:
        rows, today, fails = [], time.strftime('%Y-%m-%d'), 0

        def save():
            nonlocal cached, rows
            if rows:
                cached = pd.concat([cached, pd.DataFrame(rows)], ignore_index=True).drop_duplicates('paper_id', keep='last')
                tmp = f'{API_TITLES_PQ}.{os.getpid()}.tmp'
                cached.to_parquet(tmp, index=False); os.replace(tmp, API_TITLES_PQ)
                rows = []
        for k in range(0, len(todo), batch):
            chunk = todo[k:k + batch]
            url = 'https://api.openalex.org/works?' + urllib.parse.urlencode({'filter': 'openalex:' + '|'.join(chunk), 'select': 'id,title', 'per-page': batch})
            req = urllib.request.Request(url, headers={'User-Agent': 'NobelPrizeProfiles/1.0 (academic research)'})
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=timeout) as r:
                        got = {x['id'].rsplit('/', 1)[-1]: x.get('title') for x in json.load(r).get('results', [])}
                    rows += [{'paper_id': i, 'title': got.get(i), 'fetched': today} for i in chunk]
                    break
                except Exception as e:                       # 429 / 5xx / network: back off and retry this request
                    err = e; time.sleep(2 ** attempt)
            else:
                fails += 1
                if fails >= 3 and not rows and k == (fails - 1) * batch:
                    log(f'OpenAlex API not reachable ({err.__class__.__name__}); titles only from the cache'); break
            if len(rows) >= 20 * batch:
                save()
            time.sleep(.15)
        save()
        if fails:
            log(f'OpenAlex API: {fails} request(s) failed after retries')
    m = cached.dropna(subset=['title']).set_index('paper_id').title
    return {i: m[i] for i in ids if i in m.index}


# ---------------------------------------------------------------------------------------------
# Name -> OpenAlex author id (pipeline/profile_person.py)
# ---------------------------------------------------------------------------------------------
def _institutions_text(js) -> str:
    """'Name (CC); Name (CC)' from a last_known_institutions JSON string."""
    try:
        return '; '.join(f"{i.get('display_name')} ({i.get('country_code') or '?'})" for i in json.loads(js or '[]'))
    except (ValueError, TypeError, AttributeError):
        return ''


def find_author_candidates(con, name, affiliation=None, orcid=None, prize_ids=(), use_api=True, min_works=1, limit=15, log=print) -> pd.DataFrame:
    """OpenAlex author candidates for a person's name, best first.

    Sources: the 2026-01 snapshot's authors table (cache/openalex_authors.parquet) and, with use_api, the live OpenAlex author
    search (ids created after the snapshot are resolved later by the notebook's author id check), plus `prize_ids` (the
    PrizeAtlas OpenAlex ids of a laureate with this name). Tiers (`match`):
      'display' - the display name agrees with the query: same surname, first name equal or an initial, no conflicting middle initials;
      'alias'   - only an alternative name agrees (OpenAlex alternative names also hold co-authors' and namesakes' names);
      'orcid' / 'prizeatlas' - the ORCID or a PrizeAtlas id of the laureate.
    Ranking: ORCID > PrizeAtlas id > affiliation (a distinctive word of `affiliation` among the last known institutions) >
    display tier before alias tier > citations; `limit` is applied after the ranking."""
    query = _clean_person(name)
    raw = _raw_name_tokens(query)
    if len(raw) < 2:
        raise ValueError(f'give a first and a last name: {name!r}')
    first, last = raw[0], raw[-1]
    full = ' '.join(raw)
    orcid = (orcid or '').rstrip('/').rsplit('/', 1)[-1] or None
    prize_ids = [str(i).strip() for i in prize_ids if str(i).strip()]

    def agrees(n):
        t = _raw_name_tokens(_clean_person(n))
        return len(t) >= 2 and t[-1] == last and _first_compatible(t[0], first) and not middle_conflict(_clean_person(n), query)

    def same_last(n):
        t = _raw_name_tokens(_clean_person(n))
        return bool(t) and t[-1] == last
    build_openalex_authors(con, log)
    A = f"read_parquet('{OA_AUTHORS_PQ}')"
    esc_last = last.replace("'", "''")
    pid_ints = [int(i[1:]) for i in prize_ids if re.fullmatch(r'A\d+', i)]
    snap = con.sql(f'''SELECT author_id, orcid, display_name, display_name_alternatives, works_count, cited_by_count, last_known_institutions
                       FROM {A} WHERE (works_count >= {int(min_works)}
                       AND (contains(lower(strip_accents(display_name)), '{esc_last}')
                            OR contains(lower(strip_accents(display_name_alternatives)), '{esc_last}')))
                       {f"OR orcid = '{orcid}'" if orcid else ''}
                       {f"OR author_id IN ({', '.join(map(str, pid_ints))})" if pid_ints else ''}''').df()
    snap['author_id'] = 'A' + snap.author_id.astype('int64').astype(str)
    disp_ok = snap.display_name.map(agrees).astype(bool)
    alt_ok = snap.display_name_alternatives.fillna('[]').map(lambda s: any(agrees(a) for a in (json.loads(s) if s.startswith('[') else [])))
    alt_ok = (alt_ok & snap.display_name.map(same_last)).astype(bool)
    keep = disp_ok | alt_ok | (snap.orcid == orcid) | snap.author_id.isin(prize_ids)
    snap = snap[keep.astype(bool)].copy()
    snap['match'] = np.where(snap.display_name.map(agrees).astype(bool), 'display', 'alias')
    snap['institutions'] = snap.last_known_institutions.map(_institutions_text)
    snap['source'] = 'snapshot'
    C = snap.drop(columns=['display_name_alternatives', 'last_known_institutions'])
    missing_prize = [i for i in prize_ids if i not in set(C.author_id)]      # PrizeAtlas ids created after the snapshot
    if missing_prize:
        C = pd.concat([C, pd.DataFrame({'author_id': missing_prize, 'display_name': query, 'source': 'PrizeAtlas (not in the snapshot)',
                                        'match': 'display', 'institutions': ''})], ignore_index=True)
    if use_api:
        import urllib.parse
        import urllib.request
        try:
            url = 'https://api.openalex.org/authors?' + urllib.parse.urlencode(
                {'search': query, 'per-page': 50, 'select': 'id,display_name,orcid,works_count,cited_by_count,last_known_institutions'})
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'NobelPrizeProfiles/1.0 (academic research)'}), timeout=20) as r:
                res = json.load(r).get('results', [])
            api = pd.DataFrame([{'author_id': x['id'].rsplit('/', 1)[-1], 'display_name': x.get('display_name'),
                                 'orcid': (x.get('orcid') or '').rsplit('/', 1)[-1] or None, 'works_count': x.get('works_count'),
                                 'cited_by_count': x.get('cited_by_count'), 'source': 'OpenAlex API', 'match': 'display',
                                 'institutions': '; '.join(f"{i.get('display_name')} ({i.get('country_code') or '?'})" for i in (x.get('last_known_institutions') or []))}
                                for x in res])
            if len(api):
                api = api[(api.display_name.map(agrees) | (api.orcid == orcid)).astype(bool)]
                api = api[~api.author_id.isin(set(C.author_id))]       # snapshot rows win (their works are what the notebook reads)
                C = pd.concat([C, api], ignore_index=True)
        except Exception as e:
            log(f'OpenAlex author search not reachable ({e.__class__.__name__}): snapshot candidates only')
    if C.empty:
        return C
    aff_tok = org_tokens(affiliation) if affiliation else set()
    C['name_match'] = np.where(C.display_name.map(lambda n: ' '.join(_raw_name_tokens(_clean_person(n))) == full), 'exact', 'compatible')
    C['affiliation_match'] = C.institutions.fillna('').map(lambda s: bool(aff_tok and org_tokens(s) & aff_tok)).astype(bool)
    C['orcid_match'] = (C.orcid == orcid).astype(bool) if orcid else False
    C['prize_match'] = C.author_id.isin(prize_ids).astype(bool)
    C.loc[C.orcid_match, 'match'] = 'orcid'
    C.loc[C.prize_match & ~C.orcid_match, 'match'] = 'prizeatlas'
    cites = pd.to_numeric(C.cited_by_count, errors='coerce').fillna(0)
    C['rank_score'] = (C.orcid_match * 1e14 + C.prize_match * 1e13 + C.affiliation_match * 1e12 + (C.match != 'alias') * 1e11
                       + cites + (C.name_match == 'exact') * .5)            # the exact spelling only breaks ties
    C = C.sort_values('rank_score', ascending=False).reset_index(drop=True)
    return C[['author_id', 'display_name', 'orcid', 'works_count', 'cited_by_count', 'institutions', 'source', 'match', 'name_match',
              'affiliation_match', 'orcid_match', 'prize_match', 'rank_score']].head(limit)


def pick_author(C, dominance=3.0):
    """(row, reason) of the candidate to profile, or (None, reason) when the user should choose. Automatic choices: an ORCID
    match; a PrizeAtlas id of the laureate named by the query; the only display-name candidate at the given affiliation; the
    most cited display-name candidate when it has at least `dominance` times the citations of the next display-name candidate.
    Candidates found only through an alternative name are never chosen automatically."""
    if C is None or C.empty:
        return None, 'no candidate'
    top = C.iloc[0]
    if top.orcid_match:
        return top, 'ORCID'
    if top.prize_match:
        return top, 'PrizeAtlas OpenAlex id of the laureate'
    D = C[C.match == 'display']
    if D.empty:
        return None, 'only candidates matched through alternative names: check them'
    if D.affiliation_match.any():
        at = D[D.affiliation_match]
        if len(at) == 1:
            return at.iloc[0], 'only candidate at the given affiliation'
        D = at
    if len(D) == 1:
        return D.iloc[0], 'only candidate whose display name matches'
    c1, c2 = float(D.cited_by_count.iloc[0] or 0), float(D.cited_by_count.iloc[1] or 0)
    if c1 >= dominance * max(c2, 1):
        return D.iloc[0], f'most cited ({c1:,.0f} vs {c2:,.0f} citations)'
    return None, f'ambiguous: the two most cited candidates have {c1:,.0f} and {c2:,.0f} citations'


def same_person_fragments(C, pick, min_works=2):
    """Other candidates that look like fragments of the picked author: the same display name (folded, middle initials included),
    a shared institution word, at least `min_works` works, and no different ORCID. OpenAlex splits prolific people."""
    key = ' '.join(_raw_name_tokens(_clean_person(pick.display_name)))
    tok = org_tokens(pick.institutions or '')
    if not tok:                                   # no institution to compare: namesakes cannot be told apart, merge nothing
        return []
    out = []
    for r in C.itertuples(index=False):
        if r.author_id == pick.author_id or (r.works_count or 0) < min_works:
            continue
        if ' '.join(_raw_name_tokens(_clean_person(r.display_name))) != key:
            continue
        if pick.orcid and r.orcid and r.orcid != pick.orcid:
            continue
        if tok and not (org_tokens(r.institutions or '') & tok):
            continue
        out.append(r.author_id)
    return out
