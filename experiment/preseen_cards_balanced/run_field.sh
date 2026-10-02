#!/bin/bash
# run_field.sh <field> <tag>: create one treat question, add the instruction (assume_true) and the cards (consider),
# run one rep, poll until it finishes, write runs.csv. The control arm is not repeated: the five control runs of
# ../preseen/ (1 Oct, 4) and ../preseen_cards_main/ (2 Oct, 1) are the baseline.
# Run from experiment/preseen_cards_balanced/ inside tmux; PRESEEN_API_KEY comes from the environment (never passed here).
set -euo pipefail
F=$1; TAG=$2
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$F
mkdir -p "$EXP_DIR"
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$F.json" --arms treat
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm treat --cards instruction/ --treatment assume_true
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm treat --cards "cards/$F/" --treatment consider
$PY nobel_preseen_exp.py --tag "$TAG" run --arms treat --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
