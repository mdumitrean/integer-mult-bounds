# r10 G-unlock: exact rewrites to unlock pre-life hosting (530/542) or a 13th source alias. NULL.

Base: our candidate words (retired5, b295183e), read-only. Harness scripts/bp10.py (r8 borrow_price on the retired5 package,
pinned vendor/audit_local_pr2679.py). Calibration on both words: optimal = literal = {1:2386,2:642,3:274,4:128,5:26,8:8},
certified, auditor PASS. Unlock values (F-lenders out/RELAX-r10.json): one more hosting (net width-4 removal) +6.70e-7;
a 13th source alias (width-8 removal) +1.06e-6 (entry) .. +2.44e-6 (unit).

## (a) Hosting 530/542: the cap is the source's later target read
- 530's first gate B659 (530 += r75) is pinned at dim 3 = F(B781: 144 += 530, pinned dim 4) ∩ F(B1213: 136 += r75, upper dim 7).
  542 is the same shape: B685 (542 += r84), with B786 and B1221 (221 += r84).
- Control: deleting only that read (semantics broken, audit FAIL) raises the first-frame upper to dim 4 (Δ −13,851). So that
  read is the whole obstruction.
- The read relocated, each exact on base and extra: before the copy; at B start; before 136's B50 or B311; split with the
  r349 compensation (r75 += r349 at B642) at 0/643/700/920; the r84/r365 analogues. 7 + 7 variants: **all infeasible**.
  r75's or 136's frames then flow (via 586 → 187, or 530's chain) into ends that exclude them. After the copy E flows into
  136, and 136/219's butterfly caps it at perp(p136) ∩ perp(p219) (dim 7). Splitting the read across the butterfly needs a
  dim-8 frame inside that dim-7 space.
- Host side: 18 eligible hosts on our words, all width 4. Each retires with a WRITE (h *= −1 or h += c·r) pinned at
  [4,4], so there is no read to move and no dim-3 warp.

## (b) 13th source: the six unused pairs
- Each of the 12 ports' last read is pinned at [6,7]. All 46 semantics-preserving earlier slots along the reading target's
  chain are **infeasible** on both words.

Evidence: out/{TRY0,TRY1,TRY542}-base.json, TRY01-extra.json, PORTMOVE-{base,extra}.json, HOSTMOVE-{base,extra}.json.
