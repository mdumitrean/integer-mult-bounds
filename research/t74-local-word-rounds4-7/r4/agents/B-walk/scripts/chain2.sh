#!/bin/sh
# after the positive batch, re-search the next 150 eligible neutral pre-moves
W=$(cd "$(dirname "$0")/.." && pwd)
until grep -q '^EXIT' "$W/out/LR2-pos.log" 2>/dev/null; do sleep 10; done
cd "$W" && timeout 2400 python3 -B scripts/lr2.py out/SEL2.json out/LR2b.jsonl --max2 40 > out/LR2b.log 2>&1; echo "EXIT $?" >> out/LR2b.log
