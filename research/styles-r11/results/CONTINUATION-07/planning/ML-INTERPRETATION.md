**The 12-release comparison finds recognizable structural families, but the conservative word-gain regression has only three eligible, related releases and performs worse than its baseline. A different-mechanism test is unidentifiable, and the frozen model overpredicts the separately acquired PR3015 gain by 5.25 times. The clearest cost-bearing evidence is the published same-frame joint-lowering interaction in PR2979. No construction, admission or κ improvement was produced by this analysis.**

This note interprets immutable ML1, ML2 and ML3 receipts only. It does not rerun feature extraction, fit another model, change a threshold, or promote a pattern. ML2 v1 completed with both seeds agreeing on the observed analysis: 48 provider-feature receipts, two feature-control receipts, two model-control receipts, two observed analyses, and 398 independent permutation tasks. Its recorded verdict is `EXPLORATORY`, confirmed, using 348.700065799 CPU seconds and 19.465195183 wall seconds with 61 workers. A frozen coverage correction then produced ML2 v2 with the same 452-task layout: confirmed `EXPLORATORY`, 338.890547171 CPU seconds and 19.337215371 wall seconds. All v1 receipts remain intact. The historical auxiliary ML1 is also confirmed `EXPLORATORY`. ML3 completed eight tasks with both seeds agreeing, using 21.060529403 CPU seconds and 6.243064492 wall seconds; its verdict is also `EXPLORATORY`.

The [paired release cohort](RELEASE-COHORT.json) contains 12 authenticated, source-reported complete conditional releases, each with before/after words for both providers and an allocation pair. All 12 passed the registered word/profile and descriptive graph/grammar checks. They belong to the same broad PR2833 ancestry. Native and outer admission were not independently replayed in this round; the κ labels remain the authenticated sources' conditional claims.

The label is the exact difference between the release and the complete κ claim attached to its **actual structural parent**. It is not a copied `CLAIM.gain` against a different comparator. In particular, rows sharing a parent are alternatives or descendants of that parent, not consecutive increments that may be summed. Both providers are averaged into one release observation, so the model has 12 descriptive observations, not 24 independent samples.

The table below transcribes saved feature and allocation receipts. Gains are rounded for readability; exact rationals and source hashes remain in the cohort. A/B/R are changes in literal scalar-event counts in A, B and restore. Frame/end columns count changed frames on matched gates and changed endpoint registers. These entries agree between the base and extra providers for the quantities shown. The graph columns are changes in vertices, register-chain arcs and cycle nullity of the exact warp-split inclusion graph. They are **not** measured physical sandpile topplings. Allocation moves count changed owner/child/port triples for matched `(call, helper)` roles when the same literal scale/order permits that comparison; offsets are separate.

| Release ← structural parent | Source-reported Δκ | Δ A/B/R | Frame/end edits | Allocation comparison | Δ graph V/E/cycle |
|---|---:|---:|---:|---|---:|
| #2857 ← #2833 | 1.43919e−6 | +20/0/0 | 0/0 | Normalization metadata incomplete; not aligned | +20/+40/+20 |
| #2863 ← #2857 | 4.17673e−9 | 0/0/0 | 0/0 | Scale changes; role sets not compared | 0/0/0 |
| #2875 ← #2863 | 7.07561e−27 | 0/0/0 | 0/0 | Identical fill; precision-only release | 0/0/0 |
| #2894 ← #2863 | 8.37230e−8 | +14/0/0 | 2/0 | Scale changes; role sets not compared | +14/+28/+14 |
| #2908 ← #2894 | 2.13809e−7 | +24/0/+3 | 0/1 | 1,104 moved roles | +27/+53/+26 |
| #2917 ← #2908 | 1.19031e−6 | +192/0/+27 | 13/9 | 103,059 moved roles | +219/+426/+207 |
| #2930 ← #2917 | 9.11259e−7 | 0/0/0 | 0/0 | 270,971 moved roles | 0/0/0 |
| #2942 ← #2930 | 3.16413e−7 | +122/0/+41 | 10/4 | 270,975 moved roles | +163/+320/+157 |
| #2948 ← #2930 | 8.56581e−7 | +33/−2/+4 | 0/0 | Identical fill | +35/+70/+35 |
| #2957 ← #2930 | 1.21751e−6 | +33/−2/+4 | 5/0 | Identical fill | +35/+70/+35 |
| #2966 ← #2942 | 1.21795e−6 | +44/−2/+4 | 5/0 | Identical fill | +46/+92/+46 |
| #2979 ← #2942 | 6.21766e−6 | +172/−2/+45 | 144/27 | 271,357 moved roles | +215/+423/+208 |

