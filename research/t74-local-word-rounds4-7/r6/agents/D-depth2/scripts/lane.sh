#!/bin/sh
# usage: lane.sh RUN... : run each run dir's spec sequentially under capped.py (900 s, 6 GiB)
cd r6/agents/D-depth2
export IMB_B=0.001679754956125544 CB_B=0.001679754956125544 IMB_ROOT=r3/main GEN2_VERBOSE=1 SK2_WORKERS=1
for r in "$@"; do
  python3 -B r6/agents/D-depth2/../../../r3/agents/B-interact/tools/capped.py 900 6 runs/$r/log.txt -- python3 -B scripts/run2.py r3/inputs/gauge44-word-566-554.json.gz runs/$r/spec.json runs/$r/out.json
done
