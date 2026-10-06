## TL;DR
Ultracold-atom quantum simulation leads at 9%, followed by quantum error correction at 6% and topological insulators at 5% ([calculation audit](sandbox:/mnt/data/nobel_forecast_audit.md)). Those three account for 20% of the conditional probability, so the forecast remains spread across many discoveries ([calculation audit](sandbox:/mnt/data/nobel_forecast_audit.md)). The probabilities are conditional on a listed discovery matching the official motivation; the exact laureate names do not determine resolution ([supplied resolution rules](sandbox:/mnt/data/nobel_forecast_audit.md)).

## Context
This forecast uses the client's original information cutoff of 6 October 2026 at 00:47 UTC. The Academy scheduled the announcement for 6 October at 11:45 CEST, or 09:45 UTC, at the earliest, placing it after the cutoff ([Academy press invitation, published 1 September 2026](https://www.kva.se/nyheter/pressinbjudan-offentliggorande-av-nobelprisen-i-fysik-och-kemi-samt-ekonomipriset-3/)). No Physics result or post-cutoff evidence enters the calculation.

The discovery, not the named team, is the forecasting unit. Error-correction wording maps to the specific error-correction option rather than the broader quantum-information option; quantum-anomalous-Hall wording maps to that specific option rather than generic topological materials. The larger-share, first-mentioned and most-specific-match rules apply, and an unmatched discovery annuls the question ([supplied resolution rules](sandbox:/mnt/data/nobel_forecast_audit.md)).

## Evidence
The historical backbone is the supplied timing reference class covering all 26 annual Physics prizes from 2000 through 2025. Approximately 15–20% had a decisive-work lag of ten years or less, about 35% had a lag of ten to twenty-five years, and approximately 45–50% waited longer; the supplied median is roughly thirty years ([supplied timing evidence](sandbox:/mnt/data/nobel_forecast_audit.md)). This is a maturity prior, not a quota that the candidate distribution must reproduce. Fast awards remained possible when the work was a dramatic first observation or a rapidly adopted enabling tool.

The primary comparison uses the supplied OpenAlex January 2026 snapshot, PatentsView vintage of 31 December 2025, and patent-to-paper links. Publication windows run from each person's stated age-25 boundary through 2021. The packet contains 74 person-option appearances representing 72 people, with individual samples ranging from nine to 1,020 research works; its reference cohort comprises 62 Physics laureates awarded during 2000–2025 ([supplied dataset and provenance](sandbox:/mnt/data/nobel_forecast_audit.md)). Impact measures are complete five-year, publication-year-and-field-normalized percentiles. Book and patent measures are cumulative counts, with more accumulation time for candidates than for some historical laureates. They therefore receive supporting rather than dominant weight.

I accept the stipulated Medicine outcome as a premise, not independently verified news. Its discovery-to-method narrative and roughly two-decade maturation period support giving more weight to a discovery that became a field-wide research capability. Its numerical effect is small: two percentage points move from technological translation to discovery evidence, with no physics-area rotation signal ([stipulated Medicine outcome and weighting change](sandbox:/mnt/data/nobel_forecast_audit.md)).

The aggregation rule is consistent across options: 65% of the supplied group-mean score and 35% of the group-maximum score. This allows an exceptional contributor to matter without automatically rewarding an option for naming more people. Shor and Kitaev receive their full career evidence in both options naming them, while discovery-specific papers are filtered separately ([aggregation and relevance ledger](sandbox:/mnt/data/nobel_forecast_audit.md)).

For career impact, let \(p\) be median impact and let \(h,z\) be the top-decile and top-percentile shares in percentage units. I calculate the following function on both the supplied mean figures and maximum figures, then aggregate them as above:

$$
f(p,h,z)=0.40\operatorname{clip}\left(\frac{p-0.70}{0.30}\right)+0.35\operatorname{clip}\left(\frac{h}{70}\right)+0.25\operatorname{clip}\left(\frac{z}{30}\right).
$$

Here, clip bounds a value between zero and one. The scales reflect the supplied historical-laureate comparisons and prevent extreme shares from growing without limit. The option reliability factor is the geometric mean of its named people's reliability factors; it shrinks this career score toward the midpoint, rather than adding a probability floor ([career calculation](sandbox:/mnt/data/nobel_forecast_audit.md)).

Discovery evidence combines anchor-paper impact, Foundation share and a disclosed judgment of discovery coherence and demonstrated enabling scope. Its weights are 40%, 20% and 40%, respectively. Distinct numerical anchors count once, regardless of how many named people coauthored them. Missing anchor metrics receive common imputations of 0.90 for impact and 0.50 for Foundation share, rather than zero or automatic maximum credit ([anchor inputs and discovery scores](sandbox:/mnt/data/nobel_forecast_audit.md)). The table below identifies the principal anchors; the linked ledger specifies all supporting works and relevance exclusions.

