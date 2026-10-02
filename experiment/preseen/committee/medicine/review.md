# Committee review — Physiology or Medicine 2026

Generated 2026-10-01T20:13:40+00:00 by `committee.py aggregate --field medicine` from `ballots.jsonl`. Every merge is listed below with its reason. Option = top-K discovery; score = normalized Borda (each model contributes equally).

## Ballots

| model | valid | missing | reported model(s) | ballots with warnings |
|---|---|---|---|---|
| claude-opus-5-5 | 6 | 0 | claude-opus-5-5 | 0 |
| gpt-5.5-2026-04-23 | 6 | 0 | gpt-5.5-2026-04-23 | 0 |
| gemini-3.1-pro-preview | 6 | 0 | gemini-3.1-pro-preview | 0 |

## Candidate list (top 12 + Other)

| # | option | score | models | personas | ballots | A | O | G | consensus |
|---|---|---|---|---|---|---|---|---|---|
| 1 | for the discovery of glucagon-like peptide-1 and its development into therapies for diabetes and obesity — Svetlana Mojsov, Jens Juul Holst, Lotte Bjerre Knudsen | 11.500 | 3 | 6 | 15 | 5.000 | 5.000 | 1.500 | cross-model consensus |
| 2 | for the development of optogenetics, a method to control the activity of genetically defined neurons with light — Karl Deisseroth, Peter Hegemann, Gero Miesenböck | 9.500 | 3 | 6 | 16 | 3.667 | 2.000 | 3.833 | cross-model consensus |
| 3 | for the development of chimeric antigen receptor T-cell therapy — Carl H. June, Michel Sadelain, Steven A. Rosenberg | 5.167 | 3 | 6 | 13 | 0.500 | 2.833 | 1.833 | cross-model consensus |
| 4 | for their discovery of the unfolded protein response — Kazutoshi Mori, Peter Walter | 2.667 | 2 | 6 | 7 | 0.000 | 0.167 | 2.500 |  |
| 5 | for the discovery of PCSK9 and its role in regulating LDL cholesterol metabolism — Helen H. Hobbs, Nabil G. Seidah, Jonathan C. Cohen | 1.667 | 2 | 4 | 5 | 0.500 | 1.167 | 0.000 |  |
| 6 | for their development of high-throughput next-generation DNA sequencing methods — David Klenerman, Shankar Balasubramanian | 1.667 | 1 | 2 | 2 | 0.000 | 0.000 | 1.667 | single-model |
| 7 | for their discovery of orexin and its role in the regulation of sleep and wakefulness — Emmanuel Mignot, Masashi Yanagisawa, Luis de Lecea | 1.667 | 2 | 3 | 3 | 0.000 | 0.333 | 1.333 |  |
| 8 | for their discoveries concerning the Wnt signaling pathway and its application in cultivating organoids — Hans Clevers, Roel Nusse | 1.500 | 2 | 1 | 2 | 0.667 | 0.000 | 0.833 |  |
| 9 | for the discovery of leptin and the hormonal regulation of body weight — Jeffrey M. Friedman, Stephen O'Rahilly | 1.500 | 2 | 4 | 5 | 1.167 | 0.333 | 0.000 |  |
| 10 | for the discovery of tumour necrosis factor as a therapeutic target in chronic inflammatory autoimmune disease — Marc Feldmann, Ravinder N. Maini | 1.333 | 3 | 1 | 3 | 0.667 | 0.500 | 0.167 | cross-model consensus |
| 11 | for the discovery of chaperone-mediated protein folding in cells — Arthur L. Horwich, Franz-Ulrich Hartl | 1.000 | 2 | 2 | 3 | 0.000 | 0.667 | 0.333 |  |
| 12 | for the discovery of inherited susceptibility genes for breast and ovarian cancer — Mary-Claire King, Mark H. Skolnick, Michael R. Stratton | 0.833 | 2 | 2 | 3 | 0.667 | 0.167 | 0.000 |  |
| 13 | Other | | | | | | | | |

A / O / G = normalized points from A = claude-opus-5-5, O = gpt-5.5-2026-04-23, G = gemini-3.1-pro-preview.

Tie at the cut-off (score 0.833), broken by number of models, then number of nominations: 12. for the discovery of inherited susceptibility genes for breast and ovarian cancer — Mary-Claire King, Mark H. Skolnick, Michael R. Stratton (2 models, 3 nominations); 13. for the discovery of the cGAS–STING pathway that senses cytosolic DNA and activates innate immunity — Glen N. Barber, Zhijian J. Chen (1 models, 2 nominations); 14. for his discoveries concerning the role of the gut microbiome in human health and disease — Jeffrey I. Gordon (1 models, 2 nominations)

