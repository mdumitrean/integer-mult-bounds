# r7 / T-generator: the generator-level route to the width-9 narrowing lever

Agent T-generator, round r7 (2026-10-15, from 09:19Z). Words `r3/inputs/{gauge44,extra}-word-566-554.json.gz`; toolkit
`r3/toolkit-rev3` (read-only); b = 0.001679754956125544. Upstream code was read before running and run only from this
directory with explicit paths. Local only: nothing committed, pushed or posted.

**Outcome: no valid narrowed word; kappa unchanged.** The generator was found and reproduces exactly, but planning one more
entering helper needs a new factory/leaver-cell design, and the generator's own freedom (dirt routing between equal-clean
copies), tested directly on the current words for all 104 full-c1 helpers, admits no legal construction.

## 1. Where entering helpers come from (generator found, calibrated)
- `research/gauge44-slots/construction/reproduce.py` (main 0fdd7d82; pinned upstream main 17ce0c79 and PR635 a6895a69,
  fetched read-only) rebuilds #645's gauge44 base word: shadow-early, shadow-prefix, the R492 factory
  (`construct_gauge_xcentre.py`), port0..port3, regroup, HPE, cold44. **All 10 intermediate content pins match** and the
  cold44 recipe re-derives equal to the frozen one (`out/repro-word/`, `out/TRACE-ENTERING.json`).
- **Entrances are created by PR635's port stages**, which replay the entrance (start_extra) changes of the 504-helper
  shadow chain onto the factory: raw factory 0 entering; port0 +200; port1 +1; port2 +7; port3 -4 (204). The shadow chain's
  entrances come from the promoted word (structural-gain frontier-composition; PR664's promotion mechanism, 213 entering).
  A promotion is legal only for a helper whose dirt already has zero target response, a property of the factory's dirt
  routing; promotions (PROMO-RECIPE) only enlarge existing entrances.
- The k8 ancestor (R480, 192 entering, 78 low ends) is built by `leaver/reproduce_leaver.py --id k8` +
  `reproduce_leaver_chain.py --id k8` (LeaverSAT cells, re-indexed recipes, LeaverSAT2 frame re-optimisation), then the
  slots, PR1148's k8 chain (eight-ends, three-demotions, joint-entrances: build_word.py + RECIPE.json), #1193 FOUR,
  #1297 RECIPE, #1625 and #1672 EDITS. **Calibrated end to end:** `reproduce_leaver.py --id k8` gives the cell word `58e14a02…`; `reproduce_leaver_chain.py --id k8 --skip-phases` gives the k8 ancestor `db2c7cfb3f8e…` (R480, 192 entering, 78 ended; every chain pin matches except the Clifford-recipe pin that `--skip-phases` omits; native transport, ledgers, local replay and wrappers pass); the slots recipe (`barch/build_tri.py`, RECIPE-SLOTS-k8) gives `c2b294300760…`; PR1148's k8-eight-ends gives `f43271fcabcc…`; k8-joint-entrances gives `1f66640293bd…`, **byte-identical in content to the JOINT-WORD vendored in #1193/#1297/#1672**. r6 K-recipe already reproduced JOINT-WORD -> FOUR-WORD -> #1297 -> #1625 = #1672 step 0 -> the current words. So the whole chain from the pinned upstream inputs to the current words is reproducible.

## 2. Why the chain cannot carry a new entering helper within this task
Every downstream stage is a deterministic builder applying a frozen recipe pinned to its exact input content (LOCAL-PINS,
CHAIN-PINS, SOURCE/PARENT-PINS), and several recipes are frozen search outputs (BlockInvert's CP-SAT promotion recipe,
LeaverSAT2's frame re-optimisation, PR987's slot search, PR1148's joint-entrance frame searches, #1625/#1672 kernel
searches). A changed ancestor invalidates every pin downstream; re-deriving needs those searches re-run. What is missing
is not a generator but a factory/leaver-cell design in which one more width-9 helper's dirt cancels before the targets.

## 3. Testing the generator's freedom directly on the current words
The factory's own lever for dirt routing is gauge44's change A: exchange a source with an equal-clean helper copy at equal
frames (no frame climb, clean values unchanged, only dirt moves). Its continuous form is a dirt transvection
a <- a + mu*(b - a) for equal-clean a, b with frame(b) inside frame(a) (2 gates, any dyadic mu != 1, no climb).
- `scripts/xscreen.py` (exchanges, base frames): 42,661 exchanges move narrowable dirt without entering/ended dirt; 18,905
  leave every ended row unchanged; **none zeroes a leak**. The first-order span contains every leak (rank 48-52), but only
  through swaps involving q itself (relabelings), which cannot create a new zero-response helper.
- `scripts/tscreen.py` (transvections, NARROWED word's certified frames, all 104 full-c1 helpers, `out/TS/`): 20 helpers
  have no admissible transvection at all (e.g. 478/479/490/491: at 192 of 220 sampled times no register but q carries q's
  dirt); max rank 8. **20 helpers are in span, all only via a single transvection with mu = 1** (a := b, a non-invertible
  overwrite, not a legal gate); every parallel operation is on the same register (e.g. source 60 for q = 233), so no
  legal split exists. Reason: the targets read q's dirt through a difference of the packet factory's equal-clean copies
  (at A1265-A1286, T_60 = -T_233 = -L_233); zeroing needs both copies to carry the same dirt, which a reversible program
  can only do by parking the information in a third register whose route cancels the remainder.
- `scripts/pivot3.py` / `pivot4.py` (3- and 4-gate pivot constructions that park q's dirt in a pivot r, with r's clean
  twin when r carries data): for q = 233, 2,969 (time, carrier, twin) cases, **no pivot whose route cancels the remainder**
  (pivots with the carrier's frame all carry data; clean-0 ones never share it).
- `scripts/pairscreen.py` (clean-cancelling pair deliveries into targets in B, every 3rd B position): no equal-clean pair carries 478's dirt in B.
- Relaxed upper bound (`scripts/tscreen_relaxed.py`, ended-helper rows/columns allowed to change, as a generator-level
  change with a re-derived cold construction would allow; `out/TSR/`): 104 helpers; 22 in span (adds 253 and 269), every one again only via a single transvection with mu = 1; no legal solution; max rank 8.

No candidate word arose, so audit_local, the native chain and the 3,728 units/call budget were not reached.

## Best next step
A new packet-factory (or leaver-cell) design in `construct_gauge_xcentre.py` / LeaverSAT cells in which one width-9 helper's
dirt is read by targets through a combination that a target-neutral register can absorb, followed by re-running the frozen
downstream searches. That is a construction project, not a recipe edit.

## Evidence
`out/repro-word/` (+ STEPS.json), `out/TRACE-ENTERING.json`, `out/XSCREEN-base.json`, `out/TS/` (104 + SUMMARY),
`out/TSR/`, `out/TL/233.json`, `out/PIVOT-233.json`, `out/PIVOT4-233.json`, `out/PAIRS-478.json`; scripts in `scripts/`.
Upstream sources in `src/` (git archive of main 17ce0c79 subtrees, PR635 a6895a69 cold14-st2, main 0fdd7d82
gauge44-slots). Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
