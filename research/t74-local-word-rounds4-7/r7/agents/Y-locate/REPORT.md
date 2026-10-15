# r7 / Y-locate: where the frozen searches behind the k8 chain live

Agent Y-locate, round r7 (2026-10-15). Read-only inspection of canonical main (`r3/main`, 0fdd7d82, history included) and
of PR heads fetched into separate refs (`refs/ylocate/prN` in the local clone; nothing checked out, nothing run from them).
One bounded reproduction run of main's PR987 slot search (copied into `src/u10disc/`, hard-coded `/tmp` paths redirected).
Nothing committed, pushed or posted.

## Per-search status

| Frozen output (consumer) | Produced by | Code location | Status |
|---|---|---|---|
| K-triangle read schedule `data/TRI-SCHEDULE.json` (factory packet programs; `construct_k_triangle.py` / `construct_gauge_xcentre.py`) | AtomScout, a Claude Code agent (PR622, jeremykothe2; credited in `complex-571-cold14-k492/NOTICE.md:29`) | none: PR622's head (merged as-is, `f69477f4`) has only the constructor and `data/search/` owner-LP inputs | **missing** |
| LeaverSAT all-K mutable-leaver cells (`CODED-CELLS-k8.json`, `cells-k8/`) | LeaverSAT (PR1004/PR1005, jeremykothe2) | none in PR1004 `1974578f` / PR1005 `779e80ae` heads (merged as-is) or main; builder `reproduce_leaver.py` only | **missing**; re-implementable: the cell is a 21-gate circuit, main has a scoped 21-addition optimality proof (`leaver-monotone-optimality-seed21`), a 720-labelling atlas (`leaver-relabel-atlas-seed81`), and the predecessor all-K cell's z3 event model (`complex-packet-borrowing23/search_events.py`, PR781; needs `z3-solver`, not installed here) |
| LeaverSAT layer re-indexing and frozen k8 layer recipes (`COLD-LAYERS-RECIPE-NP/P6N-k8`, `HPE-RECIPE-k8`, `PIVOT-SWAP-k8`) | LeaverSAT (re-indexing of NP/p6n recipes) | builders + recipes only (`reproduce_leaver_chain.py`); the mapping is documented in `PROOF-NOTE-LEAVER.md` §2 | **missing as code**; the HPE step is greedy and re-derivable |
| NP layer cold ends (`COLD-LAYERS-RECIPE-NP`, BlockCombine) and p6n ends (`COLD-LAYERS-RECIPE-P6N`, NoTriReopen) | PR655 / PR659 / PR676 (jeremykothe2) | PR heads `3e669dc7`, `4982f0ca`, `18649d6b` (not merged as-is) contain only `reproduce_*`, `layer_end_controls.py`, builders; recipes applied by PR635's `build_cold_end.apply` | **missing** |
| Entrance promotions `PROMO-RECIPE-*` (BlockInvert's CP-SAT: `prom.py` + `exactframe2.py`, MinCutSel) | PR664 / PR676 / PR699 | heads have `build_promotion.py`, `promo_controls.py`, `reproduce_promo.py`; `make_recipe.py` converts a CP-SAT solution; the model code is absent everywhere | **missing** |
| U8 triangle-hybrid slots `RECIPE-U8*` (NewBArch) | PR869 (jeremykothe2, merged as-is `73e86f69`) | builder `barch/build_tri.py` + `run_controls.py` only | **missing**, but superseded: PR987's slot search generalises the same triangle-hybrid delivery |
| PR987 slot search (U10 slots; and the five k8 slots X = 236/238/434/436/439 of `RECIPE-SLOTS-k8.json`) | PR987 (rohanarun), rerun on the k8 word by PR1018 | **main: `research/complex-u10-t37/construction/u10/discovery/`** (`search2.py`, `slot.py`, `mover.py`, `frameopt.py`, `compose.py`, `make_recipe.py`; 517 lines, standard library; hard-coded `/tmp/don`, `/tmp/bar/audit_local.py`) | **available and runnable; reproduces** (below) |
| LeaverSAT2 frame re-optimisation (`FRAME-RECIPE-LV-k8`, "gopt2") | LeaverSAT2 | builder `build_frames_lv.py` only | **missing as code**; replaceable: our #1186 toolkit computes certified exact optimal frames |
| PR1148 eight-ends / three-demotions / joint-entrances | PR1148 (tomdif) | vendored `discovery/search_*.py` (HiGHS / LP / IPM) in the PR1148 packages | **available**; not run here; its logs show 180 s solver limits, so exact re-derivation is not guaranteed |
| #1297 kernels / #1672 k554 | PR1297 / PR1672 | #1297 `search_relations.py` vendored; #1672 EDITS only, but #2142's `skkernel.py` rediscovers k554 (its positive control) | available / reproducible |
| T74 owner map | PR1319 | `reconstruct.py` moves only width-4/5 roles; no general exact-fill constructor | **missing** (r6 C-hosting built a one-helper min-change map) |

## Reproduction run (PR987 slot search on the k8 ancestor)
`scripts/slot_repro.py` runs search2.py's own loop (same candidate enumeration, `build`, `optimise`, `profile` and fee
at b = 0.001665, m = 73) on the k8 ancestor word `db2c7cfb...` (r7 T's reproduction, `T-generator/out/lvc/frames/`),
restricted to the copy gates whose slot X is one of the five slots PR1018 says came from re-running #987's search on k8.

| X | E | delta (search fee units) | donations (H <- src) | in `RECIPE-SLOTS-k8.json` |
|---:|---:|---:|---|---|
| 236 | 454 | -0.50696 | 556<-454, 544<-236 | yes |
| 238 | 455 | -0.50696 | 557<-455, 545<-238 | yes |
| 439 | 584 | -0.50696 | 74<-584, 10<-439 | yes |
| 434 | 585 | -0.50696 | 383<-585, 287<-434 | yes |
| 436 | 587 | -0.50696 | 351<-587, 319<-436 | yes |

Each slot changes the profile by H3+2, H4-4, H5+2, exactly one seventh of the recipe's seven-slot change from
{3:418, 4:170, 5:68} to {3:432, 4:142, 5:82} (seven-slot delta -3.5487 = 7 x -0.50696). About 31 s per slot (3 exact
evaluations each), 157 s in total, one process, peak RSS 44 MB. The only edits to the code were the two hard-coded `/tmp`
paths; the audit_local call inside search2.py was not exercised (the driver only prices).

## Feasibility and cost of the factory-redesign chain
Available today: the factory itself and its first stages (r7 U: port stages, regroup, HPE, cold44 in 2.4 s per variant),
PR987's slot search (verified above, minutes per slot class), PR1148's three searches (HiGHS/LP, solver-time-limited),
#1297's relation search, #2142's kernel search, our #1186 toolkit for every frame re-optimisation, and the strict T74
replay (about 13 min) and outer (hours at 1e-60000).

Missing and needing re-implementation, in chain order: (1) AtomScout's K-triangle read-schedule search (a new packet
program needs it; no description of its model beyond the frozen schedule); (2) LeaverSAT's cell search (small: a
21-gate circuit, with the optimality proof, relabel atlas and PR781's z3 event model as starting points); (3) LeaverSAT's
k8 re-indexing of the NP/p6n/HPE/swap recipes (documented mapping, mostly mechanical); (4) BlockCombine's NP and
NoTriReopen's p6n cold-end searches; (5) BlockInvert's promotion CP-SAT; (6) a general exact-fill T74 owner constructor.
Each re-implemented search would also have to match or beat its frozen output on the redesigned word.

Estimate: one to two weeks of focused work, dominated by (1), (4), (5) and (6), with no guarantee that the
re-derived chain ends cheaper than today's words; the bounded payoff is about +8.4e-8 kappa per narrowed width-9 helper
(r6 C-hosting), only if r7 U's packet obstruction is also solved by the new packet program.

## Evidence
`out/PR*-files.txt` (files each lineage PR changed versus its merge-base with main), `out/SLOT-REPRO.json` / `.log`,
`scripts/slot_repro.py`, `src/u10disc/` (main's PR987 discovery code, paths redirected). Prepared with substantial AI
assistance (Anthropic Claude, via Claude Code).
