# PrizeAtlas Nobel laureates

Crawled by `Nobel Prize/notebook/prizeatlas_crawl.ipynb` on 2026-09-30 from https://prizeatlas.org/es/nobel-prize/
(index -> category -> prize year -> laureate page; site build date 2026-09-30).
Data: PrizeAtlas, CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/); code https://github.com/antb123/prizeatlas.

| file | content |
|---|---|
| `prizeatlas_nobel_laureates.csv` / `.parquet` | one row per Nobel award page (662): ids (`openalex_author_id`, `orcid`, `wikidata_qid`, `ror`), motivation, prize share, affiliation, birth / death, co-laureates, URLs; `csv_*` = columns of the site's awards.csv |
| `prizeatlas_nobel_affiliations.csv` | one row per page × affiliation (663) |
| `prizeatlas_nobel_people.csv` | one row per person (658); `person_key` = Wikidata id |
| `prizeatlas_sciscinet_laureate_link.csv` | Li et al. (2019) / SciSciNet `LaureateID` -> PrizeAtlas page and OpenAlex id (543 of 545 matched) |
| `awards.csv` | the site's own download (all prizes), as fetched |
| `crawl_log.csv`, `manifest.json` | requests and run summary |
| `html/` | the raw pages (the site's folder layout); a rerun parses these |

Categories are the Spanish slugs of the crawled pages (`quimica`, `medicina`, `fisica`); `category_en` comes from the English URL.
Place names are the Spanish page text; the `csv_*` columns and `awards.csv` are in English.
