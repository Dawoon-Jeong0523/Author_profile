## TL;DR
Optical-lattice quantum simulation leads at 28%, followed by quantum error correction at 23% and CMB-fluctuation theory at 22% ([calculation](sandbox:/mnt/data/nobel_physics_2026_audit.json)). Efficient OLEDs receive 15% and topological insulators 12% ([calculation](sandbox:/mnt/data/nobel_physics_2026_audit.json)). These probabilities are conditional on a listed discovery winning; an unlisted discovery annuls the question ([resolution terms](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

## Context
The information cutoff is 6 October 2026, 02:29 UTC. The official announcement is scheduled for 11:45 CEST, or 09:45 UTC, at the earliest that day—seven hours and sixteen minutes after the cutoff. This forecast uses no subsequent Physics result ([official schedule](https://www.nobelprize.org/prizes/about/prize-announcement-dates/); [cutoff](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

The supplied profiles are the main evidence. Their vintages are OpenAlex January 2026 and PatentsView 31 December 2025, with the stipulated patent-to-paper citation data. Research windows end in 2021; five-year impact windows are complete. Book and invention citations are cumulative counts, not annual rates. The comparison cohort contains 62 Physics laureates from 2000–2025, measured at their award dates ([supplied evidence](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

## Evidence
The historical backbone is the supplied timing reference for all 26 annual Physics prizes from 2000–2025. Approximately 15–20% had discovery-to-award lags of ten years or less, 35% had lags of 10–25 years, and 45–50% had lags above 25 years; the median was roughly 30 years. These are award-lag frequencies, not annual selection chances: the number of eligible discoveries in each age band is unknown ([timing premise](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

I translate the bin midpoints into relative readiness weights of 0.50, 1.00 and 0.475/0.350. I take their square roots to limit an inference drawn from approximate bins without candidate-pool denominators. Where both prediction and realization anchors exist, I take the geometric mean. This gives maturity factors of 1.079 for simulators, 1.165 for error correction, 1.000 for topological insulators, and 1.165 for OLEDs and CMB theory. Timing enters once, before the profile distribution is normalized. OLED maturity follows its supplied 1998 anchor; the 2012 TADF extension does not restart that clock ([timing calculation](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

The stipulated Medicine outcome of 5 October 2026 is one observation from another committee. I use its optogenetics example to increase the discovery component from 38% to 40% and reduce translation from 5% to 3%. It also motivates checking original-paper credit and keeping recent recognition bonuses small. It supplies no evidence that a particular physics field is due ([Medicine premise and weight change](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

Individual research-work samples and publication windows are below. Collaborators' samples overlap; I do not sum them as independent evidence ([supplied coverage](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

| Option | Named-person sample sizes and publication windows |
|---|---|
| Simulators | Bloch: 180, 1997–2021; Cirac: 567, 1990–2021; Zoller: 507, 1977–2021 |
| Error correction | Preskill: 129, 1979–2021; Shor: 160, 1984–2021; Kitaev: 53, 1991–2021 |
| Topological insulators | Mele: 229, 1976–2021; Kane: 127, 1988–2021; Molenkamp: 451, 1981–2021 |
| OLEDs | Adachi: 790, 1988–2021; Thompson: 452, 1983–2021; Forrest: 857, 1978–2021 |
| CMB theory | Efstathiou: 414, 1980–2021; Bond: 314, 1975–2021 |

My aggregation rule is 75% of the named people's mean plus 25% of their maximum. It rewards team depth without rewarding an option merely for naming more people. Each person's career score uses the supplied historical-reference ranks: 40% median impact, 30% top-10% share and 30% top-1% share. “Higher than all” becomes 1.00. Discovery scores use 70% mean anchor impact, 20% mean anchor Foundation share and 10% mean impact of unique relevant defining works. Shared papers count once. CMB's missing Foundation share is imputed at 0.77, the median of the six other observed anchor values; missing metadata is not negative evidence ([aggregation and inputs](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

The scientific score is 45% career impact, 40% discovery work, 10% textbook reach, 3% translation and 2% collaboration. For supporting counts, I pool the supplied option mean and maximum in the same 75:25 proportions and use \(h(x,k)=\min(1,\ln(1+x)/\ln(1+k))\). Textbook reach equally weights works cited by books and distinct citing books, with saturation scales of 400 and 2,000. Translation weights citing inventions 80% and own patents 20%, with scales of 300 and 3. Collaboration uses distinct listed Nobel coauthors, transformed as \(\min(1,\ln(1+n)/\ln(7))\), then pooled across people. Disruption receives no separate weight ([complete scoring rule](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

All down-weightings are explicit. Thompson's career component receives a factor of 0.97 for his estimated birth year and medium attribution confidence; his confirmed anchor is unchanged. The Stefan Hell collaboration entry in each simulator profile receives 0.50 as a narrow precaution for the repeated cross-field attribution, not as proof of an error. Their career and discovery evidence remains intact. Every other reliability factor is 1.00. Kitaev's 53 works receive no small-sample penalty, and no selected discovery work falls after 2018. Zoller's unmeasured Hofstadter paper is included qualitatively but omitted from numerical averages, not assigned zero ([reliability decisions](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

The profile evidence behind each option is:

- **Simulators:** exceptional careers across the whole trio, including Bloch's 50% top-1% work share, plus strong textbook reach. Numerical anchors are the 1998 cold-boson proposal and 2002 Mott-transition realization. Relevant supporting works are controlled collisions (1999), high-temperature superfluidity (2002), synthetic magnetic fields (2003), Tonks–Girardeau gases (2004), atom-resolved imaging (2010), and many-body localization (2015). This is the strongest balanced scientific package ([profiles and relevant works](sandbox:/mnt/data/nobel_physics_2026_audit.json)).
- **Error correction:** Shor's 1995 memory-protection anchor has Foundation share 0.88, the highest supplied anchor value. Kitaev adds an exceptional career profile, while Preskill adds reliability, encoding and threshold work. Relevant papers are Shor's 1995/1996 codes; Preskill's 1998 reliability, 2001 oscillator encoding and 2006 threshold work; and Kitaev's 1997 error-correction, 2003 anyon fault-tolerance and supporting 2006 anyon-model papers. Shor's factoring algorithm is excluded from discovery evidence, but remains within his career profile ([profiles and relevant works](sandbox:/mnt/data/nobel_physics_2026_audit.json)).
- Topological insulators: Kane's career profile is outstanding; Mele and Molenkamp score lower against the reference cohort. The 2005 prediction and 2007 HgTe realization are strong numerical anchors, with Foundation shares of 0.81 and 0.79. The Z2 classification, three-dimensional-insulator, nonlocal-transport and strained-HgTe surface-state papers are also relevant. Discovery evidence is stronger than the team's average career ranking ([profiles and relevant works](sandbox:/mnt/data/nobel_physics_2026_audit.json)).
- OLEDs: the 1998 phosphorescent-emission anchor is mature and consequential. Relevant follow-ups are efficient green devices (1999), near-unity internal efficiency (2001), and delayed-fluorescence mechanisms and devices (2009/2012). Career-impact comparisons are less exceptional than those of the leading options. The enormous invention and patent footprint helps only in the small, saturated translation component ([profiles and relevant works](sandbox:/mnt/data/nobel_physics_2026_audit.json)).
- CMB theory: both researchers have median impact 0.98 and exceptionally strong reference-cohort career ranks. Relevant works are the 1984 anisotropy anchor, 1987 fluctuation statistics, 1992 COBE interpretation and 1998 power-spectrum estimation. Strong textbook reach and mature, field-enabling theory support its probability; low patent activity has little influence ([profiles and relevant works](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

I then apply only these secondary relative-weight factors. They are judgments, not measured award probabilities:

- Simulators: **1.20**. The primary announcement dated 2 October 2026 confirms Bloch's Wolf Prize with Jun Ye and directly connects Bloch's contribution to optical-lattice simulation. The bonus is limited because recognition repeats much of the profile evidence ([LMU announcement](https://www.physik.lmu.de/en/latest-news/news-overview/news/prestigious-honor-2026-wolf-prize-awarded-to-immanuel-bloch-403eeaa3.html)).
- Error correction: **1.10**. The below-threshold surface-code-memory paper, published online 9 December 2024 and corrected 28 April 2026, adds experimental validation. The updated article retains the qualitative memory result, not a claim of completed practical fault-tolerant computation. I use no performance-sensitive statistic ([updated primary paper](https://www.nature.com/articles/s41586-024-08449-y)).
- Topological insulators: 1.10 for specific Breakthrough recognition, multiplied by 0.95 for scientific adjacency to the earlier topology Nobel, giving **1.045**. The discoveries are distinguishable, so the overlap penalty is small ([2019 recognition](https://breakthroughprize.org/Laureates/1/L3829); [2016 Nobel motivation](https://www.nobelprize.org/prizes/physics/2016/press-release/)).
- OLEDs: 1.08. Clarivate's 17 September 2026 Physics selection names the exact trio and PHOLED/TADF contribution. It supports disciplinary fit, but its citation-based selection is correlated with the main evidence ([Clarivate announcement](https://clarivate.com/news/clarivate-reveals-citation-laureates-2026-recognizing-transformative-scientific-breakthroughs/)).
- CMB theory: 1.10 for the specific Shaw recognition, multiplied by 0.80 for overlap with Peebles's previously rewarded foundations, giving 0.88. The overlap is real; treating the Bond–Efstathiou contribution as already fully rewarded is too strong ([2025 Shaw explanation](https://260105-archive.wp-admin.shawprize.org/laureates/2025-astronomy/); [2019 Nobel scientific background](https://www.nobelprize.org/uploads/2019/10/advanced-physicsprize2019-3.pdf)).

All other secondary factors are 1.00. There is no field-rotation, geographical, symposium or market adjustment. The final calculation is

$$
P_i=\frac{[\exp(8S_i)M_i f_i]^{1/1.15}}{\sum_j[\exp(8S_j)M_j f_j]^{1/1.15}}.
$$

Here \(S_i\) is the scientific score, \(M_i\) the single maturity factor, and \(f_i\) the secondary factor. The profile-only column sets every \(f_i=1\). Both distributions receive the same common temperature of 1.15 once, after all factors. This modestly reduces concentration; no uniform floor is mixed in. The coefficients are judgmental, not fitted ([calculation audit](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

| Discovery | Scientific score | Maturity factor | Profiles only, including timing | Secondary factor | Submitted |
|---|---:|---:|---:|---:|---:|
| Optical-lattice simulators | 0.937 | 1.079 | 25% | 1.200 | 28% |
| Quantum error correction | 0.916 | 1.165 | 22% | 1.100 | 23% |
| Topological insulators | 0.850 | 1.000 | 12% | 1.045 | 12% |
| Efficient OLEDs | 0.857 | 1.165 | 15% | 1.080 | 15% |
| CMB-fluctuation theory | 0.935 | 1.165 | 25% | 0.880 | 22% |

Displayed percentages are rounded; the full-precision distributions each sum to one ([exact distributions](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

For the leading three discoveries, my expected laureate sets are secondary judgments based on anchor authorship, not extra constraints on resolution:

- Simulators: Immanuel Bloch, J. Ignacio Cirac and Peter Zoller. Cirac and Zoller are authors of the theory anchor; Bloch is an author of the realization. First authors Dieter Jaksch and Markus Greiner are substantial alternatives ([theory authors](https://arxiv.org/abs/cond-mat/9805329); [2002 experimental authors](https://doi.org/10.1038/415039a)).
- Error correction: Peter Shor, Andrew Steane and Alexei Kitaev. Their original code and fault-tolerance papers support this set. A threshold-proof emphasis would strengthen Preskill or Gottesman instead ([Shor anchor](https://doi.org/10.1103/PhysRevA.52.R2493); [Steane original](https://link.aps.org/doi/10.1103/PhysRevLett.77.793); [Kitaev original](https://arxiv.org/abs/quant-ph/9707021)).
- CMB theory: John Richard Bond and George Efstathiou. Both the anisotropy and statistics anchors have this two-author set ([1984 authorship](https://ntrs.nasa.gov/citations/19850034850); [1987 authorship](https://academic.oup.com/mnras/article/226/3/655/1034894)).

## What's non-obvious
Error correction is not a young discovery merely because convincing below-threshold hardware arrived recently. The specified award is for the old codes and fault-tolerance foundations. The experiment adds validation rather than resetting the maturity clock. Equally, an omitted anchor author winning does not make a discovery option lose: this question matches the motivation, not the proposed laureate list ([discovery and resolution premises](sandbox:/mnt/data/nobel_physics_2026_audit.json); [experimental evidence](https://www.nature.com/articles/s41586-024-08449-y)).

The strongest counterweight to dismissing CMB theory as “already awarded” is that Shaw recognized Peebles's foundations and later recognized Bond and Efstathiou's precision-prediction framework separately. That does not bind the Nobel committee. It does show an awardable distinction within overlapping science, which supports a moderate overlap discount rather than a blanket exclusion ([Peebles's 2004 Shaw explanation](https://www.shawprize.org/laureates/2004-astronomy/); [Bond–Efstathiou's 2025 explanation](https://260105-archive.wp-admin.shawprize.org/laureates/2025-astronomy/)).

## Uncertainties
The missing evidence is the committee's shortlist, its preferred discovery boundaries, and the candidate-pool denominators needed to turn award-lag frequencies into selection hazards. Author lists establish credit claims, not a unique three-person allocation. The model's weights and secondary multipliers remain judgment calls; the profiles themselves are accepted premises, not independently reconstructed measurements ([limitations](sandbox:/mnt/data/nobel_physics_2026_audit.json)).

Across 243 model variants changing career weight, pooling, score discrimination, temperature and maturity strength, simulator probabilities range from 24% to 34.0%, error correction from 21% to 25%, CMB from 19% to 26%, OLEDs from 11% to 18%, and topological insulators from 7% to 16%. These are model-sensitivity ranges, not statistical confidence intervals, and they hold secondary factors fixed. The JSON decimals preserve the calculation, not committee-level certainty at that precision ([sensitivity results](sandbox:/mnt/data/nobel_physics_2026_audit.json)).