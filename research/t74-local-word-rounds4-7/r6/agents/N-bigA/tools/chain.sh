#!/bin/sh
# chain.sh PREV NEXT: wait until run PREV's capped wrapper has exited, then run NEXT (same word, capped).
S=$(cd "$(dirname "$0")/../../../.." && pwd)   # scratchpad/
D=$S/r5/agents/D-compsplit; PY=python3; W=$S/r3/inputs/gauge44-word-566-554.json.gz
cd $D || exit 1
until grep -q '^\[capped\]' out/run-$1.cap.log; do sleep 5; done
IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B tools/capped.py 3000 6 out/run-$2.cap.log -- $PY -B tools/run3.py $W out/SPEC-$2.json out/RUN-$2.json > out/run-$2.log 2>&1
echo "chain $1 -> $2 done"
