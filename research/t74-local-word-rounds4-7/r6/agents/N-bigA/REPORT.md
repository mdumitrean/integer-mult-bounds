# r6 / N-bigA: compensation census for the large A-deletion classes (566+554 base word)

Agent N-bigA (round r6, 2026-10-15, about 06:08-07:35Z). Word `r3/inputs/gauge44-word-566-554.json.gz` (#1672 blob
76c01583), b = 0.001679754956125544. Local only: no commits, pushes or posts.

**Outcome: scoped negative result, no κ change.** In every searched class, the only exact compensations of the deleted
A gate within the model are relocations of that gate (or, in the −19,700 and −9,850 classes, re-routings of it through a
partner register with the same source); all 88 such proposals price exactly at Δ = 0 with the compensation unchanged
(7,208 gates). After they are cut the model is INFEASIBLE, for all 11 class representatives and 12 of 14 further
class members (the other two, A1866 and A2479 of the −9,850 class, stayed UNKNOWN after their re-routings even with 900 s solves: no further solution was found, but that is not a proof). No negative delta, so nothing needed the auditor or the native chain.

## Classes (r3 A-extra's A relaxation, same program on both words)
| Class gain | Members | Representatives (gate) | Further members sampled |
|---:|---:|---|---|
| −23,644 | 2 | A3305 `439 += 437`, A3311 `444 += 52` | — (both members run) |
| −20,893 | 62 | A1303 `231 += 229`, A1308 `62 += 63` (helper and data targets) | A1464, A1772, A3312 |
| −19,700 | 12 | A1401 `240 += 24` | A1863, A3095 |
| −19,690 | 16 | A2077 `312 += 314`, A2078 `70 += 71` | A2693, A2850 |
| −19,037 | 8 | A2073 `311 += 309` | A2227, A2230 |
| −16,631 | 8 | A3001 `408 += 410`, A3002 `94 += 95` | A3155, A3158 |
| −9,850 | 172 | A1247 `224 += 56` | A1866, A2479, A3263 |

Members of a class share the relaxation's Δ and profile. Symmetry is not proved: sampled members were chosen at the median,
quartile and last index. They reproduce their representative's pattern; for example A1863/A3095 repeat A1401's pair
re-routing (`288/289 += 32` vs `240/241 += 24`). The −9,850 class is not uniform: its members' targets have 57-85 nonzero
rows against 69 for A1247.

## Model
- G-ainsert's `sk4.PRound4` (first-order projected split-key model; from r5 D's `sk3.py`, r3 B's `sk2.py`, PR2142 /
  Ian Libânio's `skkernel.py`, PR1957 / Rohan Arun's `abkernel.py`). Inserts `x += λ·y` may sit in an A window (±350
  gates around the deletion; the whole A section for A3305, A1303, A3001, A2073, A1247) and anywhere in B or the early
  tail; no A insert touches a port; cone-aware admission (r3 B's `cone.LU.ok`, cut equality included).
- λ in quarter steps, |λ| ≤ 4; at most 12 inserts; summed budget |gain| − 1 and per-insert cap = budget, from #1957's
  oracle. **Oracle sentinels:** every 2^60 estimate is clipped to cost 1, so no candidate is ever pruned by sentinel cost;
  exact pricing decides. This makes the model a relaxation in those candidates, so INFEASIBLE stays a valid verdict.
- Every first-order solution is checked on the true map (projected exactness: non-port rows exact, port rows up to the
  ordinary-helper columns the re-derived compensation absorbs) and with the exact frame set test, then priced by r5 D's
  `absorb.py` (compensation re-derived, recomputed cone caps, certified optimal frames, true-moment interval).
- Two solvers: G's full CP-SAT loop (`run4.py`), and row generation (`tools/rowgen4.py`, after r6 I-resolve's
  `rowgen.py`): equations restricted to a growing row set; an infeasible restriction proves the full first-order model
  infeasible. Calibration: on A3305, row generation reproduces the full model exactly (the same two relocations, then
  INFEASIBLE). The full model left A2073 and A2077 UNKNOWN (120 s and 600 s per solve); row generation settles them in
  under a second per iteration.

## Results
See `out/TABLE.md` (one row per run). Summary per class:
- −23,644: A3305 and A3311: relocations only (A3301/A3322; A3301/A3312), then INFEASIBLE; also with the whole A section.
- −20,893: A1303, A1308, A1464, A1772, A3312: relocations only, then INFEASIBLE (A1303 also with the whole A section).
- −19,700: A1401, A1863, A3095: six exact proposals each (relocations and pair re-routings), then INFEASIBLE.
- −19,690: A2077, A2078, A2693, A2850: relocations (A2078 also a 9-insert relocation-plus-cancelling-pairs variant from the
  full model), then INFEASIBLE.
- −19,037: A2073, A2227, A2230: relocations, then INFEASIBLE (A2073 also with the whole A section, 70,918 candidates).
- −16,631: A3001, A3002, A3155, A3158: relocations, then INFEASIBLE (A3001 also with the whole A section).
- −9,850: A1247 (both windows) and A3263: relocations / re-routings, then INFEASIBLE; A1866 (six re-routings) and A2479 (two relocations) found nothing else before the solver stalled (UNKNOWN at 900-1,300 s; not a proof).
Exact pricing: 88 proposals, all `ok`, Δ = 0, compensation 7,208 gates. `out/EVIDENCE.json` "gains": [].

## Scope and limitations
- First order, one round, depth-1 key family, finite model; INFEASIBLE verdicts are proofs within this model only.
- After a proposal, its support and all supersets are cut, so "relocation plus a cancelling set of extra inserts"
  solutions are not re-enumerated. The one such solution found by the full model, A2078's 9-insert variant, priced Δ = 0.
- Interacting inserts are allowed in solutions but the equations are first order; second-order repairs (r3 B, r6 E) were
  not run here.
- Windows: ±350 gates (five representatives also with the whole A section).
- Extra word not run. r3 A showed it is the same program; only frame-dependent oracle costs and cone tests on registers
  624-631 could differ.
- Unsampled class members (the bulk of the −9,850 and −20,893 classes) are not individually searched.

## Evidence and tools
- `out/EVIDENCE.json`, `out/TABLE.md`, `out/PLAN.json`; specs `out/SPEC-*.json`; runs `out/RUN-*.json`
  (full model), `out/RG-*.json` (row generation); prices `out/PRICED-*.json`; logs `out/*.cap.log`; `out/chain.log`.
- `tools/rowgen4.py` (new), `tools/summarizeN.py`, lane scripts `chainN.sh`, `priceN.sh`, `rgN.sh`, `priceRG.sh`,
  `qN.sh`, `qL.sh`; copies of G's `sk4.py`/`run4.py`, r5 D's `sk3.py`/`absorb.py`/`price3.py`, r3 B's `sk2.py`/`cone.py`,
  `capped.py`, the rev3 toolkit (`toolkit/`) and #1957's package (`work/`).
- At most 4 worker processes at a time, each under `capped.py` (timeout and 6 GiB RSS cap); peak RSS 1.04 GiB;
  CP-SAT single-threaded.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
