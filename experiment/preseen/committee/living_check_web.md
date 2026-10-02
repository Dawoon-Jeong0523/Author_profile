# Living check, 2026-10-01 — web verification

Screen: `check_living.py` (Wikidata P569/P570) for every person shown in the three top-12 lists
(`committee/<field>/living_check.csv`). Web checks (WebSearch, 2026-10-01) for every Wikidata death, every no-match or
wrong match, every person moved up to replace a deceased one, and everyone born in or before 1940.

## Deceased (not shown in option texts; `merges.yaml` `deceased`)

| field | option | person | died | sources |
|---|---|---|---|---|
| medicine | 1 GLP-1 | Joel F. Habener | 2025-12-28 | Wikidata Q96637578; https://www.asbmb.org/asbmb-today/people/031626/in-memoriam-joel-habener ; https://laskerfoundation.org/in-memoriam-joel-habener/ |
| medicine | 3 CAR-T | Zelig Eshhar | 2025-07-03 | Wikidata Q18029986; https://lit.eu/the-father-of-car-t-cells-prof-zelig-eshhar-passed-away/ ; https://journals.sagepub.com/doi/10.1177/10430342251393633 |
| physics | 11 aberration-corrected electron optics | Harald Rose | 2026-07-27 | Wikidata Q122014; https://microscopy.org/post/In-Memorium-Harald-Rose ; https://www.physik.tu-darmstadt.de/aktuelles_physik/news_details_125312.en.jsp |

## Checked on the web, living (no death notice found)

| person | why checked | evidence |
|---|---|---|
| Jonathan C. Cohen (medicine 5) | Wikidata matched a 1915–2003 surgeon | UT Southwestern faculty profile and 2026 newsroom items: https://profiles.utsouthwestern.edu/profile/11389/jonathan-cohen.html |
| Mark H. Skolnick (medicine 12) | no Wikidata match | Wikipedia (b. 1946, no death): https://en.wikipedia.org/wiki/Mark_Skolnick |
| Steven A. Rosenberg (medicine 3, replaces Eshhar) | Wikidata matched a psychiatrist | 2026 Tang Prize; NCI staff page: https://ccr.cancer.gov/staff-directory/steven-a-rosenberg |
| Albrecht Karle (physics 7) | no Wikidata match | UW–Madison / WIPAC faculty page, IceCube Upgrade 2026: https://wipac.wisc.edu/people/faculty/albrecht-karle |
| Mark D. Matteucci (chemistry 4; models wrote "Mark H.") | no Wikidata match | no obituary found (ResearchGate: Mark D. Matteucci) |
| Yakir Aharonov (physics 4) | born 1932 | https://en.wikipedia.org/wiki/Yakir_Aharonov |
| Daniel Branton (chemistry 9) | born 1932 | https://en.wikipedia.org/wiki/Daniel_Branton |
| Ravinder N. Maini (medicine 10) | born 1937 | https://en.wikipedia.org/wiki/Ravinder_Maini |
| Alfred Y. Cho (physics 10) | born 1937 | https://en.wikipedia.org/wiki/Alfred_Y._Cho |
| David W. Deamer (chemistry 9) | born 1939 | NAI Fellow 2025: https://news.ucsc.edu/2025/12/nai-fellows-2025/ |
| Marvin H. Caruthers (chemistry 4) | born 1940 | https://en.wikipedia.org/wiki/Marvin_H._Caruthers |

Lotte Bjerre Knudsen (medicine 1, replaces Habener; b. 1964) and Ondrej L. Krivanek (physics 11, replaces Rose; b. 1950):
Wikidata, no date of death. Everyone else: Wikidata, no date of death (the rest of the matches were checked by hand in
the CSVs; same-name mismatches for Jun Ye, Robert S. Langer, Hao Yan and Mark E. Thompson, all younger, were not
web-checked). A "no death notice found" is not proof of life; deaths after 2026-10-01 are not covered.
