# r10 I-restore: making ordinary helpers restorable (no gain)

Base: F-lenders' double-move words r10/agents/F-lenders/words/{b,e}-30_564_667-31_565_669.cert.json.gz (kappa
0.001717794984118634663827; inventory {4:26,5:2,7:62,8:78,9:240}). PR list refreshed 21:58Z and 22:21Z: no new kappa claim
above #2766/#2767 (0.001717256973467002).

## Restore rule (pinned auditor vendor/audit_local_pr2679.py, run_borrow sections 4-6)
A restored (cold) helper c has end frame U = helper_final[c]; width = dim U - dim start. Forward condition: at the end of the
forward program rows[c] == {c: 1} and no other live row contains c's input; the derived inverse-reverse cleanup at FULL
replaces c by a private zero buffer (+1 physical row). Every gate's frame is shared by both of its registers afterwards.

## Census (scripts/anat.py; both words identical)
336 non-restored helpers; all but one sit below dim 9 before the final climb ((start, pre-end): (0,6) 24, (0,7) 34,
(0,8) 181, (1,6) 8, (1,7) 8, (1,8) 54, (2,6) 24, (4,8) 2, (0,9) 1). None has a clean forward-end row.
32 have NO readers (their input is already cancelled by an anticipatory read, e.g. A1323 `456 -= 474` / B849 `456 += 474`):
the 24 entering (2,9) helpers 474-477, 486-489, 522-529, 534-541 and 8 entering (1,9) helpers 472/473/496/497/520/521/544/545.
They are delay lines: 1-2 writes copy an old value of a source that changes before the last read, so the direct uncompute
(scripts/uncomp.py) is impossible for all 32.

## Construction (exact): backward replay
val(s, t) = val(s, T) - sum over intervening writes s += c*x of c*val(x, t') (recursive; scripts/replay.py) expresses the
old value through CURRENT registers: 2 gates per (2,9) helper, 3 per (1,9) helper at the earliest slot (e.g. 474 -= 279,
474 += 311). Pinned auditor PASS (both orientations, derived cleanup, 73 restored, certified frames, local profile unchanged)
for 522/475/472 restored at a FULL end frame (out/AT-base.json): exact, locally free, +1 private buffer, width unchanged.

## Why the width cannot be cut (scripts/sweep2.py: exact necessary minimal-closure test, every slot, every gate order)
- Early slots: q's frame (dim 6/7) plus the recipients' frames span only 7-8, but the recipients' later gates carry q's
  frame vectors into targets whose end frames are port hyperplanes (174/175/202/203/182/119/131/139) or into cold helpers'
  low end frames (311, 448, 484, 498): infeasible. The certified solver agrees at the earliest slot even with U = FULL
  (out/T2-base.json, T3-base.json: "L not inside U").
- Every slot that passes forces q's restored end frame to FULL (dim 9): no width change.
- Helpers WITH readers (30 testable, pre-end <= 7; out/SWEEP-READERS-base.json): no slot with restored dim < 9; 36 more are
  lenders or scaled (not attempted).

Totals (sweep2, base word): 32 candidates, 33276 slots, 15017 feasible, 0 with a restored end frame below FULL.
Result: no width cut is reachable by restoring ordinary helpers on these words; nothing to stack (out/FOR-STACK.json).
