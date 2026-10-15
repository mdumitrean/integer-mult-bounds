#!/bin/sh
# queue.sh PREV RUN1 [RUN2 ...]: wait until run PREV's capped wrapper has exited (PREV=none: start now), then run each
# RUN (spec out/SPEC-RUN.json on the base word) one after another, each capped (timeout + 6 GiB RSS).
S=$(cd "$(dirname "$0")/../../../.." && pwd)   # scratchpad/
D=$S/r5/agents/D-compsplit; PY=python3; W=$S/r3/inputs/gauge44-word-566-554.json.gz
cd $D || exit 1
prev=$1; shift
if [ "$prev" != none ]; then until grep -q '^\[capped\]' out/run-$prev.cap.log; do sleep 5; done; fi
for r in "$@"; do
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B tools/capped.py 3000 6 out/run-$r.cap.log -- $PY -B tools/run3.py $W out/SPEC-$r.json out/RUN-$r.json > out/run-$r.log 2>&1
  echo "done $r $(date -u +%H:%M:%SZ)"
done
