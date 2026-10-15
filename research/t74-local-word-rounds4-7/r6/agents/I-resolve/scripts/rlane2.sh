#!/bin/sh
# usage: rlane2.sh NAME SYSTEMDIR TOTAL ITER MAXADD OVERRIDE
cd r6/agents/I-resolve
mkdir -p runs/$1
ROWGEN_BAN=1 python3 -B r3/agents/B-interact/tools/capped.py $(( $3 + 300 )) 6 runs/$1/log.txt -- python3 -B scripts/rowgen.py $2 runs/$1/ROWGEN.json $3 $4 $5 $6
