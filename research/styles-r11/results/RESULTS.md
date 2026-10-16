# r11 execution results

**Experiment execution and the language export are complete; the final hand-back push is pending.** This report indexes the preserved experiment receipts. It does not replace their exact profiles, rational certificates, null summaries, source hashes or error records. A PASS below means the stated registered test passed. It does not, by itself, establish a pattern under all five requirements of PLAN section 6. No finding in this round met all five requirements.

The run followed the M0 → M1 → M2 → M3 → M4 order. Lane A stopped after the confirmed L-2 and L-1 NULLs; Lane C stopped after the confirmed S-6 and S-2 NULLs. The unrun continuation families have EXPLORATORY/not-run receipts, rather than inferred negative results. Lane B continued under its separate registered scope. [EXPERIMENTS.json](../EXPERIMENTS.json) is the experiment registry; [M0](M0/PREREGISTRATION.json), [M1](M1/PREREGISTRATION.json), [M2](M2/PREREGISTRATION.json), [M3](M3/PREREGISTRATION.json) and [M4](M4/PREREGISTRATION.json) retain the frozen protocols and subsequent explicit amendments are linked below.

Unless specified otherwise, the confirmation seeds are **11031 and 29063**. Exact checks use zero permutations. Monte Carlo sample sizes below are per word/null/seed, not a pooled replacement for a second seed. Exact identities and descriptive calibrations have no discovery p-value. Where inferential tests were registered, the records retain the plus-one empirical p-value and the registered BH family. A stopped or incomplete family supplies no inferential decision.

## Source attribution and reproducibility

The original corpus contains **21 files: seven FULL-WORD and fourteen BORROW-WORD**, including multiple variants and control/intermediate files. They are not 21 independent constructions. The runbook's historical “12 files” language was expanded to every entry of the frozen [PINS.json](../data/words/PINS.json) in M0. Every receipt carries its enrolled PINS entries, compressed-file SHA256 values and Git blob identities.

| Source | Pinned files | Retained author attribution |
|---|---:|---|
| #1094 | 2 | Jeremy Kothe (jeremykothe2) |
| #1195 | 1 | Marius-Paul Dumitrean (mdumitrean) |
| #1625 | 2 | Marius-Paul Dumitrean (mdumitrean) |
| #1672 | 2 | Jeremy Kothe (LeverRank); on PR #1625 words; PR #1319/#1297 lineage (Rohan Arun) |
| #2462 positive controls | 2 | Jeremy Kothe (jeremykothe2) |
| #2679 | 2 | Philippe Van Velzen (philippeVV) |
| #2745 | 2 | Jeremy Kothe (jeremykothe2) |
| #2751 | 2 | Tekalign (tekuuu) |
| #2766 | 2 | DavidAriasC |
| retired5 intermediate of #2802 | 2 | Marius-Paul Dumitrean (mdumitrean); unpublished intermediate of #2802 |
| #2802 | 2 | Marius-Paul Dumitrean |

The **nine-word screen corpus** is #1094 K8S7, both #1672 variants, both #2745 variants, #2766 base, #2751 base, and both #2802 variants. The **held-fill corpus** is #2802, #2751 and #1672, with the credits above. The **lineage** is #2679 → #2745 → #2751 → #2766 → retired5 → #2802, with both base/extra variants where applicable. These labels identify the attribution scopes used in the individual sections.

The canonical extraction follows the attributed Lane A implementation. Lane B's simplified planning extraction has the documented convention offset; its printed `match=False` is not substituted for canonical parity. Word and fetched-content inputs are inert data read under isolated Python. Parallel executions use `pipeline/pool.py`, recorded prelaunch memory projections, task deadlines and per-worker limits. The retained resource audit below records the early CPU-budget overshoot and the later guard validation; it is not hidden by the successful attempts.

Source reproducibility has a historical limit: early P1/P2 receipts recorded SHA256 manifests before automatic source-byte archiving, and not every transient version can be recovered. [SOURCE-ARCHIVE-RECOVERY.json](M0/SOURCE-ARCHIVE-RECOVERY.json) identifies affected hashes and receipts; the authoritative later [SOURCE-ARCHIVE-UPDATE.json](M0/SOURCE-ARCHIVE-UPDATE.json) records 15 remaining unavailable versions and the exact recovery of old `word_tasks.py` version `f959c23f72dd6621adb32396e02059a3b66185f25ecbdaa6c4fb4db7d170e801`. Later runs preserve source bytes under `results/SOURCES/`. Recovery is accepted only when bytes match the original recorded SHA256. The partial archive must not be described as a complete replay archive for all historical attempts.

CPU values in the attempt tables are the recorded per-seed allocations, rounded to six decimals. The receipts retain full values, wall time, process RSS and checkpoint accounting. Shared preparation/overhead can be apportioned between seeds; parallel wall times must not be added as elapsed project time. Consolidated measured CPU and its exclusions are recorded in the final section.

## P-1 — Format parity and canonical climb extraction

**Verdict: PASS, v2, both seeds.** The bar is exact profile parity for every enrolled word, with each warp counted once. All 21 words passed in each seed. The independent BORROW loader and FULL toolkit recount agreed with the canonical paid profile; helper widths and centre-descents were checked under the documented count conventions. The six stored alphabets are `full`, `mid`, `rank`, `op`, `role` and `registers`. Forward A/cut/B streams include warp events; cleanup and compensation remain derived material.

The registered controls also cover N0, N1c equality under consistent relabelling, exact N1b linear-map preservation and N2 paid-profile invariants. There is no statistical discovery or permutation p-value. Source scope is the full original PINS corpus.

Version 1 is preserved as ERROR: its seven FULL tasks passed, while fourteen BORROW tasks called a module as a constructor. The correction to `W.Word(...)` was followed by a distinct v2 run; the erroneous receipts were not rewritten.

