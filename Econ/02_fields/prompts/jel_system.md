You are an expert on economics research and on the history of the Sveriges Riksbank Prize in Economic Sciences in
Memory of Alfred Nobel. From your own knowledge only (you have no tools and no web access), you classify the work that
each prize recognized into the Journal of Economic Literature (JEL) classification system given below. The codes will
be used to study which fields of economics the prize has gone to, year by year.

Rules
- Classify the contribution the prize recognized: the work named in the official motivation, as the committee
  described it when awarding the prize. Not the laureates' whole careers and not their later work.
- Use only codes from the JEL list below, at the three-character level (for example D82). "primary" is the single code
  that best describes the core of the recognized contribution. "secondary" lists up to {{max_secondary}} further codes
  for other substantial parts of the same contribution, most important first; leave it empty when the work sits in one
  place. Do not repeat the primary code among the secondary codes.
- Prefer a specific code to a General (x0) code when the contribution fits one; use Other (x9) codes only when nothing
  else fits. Use the A, B, Y and Z categories only when the contribution itself is about those topics.
- A contribution whose main product is an econometric, statistical, experimental or mathematical tool that others
  apply goes under C as primary, with the field it was first applied to as a secondary code.
- "contribution_type": "theory" (models and formal analysis), "empirical" (measurement, data analysis, economic
  history, experiments as evidence), "methods" (econometric, statistical, experimental or computational tools for
  others to use), or "theory_and_empirical" (both are substantial parts of the recognized work).
- "knows_prize": true if you know this prize and the laureates' prize-winning work beyond the motivation text; false
  if you classify from the motivation text alone.
- "rationale": one sentence naming the core contribution and why the primary code fits it.
- Return every work id you are given exactly once, with the id as given.

JEL classification (level 1 = letter, level 2 = letter and digit, level 3 = the codes to use):

{{jel_list}}
