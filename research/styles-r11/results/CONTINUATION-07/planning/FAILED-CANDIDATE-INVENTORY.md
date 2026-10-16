# Historical E1/E2 frame-feasibility dataset: schema and scope

This is a source/schema inventory and implementation plan. No historical feature census, model fit, statistical test, or scientific module import has been run for this note. The proposed target is legal fixed-exterior frame assignment on the pinned PR2966 word. It is not a κ-success label.

## Available units and labels

The existing [E1 run](../../CONTINUATION-04/E1-ADJACENT-EXPANSIONS/v1/RUN.json) records 2,144 provider-specific assignments and 4,288 pricing tasks including confirmation. The existing [E2 run](../../CONTINUATION-04/E2-OTHER-CORRECTION-POSITIONS/v1/RUN.json) records 4,288 assignments and 8,576 pricing tasks. Each provider has 134 eligible adjacent source pairs; E1 gives eight corner labels with the correction last, and E2 gives eight labels in each of the FIRST and MIDDLE placements. The [published summary](../../CONTINUATION-04/RESULTS.md) reports these partitions, excluding the repeated confirmation seeds:

| Family | Frame rejected | Frame legal, identical profile | Frame legal, worse profile | Total |
| --- | ---: | ---: | ---: | ---: |
| E1 | 304 | 1,784 | 56 | 2,144 |
| E2 | 608 | 3,608 | 72 | 4,288 |
| Combined | 912 | 5,392 | 128 | 6,432 |

The mixed primary target is `frame_legal`: 5,520 legal versus 912 rejected. The secondary label `worse` is defined only for legal rows: zero for an identical profile, one for a rigorously worse profile. It is missing for rejected assignments. These counts come from the existing runs and write-up; they are not results of a new feature experiment.

Both frozen implementations return `REJECTED_GUARD` only when `_frames` finds a `frame_inclusion`, `exit_inclusion`, or `exit_equality` failure. A return with this status has `local_profile = null` and `moment_delta = null`. The other observed status is `NO_GAIN`; its source-derived frames passed the predicates and its canonical complete profile agreed with the independently counted boundary bill. These labels therefore distinguish frame feasibility, not successful κ improvement.

The original implementations can also return `PASS_CANDIDATE` or `EXPLORATORY` for a feasible assignment with favorable or unresolved moment sign. Neither occurred. The saved runs report no errors, timeouts, unpriced assignments, or unresolved signs. A future loader must treat a missing receipt, pool error, inconsistent status, or unsupported schema as an integrity failure, not a negative training example. An unresolved cost may still have a legal-frame label, but cannot receive a false `worse = 0` label.

## The actual parent words

The source is Jeremy Kothe (`jeremykothe2`), PR2966 head `e62d3eb9005117d82a9babcfa937ecc53237c490`.

| Provider | Actual input under `research/styles-r11/` | Compressed SHA-256 | Canonical JSON semantic SHA-256 |
| --- | --- | --- | --- |
| base | `data/continuation-04/pr2966/package/rewrite/FINAL-WORD-base.json.gz` | `4e96cf33d2e0f85f6ff5ccc6165a6c8c0305ca0081ecaf40d72c5e1c4a13e9a5` | `96354832716139e4a66581ccaff6cb825908268185fbb60921ccc7cc94e63185` |
| extra | `data/continuation-04/pr2966/package/rewrite/FINAL-WORD-extra.json.gz` | `440398ee0d2bfd9448be77fa0652512cb79c6ecda9ae030afc79259056f5c6dc` | `87cfc6f939add01e441eb830f48f6d6fb79436ca7faded768485e7ac7bbb4033` |

The package's `data/WORD-base.json.gz` and `data/WORD-extra.json.gz` are inherited PR2942 inputs. They are **not** the words priced by E1/E2. A loader using those paths would attach the wrong context to the saved labels.

Semantic hashes use the frozen implementation's exact `json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)` encoding. Each saved proposal also carries a semantic parent hash and the exact original gate preimage. The source report has `v`, `h`, and `R`; the register count is `2*v + R`, not a nonexistent `report.n` field.

## Exact task examples

The task wrapper in both families has exactly `candidate`, `kind`, `output_dir`, `provider`, and `seed`. `kind` is `price`; `output_dir` is an artifact destination, not a feature. The examples below are the first entries of the pinned task manifests, selected by file order rather than their outcomes. The candidate dictionaries are complete; the long output-directory string is omitted from the displayed wrapper.

E1: [PRICE-TASKS.json.gz](../../CONTINUATION-04/E1-ADJACENT-EXPANSIONS/v1/PRICE-TASKS.json.gz), entry zero, seed 22079:

```json
{
  "candidate_id": "0d849461c34768fff74f8216e48f482a2bdf5c2b6c1526b8357b421420f7b482",
  "chain": {
    "a": "-1/4", "b": "-3/2", "chord": "-3/8",
    "i": 332, "j": 320, "k": 510,
    "orientation": "AB_to_BAC_minus"
  },
  "interval_sha256": "562f3af9d1c7f809a1fa61e908b4e6e1f1a94a25a43b79a8340b24d0d8c02a99",
  "orientation": "AB_to_BAC_minus",
  "original_gates": [
    ["add",332,320,-1,4,[]],
    ["add",320,510,-3,2,[]]
  ],
  "parent_semantic_sha256": "87cfc6f939add01e441eb830f48f6d6fb79436ca7faded768485e7ac7bbb4033",
  "positions": [297,298], "provider": "extra", "section": "A",
  "variant": ["U2","L1","S"]
}
```

