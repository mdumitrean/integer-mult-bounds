# P1 selector obstruction on the pinned PR2979 five-copy fill

The registered P1-PACKING-TOPPLE family is a confirmed **protocol-specific NULL**. All 60 cases completed under each of seeds 28099 and 63073, and corresponding cases have identical scientific fields. Every case returned `NO_SELECTED_NEIGHBORHOOD`. This note reads the saved receipts and frozen source only; it does not rerun a census, flow, audit, or numerical calculation.

The decisive common obstruction is already visible before the four-transport constructor: every case records `F_scored = F_retained = 2`, while its selected neighborhood requires four distinct original F families. The bound of 64 retained F candidates never truncates these lists. This establishes failure of the registered selector, without establishing a global timing, matching, or packing impossibility.

The experiment consumed 317.367622998 CPU seconds and 41.37838370259851 wall seconds with the configured 61-worker pool. Controls and baseline audits passed under both seeds. The separate proposed-profile moment test passed conditionally, but no candidate fill was produced. Full scaled native, physical, prefix, supplier, and outer admission remains unrun; no improved κ is certified.

The evidence is [RUN.json](../P1-PACKING-TOPPLE/v1/RUN.json), the [first seed result](../P1-PACKING-TOPPLE/v1/seed-28099/RESULT.json), the [confirmation result](../P1-PACKING-TOPPLE/v1/seed-63073/RESULT.json), and all 120 immutable receipts in [search/](../P1-PACKING-TOPPLE/v1/search/). The protocol is [P1/PREREGISTRATION.json](../P1/PREREGISTRATION.json); the frozen implementation is [topple.py](../../../pipeline/continuation06/topple.py).

## What was counted

The counts below are **per seed**; the second seed repeats them exactly.

| Saved count | Value | Interpretation |
| --- | ---: | --- |
| Completed cases | 60 | All 15 four-Z subsets, with four fixed tie variants each |
| Cases with all 64 A-pair flows rejected | 32 | These cases stop before any D candidate is tried |
| Other cases | 28 | Each tries 128 D candidates; every attempt fails F-family matching |
| F candidates scored / retained, in every case | 2 / 2 | No top-64 truncation occurs |
| Five-role F flow checks | 480 | Four Z groups times two F candidates, across 60 cases |
| A pairs tried | 3,840 | 64 in each case |
| A flow rejections | 2,048 | 32 times 64 |
| D candidates ranked / tried | 3,584 / 3,584 | All are rejected by the following F-group matching gate |
| F-group matching rejections | 3,584 | No four-family injective assignment is found |
| Width-7 D flow checks | 0 | The program never passes F-group matching |
| Complete four-transport variants | 0 | No selected neighborhood reaches the up-to-300-variant stage |

The last two zero counts are absent Counter entries in the receipts and follow from the source's control flow. They are not failed experiments. In particular, the result must not be described as 60 times 300 failed complete transport systems: the registered conditional continuation was never reached.

Representative receipts are [task-00000](../P1-PACKING-TOPPLE/v1/search/task-00000.json.gz), which rejects its 64 A-pair flows, and [task-00001](../P1-PACKING-TOPPLE/v1/search/task-00001.json.gz), which reaches the F-family matching obstruction. Their confirmation-side representatives are [task-00061](../P1-PACKING-TOPPLE/v1/search/task-00061.json.gz) and [task-00060](../P1-PACKING-TOPPLE/v1/search/task-00060.json.gz), respectively. These representative files need not describe the same case as one another; exact confirmation was checked by `case_id` across all saved receipts.

## The restricted logical obstruction

An original Z bin has pattern `[4,8,9,9,9,9]` at capacity 48. Selecting four original Z bins and taking all five copies supplies four groups of five width-4 roles. The constructor sends each entire group to the five copies of a distinct original G bin, changing its pattern `[9,9,9]` at capacity 32 into F = `[4,9,9,9]`.

In `_select`, F scoring visits every original G bin whose physical family differs from the four chosen Z families. A bin is scored only if at least one of the 20 width-4 roles is eligible for one of its five copies. `_bin_score` applies the actual window and existing-family guard through `Context.eligible`; it does not rank an otherwise ineligible pair into the graph. The top-64 operation retains all two scored bins in every completed case.

The subsequent cached five-role flow can remove edges from this two-bin candidate graph, but cannot add a new F bin. Choosing A and D removes further forbidden families. Finally, `_injective` requires an injection from the four Z groups into **distinct physical families** of surviving F bins. There are at most two such families, even if the two bins themselves have different families. Thus, for the set of all four Z groups,

`|neighborhood of the four groups| <= 2 < 4`.

This is a Hall cardinality obstruction with deficiency at least two for this particular group-matching graph. Equivalently, a unit-capacity graph on these groups and candidate families has a separating cut of capacity at most two against demand four. This logical upper bound follows from saved cardinalities and the code; no missing concrete min-cut vector has been reconstructed or claimed. At the individual-role level, the two original F bins supply at most ten copied F positions for twenty width-4 roles under the registered target pattern.

Changing the deterministic tie order, raising the top-F limit, widening the A-pair shortlist, widening the D shortlist, or spending longer on the same selected-neighborhood flow does not remove this obstruction while this F candidate rule and four-distinct-F-family requirement remain fixed. The 32 earlier A-flow failures do not weaken the common argument, because F scoring and its count happen before the A-pair loop in every case.

