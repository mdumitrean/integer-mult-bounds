# D-depth2 (round r6): depth-2 recursive-key helper-donor kernels on the 566+554 base word

**Task.** Finish r3 B-interact's recursive-key (depth-2) kernel search, which r3 could not complete (its pure-Python
candidate generation for B822/B858 was killed after 11 minutes at about 1 GB). Base word
`r3/inputs/gauge44-word-566-554.json.gz` (249 calls), b = 0.001679754956125544. Local only: nothing committed, pushed or posted.


**Outcome: no depth-2 kernel found, kappa unchanged.** Six of the ten targets are proven infeasible at depth 2 (B783, B802, B1177, B1178, B1185, B1186); the four -6,118 reads (B822, B840, B858, B876) are budget-limited. Calibrations pass exactly (generator = sk2; k554 rediscovered).

## Tools (`scripts/`)

- **`gen2.py`: vectorised candidate generator** for r3 B's `sk2.Round` model, with the cone-aware admission test
  (r3 B `tools/cone.py`) applied during generation. sk2 loops over every (insert x, holder y, position p); at depth 2 on
  B822 that is 155,378 holder positions x 704 registers, about 109M evaluations. gen2 instead builds per-position tables
  over all registers (oracle frame pairs, chain-neighbour pairs, final-row and port-row columns), memoises the oracle cost
  (`Orc.cost`) on interned frames and the cone verdict (`LU.ok`) on interned neighbours, and deduplicates in NumPy with
  sk2's exact tie rules (per key: minimum cost, then largest position, then holder order; keys ordered by first encounter).
  Holder windows, basis and coordinates are sk2's own exact rationals.
- **`gen2.model_lean`: memory-lean CP-SAT model.** sk2's `Round.model` keeps one Python `(j, Fraction)` tuple per
  equation term; at depth 2 that exceeded the 6 GiB cap (B822 and B840 were killed at 6.04 and 6.76 GiB, logs kept as
  `runs/d2-822/killed-oldmodel.log`, `runs/d2-840/killed-oldmodel.log`). The lean builder writes the same equations (one
  common positive scale), budget, cardinality and objective from interned integer arrays straight into the CP-SAT proto,
  and encodes PR2142's "direct" interaction ban with per-register prefix-OR literals (linear instead of quadratic size).
- **`run2.py`**: r3 B's `runjob2.py` driver (cone-aware proposals, set test, minimal-conflict cuts, optional residual
  repair) on gen2 with a depth option. **`lane.sh`** runs jobs under r3 B's `capped.py` (900 s, 6 GiB). **`calib.py`**,
  **`summarize.py`**.

## Calibration (`out/CALIBRATION.json`, `out/CALIB-B783-d1.json`)

1. **Generator = sk2, exactly.** On B783 at depth 1 with the cone test, `gen2` returns sk2's candidate list identically:
   4,120 candidates in the same order, same representatives (x, y, position), coordinates, columns and costs, and the same
   130,438 cone rejections. Time 7.3 s against sk2's 73.3 s.
