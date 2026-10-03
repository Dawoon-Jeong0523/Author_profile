# Committee review — Chemistry 2026

Generated 2026-10-01T20:15:11+00:00 by `committee.py aggregate --field chemistry` from `ballots.jsonl`. Every merge is listed below with its reason. Option = top-K discovery; score = normalized Borda (each model contributes equally).

## Ballots

| model | valid | missing | reported model(s) | ballots with warnings |
|---|---|---|---|---|
| claude-opus-5-5 | 8 | 0 | claude-opus-5-5 | 1 |
| gpt-5.5-2026-04-23 | 8 | 0 | gpt-5.5-2026-04-23 | 0 |
| gemini-3.1-pro-preview | 8 | 0 | gemini-3.1-pro-preview | 0 |

Warnings: A / organic chemistry: rank 1: rationale has 3 sentences

## Candidate list (top 12 + Other)

| # | option | score | models | personas | ballots | A | O | G | consensus |
|---|---|---|---|---|---|---|---|---|---|
| 1 | for the development of controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo | 8.625 | 3 | 8 | 20 | 3.250 | 3.125 | 2.250 | cross-model consensus |
| 2 | for the development of massively parallel sequencing-by-synthesis of DNA — David Klenerman, Shankar Balasubramanian, Pascal Mayer | 8.625 | 3 | 8 | 19 | 2.250 | 3.000 | 3.375 | cross-model consensus |
| 3 | for the discovery and development of solid-state perovskite solar cells — Henry J. Snaith, Nam-Gyu Park, Tsutomu Miyasaka | 4.250 | 3 | 8 | 13 | 0.875 | 2.375 | 1.000 | cross-model consensus |
| 4 | for the development of phosphoramidite chemistry for automated DNA synthesis — Marvin H. Caruthers, Serge L. Beaucage, Mark D. Matteucci | 3.250 | 3 | 4 | 6 | 0.500 | 2.500 | 0.250 | cross-model consensus |
| 5 | for the development of transition-metal-catalyzed C-H functionalization reactions — John F. Hartwig, Jin-Quan Yu, Robert G. Bergman | 2.500 | 2 | 5 | 6 | 0.000 | 1.500 | 1.000 |  |
| 6 | for the development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids — Pieter R. Cullis, Robert S. Langer, Kazunori Kataoka | 2.375 | 2 | 8 | 10 | 2.125 | 0.000 | 0.250 |  |
| 7 | for the discovery of targeted protein degradation by small molecules that redirect ubiquitin ligases — Craig M. Crews, Raymond J. Deshaies, Stuart L. Schreiber | 1.875 | 3 | 5 | 6 | 1.125 | 0.250 | 0.500 | cross-model consensus |
| 8 | for the discovery of molecular chaperones that assist protein folding in the cell — Arthur L. Horwich, F. Ulrich Hartl | 1.750 | 2 | 2 | 3 | 1.250 | 0.000 | 0.500 |  |
| 9 | for the development of nanopore methods for single-molecule analysis and sequencing of nucleic acids — David W. Deamer, Hagan Bayley, Daniel Branton | 1.625 | 2 | 3 | 4 | 1.125 | 0.500 | 0.000 |  |
| 10 | for the development of ab initio molecular dynamics — Michele Parrinello, Roberto Car | 1.500 | 3 | 3 | 4 | 0.125 | 0.125 | 1.250 | cross-model consensus |
| 11 | for the development of efficient organic light-emitting diodes — Ching W. Tang, Steven A. Van Slyke, Mark E. Thompson | 1.125 | 2 | 4 | 4 | 0.000 | 0.500 | 0.625 |  |
| 12 | for the development of DNA origami and programmable self-assembly of DNA nanostructures — Paul W. K. Rothemund, William M. Shih, Hao Yan | 1.125 | 2 | 2 | 3 | 0.375 | 0.000 | 0.750 |  |
| 13 | Other | | | | | | | | |

