#!/bin/bash
# run_rest.sh: the Anthropic and OpenAI cells of the Econ virtual committee (22 cells), to be started from a shell whose
# environment holds valid COMMITTEE_ANTHROPIC_API_KEY and OPENAI_API_KEY (the tool shell of the editor had stale values on
# 10 Oct 2026). Existing valid cells are skipped; the Gemini cells are already done. Runs detached with nohup; log in
# run_rest.out. Afterwards: collect, aggregate, pool (see README). Keys are read from the environment only.
set -euo pipefail
cd "/project/jevans/Dawoon/Nobel Prize/Econ/06_candidates"
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib
PY=/project/jevans/Dawoon/env/Curvature/bin/python           # by path: the login shell's hkg_venv must not be used
for v in COMMITTEE_ANTHROPIC_API_KEY OPENAI_API_KEY; do
  if [ -z "${!v:-}" ]; then echo "$v is not set in this shell"; exit 1; fi
done
# one free read-only request per key: abort unless both answer 200 (the 10 Oct 13:15 run got 401 from both)
CHECK=$($PY ../../experiment/preseen/check_keys.py --no-models 2>&1 || true)
echo "$CHECK"
if echo "$CHECK" | grep -E "^(Anthropic|OpenAI) " | awk '{print $NF}' | grep -qv "^200$"; then
  echo "Anthropic or OpenAI key does not answer 200 in this shell; not starting"; exit 1
fi
nohup $PY virtual_committee.py run --providers anthropic openai --workers 3 > run_rest.out 2>&1 &
echo "started (pid $!); follow with: tail -f run_rest.out"
