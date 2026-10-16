# Recorded execution and artifact verification

The environment is the original `.venv-styles` established by the user-requested
requirements and smoke test. No package was added for this continuation.
The scientific launch commands, from the repository worktree root, were:

```sh
.venv-styles/bin/python -I -B -X pycache_prefix=research/styles-r11/results/CONTINUATION-04/E1/.bytecode-v1 research/styles-r11/pipeline/continuation04/run_registered.py --registration-sha256 1b9d4a5179e3a76f0cd2d5347c8143a89b08e1e8e2284881ae13f5f39c5ef253 --attempt v1
.venv-styles/bin/python -I -B -X pycache_prefix=research/styles-r11/results/CONTINUATION-04/E2/.bytecode-v1 research/styles-r11/pipeline/continuation04/run_other_registered.py --registration-sha256 566a7d255ceb82ecb56377784cebfc15d3dbab55fc88a2acb8d4737615ffd2ff --attempt v1
```

Their stdout/stderr are retained in each milestone's `EXECUTION-v1.log`.
The source pins, memory projections, task specifications, task receipts,
per-seed RESULT files and terminal RUN files are all preserved. Preregistration
preceded preparation, and implementation hashes were frozen before execution.

These are historical commands, not instructions to overwrite a completed run.
The runners intentionally reject a completed registry row, existing attempt
directory or expired launch window. An independently authorized replay must
use a separate namespace, an explicit fresh schedule and implementation pins,
while preserving the exact scientific domain and all original source bytes.
The two-null lane stop bars a further search extension in this round.

The administrative audit is implemented in
`pipeline/continuation04/audit_round.py`; its completed result is `AUDIT.json`.
It checks data/code hashes and recorded outcomes without rerunning a scientific
test. It too writes its output exclusively. `FINAL-MANIFEST.json` lists every
delivered continuation file except itself. Every acquired `.py` program is
stored as `.py.txt` and remains inert; it must not be imported or executed.

The final source/status checkpoint is separate from the frozen experiments.
Its newer metadata does not silently replace a scientific input or retrospectively
change a verdict.