Book reach uses logarithmic, capped counts, equally combining breadth across cited works and citing books. Translation similarly caps citing inventions and own patents, with a 70/30 split between those measures. The final profile score gives career impact 40%, discovery evidence 47%, books 10% and translation 3%. Disruption and collaboration receive no separate numerical weight ([complete supporting-channel formulas](sandbox:/mnt/data/nobel_forecast_audit.md)). Enormous patent counts therefore cannot overwhelm weak discovery or career evidence.

The complete reliability exceptions are:

- Small samples: Bistritzer receives factor 0.50 for nine works; Bouman receives 0.70 for thirty-two works ([sample adjustments](sandbox:/mnt/data/nobel_forecast_audit.md)).
- Attribution uncertainty: Halzen, Karle, Thompson, Gerber, Tu and Crooks receive 0.95; Kurahashi Neilson receives 0.90 for the combination of estimated age, merged record and missing landmark; Lee and Charbonneau receive 0.85 for low-confidence landmark attribution ([attribution adjustments](sandbox:/mnt/data/nobel_forecast_audit.md)).
- Visible record anomalies: Cho and Spaldin receive 0.90 for apparent early-career truncation, with Cho also carrying a questionable affiliation. Nakamura receives 0.855, combining 0.95 for medium confidence and 0.90 for the affiliation anomaly. Binnig's implausible historical coauthor entries receive no credit, but his genuine AFM anchors and career are not penalized for those entries ([record adjustments](sandbox:/mnt/data/nobel_forecast_audit.md)).
- Post-2018 papers retain their complete five-year impact evidence at factor 1.00. Their work-specific cumulative book and patent counts receive no additional supporting weight, factor 0.00. Supplied aggregate counts remain unchanged because the packet does not permit subtracting recent-paper contributions. Large collaborations receive no extra penalty, and every other person-level factor is 1.00 ([recent-work treatment](sandbox:/mnt/data/nobel_forecast_audit.md)).

Maturity enters once. The relative multiplier is 1.00 for supplied decisive anchors older than twenty-five years and 0.90 for ten-to-twenty-five-year anchors. The short-lag multipliers are 0.55 for magic-angle graphene, 0.70 for black-hole imaging and 0.40 for the spin-liquid/topological-order realization. The differences reflect the supplied adoption evidence and dramatic-observation precedent, not a second recency adjustment ([maturity assignments](sandbox:/mnt/data/nobel_forecast_audit.md)).

For profile score \(S_i\), maturity multiplier \(M_i\), and secondary multiplier \(K_i\), the submitted calculation is:

$$
w_i=\exp\left(8(S_i-1)\right)M_i,\qquad
P_i=\frac{(w_iK_i)^{0.80}}{\sum_j(w_jK_j)^{0.80}}.
$$

The profile-only distribution sets every \(K_i\) to one. The common power tempers score differences identically across all arms after scoring. There is no uniform floor or mixture with a uniform distribution ([probability calculation](sandbox:/mnt/data/nobel_forecast_audit.md)).

Both distributions appear below. Percentages are rounded to whole points for readability and need not sum exactly after rounding. The audit contains the full profile-only distribution, all numerical score inputs and the submitted calculation; the JSON probabilities below preserve normalization ([download the evidence and calculation audit](sandbox:/mnt/data/nobel_forecast_audit.md)).

