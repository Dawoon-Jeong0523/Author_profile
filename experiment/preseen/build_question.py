#!/usr/bin/env python3
"""build_question.py: committee/<field>/candidates.json -> questions/<field>.json (SPEC §7).

    $PY build_question.py [--fields medicine physics chemistry]

The question is the same for every arm (the client posts it once per arm). Title, description and resolution
criteria come from config.yaml `question` templates and are checked against `forbidden_words` (they must not mention
the committee, the models, the profiles or the experiment). Options: the K option texts of candidates.json + "Other".
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CFG = yaml.safe_load((HERE / "config.yaml").read_text())


def build(field):
    f, q = CFG["fields"][field], CFG["question"]
    cand = json.loads((HERE / "committee" / field / "candidates.json").read_text())
    opts = [o["option"] for o in cand["options"] if o["option"] != q["other_option"]]
    if len(opts) != q["K"]:
        sys.exit(f"{field}: {len(opts)} options in candidates.json, expected K = {q['K']}")
    if len(set(opts)) != len(opts):
        sys.exit(f"{field}: duplicate option texts")
    date = dt.datetime.fromisoformat(f["announcement"]).strftime("%A %-d %B %Y")
    question = {
        "type": q["type"],
        "title": q["title_template"].format(prize=f["prize"]),
        "description": q["description_template"].format(prize=f["prize"], date=date),
        "resolution_criteria": q["resolution_template"].format(prize=f["prize"]),
        "options": opts + [q["other_option"]],
        "options_are_mutually_exclusive": q["options_are_mutually_exclusive"],
        "options_are_comprehensive": q["options_are_comprehensive"],
        "visibility": q["visibility"],
    }
    text = " ".join(question[k] for k in ("title", "description", "resolution_criteria"))
    bad = [w for w in q["forbidden_words"] if re.search(rf"\b{re.escape(w)}", text, re.I)]
    if bad:
        sys.exit(f"{field}: forbidden words in the question text: {bad}")
    warn = [(i + 1, w) for i, o in enumerate(opts) for w in q["forbidden_words"] if re.search(rf"\b{re.escape(w)}\b", o, re.I)]
    out = HERE / "questions" / f"{field}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(question, indent=2, ensure_ascii=False) + "\n")
    print(f"{field}: {out.relative_to(HERE)} ({len(question['options'])} options, longest "
          f"{max(map(len, question['options']))} characters)" + (f"; check option words: {warn}" if warn else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fields", nargs="+", default=CFG["order"])
    for field in ap.parse_args().fields:
        build(field)
    return 0


if __name__ == "__main__":
    sys.exit(main())