## Flags (top options)

- #1: Joel F. Habener: deceased (died 2025-12-28 (Wikidata Q96637578; ASBMB Today and Lasker Foundation obituaries)); not shown, next living person by weight shown instead
- #1: 5 people named across nominations; shown: top 3; also: Daniel J. Drucker (3.33), Joel F. Habener (9.00)
- #2: 5 people named across nominations; shown: top 3; also: Edward S. Boyden (4.00), Georg Nagel (0.67)
- #3: Zelig Eshhar: deceased (died 2025-07-03 (Wikidata Q18029986; Leibniz Institute for Immunotherapy notice; Human Gene Therapy tribute 2026)); not shown, next living person by weight shown instead
- #3: 4 people named across nominations; shown: top 3; also: Zelig Eshhar (3.83)
- #5: 4 people named across nominations; shown: top 3; also: Catherine Boileau (0.83)

Deceased people are only detected for Nobel laureates (PrizeAtlas death_date) and through `merges.yaml` person_notes; every name in the top options still needs a check that the person is living.

## Merges

### Automatic: nominations that share a person (first initial + surname)

- **option 1** (15 nominations; shared: d drucker, j habener, j holst, l knudsen, s mojsov)
  - `anthropic/neurology/r1/#1`: for the discovery of glucagon-like peptide-1 and its development into therapies for diabetes and obesity — Joel F. Habener, Svetlana Mojsov, Lotte Bjerre Knudsen
  - `anthropic/molecular-systems-biology/r1/#1`: for the discovery of glucagon-like peptide-1 and its development into therapies for diabetes and obesity — Joel F. Habener, Svetlana Mojsov, Lotte Bjerre Knudsen
  - `anthropic/neuroscience/r1/#1`: for the discovery of the incretin hormone glucagon-like peptide-1 and its role in regulating insulin secretion and appetite — Joel F. Habener, Svetlana Mojsov, Jens Juul Holst
  - `anthropic/molecular-genetics/r1/#1`: for the discovery of the incretin hormone GLP-1 and its development into therapies for diabetes and obesity — Joel F. Habener, Svetlana Mojsov, Lotte Bjerre Knudsen
  - `anthropic/experimental-rheumatology-immunology-autoimmunity/r1/#1`: for the discovery of glucagon-like peptide-1 as an incretin hormone and its development into treatments for diabetes and obesity — Joel F. Habener, Svetlana Mojsov, Lotte Bjerre Knudsen
  - `anthropic/molecular-developmental-biology/r1/#1`: for the discovery of glucagon-like peptide-1 and its role as an incretin hormone regulating glucose homeostasis and appetite — Joel F. Habener, Svetlana Mojsov, Daniel J. Drucker
  - `openai/neurology/r1/#1`: for discoveries concerning glucagon-like peptide-1 and its role in the treatment of diabetes and obesity — Svetlana Mojsov, Jens Juul Holst, Daniel J. Drucker
  - `openai/molecular-systems-biology/r1/#1`: for the discovery of glucagon-like peptide-1 as an incretin hormone — Jens Juul Holst, Joel F. Habener, Svetlana Mojsov
  - `openai/neuroscience/r1/#1`: for the discovery of glucagon-like peptide-1 as an incretin hormone and its role in metabolic regulation — Joel F. Habener, Jens Juul Holst, Svetlana Mojsov
  - `openai/molecular-genetics/r1/#1`: for the discovery of glucagon-like peptide-1 as an incretin hormone and its role in glucose homeostasis — Svetlana Mojsov, Jens Juul Holst, Joel F. Habener
  - `openai/experimental-rheumatology-immunology-autoimmunity/r1/#1`: for discoveries of glucagon-like peptide-1 as an incretin hormone and therapeutic target in metabolic disease — Svetlana Mojsov, Jens Juul Holst, Daniel J. Drucker
  - `openai/molecular-developmental-biology/r1/#1`: for the discovery of glucagon-like peptide-1 as an incretin hormone and its physiological actions enabling therapy for diabetes and obesity — Svetlana Mojsov, Jens Juul Holst, Daniel J. Drucker
  - `gemini/neurology/r1/#4`: for their discoveries concerning glucagon-like peptide-1 and its development as a therapeutic for metabolic disorders — Joel F. Habener, Svetlana Mojsov, Lotte Bjerre Knudsen
  - `gemini/molecular-genetics/r1/#2`: for their discovery of the active form of glucagon-like peptide-1 (GLP-1) and its role in metabolic regulation — Joel Habener, Svetlana Mojsov, Jens Juul Holst
  - `gemini/molecular-developmental-biology/r1/#3`: for their discoveries concerning the physiological function of glucagon-like peptide-1 — Svetlana Mojsov, Joel Habener
