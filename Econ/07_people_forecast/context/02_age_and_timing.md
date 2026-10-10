# Age at the award: the record of the 99 laureates, 1969-2025

Information cutoff: 2026-10-09. Age = years from the birth date to the announcement of the prize (four laureates have a
birth year only; their age is approximate to half a year; the Nobel Prize API misdates the 2022 award as 2011, so the
ages of Bernanke, Diamond and Dybvig are taken from the prize year: 68, 68 and 67, not the API's 57, 57 and 56).

- Distribution: median 67 (bootstrap 95 % 64-69), mean 67.3, standard deviation 8.3; the middle
  80 % of laureates were 57-78 years old. Youngest Esther Duflo (2019, 47), oldest
  Leonid Hurwicz (2007, 90). Under 55: 4 of 99; 75 and over: 20; 80 and over: 6 (Leonid Hurwicz 2007 at 90; Lloyd S. Shapley 2012 at 89; Thomas C. Schelling 2005 at 84; Robert B. Wilson 2020 at 83; William Vickrey 1996 at 82; Ronald H. Coase 1991 at 81).
- One peak, not several: a Gaussian mixture prefers 1 component(s) by BIC; skewness +0.34; the mode of the
  density is about 65 (bootstrap 95 % 62-69). Among eventual laureates, the share of the not-yet-awarded who were
  awarded in a given year of age stays under 5 % before 61, passes 10 % at 68 and peaks around
  77 (ages at which at least ten laureates were still unawarded). Dolton and Tol's candidate-pool logit, which also
  counts the people who never won, puts the probability of winning at its maximum at about 70-71 years of age.
  Read together: awards cluster in the sixties, the chance per year is highest around 70, and awards after 75 are
  uncommon but not rare.
- No trend over time: +0.13 years per decade (p = 0.80); period medians 1969–79 67, 1980s 67, 1990s 65, 2000s 64, 2010s 68, 2020–25 69; 1969-1997 median
  66 against 1998-2025 median 67 (p = 0.95).
- By field (median age, laureates): Information 61 (n = 10.0); Growth 64 (n = 8.0); Equilibrium 65 (n = 9.0); Econometrics 65 (n = 12.0); Development/EH 66 (n = 8.0); Macro 66 (n = 10.0); Finance 67 (n = 11.0); Trade 69 (n = 4.0); Labour 70 (n = 7.0); Public 72 (n = 2.0); Production/IO 72 (n = 5.0); Behavioural 72 (n = 3.0); Games 74 (n = 9.0); Resources 77 (n = 1.0). The differences are
  not significant across fields with at least three laureates (Kruskal-Wallis p = 0.37). By laureates per
  prize: solo 67, two 69, three 64 (p = 0.071): three-way prizes go to younger people.
- Co-laureates are usually of one generation: in the 26 works shared by two or three laureates the age gap between
  the oldest and the youngest has a median of 9 years; 4 works have a gap of 15 years or more
  (2007 Leonid Hurwicz, Eric S. Maskin, Roger B. Myerson (34 years); 2012 Alvin E. Roth, Lloyd S. Shapley (29 years); 1996 James A. Mirrlees, William Vickrey (22 years)).
- The prize is not awarded posthumously: the 51 deceased laureates died at a median age of 86, a median
  18 years after the prize; 7 died within five years of it. Of the 20 laureates awarded at 75 or
  older, 13 have died, after a median 11 years. 48 laureates are alive (median age 79; 24 are 80 or older).

Use for the people stage: a candidate's age in 2026 matters mostly at the extremes. Under 55 is rare (4 of 99) and
80 and over is rare (6 of 99) but has happened for long-recognized theoretical work; between 58 and 77 age alone
separates candidates little. Within one laureate set, expect co-laureates of one generation more often than a
mentor-student pair.

Reading the candidates' birth years: the candidate notes give each person's year of birth as stated by the language
models of the virtual committee (the median over nominations); the years were not checked against an external source.
