#!/bin/bash
# run_field.sh <field> <tag>: create the "main" arm (30 options, no "Other"; same question as ../preseen_30_no_other),
# add the four instruction notes (assume_true, in file order) and the 30 option blocks (consider, in option order:
# every file starts with 00_ so the client keeps the sorted order), run one rep, poll until it finishes, write runs.csv.
# Run from experiment/preseen_30_main_v2/; PRESEEN_API_KEY comes from the environment (never passed here).
set -euo pipefail
F=$1; TAG=$2
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$F
mkdir -p "$EXP_DIR"
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$F.json" --arms main
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm main --cards instruction/ --treatment assume_true
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm main --cards "cards/$F/" --treatment consider
$PY nobel_preseen_exp.py --tag "$TAG" run --arms main --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