A / O / G = normalized points from A = claude-opus-5-5, O = gpt-5.5-2026-04-23, G = gemini-3.1-pro-preview.

## Flags (top options)

- #1: 5 people named across nominations; shown: top 3; also: Graeme Moad (1.00), San H. Thang (0.88)
- #5: 4 people named across nominations; shown: top 3; also: Melanie S. Sanford (0.88)
- #7: 7 people named across nominations; shown: top 3; also: Gerald R. Crabtree (0.62), Hiroshi Handa (0.25), Alessio Ciulli (0.12), Kathleen M. Sakamoto (0.12)
- #9: 4 people named across nominations; shown: top 3; also: Mark Akeson (0.50)
- #11: 4 people named across nominations; shown: top 3; also: Chihaya Adachi (0.12)
- #12: 5 people named across nominations; shown: top 3; also: Chad A. Mirkin (0.38), Peng Yin (0.38)

Deceased people are only detected for Nobel laureates (PrizeAtlas death_date) and through `merges.yaml` person_notes; every name in the top options still needs a check that the person is living.

## Merges

### Automatic: nominations that share a person (first initial + surname)

- **option 1** (20 nominations; shared: e rizzardo, g moad, k matyjaszewski, m sawamoto, s thang)
  - `anthropic/nanophysics/r1/#2`: for the development of controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `anthropic/organic-chemistry/r1/#1`: for the development of controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `anthropic/physical-chemistry/r1/#1`: for the development of controlled/living radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `anthropic/inorganic-and-structural-chemistry/r1/#3`: for the discovery of transition-metal-catalysed controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `anthropic/molecular-physics/r1/#2`: for the development of controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Graeme Moad
  - `anthropic/theoretical-chemistry/r1/#1`: for the development of controlled/living radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `openai/nanophysics/r1/#2`: for the development of reversible-deactivation radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, San H. Thang
  - `openai/medical-biochemistry/r1/#2`: for the development of reversible-deactivation radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Graeme Moad
  - `openai/organic-chemistry/r1/#3`: for the development of controlled radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo
  - `openai/physical-chemistry/r1/#4`: for the development of reversible-deactivation radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo
  - `openai/inorganic-and-structural-chemistry/r1/#2`: for the development of reversible-deactivation radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo
  - `openai/molecular-physics/r1/#3`: for the development of reversible-deactivation radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo
  - `openai/biochemistry/r1/#4`: for the development of reversible-deactivation radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo
  - `openai/theoretical-chemistry/r1/#3`: for the development of reversible-deactivation radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto, San H. Thang
  - `gemini/nanophysics/r1/#5`: for the discovery and development of atom transfer radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `gemini/organic-chemistry/r1/#2`: for the development of controlled and living radical polymerization methods — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo
  - `gemini/physical-chemistry/r1/#4`: for the development of atom transfer radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `gemini/inorganic-and-structural-chemistry/r1/#1`: for the development of controlled/living radical polymerization methods — Krzysztof Matyjaszewski, Mitsuo Sawamoto, Ezio Rizzardo
  - `gemini/molecular-physics/r1/#3`: for the discovery and development of atom transfer radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
  - `gemini/theoretical-chemistry/r1/#3`: for the development of controlled/living radical polymerization — Krzysztof Matyjaszewski, Mitsuo Sawamoto
