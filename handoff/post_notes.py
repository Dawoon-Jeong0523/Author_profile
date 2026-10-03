"""Post the context notes of one condition to a Preseen question, in the order the runs used.

    export PRESEEN_API_KEY=...
    python post_notes.py --question <question id> --field medicine --condition cards_as_context
    python post_notes.py --question <question id> --field physics --condition cards_main_evidence --cards current

The recipe is context/conditions.json. These are the calls experiment/preseen/nobel_preseen_exp.py made in the
experiment: one POST /questions/{id}/context/ per note, then GET /questions/{id}/context/ready/. A note stays on
the question and applies to every later forecast on it. To leave a piece out (say one person's card), filter the
JSONL files or post the notes yourself.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE = os.environ.get("PRESEEN_BASE", "https://preseen.com/api/v1/external")
CTX = Path(__file__).resolve().parent / "context"
CARDS = {"used": "profile_cards_used_in_runs.jsonl", "current": "profile_cards_current.jsonl"}


def headers(idem=None):
    h = {"Authorization": f"Bearer {os.environ['PRESEEN_API_KEY']}", "Accept": "application/json"}
    if idem:
        h["Idempotency-Key"] = idem
    return h


def notes_for(condition, field, cards):
    recipe = json.loads((CTX / "conditions.json").read_text())["conditions"][condition]["notes"]
    out = []
    for step in recipe:
        name = CARDS[cards] if step["file"].startswith("profile_cards") else step["file"]
        rows = [json.loads(line) for line in open(CTX / name)]
        if step["file"] == "instruction_notes.jsonl":
            rows = [r for r in rows if r["id"] == condition]
        else:
            rows = sorted((r for r in rows if r["field"] == field), key=lambda r: r.get("order", 0))
        out += [(r["id"], r["text"], step["treatment"]) for r in rows]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", required=True, help="Preseen question id")
    ap.add_argument("--field", required=True, choices=["medicine", "physics", "chemistry"])
    ap.add_argument("--condition", required=True, choices=["cards_as_context", "cards_one_main_source", "cards_main_evidence"])
    ap.add_argument("--cards", default="used", choices=sorted(CARDS), help="cards as used in the runs (default) or rebuilt")
    a = ap.parse_args()

    notes = notes_for(a.condition, a.field, a.cards)
    for nid, text, treatment in notes:
        # the idempotency key makes a re-run after a network error safe: Preseen will not add the note twice
        r = requests.post(f"{BASE}/questions/{a.question}/context/", json={"text": text, "treatment": treatment},
                          timeout=60, headers=headers(f"profiles-{a.question}-{nid}"))
        if not r.ok:
            sys.exit(f"note {nid} -> {r.status_code}: {r.text[:300]}")
        print(f"added {nid} ({treatment})")
    for _ in range(60):
        r = requests.get(f"{BASE}/questions/{a.question}/context/ready/", timeout=60, headers=headers())
        if r.ok and r.json().get("ready"):
            print(f"context ready: {len(notes)} notes")
            return
        time.sleep(10)
    sys.exit("context not ready after 10 minutes")


if __name__ == "__main__":
    main()
