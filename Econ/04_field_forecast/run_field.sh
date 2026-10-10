#!/bin/bash
# run_field.sh [tag] [question.json] [state-subfolder]: the 2026 economics FIELD question on Preseen (step 4b).
#   defaults: tag nobel26-econ-fields, questions/fields14.json, preseen_exp/fields14
#   second experiment (10 Oct): run_field.sh nobel26-econ-fields-nobel questions/fields14_nobel.json fields14_nobel
#   = the same notes and arms with the title "... 2026 Nobel Prize in Economic Sciences ..." instead of "... Sveriges
#     Riksbank Prize in Economic Sciences ..." (the only difference between the two question files).
# Two arms with an identical private question (questions/fields14.json, 14 fields, no Other):
#   control = no context
#   main    = the nine notes of context/ (00_1 ... 00_9), treatment assume_true, in name order
# One rep per arm, then poll until both finish and write preseen_exp/fields14/runs.csv.
# Run from Econ/04_field_forecast/; PRESEEN_API_KEY comes from the environment (never passed here).
# The client is a copy of ../../experiment/preseen_chem30_main/nobel_preseen_exp.py (unchanged).
set -euo pipefail
TAG=${1:-nobel26-econ-fields}
Q=${2:-questions/fields14.json}
SUB=${3:-fields14}
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$SUB
mkdir -p "$EXP_DIR"
N=$(ls context/*.md | wc -l)
if [ "$N" -ne 9 ] || ls context/*.md | grep -qv '/00_'; then echo "context/ must hold exactly the nine 00_ notes (found $N)"; exit 1; fi
date
$PY nobel_preseen_exp.py --tag "$TAG" create --question "$Q" --arms control main
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm main --cards context/ --treatment assume_true
$PY nobel_preseen_exp.py --tag "$TAG" run --arms control main --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
date
