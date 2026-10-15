#!/bin/sh
# rgN.sh NAME SPECRUN TOTAL_S ITER_S: row generation (rowgen4.py) for out/SPEC-SPECRUN.json -> out/RG-NAME.json, capped.
S=$(cd "$(dirname "$0")/../../../.." && pwd)
N=$S/r6/agents/N-bigA; PY=python3; W=$S/r3/inputs/gauge44-word-566-554.json.gz
cd $N || exit 1
IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 CB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B tools/capped.py $(( $3 + 600 )) 6 out/rg-$1.cap.log -- $PY -B tools/rowgen4.py $W out/SPEC-$2.json out/RG-$1.json $3 $4
echo "rg $1 $(date -u +%H:%M:%SZ)" >> out/chain.log
