#!/bin/bash
# run_people.sh [tag] [question.json] [state-subfolder]: the 2026 economics PEOPLE question on Preseen (step 7b).
#   defaults: tag nobel26-econ-people, questions/people30.json (30 candidates, no Other), preseen_exp/people30
#   variant with Other: run_people.sh nobel26-econ-people-other questions/people30_other.json people30_other
# Two arms with an identical private question:
#   control = no context
#   main    = the notes of context/ (00_instruction ... 25_committee_equilibrium), treatment assume_true, in name order
# One rep per arm, then poll until both finish and write preseen_exp/<sub>/runs.csv.
# Run from Econ/07_people_forecast/; PRESEEN_API_KEY comes from the environment (never passed here). The client is
# ../04_field_forecast/nobel_preseen_exp.py (unchanged copy of ../../experiment/preseen_chem30_main/nobel_preseen_exp.py).
set -euo pipefail
cd "/project/jevans/Dawoon/Nobel Prize/Econ/07_people_forecast"
TAG=${1:-nobel26-econ-people}
Q=${2:-questions/people30.json}
SUB=${3:-people30}
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
CLIENT=../04_field_forecast/nobel_preseen_exp.py
export EXP_DIR=preseen_exp/$SUB
mkdir -p "$EXP_DIR"
N=$(ls context/*.md | wc -l)
if [ "$N" -ne 14 ]; then echo "context/ must hold the 14 notes written by people_candidate_prompts.ipynb (found $N)"; exit 1; fi
if [ ! -s living_check.csv ]; then echo "living_check.csv missing: run check_living_econ.py and review it first"; exit 1; fi
date
$PY $CLIENT --tag "$TAG" create --question "$Q" --arms control main
$PY $CLIENT --tag "$TAG" add-context --arm main --cards context/ --treatment assume_true
$PY $CLIENT --tag "$TAG" run --arms control main --reps 1
$PY $CLIENT --tag "$TAG" poll --wait
$PY $CLIENT --tag "$TAG" table
date
