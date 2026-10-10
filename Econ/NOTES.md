# Econ: working notes (9-10 October 2026)

> The project description is [`README.md`](README.md); these are the working notes of the build, with the status
> table as it stood during the work (not updated after 10 October, 13:00 CDT).

## Forecasting the 2026 Sveriges Riksbank Prize in Economic Sciences

A separate forecast model for the economics prize, announced on **Monday 12 October 2026, 11:45 CEST at the earliest
(04:45 CDT)**; forecasts must finish by Sunday 11 October, 23:00 CDT. The Medicine, Physics and Chemistry forecasts in
`../experiment/` used personas that carried only the specialties of each committee and options built around
discoveries. This model starts from the members of the real 2026 committee and works in four steps:

1. **Virtual committee members.** A profile of each of the 11 members of the 2026 committee (fields, recent interests,
   representative works, persona): the three LLMs of the earlier virtual committees each describe the member from
   their own knowledge (no web search) and Claude merges the three answers into one profile per member
   ([`01_committee/`](01_committee/README.md)). The profiles will be the basis of member personas that discuss the
   prize.
2. **Fields.** Which area of economics the prize goes to, starting from the history of past prizes
   ([`data/econ_prizes.md`](data/econ_prizes.md)): the three models give every prize work JEL codes, and
   [`02_fields/prize_history.ipynb`](02_fields/prize_history.ipynb) builds their consensus and analyses the fields,
   their sequence in award order, the laureates, gender and age ([`02_fields/`](02_fields/README.md)).
3. **Candidates per field.** The leading people in each field.
4. **Preseen.** The forecast question on Preseen.

| Step | Folder | Status (2026-10-09) |
|---|---|---|
| Prize history 1969–2025 | [`data/`](data/) | done: 57 prizes, 99 laureates; list page and Nobel Prize API agree on every year, name and motivation |
| 1. committee member profiles | [`01_committee/`](01_committee/README.md) | done: 11 of 11 merged (33 answers, all members recognized by all three models; 44 calls, $4.66) |
| 1b. personas and discussion | – | not started; for the field question the profiles enter as context notes instead (step 4a) |
| 2. fields | [`02_fields/`](02_fields/README.md) | JEL coding done (64 works × 3 models, $1.52; letter agreed by all three for 58 of 64); analysis notebook executed; awarded fields in [`results/awarded_jel_fields.md`](02_fields/results/awarded_jel_fields.md) |
| 3. candidates per field | – | to do (people stage) |
| 4a. Preseen context notes for the field question | [`04_field_forecast/`](04_field_forecast/README.md) | done 10 Oct: `field_context_prompts.ipynb` executed (each note cell prints one note); 9 notes in `context/`, question `questions/fields14.json` (14 fields with keywords, no Other) |
| 4b. Preseen run (field question) | [`04_field_forecast/run_field.sh`](04_field_forecast/run_field.sh) | done 10 Oct 12:00–12:44: control (no context) vs main (9 notes, assume_true); main: Macro 16.8 %, Trade 14.0, Production/IO 13.9, Public 12.8, Equilibrium 10.3; control: Production/IO 14.6, Macro 14.5, Econometrics 12.3 ([results](04_field_forecast/results/preseen_fields14_results.md)) |
| 5. laureate reference facts for the people stage | [`05_laureates/`](05_laureates/README.md) | section 1 (age at the award) done 10 Oct: `laureate_history.ipynb`, prompt paragraph `prompt/01_age_at_award.md`; found the API's 2022 award-date error (ages 11 years too low), corrected here and in step 2 |
| 6. virtual committee: candidates for the five leading fields | [`06_candidates/`](06_candidates/README.md) | built 10 Oct: 11 real-member personas × 3 models, one call per cell covering Macro, Trade, Production/IO, Public, Equilibrium; Gemini cells running, Anthropic/OpenAI cells wait for valid keys (401); then aggregate + 30-option pool (7/6/6/6/5) |
| Record | [`record/Record.tex`](record/Record.tex) | the detailed record of the work through step 4a (10 Oct), tables written by the step-4a notebook |

