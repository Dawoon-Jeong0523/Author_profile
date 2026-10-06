# Chemistry 2026: the Preseen forecasts side by side

Seven runs, one each, on 6 October 2026. Each option is a discovery and the living people it names; v1 and v2 are the same 30 discoveries with different named people, Preseen's list words its discoveries differently (17 of its 30 options matched by hand to 16 v1/v2 discoveries, the other 13 listed at the end). Version codes (C = candidate list, P = prompt, K = cards) as in the [README](../../../README.md#what-changed-between-versions). Probabilities in %; differences of about 1 point are within the run-to-run spread.

## The runs

| Run | List | Prompt | Cards | Time (UTC) | Top 3 (discovery — named people, probability) | Max | Entropy (bits; uniform 4.91) |
|---|---|---|---|---|---|---:|---:|
| **main3** | v2 (C3) | P5: no measure called minor | K1 + K3 patents | 22:03–22:36 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.9**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **8.6**<br>dye-sensitized solar cells — Michael Grätzel, **8.4** | 8.9 | 4.58 |
| demographic | v2 (C3) | P6: P5 + demographic notes | K1 + K3 patents | 22:07–22:40 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.8**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **6.5**<br>dye-sensitized solar cells — Michael Grätzel, **6.2** | 8.8 | 4.72 |
| control | v2 (C3) | P0: no notes | none | 19:47–20:21 | massively parallel sequencing-by-synthesis of DNA — Shankar Balasubramanian, David Klenerman, **17.3**<br>solid-state perovskite solar cells — Henry J. Snaith, Tsutomu Miyasaka, Nam-Gyu Park, **7.9**<br>controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, **6.2** | 17.3 | 4.49 |
| v2 main | v2 (C3) | P3: translation and collaboration minor | K1 | 17:44–19:22 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.7**<br>dye-sensitized solar cells — Michael Grätzel, **8.5**<br>nanopore methods for single-molecule analysis and sequencing of nucleic acids — Hagan Bayley, David W. Deamer, Daniel Branton, **7.9** | 8.7 | 4.49 |
| main2 | v2 (C3) | P4: collaboration minor, patents count | K1 + K3 patents | 21:59–22:36 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.5**<br>nanopore methods for single-molecule analysis and sequencing of nucleic acids — Hagan Bayley, David W. Deamer, Daniel Branton, **6.7**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **6.5** | 8.5 | 4.65 |
| v1 main | v1 (C2) | P3 | K1 | 17:44–18:59 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **9.1**<br>dye-sensitized solar cells — Michael Grätzel, **8.9**<br>nanopore methods for single-molecule analysis and sequencing of nucleic acids — Hagan Bayley, David W. Deamer, Daniel Branton, **6.5** | 9.1 | 4.50 |
| Preseen list | Preseen's own (C4) | P3 | K1 | 17:53–19:12 | flexible organic electronics and electronic skin — Zhenan Bao, **7.7**<br>synthetic gene circuits — James J. Collins, Michael Elowitz, Stanislas Leibler, **7.3**<br>theoretical methods for heterogeneous catalysis on solid surfaces — Jens K. Nørskov, **7.1** | 7.7 | 4.61 |

## Agreement between runs

- v1 vs v2 (same 30 discoveries): Spearman 0.95, mean |diff| 0.51 pp
- Preseen's list: 53% of its probability on the 17 options shared with v1/v2, 47% on its 13 own discoveries; v1 vs Preseen on the 16 shared discoveries: Spearman 0.81, v2 vs Preseen 0.75
- v2 control (same question, no notes) vs v2 main: Spearman 0.14, mean |diff| 2.66 pp; vs v1 main: Spearman 0.15
- v2 main2 (patents on the cards, translation no longer 'minor') vs v2 main: Spearman 0.86, mean |diff| 0.85 pp; vs v2 control: Spearman 0.31
- v2 main3 (patents on the cards, no measure called minor) vs v2 main: Spearman 0.61, mean |diff| 1.30 pp
- v2 demographic arm vs v2 main3 (same notes without the demographic ones): Spearman 0.87, mean |diff| 0.73 pp

## All options

Sorted by main3. People: the v2 lineup (the people named in the v2 runs); the v1 and Preseen-list columns name people only where their lineup differs from v2.