The `accelerator-v1` subrun was separately [preregistered](M0/ACCELERATOR-PREREGISTRATION.json). Every exact commute-predicate check and every seeded reference/accelerated N1b and N2 output/RNG equality passed on all 21 words in both seeds. This allowed the same distributions to be used more cheaply in P-2; it did not change the null or scientific bar.

The `cpu-limit-v1` subrun was a resource guard check, [registered in M2](M2/RESOURCE-VALIDATION-PREREGISTRATION.json). Both seeds raised the live-pool budget exception before any 30-CPU-second task finished. Measured CPU was 9.511211 and 9.663694 seconds, below the 15-second bar; completed-task lists were empty. These implementation controls are distinct from scientific word results.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [ERROR](P-1/v1/seed-11031/RESULT.json) | [ERROR](P-1/v1/seed-29063/RESULT.json) | 0 / 0 | 26.492640 / 26.166105 |
| v2 | [PASS](P-1/v2/seed-11031/RESULT.json) | [PASS](P-1/v2/seed-29063/RESULT.json) | 0 / 0 | 84.079887 / 84.542013 |
| accelerator-v1 | [PASS](P-1/accelerator-v1/seed-11031/RESULT.json) | [PASS](P-1/accelerator-v1/seed-29063/RESULT.json) | 0 / 0 | 124.947400 / 123.353578 |
| cpu-limit-v1 | [PASS](P-1/cpu-limit-v1/seed-11031/RESULT.json) | [PASS](P-1/cpu-limit-v1/seed-29063/RESULT.json) | 0 / 0 | 9.511211 / 9.663694 |

## P-2 — Null calibration

**Verdict: PASS for completed descriptive calibration, v2, both seeds.** The registered family is the nine-word screen corpus × four nulls × eight statistics on the `mid` alphabet: LZ76, RePair size and block entropies H1–H6. Each of the 36 word/null cells contains 2,000 samples per seed: **72,000 samples per seed, 144,000 in v2**. Means and population SDs are recorded for all 288 statistic cells per seed; discovery p/q fields remain null.

N1 shuffles within forward sections. N1b performs one randomized sweep of exact toolkit commuting-window moves, with the checked formal-warp extension. N1c consistently relabels helper registers within roles. N2 starts from shipped frames, proposes one seeded gate sweep and accepts only feasible changes preserving the exact paid profile. No mixing or uniformity claim is inferred from one sweep.

N1b had a larger SD than N1 in all 63 non-H1 word/statistic comparisons in each seed; H1 is invariant under these token permutations up to numerical rounding. Across the nine words, LZ76 SD ranged from 6.998604–7.342312 for N1 versus 8.475699–9.373760 for N1b in seed 11031, and 6.890144–7.420632 versus 8.622978–9.086791 in seed 29063. RePair SD ranges were 11.496541–11.936793 versus 14.338163–15.060678, and 11.387784–12.059795 versus 14.115745–15.158147. Full per-statistic values remain in the linked receipts.

All 18,000 N1c samples per seed had identical `mid` tokens to their source; relabelling-invariant statistics have zero mathematical variance, with at most machine-rounding residue in entropy summaries. N2 accepted 1,403,536 and 1,405,230 moves out of 21,298,000 proposals per seed, respectively. Both N1b and N2 reported zero invariant failures and zero degenerate samples. These are recorded movement diagnostics, not an equilibrium certificate.

Version 1 timed out: each seed retained 9,100 completed samples, with only 250–300 samples in each cell. Its recorded CPU was 7,839.134180 and 7,894.817833 seconds against a 7,200-second per-seed budget; ordered collection/termination overshoot was retained as a resource limitation. Those partial samples were not called scientific nulls. Version 2 followed exact accelerator verification and completed within that per-seed budget. Source scope is the nine-word screen corpus, with all credits retained above and in the receipts.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [TIMEOUT](P-2/v1/seed-11031/RESULT.json) | [TIMEOUT](P-2/v1/seed-29063/RESULT.json) | 250 / 250 | 7839.134180 / 7894.817833 |
| v2 | [PASS](P-2/v2/seed-11031/RESULT.json) | [PASS](P-2/v2/seed-29063/RESULT.json) | 2000 / 2000 | 6074.753552 / 6569.966475 |

## P-3 — Literal fill mapping and N3 control

**Verdict: EXPLORATORY, v2, both seeds.** The primary bar is exact equality. Literal role inventory, unique helper/call and family/call membership, eligibility, capacity, offsets, no overlap, compact occupancy and complete literal profile all passed for the three held fills. In #2802, the recorded idle multiset is exactly `{1:17316, 3:6594, 5:9878, 32:1, 48:26558}`.

The wider binding to held provider words remains qualified for #1672: inherited PLAN/PROFILE local metadata agrees with its literal OWNERS fill but differs from the separately held #1672 word profiles. Helper widths agree. Any held-word overlay is therefore separately labelled and does not silently replace literal accounting. This unresolved binding prevents a universal P-3 PASS; it does not invalidate the verified literal conservation identities.

The registered N3 control uses one conditional equal-width-slot max-flow pass, random groups of eight calls, exact eligibility and per-call family capacity. All literal fill rules passed for all three fills in both seeds. Occupancy and idle are conditioned on by this restricted control, so it cannot test clumping or represent an unrestricted random-fill distribution. It is not counted as a 2,000-sample inferential family.

Version 1 is an interrupted ERROR during preparation/control work, with no completed scientific tasks. Version 2 preserves the broader EXPLORATORY scope. The M2 literal/DAG audit below independently rechecks the exact conservation portion. Sources: #2802 (Marius-Paul Dumitrean), #2751 (Tekalign/tekuuu), and #1672 (Jeremy Kothe/LeverRank, with the #1625 and Rohan Arun lineage attribution).

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [ERROR](P-3/v1/seed-11031/RESULT.json) | [ERROR](P-3/v1/seed-29063/RESULT.json) | 0 / 0 | 1.270873 / 1.270873 |
| v2 | [EXPLORATORY](P-3/v2/seed-11031/RESULT.json) | [EXPLORATORY](P-3/v2/seed-29063/RESULT.json) | 0 / 0 | 26.286615 / 26.440324 |