- **option 2** (16 nominations; shared: e boyden, g miesenbock, k deisseroth, p hegemann)
  - `anthropic/neurology/r1/#2`: for the discovery of optogenetics, enabling control of genetically defined neurons with light — Karl Deisseroth, Peter Hegemann, Gero Miesenböck
  - `anthropic/molecular-systems-biology/r1/#2`: for the discovery of light-gated ion channels and their use to control neuronal activity (optogenetics) — Peter Hegemann, Karl Deisseroth, Edward S. Boyden
  - `anthropic/neuroscience/r1/#2`: for the discovery of light-gated ion channels and their use to control the activity of defined neurons — Peter Hegemann, Karl Deisseroth, Edward S. Boyden
  - `anthropic/molecular-genetics/r1/#2`: for the discovery of light-gated ion channels and their use to control neuronal activity — Peter Hegemann, Georg Nagel, Karl Deisseroth
  - `anthropic/experimental-rheumatology-immunology-autoimmunity/r1/#3`: for the discovery of light-gated ion channels and their use to control neuronal activity (optogenetics) — Peter Hegemann, Karl Deisseroth, Edward S. Boyden
  - `anthropic/molecular-developmental-biology/r1/#3`: for the discovery of light-gated ion channels and their use to control neuronal activity with light — Peter Hegemann, Karl Deisseroth, Edward S. Boyden
  - `openai/neurology/r1/#3`: for the development of optogenetics for controlling defined cells in neural circuits with light — Gero Miesenböck, Peter Hegemann, Karl Deisseroth
  - `openai/molecular-systems-biology/r1/#3`: for the development of optogenetics, enabling genetically targeted control of neuronal activity with light — Gero Miesenböck, Peter Hegemann, Karl Deisseroth
  - `openai/neuroscience/r1/#3`: for the development of optogenetics for causal control of defined cells in the nervous system — Gero Miesenböck, Peter Hegemann, Karl Deisseroth
  - `openai/molecular-developmental-biology/r1/#3`: for the discovery and development of optogenetic control of neuronal activity — Gero Miesenböck, Peter Hegemann, Karl Deisseroth
  - `gemini/neurology/r1/#1`: for the development of optogenetics, a method to control the activity of genetically defined neurons with light — Karl Deisseroth, Peter Hegemann, Edward Boyden
  - `gemini/molecular-systems-biology/r1/#2`: for their development of optogenetics and its application to mapping neural circuits — Karl Deisseroth, Peter Hegemann, Gero Miesenböck
  - `gemini/neuroscience/r1/#1`: for their development of optogenetics, a method to control the activity of genetically defined neurons with light — Karl Deisseroth, Edward S. Boyden, Gero Miesenbock
  - `gemini/molecular-genetics/r1/#3`: for the development of optogenetics, a method for controlling the activity of neurons with light — Karl Deisseroth, Peter Hegemann, Gero Miesenböck
  - `gemini/experimental-rheumatology-immunology-autoimmunity/r1/#4`: for the development of optogenetics — Karl Deisseroth, Peter Hegemann, Gero Miesenbock **[check: wording overlap with the rest only 0.20]**
  - `gemini/molecular-developmental-biology/r1/#2`: for the development of optogenetics, a method for controlling the activity of neurons with light — Karl Deisseroth, Gero Miesenbock, Peter Hegemann
