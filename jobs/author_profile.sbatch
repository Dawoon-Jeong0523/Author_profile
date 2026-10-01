#!/bin/bash
#SBATCH -J author_profile
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 03:00:00
#SBATCH -o "/project/jevans/Dawoon/Nobel Prize/jobs/logs/%x_%j.out"
# Batch runner for notebook/author_profile.ipynb: executes a copy of the notebook for one author
# and keeps the executed copy (with figures) next to the author's output.
#   sbatch --export=ALL,NP_AUTHOR_ID=A5067184382 author_profile.sbatch
set -euo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
NB="/project/jevans/Dawoon/Nobel Prize/notebook/author_profile.ipynb"
: "${NP_AUTHOR_ID:=A5067184382}"
export NP_AUTHOR_ID
OUTDIR="/project/jevans/Dawoon/Nobel Prize/output/${NP_AUTHOR_ID}"
mkdir -p "$OUTDIR" "/project/jevans/Dawoon/Nobel Prize/jobs/logs"
echo "author ${NP_AUTHOR_ID}  job ${SLURM_JOB_ID}  node $(hostname)  $(date)"
cd "/project/jevans/Dawoon/Nobel Prize/notebook"
$PY -m jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --ExecutePreprocessor.kernel_name=curvature \
    --output "author_profile_${NP_AUTHOR_ID}.ipynb" --output-dir "$OUTDIR" "$NB"
echo "done $(date)"
