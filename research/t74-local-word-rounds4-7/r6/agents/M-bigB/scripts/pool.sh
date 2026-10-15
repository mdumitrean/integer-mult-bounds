#!/bin/sh
# pool.sh NAME: work-stealing worker over out/POOL.json (claims by atomic mkdir in runs/claims/). Bxxx = census job (K=4),
# Rxxx = structural rerun (pair_nogood, K=8). Each job capped (600 s / 900 s, 6 GiB); exact proposals priced by price3.py.
S=$(cd "$(dirname "$0")/../../../.." && pwd)
M=$S/r6/agents/M-bigB; D=$S/r5/agents/D-compsplit; PY=python3
W=$S/r3/inputs/gauge44-word-566-554.json.gz; me=$1
cd $M || exit 1; mkdir -p runs/claims
for j in $($PY -I -c "import json; print(' '.join(json.load(open('out/POOL.json'))['pool']))"); do
  mkdir runs/claims/$j 2>/dev/null || continue
  r=${j#?}; kind=${j%"$r"}
  if [ "$kind" = R ]; then spec='"K": 8, "tl": 60, "cut_iters": 20, "ban_reinsert": true, "pair_nogood": true'; lim=900
  else spec='"K": 4, "tl": 60, "cut_iters": 15, "ban_reinsert": true'; lim=600; fi
  printf '{"jobs": [[["B", %s]]], %s}\n' "$r" "$spec" > runs/SPEC-$j.json
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B $D/tools/capped.py $lim 6 runs/$j.cap.log -- \
    $PY -B scripts/run5.py $W runs/SPEC-$j.json runs/RUN-$j.json > runs/$j.log 2>&1
  ec=$?
  np=$($PY -I -c "import json,sys; r=json.load(open(sys.argv[1])); print(sum(len(x['proposals']) for x in r))" runs/RUN-$j.json 2>/dev/null || echo 0)
  if [ "${np:-0}" -gt 0 ]; then
    IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 $PY -B $D/tools/capped.py 900 6 runs/P-$j.cap.log -- \
      $PY -B $D/tools/price3.py $W runs/RUN-$j.json runs/PRICED-$j.json runs/audit-$j > runs/P-$j.log 2>&1
  fi
  echo "done $j exit $ec proposals ${np:-0} $(date -u +%H:%M:%SZ)" >> runs/pool-$me.log
done
echo "pool $me finished $(date -u +%H:%M:%SZ)" >> runs/pool-$me.log