- **option 3** (13 nominations; shared: c june, m sadelain, z eshhar)
  - `anthropic/neurology/r1/#5`: for the development of chimeric antigen receptor T-cell therapy — Michel Sadelain, Carl H. June
  - `anthropic/experimental-rheumatology-immunology-autoimmunity/r1/#4`: for the development of chimeric antigen receptor T-cell therapy against cancer — Michel Sadelain, Carl H. June
  - `openai/neurology/r1/#2`: for the development of chimeric antigen receptor T-cell therapy for cancer — Zelig Eshhar, Carl H. June, Michel Sadelain
  - `openai/molecular-systems-biology/r1/#2`: for the development of chimeric antigen receptor T-cell therapy for cancer — Zelig Eshhar, Carl H. June, Michel Sadelain
  - `openai/neuroscience/r1/#5`: for the development of chimeric antigen receptor T-cell therapy for cancer — Zelig Eshhar, Carl H. June, Michel Sadelain
  - `openai/molecular-genetics/r1/#3`: for the discovery of chimeric antigen receptor T cells as a programmable cellular therapy for cancer — Zelig Eshhar, Carl H. June, Michel Sadelain
  - `openai/experimental-rheumatology-immunology-autoimmunity/r1/#2`: for the discovery and development of chimeric antigen receptor T cells as a living therapy for cancer — Zelig Eshhar, Michel Sadelain, Carl H. June
  - `openai/molecular-developmental-biology/r1/#5`: for the development of chimeric antigen receptor T cells for cancer therapy — Zelig Eshhar, Michel Sadelain, Carl H. June
  - `gemini/neurology/r1/#3`: for their development of chimeric antigen receptor T-cell therapy for the treatment of cancer — Carl H. June, Michel Sadelain
  - `gemini/molecular-systems-biology/r1/#5`: for their development of chimeric antigen receptor T-cell therapy for the treatment of cancer — Carl H. June, Michel Sadelain
  - `gemini/molecular-genetics/r1/#5`: for their development of chimeric antigen receptor (CAR) T-cell therapy — Carl H. June, Michel Sadelain, Zelig Eshhar
  - `gemini/experimental-rheumatology-immunology-autoimmunity/r1/#1`: for the development of chimeric antigen receptor T-cell therapy — Carl H. June, Michel Sadelain, Zelig Eshhar
  - `gemini/molecular-developmental-biology/r1/#5`: for their development of chimeric antigen receptor T-cell therapy for the treatment of cancer — Carl H. June, Michel Sadelain, Steven A. Rosenberg
- **option 4** (7 nominations; shared: k mori, p walter)
  - `openai/molecular-systems-biology/r1/#5`: for the discovery of the unfolded protein response to endoplasmic-reticulum stress — Peter Walter, Kazutoshi Mori
  - `gemini/neurology/r1/#5`: for their discoveries concerning the unfolded protein response, an intracellular quality control system — Kazutoshi Mori, Peter Walter
  - `gemini/molecular-systems-biology/r1/#3`: for their discoveries of the unfolded protein response and its role in cellular homeostasis — Kazutoshi Mori, Peter Walter
  - `gemini/neuroscience/r1/#3`: for their discoveries of the mechanisms underlying the unfolded protein response, an intracellular quality control system — Kazutoshi Mori, Peter Walter
  - `gemini/molecular-genetics/r1/#4`: for their discoveries of the mechanisms of the unfolded protein response — Kazutoshi Mori, Peter Walter
  - `gemini/experimental-rheumatology-immunology-autoimmunity/r1/#2`: for their discovery of the unfolded protein response — Peter Walter, Kazutoshi Mori
  - `gemini/molecular-developmental-biology/r1/#4`: for their discoveries of the mechanisms of the unfolded protein response — Kazutoshi Mori, Peter Walter
- **option 5** (5 nominations; shared: c boileau, h hobbs, j cohen, n seidah)
  - `anthropic/neuroscience/r1/#4`: for the discovery of PCSK9 as a regulator of plasma cholesterol through human genetics — Nabil G. Seidah, Helen H. Hobbs, Jonathan C. Cohen
  - `anthropic/molecular-genetics/r1/#5`: for the discovery of PCSK9 as a regulator of cholesterol metabolism through human genetics — Nabil G. Seidah, Helen H. Hobbs, Jonathan C. Cohen
  - `openai/neurology/r1/#4`: for the discovery of PCSK9 as a regulator of LDL cholesterol metabolism — Nabil G. Seidah, Helen H. Hobbs, Jonathan C. Cohen
  - `openai/neuroscience/r1/#2`: for the discovery of PCSK9 and its role in regulating LDL cholesterol metabolism — Nabil G. Seidah, Catherine Boileau, Helen H. Hobbs
  - `openai/experimental-rheumatology-immunology-autoimmunity/r1/#5`: for discoveries of PCSK9 as a regulator of LDL cholesterol metabolism and cardiovascular risk — Nabil G. Seidah, Catherine Boileau, Helen H. Hobbs
