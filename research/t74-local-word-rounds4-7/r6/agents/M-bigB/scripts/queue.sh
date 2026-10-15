#!/bin/sh
# queue.sh WORKER [REP...] (no REPs: lane WORKER of out/LANES.json): run each representative B deletion as its own capped process (600 s, 6 GiB) with run5.py on
# the base word, then price any exact proposals with r5 D's price3.py (compensation-aware; audit on negative deltas).
S=$(cd "$(dirname "$0")/../../../.." && pwd)
M=$S/r6/agents/M-bigB; D=$S/r5/agents/D-compsplit; PY=python3
W=$S/r3/inputs/gauge44-word-566-554.json.gz; w=$1; shift
cd $M || exit 1
if [ $# -eq 0 ]; then set -- $($PY -I -c "import json,sys; L=json.load(open('out/LANES.json'))[int(sys.argv[1])]; print(' '.join(str(r) for r in L))" $w); fi
for r in "$@"; do
  printf '{"jobs": [[["B", %s]]], "K": 4, "tl": 60, "cut_iters": 15, "ban_reinsert": true}\n' "$r" > runs/SPEC-B$r.json
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B $D/tools/capped.py 600 6 runs/B$r.cap.log -- \
    $PY -B scripts/run5.py $W runs/SPEC-B$r.json runs/RUN-B$r.json > runs/B$r.log 2>&1
  ec=$?
  np=$($PY -I -c "import json,sys; r=json.load(open(sys.argv[1])); print(sum(len(x['proposals']) for x in r))" runs/RUN-B$r.json 2>/dev/null || echo 0)
  if [ "${np:-0}" -gt 0 ]; then
    IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 $PY -B $D/tools/capped.py 900 6 runs/P-B$r.cap.log -- \
      $PY -B $D/tools/price3.py $W runs/RUN-B$r.json runs/PRICED-B$r.json runs/audit-B$r > runs/P-B$r.log 2>&1
  fi
  echo "done B$r exit $ec proposals ${np:-0} $(date -u +%H:%M:%SZ)" >> runs/worker$w.log
done
echo "worker $w finished $(date -u +%H:%M:%SZ)" >> runs/worker$w.log
