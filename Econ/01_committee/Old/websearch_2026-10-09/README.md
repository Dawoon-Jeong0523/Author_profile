> **Superseded on 2026-10-09 (not run).** This web-search version of step 1 (research with each provider's web search, extraction, merge) was built and tested offline only; the user chose the simpler design in `../../README.md` instead (no web search: each model answers from its own knowledge, Claude merges). Kept for reference; it imports `../../../llm_providers.py`, whose web-search functions now live in `llm_providers_websearch.py` here.

# Step 1: profiles of the 2026 committee members

The 11 members of the Committee for the Prize in Economic Sciences in Memory of Alfred Nobel 2026
([`roster.yaml`](roster.yaml), from the nobelprize.org committee list as of 9 October 2026):

| Member | Role | Title as listed |
|---|---|---|
| John Hassler | chair | Professor of economics |
| Tommy Andersson | member | Professor of economics |
| Anna Dreber Almenberg | member | Professor of economics |
| Peter Fredriksson | member | Professor of economics |
| Per Strömberg | member | SSE Centencial professor of finance and private equity (spelling as pasted; the research records the official title) |
| Timo Boppart | co-opted member | Professor of economics |
| Kerstin Enflo | co-opted member | Professor in economic history |
| Richard Friberg | co-opted member | Professor of economics |
| Randi Hjalmarsson | co-opted member | Professor of economics |
| Jan Teorell | co-opted member | Professor of political science |
| Per Krusell | secretary | Professor of economics |

For each member, each of the three models of the 1 October virtual committees (`claude-opus-5-5`,
`gpt-5.5-2026-04-23`, `gemini-3.1-pro-preview`) researches the person on its own with its provider's web search, then
turns its write-up into atomic, sourced items. One merge call combines the three item lists into a single profile in
which every statement shows which models state it, which sources back it, and where the models disagree. These
profiles are the material for the member personas of the next step.

## Pipeline

```
roster.yaml ─► research (3 models, web search on) ─► extract (same model, JSON) ─► aggregate (1 model, JSON) ─► profiles/
               runs/<provider>/<slug>/research.json   runs/<provider>/<slug>/       profiles/<slug>.json, .md,
               dossier.md (text + citation markers)    extract.json (ids, sources)   index.csv, ALL.md
```

| Stage | Calls | Tools | Prompt | Output |
|---|---|---|---|---|
| research | 1 per member × model | Anthropic `web_search` + `web_fetch` (server tools, dynamic filtering; continued on `pause_turn`); OpenAI Responses `web_search` with the full source list; Gemini `google_search` + `url_context` | [`prompts/research_system.md`](prompts/research_system.md), [`prompts/research_user.md`](prompts/research_user.md): nine fixed headings (identity, education and career, research and methods, key publications, work for the prize and the Academy, documented views, honours and policy roles, collaborators, open questions); every statement followed by its source link, `[unsourced]` otherwise | `research.json` (request, every HTTP attempt, raw responses, usage, search queries, every page the tool returned or opened, the citation table), `dossier.md` |
| extract | 1 per member × model, same model | none; JSON schema | [`prompts/extract_system.md`](prompts/extract_system.md): one item = one fact, copied with its markers or links, nothing added | `extract.json`: items with ids `A01`, `O07`, `G12`, resolved sources, `grounded` flag, checks |
| aggregate | 1 per member (`claude-opus-5-5`; `--aggregator` to change) | none; JSON schema | [`prompts/aggregate_system.md`](prompts/aggregate_system.md): merge same facts, keep single-model facts, record disagreements, drop namesake items with a reason, summary sentences with ids | `profiles/<slug>.json`, `profiles/<slug>.md` |

**Citation markers.** The provider's own citations are turned into numbered markers next to the text they support:
Anthropic text blocks with `web_search_result_location` citations get `[A1]`, `[A2]` after the block; Gemini
`groundingSupports` segments get `[G1]` after the segment, with each grounding link resolved from its
`vertexaisearch.cloud.google.com/grounding-api-redirect/...` address to the original page; OpenAI's answer already
carries its citations as inline links, listed as `[O1]`, `[O2]`. The dossier ends with the numbered source list.

**Grounded.** An item is grounded when at least one of its sources is a page that the provider's search tool
returned, fetched or cited (Anthropic search results, fetched pages, citations; OpenAI search sources, opened pages,
`url_citation`; Gemini grounding chunks and successfully retrieved `url_context` pages). A link that only the model
wrote is kept, but not grounded; a marker that does not exist is flagged (`unknown marker`).

**Merge checks (in code).** Every id the merge cites must be an input id (otherwise the merge is asked again, then
recorded as invalid); every input id should appear in an item's support, a conflict or the dropped list (the rest are
listed as unaccounted); the number of models behind each item, its sources and their grounding are computed from the
cited input items, never taken from the merge model.

