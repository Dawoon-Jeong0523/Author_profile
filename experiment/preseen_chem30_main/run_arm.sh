#!/bin/bash
# run_arm.sh <list> <arm> <tag>: add an arm to the experiment of one list (questions/<list>.json, same question as its
# other arms), add its notes, run one rep, poll, rewrite runs.csv with all arms. Run from experiment/preseen_chem30_main/;
# PRESEEN_API_KEY from the environment (never passed here). Arms:
#   main2 = cards as the main evidence, updated: instruction/ (technological translation no longer "minor"; patents tied
#           to the discovery count as discovery evidence; definitions with the patent line) + cards/<list>/ with patents
#   demo  = main2 + instruction_demo/ (demographics of the 2000-2025 Chemistry laureates and the 2026 Physics and
#           Medicine laureates; instruction to weigh the demographic distribution with an explicit factor per option)
set -euo pipefail
L=$1; ARM=$2; TAG=$3
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/$L
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$L.json" --arms main "$ARM"
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards instruction/ --treatment assume_true
if [ "$ARM" = "demo" ]; then
  $PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards instruction_demo/ --treatment assume_true
fi
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards "cards/$L/" --treatment consider
$PY nobel_preseen_exp.py --tag "$TAG" run --arms "$ARM" --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
