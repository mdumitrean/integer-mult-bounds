# r10 H-widths: helper-width levers on the retired5 words (no gain)

Base: our candidate (r10/vendor/retired5, kappa 0.0017174093163354916434). PR list refreshed 21:27Z and 21:56Z: top claims
still #2766/#2767 (0.001717256973467002).

## Width rule (pinned auditor audit_local_pr2679.py, run_borrow section 4)
width(q) = dim end(q) - dim start(q): start = start_extra frame (entering) or 0; end = helper_final U (cold/restored, needs a
private zero buffer and a self-restoring forward program) or FULL (9). Local mass per call = 1856 + sum of widths. The owner
fill places each call's role of `width` cells as a compact prefix in an idle bin (cap 8/16/32/48, per owner child and port)
whose window contains the call; each bin's leftover cap - used is a profile term (independent_owners.py).
Classes: 240 (0,9), 70 (1,9), 24 (2,9), 4 (4,9) entering, 26 (0,4), 8 (0,7), 8 (0,8) cold, 30 (1,8) entering cold.

## Value table (fill relaxation = relax_r9 model for any widths; reproduces the realized root; upper bound)
Per helper, local -1 rank-1 per width unit unless noted: 9->8 +5.90e-7, 9->7 (-r2) +1.07e-6, 9->6 (-r3) +1.50e-6,
8->7 +5.90e-7, 7->6 +5.90e-7, 7->4 (-r3) +9.07e-7, 5->4 0 exactly, 5->3 +3.95e-7, 4->3 +3.95e-7; x16 up to +1.9e-5.
Widths are worth a lot in the fill; the question is the exact local cost of getting them. (out/VALUE-TABLE.json)

## Exact edits tried (certified frames: C-kernels bwprice / #1186 toolkit; both words identical)
1. Entrance raises, forced closure over all 170 wrapper-free, non-source helpers (incl. 42 cold non-entering ones): only
   667/669/670/671 (width 5) raise, by exactly one dimension (feasible span = dim 5). Certified: -6.36e-7 (one or all four).
2. Narrowing cold end frames: 18 (1,8) cold helpers have forced closure 7 < 8. Certified re-solve feasible; -7.4e-8 (586, 588;
   auditor PASS on 586) to -3.8e-7 each; pairs/groups worse (all 18: -5.4e-6). Partners 136/140/144/187/438 must split climbs.
3. Hoisting each cold helper's final uncompute (restore) gate to its earliest exactly commuting B slot (51 movable): no extra
   narrowing; same deltas.
4. Making non-cold helpers cold: their forward-end rows carry 7-9+ foreign terms and most are read elsewhere (not attempted).
