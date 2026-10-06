#!/bin/bash
# run_resume_main3.sh: the main3 arm of the v2 list runs from its own state folder (preseen_exp/v2_main3), because the
# poll loop of the main2 run rewrites preseen_exp/v2/state.json and dropped main3's question (16:02 CDT, KeyError).
set -euo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
export EXP_DIR=preseen_exp/v2_main3
TAG=nobel26-chem-30-v2-main
$PY nobel_preseen_exp.py --tag "$TAG" run --arms main3 --reps 1
$PY nobel_preseen_exp.py --tag "$TAG" poll --wait
$PY nobel_preseen_exp.py --tag "$TAG" table