- **option 6** (2 nominations; shared: d klenerman, s balasubramanian)
  - `gemini/molecular-systems-biology/r1/#1`: for their development of high-throughput next-generation DNA sequencing methods — Shankar Balasubramanian, David Klenerman
  - `gemini/molecular-genetics/r1/#1`: for their development of next-generation DNA sequencing technologies — Shankar Balasubramanian, David Klenerman
- **option 7** (3 nominations; shared: e mignot, m yanagisawa)
  - `openai/molecular-developmental-biology/r1/#4`: for the discovery of orexin/hypocretin signaling and its role in sleep-wake regulation and narcolepsy — Masashi Yanagisawa, Emmanuel Mignot, Luis de Lecea
  - `gemini/neurology/r1/#2`: for their discovery of orexin and its role in the regulation of sleep and wakefulness — Emmanuel Mignot, Masashi Yanagisawa
  - `gemini/neuroscience/r1/#2`: for their discovery of orexins and hypocretins and their critical role in the regulation of sleep and wakefulness — Emmanuel Mignot, Masashi Yanagisawa
- **option 8** (2 nominations; shared: h clevers, r nusse)
  - `anthropic/molecular-developmental-biology/r1/#2`: for their discoveries of the Wnt signaling pathway and its role in development, tissue stem cells and cancer — Roel Nusse, Hans Clevers
  - `gemini/molecular-developmental-biology/r1/#1`: for their discoveries concerning the Wnt signaling pathway and its application in cultivating organoids — Roel Nusse, Hans Clevers
- **option 9** (5 nominations; shared: j friedman)
  - `anthropic/molecular-systems-biology/r1/#3`: for the discovery of leptin and the hormonal regulation of body weight — Jeffrey M. Friedman
  - `anthropic/neuroscience/r1/#5`: for the discovery of leptin and the hormonal regulation of body weight by the brain — Jeffrey M. Friedman
  - `anthropic/experimental-rheumatology-immunology-autoimmunity/r1/#5`: for the discovery of leptin and the hormonal regulation of body weight — Jeffrey M. Friedman, Stephen O'Rahilly
  - `anthropic/molecular-developmental-biology/r1/#4`: for the discovery of leptin and the hormonal regulation of body weight — Jeffrey M. Friedman
  - `openai/experimental-rheumatology-immunology-autoimmunity/r1/#4`: for the discovery of leptin as an adipocyte-derived hormone regulating body weight and energy homeostasis — Jeffrey M. Friedman
- **option 10** (3 nominations; shared: m feldmann, r maini)
  - `anthropic/experimental-rheumatology-immunology-autoimmunity/r1/#2`: for the discovery of tumour necrosis factor as a therapeutic target in chronic inflammatory autoimmune disease — Marc Feldmann, Ravinder N. Maini
  - `openai/experimental-rheumatology-immunology-autoimmunity/r1/#3`: for the discovery of tumor necrosis factor as a therapeutic target in chronic inflammatory disease — Marc Feldmann, Ravinder N. Maini
  - `gemini/experimental-rheumatology-immunology-autoimmunity/r1/#5`: for their discovery of anti-TNF therapy for the treatment of rheumatoid arthritis — Marc Feldmann, Ravinder N. Maini **[check: wording overlap with the rest only 0.00]**
- **option 11** (3 nominations; shared: a horwich, f hartl)
  - `openai/molecular-systems-biology/r1/#4`: for the discovery of chaperone-mediated protein folding in cells — Arthur L. Horwich, F. Ulrich Hartl
  - `openai/molecular-genetics/r1/#4`: for the discovery of chaperonin-mediated protein folding in cells — Arthur L. Horwich, Franz-Ulrich Hartl
  - `gemini/molecular-systems-biology/r1/#4`: for their discoveries concerning the machinery and molecular mechanisms of chaperone-mediated protein folding — Franz-Ulrich Hartl, Arthur L. Horwich
- **option 12** (3 nominations; shared: m king)
  - `anthropic/molecular-genetics/r1/#3`: for the discovery of inherited susceptibility genes for breast and ovarian cancer — Mary-Claire King
  - `anthropic/molecular-developmental-biology/r1/#5`: for the discovery of inherited susceptibility genes for breast cancer — Mary-Claire King
  - `openai/molecular-genetics/r1/#5`: for the discovery of BRCA1 and BRCA2 and their role in inherited breast and ovarian cancer — Mary-Claire King, Mark H. Skolnick, Michael R. Stratton
