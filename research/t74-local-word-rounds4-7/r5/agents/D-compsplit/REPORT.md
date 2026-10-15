# r5 / D-compsplit: compensation-aware split-key kernels on the 566+554 words

Agent D-compsplit (round r5, 2026-10-15, start 03:05Z). Words `r3/inputs/{gauge44,extra}-word-566-554.json.gz`
(#1672 blobs 76c01583 / e86142b3), b = 0.001679754956125544. Local only: no commits, pushes or posts.

**Outcome: scoped negative result, no κ change.** Both new tools are calibrated: the compensation-aware pricer reproduces r4 C's demo, and the projected split-key model rediscovers k554 (Δ = -1,856, auditor PASS). But none of the 84 targets admits an exact kernel: 76 are proven INFEASIBLE in the model and 8 are shape-infeasible, so nothing reached pricing. A no-budget diagnostic on B933 is INFEASIBLE too.

## 1. Compensation-aware pricing option (`tools/absorb.py`)

`AbsorbPricer` (a subclass of the rev3 toolkit's `harness.Pricer`, own copy in `toolkit/`) changes exactly two rules:
- **Exactness, projected.** The A+cut+B+early-tail map (A-start coordinates) must be unchanged on every non-port row,
  and on every port row except the columns of the 240 ordinary helpers (not `start_extra`, not `helper_final`). Those
  entries are what the derived compensation cancels. On these words the precondition writes only ports and no tail or
  later cleanup gate touches a port, so this is the whole call map up to the re-derived compensation.
- **Compensation.** Re-derived by `model.cone_caps` for the candidate (caps recomputed); only the auditor's residual rule is
  enforced (no compensation gate reads an entering or low-end helper), not equality with the base compensation.
Everything else is the rev3 path: static program rules, exact optimal frames, true-moment interval, and the unchanged
`audit_local.py --main` on every negative delta. `price_ab` adds section-tagged edits (A deletions).

**Calibration 1** (`out/calib/CALIB-ABSORB.json`): r4 C's demo `112 += 482` before B0 prices `ok`, Δ = 0, certified,
compensation 7,208 -> 7,209 gates, caps unchanged, and the unchanged auditor PASSes it with 7,209 compensation gates.
The unedited word gives Δ = 0; deleting a data-carrying port read (B469, `112 += -1/2 · 1`) is rejected as inexact.

## 2. Projected split-key model (`tools/sk3.py`, driver `tools/run3.py`)

Extends r3 agent B's `sk2.Round` (from #2142's `skkernel.py`, after #1957's `abkernel.py`):
- target T = base map - map(W) on the final rows; non-port rows must match in full, port rows only after projecting out
  the ordinary-helper columns; two key bases (full keys for non-port rows, projected keys for port rows);
- inserts `x += λ y` into ANY register at any B or early-tail position (tail inserts may not touch ports; ports only feed
  ports), λ in quarter steps with |λ| <= 4, at most 12 inserts, #1957's per-insert cost oracle with the budget
  -Δdeletion - 1 and per-insert cap = budget, r3 B's exact single-insert cone test (`tools/cone.py`) before admission;
- per effect, the cheapest entries at both ends of its position window are kept;
- every CP-SAT solution is checked exactly (projected); an inexact one (a real second-order interaction) cuts its
  interacting pairs; a frame-infeasible one is cut by a minimal conflicting subset; exact ones are priced by `price3.py`
  with the compensation-aware pricer.

**Calibration 2** (`out/CALIB-k554*.json`): on #1672's pivot-566-only word (`step0-gauge44`), deleting B342 (`482 -= 554`,
-6,781): the model admits k554-signed-001 exactly (fixed-λ check OPTIMAL), and the free search returns k554 itself in three
equivalent placements (5 inserts, oracle estimate 4,925). Priced: all three Δ = -1,856, gain_certified, compensation
unchanged (7,208), unchanged auditor PASS, profile {1:2348, 2:500, 3:416, 4:130, 5:82} (the current 566+554 word).

## 3. Targets on the base word

| Targets (base word) | Jobs | Deletion price | Outcome |
|---|---:|---:|---|
| B933, B938, B941, B943, B946, B948: port reads of helpers 507/519/482/483/494/495 | 6 | -16,863 each | all INFEASIBLE, after 6-10 interaction cuts and 3-6 frame cuts each |
| B933 diagnostic: no summed budget, per-insert cap 3x budget, <= 16 inserts, re-insertion of `115 += 507` banned | 1 | -16,863 | INFEASIBLE |
| r4 C's other 42 re-sourcing reads (B540-B705, port reads of data registers) | 42 | -10,503 to -13,804 | all INFEASIBLE; most have no first-order solution at all |
| #2142's 28 B deletions | 28 | -3,059 to -8,879 | 24 INFEASIBLE (B1/B3/B39/B44/B50/B52 rerun with 40 cuts); 4 shape-infeasible (B822/B840/B858/B876, -6,118) |
| #2142's A deletions, 8 representatives (A1215/1222/1231/1246; A3403/3418/3434/3450) | 8 | -6,781 / -8,879 | A12xx: INFEASIBLE; A34xx: shape-infeasible |

Totals (`out/EVIDENCE.json`): 91 job runs, 0 exact proposals, 224 interaction cuts, 64 frame cuts, nothing priced.

**Why the six -16,863 reads fail.** Every first-order solution re-delivers the deleted port read through a window on a
copy-window helper loaded with a data value, read into the port in between. Examples: `436 += 2·319 ... 436 -= 2·319` with
`115 += ½·436` for B933, and similarly 434, 439, 444 and 446 for the others. For B938 the window is on data register 54
with helper 335. Each such window either interacts with the helper's existing port deliveries, so the word is inexact,
or pushes a lower frame outside its upper frame at B1645-B1759. The minimal conflicts are always two inserts. These are
the helpers whose frames r3 D found pinned by their butterflies, so the absorbed compensation does not reach them.

**Shape-infeasible targets.** This model places no A-section inserts. For A3403-type deletions and the four -6,118 reads,
some target equation has no candidate at a B or tail position.

The extra word was not run; it shares the gate sequence (r3 A), so the models differ only on registers 624-631.

## Scope and limitations

- Inserts in B and the early tail only (no A-section inserts); first-order model with exact checking, one round; at most
  12 inserts, |λ| <= 4 in quarter steps; #1957's oracle sets caps and budget; at most K proposals and 10-25 cuts per job.
- CP-SAT INFEASIBLE verdicts are proofs within this finite model (and the cuts applied), not supplier lower bounds.
- Extra word: not run. r3 A showed the two words share one gate sequence (frames differ only on 624-631), so the models
  differ only through oracle costs and cone tests on those registers.

## Next step

Allow A-section inserts: `absorb.compile_ab` already accepts them, and `cone.LU.ok` handles A positions with the
cut-equality term. Then rerun the 8 shape-infeasible targets. Otherwise, the compensation-aware relaxation is closed for
B/tail kernels on these words. The calibrated pricer option is ready to fold into a later #1186 revision.

## Evidence

`out/EVIDENCE.json` (all jobs, cuts, prices, calibrations), `out/TABLE.md`, `out/RUN-*.json`, `out/run-*.cap.log`,
`out/calib/`; tools in `tools/` (absorb.py, sk3.py, run3.py, price3.py, queue.sh, summarize.py; sk2.py/cone.py/capped.py are
r3 B's, unchanged). Interpreter: agi venv for CP-SAT (`run3.py`), python3 for rev3 pricing (`price3.py`).
