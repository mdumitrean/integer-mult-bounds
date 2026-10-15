#!/bin/sh
# lane.sh N: run M-bigB's run5.py (projected split-key, sentinels kept, ban_reinsert) on each word in runs/laneN.txt,
# then price any proposals with r5 D's price3.py; each process wrapped by r5 D's capped.py (900 s, 6 GiB).
S=.
W=$S/r6/agents/S-variants; D=$S/r5/agents/D-compsplit; M=$S/r6/agents/M-bigB; PY=python3
cd $W || exit 1
while read tag word; do
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B $D/tools/capped.py 1800 6 runs/$tag.cap.log -- $PY -B $M/scripts/run5.py $word runs/SPEC-$tag.json runs/RUN-$tag.json > runs/$tag.log 2>&1
  np=$($PY -I -c "import json,sys; r=json.load(open(sys.argv[1])); print(sum(len(x['proposals']) for x in r))" runs/RUN-$tag.json 2>/dev/null || echo 0)
  if [ "${np:-0}" -gt 0 ]; then IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 $PY -B $D/tools/capped.py 900 6 runs/P-$tag.cap.log -- $PY -B $D/tools/price3.py $word runs/RUN-$tag.json runs/PRICED-$tag.json runs/audit-$tag > runs/P-$tag.log 2>&1; fi
  echo "done $tag proposals ${np:-0} $(date -u +%H:%M:%SZ)" >> runs/lane$1.done
done < runs/lane$1.txt
echo "LANE $1 FINISHED $(date -u +%H:%M:%SZ)" >> runs/lane$1.done
