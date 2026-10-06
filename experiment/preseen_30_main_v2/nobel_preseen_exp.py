#!/usr/bin/env python3
"""
nobel_preseen_exp.py — does adding researcher profiles change Preseen's Nobel forecast?

Design
  Context notes are written onto a question and apply to every later run (no per-run override),
  so each arm is its own question with an identical definition:
    control : no context
    treat   : one context note per candidate profile (treatment=consider)
    shuffle : (optional placebo) same notes with the numbers swapped across candidates
  Runs are interleaved across arms and repeated; the spread of the control runs is the noise band.

Usage (needs internet: Midway3 login node, not a compute node)
  export PRESEEN_API_KEY=pre_...            # never hard-code the key
  python nobel_preseen_exp.py normalize "Who will win the 2026 Nobel Prize in Physics?" \
      --guidance "Multiple choice: the 12-15 most likely discoveries, each option naming the people \
who would share the prize, plus 'Other'."
  #   -> review/edit preseen_exp/normalized.json (the "question" object) by hand
  python nobel_preseen_exp.py create --arms control treat shuffle
  python nobel_preseen_exp.py run --arms control --reps 1           # step-1 probabilities, right away
  #   ... build cards/ (and cards_shuffled/ with the same file names) from the Midway3 records ...
  python nobel_preseen_exp.py add-context --arm treat   --cards cards/
  python nobel_preseen_exp.py add-context --arm shuffle --cards cards_shuffled/
  python nobel_preseen_exp.py run --arms control treat shuffle --reps 3
  python nobel_preseen_exp.py poll --wait
  python nobel_preseen_exp.py table                                  # runs.csv for analysis

Cards: one .md file per candidate (or per discovery). Files whose names start with "00_"
(e.g. 00_definitions.md) are added first; the rest are added in a seeded random order that is the
same for every arm as long as the file names match.

State lives in $EXP_DIR (default ./preseen_exp): state.json, normalized.json, runs/*.json, runs.csv.
Every POST carries an Idempotency-Key built from --tag, the arm and the rep, so re-running a command
after a network failure never creates a duplicate question, note or forecast.
"""
import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path

import requests

BASE = os.environ.get("PRESEEN_BASE", "https://preseen.com/api/v1/external")
KEY = os.environ.get("PRESEEN_API_KEY")
EXP = Path(os.environ.get("EXP_DIR", "preseen_exp"))
STATE_FILE = EXP / "state.json"
TERMINAL = {"completed", "failed", "cancelled"}
BUSY = {"rate_limit_error", "overloaded_error", "idempotency_in_progress", "too_many_active_forecasts"}
QUESTION_FIELDS = [
    "type", "title", "description", "resolution_criteria", "fine_print", "options",
    "options_are_mutually_exclusive", "options_are_comprehensive", "lower_bound", "upper_bound",
    "open_lower_bound", "open_upper_bound", "scale_type",
]


# ---------------------------------------------------------------- HTTP ----------------------------
def call(method, path, idem=None, allow=(), **kw):
    """One API call with timeout, backoff on 429/5xx/busy errors, and readable failures.
    Returns parsed JSON, or None when the status code is in `allow` (e.g. 404)."""
    url = path if path.startswith("http") else f"{BASE}{path}"
    head = {"Authorization": f"Bearer {KEY}", "Accept": "application/json"}
    if idem:
        head["Idempotency-Key"] = idem
    for wait in (5, 10, 20, 40, 60, 60, 60, 60, 60, 60):
        try:
            r = requests.request(method, url, headers=head, timeout=60, **kw)
        except (requests.ConnectionError, requests.Timeout) as e:
            print(f"  network error ({type(e).__name__}); retry in {wait}s")
            time.sleep(wait)
            continue
        if r.status_code in allow:
            return None
        if r.ok:
            return r.json() if r.content else {}
        try:
            err = r.json().get("error", {})
        except ValueError:
            err = {"type": "?", "message": r.text[:300]}
        if r.status_code >= 500 or err.get("type") in BUSY:
            w = float(r.headers.get("Retry-After", wait))
            print(f"  {r.status_code} {err.get('type')}; retry in {w:.0f}s")
            time.sleep(w)
            continue
        sys.exit(f"{method} {path} -> {r.status_code} {err.get('type')}: {err.get('message')}")
    sys.exit(f"gave up after retries: {method} {path}")