## L-2 — Forward/cleanup production

**Verdict: NULL for the registered universal literal-equality protocol, both seeds.** The bar required exact equality on every word. All fourteen BORROW words satisfy the literal derived-production check; all seven FULL words fail that literal comparison. Both forward and dual arithmetic endpoint checks pass for all seven FULL words. The BORROW L2 tasks report exact literal production equality, without a separate endpoint-replay field. Refactored FULL cleanup uses the documented absorptions/buffers and is not the same literal inverse-word recipe.

This is a distinction between literal production equality and an equivalent arithmetic construction. It is not corrupted input, failed canonical profiles or a failed endpoint identity. The run used all 21 original pins and zero permutations. L-2 is the first confirmed Lane A scientific NULL.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [NULL](L-2/v1/seed-11031/RESULT.json) | [NULL](L-2/v1/seed-29063/RESULT.json) | 0 / 0 | 12.464069 / 12.675933 |

## L-6 — Log-rank law audit

**Verdict: PASS for the registered accuracy/order audit, both seeds.** Every held lineage step is within 2% of the fixed `lambda × delta Phi` estimate, and there are zero pairwise ordering disagreements across the ten complete profiles. The reference multiplier is `1.2421868570241867e-10` at #2802. Cross-geometry comparison retains the declared normalization `Phi × 66304 / W`, with W=14336 for T16 and W=66304 for T74; raw ordering also has zero disagreements in this held set.

| Lineage step | Recorded exact root difference | Law estimate | Relative error |
|---|---:|---:|---:|
| #2679 → #2745 | 1.2838853030081541e-6 | 1.2815029989040966e-6 | 0.185554% |
| #2745 → #2751 | 1.0011603509848219e-6 | 9.974419701102882e-7 | 0.371407% |
| #2751 → #2766 | 1.1538711857597016e-7 | 1.1468763991430133e-7 | 0.606202% |
| #2766 → retired5 | 1.5234286848933518e-7 | 1.5401344801984570e-7 | 1.096592% |
| retired5 → #2802 | 3.8566778314302038e-7 | 3.8362762870910881e-7 | 0.528993% |

The numerical root evaluator uses the exact recorded profile; “exact root difference” is the receipt's label for direct high-precision root evaluation, not a transcendental interval proof. The registered control draws 2,000 uniform-with-replacement feasible exact-L1 two-rank exchanges per lineage step/seed on ranks 1–51. Those controls calibrate the approximation and do not assert reachable word edits or FDR discoveries. Phi is a function of the complete profile, so the non-circular pattern requirement is explicitly false. Source scope is the attributed held lineage plus the complete-profile corpus identified in the receipts. The additional #2733 complete profile is attributed there to Marius-Paul Dumitrean (composition + frame refit), with its held CLAIM path retained.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [PASS](L-6/v1/seed-11031/RESULT.json) | [PASS](L-6/v1/seed-29063/RESULT.json) | 2000 / 2000 | 16.558789 / 16.548108 |

## L-7 — Derivation decomposition and Parikh ledger

**Verdict: EXPLORATORY, both seeds.** The registered bar requires every lineage step to decompose exactly into the move alphabet, with noncommuting pairs identified. All five complete-profile deltas and both variants' local register sums reconcile exactly; idle differences are kept separate from local differences. That bookkeeping does not discharge every guarded-production obligation.

The two early transitions, #2679 → #2745 and #2745 → #2751, lack a validated decomposition into the registered move alphabet. The receipts retain their available source recipes and explicit obligations. The #2751 → #2766 frame refit and seven named stages leading through retired5 to #2802 have recorded local guards, register changes and independent endpoint audits. [The L7 review](L-7/v1/REVIEW.json) preserves the distinction between payload differences and genuine prefix-guard evidence; the later L7-GUARD-ORDER experiment below supplies the narrower local-order check.

Each seed also checks 2,000 independent destination-helper relabellings per variant against the fixed, source-pinned sequence: zero matched the pinned effect. Coherent relabelling preserves it. The `1/2001` diagnostic is scoped to that named sequence, not to every possible derivation. The ledger retains local/idle deltas, scalar L-6 references and source attribution; it is not a complete consumed/created predicate ledger for all moves. Sources are all six named lineage stages and their authors in the attribution table.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [EXPLORATORY](L-7/v1/seed-11031/RESULT.json) | [EXPLORATORY](L-7/v1/seed-29063/RESULT.json) | 2000 / 2000 | 59.888248 / 59.818367 |

## S-1 — Hall-deficiency atlas

**Verdict: EXPLORATORY, both seeds.** Exact matching/Hall/Koenig certificates and verification of every current alias edge passed for all 21 pinned words. Each word/seed has 2,000 registered floor/first-time permutation controls. The universal bar additionally required coverage of every realised lineage alias/hostee change; the unresolved early transitions prevent that stronger PASS.

| Word group | Current aliases | Maximum matching | Recorded path statement |
|---|---:|---:|---|
| Seven FULL words | 0 | 24 | Explicit augmenting path |
| #2679, #2745, #2751, #2766, both variants | 65 | 72 | Explicit augmenting path |
| retired5, both variants | 70 | 72 | Explicit augmenting path |
| #2802, both variants | 72 | 72 | No augmenting path |
| #2462 positive controls, both variants | 50 | 60 | Explicit augmenting path |

The atlas records one shortest augmenting witness per unmatched follower; that is not an exhaustive census of all paths. Exact individual floor/time compatibility does not prove a constructive simultaneous refit or price its Phi. The #2751-to-#2802 staged alias witnesses pass, while earlier held alias/hostee changes remain outside that proof. Matching certificates are not an intrinsic sandpile burning operator. Source scope is the complete original PINS corpus.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [EXPLORATORY](S-1/v1/seed-11031/RESULT.json) | [EXPLORATORY](S-1/v1/seed-29063/RESULT.json) | 2000 / 2000 | 233.098898 / 233.795046 |

