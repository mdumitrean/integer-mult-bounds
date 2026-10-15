#!/bin/sh
# sched.sh MAXPROC RUN...: start lane_long.sh RUN whenever fewer than MAXPROC run2.py jobs of this agent are running.
# A rerun of d2-X is skipped if d2-X already ended INFEASIBLE or found a proposal.
cd "$(dirname "$0")/.."; MAX=$1; shift
for r in "$@"; do
  base=runs/d2-${r#d2L-}/log.txt
  while [ -f "$base" ] && ! grep -q 'capped\] exit' "$base"; do sleep 5; done
  if [ -f "$base" ] && grep -qE 'r1 stop INFEASIBLE|r1 terms' "$base"; then echo "skip $r"; continue; fi
  while [ "$(ps -axo command | grep 'scripts/run2.py' | grep 'runs/d2' | grep -v grep | grep -vc capped)" -ge "$MAX" ]; do sleep 5; done
  echo "start $r $(date -u +%H:%M:%SZ)"; nohup sh scripts/lane_long.sh "$r" > "runs/$r.lane.log" 2>&1 &
  sleep 3
done
