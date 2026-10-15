#!/bin/sh
# wait for a free slot (< 4 jobs), then: sk2-model cross-check of B783 (depth 2), then the long B1177 rerun
cd r6/agents/D-depth2
while [ "$(ps -axo command | grep 'scripts/run2' | grep 'runs/d2\|runs/chk' | grep -v grep | grep -vc capped)" -ge 4 ]; do sleep 5; done
export IMB_B=0.001679754956125544 CB_B=0.001679754956125544 IMB_ROOT=r3/main GEN2_VERBOSE=1 SK2_WORKERS=1
echo "start chk $(date -u +%H:%M:%SZ)"
python3 -B r6/agents/D-depth2/../../../r3/agents/B-interact/tools/capped.py 600 6 runs/chk-783-sk2model/log.txt -- python3 -B scripts/run2_sk2model.py r3/inputs/gauge44-word-566-554.json.gz runs/chk-783-sk2model/spec.json runs/chk-783-sk2model/out.json
echo "start d2L-1177 $(date -u +%H:%M:%SZ)"
sh scripts/lane_long.sh d2L-1177
echo "done $(date -u +%H:%M:%SZ)"
