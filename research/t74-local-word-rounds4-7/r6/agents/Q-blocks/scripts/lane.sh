#!/bin/sh
# lane.sh (Q-blocks): run6 block jobs one after another (capped: 900 s, 6 GiB), then price3 any proposals.
# usage: lane.sh LANE TAG:SPECJSON ...
S=.; Q=$S/r6/agents/Q-blocks; D=$S/r5/agents/D-compsplit; N=$S/r6/agents/N-bigA
PY=python3; W=$S/r3/inputs/gauge44-word-566-554.json.gz
cd $Q || exit 1; lane=$1; shift
for job in "$@"; do
  tag=${job%%:*}; spec=${job#*:}; printf '%s\n' "$spec" > runs/SPEC-$tag.json
  IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 SK2_WORKERS=1 $PY -B $D/tools/capped.py 900 6 runs/$tag.cap.log -- $PY -B scripts/run6.py $W runs/SPEC-$tag.json runs/RUN-$tag.json
  np=$($PY -I -c "import json,sys; r=json.load(open(sys.argv[1])); print(sum(len(x['proposals']) for x in r))" runs/RUN-$tag.json 2>/dev/null || echo 0)
  if [ "${np:-0}" -gt 0 ]; then IMB_ROOT=$S/r3/main IMB_B=0.001679754956125544 $PY -B $D/tools/capped.py 900 6 runs/P-$tag.cap.log -- $PY -B $N/tools/price3.py $W runs/RUN-$tag.json runs/PRICED-$tag.json runs/audit-$tag; fi
  echo "done $tag proposals ${np:-0} $(date -u +%H:%M:%SZ)" >> runs/lane$lane.log
done
echo "lane $lane finished $(date -u +%H:%M:%SZ)" >> runs/lane$lane.log