## What the eligibility guard does and does not prove

For a role at call time `t` and target bin `(owner, child, port)`, `Context.eligible` requires the strict/weak window convention `start < t <= stop`, a valid port, and width no greater than capacity. If the target owner is in a different one of the five copies from the call, the unchanged lifted fill has no pre-existing role of that call in the target family. For a target in the call's own copy, the implementation rejects an existing use of the same physical family unless that particular existing role is in the declared removal set. New-to-new family collisions are handled later by the per-call/per-bin unit-capacity flow node and the simultaneous patch validator.

F scoring calls `_bin_score` with **no removals**. The cached F-group flows list the incoming width-4 group as removed, but those roles originated in Z families, which have already been excluded as F destinations. Under the registered neighborhood, all eleven original families—four Z, four F, one D, and two A—must be distinct. All 69 transported roles originate in Z, D, or A bins. Consequently none of those removals can release a pre-existing collision in an F family. Retaining every original F-family occupant during F scoring is therefore a necessary restriction of this constructor, rather than a removable false rejection within its own eleven-distinct-family premise.

This restriction is conservative relative to general allocation repair. A different construction could remove other roles occupying an otherwise useful family, use several related bins in a physical family with an explicitly coupled call-injectivity model, or change the collection of patterns and destination roles. Those possibilities were excluded here. The receipts also do not separate how many F candidates failed the time-window test versus the existing-family test. They record two surviving bins, not a causal census of all rejected pairs or the identities of the two survivors. It would be unsupported to infer that windows alone forbid the desired allocation, or that family occupancy alone does so.

The flow implementation checks integral capacity bounds, conservation, and max-flow/min-cut equality in memory. This run persists rejection counts and successful certificate summaries, rather than every rejected network and its cut vector. The saved counts justify the cardinality argument above and the stated protocol outcome. They do not supply an independent per-A-pair or per-F-edge cut census.

## The premise that a successor would need to change

The exact pattern circuit remains algebraically valid: it preserves all role-width counts and total rank mass, and its proposed idle delta is `20 H1 + 19 H3 - 25 H5 + H48`. The saved conditional moment certificate prices that profile if realized. P1 fails at allocation realization under its particular sufficient constructor.

A successor would need to expose more eligible F positions or change what counts as an F position. One concrete possibility is a coupled reassignment that also evacuates the call-family conflicts blocking new width-4 destinations. Another is a different balanced pattern circuit that sends the width-4 roles to other existing pattern classes. Either would require a fresh finite domain and preregistration, a complete inventory and simultaneous-family model, an exact complete-profile comparison, and full literal admission. Merely letting a Z group split across the same two original F bins leaves only ten copied F positions and does not by itself solve the twenty-role deficit.

An altered copy chronology or a larger lift is also a changed premise. Neither its feasibility nor a gain follows from this run. It would additionally require the corresponding source-bound scaled implementation and outer obligations. The present result neither asserts nor rules out feasibility of the 55-bin circuit under a broader reassignment, global optimality of the PR2979 literal fill, or attainment of its fractional packing ceiling.

The word “toppling” here denotes a guarded inventory-neutral pattern exchange. This experiment does not establish a state-independent Laplacian, an abelian physical process, or an order-independent cost-reducing stabilization.

## Source binding and attribution

The source is PR2979 by Marius-Paul Dumitrean (`mdumitrean`), head `be191346391661f4d35fc0d1508d0a6029572576`. This interpretation retains the full inherited [PINS.json](../../../data/words/PINS.json), the source package's [CREDITS.md](../../../data/continuation-05/pr2979/package/CREDITS.md), [NOTICE](../../../data/continuation-05/pr2979/package/NOTICE), and [SOURCES.json](../../../data/continuation-05/pr2979/package/SOURCES.json). The two per-seed results contain their complete provenance, including the original word pins and source package lineage. This note does not replace that attribution or treat producer-reported native evidence as an independent replay.

| Artifact | SHA-256 |
| --- | --- |
| P1 preregistration | `deb139a9fcda30873780c56c5f6e11679514c4f1059f958360514620186a18f7` |
| Frozen `topple.py` | `1e70fe763c412a8f8b416a3cd5c0bded85b765ddd53f2b9d402c1d4f4eaa2660` |
| Run implementation manifest | `4cdeae9dd11da7fd545a475d2aca561ed7e0552a1c4f0fa10e492b165bba3b6f` |
| `RUN.json` | `4117f310a92fd6eba8772a88a676bd6c38bb24ef3bad8a3860ec48a9abcbe4b0` |
| Seed 28099 result | `675a8fec5b06ddbab68d007e8836f1f1efa78f8bb2e7eebd8f49054809051ed1` |
| Seed 63073 result | `1ffd0bd08b25df1a98bd7f680f6bba19a0af2a27b7828fef6fbddc6565cafd6a` |
| Original `PINS.json` | `4d62f7caf94a102ebb83feb3beca6ebeb1ab9637901ff51cc84e5beeb15d2a65` |
| Source `CREDITS.md` | `bf85777bd2d9b8e537dae2e70614759ba1a265101dd903a72fbd2cfc2869c406` |
| Source `NOTICE` | `b767e40e8c7e16058d1ebb8c08eef9b9bffae31cfa30512b843ae1fcbfc6f5cd` |
| Source `SOURCES.json` | `d5f3f498d4d34125bcaed14dafaceaff342223d511d1099993d5b217a147019c` |