## Layout

```
Econ/
├── README.md               this page
├── config.yaml             shared: dates, API key variable names, models, prices
├── llm_providers.py        calls to Anthropic, OpenAI and Gemini in JSON mode (no tools)
├── data/
│   ├── crawl_econ_prizes.py   nobelprize.org list page (All Years) + Nobel Prize API -> tables and document
│   ├── econ_prizes.md         every prize 1969-2025 by decade: laureates, shares, motivations, affiliations, checks
│   ├── econ_prizes_by_year.csv, econ_prizes_laureates.csv, crawl_report.json
│   └── raw/                   the fetched page and API files (dated)
├── 01_committee/           step 1: member profiles (see its README); Old/ = the superseded web-search version
├── 02_fields/              step 2: JEL codes of the prize works, prize_history.ipynb, results/ (see its README)
├── 04_field_forecast/      steps 4a-4b: Preseen context notes, question, run script and results of the field question (see its README)
├── 05_laureates/           step 5: reference facts from the laureate record for the people stage (laureate_history.ipynb, results/, prompt/)
├── 06_candidates/          step 6: the virtual committee (virtual_committee.py, settings.yaml, committee/<field>/, results/pool.*; see its README)
└── record/                 Record.tex = the detailed record through step 4a; tables/ written by the step-4a notebook; build/ local
```

## Prize history (`data/`)

`python data/crawl_econ_prizes.py` fetches three sources one second apart: the list page in its **All Years** view
(`.../all-prizes-in-economic-sciences/all/`; the default view shows only 2020-2025) and the Nobel Prize API 2.1
(`nobelPrizes` and `laureates` for category `eco`). The page gives each year's motivation groups (a year with two
motivations was divided between two works) and the overall motivation where there is one (2025); the API adds each
laureate's share, affiliation at the prize, gender, birth and death. Every page laureate is matched to an API record
and the two motivation texts are compared; `--offline` re-parses the saved files.

Result of the 9 October 2026 crawl: 57 prizes and 99 laureates (as the page itself states), 7 prizes divided between
two works, 3 women laureates, every motivation identical in page and API. Known API error (found 10 October): the
2022 prize is dated 2011-10-10, so `age_at_award` of Bernanke, Diamond and Dybvig is eleven years too low (57, 57, 56
instead of 68, 68, 67); the notebooks recompute the age from the prize year, the crawled file stays as fetched. Licence: API data CC0; the list page is
© Nobel Prize Outreach, so the raw HTML copy stays local (`.gitignore`).

## Running

```bash
cd "/project/jevans/Dawoon/Nobel Prize/Econ"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
$PY data/crawl_econ_prizes.py                     # prize history (free)
$PY 01_committee/profiles.py estimate             # step 1 cost
$PY 01_committee/profiles.py test --member john-hassler   # step 1 for one member (paid)
$PY 01_committee/profiles.py run                  # step 1 for all members (paid)
$PY 02_fields/classify_jel.py run                 # step 2 JEL codes of the prize works (paid)
$PY -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=curvature 04_field_forecast/field_context_prompts.ipynb   # step 4a notes (free, ~2 min)
(cd record && PATH=/software/texlive-2023/bin/x86_64-linux:$PATH TEXMFVAR=/scratch/midway3/jdwoon0523/texmf-var2023b pdflatex -interaction=nonstopmode -output-directory build Record.tex)   # x3
```

API keys are read only from environment variables (names in `config.yaml`: `COMMITTEE_ANTHROPIC_API_KEY`,
`OPENAI_API_KEY`, `GEMINI_API_KEY`), inside `llm_providers.py` at request time; nothing prints, logs or stores a key.
In the VS Code extension the tool shell does not inherit variables exported in an integrated terminal: export them in
the shell that runs the commands.