- **option 2** (19 nominations; shared: d klenerman, p mayer, s balasubramanian)
  - `anthropic/medical-biochemistry/r1/#2`: for the development of sequencing-by-synthesis chemistry enabling massively parallel DNA sequencing — Shankar Balasubramanian, David Klenerman
  - `anthropic/physical-chemistry/r1/#2`: for the development of massively parallel DNA sequencing by reversible-terminator chemistry — Shankar Balasubramanian, David Klenerman
  - `anthropic/inorganic-and-structural-chemistry/r1/#2`: for the development of reversible-terminator chemistry enabling massively parallel DNA sequencing — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `anthropic/biochemistry/r1/#2`: for the development of massively parallel DNA sequencing by synthesis using reversible terminator chemistry — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `anthropic/theoretical-chemistry/r1/#4`: for the development of massively parallel DNA sequencing by synthesis using reversible terminator chemistry — Shankar Balasubramanian, David Klenerman
  - `openai/nanophysics/r1/#1`: for the development of massively parallel sequencing-by-synthesis of DNA — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `openai/medical-biochemistry/r1/#3`: for the development of high-throughput DNA sequencing by synthesis — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `openai/organic-chemistry/r1/#5`: for the development of reversible-terminator sequencing-by-synthesis — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `openai/inorganic-and-structural-chemistry/r1/#3`: for the development of sequencing-by-synthesis methods for massively parallel DNA sequencing — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `openai/molecular-physics/r1/#1`: for the development of sequencing-by-synthesis chemistry enabling massively parallel DNA sequencing — Shankar Balasubramanian, David Klenerman
  - `openai/biochemistry/r1/#1`: for the development of massively parallel DNA sequencing by synthesis — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `openai/theoretical-chemistry/r1/#4`: for the development of sequencing-by-synthesis chemistry for massively parallel DNA sequencing — Shankar Balasubramanian, David Klenerman, Pascal Mayer
  - `gemini/nanophysics/r1/#4`: for the development of reversible terminator chemistry for massively parallel DNA sequencing — Shankar Balasubramanian, David Klenerman
  - `gemini/medical-biochemistry/r1/#1`: for the development of next-generation DNA sequencing methodologies — Shankar Balasubramanian, David Klenerman
  - `gemini/physical-chemistry/r1/#1`: for the invention of next-generation DNA sequencing — Shankar Balasubramanian, David Klenerman
  - `gemini/inorganic-and-structural-chemistry/r1/#4`: for the invention of sequencing-by-synthesis on a solid surface — Shankar Balasubramanian, David Klenerman
  - `gemini/molecular-physics/r1/#2`: for the development of next-generation sequencing techniques — Shankar Balasubramanian, David Klenerman
  - `gemini/biochemistry/r1/#1`: for the development of next-generation DNA sequencing technologies — Shankar Balasubramanian, David Klenerman
  - `gemini/theoretical-chemistry/r1/#2`: for the invention of reversible terminator DNA sequencing — Shankar Balasubramanian, David Klenerman
- **option 3** (13 nominations; shared: h snaith, n park, t miyasaka)
  - `anthropic/organic-chemistry/r1/#5`: for the discovery and development of metal halide perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `anthropic/physical-chemistry/r1/#3`: for the discovery of metal halide perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `anthropic/inorganic-and-structural-chemistry/r1/#4`: for the discovery and development of metal halide perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `anthropic/biochemistry/r1/#5`: for the discovery and development of metal halide perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `openai/nanophysics/r1/#4`: for the discovery and development of organometal halide perovskite solar-cell materials — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `openai/medical-biochemistry/r1/#4`: for the discovery and development of metal-halide perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `openai/organic-chemistry/r1/#2`: for the discovery of organometal halide perovskites as efficient photovoltaic materials — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `openai/physical-chemistry/r1/#3`: for the discovery and development of metal-halide perovskites for high-efficiency solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `openai/inorganic-and-structural-chemistry/r1/#4`: for the discovery and development of metal-halide perovskite solar-cell materials — Tsutomu Miyasaka, Henry J. Snaith, Nam-Gyu Park
  - `openai/molecular-physics/r1/#4`: for the discovery and development of metal-halide perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `openai/theoretical-chemistry/r1/#2`: for the discovery and development of organometal halide perovskite solar cells — Tsutomu Miyasaka, Henry J. Snaith, Nam-Gyu Park
  - `gemini/nanophysics/r1/#1`: for the discovery and development of solid-state perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
  - `gemini/physical-chemistry/r1/#3`: for the discovery and development of perovskite solar cells — Tsutomu Miyasaka, Nam-Gyu Park, Henry J. Snaith