| # | Discovery | People (v2) | main3 | demographic | control | v2 main | main2 | v1 main | People (v1, if different) | Preseen list | People (Preseen list, if different) |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1 | the development of mass-spectrometry-based proteomics | John R. Yates III, Matthias Mann, Ruedi Aebersold | **8.9** | 8.8 | 2.8 | 8.7 | 8.5 | 9.1 |  |  |  |
| 2 | the development of self-assembled monolayers on solid surfaces | David L. Allara, Ralph G. Nuzzo, George M. Whitesides | **8.6** | 6.5 | 4.7 | 7.1 | 6.5 | 5.8 |  | 3.9 | David L. Allara, Ralph G. Nuzzo, Jacob Sagiv |
| 3 | the invention of dye-sensitized solar cells | Michael Grätzel | **8.4** | 6.2 | 0.6 | 8.5 | 5.3 | 8.9 |  |  |  |
| 4 | the development of palladium-catalyzed carbon-heteroatom bond formation | Stephen L. Buchwald, John F. Hartwig | **5.9** | 4.2 | 4.7 | 4.5 | 4.5 | 3.8 |  | 4.7 |  |
| 5 | the development of nanopore methods for single-molecule analysis and sequencing of nucleic acids | Hagan Bayley, David W. Deamer, Daniel Branton | **5.9** | 4.3 | 2.4 | 7.9 | 6.7 | 6.5 |  |  |  |
| 6 | the expansion of the genetic code to incorporate unnatural amino acids into proteins | Peter G. Schultz, Jason W. Chin | **5.6** | 5.0 | 2.3 | 3.2 | 5.1 | 3.7 |  |  |  |
| 7 | the discovery of the nuclear receptor superfamily of ligand-regulated transcription factors | Ronald M. Evans | **5.0** | 5.0 | 1.4 | 5.3 | 5.4 | 5.0 |  |  |  |
| 8 | the development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids | Pieter R. Cullis | **4.1** | 3.7 | 4.6 | 1.8 | 2.6 | 2.0 | Pieter R. Cullis, Robert S. Langer, Kazunori Kataoka | 5.9 | Kazunori Kataoka, Vladimir P. Torchilin, Karen L. Wooley / Robert S. Langer |
| 9 | the development of controlled radical polymerization | Krzysztof Matyjaszewski, Mitsuo Sawamoto | **3.8** | 4.0 | 6.2 | 3.6 | 4.0 | 2.8 | Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo | 4.0 | Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo |
| 10 | the development of massively parallel sequencing-by-synthesis of DNA | Shankar Balasubramanian, David Klenerman | **3.5** | 4.9 | 17.3 | 2.4 | 4.0 | 2.4 | Shankar Balasubramanian, David Klenerman, Pascal Mayer | 3.6 | Shankar Balasubramanian, David Klenerman, Hagan Bayley |
| 11 | the development of base editing and prime editing for precise genome editing | David R. Liu | **3.4** | 3.5 | 3.6 | 5.0 | 3.7 | 5.3 |  | 5.3 |  |
| 12 | the discovery and development of solid-state perovskite solar cells | Henry J. Snaith, Tsutomu Miyasaka, Nam-Gyu Park | **3.3** | 3.3 | 7.9 | 5.2 | 5.2 | 5.7 |  | 5.4 |  |
| 13 | the discovery and development of semiconductor photocatalysis for water splitting | Akira Fujishima, Kazunari Domen | **3.1** | 2.5 | 1.7 | 1.6 | 1.6 | 1.2 |  | 1.4 | Kazunari Domen |
| 14 | their discoveries of chemical communication in bacteria | Bonnie L. Bassler, E. Peter Greenberg | **3.0** | 2.2 | 2.2 | 3.8 | 4.0 | 3.1 |  | 5.4 |  |
| 15 | the development of programmable and chemoenzymatic synthesis of complex carbohydrates and glycoproteins | Chi-Huey Wong | **3.0** | 2.8 | 3.2 | 0.7 | 1.5 | 0.2 |  | 0.6 |  |
| 16 | the discovery of targeted protein degradation by small molecules that redirect ubiquitin ligases | Craig M. Crews, Raymond J. Deshaies | **2.8** | 3.2 | 3.4 | 2.9 | 3.9 | 3.3 | Craig M. Crews, Raymond J. Deshaies, Stuart L. Schreiber |  |  |
| 17 | the development of phosphoramidite chemistry for automated DNA synthesis | Marvin H. Caruthers | **2.8** | 3.0 | 2.8 | 0.7 | 1.8 | 0.7 | Marvin H. Caruthers, Serge L. Beaucage, Mark D. Matteucci | 0.9 |  |
| 18 | chemical-genetic methods to study protein kinases and the discovery of covalent inhibitors of oncogenic KRAS | Kevan Shokat | **2.7** | 2.7 | 1.8 | 0.7 | 2.7 | 0.5 |  |  |  |
| 19 | the development of dye-sensitized and perovskite solar cells | Michael Grätzel, Henry J. Snaith, Tsutomu Miyasaka | **2.6** | 2.1 | 0.9 | 3.3 | 2.0 | 2.5 |  |  |  |
| 20 | the development of efficient organic light-emitting diodes | Ching W. Tang, Steven A. Van Slyke | **2.0** | 2.6 | 2.7 | 0.8 | 1.8 | 3.0 | Ching W. Tang, Steven A. Van Slyke, Mark E. Thompson | 2.0 |  |
| 21 | the development of transition-metal-catalyzed C-H functionalization reactions | John F. Hartwig, Robert G. Bergman | **1.8** | 1.8 | 3.3 | 1.9 | 2.3 | 2.0 | John F. Hartwig, Jin-Quan Yu, Robert G. Bergman | 1.3 | Robert G. Bergman, John E. Bercaw |
| 22 | the discovery of molecular chaperones that assist protein folding in the cell | Arthur L. Horwich, F. Ulrich Hartl | **1.7** | 3.0 | 4.7 | 3.7 | 3.5 | 3.8 |  |  |  |
| 23 | the development of DNA origami and programmable self-assembly of DNA nanostructures | Paul W. K. Rothemund, William M. Shih, Hao Yan | **1.6** | 1.8 | 1.4 | 2.9 | 2.2 | 3.1 |  |  |  |
| 24 | the development of chemical methods for the synthesis and massively parallel sequencing of DNA | Shankar Balasubramanian, David Klenerman, Marvin H. Caruthers | **1.5** | 1.9 | 1.3 | 0.7 | 1.3 | 0.5 |  |  |  |
| 25 | the development of accurate exchange-correlation functionals that made density functional theory the workhorse of computational chemistry | John P. Perdew | **1.4** | 2.9 | 1.7 | 5.8 | 3.7 | 6.4 |  |  |  |
| 26 | the development of ab initio molecular dynamics | Michele Parrinello, Roberto Car | **1.4** | 2.9 | 2.8 | 5.3 | 3.3 | 5.8 |  | 6.0 |  |
| 27 | the isolation of stable carbenes and the development of N-heterocyclic carbenes as ligands in catalysis | Anthony J. Arduengo III, Guy Bertrand, Wolfgang A. Herrmann | **0.9** | 2.6 | 1.2 | 0.7 | 0.9 | 1.0 |  |  |  |
| 28 | the development of atomic layer deposition | Tuomo Suntola | **0.6** | 1.0 | 1.4 | 0.2 | 0.6 | 0.8 | Tuomo Suntola, Markku Leskelä, Mikko Ritala |  |  |
| 29 | foundational contributions to the theory and understanding of proton-coupled electron transfer | Sharon Hammes-Schiffer, Thomas J. Meyer | **0.6** | 1.1 | 1.2 | 0.8 | 0.9 | 0.5 |  | 0.7 | Daniel G. Nocera |
| 30 | pioneering work on electron transfer in proteins | Harry B. Gray | **0.3** | 0.7 | 4.0 | 0.2 | 0.4 | 0.5 | Harry B. Gray, Jay R. Winkler | 1.6 | Harry B. Gray, Jay R. Winkler |
|  | the development of flexible organic electronics and electronic skin |  |  |  |  |  |  |  |  | 7.7 | Zhenan Bao |
|  | the development of synthetic gene circuits |  |  |  |  |  |  |  |  | 7.3 | James J. Collins, Michael Elowitz, Stanislas Leibler |
|  | the development of theoretical methods for heterogeneous catalysis on solid surfaces |  |  |  |  |  |  |  |  | 7.1 | Jens K. Nørskov |
|  | the discovery of phase-separated biomolecular condensates in cellular organization |  |  |  |  |  |  |  |  | 5.0 | Clifford P. Brangwynne, Anthony A. Hyman, Michael K. Rosen |
|  | the development of dendritic polymers |  |  |  |  |  |  |  |  | 4.4 | Jean M. J. Fréchet, Donald A. Tomalia |
|  | the development of ordered mesoporous materials |  |  |  |  |  |  |  |  | 3.3 | Charles T. Kresge, Ryong Ryoo, Galen D. Stucky |
|  | the discovery of cell-free fetal DNA in maternal plasma and its use in noninvasive prenatal testing |  |  |  |  |  |  |  |  | 3.0 | Dennis Lo Yuk-Ming |
|  | the development of catalytic asymmetric epoxidation with chiral salen complexes |  |  |  |  |  |  |  |  | 2.5 | Eric N. Jacobsen |
|  | the development of coordination-driven molecular self-assembly |  |  |  |  |  |  |  |  | 2.2 | Makoto Fujita |
|  | the development of single-atom catalysis |  |  |  |  |  |  |  |  | 2.1 | Tao Zhang |
|  | the development of computational methods for molecular design in solution |  |  |  |  |  |  |  |  | 1.9 | William L. Jorgensen |
|  | the discovery of radical mechanisms in ribonucleotide reductases |  |  |  |  |  |  |  |  | 0.8 | JoAnne Stubbe |
|  | the development of skeletal editing |  |  |  |  |  |  |  |  | 0.1 | Mark Levin, Richmond Sarpong, Bill Morandi |

Preseen-list rows that sum two of its options (polymer delivery and controlled release) name both lineups, separated by /.
