# SPEC: control vs cards as the main evidence, 30 options without "Other" (2026 Physics)

Asked for on 5 October 2026. Every step is recorded in `LOG.md`.

## Design

- Field: physics only. Two new private questions with the same definition: `control` (no notes) and `treat`. One run
  per arm, in a random order (`run --arms control treat --reps 1`).
- Question: the 30 options of `../convergence_2026/results/options_physics.json` (committee options + convergence
  signals), no "Other". Title as before; the description and resolution criteria say the forecast is conditional on
  the prize going to one of the listed discoveries (annulled otherwise); when more than one option matches, the option
  that names the awarded discovery most specifically counts.
- `treat` context, in this order:
  1. `instruction/00_instruction.md` with `treatment=assume_true`: the main-evidence note without its "Other" sentence
     (the same file as `../preseen_main_no_other/`).
  2. `cards/physics/`: a copy of `../convergence_2026/cards/physics/` (72 cards, one per person shown in the 30 options,
     "Listed under" the 30-option texts), `00_definitions.md` first, then the cards in the client's seeded order,
     `treatment=consider`. Kurahashi Neilson's and Ken'ichi Nomoto's profiles were run again without the PatentsView
     name search (it linked namesakes' patents).
- Client: `nobel_preseen_exp.py`, an unchanged copy; `run_field.sh physics nobel26-phys-30`.