## Commands

```bash
cd "/project/jevans/Dawoon/Nobel Prize/Econ/01_committee"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY profiles.py roster
$PY profiles.py prompt --member john-hassler                     # the exact research prompt (free)
$PY profiles.py estimate                                         # cost from logged calls, else assumptions
$PY profiles.py test --member john-hassler                       # one member, three models, merged (paid)
$PY profiles.py run --workers 2                                  # all members (paid; existing valid records are kept)
$PY profiles.py run --members per-krusell --providers gemini --stages research extract
$PY profiles.py aggregate --members john-hassler --force         # merge again
$PY profiles.py render && $PY profiles.py status
$PY profiles.py check-sources                                    # HTTP status of every cited URL (free, slow)
```

An existing valid record is never asked again unless `--force`; failed or invalid records are. A crashed cell writes
nothing, so a plain re-run retries it. Every call is logged in `logs/calls.jsonl` (stage, member, model, seconds,
tokens, searches, USD).

## Outputs

| File | Content |
|---|---|
| `profiles/<slug>.md` | the merged profile: summary, identity, items by section with badges `[A O G]` (which models state it), source links (✓ = returned by a search tool), conflicts, open questions, dropped items, numbered sources |
| `profiles/<slug>.json` | the same as data: items with `support_ids`, `providers`, `n_providers`, `sources` (`cited_by`, `grounded_by`), `conflict`, `fields`; `stats` |
| `profiles/index.csv`, `profiles/ALL.md` | one row / one section per member |
| `profiles/source_check.csv` | `check-sources`: HTTP status per cited URL |
| `runs/<provider>/<slug>/` | `research.json`, `dossier.md`, `extract.json` (not versioned) |

## Settings and cost

[`settings.yaml`](settings.yaml): research `max_output_tokens` 32000 and effort `high` on all three models (Anthropic
`output_config.effort`, OpenAI `reasoning.effort`, Gemini `thinkingLevel`); Anthropic at most 20 searches and 12
fetches per call; OpenAI at most 40 built-in tool calls; extraction with provider-default effort and one JSON retry;
the merge on `claude-opus-5-5` at effort `high`. No sampling parameters and no model fallbacks are sent (a fallback
would swap the model inside a cell). Prices in `../config.yaml`; `profiles.py estimate` replaces the assumptions with
the logged cost once calls have run.

## Content rules

The research prompt limits the profiles to public professional information (positions, education, research,
publications, committee and Academy work, statements made in a professional capacity, honours, editorial and policy
roles, professional networks) and excludes private life. Views are recorded only as dated, sourced statements; the
models are told not to speculate about how a member will vote or whom they favour. The profiles are model-written
from web sources: check a statement against its sources before relying on it, especially single-model, ungrounded or
conflicting items.

## Known limits

- The three models are the only researchers; a fact none of them finds is missing, and two models can repeat the same
  wrong source.
- Gemini grounding links are redirect addresses that expire; they are resolved at research time and the resolved URL
  is stored.
- OpenAI adds `utm_source=openai` to cited links; URLs are compared without tracking parameters.
- Long research calls are non-streaming with a 30-minute read timeout and TCP keepalive.
