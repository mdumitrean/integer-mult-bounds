# r4 / D-widths: the helper width interface of the 566+554 T74 words

Agent D-widths, round r4 (2026-10-15, about 01:53–02:20Z). Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz`
(#1672 blobs 76c01583 / e86142b3). Toolkit: our #1186 rev3 copy (`toolkit/`), b = 0.001679754956125544. Local only:
nothing committed, pushed or posted.

**Outcome: scoped negative. No width change is cheaper than the extra word's own, and no same-inventory swap gains.
κ is unchanged.**

## 1. What a width is
- From the word (toolkit `word.recount`): for helper q (224..703), width(q) = dim span(`helper_final[q]`, default GF(2)^9)
  − dim span(`start_extra[q]`, default {0}). This reproduces both inventories exactly: base {4:44, 5:44, 7:38, 8:114,
  9:240}, extra {4:40, 5:48, 7:38, 8:114, 9:240}. The contract's `entrance_rank` (372) and `terminal_codimension` (214)
  are the summed start dimensions and end codimensions: 480·9 − 372 − 214 = 3,734 = Σ widths.
- A helper's frame climbs from its start frame to its end frame, so **its width is exactly its paid rank mass**. Local
  rank mass = 896 (data) + 896 (ports) + Σ widths + 64 (centres) = 5,590 base and 5,594 extra.
- Every width level is therefore one rank unit, priced at a marginal rank cost. At b, c[1..9] = 2,116,454, 4,227,983, …,
  18,977,915, and the marginal costs c[r+1] − c[r] only fall from 2,111,529 to 2,105,319. The extra word pays 2,114,588
  per upgrade; no realization of a one-level upgrade can cost less than about 2,105,319, so the whole lever is worth at
  most about 9,300 units per upgrade (about 37k per extra call) even before feasibility.
- How the hosting uses widths: PR1319's `reconstruct.py` packs whole-helper widths into rank-32 child bins
  (owner_replica, child, port) with capacity and time windows from the parent. A child (4,9,9,9) leaves an H1 hole;
  (5,9,9,9) fills it. Width-4 and width-5 roles move by augmenting paths and are assigned to *any* helper of that width
  in the call (`pool[t, w]`); other widths are fixed. The extra provider exists to turn 4 width-4 demands into width-5
  demands per call (249 base / 417 extra calls, idle H48 = 22,748, no H1 holes).

## 2. Calibration
Removing level 390 from the start frames of 627/629/630/631 in the base word and re-solving exact optimal frames gives
**+8,458,352 units per call and a word equal to the extra word** in every section (A, cut, all B frames, cleanup, tails,
helper_final, centres), up to the order of the start-frame basis vectors. A single upgrade of 627 alone costs exactly
c[1] = 2,116,454; all four together cost 7,464 less than four singles.

## 3. Cost distribution (base word, exact optimal frames, cone caps recomputed)

| Change | Options priced | Result |
|---|---:|---|
| Single upgrade 4→5, start side (12 helpers of type (5,9), every hyperplane of the start frame) | 372 | all exactly c[1] = 2,116,454 |
| Single upgrade 4→5, end side (32 helpers of type (0,4), every extension of the end frame) | 992 | all exactly c[1] |
| Group upgrade, the 3 (5,9) groups (619–623, 627–631, 651–655; one common hyperplane) | 93 | 8,458,352 for 15 of 31 hyperplanes in every group (= the extra word), else 8,465,816 = 4·c[1] |
| Group upgrade, the 8 (0,4) groups (273–282 … 385–394; one common extension) | 248 | always 4·c[1] |
| Subsets of 627–631 (2 or 3 members) | 10 | exactly 2·c[1] and 3·c[1]: the discount needs the whole group |
| Mixed hyperplanes inside a (5,9) group (random sample of the 15 optimal ones) | 80 | always 4·c[1] |
| Single narrowing 5→4, start side (44 helpers of type (4,9), every extension) | 1,364 | 1 feasible per helper: saves 2,089,290–2,108,990 (less than c[1]); 1,320 infeasible, 6 uncertified |
| Group narrowing, the 11 width-5 groups (one common extension) | 341 | 1 feasible per group: saves 8,438,652–8,458,352 |
| Narrowing 5→4, end side (the only candidate: the 8-dim frame before the final rank-1 climb) | 44 + 11 groups | all infeasible: the new cone caps on 9 registers fail "L not inside U at mutable vertex" (B1436, B1468, B1596, …) |

- **Cheapest upgrade of 4 helpers:** 8,458,352 per call, reached by all three (5,9) groups with any of 15 hyperplanes.
  That is exactly the extra word's cost; nothing is cheaper (no cheaper extra-word variant, so no dispatch change).
- **Best same-inventory swap** (narrow one width-5 group, widen one width-4 group): −8,458,352 + 8,458,352 = **0**. The
  base word's 44 width-5 helpers are the upgraded form of (5,9)-type groups, and the reverse change gives back exactly
  the upgrade price.
- **Equal-cost alternatives:** the extra interface is not unique. G1 (619–623 dropping 260) gives a word with the extra
  inventory, the same profile and the same cost; with 15 hyperplanes per group there are 45 equal-cost choices.

## 4. Exactness of the variants
`out/variants/calib-g2-390.json.gz` and `g1-alt.json.gz` (exact optimal frames written back) pass the unchanged
`audit_local.py --main`: PASS_INDEPENDENT_EXACT_FORWARD_AND_DUAL_ENDPOINT_FRAMES_ENTRANCES_CONES, 7,208 compensation
gates, extra inventory, profile {1:2340, 2:508, 3:420, 4:126, 5:82, 8:8}. Neither is a gain.

## 5. Fill implications and what a re-solve would need
No variant beats the extra word, so nothing changes in the fill. Had one done so, the steps would be: rebuild the extra
provider's registry (its `widths` list changes at the new helper indices; inventory unchanged), re-run PR1319's
`reconstruct.py` (the bins and windows do not depend on helper indices, so this relabels the width-4/5 roles), native
admission of the new word, rebind PLAN, the strict T74 replay and the outer assembly, as in our #1625 pipeline.

## Scope
One-level start- and end-side changes of single helpers and of whole 4-helper groups, at fixed program and b, on the base
word (the extra word shares the program; agent r3/A). Not covered: two-level changes, width classes 7/8/9 (fixed in the
fill), changes that also edit the program, and other hosting geometries.

## Best next step
The interface is priced out: every width level costs a full marginal rank unit and the extra word already takes the only
group discount. A remaining hosting-side lever would have to change the packing itself (other child ranks or widths
7/8/9 in the owner bins), not the per-helper interface.

## Evidence
- `out/SUMMARY.json` (all counts, distributions, best group/swap, end-side reasons, variants, audit statuses).
- `out/SWEEP-base.jsonl` (2,728 single changes), `out/JOINT-base.jsonl` (692 group changes), `out/MIXED-base.jsonl` (80),
  `out/ENDNARROW-base.jsonl` (55) + `ENDNARROW-WHY.json`, `out/variants/` (2 words, VARIANTS.json, AUDIT-*.json).
- Scripts: `scripts/wcore.py` (interface pricing), `w_inspect.py`, `calib.py`, `sweep.py`, `groups.py`, `joint.py`,
  `mixed.py`, `endnarrow.py`, `why_end.py`, `variants.py`, `analyze.py`. 3 workers (fork, maxtasksperchild, per-task
  deadline, RSS flag at 6 GiB; peak about 0.3 GiB per worker). About 20 minutes of solves.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