## S-6 — Max-flow tightness map

**Verdict: NULL under the registered contiguous-interval/divisible-cell protocol, both seeds.** The bar required zero-slack binding intervals and evidence that enlarging a binding helper forces a rank-1 idle child. The #2802 capacity relaxation sends all **2,219,112** demanded cells through capacity **3,580,416**. Of **222,111** nonempty contiguous call intervals, none is binding or violated. Minimum slack is **18,172**, at interval `[665,665]`, with demand 3,332 and neighbourhood capacity 21,504.

The endpoint-jitter null independently perturbs endpoints by −1, 0 or +1 with the registered clamping/validity rule. Both 2,000-sample runs completed. Central 99% intervals are `[2044,32508]` and `[2044,34300]`; empirical p-values are 0.5547226387 and 0.5687156422. One and four sampled flows, respectively, are infeasible. The observed minimum slack is inside both intervals.

This relaxation drops indivisible-role/family restrictions and examines contiguous call sets. The recorded promotion examples are different whole-call edits and do not establish the forced-rank-1 implication. The evaluated zero-slack premise already fails. This is the first confirmed Lane C scientific NULL. Source: #2802, Marius-Paul Dumitrean, with the pinned fill/template/plan hashes in both receipts.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [NULL](S-6/v1/seed-11031/RESULT.json) | [NULL](S-6/v1/seed-29063/RESULT.json) | 2000 / 2000 | 38.267542 / 38.319826 |

## L-1 — Shared skeleton grammar

**Verdict: NULL for the fixed capped-RePair search, both seeds.** The original bar is one shared rule set of at most 200 rules, exact regeneration of at least three skeletons and at least 90% pairwise overlap of transitively used rules. The preregistration tests every one of the **84 triples** from the nine-word screen corpus separately, rather than requiring a grammar for all nine words together.

All **168 triple tasks** completed. Every fit reached **201 rules**, failing the rule-count bar. Every one of the **252 skeleton replays per seed** was exact. Rule-use overlap ranged from 0.13930348258706468 to 1.0. Saved overlap/replay/hash evidence agreed across seeds. Axiom lengths of 5,054–5,451 and residual literals of 5,013–5,435 were anti-memorization diagnostics, not additional numerical pass criteria. No permutation inference was run.

The result does not disprove other grammars or a parametric D0L construction. It says the registered capped algorithm found no qualifying triple. The preceding L-2 NULL and this L-1 NULL trigger the binding Lane A stop in [STOP.json](M1/STOP.json). [The independent review](M1/REVIEW-SUMMARY.md) checked coverage, criteria, second-seed equality, source identities and stop receipts. Sources are the nine-word screen corpus with the exact credits listed above.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [NULL](L-1/v1/seed-11031/RESULT.json) | [NULL](L-1/v1/seed-29063/RESULT.json) | 0 / 0 | 167.493003 / 166.904018 |

## L-3 — Periodicity census and the continuation string screen

**Verdict: EXPLORATORY / not run after the Lane A stop.** The original periodicity bar was a named-parameter lag peak at least five N1b standard deviations above its null, subject to the plan's multiple-testing and pattern requirements. The frozen continuation specifies the 540-cell core screen and a separate 864-cell lag family: six alphabets × nine words × eight lags × N1/N1b, 2,000 samples per cell/seed and BH at 5% within that complete lag family. Named periods are 9, 8, 22, 112, 73, 480, 666 and 1,332; the lag statistic uses within-A/B pairs only.

The template-program census is a descriptive component with literal/opcode projections and no p/q. Neither that census nor the inferential continuation was executed. Both stop receipts have zero permutations and no inferential result. The planned source scope is the nine-word screen corpus plus the attributed #2802 template. No periodicity or compression NULL follows from this skipped family.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| stopped | [EXPLORATORY](L-3/stopped/seed-11031/RESULT.json) | [EXPLORATORY](L-3/stopped/seed-29063/RESULT.json) | 0 / 0 | 0.000000 / 0.000000 |

## L-4 — Climb-string predictability

**Verdict: EXPLORATORY / not run after the Lane A stop.** The original bar is at least 90% exact held-out-word prediction versus at most 50% under its null. The frozen features are role, entrance dimension, width and first/last motif with paid climb fields removed to avoid target leakage; leave-one-PR-out sensitivity was specified. The nine-word screen corpus and its PINS authors remain the planned scope.

No predictor fit, held-out accuracy or null was run. Both stop receipts record zero permutations. This is not evidence that the proposed feature set succeeds or fails.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| stopped | [EXPLORATORY](L-4/stopped/seed-11031/RESULT.json) | [EXPLORATORY](L-4/stopped/seed-29063/RESULT.json) | 0 / 0 | 0.000000 / 0.000000 |

## L-5 — Alias-feasibility motif

**Verdict: EXPLORATORY / not run after the Lane A stop.** The original bar requires held-out AUC at least 0.9 and the two realised moves `401→564` and `403→565` among the top five of the 192 paths beyond the floor rule. The continuation protocol separates deterministic guard-feasibility labels from actual realised-move outcomes: guard labels already give the floor baseline AUC=1, and unselected paths cannot be relabelled as failed moves. A beyond-floor AUC increment therefore needs additional outcome labels.

The registered nonleaking motif ranking and tie handling were left unexecuted. No AUC, top-five score or path census was generated after the stop. Planned sources are the S-1 atlas and attributed #2802 lineage/pre-host data. Both receipts retain zero permutations and the stop reason.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| stopped | [EXPLORATORY](L-5/stopped/seed-11031/RESULT.json) | [EXPLORATORY](L-5/stopped/seed-29063/RESULT.json) | 0 / 0 | 0.000000 / 0.000000 |

## M2-AUDIT — Literal fill and eligibility-DAG exactness

