#!/bin/bash
# Sequential C-repair chain after the base-word fusion sweep (never more than 3 workers at once).
export IMB_ROOT=r3/main IMB_B=0.001679754956125544
cd r3/agents/C-repair
until grep -q '\[capped\]' runs/repair-gauge44.log; do sleep 5; done
W=r3/inputs
python3 -B capped.py --cap-gib 6 --wall 900  --log runs/xj-gauge44.log     -- python3 -B xjsweep.py toolkit $W/gauge44-word-566-554.json.gz runs/xj-gauge44.json --workers 3 --timeout 90 --maxf 3
python3 -B capped.py --cap-gib 6 --wall 1500 --log runs/pos-gauge44.log    -- python3 -B posweep.py toolkit $W/gauge44-word-566-554.json.gz runs/pos-gauge44.json --workers 3 --timeout 90
python3 -B capped.py --cap-gib 6 --wall 2400 --log runs/repair-extra.log   -- python3 -B repair_rec.py toolkit $W/extra-word-566-554.json.gz runs/repair-extra.json --workers 3 --timeout 90 --max-tasks-per-child 50
python3 -B capped.py --cap-gib 6 --wall 900  --log runs/xj-extra.log       -- python3 -B xjsweep.py toolkit $W/extra-word-566-554.json.gz runs/xj-extra.json --workers 3 --timeout 90 --maxf 3
python3 -B capped.py --cap-gib 6 --wall 1500 --log runs/pos-extra.log      -- python3 -B posweep.py toolkit $W/extra-word-566-554.json.gz runs/pos-extra.json --workers 3 --timeout 90
echo CHAIN-DONE > runs/chain.done
