# r6 / J-carrier: carrier-aware delivery relaxation for the 13 never-written copy-window pivots

Round r6, 2026-10-15 ~05:07–06:00Z. Base word `r3/inputs/gauge44-word-566-554.json.gz` (extra word checked for 439).
Toolkit #1186 rev3 (`r3/toolkit-rev3`; private copy `scripts/frames_j.py` adds constant lower/upper hooks), b = 0.001679754956125544,
base cone caps (an exact re-delivery restores the base map, hence its compensation and caps), cut equality, tail-mutable.
Local only: no commits, pushes or posts. At most 4 worker processes, per-pricing deadline 180 s, RSS check before each task.

**Outcome: no gain; all 13 pivots show no re-delivery skeleton below the base cost.** The carrier-free part of their
deletion screens is not reachable by star re-deliveries: every feasible way to bring q's value back to all of its
B+tail column (8 targets plus the low helper 584 or 449) costs back the whole screen.

## The family and the relaxations
Family ("star" re-delivery): delete q's B reads (the screen), then add any reads `r += c*q` in B or the early tail
(direct target reads, carrier windows, restores); every other gate unchanged. This covers our #1625 kernel shape and
r3 D's re-delivery family; it excludes relays through other carriers loaded from data registers (r5 D's windows) and
edits that delete or re-time other gates.

Necessary condition used everywhere: each register y of dp (q's B+tail column change on non-full-end coordinates, as in
r3/r4: the 8 targets and the low helper) must receive q-content by dataflow from some new q-read through the existing
gates. A *meet* is one new q-read placed in a segment of its partner's chain (between two gates involving the partner);
within a segment the dataflow reach is constant.

1. **q-free relaxation** (rigorous lower bound for the family; order-free): the meet is a node on the partner's chain only,
   with a constant lower frame = q's L-propagated lower before it. Result for 439: every feasible meet is free on the
   partner chains (76 of 442 candidates feasible, all at the deleted cost −67,933) and covers exist. **It does not close
   anything:** the re-delivery cost is not on the partners' chains.
2. **r-free (q-chain) relaxation**: the meet is a node on q's chain only, bounded below by the partner's prior lower frame
   and above by its next upper frame (with cap). For 439 single meets cost back 10,821 (584 at B41, exactly r3's cap),
   14,775 or 19,700; the best full cover (584@B41, 126@B485, 10@B748, 455@B867, 584@tail 0) is still −33,468 (`out/BNB-base-439.json`).
   So the cost lives on q's own chain, but splitting the chains apart still leaves a gap.
3. **Real shared-node skeletons** (the actual frame model, q and partner share the meet node): price the deleted word
   plus the actual reads `r += q` at the meet positions, and branch and bound over all covers of dp by feasible meets,
   pruning any partial skeleton whose cost is already >= base (adding reads never lowers the optimum; coefficients and
   restores of an exact re-delivery only add gates). Positions: segment starts (tail 0 when a segment runs past the end of B).

## Results (real skeleton search, base word, `out/RBNB-base-<q>.json`)

| Pivot | Deleted (screen) | Candidates / feasible meets | Nodes (joint pricings) | Single-meet cost-back classes | Status |
|---|---:|---:|---:|---|---|
| 439 | −67,933 | 442 / 44 | 597 | 0 (low helper only), 14,775, 19,700 | no skeleton below base |
| 444 | −67,933 | 432 / 44 | 597 | 0, 14,775, 19,700 | no skeleton below base |
| 438 | −62,305 | 438 / 46 | 422 | 0, 14,775, 19,700, 36,563 | no skeleton below base |
| 226, 228, 230, 231, 238 | −51,636 | 445–459 / 47 | 602 each | 0, 19,700, 26,789 | no skeleton below base |
| 232, 236 | −51,636 | 419–452 / 47 | 548 each | 0, 19,700, 26,789 | no skeleton below base |
| 434, 436, 446 | −51,636 | 441–452 / 47 | 780 each | 0, 19,700, 26,789 | no skeleton below base |

Every search finished under its node limit (exhaustive under the monotone pruning). Feasible single meets with a
target cost back 14,775–36,563; the only free meets are low-helper meets (for 439: 584 in the tail, which covers only 584); the cheapest
covering combination always reaches the base cost (the base routing itself: for 439 its 4 reads, 584@B893, 126@B911,
10@B940, 186@B1222, reprice at exactly Δ = 0).

Checks (`out/EXTRA-CHECKS.json`):
- **Calibration:** the base routing reprices at exactly the base cost; the named r-free cover reprices at Δ = 0 in the real
  model; the r-free single 584@B41 equals r3's capped screen (−57,112); every value is >= r3's capped screens.
  No never-written helper with a zero deletion screen exists among those scanned (`out/CALIB0-scan.json`), so the "zero
  screen" calibration was replaced by the base-routing one.
- **Position sensitivity (439):** adding each segment's latest position as a second candidate (786 candidates, 76 feasible,
  same cost classes) found no skeleton below base in 4,012 joint pricings (node limit hit: not exhaustive).
- **Extra word (439):** identical (44 feasible meets, 597 nodes, no skeleton below base).
- **Bonus, group D pivot 235** (screen −44,073, no copy window, not reduced by r3's cap): no skeleton below base either
  (637 candidates, 115 feasible meets costing back 10,184–19,766, 1,438 nodes, exhaustive; `out/RBNB-base-235.json`).

## Answer to the task
- No pivot has a positive gap in the real model at segment-start positions, so no slot to build is named: under the frame
  model, any star re-delivery of these pivots costs back their whole screen. The two rigorous order-free relaxations (q-free,
  r-free) are too weak to prove this alone; the closure rests on the exhaustive real skeleton search with one position per
  partner segment, plus the sensitivity check for 439.
- Not covered: positions inside segments other than start/end on pivots other than 439; multi-hop relays through registers
  loaded from data (r5 D's family); edits that delete or re-time other gates; A-section edits (r4 A: they cannot reach ports).

## Files
- `scripts/`: `jcommon.py` (Pivot, candidates, q-free / r-free / real pricing), `frames_j.py` (toolkit frames.py + hooks),
  `singles.py`, `rsingles.py`, `bnb.py` (relaxations, 439), `rbnb.py` (real skeleton search), `rbnb2.py` (position
  sensitivity), `calib0.py`, `summarize.py`, `probe.py`.
- `out/`: `SINGLES-base-439.json`, `RSINGLES-base-439.json`, `BNB-base-439.json`, `RBNB-base-<q>.json` (13 pivots),
  `RBNB2-base-439.json`, `RBNB-extra-439.json`, `CALIB0-scan.json`, `EXTRA-CHECKS.json`, `EVIDENCE.json`, logs.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
