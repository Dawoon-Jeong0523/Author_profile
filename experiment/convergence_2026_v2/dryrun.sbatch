#!/bin/bash
#SBATCH --job-name=conv2-dryrun
#SBATCH --partition=jevans
#SBATCH --account=pi-jevans
#SBATCH --qos=jevans
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=people/dryrun_%j.out
# name search for people/<field>.txt (cards_pipeline_v2.py dryrun); submit from experiment/convergence_2026_v2/
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
/project/jevans/Dawoon/env/Curvature/bin/python -B cards_pipeline_v2.py dryrun --threads 8 "$@"
