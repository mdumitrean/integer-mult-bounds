#!/bin/sh
# lane3b.sh (M-bigB): replaces lane 3 after B588: price B588 if needed, then structural reruns (pair_nogood, K=8) of the
# jobs whose first proposals all priced >= 0, then lane 3's remaining jobs.
S=.; M=$S/r6/agents/M-bigB; D=$S/r5/agents/D-compsplit; PY=python3
W=$S/r3/inputs/gauge44-word-566-554.json.gz
cd $M || exit 1
until grep -q '^\[capped\]' runs/B588.cap.log 2>/dev/null; do sleep 5; done
np=$($PY -I -c "import json,sys; r=json.load(open(sys.argv[1])); print(sum(len(x['proposals']) for x in r))" runs/RUN-B588.json 2>/dev/null || echo 0)
if [ "${np:-0}" -gt 0 ]; then IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 $PY -B $D/tools/capped.py 900 6 runs/P-B588.cap.log -- $PY -B $D/tools/price3.py $W runs/RUN-B588.json runs/PRICED-B588.json runs/audit-B588 > runs/P-B588.log 2>&1; fi
echo "done B588 exit (orphan) proposals ${np:-0} $(date -u +%H:%M:%SZ)" >> runs/worker3.log
for r in 949 950 1053 808; do
  printf '{"jobs": [[["B", %s]]], "K": 8, "tl": 60, "cut_iters": 20, "ban_reinsert": true, "pair_nogood": true}\n' "$r" > runs/SPEC-R$r.json
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B $D/tools/capped.py 900 6 runs/R$r.cap.log -- $PY -B scripts/run5.py $W runs/SPEC-R$r.json runs/RUN-R$r.json > runs/R$r.log 2>&1
  np=$($PY -I -c "import json,sys; r=json.load(open(sys.argv[1])); print(sum(len(x['proposals']) for x in r))" runs/RUN-R$r.json 2>/dev/null || echo 0)
  if [ "${np:-0}" -gt 0 ]; then IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 $PY -B $D/tools/capped.py 900 6 runs/P-R$r.cap.log -- $PY -B $D/tools/price3.py $W runs/RUN-R$r.json runs/PRICED-R$r.json runs/audit-R$r > runs/P-R$r.log 2>&1; fi
  echo "done R$r exit rerun proposals ${np:-0} $(date -u +%H:%M:%SZ)" >> runs/worker3.log
done
exec ./scripts/queue.sh 3 693 747 548 942 734 911 937 560 659 707 735 812 903 1182 518 775 973 989 1010 1411 1824 470 1568 1695 1675 849 645 1456 1635