E1 has no `placement` field. Its correction is last; the ML slot calls this placement `TAIL`.

E2: [PRICE-TASKS.json.gz](../../CONTINUATION-04/E2-OTHER-CORRECTION-POSITIONS/v1/PRICE-TASKS.json.gz), entry zero, seed 31081:

```json
{
  "candidate_id": "a383bcc0888ac4176485397425f3fe9cea0e280386694457594ad0f355c16322",
  "chain": {
    "a": "1", "b": "1/16", "chord": "1/16",
    "i": 237, "j": 225, "k": 510,
    "orientation": "BA_to_ABC_plus"
  },
  "interval_sha256": "88cde6e07e562378f035a37b09df52305944a7e65040964a0cfee419c5e3a0f7",
  "orientation": "BA_to_ABC_plus",
  "original_gates": [
    ["add",225,510,1,16,[]],
    ["add",237,225,1,1,[]]
  ],
  "parent_semantic_sha256": "87cfc6f939add01e441eb830f48f6d6fb79436ca7faded768485e7ac7bbb4033",
  "placement": "MIDDLE",
  "positions": [127,128], "provider": "extra", "section": "A",
  "variant": ["U2","L1","U3"]
}
```

An addition is encoded as `["add", target, source, numerator, denominator, literal_frame_basis]`. Frames are bases encoded by integers in F2^9. The eight labels are the Cartesian product `S ∈ {L2,U2}`, `R ∈ {L1,S}`, `T ∈ {S,U3}`. They are retained even when two labels happen to produce the same assignment.

## Receipt schema and pre-evaluation context

The corresponding receipts are [E1 task-00000](../../CONTINUATION-04/E1-ADJACENT-EXPANSIONS/v1/price/task-00000.json.gz) and [E2 task-00000](../../CONTINUATION-04/E2-OTHER-CORRECTION-POSITIONS/v1/price/task-00000.json.gz). Both have the wrapper keys `cpu_seconds`, `peak_rss_bytes`, `result`, `seconds`, `status`. The wrapper status is `OK`, separate from the scientific result's `NO_GAIN`.

Both example results have these exact top-level fields:

```text
built_semantic_sha256, candidate, candidate_id,
canonical_profile_and_boundary_delta_agree, cleanup_sha256,
compensation_sha256, cpu_seconds, guards, local_profile, moment_delta,
optimizer, ordered_widths, physical_families, private_buffers,
provider, scalar_instruction_delta, scope, seed, source_attribution,
source_pin, status, width_inventory, word
```

Rejected rows omit the later derived fields and retain the initialized null profile, moment, word and optimizer. This field-presence difference must not become a feature.

`guards.boundaries` is populated for **both** classes before `_frames` is called. It has keys `i`, `j`, `k`; every register record has exactly:

```text
register, virtual_register, entry, exit, equality_exit,
previous_node, next_node, previous_origin, next_origin
```

For example, E1's `i` record is:

```json
{
  "register":332, "virtual_register":332,
  "entry":[], "exit":[], "equality_exit":false,
  "previous_node":1064, "next_node":1271,
  "previous_origin":["A",288], "next_origin":["A",495]
}
```

E2's `i` record is:

```json
{
  "register":237, "virtual_register":237,
  "entry":[], "exit":[], "equality_exit":false,
  "previous_node":237, "next_node":935,
  "previous_origin":["start",null], "next_origin":["A",159]
}
```

These values describe the unchanged parent word. The frozen `_fixed_graph` uses the trusted BORROW adapter to split warp aliases and construct literal source chains without an optimizer. `_boundaries` takes the contact immediately before and after the original pair on each of its three register chains. It requires the shared register to keep one alias through the pair and records cut/end equalities. No candidate profile, refit or cost participates in these values.

For a lightweight historical dataset, these authenticated boundary snapshots can be reused, with invariance checked across every corner, placement and confirmation seed for each provider/pair. This is source binding and consistency checking, not a fresh independent reconstruction of the old frame graph. The planned loader makes that scope explicit. It independently checks the literal original gate preimage against the final word bytes.

## Proposed numeric feature whitelist

[dataset.py](../../../pipeline/continuation07/dataset.py) separates all numeric features from labels and provenance. Its source declares 99 `context_` features and 23 `proposal_` features; the actual emitted schema is checked uniformly during registered preparation.

`proposal_` features are fixed one-hot encodings of section, orientation, correction placement, and the three corner choices; plus sign, absolute numerator and denominator of `a`, `b`, and the correction coefficient. `context_` features are the two original gate-frame ranks; each register's entry/exit ranks, rank slack, equality flag and entry/exit intersection/union dimensions; categorical exterior-contact origins and same-section distances; all pairwise entry and exit intersections/unions; cross-register entry/exit intersections/unions; and the three-way entry and exit intersections/unions.

