#!/bin/bash
# run_field.sh <field> <tag>: create control + treat (30 options, no "Other"), add the instruction (assume_true) and the
# cards (consider) to treat, run one rep per arm in a random order, poll until both finish, write runs.csv.
# Run from experiment/preseen_30_no_other/; PRESEEN_API_KEY comes from the environment (never passed here).
set -euo pipefail
F=$1; TAG=$2
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$F
mkdir -p "$EXP_DIR"
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$F.json" --arms control treat
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm treat --cards instruction/ --treatment assume_true
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm treat --cards "cards/$F/" --treatment consider
$PY nobel_preseen_exp.py --tag "$TAG" run --arms control treat --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
