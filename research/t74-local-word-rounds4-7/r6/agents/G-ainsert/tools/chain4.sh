#!/bin/sh
# chain4.sh RUN1 [RUN2 ...]: run each spec out/SPEC-RUN.json on the base word one after another, each capped (timeout + 6 GiB RSS).
S=$(cd "$(dirname "$0")/../../../.." && pwd)
G=$S/r6/agents/G-ainsert; PY=python3; W=$S/r3/inputs/gauge44-word-566-554.json.gz
cd $G || exit 1
for r in "$@"; do
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B tools/capped.py 2700 6 out/run-$r.cap.log -- $PY -B tools/run4.py $W out/SPEC-$r.json out/RUN-$r.json
  echo "done $r $(date -u +%H:%M:%SZ)" >> out/chain.log
done