- **option 4** (6 nominations; shared: manual only)
  - `anthropic/organic-chemistry/r1/#2`: for the development of the chemical synthesis of DNA by the phosphoramidite method — Marvin H. Caruthers
  - `openai/medical-biochemistry/r1/#1`: for the development of phosphoramidite chemistry for automated DNA synthesis — Marvin H. Caruthers, Serge L. Beaucage
  - `openai/organic-chemistry/r1/#1`: for the development of phosphoramidite chemistry for the automated synthesis of DNA — Marvin H. Caruthers, Serge L. Beaucage
  - `openai/physical-chemistry/r1/#1`: for the development of phosphoramidite chemistry for the automated synthesis of DNA and RNA — Marvin H. Caruthers
  - `openai/inorganic-and-structural-chemistry/r1/#1`: for the development of phosphoramidite chemistry for the chemical synthesis of DNA — Marvin H. Caruthers, Serge L. Beaucage, Mark D. Matteucci
  - `gemini/organic-chemistry/r1/#4`: for the development of chemical methods for the rapid and automated synthesis of DNA — Marvin H. Caruthers
- **option 5** (6 nominations; shared: j hartwig, j yu, m sanford, r bergman)
  - `openai/organic-chemistry/r1/#4`: for the development of transition-metal-catalysed C-H functionalization in organic synthesis — John F. Hartwig, Jin-Quan Yu, Melanie S. Sanford
  - `openai/molecular-physics/r1/#2`: for the development of catalytic carbon–hydrogen bond functionalization — Robert G. Bergman, John F. Hartwig, Jin-Quan Yu
  - `openai/biochemistry/r1/#5`: for the development of carbon-hydrogen bond activation and functionalization — Robert G. Bergman, John F. Hartwig, Jin-Quan Yu
  - `openai/theoretical-chemistry/r1/#1`: for the development of transition-metal-catalyzed C-H functionalization reactions — John F. Hartwig, Melanie S. Sanford, Jin-Quan Yu
  - `gemini/medical-biochemistry/r1/#3`: for the discovery and development of transition-metal catalyzed carbon-hydrogen bond functionalization — Robert G. Bergman, John F. Hartwig
  - `gemini/organic-chemistry/r1/#1`: for the discovery and development of carbon-hydrogen bond activation and functionalization — Robert G. Bergman, John F. Hartwig, Jin-Quan Yu
- **option 6** (10 nominations; shared: p cullis, r langer)
  - `anthropic/nanophysics/r1/#5`: for the development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids — Robert S. Langer, Pieter R. Cullis
  - `anthropic/medical-biochemistry/r1/#3`: for pioneering polymeric systems for controlled release and targeted delivery of drugs — Robert S. Langer, Kazunori Kataoka
  - `anthropic/organic-chemistry/r1/#3`: for the development of lipid nanoparticles for the delivery of nucleic acid therapeutics — Pieter R. Cullis
  - `anthropic/physical-chemistry/r1/#5`: for the development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids — Robert S. Langer, Pieter R. Cullis
  - `anthropic/inorganic-and-structural-chemistry/r1/#5`: for the development of lipid nanoparticle and polymer systems for the delivery of macromolecular drugs — Pieter R. Cullis, Robert S. Langer
  - `anthropic/molecular-physics/r1/#4`: for the development of polymer and lipid nanoparticle systems for the delivery of drugs and nucleic acids — Robert S. Langer, Pieter R. Cullis
  - `anthropic/biochemistry/r1/#3`: for the development of polymeric and lipid nanoparticle systems for the delivery of macromolecular drugs — Robert S. Langer, Pieter R. Cullis
  - `anthropic/theoretical-chemistry/r1/#3`: for the development of polymeric and lipid nanoparticle systems for the delivery of drugs and nucleic acids — Robert S. Langer, Pieter R. Cullis
  - `gemini/inorganic-and-structural-chemistry/r1/#5`: for the development of advanced polymeric and lipid nanoparticle systems for the delivery of macromolecular therapeutics — Pieter R. Cullis, Robert S. Langer
  - `gemini/biochemistry/r1/#5`: for the development of lipid nanoparticles for the delivery of macromolecular therapeutics — Pieter R. Cullis, Robert S. Langer
