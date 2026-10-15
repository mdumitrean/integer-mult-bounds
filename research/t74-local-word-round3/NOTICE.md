# Notice

New files: Marius-Paul Dumitrean, Apache-2.0, prepared with substantial AI assistance (Anthropic Claude, via Claude Code).

Reused and adapted code, all Apache-2.0:
- `A-extra/scripts/sk2.py` and `sk_multi.py`, and `B-interact/tools/` (the split-key models): refactorings and extensions of
  `tools/skkernel.py` from PR #2142 (Ian Libânio, research/t74-split-key-kernel-search), which builds on
  `abkernel.py` from PR #1957 (Rohan Arun, research/t74-k554-local-exhaustion). Their headers name the source.
- Relaxation reference data and the vendored toolkit used for model comparisons: PR #1957 and PR #2142, at the heads in
  `INPUTS.json`; they are referenced, not copied.
- `D-families/scripts/frames_x.py`: a copy of `frames.py` from PR #1186's exact frame toolkit (ours) with an A-end cap hook.
- The words are not copied here. They are PR #1672's (Jeremy Kothe / LeverRank) pivot-554 kernel on our PR #1625
  pivot-566 words, in the PR #1319/#1297 lineage (Rohan Arun) and its retained ancestry.
