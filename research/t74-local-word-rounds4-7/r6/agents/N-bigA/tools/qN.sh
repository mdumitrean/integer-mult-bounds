#!/bin/sh
# qN.sh M1 [M2 ...]: for each member spec out/SPEC-mM.json: row generation (rgN.sh) then exact pricing of any proposals.
S=$(cd "$(dirname "$0")/../../../.." && pwd); N=$S/r6/agents/N-bigA; PY=python3
W=$S/r3/inputs/gauge44-word-566-554.json.gz; cd $N || exit 1
for m in "$@"; do
  sh tools/rgN.sh m$m m$m 900 300
  if [ -s out/RG-m$m.json ] && grep -q '"edit_ab"' out/RG-m$m.json; then
    IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 CB_B=0.001679754956125544 $PY -B tools/capped.py 1200 6 out/price-rg-m$m.cap.log -- $PY -B tools/price3.py $W out/RG-m$m.json out/PRICED-rg-m$m.json out/audit-rg-m$m
    echo "priced rg m$m $(date -u +%H:%M:%SZ)" >> out/chain.log
  fi
done