- **option 13** (2 nominations; shared: g barber, z chen)
  - `anthropic/molecular-systems-biology/r1/#4`: for the discovery of the cGAS–STING pathway of cytosolic DNA sensing in innate immunity — Zhijian J. Chen, Glen N. Barber
  - `anthropic/neuroscience/r1/#3`: for the discovery of the cGAS–STING pathway that senses cytosolic DNA and activates innate immunity — Zhijian J. Chen, Glen N. Barber
- **option 14** (2 nominations; shared: j gordon)
  - `gemini/neuroscience/r1/#4`: for his discoveries concerning the role of the gut microbiome in human health, metabolism, and nutrition — Jeffrey I. Gordon
  - `gemini/experimental-rheumatology-immunology-autoimmunity/r1/#3`: for his discoveries concerning the role of the gut microbiome in human health and disease — Jeffrey I. Gordon
- **option 15** (2 nominations; shared: a krainer, c bennett)
  - `anthropic/neurology/r1/#3`: for the discovery of antisense oligonucleotide correction of SMN2 splicing as a therapy for spinal muscular atrophy — Adrian R. Krainer, C. Frank Bennett
  - `anthropic/molecular-systems-biology/r1/#5`: for the discovery of antisense oligonucleotide-mediated splicing correction as a therapy for spinal muscular atrophy — Adrian R. Krainer, C. Frank Bennett

### Manual (merges.yaml)

- split: `openai/neurology/r1/#5` — p53 tumour-suppressor pathway (Lane, Levine, Vogelstein) is a different discovery from BRCA1/BRCA2 inherited breast-cancer genes (King); the two were linked only through the umbrella nomination below, which names both Vogelstein and King.
- split: `openai/molecular-developmental-biology/r1/#2` — umbrella nomination "oncogenes, tumor-suppressor genes and inherited susceptibility genes in human cancer" (Weinberg, Vogelstein, King) spans several discoveries; kept as its own option instead of joining BRCA and p53.
- deceased: Joel F. Habener — died 2025-12-28 (Wikidata Q96637578; ASBMB Today and Lasker Foundation obituaries)
- deceased: Zelig Eshhar — died 2025-07-03 (Wikidata Q18029986; Leibniz Institute for Immunotherapy notice; Human Gene Therapy tribute 2026)
- people shown for the option of `anthropic/neuroscience/r1/#4`: Helen H. Hobbs, Nabil G. Seidah, Jonathan C. Cohen — tie for the third place (Cohen = Boileau, weight 0.833); Cohen, Hobbs's long-standing collaborator on the human genetics of PCSK9 loss of function (user decision).

### Possibly the same discovery, not merged (for review)

- options 12 and 16 (word overlap 0.44): "for the discovery of inherited susceptibility genes for breast and ovarian cancer" / "for discoveries of oncogenes, tumor-suppressor genes and inherited susceptibility genes in human cancer"

## Per-model top 12 and overlap

- **claude-opus-5-5**: 1; 2; 9; 13; 10; 12; 8; 15; 3; 5; 18; 19 (option numbers of the pooled list; 12 options)
- **gpt-5.5-2026-04-23**: 1; 3; 2; 5; 11; 16; 17; 10; 9; 7; 20; 4 (option numbers of the pooled list; 12 options)
- **gemini-3.1-pro-preview**: 2; 4; 3; 6; 1; 7; 8; 14; 11; 10; 21 (option numbers of the pooled list; 11 options)

| pair | Jaccard of top-12 sets |
|---|---|
| A–O | 0.33 |
| A–G | 0.28 |
| O–G | 0.44 |

Top 12: 4 cross-model consensus (nominated by all three models), 1 single-model.

## Leave-one-out stability

Options of the top 12 that change when one persona (all its ballots) or one model is dropped and the list is recomputed (merges fixed).

| dropped | options changed |
|---|---|
| persona: neurology | 0 |
| persona: molecular systems biology | 1 |
| persona: neuroscience | 0 |
| persona: molecular genetics | 2 |
| persona: experimental rheumatology (immunology, autoimmunity) | 1 |
| persona: molecular developmental biology | 2 |
| model: claude-opus-5-5 | 2 |
| model: gpt-5.5-2026-04-23 | 2 |
| model: gemini-3.1-pro-preview | 3 |
