#!/bin/bash
# run_all.sh: start the step-6 run (the asked fields, settings.yaml batches_to_ask) from a shell whose environment holds valid COMMITTEE_ANTHROPIC_API_KEY,
# OPENAI_API_KEY and GEMINI_API_KEY (the editor's tool shell had stale Anthropic/OpenAI keys on 10 Oct 2026). Checks
# that all three keys answer 200, then runs run_all_steps.sh detached with nohup; log in run_all.out (~15 min for batch 1).
set -euo pipefail
cd "/project/jevans/Dawoon/Nobel Prize/Econ/06_candidates"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python
for v in COMMITTEE_ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY; do
  if [ -z "${!v:-}" ]; then echo "$v is not set in this shell"; exit 1; fi
done
CHECK=$($PY ../../experiment/preseen/check_keys.py --no-models 2>&1 || true)     # one free read-only request per key
echo "$CHECK"
if echo "$CHECK" | grep -E "^(Anthropic|OpenAI|Gemini) " | awk '{print $NF}' | grep -qv "^200$"; then
  echo "a model key does not answer 200 in this shell; not starting"; exit 1
fi
if pgrep -u "$USER" -f "virtual_committee.py (run|integrate)" > /dev/null; then
  echo "a virtual_committee.py run is already active; not starting"; exit 1
fi
nohup bash run_all_steps.sh > run_all.out 2>&1 &
echo "started (pid $!); follow with: tail -f \"$PWD/run_all.out\""
