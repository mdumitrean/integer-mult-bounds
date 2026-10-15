#!/bin/sh
# usage: blane.sh NAME WORD BINDEX DEPTH VARIANT : build a non-deduplicated system (no LP)
cd r6/agents/I-resolve
export IMB_B=0.001679754956125544 CB_B=0.001679754956125544 IMB_ROOT=r3/main LPCERT_NOLP=1 LPCERT_NODEDUP=1 LPCERT_VARIANT=$5
mkdir -p runs/$1
python3 -B r3/agents/B-interact/tools/capped.py 1200 6 runs/$1/log.txt -- python3 -B scripts/lpcert.py $2 $3 $4 runs/$1 1
