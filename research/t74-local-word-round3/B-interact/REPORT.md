# Agent B-interact (round r3): second-order helper-donor kernels on the 566+554 base word

**Task.** #2143 handoff items 1 and 3 on the base word (`inputs/gauge44-word-566-554.json.gz`, 249 calls): interacting
compensations with an exact residual-repair round, multi-deletion kernels, and a widened key family for the shape-infeasible
−6,100 B reads. All prices are at b = 0.001679754956125544. The deletion gains here are about 0.3% larger than #2142's,
because #2142 priced at #1094's endpoint: −6,781 here against its −6,763.

**Outcome: no exact profitable kernel in any searched family. No κ change.** Local-only evidence in this directory; nothing
was committed, pushed or posted.

## Method (`tools/sk2.py`, `tools/runjob.py`)

- **Round model.** The model works on the current word W: the base word, minus the deletions, plus any earlier-round
  inserts.
  - Target: `T = base map − map(W)`, in exact rationals. It covers the final rows (after A + cut + B + early tails)
    and the port rows 112–223 of the A·cut·B map, which the derived compensation reads.
  - Inserts: `x += λ·y`, where y's value at that position lies in the span of T's values plus the key family.
  - Equations: the per-basis column equations of PR2142's `skkernel.py`.
- **Holder rule.** It is wider than PR2142's: any value in the span qualifies, not only a multiple of one family key.
  The key family at depth 1 is the same as PR2142's: values held by, or added into, the deleted read's source and target.
- **Round 1 allows interactions.** No ban is applied.
  - Each proposal is checked exactly.
  - If it is inexact, its exact residual becomes round 2's right-hand side, solved on W2 itself. Interactions with
    round-1 inserts are therefore exact.
  - Pairs within round 2 that interact are cut lazily.
  - A diversity cut forbids each interacting writer that was already tried, so the next proposal must use a different
    mechanism.
- **λ steps.** λ is in quarter steps with |λ| ≤ 4 (half steps in the first runs). The first residual had ¼ entries.
- **Budget.** Up to 12 inserts per round, a PR1957-oracle per-insert cap equal to the budget, and the summed budget
  −Δdeletion − 1. The B783 diagnostic instead used 24 inserts, a 3× cap and no summed budget.
- **Exactness and pricing.**
  - Every candidate's whole map is checked in exact rationals, and its derived compensation must be identical (7,208
    gates).
  - It is then priced with exact optimal frames (cone caps, tail-mutable frames, cut equality).
  - `tools/verify_gain.py` (audit_local --main, rev3 harness with interval bounds) was ready but had nothing to verify.
- **Calibration.** PR2142's unchanged `skkernel.py` on B783 at this b gives 9 keys, 3,922 candidates, shape true and
  CP-SAT INFEASIBLE in 76 s. That is the same as PR2142 (`runs/cal`).
- **Environment.** agi venv (Python 3.14.7, OR-Tools 9.15). One process per job, at most 3 at once, each with a 2,400 s
  timeout and a 6 GiB RSS cap (`tools/capped.py`). Peak RSS was 2.1 GiB.
  - CP-SAT with 3 workers deadlocked (all threads idle in `NonDeterministicLoop`), so every search ran single-threaded.

## Coverage

- **Deletion sets: 25 in all, 21 singles and 4 pairs.**
  - The −6,781 writes of pivots 530 and 542: B783, B802.
  - The four −6,118 reads that PR2142 could not search for lack of shape: B822, B840, B858, B876.
  - The four −8,879 B reads: B1177, B1178, B1185, B1186.
  - Eight −4,925 early B reads: B1, B3, B8, B32, B36, B39, B44, and the two kernels' own direct reads.
  - The −3,059 pivot writes: B857, B875.
  - A1215 (−6,781) and A3403 (−8,879).
  - The pairs: same-source (B875+B1186) via 98 and (B857+B1178) via 74, both −12,909; the analogous pivots (B783+B802),
    −13,562; and the register pair (A1215+A1216), −13,562.