- **option 7** (6 nominations; shared: c crews, r deshaies)
  - `anthropic/medical-biochemistry/r1/#4`: for the discovery of targeted protein degradation by small molecules that redirect ubiquitin ligases — Craig M. Crews, Raymond J. Deshaies, Hiroshi Handa
  - `anthropic/organic-chemistry/r1/#4`: for the invention of targeted protein degradation by heterobifunctional molecules — Craig M. Crews, Raymond J. Deshaies
  - `anthropic/inorganic-and-structural-chemistry/r1/#1`: for the discovery of chemically induced proximity and its development into targeted protein degradation — Stuart L. Schreiber, Gerald R. Crabtree, Craig M. Crews
  - `openai/nanophysics/r1/#5`: for the development of chemical methods for targeted protein degradation — Craig M. Crews, Raymond J. Deshaies, Kathleen M. Sakamoto
  - `openai/molecular-physics/r1/#5`: for the development of chemically induced targeted protein degradation — Craig M. Crews, Raymond J. Deshaies, Alessio Ciulli
  - `gemini/medical-biochemistry/r1/#2`: for the development of proteolysis targeting chimeras (PROTACs) and targeted protein degradation — Craig M. Crews, Raymond J. Deshaies
- **option 8** (3 nominations; shared: a horwich, f hartl)
  - `anthropic/medical-biochemistry/r1/#1`: for the discovery of molecular chaperones that assist protein folding in the cell — F. Ulrich Hartl, Arthur L. Horwich
  - `anthropic/biochemistry/r1/#1`: for the discovery of chaperone-assisted protein folding in the cell — F. Ulrich Hartl, Arthur L. Horwich
  - `gemini/biochemistry/r1/#2`: for their discoveries concerning the chaperone-mediated folding of proteins — Franz-Ulrich Hartl, Arthur L. Horwich
- **option 9** (4 nominations; shared: d branton, d deamer, h bayley)
  - `anthropic/nanophysics/r1/#1`: for the development of nanopore methods for single-molecule analysis and sequencing of nucleic acids — Hagan Bayley, David W. Deamer, Daniel Branton
  - `anthropic/physical-chemistry/r1/#4`: for the development of nanopore-based single-molecule analysis and sequencing — Hagan Bayley, David Deamer, Daniel Branton
  - `anthropic/biochemistry/r1/#4`: for the development of nanopore-based single-molecule sequencing of nucleic acids — Hagan Bayley, David W. Deamer, Daniel Branton
  - `openai/physical-chemistry/r1/#2`: for the development of nanopore sequencing of nucleic acids — David W. Deamer, Hagan Bayley, Mark Akeson
- **option 10** (4 nominations; shared: m parrinello, r car)
  - `anthropic/theoretical-chemistry/r1/#5`: for the development of ab initio molecular dynamics — Roberto Car, Michele Parrinello
  - `openai/physical-chemistry/r1/#5`: for the development of ab initio molecular dynamics — Roberto Car, Michele Parrinello
  - `gemini/molecular-physics/r1/#1`: for the development of ab initio molecular dynamics — Roberto Car, Michele Parrinello
  - `gemini/theoretical-chemistry/r1/#1`: for the development of ab initio molecular dynamics — Roberto Car, Michele Parrinello
- **option 11** (4 nominations; shared: c tang, s slyke)
  - `openai/biochemistry/r1/#2`: for the development of efficient organic light-emitting diodes — Ching W. Tang, Steven A. Van Slyke, Mark E. Thompson
  - `gemini/organic-chemistry/r1/#3`: for the discovery and development of organic light-emitting diodes — Ching W. Tang, Steven A. Van Slyke
  - `gemini/physical-chemistry/r1/#5`: for discoveries concerning organic light-emitting diodes and thermally activated delayed fluorescence — Ching W. Tang, Chihaya Adachi
  - `gemini/theoretical-chemistry/r1/#5`: for the discovery and development of organic light-emitting diodes — Ching W. Tang, Steven A. Van Slyke
