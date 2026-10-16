# SKELETON of `new_research_styles.md` (Lane D proposal)

Working title: "Two research styles for the integer-mult-bounds words: L-system descriptions and chip-firing analysis. An evaluation plan."

## Proposed section outline

0. **Purpose, scope, non-claims.** No new kappa. kappa is asymptotic and galactic; value = theory + verification tooling. Research does not
   close; every null is protocol-specific. One paragraph on what a "pattern" is (CONTROLS.md section 3) so the reader can grade the document.
1. **The objects, in one page.** Local word (gate syntax, frames, ranks, sections, the two formats), helpers/lenders/followers, the owner fill
   (roles, windows, idle cells), the complete profile, the moment equation and its concavity, the lineage as a rewriting history.
   Pointers to files and to the proof notes (`PROOF.md`, `README.md` of #2802; `05-layers.tex`, `00-introduction.tex`).
2. **Data inventory and loaders.** = DATA-INVENTORY.md (frozen word set W, formats, blob ids, loaders, sizes, run times, held-out words).
3. **Style 1a: the local word as a string / L-system (Lane A).** 3.1 alphabets (gate class x coefficient class x role x rank delta; climb
   strings; per-section strings); 3.2 measures (LZ76, Re-Pair/Sequitur, block entropies, motif census, periods 9/8/112/73/480/666);
   3.3 which rewrite class could generate the word (D0L/DT0L/parametric/IL; the lineage edits as context-sensitive productions);
   3.4 patterns worth hunting (motifs predicting alias/refit feasibility; forward vs cleanup self-similarity - noting the cleanup is a
   deterministic inverse, so only the forward string is admissible text); 3.5 experiments A1-A6 with nulls, pass bars, costs.
4. **Style 1b: growth functions, Parikh vectors, the move algebra (Lane B).** 4.1 the moment equation as a growth-exponent equation
   (D0L growth matrices, Perron-Frobenius, multi-type branching, Akra-Bazzi) and what grows per rewriting step; 4.2 the move alphabet
   (alias, refit, hostee move, width cut, helper deletion, source recovery, cold-host merge, pre-life hosting) as productions with
   Parikh deltas and preconditions; 4.3 reachable cone, kappa landscape (concavity), ceilings (packing cap 0.00175037, class ceilings);
   4.4 the PR sequence as a derivation (commutation, saturation, gain per rule); 4.5 scoped negatives as unavailable productions;
   4.6 experiments B1-B5.
5. **Style 2: chip-firing / abelian sandpiles (Lane C).** 5.1 ranked mappings with exactness status: (1) owner fill on the window graph,
   (2) frame climbs as heights, (3) lender/follower aliasing as chip-firing on the lives-vs-registers bipartite graph (pigeonhole 74/72 as
   non-stabilisability), (4) butterfly recursion as a directed sandpile with sinks; 5.2 invariants to compute (stabilisation, avalanches,
   recurrent configurations, sandpile group, Dhar burning, identity) and which are trivial on a sink-DAG; 5.3 reusable local code
   (`_exp_sandpile_beyond.py` SNF/avalanche prototype; the sieve model; the fill relaxation as divisible sandpile); 5.4 experiments C1-C5.
6. **Controls, statistics, evaluation criteria.** = CONTROLS.md (nulls N0-N6, lane-specific nulls, permutation statistics, FDR,
   pattern criteria 1-5, stop rules).
7. **Compute plan.** 12 cores, pool caps, per-experiment budgets, the run-time table (DATA-INVENTORY.md section 6).
8. **Schedule (two weeks).** Milestones M0-M6 below.
9. **Deliverables.** Code (`styles/pipeline/`: loaders, string extraction, null generators, statistics harness, result schema), result
   tables per lane, the held-out predictions and their outcomes, the final document, and the memory digest entry.
10. **Feedback into the kappa work.** How a pattern becomes a lever: a prediction (which registers admit aliases / which frames are refittable
    / which window classes hold remainders / which Parikh moves are reachable) is handed to the exact pipeline (census -> build -> pinned
    auditor -> certified frames -> literal owner fill -> exact root) and only an exact result changes kappa. The styles never decide kappa.
11. **Risks, non-claims, stop rules.** Galactic; constructor artefacts; profile restatements; the cleanup-inverse trap; sink-DAG triviality;
    the fill is already near-optimal for fixed inventory (#2733 certificate), so fill-level patterns can only redistribute idle remainders.
12. **Open questions and round log.**
Appendices: A data inventory (full tables); B prior art (annotated, verification status marked); C scripts and result schema;
D the grounding numbers (LZ76/Re-Pair on #2802 vs section shuffle).

## Two-week schedule (10 working days; dates relative to kick-off K)

| day | milestone | work | deliverable | owner |
|---|---|---|---|---|
| K+1, K+2 | **M0 pipeline frozen** | freeze word set W (10 files, blob ids), `styles/pipeline/` loaders for both formats, string extraction (6 alphabets), null generators N0/N1/N1b/N1c/N2/N3, statistics harness with permutation p/FDR, pool with timeout + RSS cap, result schema; smoke test reproduces the grounding numbers (LZ76 302 vs 1846 on #2802 forward) | `pipeline/` + `SMOKE.json` | D (+A for alphabets) |
| K+3, K+4 | **M1 string screen** | pre-registered A1-A3: alphabets x statistics x W x {N1, N1b}, 2,000 permutations; motif census; period scan; FDR table; N5 cross-family split | `A-SCREEN.json`, table of surviving (alphabet, statistic) pairs with CR and q | A |
| K+5 | **M2 sandpile exactness audit** | decide exact vs heuristic for mappings (1)-(4); window-graph structure check (sink-DAG?); implement fill chip-firing + compare its stable configuration with the literal idle profile; N3 random fills (1,000); only then group/burning items | `C-EXACTNESS.md`, `C-FILL.json` | C |
| K+6, K+7 | **M3 growth / Parikh** | move alphabet with Parikh deltas and preconditions; reachable cone; kappa landscape and ceilings; the 2026-10 PR derivation re-played as rule applications (commutation and saturation checks); unavailable productions from the scoped negatives | `B-MOVES.json`, `B-CONE.md` | B |
| K+8 | **M4 predictions and held-out tests** | each surviving pattern -> one falsifiable prediction; fetch #2833/#2853 heads as data (`git fetch origin pull/N/head`, no code execution); run the exact checks (census/bounds/fill/root), <= 1 core-hour each; record pass/fail | `PREDICTIONS.json` | all, D runs the exact checks |
| K+9 | **M5 write-up** | fill sections 3-6 and 11-12 of `new_research_styles.md`; nulls written as protocol-specific; prior-art appendix with verification flags | draft document | D merges |
| K+10 | **M6 review and feedback decision** | coordinator review; decide whether any prediction is worth an exact kappa attempt in the next kappa round (it is handed over as a census target, not as a claim); memory digest entry; next-round questions | final document + digest | coordinator |

Budget: ~40 core-hours total (M1 ~6, M2 ~4, M3 ~2, M4 ~6, slack for reruns). Human time: ~1 day per milestone.

## How results feed back into the kappa work

- A **positive pattern** produces a census target (register set, gate set, window class or Parikh move) that the existing exact pipeline
  prices in the usual order: `census_r10.py` / pairs rules -> stage build (`alias_build`, `refit`, hostmove) -> pinned PR2679 auditor ->
  certified frames (`optimal_frames`) -> literal owner fill (`independent_owners.py`) -> exact root (`exact_moment.moment_bounds`) ->
  `full_replay.py`. Only this chain can change kappa; the styles only propose targets.
- A **null** is recorded with its protocol (alphabet, statistic, null, words, n) in the document and in the memory digest; it prunes the
  search space of later kappa rounds (e.g. "no motif predicts alias feasibility beyond the floor rule" would stop motif-driven alias hunts).
- The **Parikh/cone** result (Lane B) feeds the kappa rounds directly as a landscape: which mass-preserving moves have the largest
  marginal gain at the current profile (merging low ranks, filling idle 5-remainders), and which ceilings are provable from the move set.
- The **fill chip-firing** result (Lane C) feeds the owner-fill tooling: if stabilisation from a random configuration reproduces the
  relaxation optimum, a cheap fill heuristic exists; if not, the fill lever stays with the MILP.
