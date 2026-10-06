#!/bin/bash
# run_control.sh <field> <tag>: add a "control" arm (same question, no notes) to this experiment, run one rep, poll,
# rewrite runs.csv with both arms. Run from experiment/preseen_30_main_v2/; PRESEEN_API_KEY from the environment.
set -euo pipefail
F=$1; TAG=$2
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$F
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$F.json" --arms main control
$PY nobel_preseen_exp.py --tag "$TAG" run --arms control --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
