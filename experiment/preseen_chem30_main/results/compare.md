# Chemistry 2026: cards as the main evidence and its comparison forecasts

Five Preseen runs, one each, on 6 October 2026, on the same question: 30 discoveries (the v2 list), each with the living people it names, no "Other". **Cards as the main evidence is the main result** (profile cards with the patents tied to each discovery as the main evidence; arm `main3` in the run files); the demographic forecast adds the demographics of past laureates to its notes; cards as one main source and cards as context keep its reference notes and cards but replace its instruction (one main source) or leave it out (context); the control has no notes at all. Prompts and cards: [README](../../../README.md#chemistry-announced-7-october). Probabilities in %; differences of about one point are within the run-to-run spread.

## The runs

| Forecast | Notes given to the forecaster | Time (UTC) | Top 3 (discovery — named people, probability) | Max | Entropy (bits; uniform 4.91) | Preseen report |
|---|---|---|---|---:|---:|---|
| **Cards as the main evidence** | profile cards with the patents tied to the discovery as the main evidence, every card measure important; Chemistry timing base rate; Medicine and Physics 2026 outcomes | 22:03–22:36 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.9**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **8.6**<br>dye-sensitized solar cells — Michael Grätzel, **8.4** | 8.9 | 4.58 | [PDF](../../../Data/Result/Chemistry/Treatment.pdf) |
| Cards as one main source | the same reference notes and cards; instruction: the profiles are one of the main sources, weighed comparably with prizes, news, predictions and the history of the prize | 00:00–00:31 | massively parallel sequencing-by-synthesis of DNA — Shankar Balasubramanian, David Klenerman, **12.5**<br>mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **11.1**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **8.8** | 12.5 | 4.34 | – |
| Cards as context | the same reference notes and cards; no instruction | 00:00–00:43 | massively parallel sequencing-by-synthesis of DNA — Shankar Balasubramanian, David Klenerman, **22.9**<br>solid-state perovskite solar cells — Henry J. Snaith, Tsutomu Miyasaka, Nam-Gyu Park, **8.1**<br>controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, **6.2** | 22.9 | 4.31 | – |
| Demographic | the notes of cards as the main evidence + the demographics of the 2000–2025 Chemistry laureates and the 2026 laureates, with a demographic factor of 0.5–2 per option | 22:07–22:40 | mass-spectrometry-based proteomics — John R. Yates III, Matthias Mann, Ruedi Aebersold, **8.8**<br>self-assembled monolayers on solid surfaces — David L. Allara, Ralph G. Nuzzo, George M. Whitesides, **6.5**<br>dye-sensitized solar cells — Michael Grätzel, **6.2** | 8.8 | 4.72 | [PDF](../../../Data/Result/Chemistry/Demographic.pdf) |
| Control | none | 19:47–20:21 | massively parallel sequencing-by-synthesis of DNA — Shankar Balasubramanian, David Klenerman, **17.3**<br>solid-state perovskite solar cells — Henry J. Snaith, Tsutomu Miyasaka, Nam-Gyu Park, **7.9**<br>controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, **6.2** | 17.3 | 4.49 | [PDF](../../../Data/Result/Chemistry/Control.pdf) |

## Agreement with cards as the main evidence

- control vs cards as the main evidence: Spearman 0.32, mean |difference| 2.31 points per option
- cards as one main source vs cards as the main evidence: Spearman 0.83, mean |difference| 1.46 points per option
- cards as context vs cards as the main evidence: Spearman 0.53, mean |difference| 2.41 points per option; vs control: Spearman 0.88
- demographic vs cards as the main evidence: Spearman 0.87, mean |difference| 0.73 points per option

## All 30 options

Sorted by cards as the main evidence.

| # | Discovery | Named people | Cards as the main evidence | Cards as one main source | Cards as context | Demographic | Control |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | the development of mass-spectrometry-based proteomics | John R. Yates III, Matthias Mann, Ruedi Aebersold | **8.9** | 11.1 | 4.5 | 8.8 | 2.8 |
| 2 | the development of self-assembled monolayers on solid surfaces | David L. Allara, Ralph G. Nuzzo, George M. Whitesides | **8.6** | 8.8 | 3.8 | 6.5 | 4.7 |
| 3 | the invention of dye-sensitized solar cells | Michael Grätzel | **8.4** | 3.5 | 1.3 | 6.2 | 0.6 |
| 4 | the development of palladium-catalyzed carbon-heteroatom bond formation | Stephen L. Buchwald, John F. Hartwig | **5.9** | 5.7 | 4.4 | 4.2 | 4.7 |
| 5 | the development of nanopore methods for single-molecule analysis and sequencing of nucleic acids | Hagan Bayley, David W. Deamer, Daniel Branton | **5.9** | 3.7 | 2.7 | 4.3 | 2.4 |
| 6 | the expansion of the genetic code to incorporate unnatural amino acids into proteins | Peter G. Schultz, Jason W. Chin | **5.6** | 6.5 | 3.4 | 5.0 | 2.3 |
| 7 | the discovery of the nuclear receptor superfamily of ligand-regulated transcription factors | Ronald M. Evans | **5.0** | 3.0 | 1.3 | 5.0 | 1.4 |
| 8 | the development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids | Pieter R. Cullis | **4.1** | 4.5 | 4.1 | 3.7 | 4.6 |
| 9 | the development of controlled radical polymerization | Krzysztof Matyjaszewski, Mitsuo Sawamoto | **3.8** | 5.4 | 6.2 | 4.0 | 6.2 |
| 10 | the development of massively parallel sequencing-by-synthesis of DNA | Shankar Balasubramanian, David Klenerman | **3.5** | 12.5 | 22.9 | 4.9 | 17.3 |
| 11 | the development of base editing and prime editing for precise genome editing | David R. Liu | **3.4** | 6.0 | 2.2 | 3.5 | 3.6 |
| 12 | the discovery and development of solid-state perovskite solar cells | Henry J. Snaith, Tsutomu Miyasaka, Nam-Gyu Park | **3.3** | 4.3 | 8.1 | 3.3 | 7.9 |
| 13 | the discovery and development of semiconductor photocatalysis for water splitting | Akira Fujishima, Kazunari Domen | **3.1** | 1.1 | 1.6 | 2.5 | 1.7 |
| 14 | their discoveries of chemical communication in bacteria | Bonnie L. Bassler, E. Peter Greenberg | **3.0** | 2.2 | 3.2 | 2.2 | 2.2 |
| 15 | the development of programmable and chemoenzymatic synthesis of complex carbohydrates and glycoproteins | Chi-Huey Wong | **3.0** | 3.7 | 1.8 | 2.8 | 3.2 |
| 16 | the discovery of targeted protein degradation by small molecules that redirect ubiquitin ligases | Craig M. Crews, Raymond J. Deshaies | **2.8** | 2.4 | 3.3 | 3.2 | 3.4 |
| 17 | the development of phosphoramidite chemistry for automated DNA synthesis | Marvin H. Caruthers | **2.8** | 1.6 | 3.2 | 3.0 | 2.8 |
| 18 | chemical-genetic methods to study protein kinases and the discovery of covalent inhibitors of oncogenic KRAS | Kevan Shokat | **2.7** | 1.2 | 1.3 | 2.7 | 1.8 |
| 19 | the development of dye-sensitized and perovskite solar cells | Michael Grätzel, Henry J. Snaith, Tsutomu Miyasaka | **2.6** | 0.9 | 0.4 | 2.1 | 0.9 |
| 20 | the development of efficient organic light-emitting diodes | Ching W. Tang, Steven A. Van Slyke | **2.0** | 1.0 | 2.4 | 2.6 | 2.7 |
| 21 | the development of transition-metal-catalyzed C-H functionalization reactions | John F. Hartwig, Robert G. Bergman | **1.8** | 1.6 | 2.4 | 1.8 | 3.3 |
| 22 | the discovery of molecular chaperones that assist protein folding in the cell | Arthur L. Horwich, F. Ulrich Hartl | **1.7** | 3.9 | 4.0 | 3.0 | 4.7 |
| 23 | the development of DNA origami and programmable self-assembly of DNA nanostructures | Paul W. K. Rothemund, William M. Shih, Hao Yan | **1.6** | 0.8 | 1.2 | 1.8 | 1.4 |
| 24 | the development of chemical methods for the synthesis and massively parallel sequencing of DNA | Shankar Balasubramanian, David Klenerman, Marvin H. Caruthers | **1.5** | 0.9 | 0.4 | 1.9 | 1.3 |
| 25 | the development of accurate exchange-correlation functionals that made density functional theory the workhorse of computational chemistry | John P. Perdew | **1.4** | 0.4 | 1.2 | 2.9 | 1.7 |
| 26 | the development of ab initio molecular dynamics | Michele Parrinello, Roberto Car | **1.4** | 1.0 | 2.1 | 2.9 | 2.8 |
| 27 | the isolation of stable carbenes and the development of N-heterocyclic carbenes as ligands in catalysis | Anthony J. Arduengo III, Guy Bertrand, Wolfgang A. Herrmann | **0.9** | 0.5 | 1.1 | 2.6 | 1.2 |
| 28 | the development of atomic layer deposition | Tuomo Suntola | **0.6** | 0.2 | 1.5 | 1.0 | 1.4 |
| 29 | foundational contributions to the theory and understanding of proton-coupled electron transfer | Sharon Hammes-Schiffer, Thomas J. Meyer | **0.6** | 0.1 | 0.9 | 1.1 | 1.2 |
| 30 | pioneering work on electron transfer in proteins | Harry B. Gray | **0.3** | 1.5 | 3.3 | 0.7 | 4.0 |
