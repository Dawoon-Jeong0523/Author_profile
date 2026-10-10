# First committee run: the five leading fields only (10 October 2026, 13:05-13:47 CDT)

Archived on 10 October 2026 when the committee was re-asked on all 14 fields (option B, user's choice): three
requests per member x model (batches of 5/5/4 fields), the age paragraph instead of the one-line age record, and
`key_works` / `rationale` asked as defining works and reasoning (up to 3 sentences).

Contents: `committee/raw/<model>/<member>.json` (one call per member x model covering Macro, Trade, Production/IO,
Public, Equilibrium; 31 of 33 valid: claude-opus-5-5 returned only the Macro block for Hassler and Boppart twice),
`committee/<field>/ballots.jsonl`, `candidates.json`, `review.md` (rule-based clusters with `link_min_overlap` 0.15),
`results/pool.*`, the run logs and `run_rest.sh`, `prompts/` (the five-field prompt and the integration dry-run prompts),
`calls_until_2026-10-10_1400.jsonl` (copy of the cost log; spent $8.14 over 61 calls). The raw files use the old path
scheme `<member>.json` without a batch suffix and are not read by the current `virtual_committee.py`.
