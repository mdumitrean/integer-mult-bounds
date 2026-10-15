# r6 P-peephole: exact peephole equivalents of B windows (566+554 base word)

**Outcome: no gain, kappa unchanged.** 13,445 exact alternatives enumerated, 10,265 priced; every priced one is
Delta = 0, +4,925 (18) or frame-infeasible (946). Nothing committed or posted.

## Method
- `scripts/peep.py`: for a window B[i:i+k] on registers R, its exact map; alternatives of length L over R (adds with
  coefficients +-{1/4,1/2,1,2,4}, auditor's non-target-reads-target rule; scales +-2, +-1/2, -1 if the window has a
  scale) found by meet-in-the-middle in float64 (exact for these dyadics) and re-verified in exact rationals. Excluded:
  the original, pure permutations (commuting reorders, covered by #1957/r3), consecutive same-(t,s) gates.
- `scripts/enumerate.py`, `scripts/price_alts.py` (rev3 harness at b = 0.001679754956125544: exact screen, static rules,
  derived compensation, cone caps, certified frames; 4 workers, 90 s deadline, RSS limit, maxtasksperchild).
- Calibration (`out/CALIB0.json`, `scripts/test_calib.py`): identity substitutions price Delta = 0; r3 D's neutral
  re-timing FW-42-past43-to44 is rediscovered as a k=2 -> 3-gate equivalent.

## Results (`EVIDENCE.json`, `out/PRICED.jsonl`)
| Group | Enumerated | Priced | Outcome |
|---|---:|---:|---|
| Strict reductions (k=3->2, k=4->3, k=5->4) | 592 | 592 | all Delta = 0 |
| k=4 same-length rewrites | 2,166 | 2,166 | all Delta = 0 |
| k=3 same-length rewrites | 334 | 334 | all Delta = 0 |
| k=2 two-gate rewrites (scale/add swaps of butterfly halves) | 56 | 56 | all Delta = 0 |
| k=2 three-gate rewrites (compensated crossings) | 10,297 | 7,117 | 6,153 Delta 0, 18 +4,925, 946 infeasible |

The reductions include every donor window `h += c q; t += a h; h -= c q` -> `t += a c q; t += a h` (a direct read): shorter
programs, same frames cost. So the frame optimum is insensitive to these local rewrites.

## Limits
k=4/5 windows touching more than 6 registers were skipped (778 / 1,066); k=5 alternatives limited to 4 gates; no extra
scratch registers; 3,180 lowest-priority k=2 three-gate rewrites (on windows touching no large-deletion gate) unpriced.
No negative delta arose, so no audit/native/extra-word checks were needed (`scripts/verify_gain.py` is ready).
