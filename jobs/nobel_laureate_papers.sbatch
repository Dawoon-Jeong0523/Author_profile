#!/bin/bash
#SBATCH -J nobel_laureate_papers
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1
#SBATCH -c 8
#SBATCH --mem=96G
#SBATCH -t 03:00:00
#SBATCH -o "/project/jevans/Dawoon/Nobel Prize/jobs/logs/%x_%j.out"
# Batch runner for notebook/nobel_laureate_papers.ipynb: executes a copy of the notebook and keeps the
# executed copy (with figures) next to its outputs; the notebook in notebook/ is not modified.
#   sbatch nobel_laureate_papers.sbatch                                  (all laureates)
#   sbatch --export=ALL,NL_LAUREATE_LIMIT=30 nobel_laureate_papers.sbatch (quick version)
set -euo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
NB="/project/jevans/Dawoon/Nobel Prize/notebook/nobel_laureate_papers.ipynb"
TAG=""; [ "${NL_LAUREATE_LIMIT:-0}" != "0" ] && TAG="_limit${NL_LAUREATE_LIMIT}"
OUTDIR="/project/jevans/Dawoon/Nobel Prize/output/nobel_laureates${TAG}"
mkdir -p "$OUTDIR" "/project/jevans/Dawoon/Nobel Prize/jobs/logs"
echo "nobel_laureate_papers  limit=${NL_LAUREATE_LIMIT:-0}  job ${SLURM_JOB_ID}  node $(hostname)  $(date)"
cd "/project/jevans/Dawoon/Nobel Prize/notebook"
$PY -m jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --ExecutePreprocessor.kernel_name=curvature \
    --output "nobel_laureate_papers_executed.ipynb" --output-dir "$OUTDIR" "$NB"
echo "done $(date)"
