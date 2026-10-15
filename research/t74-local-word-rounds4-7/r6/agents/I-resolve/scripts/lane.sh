#!/bin/sh
# usage: lane.sh NAME WORD BINDEX DEPTH TLIM [TIMEOUT_S]
cd r6/agents/I-resolve
export IMB_B=0.001679754956125544 CB_B=0.001679754956125544 IMB_ROOT=r3/main
mkdir -p runs/$1
python3 -B r3/agents/B-interact/tools/capped.py ${6:-2400} 6 runs/$1/log.txt -- python3 -B scripts/lpcert.py $2 $3 $4 runs/$1 $5
