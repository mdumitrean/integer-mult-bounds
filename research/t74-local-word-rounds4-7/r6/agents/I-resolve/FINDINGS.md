# r6 I-resolve: the four depth-2 models for B822/B840/B858/B876 (all infeasible; no kernel)

Written from the agent's final message: the subagent harness blocked its REPORT.md and FINDINGS.md.

- **LP route:** fails. B783 under D's candidates is LP-feasible even though its integer model is infeasible, because
  fractional selections take zero-cost candidates for free, so there is no Farkas certificate.
- **Oracle sentinels:** #1957's oracle prices some legal inserts at 2^60, and D's cost cap had dropped 14-15 of them per
  target. Each 2^60 candidate was re-priced exactly as a standalone insert with rigorous lower bounds:

  | Target | Sentinels | Within budget | Provably over |
  |---|---:|---:|---:|
  | B822 | 54 | 14 | 40 |
  | B840 | 53 | 14 | 39 |
  | B858 | 56 | 15 | 41 |
  | B876 | 54 | 15 | 39 |

- **How they were settled:** CP-SAT on a growing set of equation rows, keeping D's interaction ban, <= 12 inserts and the
  budget. An infeasible restriction proves the full model infeasible.
  - Calibration: B783 comes out infeasible in 3 iterations, and the pivot-566-only word gives k554-signed-001 first.
  - All four targets are infeasible in 2 iterations, in D's model and in the sentinel-corrected one. The final
    restrictions have 78-418 rows and 912-29,209 candidates.
  - HiGHS confirms all 8 restrictions; SCIP confirms some and timed out on the rest.
- **With no cost information (B822):** the only exact solutions are relocations of the deleted read at delta 0.
- **Scope:** first order with the ban, key depth 2, base word only.
- **Evidence:** `EVIDENCE.json`, `runs/`, `scripts/`.