The table already prevents two misleading generalizations. Pure allocation gains can occur with no word-graph change (#2863 and #2930), and a numerical-certificate refinement can increase the stated bound while both words and allocation remain identical (#2875). All nine word-changing releases in this cohort **increase** total scalar-event count, by 14 to 219, and increase operation-stream LZ76 complexity, by 1 to 59. Thus scalar-word shortening was not the observed success signal in these released examples. This is a descriptive fact about the acquired positive cohort, not a statistical law or an instruction to lengthen words. Paid climb distributions and allocation changes still determine the relevant costs.

The allocation audit checked supported literal role, ordered-width, compact-prefix and disjoint-cell facts. It did not replay the complete template/plan geometry, chronology, physical-family or capacity admission. A moved-role count therefore describes the archived allocation difference; it does not certify that alteration independently. Pairs with changed scale or incomplete normalization metadata were explicitly left incomparable rather than silently folded or relabelled. In particular, #2857 is T37 to T37 with missing live-family normalization metadata; the saved comparison does not establish a scale change.

**What entered the regression.** The model used 73 structural delta/edit features: rank-free operation/role stream measures, scalar and role counts, finite graph descriptors, and literal frame/endpoint edit counts. Paid profiles, width inventories, moments, prices, roots, author/PR identities and reported outcomes were excluded. Canonical climb strings and their costs were retained only as audit/descriptive output. No unmatched failed scalar-edit proposal was turned into a negative release label.

The final conservative coverage correction, **ML2 v2**, requires literal allocation-role mapping, order, dispatch and normalization to remain unchanged before attributing a whole-release κ gain to word/frame covariates. Only **#2948, #2957 and #2966** remain eligible. They are all in the same declared gate-rewrite family. The source grouping has two groups, one of which leaves only one training observation; mechanism-held-out validation has no second group and is explicitly `UNIDENTIFIABLE_GROUPING`.

| Final v2 held-out grouping | Training-mean baseline MSE | Ridge MSE | Baseline MSE − ridge MSE | Interpretation |
|---|---:|---:|---:|---|
| Immediate structural source, n=3 | 0.0097402171 | 0.1053822688 | −0.0956420516 | Ridge is worse than the baseline |
| Declared mechanism, n=3 | — | — | — | One family; no independent mechanism test |

The v2 source-group shuffle fractions are 104/200 and 98/200. They remain descriptive only. The nine regression-censored releases are #2857/#2894 (mixed declared word/allocation changes), #2863/#2930 (allocation-only), #2875 (precision-only), and #2908/#2917/#2942/#2979 (word-changing releases with changed literal allocations). All 12 remain in the valid paired descriptive analysis and PCA. A high rank correlation in a three-row table with tied predictions is not evidence against the substantially worse squared prediction error.

**The separate PR3015 check also fails the fixed accuracy criterion.** The [additional source cohort](HOLDOUT-3015-COHORT-v2.json) compares Jeremy Kothe's PR3015 with its actual parent PR2979, using the unchanged literal fill, order and dispatch. Its outcome and edit were known before registration. ML3 therefore is an **unblinded, related-ancestry diagnostic**, not a prospective or PLAN section 6 held-out pattern test. It fitted the frozen alpha-1 ridge only to #2948/#2957/#2966; #3015 never entered fitting, scaling or tuning.

The exact source-reported matched gain is `58495443855455489/500000000000000000000000`, or `1.16990887710910978e−7`. The frozen model and baseline gave:

| PR3015 diagnostic | Predicted log10 gain | Prediction / actual gain | Within fixed factor two | Squared log error |
|---|---:|---:|---|---:|
| Ridge trained on three releases | −6.2120741257 | 5.2453423409 | No | 0.5180743779 |
| Training-mean baseline | −5.9653764027 | 9.2570276499 | No | 0.9340672781 |
| Actual source-reported gain | −6.9318479636 | 1 | — | — |

The ridge error is smaller than this baseline's error on this one known positive, but it still misses the preregistered factor-two range. Together with v2's worse grouped prediction error and single eligible mechanism, this gives no reliable quantitative gain predictor. Both seeds reproduce the same prediction; reproducibility does not establish accuracy or independent generalization.

The saved PR3015 features provide a concrete cost explanation that the generic grammar descriptors miss: it adds **one scalar event**, leaves LZ76 unchanged, changes one register's paid climb chain, and has zero moved allocation roles or offsets. Its exact local paid-profile delta is **`H2 − 2 H1`**, with unchanged rank mass. The related fixed-allocation #2957 and #2966 releases have local delta **`−4 H1 − 4 H2 − 4 H3 + 6 H4`** while their scalar words also grow. Here `Hr` denotes one paid rank-r child, not a graph vertex. These are source-bound paid-profile facts, excluded from the predictor to avoid giving it the cost outcome. They direct interpretation toward the distribution of charged recursive children and legal frame changes, while leaving full supplier/native/outer validity at the authenticated sources' conditional scope. No fresh admission of PR3015 was performed here.

**Preserved v1 mixed-coverage diagnostic.** The original rule admitted seven rows: #2908, #2917, #2942, #2948, #2957, #2966 and #2979. It already censored the first five mixed/allocation/precision scopes listed above, but its `mechanism_complete` flag only meant that the declared primary scope was word/frame-related. It did not demonstrate that allocation effects were observed. The saved table shows the defect: four of those seven rows also repack. These v1 regression numbers are preserved below as a partial-coverage diagnostic, not the final covered gain model.

The target was `log10` of the exact positive matched-parent κ difference. Ridge used fixed alpha 1 with an unpenalized intercept, training-fold means/scales and training-constant feature removal. There was no hyperparameter search. Four immediate-source groups and four declared-mechanism groups were evaluated separately. The latter grouped #2948, #2957, #2966 and #2979 together to withhold the shared gate-rewrite family and its joint descendants. That fold trains on only three releases, which makes the small-sample limitation concrete.

| Held-out grouping | Training-mean baseline MSE | Ridge MSE | Baseline MSE − ridge MSE | Gain-order Spearman |
|---|---:|---:|---:|---:|
| Immediate structural source | 0.2898564792 | 0.1380918079 | +0.1517646713 | +0.75 |
| Declared mechanism | 0.3876949582 | 0.4027161001 | −0.0150211419 | −0.178571 |

Errors are squared log10-gain errors, not κ units. The v1 source-held-out error is numerically lower than its baseline, but mixed, unmodeled allocation changes make it unsuitable as evidence for a covered word-gain predictor. Even before that coverage correction, the mechanism-held-out result did not beat the baseline or preserve gain ordering. The conservative v2 result above removes that ambiguity and is negative for predictive error, with no identifiable mechanism split. There is no valid classifier of success versus failure or independent-lineage validation here.

The v1 199 label permutations per seed gave source-group add-one fractions **5/200 and 2/200**, and mechanism-group fractions **34/200 and 26/200**. These are the registered descriptive shuffle calibrations. Exchangeability is not established for selected, related releases, and the preregistration prohibits a significance or pattern promotion from these values regardless of size. Both observed fits were exactly repeated; the two independent shuffle samples were intentionally different.

The preserved v1 coefficient stability also limits interpretation. The maximum-chain-length coefficient ranged from −0.02789 to +0.02305 across source folds, changing sign. The role-stream RePair-rule coefficient ranged from −0.03296 to +0.00948 across mechanism folds, also changing sign. Matched-gate frame edits had positive coefficients in all these folds, but ranged from 0.00540 to 0.04610 in the mechanism split. Graph arcs, vertices, branch/merge counts, cycle nullity and event counts are strongly coupled descriptors of the same construction size; their positive fitted coefficients do not independently identify several causal effects. A recommendation to add graph cycles, increase grammar size, or edit more frames would therefore be unsupported.

**Descriptive structure.** PCA on the 12 complete structural vectors explained 73.5838% of their variance on the first axis and 14.7950% on the second. These percentages describe feature variance, not variance in κ gain. The first axis largely tracks inserted scalar events and correlated graph/stream size; the second distinguishes B-gate/deletion and vocabulary/grammar changes. Fixed three-cluster Ward grouping produced:

- #2857, #2863, #2875, #2894, #2908, #2930: zero or relatively small word changes, mixing several distinct allocation/precision/extraction mechanisms.
- #2917, #2942, #2979: larger paired-extraction/endpoint-changing constructions.
- #2948, #2957, #2966: the related declared gate-rewrite releases.

#2863, #2875 and #2930 have zero distance in this structural feature space despite representing different gain mechanisms. That is a coverage limitation, not evidence that their physics or numerical effects are identical. Shared binary grammars replayed their finite token streams exactly, but no iterative generative L-system was inferred. The incidence Smith factors are units by the oriented-graph incidence theorem; a reference Laplacian nullity or cycle count does not establish an intrinsic physical toppling law, a critical group or cost confluence.

**The sharper historical lesson is shared local cost.** ML1 read PR2979's existing `STAGE-PRICES.json`, not a new experiment on those subsets. It collapsed 59 source occurrences into 54 distinct requested assignments. The five same-W contrasts below are exact arithmetic in the source's integer surrogate at `b=0.001703676387993676`. Its break-even guide is 2,091,300 units per freed width unit, and `margin = −delta − k·break_even`. These are not exact global-moment or per-subset κ labels.

| Source group and helpers | Sum of singleton margins | Joint margin | Joint − singleton sum |
|---|---:|---:|---:|
| V45: 249,251,265,267 | −212,564 | +22,972 | **+235,536** |
| A: 331,450,451,508,509 | −137,313 | +42,541 | **+179,854** |
| B: 299,448,449,484,485 | −132,317 | +42,541 | **+174,858** |
| C: 452,453,532,533 | −65,263 | +17,170 | **+82,433** |
| D: 454,455,556,557 | −65,263 | +17,170 | **+82,433** |

The linear break-even charge cancels exactly in every interaction: `m(S)−Σm({h}) = Σdelta({h})−delta(S)`. The positive contrasts therefore are not an artifact of subtracting the per-helper guide. All 15 stored cross-W unions, in contrast, have zero additivity residual. In the original restore-contact graph, V45 has two shared external carriers and one selected component; A/B have three shared carriers and one component; C/D have two shared carriers and two components. These are pre-price contact descriptors, not optimized-frame features.

All 15 nonempty V45 subsets are present. Their margins by cardinality are −53,141, −27,770, −2,399 and +22,972, respectively. Equivalently, this finite price table satisfies `m(k)=25,371k−78,512` for `k=1,2,3,4`. It exhibits a shared setup charge and explains why pricing isolated members can miss a favorable whole group. The missing per-single optimized frame assignments prevent attributing the entire 78,512-unit charge to a particular literal gate or proving a unique physical explanation from the table alone.

**The V45 fixed-parent packing question is now closed by a later source audit.** The [final checkpoint](../../../data/continuation-07/final-checkpoint/REVIEW.json) records Petalas's PR3014 at head `16e8db5656b4fea487a2212395f39707bf134f7a`: all 16 endpoint subsets lose after charging PR2942's original owner bins and actual remaining capacities, even granting free compaction within those bins. Its reported full joint delta is `1038 H1 + 6807 H2 + 3996 H3 − 6660 H4`, with equal rank mass and a strictly worse complete recursive moment in the stated positive-saving domain. The report distinguishes this fixed assignment from PR2979's changed final packing. We read this as pinned source metadata, not a new replay of that proof. The positive local surrogate interaction above remains historical evidence for cost sharing, but **is neither a V45 κ gain nor a candidate to retest under the original owner assignment**. No further V45 subset sweep is proposed.

The same source reports that Stage2 extraction choices become favorable after Stage1, while its parent-only comparison had no positive normal; the five realized Stage2 steps have total guide margin 66,903. The 14 Jeremy Kothe rewrites in Stage3 have composed integer price change −52,350, exactly the sum of their listed individual deltas. These two observations separate genuinely state-dependent opportunities from additive composition. They retain source-reported surrogate scope and are not additional independent release observations.

The useful future question is consequently narrower than “does compression or graph nullity predict κ?”: for a **fresh, legal production on a fresh source**, can a shared restore/interface cost be paid once across a connected same-frame group, and does that group unlock an extraction that its members do not? That question needs explicit guards, complete local-plus-idle pricing and admission, and must respect the existing lowering/extraction fixed-point results and the now-closed V45 frozen-owner obstruction. A fresh question must change the justified production or complete allocation premise; widening the closed subset sweep does not do that. This retrospective report does not authorize a repeat sweep or promote a candidate. Cross-W independence in this source also gives a concrete control against assuming synergy merely because two individual transformations can be combined.

Source attribution is preserved in the [cohort](RELEASE-COHORT.json), [historical source ledger](HISTORICAL-SOURCES.json), the full paired-feature receipt, and the original [word pins](../../../data/words/PINS.json). Release authors include Lyy-iiis (#2857), Dugongue (#2863), digitalis-p (#2875), Jeremy Kothe/jeremykothe2 (#2894/#2948/#2957/#2966), Jeremy Diviney/jeremydiviney (#2908), Mason Hale/mason-hale (#2917), and Marius-Paul Dumitrean/mdumitrean (#2930/#2942/#2979), with inherited credits retained verbatim in those sources. PR2979's historical Stage3 explicitly attributes the rewrite family to Jeremy Kothe's PR2957. The separate PR3015 restore edit is also credited to Jeremy Kothe/jeremykothe2; its [cohort](HOLDOUT-3015-COHORT-v2.json) preserves all predecessor and original PINS credits.

The report's principal immutable evidence includes the [ML3 RUN](../ML3-OUT-OF-COHORT/v1/RUN.json), its [frozen prediction](../ML3-OUT-OF-COHORT/v1/predictions/task-00000.json.gz) and [paired features](../ML3-OUT-OF-COHORT/v1/RELEASE-FEATURES.json.gz), the final [ML2 v2 RUN](../ML2-RELEASE-COMPARISON/v2/RUN.json), the final [v2 features](../ML2-RELEASE-COMPARISON/v2/RELEASE-FEATURES.json.gz), and preserved [ML2 v1 RUN](../ML2-RELEASE-COMPARISON/v1/RUN.json), [paired release features](../ML2-RELEASE-COMPARISON/v1/RELEASE-FEATURES.json.gz), [observed analysis](../ML2-RELEASE-COMPARISON/v1/observed/task-00000.json.gz), and the [first](../ML1-HISTORICAL-CONTROLS/v1/history/task-00000.json.gz) and [second](../ML1-HISTORICAL-CONTROLS/v1/history/task-00001.json.gz) historical confirmation receipts. Their SHA256 bindings are:

| Artifact | SHA256 |
|---|---|
| RELEASE-COHORT.json | `3969d32d59be02b88059da8a6e16c21606eb7fadd7c3982c2feda90fe5a4636f` |
| ML2 v1 RUN.json | `50d169cc0f3ccd4fde24bdd4926730a817dacd0a728d133e1497be11bb082b98` |
| ML2 v1 RELEASE-FEATURES.json.gz | `c75b86ac5f86c0dac9a2fbb561fa46b04c57e887066a6e98cb89a75c289875bc` |
| ML2 v1 observed/task-00000.json.gz | `d67e6604c460986014c10b105ec54f80731a7bcff0a5c8ca9e4319f5e23a629a` |
| ML1 history/task-00000.json.gz | `886fd7e7b6640bcc9bf4fd38b33f3daf0e6ee6b6bc2c81d3da7ea844ef9e9404` |
| ML1 history/task-00001.json.gz | `f953d9a134a897cd7bf5031d4b5a0a4c1a097ba8b81dc251d5034da6ecad7b31` |
| ML2 v2 RUN.json | `637e26deeab6d068719ff446c33bceb564d5bbf4130d674ae20f45c2e9a32db8` |
| ML2 v2 RELEASE-FEATURES.json.gz | `6287a9eca573df54a6ce50ba3d2f23d919a3e8ad383a2ba2e16bfe71af1b33e6` |
| ML2 v2 observed/task-00000.json.gz | `25f85277fff83c11597706554539ab2298f116deb1c7517e98743d55bc28d3bb` |
| HOLDOUT-3015-COHORT-v2.json | `e627bc4c150cc106a6397d86296287ddb9dab79b988da3eed9e6ef8a87c80bea` |
| ML3 RUN.json | `576cc454bd0be4a070935da773233bc099bc295fe73cee834af2bafe56bd9075` |
| ML3 RELEASE-FEATURES.json.gz | `959719bf19417746f657244f896604792322772855bb0946565c765fb1d67f2f` |
| ML3 predictions/task-00000.json.gz | `5a228606b581ff5400f55bd00ba86fa7ab3bd6547464b459ae90005aa9153962` |
| ML3 predictions/task-00001.json.gz | `fa5b32735d4d692c7e05d5019d9467fc33e074a4764d46a0bf57dbdb6f4e54a9` |
| Final source checkpoint REVIEW.json | `e917d26da5f436b50df4eb48dd231cdf404d5237ada081696c8787b765031828` |
