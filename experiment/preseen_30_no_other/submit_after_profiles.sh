#!/bin/bash
# Wait for the two re-run profiles, rebuild and check the 30-option cards, copy the physics cards, run both arms.
cd "$(dirname "$0")"
PY=/project/jevans/Dawoon/env/Curvature/bin/python; export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
until [ -z "$(squeue -h -j 60115070,60115071 2>/dev/null)" ]; do sleep 20; done
echo "$(date '+%H:%M') jobs: $(sacct -j 60115070,60115071 -X -n --format=State | xargs)"
[ "$(sacct -j 60115070,60115071 -X -n --format=State | grep -c COMPLETED)" = 2 ] || { echo "STOP: a profile job did not complete"; exit 1; }
(cd ../convergence_2026 && $PY -B cards_pipeline.py cards && $PY -B cards_pipeline.py check) || { echo "STOP: cards or check failed"; exit 1; }
for c in naoko-kurahashi-neilson ken-ichi-nomoto; do
  f=../convergence_2026/cards/physics/$c.md
  grep -q "Own US utility patents: 0 " "$f" || { echo "STOP: $c still has patents: $(grep 'Own US' $f)"; exit 1; }
done
grep -q "published 2003-" ../convergence_2026/cards/physics/naoko-kurahashi-neilson.md || { echo "STOP: Kurahashi works window changed"; exit 1; }
rm -rf cards && mkdir -p cards && cp -r ../convergence_2026/cards/physics cards/physics
echo "$(date '+%H:%M') cards copied: $(ls cards/physics | wc -l) files; submitting run_field.sh physics nobel26-phys-30"
./run_field.sh physics nobel26-phys-30
echo "$(date '+%H:%M') run_field.sh exit=$?"
