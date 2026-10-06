#!/bin/bash
# run_list.sh <list> <tag>: create the "main" arm for one 2026 Chemistry 30-option list (questions/<list>.json; v1, v2 or
# preseen), add the five instruction notes (assume_true, in file order: instruction, definitions, timing base rate,
# Medicine 2026, Physics 2026) and the person cards of that list (consider), run one rep, poll until it finishes,
# write runs.csv. Run from experiment/preseen_chem30_main/; PRESEEN_API_KEY comes from the environment (never passed here).
set -euo pipefail
L=$1; TAG=$2
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$L
mkdir -p "$EXP_DIR"
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$L.json" --arms main
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm main --cards instruction/ --treatment assume_true
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm main --cards "cards/$L/" --treatment consider
$PY nobel_preseen_exp.py --tag "$TAG" run --arms main --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
