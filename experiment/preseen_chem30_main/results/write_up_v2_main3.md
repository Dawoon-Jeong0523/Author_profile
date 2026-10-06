## TL;DR
Mass-spectrometry-based proteomics leads my conditional forecast at 9%, followed by self-assembled monolayers at 9% and dye-sensitized solar cells at 8% ([calculation ledger](sandbox:/mnt/data/forecast_model.md)). Together, those discoveries account for 26% of the probability ([calculation ledger](sandbox:/mnt/data/forecast_model.md)). Use the full distribution: this is an open field, not a dominant-favorite forecast ([submitted distribution](sandbox:/mnt/data/forecast_model.md)).

## Context
The information cutoff is October 6, 2026, at 22:22 UTC, after the question was submitted at 22:01 UTC ([client-supplied cutoff](sandbox:/mnt/data/supplied_evidence.md)). Chemistry is scheduled for October 7, 2026, at 11:45 CEST at the earliest, equivalent to 09:45 UTC ([official calendar](https://www.nobelprize.org/prizes/about/prize-announcement-dates/)). The remaining uncertainty concerns the committee's choice and motivation, not scientific progress before the announcement.

This forecast is conditional on a listed discovery winning. Exact laureate names do not control resolution. A divided prize is matched by the larger discovery share, or the first-mentioned discovery when shares are equal; overlapping options are matched to the most specific description ([resolution rules](sandbox:/mnt/data/supplied_evidence.md)). I accept the supplied Medicine and Physics outcomes as premises and use them only for the limited calibration requested.

## Evidence
The historical backbone is the supplied reference class: 26 Chemistry prize years covering 2000–2025, with roughly 15–20% awarded within ten years of the decisive realization, about a third after 10–25 years, and roughly 45% after more than 25 years. The median lag is approximately 25 years. These are approximate cohort aggregates, not a reconstructed annual series. The fast-award examples were tools or structures adopted rapidly across their fields, including CRISPR and AlphaFold ([supplied timing prior](sandbox:/mnt/data/supplied_evidence.md)).

The profile comparison cohort contains 61 Chemistry laureates from 2000–2025, measured at their prize dates. The candidate records use the January 2026 OpenAlex snapshot, December 31, 2025 PatentsView vintage, and supplied patent-to-paper links; eligible works and granted patents run through 2021. Impact and disruption are five-year cohort percentiles. Foundation is a share. Inventions, patents, books, and later patent citations are distinct counts, not interchangeable measures ([definitions and vintage](sandbox:/mnt/data/supplied_evidence.md)).

Three checks drove the analysis: whether a prominent work actually supports the named discovery; whether a broad option survives the specificity rule; and whether original authorship or independent recognition adds evidence beyond the profiles. I discarded subject-area rotation arguments, public poll totals, and automatic penalties for neighboring fields having won before. No prediction-market prices enter the calculation ([model and relevance ledger](sandbox:/mnt/data/forecast_model.md)).

The scoring model gives career impact weight 0.20, technological translation 0.15, textbook reach 0.15, collaboration 0.05, discovery-relevant works 0.30, and discovery-specific patents 0.15. Grades run from zero to one and are analyst assessments anchored to the supplied reference comparisons. The work grade considers impact, disruption, Foundation, uptake, and the realization that made the discovery useful. The patent grade considers downstream citations, discovery-related portfolio size and concentration, and enabling disclosures. Missing disruption or Foundation values are unknown, not zero. Reviews establish diffusion and consolidation but do not substitute for an original demonstration ([complete scoring inputs](sandbox:/mnt/data/forecast_model.md)).

For each career component, a multi-person option receives half the strongest retained named profile plus half the mean retained named profile. A singleton receives its own profile unchanged. A person appearing in multiple options contributes fully to each. Relevant papers and patents are pooled and deduplicated, rather than multiplied by the number of names. Collaboration receives diminishing-return grades and a small weight. This implements the supplied Medicine and Physics lessons without treating either committee's outcome as evidence that a chemistry area is due ([aggregation rule and accepted reference outcomes](sandbox:/mnt/data/forecast_model.md)).

Let \(H_i\) be the weighted profile score, \(M_i\) the maturity factor, \(Q_i\) the motivation-matching factor, and \(f_i\) the secondary evidence factor. The calculation is:

$$
u_i=\exp(9H_i)M_iQ_i,
\qquad
p_i^{\mathrm{profile}}=\frac{u_i^{0.85}}{\sum_j u_j^{0.85}},
\qquad
p_i^{\mathrm{final}}=\frac{(u_if_i)^{0.85}}{\sum_j(u_jf_j)^{0.85}}.
$$

The common 0.85 power flattens every arm identically. There is no uniform probability floor. The scale and grades are judgmental, not fitted selection coefficients; the exact inputs and normalized results are disclosed in the [calculation ledger](sandbox:/mnt/data/forecast_model.md).

Maturity enters once. The factor is 0.80 for sequencing-by-synthesis, solid-state perovskites, targeted degradation, DNA origami, and genetic-code expansion; 0.40 for the combined base/prime-editing record; and the square root of 0.80 for combined solar cells, combined DNA synthesis/sequencing, and chemical genetics/KRAS. Other factors are 1.00, reflecting mature anchors or a neutral treatment where the card does not establish the original discovery date. Relevant papers and patent filings anchor these judgments; later reviews do not restart the clock. The editing profiles show substantial uptake, but do not establish adoption comparable to the strongest fast-award precedents ([maturity anchors and factors](sandbox:/mnt/data/forecast_model.md)).

The matching factor is 0.30 for combined dye/perovskite cells and 0.25 for combined DNA synthesis/sequencing, with 1.00 elsewhere. These are interpretations of this question's resolution mechanics, not external scientific penalties. A narrow sequencing or perovskite motivation goes to its narrower option; the combined arm needs an integrated motivation that survives the share and specificity rules ([matching judgments](sandbox:/mnt/data/forecast_model.md)).

The permitted reliability adjustments affect aggregate career evidence, not clearly identified landmark works or patents:

- Retention factor 0.95 for Grätzel, Liu, and Roberto Car, reflecting modest affiliation/identity ambiguity; 0.90 for Yan's affiliation ambiguity and Mann's unusually early publication window ([profile issues and factors](sandbox:/mnt/data/forecast_model.md)).
- Retention factor 0.85 for Yates, Hartl, Balasubramanian, Bergman, and Chin; 0.80 for Evans and Herrmann; 0.75 for Gray and Bertrand; and 0.65 for Rothemund. These address visible publication-window anomalies ([profile issues and factors](sandbox:/mnt/data/forecast_model.md)).
- Van Slyke receives career retention 0.75 for the 15-work sample. His identified OLED work and patents remain usable. Suntola's 50 works and Rothemund's 53 works receive no additional small-sample penalty ([sample sizes and factors](sandbox:/mnt/data/supplied_evidence.md)).
- The anomalous Rothemund–Hans Fischer and Hammes-Schiffer–Bertozzi coauthor entries receive retention zero within collaboration assessment. Patent/book-uptake support from Miyasaka's 2019 review, Park's 2020 review, and Liu's 2019 prime-editing paper receives retention 0.75; completed five-year impact remains intact. Every other career reliability factor is 1.00 ([adjustment ledger](sandbox:/mnt/data/forecast_model.md)).

The following registry states which numbered card entries count. W1–W3 and P1–P3 refer to the client's defining works and selected patents. Shared entries count once. Omitted entries are excluded from discovery-specific scoring, while career evidence remains available. Supporting reviews, mechanisms, fabrication methods, and applications receive less decisive weight than first realizations ([relevance ledger](sandbox:/mnt/data/forecast_model.md)).

| Discovery | Relevant supplied works and patents |
|---|---|
| Sequencing-by-synthesis | Balasubramanian W1/P1–P3; Klenerman W1/P1 |
| Controlled radical polymerization | Matyjaszewski W1–W3/P1–P3; Sawamoto W1–W2/P1, W3 supporting |
| Solid-state perovskites | Snaith W1–W3/P1–P3; Miyasaka W1, W2 supporting; Park W1–W3/P1–P3 |
| Drug/nucleic-acid delivery | Cullis W1–W3/P1–P3 |
| Phosphoramidite synthesis | Caruthers W1, W3/P1–P3 |
| C–H functionalization | Hartwig W1/P3; Bergman W1–W3/P1–P3 |
| Nanopore methods | Bayley, Deamer and Branton W1–W3/P1–P3; pore structure and fabrication supporting |
| Self-assembled monolayers | Allara W1–W3/P1; Nuzzo W1–W2/P1–P3; Whitesides W2/P1–P3, W3 supporting |
| Protein electron transfer | Gray P1 supporting; no listed defining work directly establishes protein electron transfer |
| Base/prime editing | Liu W1–W3/P1–P3 |
| Targeted protein degradation | Crews W1–W3/P1–P3; Deshaies W2/P1, W1 and W3 mechanistic support |
| Ab initio molecular dynamics | Parrinello W3; Car W2, W1 software support; no tied patent |
| Molecular chaperones | Hartl and Horwich W1–W3/P1–P3; Hartl P3 is an application |
| Combined dye/perovskite cells | Grätzel W1–W3/P1–P3 plus the Snaith and Miyasaka entries above |
| OLEDs | Van Slyke W1–W3/P1–P3; Tang W2–W3/P1–P3 |
| DNA origami | Rothemund W1–W2/P1–P3; Shih and Yan W1–W3/P1–P3; application papers supporting |
| Pd carbon–heteroatom coupling | Buchwald W1, W3/P1–P3; Hartwig W2–W3/P1–P2 |
| Combined DNA synthesis/sequencing | Union of the sequencing and phosphoramidite entries |
| Exchange-correlation functionals | Perdew W1–W3; no patent |
| Chemical genetics/KRAS | Shokat P1–P3; W2 only supporting kinase pharmacology |
| Genetic-code expansion | Schultz W3/P1–P3; Chin W1–W3/P1–P3 |
| Atomic layer deposition | Suntola W1–W3/P1–P3; patents supply the foundational realization |
| Carbohydrate/glycoprotein synthesis | Wong W3/P1–P3 |
| MS-based proteomics | Yates W1–W2/P1–P3; Mann W1–W3/P1–P3; Aebersold W1–W3/P1–P2 |
| Dye-sensitized cells | Grätzel W1–W2/P1–P3 |
| Stable/NHC carbenes | Arduengo and Bertrand W1–W3/P1–P3; Herrmann W1–W2/P1–P3 |
| Bacterial communication | Bassler and Greenberg W1–W3/P1–P3; biofilm and review papers supporting |
| Photocatalytic water splitting | Fujishima W1/P1, W2 supporting; Domen W1–W3/P1–P3 |
| Proton-coupled electron transfer | Hammes-Schiffer W1–W2 supporting; Meyer W1, W3/P1 supporting |
| Nuclear receptors | Evans W1, W3/P1–P3 |

Every non-unit secondary adjustment is listed below. Recognition cascades are correlated and are not stacked as independent signals. Unit factors mean no incremental adjustment, not evidence that an option lacks recognition ([factor ledger](sandbox:/mnt/data/forecast_model.md)).

- Sequencing-by-synthesis: 1.60. The official Wolf record recognizes Balasubramanian, Klenerman, and Mayer; an institutional announcement dated October 4, 2026 establishes availability before the cutoff. The May 13, 2026 Asturias announcement recognizes the same platform and trio. Combined DNA receives a smaller 1.25 corroboration factor for its sequencing component, without removing its separate matching constraint ([Wolf record](https://wolffund.org.il/category/field/chemistry/), [dated Strasbourg announcement](https://isis.unistra.fr/en/news/pascal-mayer-laureat-du-prix-wolf-2026-de-chimie/), [Asturias announcement](https://www.fpa.es/es/area-de-comunicacion-y-prensa/notas-de-prensa/los-pioneros-en-las-tecnologias-de-nueva-generacion-para-la-secuenciacion-de-adn-premio-princesa-de-asturias-de-investigacion-cientifica-y-tecnica-2026/)).
- Perovskites: 1.25. Miyasaka's Kyoto recognition is discovery-specific. Combined solar receives 1.15 for partial corroboration of its components. Neither adjustment implies that a combined motivation is required ([official Kyoto record](https://www.kyotoprize.org/laureates/tsutomu_miyasaka-j/)).
- Monolayers: 1.20. The Kavli award validates the discovery boundary and complementary contributions. Clarivate adds limited corroboration because its citation-based evidence overlaps the profiles ([Kavli record](https://www.kavliprize.org/prizes/nanoscience/2022), [Clarivate Chemistry record](https://clarivate.com/citation-laureates/chemistry/)).
- Protein electron transfer: 1.25; base/prime editing: 1.15. Clarivate's September 17, 2026 recognition directly matches these discoveries. This does not replace missing direct evidence on Gray's card or override editing's maturity prior ([dated Clarivate announcement](https://clarivate.com/news/clarivate-reveals-citation-laureates-2026-recognizing-transformative-scientific-breakthroughs/), [discovery citations](https://clarivate.com/citation-laureates/chemistry/)).
- Proteomics: 1.35. The March 31, 2026 Gairdner grouping closely matches both the discovery and the three named leaders. Its HTML body has an inconsistent earlier-year dateline; the publication header and independently dated institutional account establish the award year ([Gairdner announcement](https://www.gairdner.org/resource-hub/2026-canada-gairdner-award-winners), [ETH confirmation](https://ethz.ch/en/news-and-events/eth-news/news/2026/03/one-of-the-most-prestigious-medical-research-awards-bestowed-on-proteomics-pioneer-ruedi-aebersold.html)).
- Pd carbon–heteroatom coupling: 1.10, for the established joint Wolf recognition of the practical amination method. Dye cells: 1.05, for longstanding, exact-discovery Millennium recognition ([MIT account](https://news.mit.edu/2019/buchwald-awarded-wolf-prize-chemistry-0116), [Millennium record](https://millenniumprize.org/winners/dye-sensitised-solar-cells/)).

The complete distributions follow. Display percentages are rounded; values below one percent remain positive. Exact profile-only values are in the linked ledger, and exact submitted values are in the JSON probability field ([complete calculations](sandbox:/mnt/data/forecast_model.md)).

| Discovery | Profiles only | Secondary factor | Submitted |
|---|---:|---:|---:|
| Sequencing-by-synthesis | 3% | 1.60 | 3% |
| Controlled radical polymerization | 4% | 1.00 | 4% |
| Solid-state perovskites | 3% | 1.25 | 3% |
| Drug/nucleic-acid delivery | 4% | 1.00 | 4% |
| Phosphoramidite synthesis | 3% | 1.00 | 3% |
| C–H functionalization | 2% | 1.00 | 2% |
| Nanopore methods | 6% | 1.00 | 6% |
| Self-assembled monolayers | 8% | 1.20 | 9% |
| Protein electron transfer | <1% | 1.25 | <1% |
| Base/prime editing | 3% | 1.15 | 3% |
| Targeted protein degradation | 3% | 1.00 | 3% |
| Ab initio molecular dynamics | 1% | 1.00 | 1% |
| Molecular chaperones | 2% | 1.00 | 2% |
| Combined dye/perovskite cells | 3% | 1.15 | 3% |
| OLEDs | 2% | 1.00 | 2% |
| DNA origami | 2% | 1.00 | 2% |
| Pd carbon–heteroatom coupling | 6% | 1.10 | 6% |
| Combined DNA synthesis/sequencing | 1% | 1.25 | 1% |
| Exchange-correlation functionals | 1% | 1.00 | 1% |
| Chemical genetics/KRAS | 3% | 1.00 | 3% |
| Genetic-code expansion | 6% | 1.00 | 6% |
| Atomic layer deposition | <1% | 1.00 | <1% |
| Carbohydrate/glycoprotein synthesis | 3% | 1.00 | 3% |
| MS-based proteomics | 7% | 1.35 | 9% |
| Dye-sensitized cells | 9% | 1.05 | 8% |
| Stable/NHC carbenes | <1% | 1.00 | <1% |
| Bacterial communication | 3% | 1.00 | 3% |
| Photocatalytic water splitting | 3% | 1.00 | 3% |
| Proton-coupled electron transfer | <1% | 1.00 | <1% |
| Nuclear receptors | 5% | 1.00 | 5% |

Proteomics earns its leading position through balanced, discovery-specific evidence. Mann and Aebersold have exceptional career-impact and textbook comparisons. All three profiles show strong invention reach. The original-method evidence matters more than the reviews: Yates's database-matching work has disruption 0.75 and Foundation 0.56; Mann's sensitive protein-analysis work has disruption 0.92; Aebersold's validation work has Foundation 0.77. The record joins measurement, identification, quantification, and reliability rather than relying on one famous investigator ([supplied proteomics evidence](sandbox:/mnt/data/supplied_evidence.md)).

Monolayers combine Whitesides's exceptional dissemination with Allara's and Nuzzo's direct surface-specific work. Whitesides's invention and textbook comparisons reach the top of the historical cohort, while the microstamping patent has 1,040 later patent citations. Allara's comparative monolayer work has disruption 0.95. Microfluidics and unrelated printing are excluded, so broad eminence does not stand in for the named discovery ([supplied SAM evidence](sandbox:/mnt/data/supplied_evidence.md)).

Dye cells have the strongest profile-only weight. Grätzel's impact, technological translation, and textbook comparisons are unusually strong. The decisive dye-cell work has disruption 0.76, Foundation 0.36, and substantial invention and book uptake. Its mature realization fits the waiting prior. The perovskite paper contributes nothing to this narrower arm ([supplied dye-cell evidence](sandbox:/mnt/data/supplied_evidence.md)).

Nanopores receive substantial weight from Branton's exceptional impact comparisons, the directly relevant translocation and engineered-pore work, and the concentrated patent record. The shared membrane-channel paper is cited by 573 inventions; the foundational shared patent has 430 later patent citations. Structure and pore fabrication support the enabling chain without being mistaken for separate sequencing breakthroughs ([supplied nanopore evidence](sandbox:/mnt/data/supplied_evidence.md)).

Pd carbon–heteroatom coupling combines strong translation and textbook comparisons with a coherent practical-method record. Buchwald's invention reach exceeds 98% of the reference laureates; Hartwig's exceeds 92%. The amination and etherification evidence is retained, while Suzuki carbon–carbon coupling and C–H borylation are excluded ([supplied coupling evidence](sandbox:/mnt/data/supplied_evidence.md)).

Genetic-code expansion combines Schultz's exceptional translation and textbook reach with Chin's directly relevant incorporation work, which has disruption 0.93 and Foundation 0.64. The patent portfolio is unusually concentrated on the named discovery. Unrelated nanocrystal and circadian papers do not inflate its discovery grade ([supplied genetic-code evidence](sandbox:/mnt/data/supplied_evidence.md)).

Nuclear receptors also exceed five percent before secondary normalization. Evans has strong impact, invention, patent, and textbook comparisons, with 110 patents reported as discovery-related. The receptor and ligand works count; the fibroblast paper does not. The publication-window anomaly reduces career support, not the existence of the identifiable receptor discoveries ([supplied receptor evidence](sandbox:/mnt/data/supplied_evidence.md)).

My conditional laureate predictions for the leading discoveries are:

- Proteomics: John R. Yates III, Matthias Mann, and Ruedi Aebersold. This is a field-building interpretation, not a claim that they alone authored every component method. The original database-search, protein-analysis, and statistical-validation papers establish complementary research programs ([SEQUEST paper](https://doi.org/10.1016/1044-0305(94)80016-2), [protein-analysis paper](https://doi.org/10.1021/ac950914h), [validation paper](https://doi.org/10.1021/ac025747h)).
- Monolayers: David Allara, Ralph Nuzzo, and George Whitesides, for a motivation joining metal-surface assembly, characterization, and usable patterning. Nuzzo and Allara authored the original gold-surface realization; Whitesides coauthored functional-film development and the original microcontact-printing work. Jacob Sagiv is the major alternative if oxide-bound monolayers receive central emphasis ([gold-surface paper](https://doi.org/10.1021/ja00351a063), [functional-film paper](https://doi.org/10.1021/ja00183a049), [printing paper](https://doi.org/10.1063/1.110628), [Kavli attribution](https://www.kavliprize.org/prizes/nanoscience/2022)).
- Dye cells: Brian O'Regan and Michael Grätzel. They jointly authored the decisive paper published October 24, 1991. A two-person award still matches the option naming Grätzel alone ([original paper](https://www.nature.com/articles/353737a0)).

## What's non-obvious
The fresh recognition cascade is real, but it does not dominate the profile-constrained ranking. Sequencing receives the largest secondary increase and still remains below the leading mature portfolios. Conversely, a prior award in a neighboring area is not a veto: the earlier Chemistry recognition concerned soft ionization, not the full proteomics identification-and-quantification platform. I apply no automatic overlap penalty ([factor calculation](sandbox:/mnt/data/forecast_model.md), [official earlier motivation](https://www.nobelprize.org/prizes/chemistry/2002/summary/)).

Discovery wording matters more than the option's names. Mayer's enabling amplification work strengthens the expected sequencing laureate set, but does not turn a sequencing motivation into an award for chemical DNA synthesis. SAM attribution has a genuine four-person problem, whereas this question still offers one discovery arm. The committee can also recognize a tool's realization and leadership without following first-author order mechanically. These distinctions prevent double-counting broad options and penalizing discoveries for omitted names ([resolution rules](sandbox:/mnt/data/supplied_evidence.md), [sequencing attribution](https://www.fpa.es/es/area-de-comunicacion-y-prensa/notas-de-prensa/los-pioneros-en-las-tecnologias-de-nueva-generacion-para-la-secuenciacion-de-adn-premio-princesa-de-asturias-de-investigacion-cientifica-y-tecnica-2026/), [SAM attribution](https://www.kavliprize.org/prizes/nanoscience/2022)).

## Uncertainties
The largest gap is the committee's actual shortlist and credit judgment. Nomination information and associated investigations remain confidential for 50 years. Public recognition does not reveal the selection decision ([official selection process](https://www.nobelprize.org/nomination/chemistry/)). The profile grades, probability scale, and motivation-matching factors therefore remain judgment calls. A small lead between the top options is not a robust separation.

The supplied cards also contain attribution contamination and only a short defining-work list. Gray's low probability reflects weak direct evidence on his card, not proof that protein electron transfer lacks a Nobel case. A cleaned identity-linked record, fuller landmark-paper coverage, and discovery-level adoption histories would sharpen the ranking. In 50,000 score-perturbation simulations, the leading options' probability ranges were roughly 6–12%; these are model-sensitivity ranges, not validated confidence intervals ([data limitations](sandbox:/mnt/data/supplied_evidence.md), [sensitivity calculation](sandbox:/mnt/data/forecast_model.md)). The decimal precision in the submitted vector preserves normalization and reproducibility, not knowledge of the committee's choice to that precision.