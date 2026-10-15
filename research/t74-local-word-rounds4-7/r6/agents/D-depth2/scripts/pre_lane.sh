#!/bin/sh
cd r6/agents/D-depth2
while [ "$(ps -axo command | grep 'scripts/run2' | grep 'runs/d2\|runs/chk\|runs/ctl' | grep -v grep | grep -vc capped)" -ge 4 ]; do sleep 5; done
export IMB_B=0.001679754956125544 CB_B=0.001679754956125544 IMB_ROOT=r3/main GEN2_VERBOSE=1 SK2_WORKERS=1 GEN2_LIN=2 GEN2_PRESOLVE=1
echo "start ctl2P $(date -u +%H:%M:%SZ)"
python3 -B r6/agents/D-depth2/../../../r3/agents/B-interact/tools/capped.py 600 6 runs/ctl2P/log.txt -- python3 -B scripts/run2.py r3/agents/B-interact/work/research/t74-k554-local-exhaustion/inputs/step0-gauge44.json.gz runs/ctl2P/spec.json runs/ctl2P/out.json
echo "start d2P-822 $(date -u +%H:%M:%SZ)"
sh scripts/lane_pre.sh d2P-822
echo "done $(date -u +%H:%M:%SZ)"
