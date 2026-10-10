# Instruction: forecasting the contribution and laureates of the 2026 Nobel Prize in Economic Sciences

Information cutoff: 2026-10-09, before the announcement of the 2026 prize (Monday 12 October 2026, 11:45 CEST at the earliest).

## Goal
For each of the 30 options, give the probability that the 2026 Sveriges Riksbank Prize in Economic Sciences in Memory
of Alfred Nobel recognizes the contribution the option names. Each option is a contribution in the style of an
official motivation with the one to three people most associated with it; the options come from the five fields that
the field forecast rated most likely (note 01). The question has no "Other" option: the forecast is conditional on the
prize going to one of the listed contributions, so the probabilities sum to 100 %.

## The notes
- 01: the field forecast. Use the rescaled field probabilities as the starting weight of each field's candidates as a
  group; move a field's total away from it only for stated reasons about its candidates.
- 11-15: the candidates of each field with the people (stated years of birth) and the defining works. Judge the
  importance, maturity and influence of each contribution from its defining works and your own knowledge of them, and
  mark what comes from your own knowledge.
- 03: the prizes already awarded. A contribution that is the same as, or a re-labelling of, an awarded one is
  unlikely; weigh the overlap of each candidate with recent prizes, including prizes in other fields.
- 21-25: the support and reasoning of a simulated committee (personas of the 2026 members on three language models).
  Treat it as one input on how the contributions might be seen, including the reservations it records; it is not
  evidence of the real committee's views, and its scores are not probabilities: do not copy them.
- 02: the age record. A person's age matters mostly at the extremes; the prize is never awarded posthumously and
  co-laureates are usually of one generation.

## Eligibility
The prize goes to at most three living people; previous laureates and sitting members of the 2026 committee cannot
be awarded. The notes flag people named by the committee who cannot be awarded and people aged 85 or more. The
living status of every person in the options was screened on Wikidata before submission; people named by the committee
who have died are noted in the candidate notes and are not part of the options.

## Required output
For each option: the probability, and the main grounds for and against it (contribution and its maturity, overlap with
awarded prizes, the field's weight, the people and their ages). Report the field totals of your distribution next to
the rescaled field forecast of note 01 and explain every field that moves by more than five percentage points. The
question resolves by contribution: the people named in an option need not match the laureates exactly.