The function producing features accepts only the proposal and source-boundary values. It never receives result status, a candidate profile, a moment, the optimizer or failed predicates. Provenance hashes, candidate IDs, provider names, source positions and fold keys are retained outside the feature matrix. Source positions are used only to obtain contact distances and to group all variants of one pair.

Explicitly excluded as predictors: `guards.frames`, `guards.failures`, `guards.predicates_passed`, `guards.original_window_bill`, `guards.expanded_window_bill`, `local_profile`, `moment_delta`, `ordered_widths` from the result, output-word presence/hashes, execution time, memory, selection status and any admission result. Label parsing may read these fields to validate its label; feature construction may not.

The registered feasibility predicates are already exact and cheap. Any classifier result must be compared with that fact: it may summarize which source contexts caused rejection or support a bounded screening study, but it does not replace an exact guard or establish a new structural law. It cannot establish a κ gain because this dataset contains none.

## Loader, integrity and grouping design

The proposed API is `prepare() -> summary`, `get_rows() -> prepared rows`, and `audit_task(seed) -> JSON receipt`. Preparation runs once in the coordinator after preregistration and source freeze. It loads two final words, the historical task manifests and original result-receipt references; verifies `RUN → RESULT → task receipt` hashes; verifies frozen old implementation bytes; binds each receipt to the matching task and literal source preimage; and removes repeated seeds only after exact proposal/label agreement. No acquired program is imported.

A prepared row contains:

```text
row_id, experiment, candidate_id, provider,
pair_group, pair_address, permutation_slot, permutation_stratum,
features, labels, proposal, source_boundaries, provenance
```

`labels` has `frame_legal`, `worse`, and `profile_relation`. `provenance` points to both confirmation receipts and their hashes, the input task manifest, the exact final-word bytes and semantic hash, source author/pin, and old implementation hash. Summary fields include `feature_names`, `proposal_feature_names`, `sourcecontext_names`, `context_feature_names`, source-result references and complete inherited word attribution.

The planned `pair_group` hashes `(source lineage, section, positions, register-role pattern)` and excludes provider, seed, orientation, corner and placement. Both provider twins and all 24 assignments/provider must stay together. Preparation will require 134 groups, each with the same 48 unique slots; if the historical addresses do not support that grouping, preparation fails rather than silently permitting leakage.

`permutation_slot = (provider, TAIL/MIDDLE/FIRST, corner tuple)` aligns the complete label vector within each group. `permutation_stratum = (section, orientation, canonical Fraction strings for a, b, chord)` preserves every proposal-only feature at each aligned slot. A null permutation should transfer whole aligned 48-label vectors between groups in the same stratum, never shuffle individual rows. The learner should explicitly verify identical proposal features before a permutation. Singleton strata remain fixed and cannot provide evidence of significance; sparse strata are reported without adaptive widening.

Leave-pair-out folds test new adjacent pairs within this one pinned source. Neighboring pairs may still share registers or nearby contacts, so this is not independent-lineage generalization. E1-only versus E2-only random splits would also leak the same source pairs. A later unchanged methodology on an untouched word is needed for a prospective transfer claim.

The registered audit should verify exact binary-rank controls, source preimage rejection, unsupported-status rejection, source-boundary invariance, confirmation equality, uniform feature keys, expected label partition and slot completeness. It should not train a model. No such audit has run while writing this note.

## Pins and credit

| Artifact | SHA-256 |
| --- | --- |
| Frozen E1 implementation | `5f358c2084cd39f669758cd42c077dbb93726ef79bc8a2055d7ea1f17f7f7442` |
| Frozen E2 implementation | `3090a36a2b6daa7dad88fa5c3da1e6b08623a881d744ca5275b15c405055adb0` |
| E1 task manifest | `a8acf8514350c7c57bac72834f107bcb2d6f09cc8c96d8b47ebee458b573d8a5` |
| E2 task manifest | `33f233207d1582e0e855955e2962de49f608f5e6a904a9cff11b6249b2ecbfd7` |
| E1 run manifest | `bc70b24a299c9c102da06152e51fc8eafa1e6af0fb6d770bd84d23be08f9b4c9` |
| E2 run manifest | `7026ad525428d27014890a5f5faa77761c80f603e3c3728153c354cbd3540d53` |
| E1 example receipt | `f0bafb83c71731d2892adb8f2f9f1e6b8e4fa8eb211c7a3e9aff2d7f5efbe46f` |
| E2 example receipt | `82964c533d7043f58f29166f099cffe3d1d7b6ac69793ae4cd7ea88c327d7de8` |

Every original seeded result retains all inherited [PINS.json](../../../data/words/PINS.json) attribution and PR2966's source notices. The production's direct predecessor is CubeJerry's PR1533 adjacent-expansion analysis on the older PR589 bit word; the modern source and rewrite lineage credits Jeremy Kothe, Marius-Paul Dumitrean, Mason Hale, Jeremy Diviney and all upstream notices. Model labels must retain their original protocol and evidence tier rather than turn these scoped experiments into universal failed-method claims.
