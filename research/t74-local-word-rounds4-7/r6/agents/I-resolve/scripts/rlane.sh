#!/bin/sh
# usage: rlane.sh NAME SYSTEMDIR TOTAL ITER MAXADD
cd r6/agents/I-resolve
mkdir -p runs/$1
python3 -B r3/agents/B-interact/tools/capped.py $(( $3 + 300 )) 6 runs/$1/log.txt -- python3 -B scripts/rowgen.py $2 runs/$1/ROWGEN.json $3 $4 $5
