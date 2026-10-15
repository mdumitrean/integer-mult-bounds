# r6 / M-bigB: compensation census for the large B-deletion classes (566+554 base word)

Agent M-bigB (round r6, 2026-10-15, start 06:08Z). Word `r3/inputs/gauge44-word-566-554.json.gz` (#1672 blob 76c01583), b = 0.001679754956125544. Local only: no commits, pushes or posts.

**Outcome: no gain (κ unchanged).** 112 of 151 class/shape representatives searched; status counts {'shape-infeasible': 49, '4 exact proposals': 26, 'INFEASIBLE': 35, 'stop UNKNOWN (budget/cut limit)': 2}; 230 exact proposals priced, 0 with a negative delta.

Every exact proposal prices at Δ >= 0 (distinct values [0, 4925, 5886, 6781, 7984]): the Δ = 0 ones are neutral alternatives, the others cost more than the deletion saves. No negative delta arose, so no gain_certified interval, audit_local.py or native chain run was needed. Time-limited: B975 (-21530, 75474 candidates), B1180 (-15968, 87631 candidates).

## Model

- r5 D-compsplit's projected split-key model (`sk3.PRound`, driver `run3.py`), unchanged except candidate generation (`scripts/sk5.py`, driver `scripts/run5.py`): inserts anywhere in B or the early tail, quarter-step |λ| <= 4, <= 12 inserts, budget |gain| - 1 (#1957 oracle), r3 B's exact single-insert cone test, compensation re-derived (port-row ordinary-helper columns projected out), direct exactness and frame checks with lazy cuts, exact proposals priced by r5 D's `price3.py`.
- **Sentinels:** an insert the #1957 oracle prices at INF (2^60) is never pruned by cost. If it passes the cone test it is kept at cost 0 (optimistic lower bound), so INFEASIBLE / shape-infeasible remain proofs within the model. In these large-deletion models sentinels are most of the candidates (thousands to tens of thousands per job): every earlier cost-pruned run dropped them.
- **Re-insertion ban:** inserts re-reading the deleted (target, source) pair are excluded (`ban_reinsert`). Without the ban (control run B1061, `runs/RUN-t1061.json`) the cheapest exact solutions are pure relocations of the deleted read, which #1957's 4,461-move census and r3 D's re-timing families already price at >= 0.
- **Structural reruns:** for jobs whose first proposals are variants of one structure, `pair_nogood` forbids the same set of (x, y) pairs so each further proposal is structurally different (K = 8).
- **Calibration:** on #1672's pivot-566-only word, deleting B342 returns k554 in three equivalent 5-insert placements (`runs/RUN-calib.json`), as in r5 D.

## Per class (representative per gate shape; `out/TABLE.md` has every job)

| Class Δ | Members | Reps run | Status of reps | Priced proposals |
|---:|---:|---:|---|---|
| -26461 | 14 | 2 of 2 | {'shape-infeasible': 2} | - |
| -25742 | 2 | 1 of 1 | {'shape-infeasible': 1} | - |
| -23876 | 8 | 2 of 2 | {'4 exact proposals': 2} | B949: 6781; B950: 6781 |
| -23634 | 16 | 6 of 6 | {'shape-infeasible': 6} | - |
| -23402 | 2 | 1 of 1 | {'INFEASIBLE': 1} | - |
| -22749 | 16 | 1 of 1 | {'INFEASIBLE': 1} | - |
| -22096 | 24 | 2 of 2 | {'shape-infeasible': 2} | - |
| -21530 | 72 | 5 of 5 | {'shape-infeasible': 4, 'stop UNKNOWN (budget/cut limit)': 1} | B975: 4925 |
| -20893 | 16 | 1 of 1 | {'shape-infeasible': 1} | - |
| -20817 | 4 | 2 of 2 | {'shape-infeasible': 1, 'INFEASIBLE': 1} | - |
| -19922 | 6 | 1 of 1 | {'4 exact proposals': 1} | B1053: 6781 |
| -19690 | 2 | 1 of 1 | {'INFEASIBLE': 1} | - |
| -19037 | 24 | 2 of 2 | {'shape-infeasible': 2} | - |
| -19027 | 4 | 1 of 1 | {'4 exact proposals': 1} | B808: 4925 |
| -18719 | 50 | 11 of 11 | {'shape-infeasible': 8, 'INFEASIBLE': 3} | - |
| -18066 | 8 | 3 of 3 | {'INFEASIBLE': 2, '4 exact proposals': 1} | B1226: 0, 4925 |
| -17834 | 2 | 1 of 1 | {'shape-infeasible': 1} | - |
| -17824 | 28 | 8 of 8 | {'INFEASIBLE': 4, 'shape-infeasible': 2, '4 exact proposals': 2} | B1225: 0; B1233: 0 |
| -17171 | 4 | 1 of 1 | {'shape-infeasible': 1} | - |
| -16863 | 48 | 9 of 9 | {'shape-infeasible': 1, 'INFEASIBLE': 6, '4 exact proposals': 2} | B921: 5886; B1055: 7984 |
| -16621 | 58 | 9 of 9 | {'INFEASIBLE': 3, '4 exact proposals': 4, 'shape-infeasible': 2} | B554: 4925; B580: 0, 4925; B638: 0, 4925; B659: 0, 4925 |
| -16210 | 4 | 1 of 1 | {'4 exact proposals': 1} | B1212: 0 |
| -15968 | 112 | 20 of 20 | {'shape-infeasible': 12, 'INFEASIBLE': 2, '4 exact proposals': 5, 'stop UNKNOWN (budget/cut limit)': 1} | B1173: 0; B1180: 0; B1182: 0; B1187: 0; B1214: 0; B1216: 0 |
| -14851 | 2 | 1 of 1 | {'INFEASIBLE': 1} | - |
| -14765 | 12 | 3 of 3 | {'INFEASIBLE': 3} | - |
| -14749 | 80 | 12 of 13 | {'shape-infeasible': 3, '4 exact proposals': 3, 'INFEASIBLE': 6} | B957: 4925; B973: 4925; B974: 4925 |
| -13804 | 6 | 1 of 1 | {'4 exact proposals': 1} | B660: 4925 |
| -13562 | 32 | 4 of 8 | {'INFEASIBLE': 1, '4 exact proposals': 3} | B1407: 0; B1408: 0; B1412: 0; B1424: 0 |

**Structural reruns** (`pair_nogood`, K = 8):

- R949 (Δdel -23876): 1 proposal(s), then INFEASIBLE; prices [6781].
- R950 (Δdel -23876): 1 proposal(s), then INFEASIBLE; prices [6781].
- R1053 (Δdel -19922): 1 proposal(s), then INFEASIBLE; prices [6781].
- R808 (Δdel -19027): 1 proposal(s), then INFEASIBLE; prices [4925].
- R1226 (Δdel -18066): 1 proposal(s), then None; prices [4925].
- R1225 (Δdel -17824): 1 proposal(s), then INFEASIBLE; prices [0].
- R1233 (Δdel -17824): 1 proposal(s), then INFEASIBLE; prices [0].
- R580 (Δdel -16621): 5 proposal(s), then INFEASIBLE; prices [0, 4925].
- R638 (Δdel -16621): 5 proposal(s), then None; prices [0, 4925].
- R659 (Δdel -16621): 5 proposal(s), then None; prices [0, 4925].
- R1212 (Δdel -16210): 1 proposal(s), then None; prices [0].
- R1173 (Δdel -15968): 1 proposal(s), then INFEASIBLE; prices [0].
- R1182 (Δdel -15968): 1 proposal(s), then INFEASIBLE; prices [0].
- R1187 (Δdel -15968): 1 proposal(s), then INFEASIBLE; prices [0].
- R1214 (Δdel -15968): 1 proposal(s), then INFEASIBLE; prices [0].
- R1216 (Δdel -15968): 1 proposal(s), then INFEASIBLE; prices [0].
- R1407 (Δdel -13562): 1 proposal(s), then INFEASIBLE; prices [0].
- R1408 (Δdel -13562): 1 proposal(s), then INFEASIBLE; prices [0].
- R1412 (Δdel -13562): 1 proposal(s), then INFEASIBLE; prices [0].
- R1424 (Δdel -13562): 1 proposal(s), then INFEASIBLE; prices [0].

**Not run (time):** 39 representatives: B1010 (-14749), B1411 (-13562), B1423 (-13562), B1824 (-13562), B1832 (-13562), B893 (-13546), B1194 (-13546), B470 (-12909), B471 (-12909), B475 (-12909), B1567 (-12909), B1568 (-12909), B1580 (-12909), B1583 (-12909), B1584 (-12909), B1695 (-12909), B1711 (-12909), B1663 (-12256), B1664 (-12256), B1675 (-12256), B1676 (-12256), B1679 (-12256), B1680 (-12256), B849 (-11938), B868 (-11938), B881 (-11938), B882 (-11938), B645 (-10503), B1439 (-9850), B1440 (-9850), B1455 (-9850), B1456 (-9850), B1504 (-9850), B1516 (-9850), B1520 (-9850), B1635 (-9850), B469 (-9592), B474 (-9592), B477 (-9592)

**Remaining:** structural reruns (`pair_nogood`) of the Δ = 0 proposal jobs, the time-limited jobs with a longer limit, the unrun representatives above, and A-section inserts.

## Follow-up (07:30-08:30Z): skipped representatives, Δ = 0 reruns, timeouts

- **Skipped representatives:** 39 of 39 run; outcomes {'INFEASIBLE': 24, 'stop UNKNOWN (budget/cut limit)': 1, '4 exact proposals': 9, 'shape-infeasible': 5}; priced deltas [0].
- **Δ = 0 reruns** (`pair_nogood`, K = 8): 16 of 16 run; stop states {'None': 4, 'INFEASIBLE': 12}; priced deltas [0, 4925].
- **B975 (timeout) via r6 I-resolve's row generation** (`scripts/export_sys.py` + I's `rowgen.py`, ROWGEN_BAN=0): PROPOSAL_LIMIT after 20 iterations, 20 first-order proposals; 16 pass full exactness + frames; priced deltas [4925]. Positive control: B949's exported system yields its known window solutions (`runs/RG-B949.json`).
- **B1180 (timeout) via r6 I-resolve's row generation** (`scripts/export_sys.py` + I's `rowgen.py`, ROWGEN_BAN=0): PROPOSAL_LIMIT after 22 iterations, 20 first-order proposals; 20 pass full exactness + frames; priced deltas [0]. Positive control: B949's exported system yields its known window solutions (`runs/RG-B949.json`).

## Scope

- Base word only (the extra word shares the gate sequence, r3 A). One representative per (class, gate shape); members of a shape were assumed equivalent, not proven. First order with exact checks, one round, <= 12 inserts, |λ| <= 4 in quarter steps, B/tail inserts only (no A-section inserts), deleted pair not re-read, at most K proposals and 15-20 cuts per job.
- INFEASIBLE / shape-infeasible are proofs within this model (sentinels optimistic at 0), not supplier lower bounds. Jobs that stopped on a time or cut limit are reported as such.

## Evidence

`out/EVIDENCE.json` (every job, priced proposals, gains), `out/TABLE.md`, `out/CLASSES.json`, `out/JOBS.json`, `out/LANES.json`; `runs/RUN-*.json`, `runs/*.cap.log` (solver logs), `runs/PRICED-*.json`; scripts in `scripts/` (sk5.py, run5.py, queue.sh, lane3b.sh, classes.py, summarize.py, report.py). Files in `runs/` whose names contain spaces come from a first launch whose lane arguments were not split; they hold no results.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
