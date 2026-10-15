# A-extra: helper-donor kernels on the extra word (round r3, 2026-10-15)

**Scoped negative result. No exact profitable kernel on the extra word in the searched families; no κ change.**
Pivot: #2143 handoff item 2 (#2142 searched only the base word). The extra word serves 417 of the 666 T74 calls.

## Inputs and tools
- Words (shared, read-only): `inputs/extra-word-566-554.json.gz` (sha256 cd417b90…) and `inputs/gauge44-word-566-554.json.gz` (eeb6a236…), = #1672 `new/*-word-566.json.gz`, used by #2044/#2161/#2180.
- Relaxations and relocations: our #1186 rev3 toolkit (c37dfb07, copied to `toolkit/`) at b = 0.001679754956125544.
- Model comparisons and CP-SAT: #1957's vendored #1186 toolkit at #1094's DEFAULT_B, exactly as #2142, so models are comparable with #2142's proofs.
- `scripts/sk2.py` = #2142 `skkernel.py` refactored into build/solve (validated: B783, B1, A1220 reproduce #2142's ddel, keys and candidate counts).
- `scripts/sk_multi.py` = new multi-deletion generalization (several deleted reads with distinct source keys); validated on B783 to reproduce #2142's single-deletion model exactly (same 3,922 candidates in order, same right-hand side).
- Python: agi venv (3.14.7, OR-Tools 9.15, NumPy 2.4.4); at most 3 worker processes; per-task deadlines (compat.deadline) and RSS checks; peak worker RSS ≈ 0.5 GiB.

## Results
1. **Word diff.** The two words have identical gates in A, cut, B, early cleanup and cleanup. Only 12 B gates (B397–B408) differ, in frames only, and `start_extra` of 627/629/630/631 lacks the 390 level (rank 4 instead of 5). The extra word's +8,458,352 units per call is 4 extra rank units (local rank mass 5,594 vs 5,590), fixed by the interface; no rewrite can recover it.
2. **B deletion relaxation, all 1,797 add gates on the extra word** (`out/relax-extra.json`, `out/RELAX-COMPARISON.json`): 1,002 deletions save cost, and every deletion's profile change equals #1957's base-word relaxation (1,797/1,797; the 40 gain classes pair one to one). The extra word has no new kernel-sized B deletion.
3. **A deletion relaxation, all 3,451 A gates on the extra word** (`out/relaxA-extra.json`): all 3,451 gates solve; 360 deletions save cost, and every deletion's profile change equals the base-word reference (#2142 `relaxation-A-rest.json` + #1957 `relaxation-A-sample.json`): 3,451/3,451. The gain classes are #2142's (−23,644 ×2, −20,893 ×62, −19,700 ×12, −19,690 ×16, −19,037 ×8, −16,631 ×8, −9,850 ×172, −8,879 ×48, −6,781 ×32 at the frontier b). No new kernel-sized A deletion on the extra word.
4. **#2142's 108 strict searches transfer exactly** (`out/diffcheck108.json`, `scripts/diffcheck.py`). For every job the deletion price is equal on both words, and the only registers whose deleted-word frame timeline differs are S = {624..631}. All 30,456,050 S-involving candidate costs are equal or exceed both caps. So the filtered candidate lists, budgets and equations coincide, and the CP-SAT model is identical. #2142's 104 infeasibility proofs and 4 shape-infeasibilities therefore hold on the extra word. ddel and key counts match #2142's RESULTS.json for all 108 jobs.
5. **The only word-dependent structure: the width-interface reader groups.** Readers 624/625/626/628 each read three of the pivots 627/629/630/631 at B397–B408, before the pivots' first writes at B1096–B1100 (`out/spivot-relax.json`).
   - Deleting one reader's three reads saves 11,938 units on the extra word (H2 −1, H3 −1, H5 +1) against 8,879 on the base word (H1 −1, H4 −1, H5 +1). All 12 reads: −47,752 vs −35,516.
   - Exact relocations (92 joint and single moves inside the commutation window, rev3 harness with interval certificates; `out/jointmove-extra.json`): 71 cost-neutral, 21 frame-infeasible, 0 gains.
   - Multi-deletion split-key searches (strict #2142 settings: ≤12 inserts, |λ| ≤ 4 in half steps, budget |gain| − 1, per-insert cap = budget, CP-SAT 300 s; `out/skm-extra/`): readers 624, 625, 626 and 628 (20–24 keys, 3,380–5,023 candidates) and all 12 reads (36 keys, 5,606 candidates): **all proven infeasible**.
   - Positive control / diagnostic (no summed budget, per-insert cap ×3; `out/skm-diag/`): for reader-624, reader-628 and all-12 the only exact compensation is relocating the deleted reads (to just before B1093 / B1097), with delta 0; after excluding it the model is infeasible. The obstruction is algebraic within the family, not a pricing artifact.

## Scope and limitations
- Searched: single-deletion split-key compensation (one key level, first order) on all 108 kernel-sized deletions; multi-deletion split-key compensation for the 5 width-interface read groups; 92 exact relocations of those reads; full A and B deletion relaxations.
- Not searched here: interacting inserts and recursive keys (agent B's lane), other multi-deletion groups, delivery reads and data butterflies (agent D), toolkit fusion/slot/exchange sweeps (agent C).
- The base-word versions of the multi-deletion searches were not run (base budgets are smaller: 8,879 per reader).
- Finite searches on fixed words, not a supplier lower bound.

## Next step
- The extra word is the base word up to the frames of S = {624..631}. A future kernel search only needs to run on one word plus `diffcheck.py`'s S-identity test for the other (seconds per job), which halves the cost of #2143-style searches.
- The cheapest remaining extra-specific test is a second key level restricted to the 12 width-interface reads (5 jobs, about 3 minutes each).

Evidence: `RESULTS.json` (summary), `out/` (raw), `scripts/` (tools). Runtime: about 65 minutes wall, at most 3 processes. Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