2. **k554 positive control.** On #1672's pivot-566-only word (`step0-gauge44.json.gz`, B342 deleted), with PR2142's
   direct (non-interacting) rule, the first exact round-1 proposal at depth 1 (2,882 candidates) and at depth 2 (5,210
   candidates) is k554-signed-001 itself: 122 += 554, 126 += 554, 186 -= 554 (B0), 74 -= 554 (B517) and 74 -= 554
   (tail 84), priced exactly at -1,856 at this b (-1,850 at #1094's). A second exact 6-insert variant (a 381 window) prices
   the same; then round 1 is INFEASIBLE. The lean model reproduces both proposals and the stop exactly (`runs/ctl1L`,
   `runs/ctl2L` against `runs/ctl1`, `runs/ctl2`).
3. **Rejected tool: aggregated relaxation.** Replacing each basis block's rows by K = 6 random integer combinations is a
   sound relaxation, but CP-SAT returned UNKNOWN on the k554 control in 180 s (large coefficients defeat propagation), so
   it was not used (`runs/ctl2A`; its B1185 run was aborted).

## Search (base word, depth 2, PR2142's direct rule, at most 12 inserts, quarter-step lambda |lambda| <= 4, cone-aware)

Round 1 is the first-order split-key model of r3 B's sk2 with depth-2 keys (values held by or added into the registers
that add into the deleted read's source and target), budget -ddel - 1 and per-insert cap = budget. CP-SAT single-threaded.
"INFEASIBLE" is a CP-SAT proof within this finite model; "UNKNOWN" means the time limit ran out with no solution found.

| Target | Deletion gain | Depth-2 family regs | Basis | Candidates | Exact model, 300 s | LP level 2, 1,200 s | Presolve + LP 2, 600 s | Outcome |
|---|---:|---:|---:|---:|---|---|---|---|
| B822 | -6,118 | 13 | 35 | 80,660 | UNKNOWN | UNKNOWN | UNKNOWN | **UNKNOWN** |
| B840 | -6,118 | 13 | 33 | 79,844 | UNKNOWN | UNKNOWN | UNKNOWN | **UNKNOWN** |
| B858 | -6,118 | 13 | 31 | 78,972 | UNKNOWN | UNKNOWN | UNKNOWN | **UNKNOWN** |
| B876 | -6,118 | 13 | 29 | 78,119 | UNKNOWN | UNKNOWN | — | **UNKNOWN** |
| B783 | -6,781 | 5 | 11 | 5,326 | INFEASIBLE | — | — | **INFEASIBLE** |
| B802 | -6,781 | 5 | 11 | 5,326 | INFEASIBLE | — | — | **INFEASIBLE** |
| B1177 | -8,879 | 13 | 71 | 49,134 | UNKNOWN | INFEASIBLE | — | **INFEASIBLE** |
| B1178 | -8,879 | 12 | 81 | 70,943 | INFEASIBLE | — | — | **INFEASIBLE** |
| B1185 | -8,879 | 13 | 70 | 48,661 | UNKNOWN | INFEASIBLE | — | **INFEASIBLE** |
| B1186 | -8,879 | 12 | 78 | 69,377 | INFEASIBLE | — | — | **INFEASIBLE** |

- **No exact candidate arose on any target, so nothing was priced and there is no gain.** No gain_certified interval,
  audit, native chain, kappa estimate or extra-word transfer applies.
- **Proofs: B783, B802, B1177, B1178, B1185, B1186.** Their depth-2 round-1 models are infeasible. B783's verdict was cross-checked with r3 B's original
  `sk2.Round.model` builder (`runs/chk-783-sk2model`: INFEASIBLE in 17.7 s), so the lean builder and sk2 agree. B1185 was
  UNKNOWN at 300 s and was proved INFEASIBLE in 82 s with CP-SAT's LP linearization level 2.
- **Budget-limited: B822, B840, B858, B876.** These models have 78-81k candidates and about 18M nonzero equation terms (B822 measured:
  17,995,916; the sound singleton presolve removes only 97 candidates). CP-SAT found no solution and no proof in 300 s
  (exact model), 1,200 s (LP level 2) or 600 s (presolve + LP level 2). This is a scoped "no solution found", not a proof.
- **Scope.** Base word only. The extra word shares the gate sequence (r3 A), but this cone-aware depth-2 model's transfer was
  not re-derived. First order only (direct rule, no residual repair); keys to depth 2, not 3; deletions taken singly.

## Next step

The four -6,118 reads need a smaller exact formulation before CP-SAT can decide them. Options: drop the candidates whose
equation rows are dominated (a support/rank presolve beyond singletons), split by the basis block that carries the
residual, or let CP-SAT use its portfolio (several workers) on one target at a time with a 30-60 minute budget.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
