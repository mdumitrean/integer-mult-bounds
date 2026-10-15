# r6 R-apeep: exact peephole equivalents of A-section windows (566+554 base word)

**Outcome: no gain, kappa unchanged.** Nothing committed, pushed or posted.

## Method
- `scripts/apeep.py` (adapted from r6 P-peephole's `peep.py`): for a window A[i:i+k] (k = 2, 3, 4) on registers R (no A
  gate touches a port, so R never contains one), its exact map; alternative sequences of length L <= k (k = 2: also L = 3)
  over R with adds t += c s, c in +-{1/4, 1/2, 1, 2, 4}, and, when the window has a scale, scales +-2, +-1/2, -1; found by
  meet-in-the-middle in float64 (exact for these dyadics) and re-verified in exact rationals. Unlike the B search, pure
  permutations (commuting reorders) are kept: in A they were only tried in two pivot blocks (r4 A-reroute, 459 moves).
  Excluded: the original, consecutive same-(t, s) gates, scale/inverse-scale pairs. k = 4 windows on more than 6 registers
  are skipped (232 of 3,448).
- `scripts/aenum.py`: all windows: k = 2 (3,450 windows, 22,010 alternatives), k = 3 (3,449; 13,636), k = 4 (3,216; 59,000).
  `scripts/aplan.py` dedupes by the resulting A section (66,805 unique) and builds a quota plan (`out/PLAN.jsonl`, 7,955):
  every strict reduction (536), every same-length rewrite for k = 2, 3 (2,959), k = 4 same-length rewrites in large-deletion
  windows (56) plus 1,200 sampled nonzero-frame ones, permutations in large-deletion windows (k = 2 all 404, k = 3 900,
  k = 4 600 sampled), 900 sampled k = 2 -> 3 rewrites in large-deletion windows and 400 k = 2 nonzero-frame permutations.
  "Large-deletion window": contains a gate with an uncompensated deletion gain <= -6,781 (r3 A-extra relaxA-extra.json).
- `scripts/aprice.py`: r5 D's compensation-aware pricer (`absorb.AbsorbPricer.price_ab`): section-tagged A edits, static
  program rules, the whole A+cut+B+tail map checked (up to absorbed port columns), compensation re-derived, cone caps
  recomputed, exact optimal frames with cut equality (toolkit rev3, b = 0.001679754956125544). 4 workers, 90 s per pricing,
  maxtasksperchild = 100, run stops if a worker's peak RSS passes 5.5 GiB; 45-minute budget.
- Calibration (`out/CALIB.json`, `scripts/acalib.py`): base cost 11,683,290,250 reproduced; identity substitutions at
  k = 2, 3, 4 price ok, delta 0, compensation unchanged (7,208 gates); r4 A-reroute's neutral move "A1248 to 1247" is
  rediscovered as a permutation equivalent of window [1247, 1248] and prices delta 0; an inexact control is rejected.

## Results
All 7,955 planned alternatives were priced (`out/PRICED.jsonl`, `out/SUMMARY.json`): **7,852 at delta 0, 103
frame-infeasible, 0 negative.** Peak worker RSS 0.70 GiB, 1.3 s per pricing.

| Group (deduped) | Priced | Outcome |
|---|---:|---|
| Strict reductions k=2->1, 3->2, 4->3 (all) | 536 | all delta 0 |
| Same-length rewrites, k = 2 (all) | 513 | all delta 0 |
| Same-length rewrites, k = 3 (all) | 2,446 | 2,432 delta 0; the 14 in large-deletion windows infeasible |
| Same-length rewrites, k = 4: large-deletion windows (all 56) + 1,200 sampled | 1,256 | 1,200 delta 0; all 56 large-deletion ones infeasible |
| Commuting reorders, large-deletion windows: k = 2 all 404, k = 3 900, k = 4 600 sampled | 1,904 | 1,882 delta 0, 22 infeasible |
| Commuting reorders, k = 2 nonzero-frame windows (sampled) | 400 | all delta 0 |
| k = 2 -> 3 rewrites in large-deletion windows (sampled) | 900 | 889 delta 0, 11 infeasible |

Every priced edit keeps the whole call map exactly (window maps verified in exact rationals; the pricer re-checks the A+cut+B+tail
map), and the re-derived compensation stays 7,208 gates. As with r6 P-peephole on B, shorter or rewritten A programs (e.g.
`A1482-A1483 -> 240 *= 2`, a 2 -> 1 reduction) cost exactly the same frames: the frame optimum is insensitive to these local
rewrites, and in the large-deletion windows any change of the window's internal structure is frame-infeasible. No negative
delta occurred, so no interval, audit, native-chain or extra-word check was needed (`scripts/averify.py` is ready).

## Limits
Not priced: 58,850 deduped alternatives (mostly k = 4 commuting reorders and same-length rewrites in nonzero/zero-frame
windows outside the large-deletion classes, and 2 -> 3 rewrites outside them); k = 4 windows on more than 6 registers (232);
k = 5 windows; rewrites using an extra scratch register; the extra word (same program, so the same edits apply). Finite
searches in one frame model at fixed b, not a supplier lower bound.

Evidence: `out/SUMMARY.json`, `out/PRICED.jsonl`, `out/PLAN.jsonl`, `out/ALT-k{2,3,4}.jsonl`, `out/CALIB.json`, logs;
scripts in `scripts/` (`apeep.py`, `aenum.py`, `aplan.py`, `aprice.py`, `acalib.py`, `averify.py`, `asummary.py`, `absorb.py`
from r5 D / r6 G). Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
