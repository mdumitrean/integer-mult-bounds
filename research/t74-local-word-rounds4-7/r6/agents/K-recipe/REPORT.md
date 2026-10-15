# r6 / K-recipe: can the word recipe plan one more entering pair?

Agent K-recipe, round r6 (2026-10-15, from 05:57Z). Words `r3/inputs/{gauge44,extra}-word-566-554.json.gz`, toolkit rev3
(`r3/toolkit-rev3`, read-only), b = 0.001679754956125544. Vendor code was read, not run: every step is re-implemented in
`scripts/`. Local only: nothing committed, pushed or posted.

**Outcome: no recipe-level change yields a valid narrowed word; κ unchanged.**

## 1. How entering pairs arise
- **The lineage never plans them.** `scripts/lineage.py` diffs PR1148's JOINT-WORD, PR1193's FOUR-WORD, PR1286's inputs,
  PR1297's words, our PR1625 words and the current PR1672 words (`out/LINEAGE.json`). Across all of them, the 192
  entering helpers (`start_extra` keys), the 78 cold ends, the A-section scalar operations, the cut and the precondition
  are identical. The recipes only change `start_extra` values (PR1193's demotion of 627/629/630/631), frames, and B.
- **PR1193's FOUR-RECIPE** changes 4 entrance labels and 12 B frames; scalar operations are asserted unchanged.
  **PR1297's RECIPE-{base,extra}** replaces B, cleanup, early_cleanup and report. The kernel EDITS (PR1625, PR1672) change
  B and the tail only. The entering structure is inherited from the k8/R480 construction before PR1148 (PR1018, PR987,
  PR869, PR664's promotion mechanism); no generator for it is vendored.
- **The pair mechanism is a pure copy with a mirrored leak** (`scripts/pairs.py`, `out/PAIRS-base.json`). Entering 526
  [96] has one pure read, `A1219: 478 += -1*526`, and is first written at B817; likewise 527→479, 538→490, 539→491,
  550→502, 551→503, 563→515. The partners are exactly the 4-leak helpers r6 A/B tried to narrow. In total: 33 entering
  helpers with one A partner, 9 with three or more, 21 with one B partner, 120 with two or more B partners, 8 with none.
  The copy works because the partner's downstream influence on the targets equals minus the entering helper's leak.

## 2. Calibration (passes)
`scripts/calibrate.py` (`out/CALIBRATION.json`):
- JOINT-WORD + FOUR-RECIPE reproduces FOUR-WORD byte-for-byte in content.
- PR1286 inputs + PR1297 RECIPE-{base,extra} reproduce PR1297's two words byte-for-byte in content.
- PR1297 + EDITS.json (pivot 566) gives the same scalar program and interfaces as PR1672's step 0. Our PR1625 words equal
  that step 0 byte-for-byte in content.
- Step 0 + EDITS-1.json (pivot 554) gives the current words' scalar program and every interface; only the 4 new gates'
  frame labels differ, and those are solver output. `scripts/frames_calib.py` re-solves the rebuilt words: both equal the
  shipped words, certified (base 11,683,290,250; extra 11,691,748,602).

## 3. Planning one more pair: the screen and the recipe attempt
- **Single-partner mirror screen** (`scripts/mirror.py`, exact backward column pass over A+cut+B). For every
  compensation-read width-9 helper q it searches every register r and time t before q's first write for a column
  col_r(t) proportional to q's leak L_q, which is what one pre-cancel copy needs.
  - Positive control: with 526's copy A1219 removed, it recovers exactly r = 478, c = -1, valid at any t before B817.
  - Result: **0 of 240 helpers on the base word and 0 of 240 on the extra word have any mirror partner**, even
    algebraically and ignoring frames (`out/MIRROR-{base,extra,control526}.json`).
- Multi-partner copies exist algebraically but are frame-infeasible: r6 A's screen (153 pairs) and r6 H's sound screen
  (all holders, with and without cone caps) admit at most rank 4 against leaks of 16 to 72 rows.
- **Recipe-style narrowing** (`scripts/narrow_recipe.py`): the FOUR-RECIPE mechanism (label change, scalar program kept,
  frames re-solved) applied to 478 with basis [96].
  - The toolkit certifies frames at 11,681,173,796 (base − 2,116,454, H1 −1), widths {8:115, 9:239}.
  - The unchanged `audit_local.py --main` **fails: "nonzero entrance response"**. The re-derived compensation still reads
    478 in 4 gates (`out/AUDIT-NARROW478-recipe.log`, `words/NARROW478-recipe-gauge44.json.gz`).
- No valid word arose, so the native chain was not run and there is no net value against the 3,728 units/call budget.

## Why it is closed, and what would be needed
An entering pair needs a partner whose later use of the values mirrors the helper's leak. On this scalar program no
register does that for any width-9 helper, and every multi-partner copy breaks frames. Creating a mirror means changing
how B uses q, which is a new k8 word construction. That generator is not in the vendored lineage; the frozen recipes
cannot express it.

## Evidence
`EVIDENCE.json`; `out/` (LINEAGE, PAIRS-base, CALIBRATION, FRAMES-CALIB-{gauge44,extra}, MIRROR-*, NARROW478-recipe,
AUDIT-NARROW478-recipe.{json,log}); `words/` (REBUILT-{gauge44,extra}, NARROW478-recipe-gauge44); `scripts/` (lineage.py,
pairs.py, calibrate.py, frames_calib.py, mirror.py, narrow_recipe.py). Prepared with substantial AI assistance (Anthropic
Claude, via Claude Code).
