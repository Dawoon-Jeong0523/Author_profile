# Chemistry 2026: the treatment and its comparison forecasts

Three Preseen runs, one each, on 6 October 2026, on the same question: 30 discoveries (the v2 list), each with the living people it names, no "Other". **The treatment is the main result** (profile cards with the patents tied to each discovery as the main evidence; arm `main3` in the run files); the demographic forecast adds the demographics of past laureates to the treatment's notes, the control has no notes at all. Prompts and cards: [README](../../../README.md#chemistry-announced-7-october). Probabilities in %; differences of about one point are within the run-to-run spread.

## The runs

| Forecast | Notes given to the forecaster | Time (UTC) | Top 3 (discovery — named people, probability) | Max | Entropy (bits; uniform 4.91) | Preseen |
|---|---|---|---|---:|---:|---|
| **Treatment** | profile cards with the patents tied to the discovery as the main evidence, every card measure important; Chemistry timing base rate; Medicine and Physics 2026 outcomes | 22:03–22:36 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.9**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **8.6**<br>dye-sensitized solar cells — Michael Grätzel, **8.4** | 8.9 | 4.58 | [result](https://preseen.com/q/urrByOH0UlbPnAcF-Kk7YA) |
| Demographic | the treatment's notes + the demographics of the 2000–2025 Chemistry laureates and the 2026 laureates, with a demographic factor of 0.5–2 per option | 22:07–22:40 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.8**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **6.5**<br>dye-sensitized solar cells — Michael Grätzel, **6.2** | 8.8 | 4.72 | [result](https://preseen.com/q/IRgKh66nV-BgnQslZ6oM0A) |
| Control | none | 19:47–20:21 | massively parallel sequencing-by-synthesis of DNA — Shankar Balasubramanian, David Klenerman, **17.3**<br>solid-state perovskite solar cells — Henry J. Snaith, Tsutomu Miyasaka, Nam-Gyu Park, **7.9**<br>controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, **6.2** | 17.3 | 4.49 | [result](https://preseen.com/q/tV5NqBF_m70rlHecLi8aVg) |

## Agreement with the treatment

- control vs treatment: Spearman 0.32, mean |difference| 2.31 points per option
- demographic vs treatment: Spearman 0.87, mean |difference| 0.73 points per option

## All 30 options

Sorted by the treatment.

| # | Discovery | Named people | Treatment | Demographic | Control |
|---:|---|---|---:|---:|---:|
| 1 | the development of mass-spectrometry-based proteomics | John R. Yates III, Matthias Mann, Ruedi Aebersold | **8.9** | 8.8 | 2.8 |
| 2 | the development of self-assembled monolayers on solid surfaces | David L. Allara, Ralph G. Nuzzo, George M. Whitesides | **8.6** | 6.5 | 4.7 |
| 3 | the invention of dye-sensitized solar cells | Michael Grätzel | **8.4** | 6.2 | 0.6 |
| 4 | the development of palladium-catalyzed carbon-heteroatom bond formation | Stephen L. Buchwald, John F. Hartwig | **5.9** | 4.2 | 4.7 |
| 5 | the development of nanopore methods for single-molecule analysis and sequencing of nucleic acids | Hagan Bayley, David W. Deamer, Daniel Branton | **5.9** | 4.3 | 2.4 |
| 6 | the expansion of the genetic code to incorporate unnatural amino acids into proteins | Peter G. Schultz, Jason W. Chin | **5.6** | 5.0 | 2.3 |
| 7 | the discovery of the nuclear receptor superfamily of ligand-regulated transcription factors | Ronald M. Evans | **5.0** | 5.0 | 1.4 |
| 8 | the development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids | Pieter R. Cullis | **4.1** | 3.7 | 4.6 |
| 9 | the development of controlled radical polymerization | Krzysztof Matyjaszewski, Mitsuo Sawamoto | **3.8** | 4.0 | 6.2 |
| 10 | the development of massively parallel sequencing-by-synthesis of DNA | Shankar Balasubramanian, David Klenerman | **3.5** | 4.9 | 17.3 |
| 11 | the development of base editing and prime editing for precise genome editing | David R. Liu | **3.4** | 3.5 | 3.6 |
| 12 | the discovery and development of solid-state perovskite solar cells | Henry J. Snaith, Tsutomu Miyasaka, Nam-Gyu Park | **3.3** | 3.3 | 7.9 |
| 13 | the discovery and development of semiconductor photocatalysis for water splitting | Akira Fujishima, Kazunari Domen | **3.1** | 2.5 | 1.7 |
| 14 | their discoveries of chemical communication in bacteria | Bonnie L. Bassler, E. Peter Greenberg | **3.0** | 2.2 | 2.2 |
| 15 | the development of programmable and chemoenzymatic synthesis of complex carbohydrates and glycoproteins | Chi-Huey Wong | **3.0** | 2.8 | 3.2 |
| 16 | the discovery of targeted protein degradation by small molecules that redirect ubiquitin ligases | Craig M. Crews, Raymond J. Deshaies | **2.8** | 3.2 | 3.4 |
| 17 | the development of phosphoramidite chemistry for automated DNA synthesis | Marvin H. Caruthers | **2.8** | 3.0 | 2.8 |
| 18 | chemical-genetic methods to study protein kinases and the discovery of covalent inhibitors of oncogenic KRAS | Kevan Shokat | **2.7** | 2.7 | 1.8 |
| 19 | the development of dye-sensitized and perovskite solar cells | Michael Grätzel, Henry J. Snaith, Tsutomu Miyasaka | **2.6** | 2.1 | 0.9 |
| 20 | the development of efficient organic light-emitting diodes | Ching W. Tang, Steven A. Van Slyke | **2.0** | 2.6 | 2.7 |
| 21 | the development of transition-metal-catalyzed C-H functionalization reactions | John F. Hartwig, Robert G. Bergman | **1.8** | 1.8 | 3.3 |
| 22 | the discovery of molecular chaperones that assist protein folding in the cell | Arthur L. Horwich, F. Ulrich Hartl | **1.7** | 3.0 | 4.7 |
| 23 | the development of DNA origami and programmable self-assembly of DNA nanostructures | Paul W. K. Rothemund, William M. Shih, Hao Yan | **1.6** | 1.8 | 1.4 |
| 24 | the development of chemical methods for the synthesis and massively parallel sequencing of DNA | Shankar Balasubramanian, David Klenerman, Marvin H. Caruthers | **1.5** | 1.9 | 1.3 |
| 25 | the development of accurate exchange-correlation functionals that made density functional theory the workhorse of computational chemistry | John P. Perdew | **1.4** | 2.9 | 1.7 |
| 26 | the development of ab initio molecular dynamics | Michele Parrinello, Roberto Car | **1.4** | 2.9 | 2.8 |
| 27 | the isolation of stable carbenes and the development of N-heterocyclic carbenes as ligands in catalysis | Anthony J. Arduengo III, Guy Bertrand, Wolfgang A. Herrmann | **0.9** | 2.6 | 1.2 |
| 28 | the development of atomic layer deposition | Tuomo Suntola | **0.6** | 1.0 | 1.4 |
| 29 | foundational contributions to the theory and understanding of proton-coupled electron transfer | Sharon Hammes-Schiffer, Thomas J. Meyer | **0.6** | 1.1 | 1.2 |
| 30 | pioneering work on electron transfer in proteins | Harry B. Gray | **0.3** | 0.7 | 4.0 |
