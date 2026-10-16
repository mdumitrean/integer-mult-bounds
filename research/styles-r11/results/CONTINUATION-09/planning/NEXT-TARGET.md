# What J1 resolves, and a possible next target

**J1 is confirmed EXPLORATORY because its registered eligible domain is empty. It is not a broader shared-carrier NULL, and it produced no κ improvement.** This note reads only the saved J1 run, census, and control receipts. It performs no new source-word census, commutation test, frame computation, price calculation, or scientific import. Continuation09 is closed without broadening J1.

Both seeds, 49019 and 98009, report the same counts for each provider:

| Saved census quantity | Count per provider and seed |
|---|---:|
| Inner consecutive-contact pair records | 4,360 |
| Grouped pair combinations | 2,946 |
| Preliminary same-inner combinations, outside the four-register domain | 68 |
| Four-register combinations rejected by the exposure guard | 2,878 |
| Eligible packets / priced candidates | 0 / 0 |

Every recorded exposure rejection is an `intervening_contact`, not an unsupported opcode. Their section/kind counts are A fan-in 1,437; A fan-out 1,287; B fan-in 86; B fan-out 68. There were no ratio rejection receipts because no packet survived to carrier enumeration; that does **not** establish that all proposed transport ratios are admissible.

The 256 pricing tasks therefore contained no candidate prices. Both control tasks passed 3,212 checks, including the joint-positive fixture `4H1 → 2H1+H2` with neutral constituent single factors. This verifies the implemented synthetic mechanism and guards; it does not place that favorable geometry in the source word. The saved run records 15.697287087 CPU seconds, 8.077522051 wall seconds, and 61 configured workers.

## The bottleneck is the disjoint-exposure condition

The saved first offending gate touches packet registers only in its source position in 2,263 exclusions, only in its target position in 264, and in both positions in 351. These are descriptive counts of **one stored witness per rejected packet**. They neither classify all intervening gates nor show that any full exposure is algebraically legal. In particular, the receipt alone does not identify whether a read uses an inner or outer packet register, and a later intervening gate may impose a different dependency.

Nevertheless, the mechanism's immediate missing prerequisite is concrete: expose the four original operations while preserving their complete operator and a feasible frame invoice. The result does not say that the twenty-label tariff was unfavorable; that tariff was never reached on a source candidate.

## Prefer an exact commutation certificate before a whole-window rewrite

A plausible **untested and unpriced** follow-up would retain the saved excluded packet addresses and replace the support-disjointness requirement with a certificate of literal adjacent commutations. For additions `g=(t += a*s)` and `h=(u += b*v)`, the guard

` s != u and v != t `

is sufficient for exact commutation, even when the gates share a source or target. A separately preregistered deterministic procedure could gather the selected four additions at their first original position, recording every actual adjacent crossing and rejecting the packet at the first noncommuting gate. Prelude, warp, cut, and section barriers would remain fixed. No radius increase, extra target count, or unpriced correction would be introduced.

This changes the legal exposure hypothesis: J1 rejected every shared-register intervening operation, including operations that might commute exactly. It is not a conclusion that such an exposure exists. All earlier source-reported read-merge/split/retiming overlap remains possible; the unpublished details of PR2979's 5,893-candidate search prevent an assertion that this domain is previously unsearched.

A scalar commutation certificate would still be only the first gate. The commuting operations may change the per-register frame order. The new factor block would need its actual new entry and first-successor frames, including equality exits. Every remaining intervening gate must retain a valid chain. The old invoice must cover the **whole original window**, and the new invoice must cover the factor block plus the entire remaining window and first unchanged successors. One cannot reuse J1's four-selected-gate tariff as the total delta once interveners touch packet registers. The twenty-label theorem may optimize the now-contiguous factor block with those newly derived fixed interfaces, but a canonical whole-word profile/cleanup comparison must verify the complete delta.

This route has a small, reviewable new obligation: an exact crossing log plus the full changed chain invoice. It is more concrete than immediately introducing general context conjugation.

## Why coordinated whole-window rewriting remains a later possibility

If a packet cannot be exposed by exact commuting swaps, a whole-window carrier change could instead conjugate every affected read/write and add its required compensating operations. That is a genuinely different operator-production family. It is also much less mature: merely inserting a carrier and correcting the context may refine existing contacts without providing a cost improvement, and continuation05 already demonstrated that fixed target interfaces can forbid the needed new directions.

A useful proposal would first exhibit a named cancellation or contact deletion and a fully charged positive fixture for the *complete* context, including setup, undo, every correction, successor climbs, cleanup, and native scalar overhead. It would then need a finite coefficient/window alphabet and an exact all-column identity certificate. J1's shared-restoration fixture does not supply those additional context obligations. No whole-window candidate has been constructed or priced here.

Neither suggested route identifies an intrinsic Laplacian or proves a sandpile dynamical law. A commuting rewrite dependency graph is only a graph of the explicitly certified transformations. Any eventual favorable local word still needs both-provider canonical and full semantic audits, current literal allocation/profile binding, changed-word native evidence, finite/prefix charges, and strict outer arithmetic before a κ claim.

## Saved evidence and attribution

The authoritative outcome is [RUN.json](../J1-SHARED-CARRIERS/v1/RUN.json), with separate immutable [seed 49019](../J1-SHARED-CARRIERS/v1/seed-49019/RESULT.json) and [seed 98009](../J1-SHARED-CARRIERS/v1/seed-98009/RESULT.json) results. The observations above come from `data/continuation-09/j1-v1/census/task-00000.json.gz` through `task-00003.json.gz` and the two saved control receipts. Per-provider exclusion digests agree across seeds:

- Base: `046c9d5125106e339a294ae70f7107af8242ec4f171c9f98718bf61f96c262cf`.
- Extra: `d248167d990304991d0bf779cd830274d004448f24c1ec508344aefad8204b4c`.

The words are Jeremy Kothe's PR3015 at `e244296debb45fe6f4da84d29e4d64fbab55fda0`, retaining Marius-Paul Dumitrean's PR2979 and the complete inherited credits. Nick Petalas's PR3028 at `9d10633660a3dff5469f4e7a0a009a6c9994c0d7` supplies the source-reported current comparison endpoint `34583046742859167313/20000000000000000000000`; it reuses those words in its separate T148 allocation. All original `data/words/PINS.json` attribution remains in the result receipts. This note neither replays nor promotes the source releases' native/outer admissions.