- **option 12** (3 nominations; shared: p rothemund, w shih)
  - `anthropic/nanophysics/r1/#3`: for the development of DNA origami and programmable self-assembly of DNA nanostructures — Paul W. K. Rothemund, William M. Shih, Peng Yin
  - `gemini/nanophysics/r1/#3`: for the development of structural DNA nanotechnology and DNA origami — Paul W. K. Rothemund, Hao Yan, William M. Shih
  - `gemini/inorganic-and-structural-chemistry/r1/#3`: for the invention of structural DNA nanotechnology and spherical nucleic acids — Paul W.K. Rothemund, Chad A. Mirkin
- **option 13** (4 nominations; shared: g whitesides, r nuzzo)
  - `gemini/nanophysics/r1/#2`: for the development of self-assembled monolayers on solid surfaces — George M. Whitesides, Ralph G. Nuzzo, David L. Allara
  - `gemini/medical-biochemistry/r1/#4`: for the pioneering development of microfluidics and soft lithography — George M. Whitesides
  - `gemini/organic-chemistry/r1/#5`: for the development of soft lithography and studies of self-assembled monolayers — George M. Whitesides
  - `gemini/molecular-physics/r1/#5`: for the development of self-assembled monolayers and soft lithography — George M. Whitesides, Ralph G. Nuzzo
- **option 14** (2 nominations; shared: a becke, j perdew)
  - `anthropic/molecular-physics/r1/#3`: for the development of accurate exchange-correlation functionals in density functional theory — Axel D. Becke, John P. Perdew
  - `anthropic/theoretical-chemistry/r1/#2`: for the development of accurate exchange-correlation functionals that made density functional theory the workhorse of computational chemistry — Axel D. Becke, John P. Perdew
- **option 15** (2 nominations; shared: t suntola)
  - `anthropic/nanophysics/r1/#4`: for the invention of atomic layer deposition — Tuomo Suntola
  - `openai/biochemistry/r1/#3`: for the development of atomic layer deposition — Tuomo Suntola, Markku Leskelä, Mikko Ritala
- **option 21** (2 nominations; shared: a arduengo, g bertrand, w herrmann)
  - `openai/medical-biochemistry/r1/#5`: for the isolation of stable carbenes and the development of N-heterocyclic carbenes as ligands in catalysis — Anthony J. Arduengo III, Guy Bertrand, Wolfgang A. Herrmann
  - `openai/theoretical-chemistry/r1/#5`: for the discovery and development of stable carbenes and N-heterocyclic carbene ligands — Anthony J. Arduengo III, Guy Bertrand, Wolfgang A. Herrmann

### Manual (merges.yaml)

