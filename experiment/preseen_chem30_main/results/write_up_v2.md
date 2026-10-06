## TL;DR
Mass-spectrometry-based proteomics leads at 9%, followed by dye-sensitized solar cells and nanopore methods at 8% each ([forecast calculation](#evidence)). These three discoveries account for 25% of the conditional distribution, leaving 75% elsewhere ([forecast calculation](#evidence)). The supplied profiles support a broad field of mature discoveries, not a dominant winner ([client-supplied evidence](#context)).

## Context
The information cutoff is October 6, 2026, at 19:07 UTC. Chemistry is scheduled for October 7 at 11:45 CEST at the earliest, equivalent to 09:45 UTC ([official schedule](https://www.nobelprize.org/prizes/about/prize-announcement-dates/)). This forecast is conditional on a listed discovery matching the official motivation. Laureate names need not match the option labels. The larger-share, first-mentioned, and most-specific-discovery rules determine the winning option; an unmatched discovery annuls the question ([client resolution rules](#context)).

The principal evidence is the client’s supplied profiles and assumed reference outcomes. Throughout this report, links to “client-supplied evidence” refer to those materials in the question, not independently retrieved datasets. Their stated vintages are OpenAlex January 2026 and PatentsView December 31, 2025; research works and granted patents run through 2021. Reliance on Science has no separately specified vintage. The historical comparison contains 61 Chemistry laureates from 2000–2025, measured at their prize dates. I accept the supplied Medicine and Physics outcomes as premises and use them only for the permitted lessons about decisive realization, instrument leadership, and recognition cascades—not to infer which chemistry area is due ([client-supplied evidence](#context)).

## Evidence
The historical backbone is the supplied timing record for the 26 annual Chemistry prizes from 2000 through 2025. Approximately 15–20% had discovery-to-prize lags of ten years or less, about a third had lags of 10–25 years, and about 45% exceeded 25 years; the median was roughly 25 years. Fast awards generally recognized structures or tools already adopted across a field. These are approximate bins, not an estimated annual award hazard ([supplied timing prior](#context)).

I translate that record into maturity multipliers of 0.40 for lags of ten years or less, 0.75 for 11–25 years, and 1.00 beyond 25 years. Where the displayed works do not establish a usable realization date, I use 0.80, a coarse marginalization over the supplied bins. The timing prior enters once. I impose no additional recency discount afterward and no automatic penalty merely for exceeding 45 years ([model specification](#evidence)).

The other committees’ supplied outcomes favor a distinction between discovering a phenomenon and making it a field-wide tool. They also argue against rewarding collaboration size or requiring three recipients. I therefore give original realizations more weight than reviews, do not sum scientists’ careers, and keep collaboration to a minor component. The recognition cascade remains secondary ([assumed reference outcomes](#context)).

The scoring model uses the supplied historical reference lines rather than replacing them with current citation totals. For each person, career impact C is the mean of the reference ranks for median impact, top-decile share, and top-percentile share. Textbook reach B is the higher of the two book-reference ranks, avoiding a double bonus for closely related measures. Translation T is the mean of the invention and own-patent reference ranks. Collaboration K is a binary indicator for a reported laureate coauthor, not a count of collaborators or shared papers. These definitions use the client’s benchmark of approximately 200 citing inventions and six own US patents at prize time; thousands of inventions are meaningful, but translation does not dominate the ranking ([profile definitions and reference lines](#context)).

Each career feature is multiplied by the person’s reliability factor h, listed below. Within an option, each feature is aggregated as 0.60 times the strongest named person plus 0.40 times the mean across the named people. This is not a sum. A single-person option receives that person’s full adjusted feature. A scientist named in two options contributes the same career measures to both; only discovery-work relevance changes ([model specification](#evidence)).

For a relevant displayed work, I assign a realization grade R: 1.00 for a direct original method or realization, 0.80 for an enabling implementation or structural contribution, and 0.45 for a review or synthesis. Its work score is:

$$
q_j=0.60I_j+0.30R_j+a_j\left[0.05\frac{\ln(1+V_j)}{\ln(5090)}+0.05\frac{\ln(1+L_j)}{\ln(72)}\right].
$$

Here I is the supplied five-year impact percentile, V counts citing inventions, and L counts citing books. The denominators normalize against the largest relevant-work counts in the supplied profiles. The exposure factor a is 0.50 for works after 2018 and 1.00 otherwise. It attenuates patent and book evidence only; completed five-year impact windows are retained. Disruption and Foundation share receive no separate numerical weight ([work inputs](#context); [model specification](#evidence)).

Shared papers are counted once within an option. Discovery evidence D is 0.75 times the best work score plus 0.25 times the mean of the three highest scores, or all relevant works when fewer are available. Gray and Shokat have no displayed work that directly establishes their specified discoveries, so D is imputed at 0.50 rather than set to zero. This is missing-feature treatment, not a probability floor ([relevant-work selections below](#evidence)).

The option score and unnormalized profile weight are:

$$
S_i=0.40C_i+0.40D_i+0.15B_i+0.04T_i+0.01K_i,
\qquad W_i=\exp(10S_i)t_i m_i.
$$

Thus career impact and discovery evidence carry 80% of the score. The maturity factor is t. The motivation-scope factor m is 0.40 for each combined option and 1.00 otherwise. The combined options require a genuinely broader motivation; recipient overlap alone does not qualify them, and a separately divided award still follows the client’s share/order rules ([model specification](#evidence); [resolution rules](#context)).

Calibration is applied identically to all arms:

$$
P_{\mathrm{profile},i}=\frac{W_i^{0.80}}{\sum_jW_j^{0.80}},
\qquad
P_{\mathrm{final},i}=\frac{(W_iF_i)^{0.80}}{\sum_j(W_jF_j)^{0.80}}.
$$

F is the bounded secondary-evidence factor. The common power broadens the distribution without adding a uniform floor. These coefficients are explicit forecasting judgments, not a fitted model of secret committee decisions ([model specification](#evidence)).

All non-neutral reliability adjustments are listed here. They affect career summaries, not the plausible, identified discovery papers. The chronology flags indicate attribution uncertainty; they do not establish that every work in a profile is misassigned ([supplied profiles](#context); [model specification](#evidence)).

| Reliability factor h | People and reason |
|---|---|
| 0.90 | Yates: 1945 window start; Hartl: 1953; Balasubramanian: 1958; Evans: 1933; Bergman: 1942; Chin: 1969; Mann: 1972; Herrmann: early window and historical coauthor entries |
| 0.90 | Hammes-Schiffer: the reported 123 shared works with Bertozzi raise attribution concerns; her collaboration indicator is also set to zero |
| 0.80 | Rothemund: 1928 start and historical coauthor entry; Gray: 1920 start; Bertrand: 1904 start |
| 0.85 | Hao Yan: affiliation/identity ambiguity |
| 0.80 | Van Slyke: only 15 research works |
| 0.95 | Grätzel, Liu, and Car: incongruent affiliation combinations, a weaker attribution warning |
| 1.00 | Every other named person |

Suntola’s 50 works and Rothemund’s 53 do not receive an additional small-sample penalty. The post-2018 exposure factor applies to exactly three included entries: Miyasaka’s 2019 review, Park’s 2020 review, and Liu’s 2019 prime-editing paper. It does not discount their impact percentiles or their entire careers ([supplied profiles](#context); [model specification](#evidence)).

The following table gives every relevant-work selection, maturity factor, secondary factor, and both distributions. Entry numbers identify the three defining works in each supplied profile; d, a, and r are the realization grades defined above. Unlisted works are excluded from D. Dates are displayed-work anchors, not claims that every field began with that publication. The chaperone structure is a maturity proxy, while the C–H review establishes that the relevant work was already mature. All work selections and dates refer to the [supplied profiles](#context); the probabilities are [model outputs](#evidence). Probability columns are rounded to whole percentages, so they do not sum exactly; “<1%” denotes a positive probability. The unrounded distributions each sum to one.

| Discovery | Relevant entries | Anchor; t | F | Profiles only | Submitted |
|---|---|---:|---:|---:|---:|
| Sequencing-by-synthesis | Balasubramanian 1d; Klenerman 1d | 2008; 0.75 | 1.60 | 2% | 2% |
| Controlled radical polymerization | Matyjaszewski 1r, 2d, 3r; Sawamoto 1r, 2d, 3r | 1995; 1.00 | 1.05 | 4% | 4% |
| Solid-state perovskites | Snaith 1d, 2a, 3d; Miyasaka 1d, 2r; Park 1d, 2r, 3d | 2012; 0.75 | 1.15 | 5% | 5% |
| Nanoparticle delivery | Cullis 1r, 2r, 3a | 1985; 1.00 | 1.00 | 2% | 2% |
| Phosphoramidite synthesis | Caruthers 1d, 3r | 1981; 1.00 | 1.00 | <1% | <1% |
| C–H functionalization | Hartwig 1r; Bergman 1r, 2r, 3r | Before 1995; 1.00 | 1.00 | 2% | 2% |
| Nanopore methods | Bayley 1r, 2a, 3d; Deamer 1d, 2r, 3r; Branton 1d, 2r, 3a | 1996; 1.00 | 1.00 | 8% | 8% |
| Self-assembled monolayers | Allara 1a, 2d, 3a; Nuzzo 1r, 2d; Whitesides 2r, 3r | 1983; 1.00 | 1.40 | 6% | 7% |
| Protein electron transfer | None directly establishes the specified discovery | Unknown; 0.80 | 1.50 | <1% | <1% |
| Base/prime editing | Liu 1d, 2d, 3d | 2016/2019; 0.40 | 1.30 | 4% | 5% |
| Targeted degradation | Crews 1d, 2r, 3d; Deshaies 2d | 2001; 0.75 | 1.00 | 3% | 3% |
| Ab initio molecular dynamics | Parrinello 3d; Car 1a, 2d | 1985; 1.00 | 1.00 | 6% | 5% |
| Molecular chaperones | Hartl 1r, 2r, 3r; Horwich 1r, 2a, 3a | 1994 proxy; 1.00 | 1.10 | 4% | 4% |
| Combined dye/perovskite cells | Grätzel 1d, 2r, 3d; Snaith 1d, 2a, 3d; Miyasaka 1d, 2r | 2012; 0.75 | 1.00 | 4% | 3% |
| OLEDs | Van Slyke 1d, 2d, 3d; Tang 2d, 3d | 1987; 1.00 | 1.00 | <1% | <1% |
| DNA origami/self-assembly | Rothemund 1d, 2a; Shih 1d, 2r, 3d; Yan 1d, 2a, 3r | 2004; 0.75 | 1.00 | 3% | 3% |
| Pd carbon–heteroatom coupling | Buchwald 1r, 3r; Hartwig 2d, 3r | 1998; 1.00 | 1.25 | 4% | 4% |
| Combined DNA synthesis/sequencing | Balasubramanian 1d; Klenerman 1d; Caruthers 1d, 3r | 2008; 0.75 | 1.00 | <1% | <1% |
| Exchange-correlation functionals | Perdew 1d, 2d, 3a | 1992; 1.00 | 0.85 | 7% | 6% |
| Shokat chemical genetics/KRAS | None directly establishes the specified inventions | Unknown; 0.80 | 1.00 | <1% | <1% |
| Genetic-code expansion | Schultz 3r; Chin 1r, 2r, 3d | 2002; 0.75 | 1.00 | 3% | 3% |
| Atomic layer deposition | Suntola 1a, 2d, 3d | 1980; 1.00 | 1.10 | <1% | <1% |
| Carbohydrate synthesis | Wong 3r | Unknown realization; 0.80 | 1.05 | <1% | <1% |
| Mass-spec proteomics | Yates 1d, 2d; Mann 1d, 2d, 3d; Aebersold 1r, 2d, 3d | 1994; 1.00 | 1.25 | 8% | 9% |
| Dye-sensitized cells | Grätzel 1d, 2r | 1991; 1.00 | 1.10 | 8% | 8% |
| Stable/NHC carbenes | Arduengo 1d, 2r, 3a; Bertrand 1r, 2d, 3r; Herrmann 1r, 2r | 1991; 1.00 | 1.00 | <1% | <1% |
| Bacterial communication | Bassler 1r, 2r, 3r; Greenberg 2a, 3r | 1998; 1.00 | 1.00 | 4% | 4% |
| Photocatalytic water splitting | Fujishima 1d, 2r; Domen 1d, 2r, 3d | 1972; 1.00 | 1.00 | 2% | 2% |
| Proton-coupled electron transfer | Meyer 1r, 3r | Unknown realization; 0.80 | 1.00 | <1% | <1% |
| Nuclear receptors | Evans 1r, 3d | 1995; 1.00 | 1.00 | 6% | 5% |

The complete secondary-adjustment ledger follows. Each is one net factor, not a multiplication of correlated mentions. No market prices or public probability aggregates enter the calculation ([model specification](#evidence)).

- Proteomics, F = 1.25: the Gairdner announcement dated March 31, 2026 recognizes Yates, Aebersold, and Mann together for systems-proteomics foundations. Its opening dateline says 2025, but the heading and separate 2026 notices establish the award year. This supports a coherent discovery and credit narrative, not a decisive fresh-cascade bonus ([announcement](https://www.gairdner.org/resource-hub/2026-canada-gairdner-award-winners); [corroborating notice](https://www.gairdner.org/resource-hub/announcing-the-2026-gairdner-early-career-investigators)).
- Sequencing-by-synthesis, F = 1.60: the official 2026 Wolf record credits Balasubramanian, Klenerman, and Mayer for large-scale sequencing. The October 2 expert discussion adds support for the specific sequencing discovery. I treat these signals as a bounded bundle and do not extend it to phosphoramidite synthesis ([Wolf record](https://wolffund.org.il/shankar-balasubramanian/); [ACS expert discussion](https://cen.acs.org/people/nobel-prize/predictions-2026-nobel-prize-chemistry/104/web/2026/10)).
- Monolayers, F = 1.40; protein electron transfer, F = 1.50; editing, F = 1.30: Clarivate’s 2026 selections directly match these discoveries. Citation-based recognition overlaps with the profiles, so the adjustments are modest. Editing also has independent recognition and evidence of broad laboratory adoption in Broad’s April 5, 2025 announcement; I retain its short-lag prior rather than applying another age adjustment ([Clarivate](https://clarivate.com/citation-laureates/chemistry/); [Broad announcement](https://www.broadinstitute.org/news/david-liu-receives-breakthrough-prize-life-sciences)).
- Perovskites, F = 1.15; controlled polymerization, F = 1.05; glycosynthesis, F = 1.05: these receive small adjustments from the October 2 ACS discussion. I use the named expert selections, not audience or reader vote totals ([ACS discussion](https://cen.acs.org/people/nobel-prize/predictions-2026-nobel-prize-chemistry/104/web/2026/10)).
- Pd carbon–heteroatom coupling, F = 1.25: the 2019 Wolf citation directly recognizes Buchwald and Hartwig’s carbon–heteroatom catalysts. It supports this option more specifically than broad C–H functionalization ([Wolf record](https://wolffund.org.il/john-f-hartwig/)).
- Dye-sensitized cells, F = 1.10; ALD, F = 1.10: the 2010 and 2018 Millennium recognitions corroborate their specific realizations and technological use. They do not replace the career evidence ([dye-cell record](https://millenniumprize.org/winners/dye-sensitised-solar-cells/); [ALD announcement, May 22, 2018](https://millenniumprize.org/news-articles/news/2018-millennium-technology-prize-for-tuomo-suntola-for-enabling-smart-technology/)).
- Chaperones, F = 1.10: the 2011 Lasker award validates the Hartl–Horwich pairing and identifies the decisive folding experiments, which are absent from their displayed defining-work lists ([Lasker account](https://laskerfoundation.org/winners/chaperone-assisted-protein-folding/)).
- Exchange-correlation functionals, F = 0.85: the October 13, 1998 Nobel announcement already recognized DFT and its practical role in computational chemistry. Improved functionals remain distinguishable, so this is a mild scope-overlap discount, not exclusion ([official announcement](https://www.nobelprize.org/prizes/chemistry/1998/press-release/)).

Every remaining option has F = 1.00. Missing current publicity is not treated as negative evidence, and neither proteomics nor ab initio dynamics receives an automatic penalty for an adjacent earlier Nobel ([model specification](#evidence)).

The following profile evidence drives every submitted option whose unrounded probability exceeds 5%. Counts are research works; coverage windows and historical reference ranks come from the stipulated vintages, not live bibliometrics ([client-supplied profiles](#context)).

- Proteomics: Mann’s 797-work profile, covering 1972–2021, has impact reference ranks of 92/87/92. Aebersold’s 788 works, covering 1982–2021, have ranks of 79/79/85. Both have exceptional book reach. Yates’s 1,014-work record, covering 1945–2021 and discounted for chronology, supplies the directly relevant database-search and large-scale MudPIT realizations. Multiple original methods and mature timing—not the highly cited review alone—drive the probability ([supplied profiles](#context)).
- Dye-sensitized cells: Grätzel’s 1,465 works, covering 1973–2021, have impact reference ranks of 84/84/89, and both book-reference measures exceed the comparison cohort. The original cell realization supplies direct discovery evidence and a mature chronology. His perovskite paper is excluded from this specific option ([supplied profile](#context)).
- Nanopore methods: Branton’s 165 works, covering 1961–2021, have impact reference ranks of 93/92/97. Bayley’s 328 works, covering 1977–2021, and Deamer’s 220, covering 1961–2021, supply complementary channel engineering and early experiment evidence. The shared membrane-channel paper counts once. The profiles support single-molecule analysis strongly; they do not establish that the first experiment was already a finished sequencer ([supplied profiles](#context); [original experiment](https://pubmed.ncbi.nlm.nih.gov/8943010/)).
- Monolayers: Whitesides’s 1,505 works, covering 1962–2021, provide strong career and book evidence. Allara’s 236 works, covering 1965–2021, and Nuzzo’s 403, covering 1975–2021, provide the direct surface-assembly realizations. Whitesides’s microfluidics and Nuzzo’s 4D-printing entries are not credited to monolayers ([supplied profiles](#context)).
- Exchange-correlation functionals: Perdew’s 313 works, covering 1970–2021, have impact reference ranks of 79/84/77. All displayed defining works concern useful functionals. The GGA paper’s reported 71 citing books supports durable reach. Zero own patents is not a substantial penalty for fundamental theory ([supplied profile](#context)).
- Nuclear receptors: Evans’s 646-work record, covering 1933–2021, receives the chronology discount but retains strong impact reference ranks of 84/77/89 and broad book reach. The superfamily review supports the framework; the ligand-identification paper supplies original realization evidence. The fibroblast paper is excluded ([supplied profile](#context)).
- Ab initio dynamics: Car’s 342 works, covering 1975–2021, and Parrinello’s 662, covering 1971–2021, have strong impact and book-reference lines. Their shared method paper is direct realization evidence; QUANTUM ESPRESSO supplies enabling implementation evidence. Classical sampling and unrelated applications are excluded ([supplied profiles](#context)).
- Solid-state perovskites: Snaith’s 481 works, covering 2000–2021, have impact reference ranks of 95/89/97. The displayed device and transport papers support the specific discovery; Miyasaka and Park add complementary realizations without a three-person bonus. The shorter maturity receives the middle-bin prior ([supplied profiles](#context)).

My expected recipient sets for the leading three discoveries are conditional credit forecasts, separate from discovery resolution. For proteomics, I expect Yates, Mann, and Aebersold: their original methods form a coherent leadership set, also recognized jointly by Gairdner. A narrowly software-centered motivation could instead credit Cox, whose name appears with Mann on MaxQuant ([Gairdner](https://www.gairdner.org/resource-hub/2026-canada-gairdner-award-winners); [MaxQuant original](https://www.nature.com/articles/nbt.1511)).

For dye-sensitized cells, I expect Michael Grätzel and Brian O’Regan, the two authors of the decisive paper published October 24, 1991. A Grätzel-only award remains a credit alternative, but the option label does not remove O’Regan’s original contribution ([original paper](https://www.nature.com/articles/353737a0)).

For nanopores, I retain Hagan Bayley, David Deamer, and Daniel Branton as the broad-development set, with John Kasianowicz the strongest substitution risk. The 1996 experiment names Kasianowicz, Brandin, Branton, and Deamer; the 2001 engineered-pore paper names Howorka, Cheley, and Bayley. A motivation centered on the early experiment rather than broad platform development could change that allocation ([1996 original](https://pubmed.ncbi.nlm.nih.gov/8943010/); [2001 original](https://www.nature.com/articles/nbt0701_636)).

## What's non-obvious
The strongest outside sequencing signal does not produce the strongest profile-led forecast. The supplied sequencing careers have weaker impact reference lines than the leading proteomics, nanopore, and solar-cell profiles, even though their reversible-terminator paper is compelling. The bounded Wolf/expert adjustment raises sequencing, but it cannot replace the client’s stipulated evidence hierarchy. Likewise, a sequencing motivation does not become a synthesis-plus-sequencing award because Caruthers is mentioned or receives credit elsewhere ([supplied profiles and rules](#context); [Wolf sequencing record](https://wolffund.org.il/shankar-balasubramanian/)).

Prior recognition and decisive realization are separate questions. The 2002 Chemistry award recognized enabling ionization methods, not the later database-search, statistical-inference, and quantitative workflows scored here. Meanwhile, the foundational nanopore experiment detected polymer passage rather than reading a full DNA sequence. Those distinctions support proteomics as a separate candidate and make nanopore credit sensitive to the wording of the new observational window—not simply to conceptual priority or career breadth ([2002 Nobel record](https://www.nobelprize.org/prizes/chemistry/2002/summary/); [nanopore original](https://pubmed.ncbi.nlm.nih.gov/8943010/)).

## Uncertainties
The largest unknown is the committee’s private choice and exact motivation. The supplied evidence cannot reveal nominations, deliberations, or how the committee separates adjacent achievements. The combined-option scope factors are judgments about resolution wording, not observed frequencies. Clean author-disambiguated records and discovery-specific adoption evidence would reduce the profile uncertainty; the displayed lists omit decisive papers for some candidates ([supplied profiles](#context); [model specification](#evidence)).

The numerical ordering is sensitive to how career breadth, original realization, and maturity are weighted. A 27-setting sensitivity grid varying common calibration and the two shorter-lag factors gives approximately 7–10% for proteomics, 7–10% for dye cells, and 7–9% for nanopores. These are model-sensitivity ranges, not confidence intervals; changes in attribution or scoring structure create wider uncertainty. The JSON digits preserve calculation and normalization, not nine-decimal knowledge of committee behavior ([forecast calculation](#evidence)).