- **Searches:** 27 completed job runs, 16 round-1 proposals (all interacting) and 15 round-2 repair searches.
- **Candidates priced exactly:** 17. Of these, 16 are exact in the map but have infeasible frames. The other is A3403's
  read relocated to A3449, at Δ = 0. **None has Δ < 0.**
- **Not completed:**
  - B12 was stopped during its repair round when the budget ran out.
  - A depth-2 family run on B822/B858 was killed after 11 minutes of candidate generation (Python, about 1 GB).
  - Two duplicate B783/B802 runs were superseded by the diversity-cut runs.

## Results

1. **Item 3: widened keys for the −6,100 reads.** Span-based holders already make B822, B840, B858 and B876
   shape-feasible, with about 33.6k candidates each against PR2142's 15.9k, which were shape-infeasible.
   - CP-SAT then proves round 1 INFEASIBLE for all four, even with interactions allowed and quarter steps.
   - The obstruction for these reads is therefore algebraic or budget-bound, not shape.
2. **Item 1: interacting inserts.**
   - **No zero-cost proposal.** These targets have none, even with interactions allowed: B1177/B1178/B1185/B1186,
     A1215, A3403, B32, B36, B857 and B875, plus the pairs (B875+B1186), (B857+B1178) and (A1215+A1216). Round 1 is
     proven INFEASIBLE within 12 or fewer inserts and the budget. A3403 also has its Δ=0 relocation.
   - **B783 and B802: an unrepairable 6-insert core.** Each has one interacting core at oracle cost 0, which is the
     proposal PR2142 reported. For B783 it is:
     - `506 += 66` before base B931;
     - `114 −= 506` and `530 −= 506` before B1055;
     - `530 += 66` after the last early tail;
     - side terms at A63.

     Its exact residual has rank 1, value ½(e65 − e66 + e69 − e70), spread over 11 final rows and 6 port rows (506 is
     read throughout B). Within the budget the repair is INFEASIBLE with half and with quarter steps. Banning the core's
     writer makes round 1 INFEASIBLE. Dropping the summed budget (24 inserts, 3× cap) gives exact repairs, but at oracle
     cost 6,781, the whole deletion gain, and with infeasible frames. They amount to re-inserting the deleted read in
     halves.
   - **The −4,925 early reads (B1, B3, B8, B39, B44): second-order kernels exist but are frame-infeasible.**
     - They have zero-oracle-cost round-1 proposals, and round 2 finds exact repairs at oracle cost 0.
     - Example for B1 (`126 += 554`): `74 += 554` before base B911, `126 −= 74` before base B1273 and `554 −= 74` at the end, repaired by
       `74 −= 554` and `74 += 554`.
     - These are 16 words, exactly map-preserving and with an unchanged compensation (7,208 gates), but exact frames
       reject all of them. The checked reasons are all "L not inside U at mutable vertex" (cone-cap containment), at
       B1518 (B1), tail 75 (B39) and B1602 (B44).
     - The interacting trick parks a helper value in another register (a data register 74 or 98, or a helper such as
       585, 434 or 448) across B. That breaks a downstream cone cap, which PR1957's per-insert cost oracle does not model.
3. **Multi-deletion.** Pairs sharing a source or a pivot structure give no shared compensation. Their round 1 is
   INFEASIBLE, or for B783+B802 it is the union of the two unrepairable cores.

**Scope.**
- Base word only, at fixed b.
- At most two rounds of 12 inserts each (24 in the diagnostic), |λ| ≤ 4 in quarter steps.
- At most 2–5 round-1 proposals per target, with diversity cuts on interacting writers.
- Holders lie in span(residual values + depth-1 family). The PR1957 oracle sets each insert's cap and the summed budget.
- CP-SAT INFEASIBLE verdicts are proofs within this finite model only. They are not a supplier lower bound and do not
  cover other edit families, multi-level recursion or the extra word.