- split: `anthropic/organic-chemistry/r1/#2`, `openai/medical-biochemistry/r1/#1`, `openai/organic-chemistry/r1/#1`, `openai/physical-chemistry/r1/#1`, `openai/inorganic-and-structural-chemistry/r1/#1`, `gemini/organic-chemistry/r1/#4` — phosphoramidite chemical synthesis of DNA (Caruthers, Beaucage, Matteucci) is a different discovery from sequencing-by-synthesis (Balasubramanian, Klenerman, Mayer); the two were linked only through the umbrella nomination below.
- split: `anthropic/molecular-physics/r1/#1` — umbrella nomination "chemical methods for the synthesis and massively parallel sequencing of DNA" (Caruthers, Balasubramanian, Klenerman) spans both discoveries; kept as its own option (same rule as the Medicine umbrella).
- split: `gemini/inorganic-and-structural-chemistry/r1/#2` — umbrella nomination "dye-sensitized and perovskite solar cells" (Grätzel, Miyasaka, Snaith) spans two discoveries that also have options of their own; kept as its own option.
- split: `gemini/biochemistry/r1/#3` — palladium-catalysed carbon-heteroatom bond formation (Buchwald, Hartwig) is a different discovery from C-H functionalization (Bergman, Hartwig, Yu, Sanford); linked only through John Hartwig.
- wording from `anthropic/theoretical-chemistry/r1/#3` — the automatic wording came from the single Langer / Kataoka polymer nomination (a tie at 3 points broken by persona order) and does not fit the option's top people (Cullis, Langer); 7 of the 10 nominations describe polymer and lipid nanoparticle delivery together, as this wording does.
- wording from `anthropic/medical-biochemistry/r1/#4` — the automatic wording came from the single "chemically induced proximity" nomination (Schreiber, Crabtree, Crews); the other 5 nominations describe targeted protein degradation (Crews, Deshaies); this wording covers both bifunctional degraders and molecular glues.
- people shown for the option of `anthropic/medical-biochemistry/r1/#4`: Craig M. Crews, Raymond J. Deshaies, Stuart L. Schreiber — tie for the third place (Crabtree = Schreiber, weight 0.625, both from one nomination); Schreiber, named first in that nomination (user decision).
- people shown for the option of `anthropic/nanophysics/r1/#3`: Paul W. K. Rothemund, William M. Shih, Hao Yan — tie for the third place (Mirkin = Hao Yan = Peng Yin, weight 0.375); Mirkin entered through a nomination for spherical nucleic acids, a different discovery; Hao Yan, named in a DNA-origami nomination (user decision).
- alias: "Michael Graetzel" read as "Michael Grätzel"
- alias: "Mark H. Matteucci" read as "Mark D. Matteucci"

### Possibly the same discovery, not merged (for review)

- options 2 and 16 (word overlap 0.86): "for the development of massively parallel sequencing-by-synthesis of DNA" / "for the development of chemical methods for the synthesis and massively parallel sequencing of DNA"
- options 17 and 27 (word overlap 0.80): "for the development of dye-sensitized and perovskite solar cells" / "for the invention of dye-sensitized solar cells"
- options 3 and 17 (word overlap 0.60): "for the discovery and development of solid-state perovskite solar cells" / "for the development of dye-sensitized and perovskite solar cells"
- options 4 and 16 (word overlap 0.44): "for the development of phosphoramidite chemistry for automated DNA synthesis" / "for the development of chemical methods for the synthesis and massively parallel sequencing of DNA"
- options 3 and 27 (word overlap 0.40): "for the discovery and development of solid-state perovskite solar cells" / "for the invention of dye-sensitized solar cells"

## Per-model top 12 and overlap

- **claude-opus-5-5**: 1; 2; 6; 8; 7; 9; 3; 14; 16; 4; 12; 15 (option numbers of the pooled list; 12 options)
- **gpt-5.5-2026-04-23**: 1; 2; 4; 3; 5; 9; 11; 15; 20; 7; 21; 10 (option numbers of the pooled list; 12 options)
- **gemini-3.1-pro-preview**: 2; 1; 10; 3; 5; 13; 12; 11; 7; 8; 17; 18 (option numbers of the pooled list; 12 options)

| pair | Jaccard of top-12 sets |
|---|---|
| A–O | 0.41 |
| A–G | 0.33 |
| O–G | 0.41 |

Top 12: 6 cross-model consensus (nominated by all three models), 0 single-model.

## Leave-one-out stability

Options of the top 12 that change when one persona (all its ballots) or one model is dropped and the list is recomputed (merges fixed).

| dropped | options changed |
|---|---|
| persona: nanophysics | 1 |
| persona: medical biochemistry | 0 |
| persona: organic chemistry | 1 |
| persona: physical chemistry | 1 |
| persona: inorganic and structural chemistry | 1 |
| persona: molecular physics | 0 |
| persona: biochemistry | 2 |
| persona: theoretical chemistry | 1 |
| model: claude-opus-5-5 | 1 |
| model: gpt-5.5-2026-04-23 | 2 |
| model: gemini-3.1-pro-preview | 3 |
