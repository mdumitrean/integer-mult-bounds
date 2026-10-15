# Notice

New files: Marius-Paul Dumitrean, Apache-2.0, prepared with substantial AI assistance (Anthropic Claude, via Claude Code).

Reused or adapted code (Apache-2.0), named in each script's header where applicable:
- split-key search models adapted from PR #2142 (Ian Libânio, `tools/skkernel.py`) and PR #1957 (Rohan Arun,
  `abkernel.py`, relaxation data);
- the exact frame toolkit of PR #1186 (ours), with copies modified per agent where noted (e.g. `frames_x.py`, the
  `tail_caps` switch, `absorb.py`);
- reproductions of main's construction scripts (`research/gauge44-slots/construction/reproduce.py`, PR635's pipeline,
  PR987's slot search `research/complex-u10-t37/construction/u10/discovery/`), run from pinned sources and not vendored here;
- PR1319's hosting code (`reconstruct.py`, `independent_core.py`), used for owner-map checks.

The supplier words are referenced by pin (`INPUTS.json`), not copied: PR #1672's pivot-554 kernel on PR #1625's
pivot-566 words, in the PR #1319/#1297 lineage and its retained ancestry.
