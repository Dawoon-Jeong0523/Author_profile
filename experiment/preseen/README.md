# Preseen context experiment — 2026 Nobel Prizes in Physiology or Medicine, Physics and Chemistry

**Question.** When an AI forecasting system ([Preseen](https://preseen.com)) is given neutral, descriptive bibliometric
profiles of the people named in a forecasting question, do its probabilities for the 2026 Nobel Prizes move by more
than they move between repeated runs *without* the profiles?

**Answer (runs of 1 October 2026).** Hardly. In all three fields the profiles moved an option by less, on average, than
two runs without profiles differ from each other (0.53×, 0.56× and 0.72× the control run-to-run spread). The leading
discovery and the probability of "Other" are the same in both arms. The forecaster read the profiles — its subforecasts
cite them 8–11 times per run — but says it used them only as a secondary cross-check.

- **Dashboard** (results, reasoning, process, card examples; one self-contained HTML file):
  [`results/dashboard.html`](results/dashboard.html) — download and open it in a browser.
- **Manuscript draft** (protocol, every decision, incidents, appendices): [`../../manuscript/preseen_nobel2026_experiment.tex`](../../manuscript/preseen_nobel2026_experiment.tex)
- **Protocol:** [`SPEC.md`](SPEC.md) · **step log** (time, command, outcome, decision): [`LOG.md`](LOG.md) · **configuration:** [`config.yaml`](config.yaml)

The experiment uses the repository's author-profile pipeline ([`../../README.md`](../../README.md)) for the profiles;
everything specific to the experiment lives in this folder.

## Contents

[Results](#results) · [Design](#design) · [Timeline](#timeline) · [Step 1 — virtual committee](#step-1--a-virtual-nobel-committee) ·
[Step 2 — aggregation and review](#step-2--aggregation-and-review) · [Step 3 — the question](#step-3--the-preseen-question) ·
[Step 4 — profiles](#step-4--author-profiles) · [Step 5 — cards](#step-5--profile-cards) · [Step 6 — runs](#step-6--preseen-runs) ·
[Step 7 — analysis](#step-7--analysis) · [Reproduce](#how-to-reproduce) · [Layout](#folder-layout) · [Keys and data](#keys-secrets-and-what-is-versioned) ·
[Incidents](#incidents-and-deviations-from-the-protocol) · [Limitations](#limitations) · [Costs](#costs)

## Results
### Who each arm predicts

| Field | Control (no context): leading named discovery | Treat (profile cards): leading named discovery | “Other” control → treat |
|---|---|---|---|
| Physiology or Medicine | **21.0 %** Discovery of glucagon-like peptide-1 and its development into therapies for diabetes and … — *Svetlana Mojsov, Jens Juul Holst, Lotte Bjerre Knudsen* (range 18.0 %–22.6 %) | **19.6 %** Discovery of glucagon-like peptide-1 and its development into therapies for diabetes and … — *Svetlana Mojsov, Jens Juul Holst, Lotte Bjerre Knudsen* (range 17.4 %–22.1 %) | 30.5 % → 30.4 % |
| Physics | **14.6 %** Invention and development of optical lattice clocks, enabling time and frequency measurem… — *Hidetoshi Katori, Jun Ye* (range 13.8 %–15.7 %) | **15.4 %** Invention and development of optical lattice clocks, enabling time and frequency measurem… — *Hidetoshi Katori, Jun Ye* (range 14.8 %–16.2 %) | 32.7 % → 31.1 % |
| Chemistry | **18.8 %** Development of massively parallel sequencing-by-synthesis of DNA — *David Klenerman, Shankar Balasubramanian, Pascal Mayer* (range 18.3 %–19.8 %) | **19.2 %** Development of massively parallel sequencing-by-synthesis of DNA — *David Klenerman, Shankar Balasubramanian, Pascal Mayer* (range 18.2 %–20.3 %) | 33.3 % → 33.1 % |

### Effect versus noise

Per option, *Δ* = treat mean − control mean; the noise band is the control run-to-run spread (mean |p<sub>a</sub> − p<sub>b</sub>| over pairs of control runs), averaged over the 13 options.

| Field | Runs (control · treat) | Control run-to-run spread | Mean \|Δ\| | Ratio | Options with the treat mean outside the control range | Rank correlation (Spearman) | Entropy (bits) control → treat |
|---|---|---|---|---|---|---|---|
| Physiology or Medicine | 4 · 3 | 0.89 pp | 0.47 pp | 0.53× | 4: Development of optogenetics, a method to control the activi… +1.41 pp; Discovery of PCSK9 and its role in regulating LDL cholester… +0.73 pp; Discoveries concerning the Wnt signaling pathway and its ap… +0.34 pp; Discovery of chaperone-mediated protein folding in cells -0.77 pp | 0.95 | 3.03 → 3.08 |
| Physics | 4 · 3 | 0.93 pp | 0.51 pp | 0.56× | 2: Invention of aberration-corrected electron optics, enabling… +0.87 pp; Theoretical formulation of cosmic inflation and the predict… -0.22 pp | 0.98 | 3.13 → 3.16 |
| Chemistry | 4 · 3 | 0.70 pp | 0.50 pp | 0.72× | 5: Development of transition-metal-catalyzed C-H functionaliza… -0.59 pp; Discovery of targeted protein degradation by small molecule… +0.46 pp; Discovery of molecular chaperones that assist protein foldi… +0.98 pp; Development of nanopore methods for single-molecule analysi… +0.40 pp; Development of DNA origami and programmable self-assembly o… -0.26 pp | 0.96 | 3.09 → 3.09 |

Pooled over the three fields: mean |Δ| = 0.59× the control spread. “Other” is lower in treat in all three fields (-0.13 pp, -1.61 pp, -0.14 pp), each change within its control range.

### Did the forecaster use the cards?

Mentions per run in the four subforecast write-ups (`results/<field>/terms.csv`):

| Field | References to the supplied bibliometrics: control → treat | “percentile”: control → treat | Final write-up references: treat |
|---|---|---|---|
| Physiology or Medicine | 0.5 → 8.0 | 0.0 → 3.7 | 1.0 |
| Physics | 0.5 → 8.0 | 0.0 → 3.7 | 1.0 |
| Chemistry | 0.0 → 11.0 | 0.0 → 3.3 | 1.0 |

In the forecaster's words (treat subforecasts, Physiology or Medicine): “The user-provided bibliometrics were used as a secondary cross-check.” · “I gave the supplied bibliometrics little quantitative weight, for four reasons:” · “Percentiles among previous laureates cannot by themselves supply a calibrated Nobel-selection probability.”

### Other diagnostics

| Field | Committee Borda score vs control probability (Spearman) | Control run 1 (before any context) vs later control runs | Exploratory: Δ vs the people's laureate comparison on impact |
|---|---|---|---|
| Physiology or Medicine | 0.67 | 0.53 pp per option | 0.52 (p = 0.08, n = 12) |
| Physics | 0.85 | 0.55 pp per option | 0.07 (p = 0.83, n = 12) |
| Chemistry | 0.91 | 0.52 pp per option | 0.01 (p = 0.97, n = 12) |

The exploratory correlation was not pre-specified. It is suggestive in Physiology or Medicine (optogenetics, whose
lead person is above 98 % of past laureates on impact, gains 1.4 points; GLP-1, whose first-named person is above 27 %,
loses 1.4 points within its control range) and absent in Physics and Chemistry.

**Why each arm ranks the discoveries this way** — summaries written from the write-ups: `results/<field>/reasoning_summary.md`;
every run's TL;DR and full write-up are in the dashboard. In short: the forecaster ranks *discoveries* by the strength
and recency of outside recognition (Lasker, Breakthrough, Wolf, Clarivate), treats those awards as correlated evidence
of one achievement, discounts crowded attribution, and keeps 29–35 % on “Other” because it names strong contenders
missing from the list (e.g. cGAS–STING, optical coherence tomography; self-assembled monolayers, base and prime editing).

**Still to come:** the log score of the realised option per arm after the announcements (5, 6 and 7 October 2026):
`$PY analyze.py score --field <field> --option <n>`, then `$PY build_dashboard.py`.

## Design

```
virtual committee ──► Borda aggregation ──► Preseen question ──┬──► control question (no context) ──┐
(personas × 3 LLMs)   + recorded review     (12 + "Other")     └──► treat question (+ cards) ────────┴──► repeated, interleaved runs ──► analysis
                                  │                                          ▲
                                  └── named people ──► author profiles ──► cards (with a laureate reference at prize time)
```

For each field:

1. **Virtual committee.** Personas mirror the specialties of the actual 2026 Nobel Committee (Medicine 6, Physics 8,
   Chemistry 8); every persona runs on three LLMs from different providers (crossed persona × model design). Ballots
   are aggregated by a model-balanced Borda count into 12 candidate discoveries + “Other”.
2. **One question, two arms.** The same private multiple-choice question is created twice on Preseen: **control** (no
   context) and **treat** (one context note per named person plus a definitions note, `treatment=consider`). Context
   notes attach to a question and apply to all its later runs, so separate, identically defined questions are the only
   way to vary the context. A placebo arm (*shuffle*: the same cards with the numbers deranged across people) is
   implemented and switched off (`placebo: false`).
3. **Repeated, interleaved runs.** One control run before any context exists (first look), then three runs per arm,
   interleaved in a random order. The treatment effect per option is compared with the control run-to-run spread.

**Independence.** The committee never sees profiles, cards or Preseen output and uses no tools, web search or
grounding. The question's title, description and resolution criteria are neutral and identical in both arms; they are
checked automatically against forbidden words (committee, model, profile, experiment, Preseen, …).

**Deadlines.** No forecast may run after its prize is announced; all runs finished on 1 October 2026.

| Field | Announcement (earliest, CDT) | Runs had to finish by | Tag |
|---|---|---|---|
| Physiology or Medicine | Mon 05 Oct 04:30 | Sun 04 Oct 23:00 | `nobel26-med` |
| Physics | Tue 06 Oct 04:45 | Mon 05 Oct 23:00 | `nobel26-phys` |
| Chemistry | Wed 07 Oct 04:45 | Tue 06 Oct 23:00 | `nobel26-chem` |

## Timeline

All times 1 October 2026, CDT (details in [`LOG.md`](LOG.md)).

| Time | Step |
|---|---|
| 13:30–13:55 | Phase 0: key names fixed, `check_keys.py` (all four keys HTTP 200), models chosen |
| 13:56–14:14 | Test ballots (one persona, three models); Gemini needed a paid tier first |
| 14:17–14:36 | Committees of all three fields: 66 persona × model cells, all valid |
| 14:23–15:15 | Aggregation, merge review, living check (three deceased nominees replaced) |
| 15:52–15:55 | Questions built; Medicine questions created; Medicine control run 1 |
| 15:56–16:35 | Identity resolution of 98 people; 16 decided by hand |
| 16:34–17:27 | Profiles on Slurm (first batch failed on stale shared caches → one rebuild job → 92 profiles) |
| 17:28–17:33 | Cards built; Physics and Chemistry questions created |
| 17:34–19:19 | Context notes added; runs (paused 18:34–18:46 at the investigator's request) |
| 18:47–19:21 | Analyses, pooled comparison, dashboard |

## Step 1 — a virtual Nobel committee

Each persona is *“a senior member of the Nobel Committee for ⟨field⟩ whose own expertise is ⟨specialty⟩”* — the
specialties of the real 2026 committees, no names, no impersonation, no opinions attributed to real people. Each persona
uses its specialty as a lens but nominates across the whole field.

| Field | Personas |
|---|---|
| Physiology or Medicine (6) | neurology; molecular systems biology; neuroscience; molecular genetics; experimental rheumatology (immunology, autoimmunity); molecular developmental biology |
| Physics (8) | astroparticle physics; theoretical magnetism; applied and theoretical quantum physics; atomic physics; general physics; theoretical physics; complex systems; experimental physics, microscopy and microanalysis |
| Chemistry (8) | nanophysics; medical biochemistry; organic chemistry; physical chemistry; inorganic and structural chemistry; molecular physics; biochemistry; theoretical chemistry |

**Models** (fixed for all fields): Anthropic `claude-opus-5-5`, OpenAI `gpt-5.5-2026-04-23`, Google
`gemini-3.1-pro-preview`. All calls are plain HTTPS with `requests` ([`llm_providers.py`](llm_providers.py)):
Anthropic `/v1/messages` with `output_config.format` (JSON schema), OpenAI `/v1/responses` with a strict `json_schema`
and `store=false`, Gemini `generateContent` with `responseJsonSchema`. The same system and user text go to every
provider; no tools, web search, grounding, sampling, reasoning-effort or fallback parameters are sent, so each provider
runs with its defaults; the output cap is 32,000 tokens. Every response's reported model string equals the requested id.

**Prompt** (`$PY committee.py prompt --field medicine --persona 0` prints it): the persona; the date context (“late
September 2026; the 2026 prize has not been announced”); the rules that matter (the will's wording, at most three
living laureates, a possible division between two discoveries); the field's prizes 2000–2025 with official motivations
and laureates from PrizeAtlas; the task — up to five ranked nominations, each with a one-line discovery in the style of
a prize motivation, 1–3 living people with affiliations, up to 3 key papers if known and a rationale of at most two
sentences — returned as one JSON object.

**Validation.** Structure and types are hard requirements; count limits are warnings. An invalid ballot is asked once
more; a cell that still fails is recorded as missing, never re-asked silently. Transient HTTP errors (408, 429, 5xx) are
retried with back-off; a 429 that reports a zero quota is not retried. All 66 cells were valid on the first attempt.

## Step 2 — aggregation and review

**Model-balanced Borda.** Rank *r* earns 6 − *r* points; each model's points are divided by its number of valid
ballots and summed over models: *S<sub>j</sub>* = Σ<sub>m</sub> *P<sub>m,j</sub>* / *B<sub>m</sub>*. Ties: more models,
then more nominations.

**Merging.** Nominations that share a person are linked automatically (first initial + surname, accents folded; a key
with two different middle initials, such as Charles H. and Charles L. Bennett, is split). A recorded review
(`committee/<field>/merges.yaml`, each entry with its reason; listed in `review.md`) applies three rules: an umbrella
nomination that chains two distinct discoveries becomes an option of its own; discoveries linked only through one
shared person are split; wording taken from an outlier is replaced by the majority wording. It also records aliases,
the third person when two people tie, and deceased people.

| Field | Ballots | Nominations | Options | Splits | Aliases | Wording | People (ties) | Deceased |
|---|---|---|---|---|---|---|---|---|
| Physiology or Medicine | 18 | 90 | 22 | 2 | 0 | 0 | 1 | 2 |
| Physics | 24 | 120 | 21 | 2 | 2 | 1 | 0 | 1 |
| Chemistry | 24 | 120 | 28 | 4 | 2 | 2 | 2 | 0 |

**Diagnostics** (`review.md`): per-model top-12 lists and their Jaccard overlap, cross-model-consensus and single-model
options, leave-one-out stability (drop a persona or a model), and flags (resembles a 2000–2025 motivation, Nobel
laureate or deceased person among the named, more than three people, a person in two options).

**Living check.** All 95 shown people were screened against Wikidata ([`check_living.py`](check_living.py)) and every
death, missing or wrong match, replacement and everyone born ≤ 1940 was checked on the web
([`committee/living_check_web.md`](committee/living_check_web.md)). Three had died and were replaced in the option text
by the next living person: Joel F. Habener (GLP-1, d. 2025-12-28 → Lotte Bjerre Knudsen), Zelig Eshhar (CAR-T,
d. 2025-07-03 → Steven A. Rosenberg), Harald Rose (aberration-corrected electron optics, d. 2026-07-27 → Ondrej L. Krivanek).

### Candidate lists

**Physiology or Medicine** (`committee/medicine/candidates.json`)

| # | Discovery | People shown | Borda | Models | Personas |
|---|---|---|---|---|---|
| 1 | Discovery of glucagon-like peptide-1 and its development into therapies for diabetes and obesity | Svetlana Mojsov, Jens Juul Holst, Lotte Bjerre Knudsen | 11.50 | 3 | 6 |
| 2 | Development of optogenetics, a method to control the activity of genetically defined neurons with light | Karl Deisseroth, Peter Hegemann, Gero Miesenböck | 9.50 | 3 | 6 |
| 3 | Development of chimeric antigen receptor T-cell therapy | Carl H. June, Michel Sadelain, Steven A. Rosenberg | 5.17 | 3 | 6 |
| 4 | Discovery of the unfolded protein response | Kazutoshi Mori, Peter Walter | 2.67 | 2 | 6 |
| 5 | Discovery of PCSK9 and its role in regulating LDL cholesterol metabolism | Helen H. Hobbs, Nabil G. Seidah, Jonathan C. Cohen | 1.67 | 2 | 4 |
| 6 | Development of high-throughput next-generation DNA sequencing methods | David Klenerman, Shankar Balasubramanian | 1.67 | 1 | 2 |
| 7 | Discovery of orexin and its role in the regulation of sleep and wakefulness | Emmanuel Mignot, Masashi Yanagisawa, Luis de Lecea | 1.67 | 2 | 3 |
| 8 | Discoveries concerning the Wnt signaling pathway and its application in cultivating organoids | Hans Clevers, Roel Nusse | 1.50 | 2 | 1 |
| 9 | Discovery of leptin and the hormonal regulation of body weight | Jeffrey M. Friedman, Stephen O'Rahilly | 1.50 | 2 | 4 |
| 10 | Discovery of tumour necrosis factor as a therapeutic target in chronic inflammatory autoimmune disease | Marc Feldmann, Ravinder N. Maini | 1.33 | 3 | 1 |
| 11 | Discovery of chaperone-mediated protein folding in cells | Arthur L. Horwich, Franz-Ulrich Hartl | 1.00 | 2 | 2 |
| 12 | Discovery of inherited susceptibility genes for breast and ovarian cancer | Mary-Claire King, Mark H. Skolnick, Michael R. Stratton | 0.83 | 2 | 2 |
| 13 | Other | | | | |

**Physics** (`committee/physics/candidates.json`)

| # | Discovery | People shown | Borda | Models | Personas |
|---|---|---|---|---|---|
| 1 | Theoretical prediction and experimental discovery of topological insulators and the quantum spin Hall effect | Charles L. Kane, Eugene J. Mele, Laurens W. Molenkamp | 8.75 | 3 | 8 |
| 2 | Invention and development of optical lattice clocks, enabling time and frequency measurements at unprecedente… | Hidetoshi Katori, Jun Ye | 7.00 | 3 | 8 |
| 3 | Theoretical prediction and experimental realization of negative index metamaterials | John B. Pendry, David R. Smith, Eli Yablonovitch | 5.12 | 3 | 8 |
| 4 | Discovery of topological and geometric phases in quantum systems | Michael V. Berry, Yakir Aharonov | 4.12 | 3 | 6 |
| 5 | Theoretical prediction and experimental discovery of correlated insulator behavior and superconductivity in m… | Allan H. MacDonald, Pablo Jarillo-Herrero, Rafi Bistritzer | 3.00 | 3 | 8 |
| 6 | Foundational discoveries in quantum information science, including quantum cryptography and quantum algorithms | Charles H. Bennett, Gilles Brassard, Peter W. Shor | 2.50 | 2 | 4 |
| 7 | Pioneering contributions to neutrino astronomy, in particular the discovery of high-energy cosmic neutrinos | Francis Halzen, Albrecht Karle, Naoko Kurahashi Neilson | 2.12 | 3 | 2 |
| 8 | Observation of the shadow of a black hole by event-horizon-scale radio interferometry | Heino Falcke, Sheperd S. Doeleman, Katherine L. Bouman | 1.88 | 2 | 6 |
| 9 | Theoretical proposals and experimental realizations of quantum simulators using ultracold atoms in optical la… | Immanuel Bloch, J. Ignacio Cirac, Peter Zoller | 1.88 | 2 | 4 |
| 10 | Invention of the quantum cascade laser | Alfred Y. Cho, Federico Capasso, Jérôme Faist | 1.75 | 2 | 5 |
| 11 | Invention of aberration-corrected electron optics, enabling electron microscopy with sub-ångström resolution | Maximilian Haider, Knut Urban, Ondrej L. Krivanek | 1.50 | 3 | 1 |
| 12 | Theoretical formulation of cosmic inflation and the prediction of the quantum origin of cosmological structure | Alan H. Guth, Andrei Linde, Viatcheslav Mukhanov | 1.25 | 3 | 3 |
| 13 | Other | | | | |

**Chemistry** (`committee/chemistry/candidates.json`)

| # | Discovery | People shown | Borda | Models | Personas |
|---|---|---|---|---|---|
| 1 | Development of controlled radical polymerization | Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo | 8.62 | 3 | 8 |
| 2 | Development of massively parallel sequencing-by-synthesis of DNA | David Klenerman, Shankar Balasubramanian, Pascal Mayer | 8.62 | 3 | 8 |
| 3 | Discovery and development of solid-state perovskite solar cells | Henry J. Snaith, Nam-Gyu Park, Tsutomu Miyasaka | 4.25 | 3 | 8 |
| 4 | Development of phosphoramidite chemistry for automated DNA synthesis | Marvin H. Caruthers, Serge L. Beaucage, Mark D. Matteucci | 3.25 | 3 | 4 |
| 5 | Development of transition-metal-catalyzed C-H functionalization reactions | John F. Hartwig, Jin-Quan Yu, Robert G. Bergman | 2.50 | 2 | 5 |
| 6 | Development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids | Pieter R. Cullis, Robert S. Langer, Kazunori Kataoka | 2.38 | 2 | 8 |
| 7 | Discovery of targeted protein degradation by small molecules that redirect ubiquitin ligases | Craig M. Crews, Raymond J. Deshaies, Stuart L. Schreiber | 1.88 | 3 | 5 |
| 8 | Discovery of molecular chaperones that assist protein folding in the cell | Arthur L. Horwich, F. Ulrich Hartl | 1.75 | 2 | 2 |
| 9 | Development of nanopore methods for single-molecule analysis and sequencing of nucleic acids | David W. Deamer, Hagan Bayley, Daniel Branton | 1.62 | 2 | 3 |
| 10 | Development of ab initio molecular dynamics | Michele Parrinello, Roberto Car | 1.50 | 3 | 3 |
| 11 | Development of efficient organic light-emitting diodes | Ching W. Tang, Steven A. Van Slyke, Mark E. Thompson | 1.12 | 2 | 4 |
| 12 | Development of DNA origami and programmable self-assembly of DNA nanostructures | Paul W. K. Rothemund, William M. Shih, Hao Yan | 1.12 | 2 | 2 |
| 13 | Other | | | | |

## Step 3 — the Preseen question

Built by [`build_question.py`](build_question.py) into `questions/<field>.json` from templates in `config.yaml`:

- **Title:** Which discovery will the 2026 Nobel Prize in Physiology or Medicine be awarded for?
- **Description:** The 2026 Nobel Prize in Physiology or Medicine is scheduled to be announced on Monday 5 October 2026. Each option names a discovery and the people most closely associated with it.
- **Resolution criteria:** Resolves to the option whose discovery matches the discovery named in the official motivation of the 2026 Nobel Prize in Physiology or Medicine, as published at nobelprize.org. Options are matched by discovery; the people named in an option need not match the laureates exactly. If the prize is divided between two discoveries, only the discovery with the larger share counts; if the shares are equal, the discovery named first in the announcement counts. If no option matches that discovery, the question resolves to Other.
- **Options:** the 12 option texts (“⟨discovery⟩ — ⟨Name A⟩, ⟨Name B⟩, ⟨Name C⟩”) + “Other”; mutually exclusive and
  comprehensive; private.

The client ([`nobel_preseen_exp.py`](nobel_preseen_exp.py), unchanged during the experiment) creates one question per arm
and verifies that the stored definitions are identical and that no automatic re-forecast watch is on.

## Step 4 — author profiles

- **People:** `people/<field>.txt` lists every person shown in the options (98 rows, 94 distinct people; four appear in
  two fields).
- **Identity resolution:** the repository's name pipeline (`pipeline/profile_person.py`). Its command-line dry run scans
  the 6 GB snapshot authors table once per person (~1.5 min each), so a faster local script (not versioned) called the same,
  unchanged `resolve()` on a one-scan subset of the table (rows whose names contain one of the surnames, the resolver's
  own substring test); for the 11 people both runs had finished, the results were identical.
- **Review:** every unresolved or doubtful pick was checked with candidate tables, OpenAlex author lookups (topics,
  institutions) and the public ORCID API; 16 people were decided by hand (`people/<field>_choices.yaml`, with reasons):
  - Physiology or Medicine: Michel Sadelain (`A5059625599;A5103081365;A5058976864`); Peter Walter (`A5087493059`); Emmanuel Mignot (`A5073040042;A5021339764;A5109153776`); Stephen O'Rahilly (`A5013261212`); Mark H. Skolnick (`A5110003746;A5108406066`)
  - Physics: Jun Ye (`A5100382923;A5029823127;A5108688194`); Maximilian Haider (`A5085200056`); Alan H. Guth (`A5105707535`); Michael V. Berry (`A5032503181;A5006305535`); Knut Urban (`A5102812716`)
  - Chemistry: Pascal Mayer (`A5050699304`); John F. Hartwig (`A5088865204`); Jin-Quan Yu (`A5108685090;A5122352517`); Michele Parrinello (`A5023487560;A5109157985`); Ching W. Tang (`A5085816509;A5103415041;A5075010179`); Steven A. Van Slyke (`A5025520043;A5036976819`)
- **Identity table:** `people/<field>_identity.csv` (options, chosen ids and rule, ORCID, institution, works,
  citations, expected inventor source).
- **Profiles:** [`submit_profiles.py`](submit_profiles.py) submits one Slurm job per distinct id set through the
  pipeline's own `resolve()` and `run()` (unchanged), with the experiment's API keys removed from the submitting
  environment so that `sbatch --export=ALL` does not copy them; an existing profile with the same ids and window is
  reused, never re-run. 92 new profiles + 2 reused, about 1.7 minutes each.

## Step 5 — profile cards

> **Since 2026-10-03** the cards the runs used are in [`cards_v1/`](cards_v1/) (moved unchanged; `analyze.py` and the
> dashboards read them there), and [`cards/`](cards/) holds the same cards rebuilt after the pipeline's inventor linking
> was refined: only the own-patent and co-author/co-inventor lines differ ([`cards/README.md`](cards/README.md),
> [`cards/CHANGES.md`](cards/CHANGES.md)). In this README, `cards/` paths describing the runs refer to `cards_v1/`.

[`build_cards.py`](build_cards.py) writes `cards/<field>/00_definitions.md` and one card per person (300–500 words,
fixed template, English):

- name, affiliation (OpenAlex last known institution), the option(s), prior Nobel Prize;
- **impact:** research works analysed, median 5-year citation percentile, shares in the cohort top 10 % and top 1 %;
- **three defining works** (most cited research works ≤ 2021): impact and disruption percentiles, Foundation share,
  citing inventions and citing books;
- **technological translation:** distinct citing inventions, own US utility patents;
- **textbook reach:** works cited by books, distinct citing books;
- **collaboration:** Nobel laureate co-authors (with the number of shared works), people who are both co-authors and
  co-inventors;
- a **reference line** per headline metric: the share of the field's 2000–2025 laureates the person exceeds,
  **measured at the time of their prize** (only works, and patent and book citations, dated before the prize year).

The definitions note defines every measure neutrally and ends with “These are descriptive bibliometric measures, not
forecasts.” Cards never mention the committee, the forecasting question or the experiment.

| Field | Laureates in the reference | Impact median | Top 10 % | Citing inventions | Own patents | Citing books |
|---|---|---|---|---|---|---|
| Physiology or Medicine | 60 | 0.931 | 58.6 % | 256 | 5 | 731 |
| Physics | 62 | 0.865 | 42.4 % | 8 | 0 | 459 |
| Chemistry | 61 | 0.901 | 50.9 % | 203 | 6 | 593 |

(Medians at prize time, `cards_v1/laureate_reference.csv`; 18 laureates without a usable profile are listed in
`cards_v1/laureate_reference_missing.json`.) The metric function reproduces a pipeline record exactly (Geoffrey Hinton: 175
research works, impact median 0.964, 63.6 % top 10 %, 34.1 % top 1 %, 13 patents, 5,192 citing inventions, 25,117 citing
books).

Card examples are in the dashboard and in `cards_v1/medicine/svetlana-mojsov.md`, `cards_v1/medicine/karl-deisseroth.md`,
`cards_v1/physics/john-b-pendry.md`, `cards_v1/chemistry/krzysztof-matyjaszewski.md`.

## Step 6 — Preseen runs

Client invariants: identical private questions per arm; notes with `treatment=consider` (definitions first, cards in a
seeded random order identical across arms); `allow_incomplete_context=false`; no `source_forecast_id`, no
`accept-context`, no watches or schedules; randomised interleaving of arms; at most three active runs per field; an
Idempotency-Key on every POST (re-running a command never duplicates a question, note or run).

Per field: `create` (control, treat) → control run 1 → `add-context` to treat (Medicine 31 notes, Physics 35, Chemistry
35) → `run --arms control treat --reps 3` → `poll` → `table`. One run takes ~25 minutes and combines four subforecasts
into the final forecast (`forecast.forecast_data.payload.probabilities`; schema in `results/medicine/schema.md`).

## Step 7 — analysis

[`analyze.py`](analyze.py) (`field`, `pooled`, `score`) writes `results/<field>/`:

| File | Content |
|---|---|
| `runs_long.csv` | every run × option probability |
| `by_option.csv` | per arm × option: n, mean, sd, min, max |
| `effects.csv` | per option: control mean, sd, range; treat mean; Δ; Δ / control sd; outside the control range |
| `subforecasts.csv` | per arm × subforecast × option mean |
| `terms.csv` | metric terms per run in the final and the subforecast write-ups |
| `committee_vs_preseen.csv` | Borda score, number of models, control mean |
| `card_strength_vs_effect.csv` | exploratory: the people's laureate comparison vs Δ |
| `summary.json` | everything above in one object, plus uptake quotes |
| `option_probabilities.png`, `treat_minus_control.png`, `captions.md` | figures; series and bars are defined in the captions |
| `reasoning_summary.md` | summary of the forecaster's reasoning, written with Claude (an LLM) |

`results/pooled/pooled.csv` compares the fields; [`build_dashboard.py`](build_dashboard.py) writes `results/dashboard.html`.

## How to reproduce

```bash
cd experiment/preseen
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib; PY=/project/jevans/Dawoon/env/Curvature/bin/python
# keys only as environment variables: PRESEEN_API_KEY, COMMITTEE_ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY

# committee (paid LLM calls)
$PY committee.py test                               # one persona on each model
$PY committee.py estimate                           # cost of all committees from the test usage
$PY committee.py run --fields medicine physics chemistry --workers 2
$PY committee.py aggregate --field medicine         # reads committee/medicine/merges.yaml; writes candidates.json, review.md
$PY check_living.py                                 # Wikidata screen of the shown people

# question, people, profiles, cards
$PY build_question.py                               # questions/<field>.json
$PY ../../pipeline/profile_person.py --names-file people/medicine.txt --dry-run > people/medicine_dryrun.log
$PY people.py identity --field medicine   # + people/medicine_choices.yaml
$PY submit_profiles.py                              # Slurm, one job per id set (--only <name> for a single job)
$PY build_cards.py reference && $PY build_cards.py cards --field medicine

# Preseen (paid; remote state)
export EXP_DIR=preseen_exp/medicine; TAG=nobel26-med
$PY nobel_preseen_exp.py --tag $TAG create --question questions/medicine.json --arms control treat
$PY nobel_preseen_exp.py --tag $TAG run --arms control --reps 1
$PY nobel_preseen_exp.py --tag $TAG add-context --arm treat --cards cards/medicine/
$PY nobel_preseen_exp.py --tag $TAG run --arms control treat --reps 3
$PY nobel_preseen_exp.py --tag $TAG poll --wait && $PY nobel_preseen_exp.py --tag $TAG table

# analysis and dashboard
$PY analyze.py field --field medicine && $PY analyze.py pooled
$PY build_dashboard.py
```

## Folder layout

```
experiment/preseen/
├── SPEC.md, LOG.md, config.yaml        protocol, step log, configuration (fields, models, prices, templates)
├── nobel_selection_process.md         background on the prize process and the 2026 committees
├── llm_providers.py                   one call per provider over HTTPS
├── committee.py                       prompt, test, run, collect, estimate, aggregate, diagnostics
├── check_living.py                    Wikidata living screen
├── build_question.py                  candidate list -> question JSON
├── people.py                          identity tables
├── submit_profiles.py                 Slurm profile submission
├── build_cards.py                     laureate reference and cards
├── nobel_preseen_exp.py               Preseen client
├── analyze.py                         per-field and pooled analysis, figures
├── build_dashboard.py                 results/dashboard.html
├── committee/<field>/                 ballots.jsonl, merges.yaml, candidates.json, clusters.json, review.md, living_check.csv
├── committee/logs/, committee/living_*  run log, Wikidata cache, web verification
├── questions/<field>.json
├── people/                            <field>.txt, dry-run logs, <field>_identity.csv, <field>_choices.yaml, profile_jobs.csv
├── cards_v1/<field>/                  the cards the runs used: 00_definitions.md + one card per person; laureate_reference.csv
├── cards/<field>/                     the same cards rebuilt 2026-10-03 (inventor linking); README.md, CHANGES.md
└── results/<field>/, results/pooled/, results/dashboard.html
```

## Keys, secrets and what is versioned

- Keys are only environment variables, read with `os.environ[...]` inside Python at the moment of a request and sent
  only in headers; nothing prints, logs or writes a key; no key ever appears on a command line. The committee's
  Anthropic calls read `COMMITTEE_ANTHROPIC_API_KEY`; `ANTHROPIC_API_KEY` is deliberately never set.
- Error bodies of 401/403 responses are not kept (some echo a masked key); exceptions are recorded by class name.
- Not versioned: `preseen_exp/` (Preseen client state, question and task ids, every run JSON with its write-up and
  sources), `committee/*/raw/` (raw LLM responses), and all `*.parquet` files (including the authors subsets of the dry
  runs). The analysis tables, the dashboard (which embeds the write-ups) and the cards are versioned.

## Incidents and deviations from the protocol

1. **Keys.** The first Anthropic key returned HTTP 401 and was replaced; the Gemini key's project was on the free tier
   (zero quota for the model) until billing was enabled.
2. **Max Zhu's shortlist** (planned coverage diagnostic) is not used; that folder was never accessed.
3. **OpenAlex API budget.** List and search endpoints returned HTTP 429 (no API key; the shared IP's free daily budget
   was used up); name resolution fell back to the 2026-01 snapshot, single-entity lookups were used where needed.
4. **Faster dry run** instead of the command-line dry run (same resolver, validated on 11 people).
5. **Stale shared caches.** `paper_metadata.parquet` had been rewritten at 13:28 (an intended update in a related
   project); all 93 first profile jobs then tried to rebuild the shared percentile caches at once and collided. They
   were cancelled, 15 orphan temporary files (~45 GB) deleted with approval, the caches rebuilt by one job, and the rest
   resubmitted. The citation percentiles of 13 laureate profiles (7,134 papers) are identical to the rebuilt cache, so the
   laureate reference stays comparable.
6. **Wikidata rate limit** during the living check; re-run with pacing and a cache.
7. **Pause.** Preseen submissions were paused 18:34–18:46 at the investigator's request; seven runs already submitted
   finished server-side; the four remaining runs were submitted on resume (the Chemistry order of the last three runs
   follows the resume, not the original random plan).
8. **Option texts** were changed by hand only through recorded `merges.yaml` decisions, approved at the committee
   checkpoint.

## Limitations

- Few runs (4 control, 3 treat per field): a coarse noise band and a descriptive comparison, not a significance test.
- The cards are a bundle of many numbers; without the placebo arm, “more text about these people” cannot be separated
  from “these particular numbers”.
- The options come from three correlated language models; a prize for another discovery resolves to “Other” in both
  arms; three nominees had died after the models' training data.
- OpenAlex splits and merges authors; some profiles are thin or undercounted; patent counts from the PatentsView name
  search and id-matched laureate co-authors may include namesakes.
- One forecasting system on one day; resolution by discovery may need judgement when a motivation is broader or narrower
  than an option.

## Costs

| Item | Cost |
|---|---|
| Committee, `claude-opus-5-5` (60,176 input / 72,791 output tokens) | $1.70 |
| Committee, `gpt-5.5-2026-04-23` (33,152 input / 134,585 output tokens) | $4.20 |
| Committee, `gemini-3.1-pro-preview` (32,210 input / 96,154 output tokens) | $1.22 |
| Committee total (66 cells) | **$7.12** |
| Test ballots | about $0.33 |
| Preseen: 6 questions, 101 context notes, 21 runs | not reported by the API (see the Preseen account) |
| OpenAlex, Wikidata, ORCID lookups; Slurm profiles | free / cluster allocation |