def load():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"questions": {}, "runs": []}


def save(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- commands ------------------------
def cmd_normalize(a):
    """Step 1a: let Preseen's AI turn the title into a question with candidate options."""
    body = {"title": a.title}
    if a.draft:
        body["draft"] = json.loads(Path(a.draft).read_text())
    res = call("POST", "/questions/normalize/", json=body)
    if a.guidance and res.get("status") == "supported":
        res = call("POST", "/questions/normalize/revise/", json={
            "title": a.title, "draft": res.get("question"), "guidance": a.guidance,
            "completion_session": res.get("completion_session")})
    out = EXP / "normalized.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print("status:", res.get("status"))
    if res.get("status") == "unsupported":
        print("reason:", res.get("unsupported_reason"))
        print("suggested reframe:", res.get("suggested_reframe"))
        return
    q = res.get("question") or {}
    print("type:", q.get("type"),
          "| mutually exclusive:", q.get("options_are_mutually_exclusive"),
          "| comprehensive:", q.get("options_are_comprehensive"))
    for o in q.get("options") or []:
        print("  -", o)
    for c in res.get("requested_clarifications") or []:
        print("clarification requested:", c)
    print(f"-> review/edit the 'question' object in {out} before `create`.")


def cmd_create(a):
    """Step 1b: create one identical, private question per arm and make sure no watch is on."""
    state = load()
    src = json.loads(Path(a.question or EXP / "normalized.json").read_text())
    q = src.get("question", src)
    payload = {k: q[k] for k in QUESTION_FIELDS if q.get(k) is not None}
    payload["visibility"] = "private"
    for arm in a.arms:
        if arm in state["questions"]:
            print(f"{arm}: already exists ({state['questions'][arm]})")
            continue
        res = call("POST", "/questions/", idem=f"{a.tag}-create-{arm}", json=payload)
        state["questions"][arm] = res["id"]
        save(state)
        print(f"{arm}: created {res['id']}")
    # integrity: the arms must differ only in context
    seen = {}
    for arm, qid in state["questions"].items():
        got = call("GET", f"/questions/{qid}/")
        seen[arm] = {k: got.get(k) for k in QUESTION_FIELDS}
        watch = call("GET", f"/questions/{qid}/watch/", allow=(404,))
        if watch and watch.get("enabled"):
            call("DELETE", f"/questions/{qid}/watch/")
            print(f"  {arm}: auto-reforecast watch stopped")
    first = next(iter(seen.values()))
    if any(v != first for v in seen.values()):
        sys.exit("WARNING: question definitions differ across arms; fix before running.")
    print("all arms have identical question definitions; visibility=private")


def cmd_add_context(a):
    """Step 3a: attach the cards to one arm as context notes, then wait until context is ready."""
    state = load()
    qid = state["questions"][a.arm]
    cards = sorted(Path(a.cards).glob("*.md"))
    if not cards:
        sys.exit(f"no .md cards in {a.cards}")
    fixed = [c for c in cards if c.name.startswith("00_")]
    rest = [c for c in cards if not c.name.startswith("00_")]
    random.Random(a.seed).shuffle(rest)  # same seed + same names -> same order in every arm
    for c in fixed + rest:
        call("POST", f"/questions/{qid}/context/", idem=f"{a.tag}-ctx-{a.arm}-{c.stem}",
             json={"text": c.read_text(), "treatment": a.treatment})
        print(f"  {a.arm}: note added <- {c.name}")
    for _ in range(60):
        if (call("GET", f"/questions/{qid}/context/ready/") or {}).get("ready"):
            print(f"{a.arm}: context ready ({len(cards)} notes, treatment={a.treatment})")
            return
        time.sleep(10)
    sys.exit("context not ready after 10 minutes")


def refresh_active(state):
    active = 0
    for r in state["runs"]:
        if r.get("status") in TERMINAL:
            continue
        r["status"] = call("GET", f"/forecasts/{r['task_id']}/").get("status")
        active += r["status"] not in TERMINAL
    save(state)
    return active


def cmd_run(a):
    """Step 2/3b: submit repeated runs, interleaved across arms in a random order per round."""
    state = load()
    done = {}
    for r in state["runs"]:
        done[r["arm"]] = max(done.get(r["arm"], 0), r["rep"])
    rng = random.Random(a.seed + len(state["runs"]))
    plan = []
    for k in range(1, a.reps + 1):
        arms = list(a.arms)
        rng.shuffle(arms)
        plan += [(arm, done.get(arm, 0) + k) for arm in arms]
    for arm, rep in plan:
        while refresh_active(state) >= a.max_active:
            print(f"  {a.max_active} runs active; waiting 30s")
            time.sleep(30)
        qid = state["questions"][arm]
        res = call("POST", f"/questions/{qid}/forecasts/", idem=f"{a.tag}-run-{arm}-rep{rep:02d}",
                   json={"allow_incomplete_context": False})
        state["runs"].append({
            "arm": arm, "rep": rep, "task_id": res["id"], "question_id": qid,
            "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "status": res.get("status")})
        save(state)
        print(f"submitted {arm} rep{rep:02d} -> {res['id']}")


def cmd_poll(a):
    """Step 4: save the full task envelope (with subforecasts) of every finished run."""
    state = load()
    out = EXP / "runs"
    out.mkdir(exist_ok=True)
    while True:
        pending = 0
        for r in state["runs"]:
            f = out / f"{r['arm']}_rep{r['rep']:02d}_{r['task_id']}.json"
            if f.exists():
                continue
            t = call("GET", f"/forecasts/{r['task_id']}/", params={"include_subforecasts": "true"})
            r["status"] = t.get("status")
            if r["status"] in TERMINAL:
                f.write_text(json.dumps(t, indent=2, ensure_ascii=False))
                print(f"saved {f.name} ({r['status']})")
            else:
                pending += 1
                print(f"  {r['arm']} rep{r['rep']:02d}: {r['status']} {t.get('progress_message') or ''}")
        save(state)
        if not a.wait or pending == 0:
            print(f"pending: {pending}")
            return
        time.sleep(60)


def cmd_table(a):
    """One row per run; forecast_data kept as raw JSON until its structure is known."""
    rows = []
    for f in sorted((EXP / "runs").glob("*.json")):
        t = json.loads(f.read_text())
        fc = t.get("forecast") or {}
        rows.append({
            "arm": f.name.split("_rep")[0], "rep": int(f.name.split("_rep")[1][:2]),
            "task_id": t.get("id"), "status": t.get("status"),
            "created_at": t.get("created_at"), "finished_at": t.get("finished_at"),
            "n_subforecasts": len(t.get("subforecasts") or []),
            "forecast_data": json.dumps(fc.get("forecast_data"), ensure_ascii=False)})
    if not rows:
        sys.exit("no saved runs yet; run `poll` first")
    with open(EXP / "runs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {EXP / 'runs.csv'} ({len(rows)} runs)")


# ---------------------------------------------------------------- CLI -----------------------------
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tag", default="nobel26-phys", help="prefix for idempotency keys (one per experiment)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("normalize")
    s.add_argument("title")
    s.add_argument("--draft", help="JSON file with a partial draft (description, options, ...)")
    s.add_argument("--guidance", help="instructions for one revise pass")
    s.set_defaults(fn=cmd_normalize)

    s = sub.add_parser("create")
    s.add_argument("--arms", nargs="+", default=["control", "treat"])
    s.add_argument("--question", help="JSON with the question object (default: normalized.json)")
    s.set_defaults(fn=cmd_create)

    s = sub.add_parser("add-context")
    s.add_argument("--arm", required=True)
    s.add_argument("--cards", required=True, help="directory of .md cards")
    s.add_argument("--treatment", default="consider", choices=["consider", "look_into", "assume_true"])
    s.add_argument("--seed", type=int, default=2026)
    s.set_defaults(fn=cmd_add_context)

    s = sub.add_parser("run")
    s.add_argument("--arms", nargs="+", required=True)
    s.add_argument("--reps", type=int, default=3)
    s.add_argument("--max-active", type=int, default=3, help="concurrent runs allowed before waiting")
    s.add_argument("--seed", type=int, default=2026)
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("poll")
    s.add_argument("--wait", action="store_true", help="keep polling until every run has finished")
    s.set_defaults(fn=cmd_poll)

    s = sub.add_parser("table")
    s.set_defaults(fn=cmd_table)

    a = p.parse_args()
    if not KEY:
        sys.exit("set PRESEEN_API_KEY in the environment (e.g. in ~/.bashrc), not in this file")
    EXP.mkdir(exist_ok=True)
    a.fn(a)


if __name__ == "__main__":
    main()
