#!/bin/sh
# usage: settle.sh BINDEX : overrides (D = all sentinels excluded; C = exact lower-bound prices), ban-on row generation for
# both, then the independent SCIP/HiGHS re-solve of each final restricted model.
cd r6/agents/I-resolve; T=$1; P=python3
$P -B scripts/override.py runs/nd${T}U runs/s${T}/SENTINEL.json runs/nd${T}U/OVR-corrected.json
$P -B -c "import json, numpy as np; cm=np.load('runs/nd${T}U/system.npz')['candmeta']; ex=[j for j,(x,y,p,c) in enumerate(cm.tolist()) if c>=2**59]; json.dump(dict(cost={}, exclude=ex), open('runs/nd${T}U/OVR-D.json','w')); print('D excludes', len(ex))"
for V in D C; do
  if [ $V = D ]; then O=OVR-D; else O=OVR-corrected; fi
  rm -rf runs/rg${T}$V; sh scripts/rlane2.sh rg${T}$V runs/nd${T}U 1500 ${ITER:-180} ${MAXADD:-60} runs/nd${T}U/$O.json
  VERIFY_TL=${VTL:-240} VERIFY_NOBAN=${VNOBAN:-0} $P -B scripts/verify_small.py runs/nd${T}U runs/rg${T}$V/ROWGEN.json runs/nd${T}U/$O.json > runs/rg${T}$V/verify.log 2>&1
done
