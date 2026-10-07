#!/bin/bash
# run_arm.sh <list> <arm> <tag>: add an arm to the experiment of one list (questions/<list>.json, same question as its
# other arms), add its notes, run one rep, poll, rewrite runs.csv with all arms. Run from experiment/preseen_chem30_main/;
# PRESEEN_API_KEY from the environment (never passed here). Arms:
#   main2 = cards as the main evidence, updated: instruction/ (technological translation no longer "minor"; patents tied
#           to the discovery count as discovery evidence; definitions with the patent line) + cards/<list>/ with patents
#   main3 = main2 with no measure called "minor" (all profile information important); instruction/ is this version
#   demo  = instruction_demo/: the main3 notes (00_1 adapted: this year's laureates enter only through the demographic
#           note) + 00_6 demographics of the 2000-2025 Chemistry laureates and the 2026 Physics and Medicine laureates
#           + 00_7 weigh the demographic distribution with an explicit factor 0.5-2 per option; + cards/<list>/
#   balanced = instruction_balanced/: "cards as one of the main sources" (the 2 October instruction of
#           ../preseen_cards_balanced/ adapted to Chemistry and the 30-option question) + main3's reference notes
#           00_2-00_5 unchanged; + cards/<list>/ (the treatment's cards)
#   context = instruction_context/: "cards as context", no instruction; main3's reference notes 00_2-00_5 unchanged;
#           + cards/<list>/ (the treatment's cards)
set -euo pipefail
L=$1; ARM=$2; TAG=$3
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
# own state folder per arm: a poll loop of another arm rewrites its state.json and would drop this arm's question
export EXP_DIR=preseen_exp/${L}_${ARM}
mkdir -p "$EXP_DIR"
$PY nobel_preseen_exp.py --tag "$TAG" create --question "questions/$L.json" --arms "$ARM"
if [ "$ARM" = "demo" ]; then   # instruction_demo/ is the full note set of the arm (main3 notes, 00_1 adapted, + 00_6, 00_7)
  $PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards instruction_demo/ --treatment assume_true
elif [ "$ARM" = "context" ]; then    # instruction_context/: main3's 00_2-00_5, no instruction note
  $PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards instruction_context/ --treatment assume_true
elif [ "$ARM" = "balanced" ]; then   # instruction_balanced/: one-main-source 00_1 + main3's 00_2-00_5
  $PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards instruction_balanced/ --treatment assume_true
else
  $PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards instruction/ --treatment assume_true
fi
$PY nobel_preseen_exp.py --tag "$TAG" add-context --arm "$ARM" --cards "cards/$L/" --treatment consider
$PY nobel_preseen_exp.py --tag "$TAG" run --arms "$ARM" --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
