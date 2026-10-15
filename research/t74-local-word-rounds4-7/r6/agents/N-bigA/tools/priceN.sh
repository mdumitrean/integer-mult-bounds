#!/bin/sh
# priceN.sh RUN1 [RUN2 ...]: exact compensation-aware pricing (price3.py) of each out/RUN-RUN.json, capped.
S=$(cd "$(dirname "$0")/../../../.." && pwd)
N=$S/r6/agents/N-bigA; PY=python3; W=$S/r3/inputs/gauge44-word-566-554.json.gz
cd $N || exit 1
for r in "$@"; do
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 CB_B=0.001679754956125544 $PY -B tools/capped.py 1800 6 out/price-$r.cap.log -- $PY -B tools/price3.py $W out/RUN-$r.json out/PRICED-$r.json out/audit-$r
  echo "priced $r $(date -u +%H:%M:%SZ)" >> out/chain.log
done