## Evidence

- `evidence/RESULTS.json` (every job), `evidence/TABLE.md`, `runs/*/{spec.json,log.txt,out.json}`. The out.json files
  hold every proposal's terms, the exact repair inserts and the prices.
- `runs/cal/` is the PR2142 calibration. `evidence/audit/base-word.json` is audit_local --main PASS on the base word.
- Tools: `tools/sk2.py` (round model), `tools/runjob.py` (driver), `tools/capped.py` (timeout and RSS cap),
  `tools/diag_resid.py`, `tools/why_infeasible.py`, `tools/verify_gain.py` (unused: there was no gain) and
  `tools/summarize.py`/`table.py`.
- Run with the agi venv, `IMB_B=0.001679754956125544`, `IMB_ROOT=<main worktree>`, `SK2_WORKERS=1`.
- Runtime: about 60 minutes of searches, 3 processes at a time, peak RSS 2.1 GiB.

## Best next step

**Make the oracle cone-aware before searching interacting families further.** Every zero-cost interacting kernel found
here dies on cone-cap containment, which the per-insert oracle cannot see.
- First step: in the candidate filter, compute for each insert x += λy whether y's frame span at p fits inside x's cone
  cap (the `caps` from `cone_caps`) over x's remaining lifetime. Reject or price the violating ones.