| # | Discovery and principal anchors | M | Secondary K | Profiles only | Submitted |
|---:|---|---:|---:|---:|---:|
| 1 | [QSH: 2005 theory / 2007 HgTe](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.15 | 5% | 5% |
| 2 | [Optical clocks: 2003 clock papers](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.30 | 3% | 4% |
| 3 | [Metamaterials: 1999 theory / 2000 medium](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.30 | 4% | 4% |
| 4 | [Geometric phases: 1959 / 1984](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 2% | 2% |
| 5 | [Quantum-information foundations: 1984 / 1992 / 1994](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.10 | 3% | 3% |
| 6 | [Magic-angle graphene: 2011 / 2018](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.55 | 1.00 | 3% | 3% |
| 7 | [Quantum simulation: 1998 / 2002](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.30 | 7% | 9% |
| 8 | [2D electrons: 1989 theory / 1987 observation](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.10 | 3% | 3% |
| 9 | [Quantum cascade laser: 1994](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 2% | 2% |
| 10 | [Cosmic neutrinos: 2013](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.00 | 4% | 4% |
| 11 | [Error correction: 1995](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 6% | 6% |
| 12 | [Black-hole shadow: 2000 / 2019](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.70 | 1.00 | 3% | 3% |
| 13 | [Inflation: 1981](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 3% | 3% |
| 14 | [CDM simulations: 1985](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 5% | 5% |
| 15 | [Corrected electron optics: 1995](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.15 | 1% | 1% |
| 16 | [Efficient OLEDs: 1998](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.10 | 5% | 5% |
| 17 | [Atomic force microscopy: 1986](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 0.70 | 5% | 4% |
| 18 | [Spin liquids/topological order: 2003 / 2021](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.40 | 1.00 | 2% | 2% |
| 19 | [Wavelets: 1986 / 1987](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 0.75 | 1% | 1% |
| 20 | [Quantum-dot spin computation: 1998](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 4% | 4% |
| 21 | [Stellar explosions: 1973](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 2% | 2% |
| 22 | [CMB fluctuation theory: 1984](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 5% | 5% |
| 23 | [Rees astrophysics: 1967](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 1.00 | 1% | 1% |
| 24 | [Skyrmions: 2006 / 2009](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.00 | 4% | 4% |
| 25 | [Exoplanet atmospheres: 2000 / 2002](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.00 | 5% | 5% |
| 26 | [Active matter: 1995 / 2007](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.00 | 1% | 1% |
| 27 | [Multiferroics: 2003](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.10 | 4% | 4% |
| 28 | [Quantum anomalous Hall effect: 2013](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.10 | 2% | 3% |
| 29 | [Superconducting-qubit control: 1999](sandbox:/mnt/data/nobel_forecast_audit.md) | 1.00 | 0.50 | 2% | 1% |
| 30 | [Fluctuation theorems: 1993 / 2002](sandbox:/mnt/data/nobel_forecast_audit.md) | 0.90 | 1.00 | 3% | 3% |

Every non-neutral secondary adjustment is listed here. These are judgmental relative-weight factors, not measured selection odds:

- Quantum simulation and optical clocks each receive 1.30 from the shared Wolf recognition. The institutional announcement dated 2 October 2026 identifies Bloch's optical-lattice platform and the shared award with Ye; the foundation describes Ye's clock-development contribution. I count this overlapping signal once per arm, not as several independent endorsements ([dated institutional announcement](https://www.mpq.mpg.de/7265106/09-wolf-prize-for-immanuel-bloch?c=6204982), [Wolf Foundation](https://wolffund.org.il/home-page/)).
- Metamaterials receive 1.30 for the officially listed 2026 Nobel Symposium on metamaterials science and technology. A relevant conference is a useful weak signal, not a nomination list or a promise of an award ([Academy symposium list](https://www.kva.se/utlysningar/nobelsymposier/)).
- Topological insulators receive 1.15 from the discovery-specific 2019 Breakthrough recognition; strong-field 2D electrons receive 1.10 from the 2025 Wolf recognition documented on 11 March 2025; corrected electron optics receive 1.15 from the exact-tool 2020 Kavli award ([Breakthrough](https://breakthroughprize.org/Laureates/1/L3829), [ERC announcement](https://erc.europa.eu/news-events/news/two-erc-grantees-among-2025-wolf-prize-winners-physics-and-agriculture), [Kavli](https://www.kavliprize.org/prizes/nanoscience/2020)).
- Quantum-information foundations receive 1.10 from Bennett and Brassard's 2025 Turing Award, announced on 18 March 2026. This validates the foundations package without assuming a fresh recognition cascade must continue ([dated NSF account](https://www.nsf.gov/cise/updates/pioneers-quantum-information-science-recognized-2025-acm-am)).
- OLEDs, multiferroics and the quantum anomalous Hall effect each receive 1.10 from the discovery-specific Clarivate selections released on 17 September 2026. Their underlying bibliometric evidence overlaps the primary profiles, so the increments remain small ([dated Clarivate release](https://www.clarivate.com.cn/news/clarivate-reveals-citation-laureates-2026-recognizing-transformative-scientific-breakthroughs/), [Physics selections](https://clarivate.com/citation-laureates/physics/)).
- AFM receives 0.70 for the neighboring STM recognition and repeated-credit complication associated with Binnig's prior award; this is not a requirement that he win again or a ban on an AFM prize. Wavelets receive 0.75 for disciplinary fit, informed by the mathematical framing of the Abel citation. Superconducting-qubit control receives 0.50 for its close adjacency to the circuit discovery honored on 7 October 2025; coherent control remains a distinct discovery ([Binnig's prior award](https://www.nobelprize.org/prizes/physics/1986/binnig/facts/), [Abel citation](https://abelprize.no/abel-prize-laureates/2017), [2025 Physics motivation](https://www.nobelprize.org/prizes/physics/2025/press-release/)).

Every other secondary factor is 1.00. There is no general penalty on quantum physics, no claim that astrophysics is due, no committee-specialty adjustment, and no market signal in the calculation ([complete adjustment ledger](sandbox:/mnt/data/nobel_forecast_audit.md)).

The five submitted arms exceeding 5% before rounding are supported by these profile features:

- Quantum simulation combines exceptionally strong careers with a demonstrated platform. Its supplied mean/max median impact is 0.97/0.99 and top-percentile share is 34%/50%. Both anchors have impact 1.00, with Foundation shares 0.75 and 0.71; the realization has a twenty-four-year lag. It leads before secondary evidence is applied ([supplied profiles and calculation](sandbox:/mnt/data/nobel_forecast_audit.md)).
- Error correction combines strong career evidence with the Shor memory-protection anchor, whose impact is 1.00 and Foundation share is 0.88. Coding, reliable-computation, threshold and fault-tolerant-anyonic works support the enabling package, with a thirty-one-year anchor lag. Shor's factoring algorithm is not imported into this discovery score ([relevance ledger and profiles](sandbox:/mnt/data/nobel_forecast_audit.md)).
- Topological insulators have unusually clear conceptual and observational anchors. Kane's supplied top-percentile share is 39%, exceeding the entire historical reference cohort. The theory and observation anchors have Foundation shares of 0.81 and 0.79, and the HgTe realization has a nineteen-year lag ([supplied profiles](sandbox:/mnt/data/nobel_forecast_audit.md)).
- OLEDs have a balanced career package and a sharply identified invention. The supplied mean/max median impact is 0.92/0.94; the phosphorescence anchor has impact 1.00 and Foundation share 0.74, with a twenty-eight-year lag. Its extraordinary patent reach helps only through the capped translation channel ([supplied profiles and channel weights](sandbox:/mnt/data/nobel_forecast_audit.md)).
- CMB theory has exceptional group career impact: supplied mean/max median impact is 0.98/0.98 and top-percentile shares are 41%/41%. Its anchor is forty-two years old. Its discovery score is restrained relative to compact demonstrated platforms because the supplied package centers on theoretical calculation and interpretation, rather than an equivalent first experimental capability ([supplied profiles and discovery score](sandbox:/mnt/data/nobel_forecast_audit.md)).

## What's non-obvious
The discovery boundary matters as much as the career totals. The clock packet's low-impact cooling anchor is preparatory, not the clock invention; I use it for context and timing, while the discovery score uses the relevant clock papers. Conversely, Yablonovitch's photonic-bandgap work counts fully toward his career but not as negative-index discovery evidence ([relevance exclusions](sandbox:/mnt/data/nobel_forecast_audit.md)). The same distinction applies to QSH: the graphene concept and HgTe observation form a broad discovery chain, but the direct HgTe material prediction involved an additional theoretical bridge ([original HgTe theory](https://arxiv.org/abs/cond-mat/0611399)). Strong profiles do not settle how the committee will compress credit.

My working laureate sets for the leading discoveries follow anchor authorship: quantum simulation—Dieter Jaksch, Peter Zoller and Immanuel Bloch, with Cirac and Greiner strong alternatives ([theory anchor](https://arxiv.org/abs/cond-mat/9805329), [realization anchor](https://www.nature.com/articles/415039a)); quantum error correction—Peter Shor, Andrew Steane and Alexei Kitaev, with threshold-centered wording changing the credit allocation ([Shor anchor](https://link.aps.org/doi/10.1103/PhysRevA.52.R2493), [Steane anchor](https://link.aps.org/doi/10.1103/PhysRevLett.77.793), [Kitaev anchor](https://arxiv.org/abs/quant-ph/9707021)); topological insulators/QSH—Charles Kane, Eugene Mele and Laurens Molenkamp ([conceptual anchor](https://arxiv.org/abs/cond-mat/0411737), [experimental anchor](https://arxiv.org/abs/0710.0582)). These are secondary credit judgments. Unlisted people's careers do not enter the option ranking.

## Uncertainties
The largest gap is evidence about the confidential choice, not new science before the announcement. A date-matched comparison of nominated winners and non-winners would help calibrate the feature weights and score concentration. The supplied packet instead gives rich candidate profiles and laureate reference lines. Attribution gaps and unequal cumulative-citation exposure remain, despite the disclosed reliability treatment. The stipulated Medicine outcome remains an accepted premise rather than an independently checked observation ([data limitations and premises](sandbox:/mnt/data/nobel_forecast_audit.md)).

Changing only the score slope from six to ten moves quantum simulation from about 7% to 10%, while retaining the same leading three arms. That is a sensitivity check, not a confidence interval; changing discovery-coherence judgments or evidence weights can move the ranking further ([sensitivity calculation](sandbox:/mnt/data/nobel_forecast_audit.md)). The decimal places in the JSON preserve the computed distribution and normalization. They do not represent comparable certainty about the committee's decision.