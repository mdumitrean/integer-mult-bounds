# r6 / Q-blocks: block deletions on the 566+554 base word

Agent Q-blocks (round r6, 2026-10-15, start 07:35Z). Word `r3/inputs/gauge44-word-566-554.json.gz` (#1672 blob 76c01583),
b = 0.001679754956125544. Local only: no commits, pushes or posts.

**Outcome: no gain, kappa unchanged.** No block deletion admitted a cheaper exact joint compensation, and the one new
composite re-synthesis family (butterfly to cleanup prepend) is frame-infeasible in all 112 cases.

## 1. Joint deletion relaxations (`out/RELAX-SUMMARY.json`, `runs/RELAX-*.json`)

182 exact joint deletions (certified optimal frames under the base caps, no compensation; 179 certified, 3 uncertified),
over the representative blocks of the large classes: full blocks, halves and every adjacent pair. Singles are r3 A's
relaxations (same program on both words).

- Disjoint A layers (A1303-1310, A2073-2080, A2997-3004, A3305-3312: 8 gates on 16 distinct registers): pairs and
  quads are exactly additive; the full 8-blocks are sub-additive (A1303-1310: -154,868 against -167,144).
- **Superadditive blocks (32 rows, 22 distinct):** the largest excess is in two-gate B port-delivery pairs:
  B1439-1440 -43,642 vs -19,700 singles (-23,942 extra), B1407-1408 -49,210 vs -27,124, B1503-1504 -39,930 vs -19,700,
  B1567-1568 -36,311 vs -25,818; then the A fan-out blocks A1405-1409 / A1251-1255 (-68,267 vs -49,250) and A1247-1255
  (-105,820 vs -88,650), B1125-1132 (-191,616 vs -176,768), B735-738 / B809-812 (-74,471 vs -63,872), B1061-1068
  (-221,312 vs -211,688), B737-738, B1128-1129, B1064-1065, B1173-1176 and others.

## 2. Joint compensation searches (`runs/RUN-*.json`, `runs/*.cap.log`)

Model `scripts/sk6.py` + `scripts/run6.py`: agent G-ainsert's sk4 (A-window and B/tail inserts; r5 D's projected split-key
model with the compensation re-derived) with agent M-bigB's sentinel rule (cone-valid 2^60-sentinel inserts kept at cost
0), re-reading any deleted (target, source) pair banned for A and B deletions, budget = |joint relaxation| - 1, <= 12
inserts, quarter-step |lambda| <= 4, cone-aware admission, direct exactness and frame checks with lazy cuts. A
`drop_sentinels` option (phase 1) searches only oracle-priced candidates.

| Block | Joint relaxation | Sentinels | Outcome |
|---|---:|---|---|
| B735-738 (4) | -74,471 | kept (101,344) | INFEASIBLE (proof in model) |
| B1125-1132 (8) | -191,616 | kept (134,867) | INFEASIBLE (proof in model) |
| A1405-1409 (5, A window 1055-1760) | -68,267 | kept (40,860) | shape-infeasible (proof in model) |
| B1439-1440, B1407-1408, B1503-1504, B1567-1568 (pairs) | -43,642 / -49,210 / -39,930 / -36,311 | dropped | INFEASIBLE on all oracle-priced candidates |
| B1128-1129, B737-738, B1064-1065 (pairs), B1061-1068 (8) | -47,904 / -39,698 / -55,328 / -221,312 | dropped | shape-infeasible on oracle-priced candidates |
| B1439-1440, B1503-1504 | as above | kept | every proposal is a 2-insert pair failing cone-cap containment late in B (B1532-B1850); 39 and 12 frame cuts, then the 900 s cap: not a proof |
| A1247-1255 (9, A window 897-1606) | -105,820 | dropped (38.3M) | shape-infeasible on oracle-priced candidates |
| B1407-1408 | -49,210 | kept (42,804) | first 20 s CP-SAT solve UNKNOWN: not a proof |

So the only exact compensations of the superadditive pairs use sentinel inserts (re-deliveries the #1957 oracle cannot
price), and every one tested is frame-infeasible.

## 3. Block re-synthesis

- **Lower bound (exact):** an add gate `t += c*s` changes one row of the map, so an exact sequence over a block's own
  registers needs at least one gate per distinct target, plus one per extra source of a shared target. Every block here
  (disjoint layers, fan-outs A1247-1255, chains A1401-1409, shared-target quads B735-738) is already that short, so no
  shorter exact block exists; equal-length alternatives are reorderings, which #1957's commuting census and r3 D cover.
- **New composite family, butterfly to cleanup (`scripts/bfly_scan.py`, `scripts/bfly_price.py`, `runs/BFLY-ALL.json`):**
  every superadditive pair is the output stage of a two-gate butterfly (e.g. B1437-1438 `279 += 359; 359 += -1/2*279`,
  then B1439/B1440 deliver into ports 139/142). All 112 B butterflies have outputs used only by port deliveries and are
  untouched afterwards in B and the early tail. Rewrite: delete the butterfly and its deliveries, re-deliver each port from
  the pre-butterfly values (4 deliveries), and prepend the butterfly to the frame-free cleanup. Exact by construction and
  accepted by the rev3 harness's static rules, exactness screen and compensation check; **all 112 are frame-infeasible**
  ("L not inside U at mutable vertex"): a port reading both pre-butterfly values breaks its end-hyperplane cap.

## Scope

Base word only (the extra word shares the gate sequence, r3 A). One representative per block shape; first order, one
round, <= 12 inserts, |lambda| <= 4 in quarter steps, deleted pairs not re-read. INFEASIBLE / shape-infeasible with
sentinels kept are proofs within this model; with sentinels dropped they cover only oracle-priced candidates. No negative
delta arose, so no interval certificate, auditor or native-chain run was needed.

