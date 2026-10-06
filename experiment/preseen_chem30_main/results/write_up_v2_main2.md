## TL;DR
Mass-spectrometry-based proteomics leads my forecast with a 9% conditional probability ([calculation](#evidence)). Nanopore analysis and sequencing follows at 7%, and self-assembled monolayers at 6% ([calculation](#evidence)). The top three account for 22% of the distribution, so the answer is a broad forecast rather than a confident single winner ([calculation](#evidence)).

## Context
At the supplied cutoff of 6 October 2026, 22:19 UTC, the Chemistry announcement remains in the future. The official schedule places it on 7 October at 11:45 CEST at the earliest, equivalent to 09:45 UTC ([client timing](#context); [official schedule](https://www.nobelprize.org/prizes/about/prize-announcement-dates/?trk=public_post_comment-text)). These probabilities are conditional on the official motivation matching a listed discovery. They exclude annulment, match discoveries rather than exact recipients, and follow the larger-share, first-mentioned and specificity rules in the question ([client resolution criteria](#context)).

The supplied profiles are the main evidence. External research checks discovery boundaries, authorship and selected recognition records; it does not replace the profile measurements. Links labelled “client evidence” below refer to the stipulated material in your question, not to an independently retrieved public dataset. The supplied Medicine and Physics outcomes are treated as premises and used only to refine the treatment of decisive realizations, credit and recognition cascades ([client evidence](#evidence)).

## Evidence
The historical backbone is the supplied timing reference class: the 26 annual Chemistry decisions from 2000–2025. Approximately 15–20% had discovery-to-prize lags of ten years or less, roughly a third had lags of 10–25 years, and about 45% exceeded 25 years. The median was roughly 25 years. The fast cases were rapidly adopted structures and enabling tools, not simply highly cited recent research ([client timing evidence](#evidence)). I therefore favor established realizations, but leave room for fast awards when adoption resembles the supplied precedents. Timing enters the ranking once.

The profile reference population contains 61 Chemistry laureates from 2000–2025, measured before their awards. The candidate cards use the January 2026 OpenAlex snapshot, the 31 December 2025 PatentsView vintage and the supplied patent-to-paper links. Research works and own patent grants end in 2021; their first observation years are the individual windows printed on the cards. Impact measures are completed five-year citation percentiles. Inventions, patents and book reach are cumulative counts, not annual rates. All profile comparisons below retain these vintages ([client definitions and profiles](#evidence)).

Translation is read against the supplied reference lines and historical medians of about 200 citing inventions and six own US patents. A large invention count is evidence of translation, but does not create a proportionate probability advantage. Book reach supports durable influence. Collaboration has little weight, and collaboration size receives no separate bonus ([client evidence and modelling assumptions](#evidence)).

The scoring rule gives career impact and discovery evidence three-quarters of the feature weight:

$$
S_i=0.35C_i+0.40D_i+0.13T_i+0.10B_i+0.02K_i.
$$

Here, C is career impact, D is discovery-relevant evidence, T is translation, B is book reach and K is a bounded collaboration indicator. These weights are forecasting judgments. The final score inputs are disclosed in the table below ([model specification](#evidence)).

For each person, career impact combines the supplied past-laureate comparison ranks with weights of 0.40 for median impact and 0.30 each for the top-10% and top-1% work shares. The person’s attribution factor multiplies that score. An option receives 60% of its strongest adjusted person score plus 40% of the adjusted mean. This does not reward an option merely for naming more people. A single-person option receives no headcount penalty, and a person appearing in two options contributes fully to both ([aggregation assumptions](#evidence)).

Translation and book reach are bounded option-level assessments of the supplied reference lines. The strongest named profile carries substantial weight, with the others providing corroboration. Their quality multiplier is likewise 60% of the highest attribution factor plus 40% of the mean. Collaboration uses the same aggregation on an indicator for a plausible laureate co-author, rather than the number of co-authors. The suspect Rothemund–Fischer and Hammes-Schiffer–Bertozzi entries receive no collaboration credit ([client profiles and aggregation assumptions](#evidence)).

Discovery evidence is built from distinct, relevant card records. Shared papers and patents are counted once. For papers, the item score combines impact, foundation share and logarithmically scaled invention and book citations, with weights of 0.70, 0.10, 0.12 and 0.08. Missing foundation shares receive a neutral 0.50. Original demonstrations receive full realization weight; reviews receive 0.75. For post-2018 papers, only the invention- and book-citation terms receive a 0.85 opportunity adjustment; completed impact windows remain unchanged. Patent scores run from 0.55 to 1.00 using logarithmically scaled later-patent citations. Discovery score D is 60% of the strongest eligible item plus 40% of the mean of the strongest three, or all items when fewer exist. The scaling anchors are 5,089 paper-citing inventions, 71 citing books and 1,218 later patent citations, taken from the supplied range. Disruption gets no separate bonus ([client evidence and scoring assumptions](#evidence)).

This rule lets patents supply decisive evidence for inventions such as automated DNA synthesis and atomic layer deposition. It also lets a theoretical discovery score strongly without patents. Gray’s assay patent receives a 0.75 relevance factor because it supports an application but does not itself establish the specific protein-electron-transfer discovery ([client discovery records](#evidence)).

All profile qualifications are explicit. The following factors apply to career-derived evidence; clearly identified discovery records remain intact ([client attribution and sample-size evidence](#evidence)):

- **0.90:** Grätzel, Yates, Hartl, Balasubramanian, Hao Yan, Evans, Roberto Car, Bergman and Chin. The flags are the unusual printed affiliations or implausibly early publication windows on their respective cards.
- **0.80:** Gray, Herrmann and Bertrand, whose historical publication windows or co-author entries create stronger attribution warnings.
- **0.75:** Rothemund, combining the anomalous publication window and historical co-author entry.
- **0.85:** Hammes-Schiffer for the collaboration-attribution anomaly; Van Slyke for the small sample of 15 research works.
- **0.95:** Mann for the early publication-window warning; Liu for the unusual printed hospital affiliation.
- Every other person receives **1.00**. Suntola’s 50 works and Rothemund’s 53 do not trigger an additional below-50 sample discount.

These are uncertainty qualifications, not reconstructed bibliometrics. Missing landmark works are not treated as proof of weak science, and no profile is penalized merely because it lacks patents. The post-2018 adjustment described above applies to the relevant prime-editing and perovskite records, not to their completed impact measures ([client evidence and qualification rules](#evidence)).

The discovery-relevance ledger is below. Abbreviated descriptions identify the supplied card records. “Listed patents” means the discovery-linked patent entries on the named cards, not all career patents. This ledger also records the main exclusions ([client discovery cards](#evidence)).

| Discovery | Relevant works and patents used |
|---|---|
| Sequencing-by-synthesis | The reversible-terminator whole-genome paper; US 6,833,246, 6,787,308 and 7,057,026. G-quadruplex and protein-aggregation papers are excluded. |
| Controlled radical polymerization | The two living-radical/ATRP realizations and directly related reviews; Matyjaszewski’s three listed ATRP patents and Sawamoto’s metal-removal patent. The broad sequence-controlled-polymer review is not a separate realization. |
| Solid-state perovskites | The shared meso-superstructured-cell paper, Snaith’s diffusion-length and vapor-deposition papers, Park’s sensitized-cell and reproducibility papers, and the qualified recent reviews; Snaith’s and Park’s listed perovskite patents. Miyasaka’s battery paper is excluded. |
| Polymeric/lipid delivery | Vesicle extrusion and the delivery reviews; Cullis’s three listed encapsulation patents. |
| Phosphoramidite synthesis | The phosphoramidite realization and synthesis-machine exposition; Caruthers’s three listed synthesis patents. RNA-duplex thermodynamics is excluded. |
| C–H functionalization | Hartwig’s C–B activation work, Bergman’s activation and directed-reaction works; US 6,451,937 and Bergman’s three listed alkane/iridium patents. Amination records are reserved for carbon–heteroatom coupling. |
| Nanopores | Polynucleotide translocation, pore structure, engineered sequence-specific detection, ion-beam pore fabrication and directly related reviews; the listed pore, sensing and polymer-characterization patents on the three cards, deduplicated. |
| Self-assembled monolayers | Disulfide adsorption, thiol-film assembly, structural/wetting studies and the SAM review; US 4,690,715, 4,579,752, 6,518,168, 5,512,131 and 5,620,850. Microfluidics and 4D printing are excluded. |
| Protein electron transfer | US 7,105,310 as qualified supporting evidence. The solar-fuel, vanadyl and cobaloxime papers do not directly establish the named discovery. |
| Base/prime editing | All three listed editing papers and editor patents, with the stated citation-opportunity treatment for prime editing. |
| Targeted degradation | The original PROTAC paper, catalytic small-molecule realization and induced-degradation review; US 7,041,298, 10,730,862 and 10,730,870. General ligase reviews are not separate PROTAC realizations. |
| Ab initio molecular dynamics | The unified molecular-dynamics/DFT paper and Quantum ESPRESSO implementation paper. Classical variable-cell dynamics, thermostat sampling and the graphene application are excluded from discovery evidence. |
| Chaperones | Folding-machine reviews and the GroEL/GroEL–GroES structures; US 5,776,724, 5,302,518, 6,214,606 and 5,428,131. The vaccine patent is excluded. |
| Joint dye/perovskite cells | The dye-cell records, Grätzel’s sequential perovskite deposition and relevant Snaith/Miyasaka records; the dye-cell and Snaith device patents. Park-only card evidence is not imported. |
| OLEDs | Van Slyke’s diode, doping and stability papers, Tang’s injection and tandem-device papers, and the listed Van Slyke electroluminescence patents, including the shared Tang patent. The photovoltaic paper is excluded. |
| DNA origami | Algorithmic assembly, origami templating, three-dimensional assembly, design software, DNA arrays, the nanorobot application and structural-DNA reviews; the listed nanostructure, nanoarray, assembly and barcode patents. SAT computation is excluded. |
| Pd carbon–heteroatom formation | Arylamine/ether chemistry, practical C–N catalyst development, amination/thioetherification and applications; the two Hartwig amination patents and three Buchwald catalyst patents. Suzuki C–C coupling is excluded. |
| DNA synthesis plus sequencing | The union of the two narrower DNA evidence sets, deduplicated. |
| DFT functionals | All three listed Perdew correlation/GGA papers. |
| Kinase chemical genetics/KRAS | The three listed kinase and cancer-inhibition patents. The displayed top-paper set does not directly establish the named discovery; the SARS-CoV-2 paper is excluded. |
| Genetic-code expansion | Chin’s azido-amino-acid realization and incorporation/reprogramming reviews, Schultz’s new-chemistries review, and the listed incorporation/orthogonal-tRNA/eukaryotic-expansion patents. Nanocrystal assembly and circadian transcription are excluded. |
| Atomic layer deposition | The listed atomic-layer growth papers and US 4,058,430, 4,413,022 and 4,389,973. |
| Carbohydrate/glycoprotein synthesis | The enzyme-synthesis exposition and all three listed synthesis patents. HIV neutralization and biological glycosphingolipid recognition are excluded. |
| Proteomics | Spectral database matching, MudPIT, gel sequencing, MaxQuant, sample preparation, statistical peptide/protein identification and the proteomics review; the listed database-search, labeling, electrospray and quantitative-analysis patents. Microglial learning is excluded. |
| Dye-sensitized cells | The original dye-cell realization and photoelectrochemical review; all three listed photoelectrochemical-cell patents. Perovskite deposition is excluded. |
| Stable/NHC carbenes | Stable-carbene isolation/stabilization, cyclic-carbene realization and direct reviews; the listed carbene, precursor and metal–NHC patents used as direct or enabling evidence. The broad CO2 review is excluded. |
| Bacterial communication | The signaling/biofilm realization, Lux-system and quorum-sensing reviews; all listed autoinducer, signaling and bacterial-regulation patents. |
| Photocatalytic water splitting | Semiconductor water photolysis, hydrogen-producing photocatalysts and relevant reviews; US 6,387,844 and Domen’s three listed photocatalyst patents. Architectural/superhydrophilic applications are excluded. |
| Proton-coupled electron transfer | Proton-transfer quantum dynamics, enzyme-catalysis context and the two PCET reviews; US 8,524,903 as supporting catalysis evidence. Q-Chem and generic mixed-phosphine chemistry are excluded. |
| Nuclear receptors | The receptor-superfamily and PPAR-ligand records; all three listed receptor patents. The fibroblast framework is excluded. |

Maturity factors M reflect the realization clocks in that ledger. Established older methods generally receive 1.15; intermediate-age realizations generally receive 0.95; mixed foundation-and-realization histories receive intermediate values. Base/prime editing receives 0.55 because its listed realizations are only seven to ten years old at the forecast date. Its strong adoption evidence keeps it competitive. There is no second maturity discount after this step ([client timing prior and model assumptions](#evidence)).

The composite solar and DNA options receive specificity factors X of 0.25 and 0.35 respectively. Their named people retain full career evidence, but a joint motivation is a narrower resolution path than an award for either constituent discovery alone. A recipient’s identity does not override the motivation’s discovery wording ([client resolution criteria and scope assumptions](#context)).

For profile-only weights, I calculate exp(8S) times M and X. For submitted weights, I also multiply by the secondary factor A. Both sets then receive the same common calibration exponent, 1/1.20, and are normalized. No uniform floor is mixed in. Component scores are frozen to three decimals; S below is the resulting arithmetic score ([model specification](#evidence)).

Every non-neutral secondary adjustment is listed here. Overlapping awards are treated as one corroborating signal, not multiplied as independent evidence:

- Sequencing-by-synthesis: **A = 1.50**. The sequencing-specific recognition spans the 2022 Breakthrough record and the Princess of Asturias decision dated 13 May 2026. The latter credits Balasubramanian, Klenerman and Mayer for widely used sequencing technology ([Breakthrough](https://breakthroughprize.org/Laureates/2/L3918); [Asturias jury decision](https://www.fpa.es/es/premios-princesa-de-asturias/premiados/2026-david-klenerman-shankar-balasubramanian-y-pascal-mayer/?texto=acta)).
- Proteomics: A = 1.25. The Gairdner release dated 31 March 2026 recognizes Yates, Aebersold and Mann together for scalable, quantitative and computational proteomics. The official PDF confirms the date despite a year typo in the HTML release ([official release](https://www.gairdner.org/docs/default-source/insight-pdf%27s/en-media-release---2026-canada-gairdner-awards53ba52c7-9fba-4f3c-8b89-e828356c35c0.pdf?sfvrsn=d706958_1)).
- Solid-state perovskites: A = 1.30. The Kyoto announcement of 19 June 2026 directly recognizes Miyasaka’s perovskite-cell contribution ([announcement](https://www.kyotoprize.org/); [citation](https://www.kyotoprize.org/en/laureates/tsutomu_miyasaka/)).
- Targeted degradation: A = 1.20. FDA approval of the heterobifunctional degrader vepdegestrant on 1 May 2026 provides concrete therapeutic translation ([FDA](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-vepdegestrant-er-positive-her2-negative-esr1-mutated-advanced-or-metastatic-breast)).
- Genetic-code expansion: A = 1.15. The Welch Foundation’s May 2025 announcement explicitly recognizes Schultz’s expansion of the genetic alphabet ([Welch](https://welch1.org/news-reports/news/welch-award-2025)).
- Pd carbon–heteroatom formation: A = 1.15. The 2019 Wolf citation directly matches Buchwald and Hartwig’s catalyst contribution ([Wolf](https://wolffund.org.il/category/field/page/7/)).
- Controlled radical polymerization: A = 1.10; OLEDs: A = 1.05. The institutional announcement dated 17 February 2011 documents the Wolf recognition of Matyjaszewski and Tang, with the polymer contribution described more specifically ([Carnegie Mellon](https://www.cmu.edu/news/stories/archives/2011/february/feb17_wolfprize.html)).
- Phosphoramidite synthesis: A = 1.10. Caruthers’s 2023 Merkin recognition directly addresses automated DNA synthesis ([Merkin](https://merkinprize.org/2023-prize-recipient)).
- Chaperones: A = 1.10. The 2011 Lasker record corroborates the Hartl–Horwich folding discovery and its credit set ([Lasker](https://laskerfoundation.org/winners/chaperone-assisted-protein-folding/)).
- Both composite options: A = 1.05. Recognition supports one constituent branch, not a demonstrated joint motivation ([Asturias](https://www.fpa.es/es/premios-princesa-de-asturias/premiados/2026-david-klenerman-shankar-balasubramanian-y-pascal-mayer/?texto=acta); [Kyoto](https://www.kyotoprize.org/en/laureates/tsutomu_miyasaka/)).
- Every other option: A = 1.00. No additional adjustment is made for nationality, an area being “due,” audience polls, supplied market figures or candidate-list frequency ([model boundary](#evidence)).

The full profile-only and submitted distributions follow. Percentages are rounded for reading; the probability object contains the exact submitted arithmetic. All scores and factors are modelling judgments derived as described above, not additional empirical measurements ([calculation](#evidence)).

| Discovery | S | M | X | A | Profiles | Submitted |
|---|---:|---:|---:|---:|---:|---:|
| Sequencing-by-synthesis | 0.76558 | 0.95 | 1.00 | 1.50 | 3% | 4% |
| Controlled radical polymerization | 0.78155 | 1.15 | 1.00 | 1.10 | 4% | 4% |
| Solid-state perovskites | 0.82300 | 0.95 | 1.00 | 1.30 | 4% | 5% |
| Polymeric/lipid delivery | 0.73360 | 1.10 | 1.00 | 1.00 | 3% | 3% |
| Phosphoramidite DNA synthesis | 0.66520 | 1.15 | 1.00 | 1.10 | 2% | 2% |
| C–H functionalization | 0.72187 | 1.05 | 1.00 | 1.00 | 2% | 2% |
| Nanopore analysis/sequencing | 0.87600 | 1.10 | 1.00 | 1.00 | 7% | 7% |
| Self-assembled monolayers | 0.86556 | 1.15 | 1.00 | 1.00 | 7% | 6% |
| Protein electron transfer | 0.45618 | 1.05 | 1.00 | 1.00 | <1% | <1% |
| Base/prime editing | 0.87503 | 0.55 | 1.00 | 1.00 | 4% | 4% |
| Targeted protein degradation | 0.78385 | 1.00 | 1.00 | 1.20 | 4% | 4% |
| Ab initio molecular dynamics | 0.76338 | 1.15 | 1.00 | 1.00 | 3% | 3% |
| Molecular chaperones | 0.76165 | 1.15 | 1.00 | 1.10 | 3% | 4% |
| Dye cells + perovskites | 0.86957 | 1.05 | 0.25 | 1.05 | 2% | 2% |
| OLEDs | 0.66774 | 1.15 | 1.00 | 1.05 | 2% | 2% |
| DNA origami | 0.73071 | 0.95 | 1.00 | 1.00 | 2% | 2% |
| Pd carbon–heteroatom formation | 0.79520 | 1.15 | 1.00 | 1.15 | 4% | 5% |
| DNA synthesis + sequencing | 0.76172 | 1.05 | 0.35 | 1.05 | 1% | 1% |
| DFT functionals | 0.78195 | 1.15 | 1.00 | 1.00 | 4% | 4% |
| Kinase chemical genetics/KRAS | 0.75950 | 0.95 | 1.00 | 1.00 | 3% | 3% |
| Genetic-code expansion | 0.83645 | 0.95 | 1.00 | 1.15 | 5% | 5% |
| Atomic layer deposition | 0.51690 | 1.15 | 1.00 | 1.00 | <1% | <1% |
| Carbohydrate/glycoprotein synthesis | 0.65740 | 1.05 | 1.00 | 1.00 | 2% | 1% |
| Mass-spectrometry proteomics | 0.87888 | 1.15 | 1.00 | 1.25 | 8% | 9% |
| Dye-sensitized solar cells | 0.83480 | 1.15 | 1.00 | 1.00 | 6% | 5% |
| Stable/NHC carbenes | 0.58033 | 1.10 | 1.00 | 1.00 | <1% | <1% |
| Bacterial chemical communication | 0.79350 | 1.15 | 1.00 | 1.00 | 4% | 4% |
| Photocatalytic water splitting | 0.66950 | 1.05 | 1.00 | 1.00 | 2% | 2% |
| Proton-coupled electron transfer | 0.57507 | 1.05 | 1.00 | 1.00 | <1% | <1% |
| Nuclear receptor superfamily | 0.83931 | 1.15 | 1.00 | 1.00 | 6% | 5% |

Seven submitted options exceed 5% before display rounding. Their profile drivers are:

- Proteomics: Mann’s 797-work record covers 1972–2021; Aebersold’s 788 covers 1982–2021; Yates’s 1,014 covers the anomalous 1945–2021 window. Mann and Aebersold combine exceptional impact comparisons with book reach above the reference cohort. The relevant records span identification, quantitative measurement, sample preparation and statistical reliability, rather than one famous review ([client profiles](#evidence)).
- Nanopores: Branton’s 165-work record covers 1961–2021 and exceeds 93%, 92% and 97% of past laureates on the three career-impact comparisons. Bayley and Deamer add complementary pore-engineering and translocation evidence. The early translocation and later sequence-sensitive detection are distinct realizations ([client profiles](#evidence); [original translocation paper](https://pmc.ncbi.nlm.nih.gov/articles/19421/); [engineered detection paper](https://doi.org/10.1038/90236)).
- Self-assembled monolayers: Whitesides’s 1,505-work record covers 1962–2021, with exceptional invention and book reach. Allara and Nuzzo supply directly relevant early surface-assembly evidence. The microstamping patent’s supplied 1,040 later-patent citations strengthen realization evidence; its claims explicitly form patterned SAMs ([client profiles](#evidence); [patent](https://patents.google.com/patent/US5512131A/en)).
- Nuclear receptors: Evans’s 646-work record has an anomalous 1933–2021 window, already qualified. His impact comparisons, receptor-superfamily and ligand records, and directly linked receptor patents together produce a strong mature-discovery score. The unrelated fibroblast paper contributes nothing to discovery evidence ([client profile](#evidence)).
- Dye-sensitized cells: Grätzel’s 1,465-work record covers 1973–2021. Strong impact comparisons, exceptional book reach, a clear original realization and direct cell patents support this narrow option without importing perovskite evidence ([client profile](#evidence); [original dye-cell paper](https://doi.org/10.1038/353737a0)).
- Solid-state perovskites: Snaith’s 481-work record covers 2000–2021 and exceeds 95% and 97% of past laureates on median-impact and top-1% comparisons. The shared cell realization and subsequent transport/device papers give the option a direct discovery-to-platform chain. Its younger maturity is already reflected in M ([client profiles](#evidence)).
- Genetic-code expansion: Schultz’s 678-work record covers 1980–2021; Chin’s 136 covers the qualified 1969–2021 window. Chin supplies strong career-impact and direct incorporation evidence. Schultz supplies exceptional translation and extensive discovery-linked patent evidence. Unrelated nanocrystal and circadian papers are excluded ([client profiles](#evidence)).

For the top three discoveries, my expected laureate sets are credit judgments, not nomination claims:

1. Proteomics: John R. Yates III, Matthias Mann and Ruedi Aebersold. The paper record supports complementary research programs. Eng and McCormack coauthored the database-search realization; Shevchenko, Wilm and Vorm coauthored Mann’s gel-analysis realization; Keller and colleagues coauthored the statistical identification method. A narrower motivation could therefore change the recipients ([database-search paper](https://doi.org/10.1016/1044-0305(94)80016-2); [gel-analysis paper](https://doi.org/10.1021/ac950914h); [statistical-method paper](https://tools.proteomecenter.org/publications/Keller.AnalChem.02.pdf)).
2. Nanopores: Hagan Bayley, David W. Deamer and Daniel Branton. The translocation paper names Kasianowicz, Brandin, Branton and Deamer; the engineered detection paper names Howorka, Cheley and Bayley. Kasianowicz is a serious substitution possibility, especially under a narrowly framed early-experiment motivation ([translocation paper](https://pmc.ncbi.nlm.nih.gov/articles/19421/); [engineered detection paper](https://doi.org/10.1038/90236)).
3. Self-assembled monolayers: David L. Allara, Ralph G. Nuzzo and George M. Whitesides. The founding adsorption paper credits Nuzzo and Allara; the later systematic assembly paper connects Nuzzo and Whitesides to development of the platform. A narrower founding-discovery motivation could omit Whitesides ([adsorption paper](https://doi.org/10.1021/ja00351a063); [assembly paper](https://doi.org/10.1021/ja00183a049)).

## What's non-obvious
The option labels hide a resolution trap. Sequencing-by-synthesis is not chemical oligonucleotide synthesis, and a perovskite prize is not automatically a joint dye/perovskite prize. Adding Caruthers or Grätzel to a recipient list would not move a specifically worded motivation into the composite arm. Conversely, names omitted from an option can receive the prize without defeating that option. The specificity factors reflect these narrower resolution paths, not weaker careers ([client resolution criteria](#context)).

Prior recognition of an enabling technology is not a blanket veto on a distinct downstream discovery. The mass-spectrometry portion of the 2002 Chemistry prize recognized soft-ionization methods; the proteomics option concerns scalable identification, quantification and interpretation. Likewise, microcontact printing is genuinely linked to SAM realization—the patent claims say so—but does not by itself settle founding credit. Nanopore translocation and sequence-specific detection also should not be inflated into demonstrations of general de novo sequencing. These distinctions preserve strong platform evidence without overstating what the decisive papers achieved ([2002 motivation](https://www.nobelprize.org/prizes/chemistry/2002/summary/?mod=article_inline); [SAM patent](https://patents.google.com/patent/US5512131A/en); [nanopore paper](https://pmc.ncbi.nlm.nih.gov/articles/19421/); [sequence-sensitive detection](https://doi.org/10.1038/90236)).

## Uncertainties
The largest gap is private committee evidence. The profiles, papers and recognition records do not reveal nominations, deliberations or the final motivation’s wording. Authorship verifies participation, but does not fully separate conception, experiment and program leadership. Historical contribution records and reliable author-level disambiguation would most improve the forecast, especially for the cards with implausible windows and for discoveries whose key realization is absent from the displayed works ([client profile limitations](#evidence)).

I tested 81 specifications by varying the career/discovery balance, score concentration, common calibration and maturity strength. Proteomics remained first throughout; its probability ranged from 6% to 12%. Nanopores ranged from 5% to 9%, and SAMs from 5% to 8%. These are model-sensitivity ranges, not statistical confidence intervals, and they do not cover all uncertainty in relevance coding or committee choice ([sensitivity calculation](#uncertainties)).

The submitted decimal precision preserves normalization and reproducible arithmetic. It is not decimal-level confidence in the committee’s decision. The supplied Medicine and Physics outcomes support decisive-realization credit and restraint toward fresh recognition cascades; they provide no evidence that a particular chemistry area is due ([client reference outcomes](#evidence)).