**Verdict: PASS, both seeds.** This exact audit rechecks the three held fills under the unchanged literal interpretation. Every fill has **666 calls, 1,332 windows, 112 ports/window and 149,184 bins**. Both seeds verify complete inventories, the exact `start < call <= stop` guard, per-call family uniqueness, valid offsets, no overlap, compact occupied prefixes, literal full-profile parity and global rank mass **4,816,512**.

| Fill | Roles | Capacity cells | Used cells | Idle cells | Empty-or-full bin fraction |
|---|---:|---:|---:|---:|---:|
| #2802 | 271,728 | 3,580,416 | 2,219,112 | 1,361,304 | 0.7735145860 |
| #2751 | 276,390 | 3,580,416 | 2,242,422 | 1,337,994 | 0.8047645860 |
| #1672 | 319,680 | 3,580,416 | 2,488,512 | 1,091,904 | 1.0000000000 |

Eligibility arcs increase the lexicographic order `(call time,0) → (window stop,1)`, giving a sink DAG. Each graph has 1,998 vertices; #2802/#2751 have 206,202 arcs and #1672 has 243,522. This proves the stated directed incidence/conservation structure. It supplies no intrinsic Laplacian, chip threshold or toppling operator. Group, identity and intrinsic sandpile stabilization claims remain dropped.

The literal empty/full fractions are geometric measurements, not an S-4 walk result. The #1672 metadata qualification in P-3 remains unchanged. [C-EXACTNESS.md](M2/C-EXACTNESS.md), [C-FILL.json](M2/C-FILL.json) and [REVIEW.json](M2/REVIEW.json) preserve the detailed independent review. Source scope is the three held fills and their credited authors.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [PASS](M2-AUDIT/v1/seed-11031/RESULT.json) | [PASS](M2-AUDIT/v1/seed-29063/RESULT.json) | 0 / 0 | 4.724664 / 4.724664 |

## S-2 — Greedy frame-lowering confluence/optimality check

**Verdict: NULL for the registered strict-lowering-from-U protocol, both seeds.** The bar is at least 95 reference-profile hits out of 100 orders. The primary words are #2802 base/extra; #2751 base is the predeclared replication. Every word/seed cell completed all 100 orders: **600 orders total**.

All cells had **0/100 reference hits and 100/100 rigorously worse maximal terminals**. Each word reached one terminal assignment, also identical across seeds. Thus the observation is failure of greedy optimality; it does not show order dependence or multiple sampled terminals. Every legal lowering was nested and strictly true-cost decreasing under rational cost bounds; exhaustive terminal sweeps had zero unresolved signs.

The terminal lower bound exceeds a feasible reference's upper bound by approximately `9.0267420337e-7` for each #2802 variant and `9.0282068255e-7` for #2751 base. These are per-call toolkit cost differences, including its declared fallback term, not kappa differences. The reference establishes integer-surrogate optimality and a true-cost interval; it does not certify a unique exact true-cost optimum profile. A feasible strictly cheaper reference is sufficient for the negative decision.

The independent [M2 review](M2/REVIEW.json) checked all 600 checkpoints, rational sums/inequalities, profile mass, seed identities and source hashes without rerunning dynamics. Neutral moves, larger blocks and other starts were not tested. Together with S-6, this is the second consecutive Lane C scientific NULL and triggers [STOP.json](M2/STOP.json). Sources: #2802 (Marius-Paul Dumitrean) and #2751 (Tekalign/tekuuu), retaining the attributed toolkit cost implementation.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [NULL](S-2/v1/seed-11031/RESULT.json) | [NULL](S-2/v1/seed-29063/RESULT.json) | 100 / 100 | 67.322632 / 67.322632 |

## S-4 — Fill-energy walk slopes

**Verdict: EXPLORATORY / not run after the Lane C stop.** The original bar required slope within 10% of prediction on every fill and clumping at least 0.75. Literal clumping was recorded by M2-AUDIT, but no walk, slope estimate or slope-null family was executed. P-3's N3 control conditions on occupancy and cannot substitute for that test.

Both stop receipts have zero permutations. Planned sources are the three held fills and their PINS attributions. The exact conservation audit does not make this unrun energy claim pass or fail.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| stopped | [EXPLORATORY](S-4/stopped/seed-11031/RESULT.json) | [EXPLORATORY](S-4/stopped/seed-29063/RESULT.json) | 0 / 0 | 0.000000 / 0.000000 |

## S-5 — Order-independent repair

**Verdict: EXPLORATORY / not run after the Lane C stop.** The original bars were at least 95% identical terminals for the abelian claim, or repair within `1e-8` kappa of exact re-hosting in at least 90% for the stated useful surrogate. No repair-order experiment or kappa comparison was executed.

Both stop receipts have zero permutations. The existence of implementation/protocol material is not the stopping reason; the binding S-6/S-2 stop is. Planned source scope remains the attributed held-fill/hosting corpus, with no untested order-independence conclusion.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| stopped | [EXPLORATORY](S-5/stopped/seed-11031/RESULT.json) | [EXPLORATORY](S-5/stopped/seed-29063/RESULT.json) | 0 / 0 | 0.000000 / 0.000000 |

## L7-GUARD-ORDER — Named local-order follow-up

**Verdict: PASS for the finite guarded-order obligation, both seeds.** The bar requires exact reconstruction of original named successors in both variants and classification of all registered swaps by actual current-prefix guards without unexplained auditor rejection. It tests six adjacent pairs × two variants. Each variant has **three inadmissible swapped sequences and three pairs admissible in both orders with the same payload**. Original local rebuilds all pass; unexplained auditor rejections are zero.

