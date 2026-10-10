# What the paper reports, and the limits of using it [P, D]

Information cutoff: 2026-10-09. Source: Peter J. Dolton and Richard S. J. Tol, "The Process and Dynamics of the Nobel
Memorial Prize in Economics, 1969-2025", arXiv:2603.20767v1, 21 March 2026 (Table 2 p. 34, Table B.7 p. 50, Table
E.12 pp. 72-73, pp. 16-21). Figures below were read from the paper on 10 October 2026.

## Findings on the field [P]
- Field-level logit, 14 fields x 57 years = 798 field-years. With the first-order transition matrix included
  (estimated separately for 1969-1994, when Lindbeck was on the committee, and 1995-2025), the consolidated model
  keeps: the number of candidates in the field (19.8, p < 0.001), the transition probability (75.8, p < 0.001), the
  years since the field last won (0.058, p < 0.01) and a time trend (0.025, p < 0.05). Not significant: citations to
  the most cited paper in the field, total citations, proximity to the committee, the number of previous prizes in
  the field, whether the field has never won, whether the field won in the previous year (0.07 with the matrix,
  -1.8 without, both insignificant), publications in the last five years.
- Without the transition matrix the number of candidates is the only significant variable; the log-likelihood falls
  from -137 to -198 and the pseudo-R2 from 37 % to 9.1 %.
- The authors read the result as "semi-regular rotation" whose pattern changed after Lindbeck left; larger fields
  (by their candidate pool) win more often; a field kept waiting becomes more likely.
- Individual level (Table 3, E.12): the probability of winning peaks at about 70-71 years of age; having a student
  or a co-author who won matters, broader networks do not; the committee's thematic proximity to a candidate is
  significant only in the 1998-2025 split; citation indicators were significant before 1997 and not after.

## Why these numbers are not 2026 probabilities [P, D]
- The fit is in-sample: it explains 1969-2025. The transition matrix is estimated on the whole period (the window
  that includes the award year itself fits best, which is description, not prediction). Using data through 2025
  for 2026 is right; quoting the fit as validated forecasting skill is not.
- 14 fields give 196 transition cells but there are only 56 consecutive-year transitions; most cells are empty and
  individual paths are sparse (note 00_4 lists the repeats).
- Do not convert coefficients, pseudo-R2, un-normalized transition scores or historical "who should have won" scores
  into 2026 probabilities, and do not move the individual-level regularities (peak age about 71, years since the
  PhD, lineage or co-authorship with laureates) into fixed points for fields.
- Citation results depend on specification, period and pool; do not generalize that citations are meaningless.
- The paper's candidate counts are historical totals over its constructed pool (note 00_6), not the number of
  living, unawarded candidates in 2026.
