#!/bin/sh
# priceRG.sh NAME...: exact pricing of out/RG-NAME.json proposals (price3.py), capped.
S=$(cd "$(dirname "$0")/../../../.." && pwd); N=$S/r6/agents/N-bigA; PY=python3
W=$S/r3/inputs/gauge44-word-566-554.json.gz; cd $N || exit 1
for r in "$@"; do
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 CB_B=0.001679754956125544 $PY -B tools/capped.py 1200 6 out/price-rg-$r.cap.log -- $PY -B tools/price3.py $W out/RG-$r.json out/PRICED-rg-$r.json out/audit-rg-$r
  echo "priced rg $r $(date -u +%H:%M:%SZ)" >> out/chain.log
done
