# SPEC: cards as the main evidence, 12 options without "Other" (2026 Physics)

Follow-up to `../preseen_cards_main/` (cards as the main evidence), asked for on 5 October 2026. Every step is
recorded in `LOG.md`.

## Design

- Field: physics only (the 2026 prize is announced on 6 October). One run, no control run (the user's choice).
- Question: `../preseen/questions/physics.json` with "Other" removed (12 options). Description and resolution
  criteria say the forecast is conditional on the prize going to one of the listed discoveries; if none matches, the
  question is annulled.
- Context, in this order:
  1. `instruction/00_instruction.md` with `treatment=assume_true`: the main-evidence note of `../preseen_cards_main/`
     with its "Other" sentence removed (first bullet: "Judge each option by the profiles of its named people.").
  2. `cards/physics/`: the cards rebuilt on 3 October (`../preseen/cards/physics/`, refined inventor linking),
     `00_definitions.md` first, then the cards in the client's seeded order, `treatment=consider`. Naoko Kurahashi
     Neilson's card is rebuilt from a profile that adds OpenAlex A5064710180 ("N. Kurahashi", ORCID
     0000-0003-1047-8094, her IceCube record) to A5024594692 (see `../convergence_2026/people/overrides.yaml`).
- Client: `nobel_preseen_exp.py`, an unchanged copy; `run_field.sh physics nobel26-phys-main12`.
