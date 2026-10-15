#!/bin/sh
W=$(cd "$(dirname "$0")/.." && pwd)
until grep -q '^EXIT' "$W/out/LR2b.log" 2>/dev/null; do sleep 10; done
cd "$W" && timeout 900 python3 -B scripts/price2.py out/JOBS-shared2.json out/SHARED3.jsonl > out/SHARED3.log 2>&1; echo "EXIT $?" >> out/SHARED3.log
