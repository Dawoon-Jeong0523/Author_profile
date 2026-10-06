## TL;DR
Mass-spectrometry-based proteomics leads at 9%, followed by dye-sensitized solar cells at 9% and nanopore methods at 6% ([calculation](#model)). Together, these discoveries account for 25% of the conditional probability, so the ranking does not support a strong favorite ([calculation](#model)). This distribution applies only if the official motivation matches a listed discovery; it assigns no probability to annulment ([client resolution rules](#client-profiles)).

## Context
The information cutoff is October 6, 2026, at 18:44 UTC. The Chemistry announcement is scheduled for October 7, 2026, no earlier than 11:45 CEST, or 09:45 UTC—about fifteen hours after the cutoff ([official schedule](https://www.nobelprize.org/prizes/about/prize-announcement-dates/)). The forecast concerns that announcement, not whether the underlying discoveries have already occurred.

The supplied profiles determine the main ranking. The supplied Medicine and Physics outcomes are accepted as scenario premises and used only to refine discovery, realization, and credit judgments. Outside recognition receives bounded secondary adjustments. Neither market prices nor public probability aggregates enter the calculation ([client premises and method](#client-profiles)).

## Evidence
<a id="client-timing"></a>
The historical backbone is the supplied reference class of all 26 annual Chemistry prizes from 2000 through 2025. Its approximate lag distribution puts 15–20% within ten years of the decisive realization, about one-third at ten to twenty-five years, and about 45% beyond twenty-five years; the median is roughly twenty-five years. The short-lag precedents were rapidly adopted structures and tools, not simply discoveries with recent publicity ([client timing evidence](#client-timing)). I use this as a maturity prior, not an annual award hazard: the number of still-unawarded discoveries in each age group is unknown.

<a id="client-profiles"></a>
The primary dataset is the client-supplied profile collection: 63 distinct people across 71 option-person positions, with individual samples ranging from 15 to 1,505 research works. Works and owned-patent grants are covered through 2021; the stated vintages are OpenAlex January 2026 and PatentsView December 31, 2025, with Reliance on Science patent-to-paper links. The historical comparison group contains 61 Chemistry laureates from 2000–2025, measured before their respective awards. Impact figures are completed five-year, publication-year-and-field percentiles. Book and patent figures are counts with separate historical-reference ranks ([client profiles](#client-profiles)). These internal links identify supplied premises and calculations, not independent public verification.

The supplied Medicine and Physics outcomes favor a specific discovery paired with its enabling realization. They also support crediting decisive authors or instrument leaders without requiring three laureates, and warn against treating a fresh recognition cascade as decisive. I apply those lessons through the discovery score and aggregation rule, not through a chemistry-area rotation adjustment ([client calibration premises](#client-profiles)).

I checked three decision-relevant threads: whether prominent papers were original demonstrations or reviews; whether broad options survive the specificity rule; and whether outside recognition corroborates the same discovery. The paper audit confirmed complementary original methods behind proteomics, separated the original dye-cell demonstration from its later review, and showed that the early nanopore experiments established translocation and sequence-specific sensing rather than unrestricted DNA sequencing ([proteomics methods](https://www.nature.com/articles/nbt0301_242), [dye-cell demonstration](https://www.nature.com/articles/353737a0), [engineered nanopores](https://www.nature.com/articles/nbt0701_636)).

<a id="model"></a>
The scoring model is judgmental and reproducible, not statistically fitted. For each person, career impact is the weighted mean of the supplied historical-reference ranks: 0.40 for median impact, 0.30 for the top-ten-percent share, and 0.30 for the top-one-percent share. Reliability factor r shrinks this score toward the reference midpoint: adjusted career impact equals 0.50 plus r times the original score minus 0.50. Within an option, career score C equals 0.65 times the strongest adjusted score plus 0.35 times the mean. A singleton receives its full score. A person named in two options contributes fully to both ([model inputs](#model)).

Discovery score D is an elicited assessment of the deduplicated relevant-work set: direct realization, completed impact, and coherent enabling advances dominate; reviews support field reach but do not substitute for demonstrations. B is an elicited supporting score for book reach, and T is a minor score for technological translation, both read against the supplied historical-reference lines. Their exact judgment inputs appear below. I neither sum careers nor award a mechanical bonus for more people or more papers. Collaboration size and disruption receive no separate numerical bonus. The supplied historical medians of about 200 citing inventions and six owned US patents also prevent very large patent totals from becoming proportional award odds ([client profiles and model](#client-profiles)).

The combined score and probability calculation are:

$$
S_i=0.45C_i+0.45D_i+0.08B_i+0.02T_i,
\qquad W_i=\exp[9(S_i-0.50)]M_iH_i.
$$

$$
P_i^{\mathrm{profiles}}=\frac{W_i^{0.85}}{\sum_jW_j^{0.85}},
\qquad
P_i^{\mathrm{final}}=\frac{(F_iW_i)^{0.85}}{\sum_j(F_jW_j)^{0.85}}.
$$

Here M is maturity, H implements resolution specificity, and F is the secondary-evidence factor. The same 0.85 power calibration is applied after evidence weighting to every arm. No uniform floor is mixed in ([calculation](#model)).

All reliability down-weighting is explicit. Factor r = 0.90 applies to Langer, Chin, Gray, Bertrand, Bergman, Kataoka, Herrmann, Balasubramanian, Evans, Yates, Mann, Hartl, and Thompson because their reported publication windows start implausibly early. Rothemund receives r = 0.80 for the early window and the Hans Fischer attribution. Car and Yan receive r = 0.95 for affiliation anomalies. Mayer and Van Slyke receive r = 0.80 for samples of 22 and 15 works. These factors are not stacked; everyone else receives r = 1.00. Shrinkage reduces confidence in aggregate attribution rather than subtracting merit, so it can raise a below-midpoint score. Recognizable landmark papers retain their own discovery evidence. The suspect Bertozzi collaboration records supply no bonus because collaboration has no separate coefficient ([client profiles and reliability rule](#client-profiles)).

For post-2018 works, completed five-year impact remains at full weight, while their book- and patent-citation support receives factor 0.50 during score elicitation. The affected included works are Miyasaka’s 2019 review, Park’s 2020 review, Langer’s 2020 nanoparticle review, and Liu’s 2019 prime-editing paper. This is not another discovery-age penalty. No career profile is discounted merely because its three-paper list omits a landmark ([client profiles and reliability rule](#client-profiles)).

Maturity factors are 1.25 for clearly established realizations older than twenty-five years, 1.00 for intermediate-age realizations, and 0.50 for the base/prime-editing package. Delivery receives 1.15 and proton-coupled electron transfer receives 1.10 because their listed works provide mixed or incomplete first-realization chronology. Chemical genetics/KRAS receives neutral 1.00 rather than an invented discovery date. Reviews establish that a discovery existed by their publication, not that it originated then. All option-specific factors appear in the table, and the maturity prior is applied only once ([client timing and model](#client-timing)).

The two compound options receive H = 0.30; all others receive H = 1.00. A perovskite-only motivation belongs to the specific perovskite arm even if Grätzel wins. A sequencing-only motivation belongs to the sequencing arm even if Caruthers wins. Separately divided discoveries follow the larger-share or first-mentioned rule. The compound arms therefore require an integrated motivation that survives the specificity rule; their scientists’ careers are not penalized ([client resolution rules and model](#client-profiles)).

The relevance ledger below identifies exactly which supplied defining works enter D. Numbers refer to each person’s numbered works in the client profiles. Shared papers are counted once within an option. Unlisted works remain part of career evidence but supply no discovery-specific evidence ([client profiles](#client-profiles)).

| Discovery | Defining works included |
|---|---|
| Sequencing-by-synthesis | Balasubramanian 1 and Klenerman 1: the shared 2008 reversible-terminator demonstration. Mayer’s electrophoresis papers are excluded. |
| Controlled radical polymerization | Matyjaszewski 1–3; Sawamoto 1–2; Rizzardo 1–3. Original living-radical and RAFT demonstrations carry more weight than reviews. |
| Solid-state perovskites | Snaith 1–3; Miyasaka 1–2; Park 1–3. Park’s earlier sensitized-cell work is supporting evidence; the solid-state maturity anchor is 2012. |
| Drug/nucleic-acid delivery | Cullis 1–3; Langer 2–3; Kataoka 1–3. Tissue engineering is excluded. |
| Protein electron transfer | Winkler 2. Solar fuels, cobaloximes, and vanadyl electronic structure are not direct evidence for this discovery. |
| Phosphoramidite synthesis | Caruthers 1 and 3; Beaucage 1 and 3; Matteucci 1. Shared synthesis papers are deduplicated. |
| C–H functionalization | Hartwig 1; Yu 1–3; Bergman 1–3. The catalytic 2009 work is distinguished from broader reviews. |
| Nanopores | Bayley 1–3; Deamer 1–3; Branton 1–3. Pore structure, translocation, engineered recognition, and solid-state-pore methods have distinct roles. |
| Self-assembled monolayers | Allara 1–3; Nuzzo 1–2; Whitesides 2, with Whitesides 3 as partial support. Microfluidics and 4D printing are excluded. |
| Targeted degradation | Crews 1–3; Deshaies 2, with Deshaies 1 and 3 as ligase-background support. Schreiber’s listed papers do not demonstrate ligase redirection. |
| Base/prime editing | Liu 1–3: the cytosine, adenine, and prime-editing methods. |
| Ab initio molecular dynamics | Car 2 and Parrinello 3: the shared 1985 method; Car 1 provides implementation support. Classical dynamics and thermostat methods are excluded. |
| Chaperones | Horwich 1–3 and Hartl 1–3. Structural studies are separated from reviews. |
| Combined solar cells | Grätzel 1–3 plus the relevant Snaith and Miyasaka works above. Park’s profile is not added. |
| OLEDs | Van Slyke 1–3; Thompson 1–3; Tang 2–3. Tang’s photovoltaic cell is excluded. |
| DNA origami/self-assembly | Rothemund 1–2; Shih 1–3; Yan 1–3. The DNA-computing paper is excluded. |
| Pd carbon–heteroatom coupling | Buchwald 1 and 3; Hartwig 2 and 3. Suzuki carbon–carbon coupling is excluded. |
| Combined DNA methods | The shared sequencing demonstration plus Caruthers 1 and 3. |
| Exchange-correlation functionals | Perdew 1–3. |
| Chemical genetics/KRAS | None of the three listed papers directly demonstrates the named methods; D = 0.50 represents missing discovery-specific evidence, not zero scientific merit. |
| Genetic-code expansion | Schultz 3; Chin 1–3. Nanocrystal assembly and circadian transcription are excluded. |
| Atomic layer deposition | The listed deposition, precursor, and growth works of Suntola, Leskelä, and Ritala; shared papers are deduplicated. |
| Carbohydrate/glycoprotein synthesis | Wong 3 as supporting synthesis evidence. Antibody neutralization and glycosphingolipid recognition are excluded. |
| Proteomics | Yates 1–2; Mann 1–3; Aebersold 1–3. The proteomics review supports reach, while original identification, validation, preparation, and quantification methods support realization. |
| Dye-sensitized cells | Grätzel 1–2. His perovskite deposition work is excluded. |
| Stable/NHC carbenes | Arduengo 1–3; Bertrand 1–3; Herrmann 1–2. General carbon-dioxide catalysis is excluded. |
| Bacterial communication | Bassler 1–3 and Greenberg 1–3, distinguishing direct signaling experiments from field accounts. |
| Photocatalytic water splitting | Fujishima 1–2; Domen 1–3. Surface amphiphilicity is excluded. |
| Proton-coupled electron transfer | Meyer 1 and 3; Hammes-Schiffer 1 as partial theoretical support. Generic software, coordination, and enzyme-catalysis works are excluded. |
| Nuclear receptors | Evans 1 and 3. The fibroblast framework is excluded. |

Secondary adjustments are limited to the following factors; every unlisted option has F = 1.00. These are corroboration judgments, not historically estimated likelihood ratios, and correlated recognitions are not stacked ([adjustment method](#model)).

- Sequencing-by-synthesis: 1.70. The Wolf Foundation’s 2026 record recognizes Balasubramanian, Klenerman, and Mayer for scalable DNA sequencing. This corroborates the enabling platform and credit that Mayer’s publication-only profile represents poorly ([Wolf Foundation](https://wolffund.org.il/category/field/chemistry/)).
- Proteomics: 1.25. The March 31, 2026 Gairdner announcement groups Yates, Aebersold, and Mann around quantitative measurement, mass spectrometry, and computational analysis. Its erroneous body dateline is reconciled against its header and ETH’s same-day announcement; it is one award observation ([Gairdner](https://www.gairdner.org/resource-hub/2026-canada-gairdner-award-winners), [ETH Zurich](https://ethz.ch/en/news-and-events/eth-news/news/2026/03/one-of-the-most-prestigious-medical-research-awards-bestowed-on-proteomics-pioneer-ruedi-aebersold.html)).
- SAMs: 1.40. The 2022 Kavli recognition and 2026 Clarivate selection corroborate the discovery. Clarivate’s different third name does not change discovery-based resolution ([Kavli](https://www.kavliprize.org/prizes/nanoscience/2022), [Clarivate](https://clarivate.com/citation-laureates/chemistry/)).
- Protein electron transfer: 1.40. Clarivate’s 2026 selection directly matches the discovery, but does not erase the limited direct-work evidence in the supplied profiles ([Clarivate](https://clarivate.com/citation-laureates/chemistry/)).
- Base/prime editing: 1.20. The 2025 Breakthrough recognition and 2026 Clarivate selection corroborate a distinct precision-editing platform; they receive one combined adjustment ([Breakthrough](https://breakthroughprize.org/News/91), [Clarivate](https://clarivate.com/citation-laureates/chemistry/)).
- Perovskites: 1.10. The Kyoto Prize announcement of June 19, 2026 recognizes Miyasaka’s perovskite photovoltaic work ([Kyoto Prize](https://www.kyotoprize.org/260619-j)).
- Delivery systems: 1.10. Cullis’s 2022 Gairdner recognition directly corroborates lipid delivery. Broader tissue-engineering recognition is not transferred wholesale to nanoparticles ([Gairdner](https://www.gairdner.org/resource-hub/gairdner-global-perspective-panel-therapeutics-for-the-future)).
- Targeted degradation: 1.15. FDA’s May 1, 2026 approval of vepdegestrant confirms therapeutic realization of a heterobifunctional protein degrader. Clinical translation is supporting evidence, not a prerequisite for a Chemistry award ([FDA](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-vepdegestrant-er-positive-her2-negative-esr1-mutated-advanced-or-metastatic-breast)).
- Pd carbon–heteroatom coupling: 1.10. The exact-topic 2019 Wolf recognition corroborates the method ([Wolf Foundation](https://wolffund.org.il/category/field/chemistry/page/2/)).
- Dye-sensitized cells: 1.10. The discovery-specific 2010 Millennium recognition supplies modest corroboration ([Millennium Technology Prize](https://millenniumprize.org/winners/dye-sensitised-solar-cells/)).

The full distributions follow. C is displayed rounded; D, B, T, M, H, and F are the exact judgment inputs. Probability columns are rounded percentages for readability. Both underlying distributions sum to one, and the final JSON preserves normalized arithmetic rather than epistemic certainty to nine decimal places ([calculation](#model)).

| Discovery | C | D | B | T | M | H | F | Profiles % | Final % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sequencing-by-synthesis | .478 | .98 | .70 | .90 | 1.00 | 1.00 | 1.70 | 1.7 | 2.4 |
| Controlled radical polymerization | .588 | .95 | .90 | .90 | 1.25 | 1.00 | 1.00 | 3.0 | 2.8 |
| Solid-state perovskites | .838 | .97 | .77 | .68 | 1.00 | 1.00 | 1.10 | 5.6 | 5.7 |
| Delivery systems | .621 | .81 | .96 | .96 | 1.15 | 1.00 | 1.10 | 2.0 | 2.0 |
| Protein electron transfer | .325 | .67 | .83 | .62 | 1.25 | 1.00 | 1.40 | .4 | .5 |
| Phosphoramidite synthesis | .221 | .98 | .50 | .96 | 1.25 | 1.00 | 1.00 | .7 | .7 |
| C–H functionalization | .684 | .85 | .75 | .70 | 1.00 | 1.00 | 1.00 | 2.2 | 2.0 |
| Nanopores | .839 | .97 | .75 | .92 | 1.25 | 1.00 | 1.00 | 6.9 | 6.5 |
| SAMs | .705 | .95 | .95 | .94 | 1.25 | 1.00 | 1.40 | 4.6 | 5.8 |
| Targeted degradation | .693 | .93 | .82 | .88 | 1.00 | 1.00 | 1.15 | 3.1 | 3.3 |
| Base/prime editing | .920 | .99 | .85 | .98 | .50 | 1.00 | 1.20 | 4.9 | 5.3 |
| Ab initio dynamics | .764 | .99 | .97 | .52 | 1.25 | 1.00 | 1.00 | 6.2 | 5.8 |
| Chaperones | .785 | .87 | .81 | .69 | 1.25 | 1.00 | 1.00 | 4.1 | 3.8 |
| Combined solar cells | .871 | .98 | .95 | .80 | 1.00 | .30 | 1.00 | 2.7 | 2.5 |
| OLEDs | .599 | .98 | .77 | .97 | 1.25 | 1.00 | 1.00 | 3.2 | 3.0 |
| DNA origami | .764 | .92 | .60 | .68 | 1.00 | 1.00 | 1.00 | 3.3 | 3.1 |
| Pd carbon–heteroatom coupling | .651 | .96 | .85 | .95 | 1.25 | 1.00 | 1.10 | 3.8 | 3.8 |
| Combined DNA methods | .472 | .98 | .67 | .93 | 1.00 | .30 | 1.00 | .6 | .5 |
| Exchange-correlation functionals | .799 | .99 | .97 | .44 | 1.25 | 1.00 | 1.00 | 6.9 | 6.4 |
| Chemical genetics/KRAS | .580 | .50 | .85 | .91 | 1.00 | 1.00 | 1.00 | .5 | .5 |
| Genetic-code expansion | .747 | .93 | .87 | .95 | 1.00 | 1.00 | 1.00 | 4.0 | 3.7 |
| Atomic layer deposition | .280 | .93 | .65 | .85 | 1.25 | 1.00 | 1.00 | .8 | .8 |
| Carbohydrate synthesis | .250 | .62 | .90 | .98 | 1.00 | 1.00 | 1.00 | .3 | .2 |
| Proteomics | .826 | .98 | 1.00 | .98 | 1.25 | 1.00 | 1.25 | 8.1 | 9.1 |
| Dye-sensitized cells | .855 | .98 | 1.00 | .90 | 1.25 | 1.00 | 1.10 | 8.8 | 8.9 |
| Stable/NHC carbenes | .317 | .97 | .76 | .58 | 1.25 | 1.00 | 1.00 | 1.1 | 1.0 |
| Bacterial communication | .702 | .87 | .91 | .78 | 1.25 | 1.00 | 1.00 | 3.3 | 3.1 |
| Photocatalytic water splitting | .324 | .97 | .97 | .76 | 1.25 | 1.00 | 1.00 | 1.3 | 1.2 |
| Proton-coupled electron transfer | .455 | .65 | .78 | .55 | 1.10 | 1.00 | 1.00 | .5 | .5 |
| Nuclear receptors | .801 | .89 | .98 | .98 | 1.25 | 1.00 | 1.00 | 5.4 | 5.0 |

The profile drivers for every submitted option above 5% are as follows ([distribution](#model)).

Proteomics has strong careers and several complementary original methods. Mann’s sample of 797 works, reported for 1972–2021, has career-reference ranks of 92%, 87%, and 92%; Aebersold’s 788 works from 1982–2021 have ranks of 79%, 79%, and 85%. Their book reach is exceptional. Yates’s database search and scalable proteome analysis connect these careers to a coherent analytical platform. The anomalous Mann and Yates windows reduce aggregate confidence without invalidating recognizable methods ([client profiles](#client-profiles), [original MudPIT paper](https://www.nature.com/articles/nbt0301_242)).

Dye-sensitized cells combine Grätzel’s strong singleton profile with a clear device realization. His 1,465 works from 1973–2021 have career-reference ranks of 84%, 84%, and 89%, and both book measures exceed the supplied comparison cohort. The original cell paper has maximum supplied impact, 24 citing books, and a mature realization age. His perovskite paper contributes no discovery evidence to this narrower arm ([client profiles](#client-profiles), [original cell paper](https://www.nature.com/articles/353737a0)).

Nanopores are supported by Branton’s unusually strong career ranks—93%, 92%, and 97% across 165 works from 1961–2021—and complementary Bayley and Deamer papers. The original translocation, pore-structure, and engineered-recognition studies establish a distinct single-molecule analytical window. The option includes analysis as well as sequencing, so the early experiments’ limited sequencing capability does not disqualify their discovery evidence ([client profiles](#client-profiles), [translocation paper](https://doi.org/10.1073/pnas.93.24.13770), [engineered recognition](https://www.nature.com/articles/nbt0701_636)).

Exchange-correlation functionals have unusually complete discovery-specific evidence: all three listed Perdew papers concern the named advance. His 313 works from 1970–2021 have career-reference ranks of 79%, 84%, and 77%. The supplied 71 citing books for the GGA paper provide strong supporting reach. Low patent ownership has little influence on a theoretical-method option ([client profiles](#client-profiles)).

Ab initio dynamics pair strong Car and Parrinello careers with their shared, directly relevant realization. Their samples contain 342 and 662 works, covering 1975–2021 and 1971–2021. The unified method has supplied foundation share 0.61 and fifteen citing books. Its long maturity lag supports the case; classical dynamics and thermostat papers do not inflate the discovery score ([client profiles](#client-profiles)).

SAMs combine Whitesides’s strong career and book profile with Allara and Nuzzo’s original surface studies. Whitesides’s 1,505 works from 1962–2021 have career-reference ranks of 72%, 72%, and 77%. The surface-formation and characterization papers supply direct evidence; the shared thiolate review supplies reach, not another invention ([client profiles](#client-profiles), [original adsorption paper](https://pubs.acs.org/doi/abs/10.1021/ja00351a063)).

Perovskites are driven by Snaith’s exceptional career-reference ranks of 95%, 89%, and 97% across 481 works from 2000–2021. His cell and physical-property advances have high supplied impact and foundation shares. Park and Miyasaka add relevant device evidence. Their shorter realization age restrains the otherwise strong score once, through M ([client profiles](#client-profiles)).

Base/prime editing has unusually clean discovery evidence and exceptional career impact. Liu’s 193 works from 1992–2021 reach the 92% reference rank on all three career measures. All three defining works demonstrate the named tools. This keeps the singleton competitive despite the short-lag prior; the later paper’s complete impact is not discounted ([client profiles](#client-profiles)).

Nuclear receptors remain just above the threshold because Evans’s career and book profiles are strong. His 646 works, reported for 1933–2021, have career-reference ranks of 84%, 77%, and 89%. The anomalous window is discounted, the fibroblast paper is excluded, and the receptor-superfamily account plus ligand realization provide relevant mature evidence ([client profiles](#client-profiles)).

For the leading discoveries, my conditional laureate sets are Yates, Mann, and Aebersold for broad proteomics; Brian O’Regan and Michael Grätzel for dye-sensitized cells; and Deamer, Branton, and Bayley for nanopores. The proteomics set is a leadership inference across complementary methods, not a claim that these leaders personally authored every algorithm. The dye-cell set follows the original two-author demonstration. The nanopore set is less secure: Kasianowicz’s first authorship of the translocation paper makes him a serious alternative ([proteomics leadership record](https://www.gairdner.org/resource-hub/2026-canada-gairdner-award-winners), [dye-cell authorship](https://www.nature.com/articles/353737a0), [nanopore authorship](https://doi.org/10.1073/pnas.93.24.13770)).

## What's non-obvious
A highly cited review is not a second discovery, and a short defining-work list is not an exhaustive priority record. The later dye-cell review does not remove O’Regan’s credit for the original device. The prominent SAM review is shared by Nuzzo and Whitesides, not Allara. The original nanopore translocation experiment proposed sequencing as a future possibility. These distinctions affect discovery-role scores and expected names more than they affect whether the broad discovery exists ([dye-cell review](https://www.nature.com/articles/35104607), [SAM review](https://doi.org/10.1021/cr0300789), [nanopore experiment](https://doi.org/10.1073/pnas.93.24.13770)).

A neighboring Nobel is not automatic exclusion. The earlier mass-spectrometry award recognized soft ionisation, which is related to but distinct from the scalable identification, quantification, and inference methods scored here. I therefore apply no blanket penalty to proteomics, computational chemistry, or palladium chemistry. Nor do I penalize an option merely because I found less current publicity: silence is not adverse evidence ([official mass-spectrometry background](https://www.nobelprize.org/uploads/2018/06/advanced-chemistryprize2002.pdf), [adjustment ledger](#model)).

## Uncertainties
The largest uncertainty is the conversion from descriptive profiles to selection weights. Changing the common score slope from seven to eleven and calibration power from 0.75 to 0.95 moves the proteomics estimate between 7% and 11%, with dye-sensitized cells spanning a similar range. These are model-sensitivity ranges, not statistical confidence intervals. Changing discovery boundaries or evidence judgments could move the estimates further ([sensitivity calculation](#model)).

The profiles also contain attribution anomalies and incomplete landmark-work coverage. Complete author-disambiguated records, decisive-paper contribution statements, and a fuller chronology of each enabling realization would improve the comparison. Exact laureate allocation remains less secure than discovery matching, especially for multi-contributor platforms. The committee’s assessments would be the most valuable missing evidence, but nominations and related deliberative information are confidential for fifty years ([client data limitations](#client-profiles), [official selection process](https://www.nobelprize.org/chemistry)).