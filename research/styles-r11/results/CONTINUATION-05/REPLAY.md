# Continuation 05 replay and receipt verification

Use the existing isolated environment from the repository root. Acquired PR
Python files remain inert `.py.txt`; do not import or execute them.

```
.venv-styles/bin/python -I -B research/styles-r11/pipeline/continuation05/audit_round.py
```

This administrative command verifies saved receipts and their source hashes,
seed agreement, package manifest, attribution, resource limits and preservation
of the prior evidence. It does not rerun science or overwrite an existing audit.
The final manifest covers current-round source/data/results except itself and
AUDIT.json; the audit and Git commit bind the remaining evidence.

The exact executed scientific command was:

```
.venv-styles/bin/python -I -B -X pycache_prefix=research/styles-r11/results/CONTINUATION-05/unused-pycache-r2-v1 research/styles-r11/pipeline/continuation05/run_registered.py --registration-sha256 9909c361dd712d39ca3b59263902c75fa1110f2923f5308748889e9e8a60a691 --attempt v1
```

Its frozen deadline was 16:51:55 UTC, with a checkpoint at 17:06:55 UTC on 2026-10-16.
Do not rerun that command over completed evidence or bypass its deadline.
A future replay requires a new isolated output directory, preregistered schedule,
implementation pins and attribution. Preserve all prior sources and records.
All parallel scientific work must still use pipeline/pool.py with the registered
memory projection, worker count, RSS/time caps and parent-only large-object load.

The SOURCE archives contain exact launch bytes. The R1 implementation was
preserved unexecuted for the static retirement explanation; no R1 RUN or RESULT
exists. R2 has 206 tasks: six controls, four references, four censuses, and
192 attempted prices. Candidate price completion is zero because every frame
construction is unresolved; a pool OK receipt does not mean a priced candidate.