## Evidence

`out/BLOCKS.json` (block catalogue), `out/RELAX-SUMMARY.json`, `out/RELAX-JOBS*.json`, `out/BFLY-SCAN.json`,
`out/EVIDENCE.json`; `runs/RELAX-*.json`, `runs/RUN-*.json`, `runs/SPEC-*.json`, `runs/*.cap.log`, `runs/BFLY-ALL.json`;
scripts `blocks.py`, `relax_blocks.py`, `sk6.py`, `run6.py`, `lane.sh`, `bfly_scan.py`, `bfly_price.py`, `summarize.py`.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).

## Follow-up (08:27-09:04Z): the three superadditive pairs with sentinels kept

Coordinator task: settle B1407-1408, B1439-1440 and B1503-1504 with cone-valid 2^60-sentinel inserts kept at cost 0.
**No gain; all three remain UNKNOWN (no proof, no solution).**

- Systems (`scripts/export_pair.py`, from M-bigB's export_sys.py; `runs/sys/*`): B1407-1408 52,682 candidates (42,804
  sentinels), B1439-1440 21,741 (11,649), B1503-1504 35,306 (25,822); ~7.5-8.9k rows, 3 nonzero rhs rows each; an A-window
  variant of B1439-1440 (A 2000-3451, sk6) has 23,597 candidates.
- Growing-row solver with in-loop checks (`scripts/rowgen_q.py`, from I-resolve's rowgen.py; ROWGEN_BAN=0): every exact
  proposal is applied, exactness re-checked on the whole map, frames tested; a minimal conflicting subset becomes a no-good
  (valid for supersets), frame-feasible exact proposals would be priced. Results, all exact and all frame-infeasible, each
  with a 2-insert minimal conflict: B1439-1440 410 (time limit), B1503-1504 665, B1407-1408 235 + 48 more with the exact
  conflict-star accelerator (`scripts/rowgen_qa.py`: 96 stars, 2.6M pairwise no-goods; each conflicting insert is
  frame-incompatible with about half of all candidates), A-window B1439-1440 24. **Zero frame-feasible exact proposals.**
- Cover proofs (`scripts/pairproof.py`, `scripts/coverproof.py`): every exact solution must contain inserts hitting all
  three rhs rows, and frames are monotone, so the absence of a frame-feasible covering set would be a proof. It is not
  closed: B1439-1440 has 5,056 frame-compatible pairs across its two smallest rows, and each system has >200
  frame-compatible pairs covering all three rows. Exactness, not coverage, is what fails; no 2-insert exact solution exists
  (the cost-minimising solver always returned 4-insert supports).
- Nothing reached pricing, so no gain_certified / auditor / native run was needed. Evidence: `out/FOLLOWUP.json`,
  `runs/sys/*`, `runs/rgq-*.cap.log`, `runs/rgqa-p1407.cap.log`, `runs/RGQ-p1439.json`, `runs/CP-*.json`, `runs/PP-p1439.json`.

## Second follow-up (09:05-09:12Z): explicit pairwise frame-conflict graph

`scripts/cgraph.py` (per pair: `out/CG-*-final.json`, checkpoints `out/CG-*-ckpt.json`, logs `runs/cg-*.cap.log`): the
exactness model with growing equation rows, where every candidate entering the row-restricted set C_K gets its exact
pairwise frame conflicts with all candidates present (cone.LU's single-insert test on W1+a; on a shared position the pair
conflicts only if both placements fail), encoded as one star constraint per candidate (sum of conflicting z + 12 z_a <= 12).

| Pair | Candidates in C_K / rows | Pair tests | Conflict pairs (mean degree) | Exact, frame-feasible | Priced |
|---|---:|---:|---:|---:|---|
| B1407-1408 (joint -49,210) | 1,657 / 45 | 1,371,996 | 181,163 (109) | 8, then INFEASIBLE | all Δ = 0, compensation 7,208 |
| B1503-1504 (joint -39,930) | 2,395 / 38 | 2,866,815 | 295,232 (123) | 8, then INFEASIBLE | all Δ = 0 |
| B1439-1440 (joint -43,642) | 2,041 / 49 | 2,081,820 | 229,064 (112) | 8, then INFEASIBLE | all Δ = 0 |

The 24 compensations are "piggyback" windows: a temporary `h += y ... h -= y` on the source of the neighbouring pair's
delivery (B1407-1408: 315 += 283 and 1 += 379, so B1415 `171 += -1/2*315` and B1420 `174 += 1` carry the deleted values),
re-delivering both values through existing deliveries; each costs back exactly the joint deletion gain.

**Proof statement.** Within the first-order projected split-key model (sentinel inserts at cost 0, deleted pairs banned,
<= 12 inserts, |λ| <= 4 in quarter steps, B/tail inserts, budget |joint relaxation| - 1): (i) frames are monotone, so every
frame-feasible set is pairwise frame-feasible and the star constraints are valid; (ii) a candidate outside C_K contributes
zero to the K rows, so the projection of any exact frame-feasible solution onto C_K satisfies the restricted model;
(iii) after the 8 supports above were found (each confirmed exact on the whole map, frame-feasible by the full frames.Graph
test, priced Δ = 0) and excluded, the restricted model is INFEASIBLE. Hence these 8 are the only exact frame-feasible
compensations of each pair in the model, and none gains. Completeness of the pair graph is not needed for this direction;
it relies on cone.LU's single-insert test being exact (no false rejections; r3 B's derivation and calibration). Every
solution was re-checked with the full Graph test; no conflict of size >= 3 arose.
