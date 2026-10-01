#!/bin/bash
#SBATCH -J pa_dash
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 06:00:00
#SBATCH --array=0-19
#SBATCH -o "/project/jevans/Dawoon/Nobel Prize/jobs/logs/%x_%A_%a.out"
# Dashboards (output/dashboard/) and records (output/record/) for every PrizeAtlas Nobel laureate (Data/prizeatlas):
# array task i runs notebook/author_profile.ipynb for the targets of output/batch_prizeatlas/targets.tsv with task == i
# (written by prizeatlas_prepass.py, which also builds the shared title tables), one after the other.
#   sbatch --dependency=afterany:<prepass job> prizeatlas_dashboards.sbatch
# Finished ids are marked in output/batch_prizeatlas/done/; a rerun skips them. Failures: failed_task<i>.txt, logs/<id>.log.
set -uo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
NP="/project/jevans/Dawoon/Nobel Prize"
NB="$NP/notebook/author_profile.ipynb"
B="$NP/output/batch_prizeatlas"
T="$B/targets.tsv"
mkdir -p "$B/notebooks" "$B/logs" "$B/done"
export NP_FETCH_TITLES=1 NP_TITLES_TABLE="$NP/cache/titles_prizeatlas.parquet"
[ -f "$T" ] || { echo "no $T: run prizeatlas_prepass.sbatch first"; exit 1; }
cd "$NP/notebook"
TASK=${SLURM_ARRAY_TASK_ID:-0}
echo "task $TASK on $(hostname) $(date)"
awk -F'\t' -v t="$TASK" 'NR > 1 && $2 == t {print $1}' "$T" | while read -r aid; do
  [ -f "$B/done/$aid" ] && { echo "skip $aid (done)"; continue; }
  s=$(date +%s)
  if NP_AUTHOR_ID="$aid" timeout 50m "$PY" -m jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 \
       --ExecutePreprocessor.kernel_name=curvature --output-dir "$B/notebooks" --output "$aid.ipynb" "$NB" > "$B/logs/$aid.log" 2>&1; then
    echo "$aid $(( $(date +%s) - s ))s $(date '+%F %T')" > "$B/done/$aid"
    echo "done $aid $(( $(date +%s) - s ))s"
  else
    echo "$aid failed after $(( $(date +%s) - s ))s $(date '+%F %T')" | tee -a "$B/failed_task$TASK.txt"
  fi
done
echo "task $TASK finished $(date)"
