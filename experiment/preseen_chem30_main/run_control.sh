#!/bin/bash
# run_control.sh <list> <tag>: add a "control" arm (same question, no notes: no instruction, no outcomes, no cards) to the
# experiment of one list, run one rep, poll, rewrite runs.csv with both arms. Run from experiment/preseen_chem30_main/;
# PRESEEN_API_KEY from the environment (never passed here).
set -euo pipefail
L=$1; TAG=$2
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$L
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$L.json" --arms main control
$PY nobel_preseen_exp.py --tag "$TAG" run --arms control --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
