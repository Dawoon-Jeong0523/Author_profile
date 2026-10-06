#!/usr/bin/env python3
"""make_kurahashi_card.py: rebuild cards/physics/naoko-kurahashi-neilson.md from the profile with the added OpenAlex id.

Same card function, affiliation, "Listed under" line and laureate reference as ../preseen/cards/physics/ (3 October);
only the ids differ (../convergence_2026/people/overrides.yaml). Exits 1 and leaves the old card in place when the
profile is missing or still holds only the 2019-2021 works.
"""
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "preseen"))
import build_cards as bc  # noqa: E402

NAME = "Naoko Kurahashi Neilson"
ids = yaml.safe_load((HERE.parent / "convergence_2026" / "people" / "overrides.yaml").read_text())[NAME]["author_id"].split(";")
old = (HERE / "cards" / "physics" / "naoko-kurahashi-neilson.md").read_text()
aff = re.search(r"^Affiliation: (.*)\.$", old, re.M).group(1)
opts = re.findall(r'option "(.*?)"(?:;|\.$)', re.search(r"^Listed under: (.*)$", old, re.M).group(1))
prior = re.search(r"^Prior Nobel Prize: (.*)\.$", old, re.M).group(1)
bc.TITLE_CACHE = HERE / "cards" / "_titles_cache.json"
if not bc.TITLE_CACHE.exists():
    bc.TITLE_CACHE.write_text((HERE.parent / "preseen" / "cards" / "_titles_cache.json").read_text())
if bc.find_profile(ids) is None:
    sys.exit(f"no profile for {ids}; card not changed")
ref = pd.read_csv(HERE.parent / "preseen" / "cards" / "laureate_reference.csv")
text, folder = bc.card("physics", NAME, ids, opts, aff, None if prior == "none" else prior, ref)
span = re.search(r"published (\d{4})-", text)
if not span or int(span.group(1)) >= 2019:
    sys.exit(f"profile {folder} still starts in {span.group(1) if span else '?'}; card not changed")
(HERE / "cards" / "physics" / "naoko-kurahashi-neilson.md").write_text(text)
print(f"card rebuilt from {folder.name}:")
print(text)
