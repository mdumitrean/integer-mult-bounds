#!/bin/sh
# rg.sh NAME REP...: for each REP export sk5's system (export_sys.py) and settle it with r6 I-resolve's rowgen.py
# (ROWGEN_BAN=0: restrictions are relaxations, INFEASIBLE = proof); then join the pool as worker NAME.
S=$(cd "$(dirname "$0")/../../../.." && pwd)
M=$S/r6/agents/M-bigB; D=$S/r5/agents/D-compsplit; I=$S/r6/agents/I-resolve/scripts; PY=python3
W=$S/r3/inputs/gauge44-word-566-554.json.gz; me=$1; shift
cd $M || exit 1
for r in "$@"; do
  mkdir -p runs/sys-B$r
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 $PY -B $D/tools/capped.py 900 6 runs/sys-B$r.cap.log -- $PY -B scripts/export_sys.py $W $r runs/sys-B$r > runs/sys-B$r.log 2>&1
  ROWGEN_BAN=0 $PY -B $D/tools/capped.py 1500 6 runs/rg-B$r.cap.log -- $PY -B $I/rowgen.py runs/sys-B$r runs/RG-B$r.json 1400 120 400 > runs/rg-B$r.log 2>&1
  echo "done rg B$r $(tail -1 runs/rg-B$r.cap.log) $(date -u +%H:%M:%SZ)" >> runs/pool-$me.log
done
exec ./scripts/pool.sh $me