Rejected orders stop before commitment. The evidence uses named frame refits, alias/hostee operations and their actual intermediate predicates, rather than whole-section patch overwrite or payload inequality alone. The [guard-order review](M3/GUARD-ORDER-REVIEW.json) retains the finite classifications. The two early L-7 decomposition obligations remain unresolved. This is not a claim that all productions commute, that no alternative derivation exists, or that the value of a fixed algebraic Parikh sum depends on order. Sources are the attributed #2751-to-#2802 lineage and held local recipes.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [PASS](L7-GUARD-ORDER/v1/seed-11031/RESULT.json) | [PASS](L7-GUARD-ORDER/v1/seed-29063/RESULT.json) | 0 / 0 | 41.191223 / 41.191223 |

## L-8 — Conditional class ceilings

**Verdict: PASS for the stated class certificates, v3, both seeds.** The protocol enumerates all **1,163** unordered feasible width patterns across physical bin capacities, including empty bins, and solves one fractional-pattern LP per held fill/seed. It fixes the local paid profile, total role-width inventory and capacity multiplicities, while relaxing eligibility and distinct-family restrictions. Float LP solutions are proposals only: each accepted ceiling has an independently checked rational dual over every column, using outward-bounded rank costs. A violation must change one of the stated class assumptions.

| Fixed inventory/profile scope | Held-fill control root, rounded | Certified upper ceiling |
|---|---:|---:|
| #2802 literal providers | 0.001717794984118635 | 0.001717795812 |
| #2751 literal providers | 0.001717141586348426 | 0.001717142414 |
| #1672 explicit held-word overlay, unchanged widths | 0.001679754956125545 | 0.001679754958 |

The #1672 row is explicitly overlaid: the inherited literal root `0.001679671795504738` remains separately recorded. It is not silently equated with the #1672 PINS claim or with P-3's inherited profile. All three stated control profiles lie below their ceilings.

For #2802's fixed local profile, the fractional-rank-51 comparator has rationally certified bracket `[0.001758085933, 0.001758085936]`; the numerical integral-rank-48 comparator root is approximately `0.001747404385077211`. The integral profile uses one remainder child, not that many rank-1 children. The #2802 LP upper is strictly below the certified rank-51 lower endpoint. The helper-removal envelope checks k=`0,1,2,4,8,16,32,64,128,256,408`; its certified upper endpoints range from `0.001758085936` at k=0 to `0.004097539104` at k=408. It removes ascending helper strings only and keeps all other paid children, including actual centre descents, fixed. It asserts no feasible deletion construction.

All attempts remain visible. Version 1 raised a conservation assertion because helper-paid strings included centre-descents beyond physical hosting width. [Amendment 1](M3/AMENDMENT-1.json) separated ascending width from fixed nonascending payments, retained the error and charged its six solver calls to the same budget. Version 2 produced EXPLORATORY: #1672's underdetermined positive-column least-squares dual proposal was too weak, although the exact repair was valid. [Amendment 2](M3/AMENDMENT-2.json) added the original LP equality marginals as a second proposal at the same target exponents, with no solver in the target/permutation loops and no loosened certificate test. Version 3 verified all certificates. Across the three attempts there are 18 LP calls and no budget extension. The independent [L8 certificate review](M3/L8-CERTIFICATE-REVIEW.json) checked 12 saved dual candidates against 13,956 inequalities, four comparator brackets, 22 envelope points and 408 helper identities using retained evidence only.

The bar proves conditional ceilings, not exact primal optima. Their dependence on fixed profiles/inventories fails the non-circular pattern criterion. They are class certificates and possible census context, not a kappa improvement. Sources are the three held fills and their full retained author/lineage credits. [B-CONE.md](M3/B-CONE.md) and [B-MOVES.json](M3/B-MOVES.json) consolidate the Lane B evidence and its remaining obligations.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [ERROR](L-8/v1/seed-11031/RESULT.json) | [ERROR](L-8/v1/seed-29063/RESULT.json) | 0 / 0 | 16.195509 / 16.195509 |
| v2 | [EXPLORATORY](L-8/v2/seed-11031/RESULT.json) | [EXPLORATORY](L-8/v2/seed-29063/RESULT.json) | 0 / 0 | 18.913977 / 18.913977 |
| v3 | [PASS](L-8/v3/seed-11031/RESULT.json) | [PASS](L-8/v3/seed-29063/RESULT.json) | 0 / 0 | 11.302173 / 11.302173 |

## L-9 — Saturation census

**Verdict: EXPLORATORY for the complete requested production census, both seeds.** On the exact #2802 base word, the recorded direct-alias necessary time/dimension class has **zero pairs**, and the registered follower → occupied slot → current hosted life → free slot class has **zero length-three paths**. Empty necessary-guard supersets exclude those precisely scoped classes on that pinned word.

The 2,000 independent uniform life/slot pair controls per seed have feasible fractions **0.097** and **0.0955** (194 and 191 samples), with SDs 0.2959577673 and 0.2939043212. The anticipated zero baseline was not imposed on observed data. No p-value is claimed for this descriptive control.

Constructive simultaneous hostee-refit Phi, restorable width cuts and kernel-identity classes remain explicit validation obligations. The fixed-order optimum control concerns the toolkit's stated integer cost surrogate and does not automatically optimize a global root. No positive Phi is inferred from necessary guards. The original bar sought an empty class a later PR could violate; the finite alias certificate is retained for conditional prediction, while the full census remains incomplete. Source: #2802 base, Marius-Paul Dumitrean; no transfer to an unexamined variant is assumed.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [EXPLORATORY](L-9/v1/seed-11031/RESULT.json) | [EXPLORATORY](L-9/v1/seed-29063/RESULT.json) | 2000 / 2000 | 1.171981 / 1.171981 |

## L-10 / S-3 — Partition extremality and merge calibration

**Verdict: NULL for the registered every-word conjunction, both seeds.** The fixed nine-word family compares each helper's ascending partition with 2,000 independent uniform ordered positive compositions of the same physical width and part count. Actual nonascending helper payments are held fixed and included exactly once. The statistic is paid moment at the fixed #2802 reference kappa, lower being better. The bar requires the real statistic below at least 99% of null samples on every word and a supported merge margin within 1%.

