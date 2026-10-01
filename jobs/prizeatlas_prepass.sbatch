#!/bin/bash
#SBATCH -J pa_prepass
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1
#SBATCH -c 16
#SBATCH --mem=192G
#SBATCH -t 02:00:00
#SBATCH -o "/project/jevans/Dawoon/Nobel Prize/jobs/logs/%x_%j.out"
# Pre-pass of the PrizeAtlas dashboard batch: targets.tsv + shared title tables (see prizeatlas_prepass.py)
set -euo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
/project/jevans/Dawoon/env/Curvature/bin/python "/project/jevans/Dawoon/Nobel Prize/jobs/prizeatlas_prepass.py" "${NP_BATCH_TASKS:-20}"
