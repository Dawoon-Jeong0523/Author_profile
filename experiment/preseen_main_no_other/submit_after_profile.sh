#!/bin/bash
# Wait for Kurahashi Neilson's profile job, rebuild her card, then run the Preseen condition (once).
cd "$(dirname "$0")"
until [ -z "$(squeue -h -j 60113507 2>/dev/null)" ]; do sleep 20; done
echo "$(date '+%H:%M') job 60113507: $(sacct -j 60113507 -X -n --format=State | xargs)"
LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib /project/jevans/Dawoon/env/Curvature/bin/python -B make_kurahashi_card.py || { echo "STOP: card not rebuilt; nothing submitted"; exit 1; }
echo "$(date '+%H:%M') submitting run_field.sh physics nobel26-phys-main12"
./run_field.sh physics nobel26-phys-main12
echo "$(date '+%H:%M') run_field.sh exit=$?"