The three FULL words (#1094 K8S7 and both #1672 variants) beat all 2,000 null samples in both seeds: p=`1/2001`, BH q=`0.0014992503748125937` across the nine-word moment family. All six BORROW words fail the 99% condition: each observed moment is strictly above the maximum of its nondegenerate null distribution in both seeds. The reported fraction of null samples above real is 0 and p=q=1; these are not ties. The every-word bar therefore fails. This is a conditional composition-null result, not a claim about arbitrary feasible word changes.

The supported #2751 → #2766 `(1,1)→2` merge calibration has exact recorded profile delta `{1:-1332, 2:666}`, `profile_identity=true`, predicted and observed root differences both `1.1538711857597016e-7`, and relative error zero. That one successful calibration does not rescue the failed conjunction or imply additional realised margins. Total Phi/moment is profile determined, so a non-circular structural pattern is not claimed. Sources are the nine-word screen corpus with their full PINS credits. Only Lane B's L-10 executed. Lane C's S-3 remained `not_run` under its binding stop; the [S3 bookkeeping record](L-10/v1/S3-BOOKKEEPING.json) supplies a descriptive cross-reference to L-10, with no second experiment or separate NULL.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [NULL](L-10/v1/seed-11031/RESULT.json) | [NULL](L-10/v1/seed-29063/RESULT.json) | 2000 / 2000 | 2.955644 / 2.955644 |

## L-11 — Multi-type check

**Verdict: PASS for the dispatched-local-profile prediction, both seeds.** All **666** registered local calls were present. There is **one distinct local paid profile**, `{1:2382, 2:648, 3:268, 4:128, 5:26, 8:8}`. Each of the nine stage/orientation groups contains 74 calls with that profile. The required count and profile-list consistency checks pass.

The test supports the identical-local-profile prediction on the #2802 dispatch. Stage labels and varying idle allocations do not establish inherited recursive child types, and a multi-type growth matrix was not inferred from them. No recursive type-inheritance theorem follows from this exact inventory check. Source: the #2802 base/extra providers and dispatch, attributed to Marius-Paul Dumitrean, with all nine input-source hashes retained.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [PASS](L-11/v1/seed-11031/RESULT.json) | [PASS](L-11/v1/seed-29063/RESULT.json) | 0 / 0 | 2.682107 / 2.682107 |

## L6-COST-N6 — Conditional local cheap-score calibration

**Verdict: PASS for the registered primary full-moment approximation, both seeds.** The fixed set contains **152 primary local-profile rows and 33 descriptive companions**. Each uses the conditional equation `M_after(k*) = M_before(k0)`, where `M_p(k)=sum p_r (r/73)^(1-k)` and k0 is the held #2802 reference. Direct numerical roots use 90-digit arithmetic and 280 iterations, without a root cache. These are local sensitivity diagnostics; no global or idle profile is invented.

For all 152 primary rows, the full-moment estimate agrees in sign and is within the 2% bar. Maximum relative error is **0.0002434593622408322**, or approximately **0.024346%**. There are zero ordering disagreements among 11,476 primary pairs. The 33 companions have the same maximum relative error and zero disagreements among 528 pairs. Pairwise ordering and companion results are descriptive controls.

Mass-corrected Phi also agrees in sign on this set, with maximum relative error 0.0002600214984674378. Plain Phi omits the nonzero local mass change: it disagrees in sign on all 152 primary rows and all 33 companions, with maximum relative error 1.0067681934864223. The primary PASS must not be generalized to that cheaper uncorrected score.

Mean recorded CPU per conditional root is about 37.46/37.48 ms across the two seeds; full-moment dot evaluation is about 1.812/1.810 microseconds per call, measured with 1,024 repetitions. Coefficient setup took 50.134/50.165 ms; per-row derivative/target setup had median cost 9.888/9.938 microseconds, respectively. These are microbenchmarks of individual evaluations on this machine and profile set, not an end-to-end speedup; setup is separate from the dot-evaluation timings. Full/idle near-miss profiles are absent, overwritten hyperplane word paths are not independent row witnesses, retained audit labels are source data, and the Decimal brackets are numerical rather than rational interval certificates. No global construction exponent or non-circular pattern is claimed. The receipts retain the 12 supporting lineage PINS entries and source-manifest credit for every near-miss table.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [PASS](L6-COST-N6/v1/seed-11031/RESULT.json) | [PASS](L6-COST-N6/v1/seed-29063/RESULT.json) | 0 / 0 | 8.663495 / 8.663495 |

## M4-PRED — Held-out predictions

**Verdict: EXPLORATORY overall, with all three registered bookkeeping predictions PASS in both seeds.** The [frozen prediction snapshot](M4/PREDICTIONS-FROZEN.json) and [preregistration](M4/PREREGISTRATION.json) preceded acquisition of the held-out files. They explicitly recorded **zero eligible structural patterns** and fixed the overall EXPLORATORY outcome even if every diagnostic passed. The plan already summarized these PRs' kernel changes and approximate margins from a prior comment sweep, so this is arithmetic transfer evidence, not blind structural discovery. [PREDICTIONS.json](PREDICTIONS.json) now contains the unchanged predictions, outcomes and second-seed confirmations. There were zero permutations, zero solver calls and no discovery p/q values.

The four held words are the base/extra variants of #2833, credited to **Jeremy Kothe (`jeremykothe2`)**, and #2853, credited to **Philippe Van Velzen (`philippeVV`)**. The selected commits are `e9307b48d7d1b690939935ecef0f8e524e6d92f4` and `d01045dfb67428679618027dff552f1d032fa999`. The two [data](../data/heldout/2833/DATA-MANIFEST.json) [manifests](../data/heldout/2853/DATA-MANIFEST.json) retain all 40 acquired file identities, SHA256 values and source paths; the receipts retain the four word blob IDs and complete source metadata alongside the original PINS attribution. Fetched content was read as inert data under isolated Python; no fetched code or auditor was imported or executed.

**D1-fixed-lambda: PASS.** The frozen #2802 multiplier predicts each consecutive complete-profile margin with matching sign and at most 2% relative error. All three numerical complete-profile roots and Phi values have the same pairwise ordering, with zero disagreements.

| Consecutive edge | Direct numerical root difference | Frozen-lambda prediction | Relative error |
|---|---:|---:|---:|
| #2802 → #2833 | 8.624530482212919e-7 | 8.599231432123059e-7 | 0.293338% |
| #2833 → #2853 | 7.202215307307034e-7 | 7.206103762730013e-7 | 0.053990% |

The reconstructed complete-profile roots are approximately `0.001718657437166856` for #2833 and `0.001719377658697587` for #2853. They use the registered uncached 90-digit, 280-step bisection after exact profile/rank-mass validation. Their Decimal brackets are numerical, not transcendental interval certificates. The numbers agree with the corresponding recorded outer-ledger headline roots; this numerical agreement does not validate the outer theorem or the distinct supplier-only claim.

**D2-scalar-profile: PASS.** Each package has exactly **666 actually dispatched calls**, including overrides, and one canonical local paid profile across all stage/orientation/provider groups. #2833 has `{1:2382, 2:650, 3:266, 4:128, 5:26, 8:8}`; #2853 has `{1:2402, 2:638, 3:266, 4:128, 5:26, 8:8}`. The profiles differ between packages, as permitted by the within-package prediction. This result does not infer recursive child-type inheritance from stage labels.

**D3-fixed-class-exit: PASS.** Both packages change the #2802 aggregate local paid profile **and** global role-width inventory. Dimension 73, 666 calls, 66,304 wires, rank mass 4,816,512 and physical capacity counts remain the same. Exact rational rank-cost enclosures place each held-out profile's moment strictly below 66,304 at the frozen #2802 ceiling `0.001717795812`, certifying that its root lies above that ceiling. The predicted conditional class implication is therefore satisfied through the changed local profile/inventory. Changes only to eligibility or family rules would not evade that ceiling, since those restrictions were already relaxed.

Both package adapters verify canonical paid/width parity, ordered provider binding, dispatch coverage, literal helper/family uniqueness, capacity, disjointness, exact `(start,stop]` eligibility and local-plus-idle reconstruction. Their scope is the literal owner fill, canonical profiles and fixed-gate Bounds. Native admission and the outer theorem were not replayed; this round introduces no construction or kappa claim.

The independent [M4 records review](M4/REVIEW.json) passed 212 checks on the forty data files, frozen source snapshots, receipt equality, saved integer/rational arithmetic, zero-child witnesses and attribution. It reran no extraction, fill audit, solver or prediction experiment. [C-HELDOUT-SCOPE.md](M4/C-HELDOUT-SCOPE.md) records the precise validation limits.

Version 1 is preserved as ERROR in both seeds, before prediction evaluation. Its adapter incorrectly required terminal children 18/19, whose level transition is 8→8, in the positive idle inventory. [Amendment 1](M4/AMENDMENT-1.json) and the frozen [v2 implementation](M4/IMPLEMENTATION-v2.json) apply the exact increment `8 × (to_level − from_level)`: positive increments must match bins/windows/roles, and exact-zero children must be absent from all three. They retain the original commits, predictions, thresholds, seeds and CPU budget. Version 2 passes the exact validation and all three diagnostics. Recorded experiment CPU totals are **6.898166526 seconds for v1** and **12.096953742 seconds for v2**.

| Attempt | Seed 11031 | Seed 29063 | Recorded n, 11031 / 29063 | CPU seconds, 11031 / 29063 |
|---|---|---|---:|---:|
| v1 | [ERROR](M4-PRED/v1/seed-11031/RESULT.json) | [ERROR](M4-PRED/v1/seed-29063/RESULT.json) | 0 / 0 | 3.449791 / 3.448376 |
| v2 | [EXPLORATORY](M4-PRED/v2/seed-11031/RESULT.json) | [EXPLORATORY](M4-PRED/v2/seed-29063/RESULT.json) | 0 / 0 | 6.061093 / 6.035861 |

## M5/M6 — Artifact and hand-back completion

The [language index](LANGUAGE/INDEX.json) now covers all **21 original pinned words × four immutable outputs = 84 per-word artifacts**: six-alphabet section strings, complete climb strings, a Parikh-ledger index and a move-census index. Every output preserves PINS attribution and hashed input references. The exporter formats previously recorded evidence; it ran no new experiment or census. Missing early guards, complete consumed/created predicate inventories, constructive Phi and cuts remain explicitly EXPLORATORY/unavailable. Non-lineage words are not assigned invented derivations, and L9 evidence is attached only to its exact attributed word.

The experiment registry has **23 completed entries** including explicit not-run decisions, and the preflight covered **62 immutable RESULT.json receipts** plus **40 held-out data files**. [PREDICTIONS.json](PREDICTIONS.json) contains confirmed outcomes. The [final audit](FINAL-AUDIT.json) records the integrity/accounting checks; the [hand-back](HANDBACK.md) records passed checks, protocol-specific nulls, census targets and open questions. Proposed levers remain census targets, without a new price or claim.

Measured experiment CPU is **30,347.771030474 seconds = 8.429936397354 core-hours**, including retained errors/timeouts and registered implementation controls. The additional M3 rational certificate review used **7.273402129 CPU seconds**. Other orchestration/review time is excluded; native CPU from the aborted P-3 worker is unavailable and must not be treated as zero. Recorded process RSS figures are per-process peaks, not measured machine-wide peak memory. Before the final document writes, `results/` occupied **68,226,719 bytes** (about 68.3 MB), below the 200 MB bound; the final audit retains the completed artifact accounting.

The hand-back destination is the fork branch `research/styles-r11-results`. The final commit is pushed there after integrity review; Git history and the remote branch identify the delivered revision. Nothing is posted as a PR, comment or discussion; the coordinator reviews the pushed branch first.