- Then rerun round 1 + repair on the −4,925 reads and B783/B802 (about 3 minutes per target on 1 core).
- Success test: a map-exact repair whose exact frames are feasible with Δ < 0.
- Stop test: round 1 INFEASIBLE for all targets under the cone-aware filter.
- Separately, the extra word (agent A's lane) and multi-level key recursion need a faster, vectorised candidate
  generator; depth 2 took more than 11 minutes per target in pure Python.

## Table

| Run | Deletions | Relaxation (units) | Basis / residual rank | Round-1 candidates | Shape | Round 1 | Round 2 (repair) | Exact priced | Gain |
|---|---|---:|---|---:|---|---|---|---|---|
| aA (lam/4, ban none) | A1215 | -6781 | 6 / 1 | 5137 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| aA (lam/4, ban none) | A1215+A1216 | -13562 | 12 / 2 | 10606 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| aA (lam/4, ban none) | A3403 | -8879 | 25 / 1 | 16082 | True | 1 proposals (0 interacting), then INFEASIBLE | - | ok 0 | no |
| b4913 (lam/4, ban none) | B1 | -4925 | 10 / 1 | 3761 | True | 2 proposals (2 interacting), then K reached | 3802 cand: 2 sol / 2 exact, K reached; 4301 cand: 0 sol / 0 exact, INFEASIBLE | infeasible , infeasible  | no |
| b4913 (lam/4, ban none) | B3 | -4925 | 10 / 1 | 3668 | True | 2 proposals (2 interacting), then K reached | 3709 cand: 1 sol / 1 exact, INFEASIBLE; 4205 cand: 0 sol / 0 exact, INFEASIBLE | infeasible  | no |
| b4913 (lam/4, ban none) | B8 | -4925 | 10 / 1 | 4201 | True | 2 proposals (2 interacting), then K reached | 4237 cand: 2 sol / 2 exact, K reached; 4756 cand: 2 sol / 2 exact, K reached | infeasible , infeasible , infeasible , infeasible  | no |
| b783-dup | [[['B', 783]]] | | | | | incomplete | | | |
| b802-dup | [[['B', 802]]] | | | | | incomplete | | | |
| b8857 (lam/4, ban none) | B1177 | -8879 | 15 / 1 | 5729 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| b8857 (lam/4, ban none) | B1178 | -8879 | 12 / 1 | 4397 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| b8857 (lam/4, ban none) | B1185 | -8879 | 15 / 1 | 5540 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| b8857 (lam/4, ban none) | B1186 | -8879 | 12 / 1 | 4285 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| bdiv (lam/2, ban none) | B783 | -6781 | 5 / 1 | 4500 | True | 1 proposals (1 interacting), then INFEASIBLE | 5022 cand: 0 sol / 0 exact, INFEASIBLE | - | no |
| bmix (lam/4, ban none) | B857 | -3059 | 4 / 1 | 1429 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| bmix (lam/4, ban none) | B875 | -3059 | 4 / 1 | 1353 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| bmix (lam/4, ban none) | B32 | -4925 | 10 / 1 | 3556 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| bmix (lam/4, ban none) | B36 | -4925 | 10 / 1 | 3569 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| bmix (lam/4, ban none) | B39 | -4925 | 10 / 1 | 3678 | True | 2 proposals (2 interacting), then K reached | 3714 cand: 2 sol / 2 exact, K reached; 4224 cand: 1 sol / 1 exact, INFEASIBLE | infeasible , infeasible , infeasible  | no |
| bmix (lam/4, ban none) | B44 | -4925 | 11 / 1 | 3902 | True | 2 proposals (2 interacting), then K reached | 3938 cand: 2 sol / 2 exact, K reached; 4438 cand: 2 sol / 2 exact, K reached | infeasible , infeasible , infeasible , infeasible  | no |
| diag783 (lam/4, ban none, no budget r2) | B783 | -6781 | 5 / 1 | 4500 | True | 1 proposals (1 interacting), then K reached | 5270 cand: 2 sol / 2 exact, K reached | infeasible , infeasible  | no |
| md (lam/2, ban none) | B875+B1186 | -12909 | 12 / 1 | 4387 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| md (lam/2, ban none) | B857+B1178 | -12909 | 12 / 1 | 4505 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| md (lam/2, ban none) | B783+B802 | -13562 | 8 / 2 | 8344 | True | 1 proposals (1 interacting), then INFEASIBLE | 9440 cand: 0 sol / 0 exact, INFEASIBLE | - | no |
| q4 (lam/4, ban none) | B783 | -6781 | 5 / 1 | 4500 | True | 1 proposals (1 interacting), then INFEASIBLE | 5022 cand: 0 sol / 0 exact, INFEASIBLE | - | no |
| q4 (lam/4, ban none) | B802 | -6781 | 5 / 1 | 4434 | True | 1 proposals (1 interacting), then INFEASIBLE | 4956 cand: 0 sol / 0 exact, INFEASIBLE | - | no |
| rk1 (lam/4, ban none) | B822 | -6118 | 14 / 1 | 33585 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| rk1 (lam/4, ban none) | B858 | -6118 | 14 / 1 | 33611 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| rk1 (lam/4, ban none) | B840 | -6118 | 14 / 1 | 33592 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| rk1 (lam/4, ban none) | B876 | -6118 | 14 / 1 | 33617 | True | 0 proposals (0 interacting), then INFEASIBLE | - | - | no |
| rk822-depth2-killed | [[['B', 822]], [['B', 858]]] | | | | | incomplete | | | |

## Lead 1: cone-cap aware second-order search (2026-10-15, about 01:15–01:45Z)

**Outcome: no feasible candidate, so no gain.** The filter rejects all 16 frame-infeasible words up front. Under the
filter every repair on the seven named targets is proven INFEASIBLE, so nothing reached pricing.

**The filter (`tools/cone.py`).** PR1186's `frames.Graph` is a nested-subspace lattice:
- lower frames join forward along register chains, and upper frames meet backward;
- the end-of-B cone cap meets the upper frame of a register's last B (or tail) vertex;
- both are monotone along the DAG.

So for one insert v (`x += c·y` before seq position p) into a feasible word W, this holds exactly:
`W + v feasible ⇔ L_a ∨ L_c ⊆ U_b ∧ U_d ∧ cap(x, if b is tail/end) ∧ cap(y, if d is tail/end)`.
- Here a, b are x's chain neighbours of p in W, and c, d are y's.
- When v becomes the last A vertex of x or y, the cut frame is also joined into the lower side.
- The reason: every downstream lower frame only gains L_v ⊆ U_v ⊆ U_b ⊆ U_k, and every upstream upper frame only meets
  U_v ⊇ L_v ⊇ L_k.

The test runs inside candidate generation, before an insert is admitted, using the round word's `Graph` lower/upper
arrays under the base caps. An exact final word has the base map, hence the base compensation and the base cones.
Every proposal word is then set-tested exactly: building a `Graph` must not raise Infeasible. A failure is cut by a
minimal conflicting subset (deletion filter). No set-test cut was ever needed.

**Calibration (`lead1/CALIBRATION.json`, `lead1/calib.log`, 5.8 s).** The earlier runs had 16 exact second-order words
that the exact pricer rejected as frame-infeasible. All 16 are rejected up front:
- 14 at a round-2 insert (B1 ×2, B3, B8 ×4, B39 ×3, B44 ×4); their round-1 words are feasible.
- 2 at round-1 inserts: B783's A63 side terms, whose round-1 word also fails the set test at A64.

The exact `Graph` confirms all 16 final words infeasible.

**Soundness (`lead1/soundness.txt`).** The filter makes no false rejections on known feasible inserts:
- all 5 inserts of the feasible k554 kernel pass on its deleted step0 word, including two `74 −= 554` writes into data
  register 74;
- all 7 re-insertions of the deleted reads at their own slots pass.

**Reruns (`lead1/runs/c1..c5`, `lead1/SUMMARY.json`).** Same limits as before: at most 12 inserts per round, quarter-step
λ (|λ| ≤ 4), PR1957 oracle cap and summed budget, single-threaded CP-SAT, 3 processes, timeout plus 6 GiB cap.

| Target | Cone-admitted candidates (before) | Cone-feasible round-1 proposals | Repairs | Then round 1 |
|---|---:|---:|---|---|
| B1 | 2,452 (3,761) | 2; 6 more without diversity cuts | 8 / 8 INFEASIBLE | INFEASIBLE (diversity cuts) |
| B3 | 2,390 (3,668) | 2 | 2 / 2 INFEASIBLE | INFEASIBLE |
| B8 | 2,407 (4,201) | 2 | 2 / 2 INFEASIBLE | INFEASIBLE |
| B39 | 2,394 (3,678) | 2 | 2 / 2 INFEASIBLE | INFEASIBLE |
| B44 | 3,017 (3,902) | 2 | 2 / 2 INFEASIBLE | INFEASIBLE |
| B783 | 4,120 (4,500) | 1; 6 more without diversity cuts | 7 / 7 INFEASIBLE | INFEASIBLE (diversity cuts) |
| B802 | 4,086 (4,434) | 1 | 1 / 1 INFEASIBLE | INFEASIBLE |

- **Per-target status: no feasible candidate.**
  - Every repair attempted is proven INFEASIBLE by CP-SAT, with interactions allowed.
  - Round-1 exhaustion is relative to the diversity cuts, which exclude every writer already tried, so it is a heuristic
    exhaustion and not a full proof.
  - Without the cuts (B783, B1, 6 proposals each), the enumeration only varies cosmetic side terms around the same
    interacting core, such as `648 ±2·506` windows. All 12 repairs are INFEASIBLE.
- **No exact candidate arose,** so nothing was priced, and there is no gain_certified, audit, κ or extra-word step to
  report.
  - The extra word shares the base word's gate sequence (agent A's `diffcheck.py`), so any future edit transfers
    unchanged and only needs re-pricing there.
- **Total runtime:** about 30 minutes of searches, peak RSS 0.6 GiB.

**Next step.** Under exact cones, the zero-cost interacting cores of these reads cannot be repaired within 12 inserts.
The remaining open directions are:
- a complete round-1 enumeration (no diversity cut, larger K) on one target, to turn the heuristic exhaustion into a
  proof within this model;
- three or more rounds;
- moving to the A/B families of other agents.
