# r6 / G-ainsert: helper-donor kernels with A-section inserts on the 566+554 base word

Agent G-ainsert (round r6, 2026-10-15, about 04:29-05:15Z). Word `r3/inputs/gauge44-word-566-554.json.gz` (#1672 blob
76c01583), b = 0.001679754956125544. Local only: no commits, pushes or posts.

**Outcome: scoped negative result, no κ change.** Allowing compensating inserts in the A section makes the A34xx
accumulation reads shape-feasible, but their only exact compensations are relocations of the deleted read (Δ = 0). The
A12xx pre-cancels stay INFEASIBLE with inserts anywhere in A. The four −6,118 B reads are shape-infeasible only because
#1957's cost oracle prices the needed inserts at infinity; with that estimate clipped, their exact proposals are again
relocations of the deleted read (Δ = 0). 14 exact target proposals priced, all Δ = 0; no gain.

## 1. Model (`tools/sk4.py`, driver `tools/run4.py`)
`PRound4` extends r5 D-compsplit's projected, compensation-aware split-key model (`sk3.py`; from r3 B's `sk2.py`,
PR2142 / Ian Libânio's `skkernel.py` and PR1957 / Rohan Arun's `abkernel.py`):
- inserts may also sit in the A section, at positions inside configurable windows (`a_windows`, base A indices);
- an A insert may not touch a port/target register (112..223): ports have no A vertices and empty cut frames, and the
  auditor requires the targets at their empty centre levels when B starts; no insert inside the cut;
- r3 B's exact single-insert cone test (`cone.LU.ok`) handles A positions, including the cut-equality term;
- exactness is sk3's projected check (non-port rows exact; port rows up to the ordinary-helper columns that the re-derived
  compensation absorbs); proposals are priced by r5 D's compensation-aware pricer (`absorb.py`, re-derived compensation,
  recomputed caps, exact optimal frames, true-moment interval, unchanged `audit_local.py --main` when audited);
- `to_base_edit_ab4` maps W-coordinates back to section-tagged base edits with A inserts; `inf_clip` (diagnostic) turns
  the oracle's infinite frame-relative estimate into a finite one, leaving the decision to exact pricing.

## 2. Calibration
- **k554 with an A window** (`out/CALIB-k554*.json`): on #1672's pivot-566-only word (`step0-gauge44`), deleting B342 with
  A window A3000-A3451 enabled (35 A candidates admitted): all five k554 inserts are candidates, the fixed-λ check is
  OPTIMAL, and the free search returns k554 in three placements. Priced: all three Δ = −1,856, `ok`, compensation 7,208,
  unchanged auditor PASS.
- **A-insert identity** (`out/CALIB-AID.json`, `tools/calib_aid.py`): an A gate's (t, s) inserted as +1 then −1 before it,
  at A1149, A2297 and A3450: each `ok`, Δ = 0, compensation unchanged (7,208), unchanged `audit_local.py --main` PASS.
  Control: the +1 insert alone is rejected as inexact at all three.

## 3. Targets (base word)
| Targets | A windows | Outcome |
|---|---|---|
| A3403 `60 += 28`, A3418 `63 += 45`, A3434 `240 += 111` (−8,879) | A3100-A3451 | now shape-feasible (1,327-1,477 A candidates); 2 exact proposals each = re-insertion of the deleted read at another position; priced Δ = 0; then INFEASIBLE |
| A3450 `256 += 432` (−8,879) | A3100-A3451 | shape-feasible (3,438 A candidates), INFEASIBLE |
| A1231/A1215/A1222/A1246 pre-cancels (−6,781) | A1100-A2000, and the whole A section | INFEASIBLE (up to 4,851 A candidates); also INFEASIBLE with the oracle clip |
| B822/B840/B858/B876 (−6,118) | A3100-A3451; B822/B858 also the whole A section, and with no budget and a 3x cap | shape-infeasible (up to 31,014 A candidates) |
| B822/B858 with the oracle clip (3,000) | A3100-A3451 | shape-feasible; 4 exact proposals each (K limit): relocations of the deleted read, alone or after a read of 3 (B822) or 75 (B858); all priced Δ = 0 |

**Why the −6,118 reads were shape-infeasible** (`out/SHAPE-DIAG-B822.json`, `out/WHY-B822.json`): the unmatched target
equations are the deleted value's direction on final rows 507, 519, 699 and 700. The only carrier is 531's column near
B822; re-inserting `531 += 351` there passes the cone test and has the right coordinates, but #1957's oracle returns
2^60, because it prices against the deleted word's re-solved frames, in which 531 no longer holds 351's frame. Clipping
that estimate makes the model shape-feasible; exact pricing then shows only Δ = 0 relocations.

Totals: 25 target jobs (12 deletions; late-A, whole-A, clip and no-budget variants) plus the calibrations; 14 exact target
proposals priced (`out/PRICED-*.json`: 6 A34xx relocations, 8 B822/B858 clip proposals), all Δ = 0 with the compensation
unchanged; no negative delta (`out/EVIDENCE.json` "gains": []).

## Scope and limitations
- First-order model with exact checking, one round, at most 12 inserts, quarter-step |λ| ≤ 4, #1957's per-insert oracle
  for caps and budget, K ≤ 3-4 proposals per job; INFEASIBLE verdicts are proofs within this finite model and cuts only.
- A34xx windows were A3100-A3451 (time); A12xx and B822/B858 also ran with the whole A section.
- The clip runs stop at the K limit, so they show what the cheapest exact proposals are, not that nothing else exists.
- The oracle's infinite estimates also hide candidates elsewhere; a frame-re-solving cost estimate (or exact pricing of
  the cheapest few per equation) would be the sound replacement.
- Extra word not run (r3 A: same gate sequence; models differ only on registers 624-631).

## Evidence
`out/EVIDENCE.json` (all runs, calibrations, priced proposals, diagnostics), `out/TABLE.md`, `out/RUN-*.json`,
`out/run-*.cap.log`, `out/PRICED-*.json`, `out/SHAPE-DIAG-B822.json`, `out/WHY-B822.json`, audit receipts in `out/audit*`.
Tools: `tools/sk4.py`, `tools/run4.py`, `tools/calib_aid.py`, `tools/shape_diag.py`, `tools/why822.py`,
`tools/summarize4.py`, `tools/chain4.sh`, `tools/after.sh`; r5 D's `absorb.py`, `sk3.py`, `price3.py`, `capped.py` and
r3 B's `sk2.py`, `cone.py` (copies). At most 2 worker processes, each under a timeout and 6 GiB RSS cap; peak 1.3 GiB.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
