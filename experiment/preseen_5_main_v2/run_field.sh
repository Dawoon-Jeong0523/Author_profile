#!/bin/bash
# run_field.sh <field> <tag>: create "control" (no notes) and "main" (5 options, no "Other"; the 5 leaders of the 30-option
# v2 main run, option texts unchanged), add the four instruction notes (assume_true, file order) and the 5 option blocks
# (consider, option order) to main, run one rep per arm in random order, poll, write runs.csv.
# Run from experiment/preseen_5_main_v2/; PRESEEN_API_KEY comes from the environment (never passed here).
set -euo pipefail
F=$1; TAG=$2
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$F
mkdir -p "$EXP_DIR"
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$F.json" --arms control main
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm main --cards instruction/ --treatment assume_true
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm main --cards "cards/$F/" --treatment consider
$PY nobel_preseen_exp.py --tag "$TAG" run --arms control main --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
