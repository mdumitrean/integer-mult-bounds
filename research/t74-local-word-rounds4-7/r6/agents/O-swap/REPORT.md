# r6 / O-swap: same-inventory width swaps, priced jointly

Agent O-swap (round r6, 2026-10-15, 06:19-07:10Z). Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz` (#1672 blobs
76c01583 / e86142b3). Toolkit: our #1186 rev3 copy (`toolkit/`), b = 0.001679754956125544. Local only: nothing committed,
pushed or posted.

**Outcome: scoped negative. No same-inventory width swap gains on either word; every swap priced jointly costs exactly the
sum of its two parts. κ is unchanged.**

## Question
A swap narrows one width-5 helper (or group) to width 4 and widens one width-4 helper (or group) to width 5 in the same
word, so the width inventory, and with it the T74 fill, is unchanged (PR1319's `reconstruct.py` assigns width-4/5 roles to
any helper of that width). r4 D-widths priced each half alone: the best pair cancels exactly (−8,458,352 + 8,458,352 = 0).
Coupling between the two halves (like the 7,464-unit discount inside a (5,9) group upgrade) could make a joint price negative.

## Results (exact optimal frames re-solved jointly, cone caps recomputed)

| Swap family | Pairs priced | Joint − additive | Best joint Δ | Negative |
|---|---:|---|---:|---:|
| Base, group swaps: 11 (4,9) groups (their one feasible narrowing) × 341 widening options (3 (5,9) groups × 31 hyperplanes, 8 (0,4) groups × 31 extensions) | 3,751 | 0 for all | 0 (225 pairs) | 0 |
| Extra, group swaps: 12 (4,9) groups incl. 627..631 × 310 widening options, additive ≤ +7,464 | 1,860 | 0 for all | 0 (180 pairs) | 0 |
| Base, single swaps whose influence regions overlap (of 44 × 1,364 = 60,016 pairs) | 824 | 0 for all | +7,464 | 0 |
| Base, single swaps, seeded random control of non-overlapping pairs | 200 | 0 for all | +7,464 | 0 |

- **Region filter** (`scripts/regions.py`): a change's region is every node whose (L, U) differs from the base graph, every
  frames-graph component containing one, and one chain hop. optimal_frames is separable over components, so pairs with
  disjoint regions price additively; the 200 controls confirm it.
- **The 6 uncertified single narrowings** (639, 647, 671, 679, 702, 703) are bounded rigorously with the toolkit's
  true-moment interval: their largest possible saving is 2,089,286 or 2,091,739 units, at least 24,715 below a widening's
  c[1] = 2,116,454, so no swap using them can gain (`out/UNCERT-BOUNDS.json`).
- **Why it is additive:** the (5,9) and (0,4) widening groups have fully forced chains in the base graph (no frame
  variables); widening one creates variables only on its own chains, which never meet the components that carry the (4,9)
  narrowings (components 0 and 2). The only coupling found anywhere is the known discount inside one group.
- **Exactness of the zero-delta swaps:** `words/swap-603-619.json.gz` (narrow 603..607, widen 619..623 with hyperplane
  [24, 96, 132, 260]) has Δ = 0, certified, the base profile, 7,208 compensation gates, the unchanged inventory, and passes
  the unchanged `audit_local.py --main` (PASS_INDEPENDENT_EXACT_FORWARD_AND_DUAL_ENDPOINT_FRAMES_ENTRANCES_CONES). It is an
  equal-cost alternative word, not a gain.

## Scope
One-level width swaps in classes 4/5 (single helpers and r4 D's 4-helper groups), start side and end side as r4 D
defined them, on the base word (and group swaps on the extra word), at fixed program and b. Not covered: widths 7/8/9
(their roles are tied to specific helpers in the owner map, so swapping them changes the hosting), multi-group swaps,
and swaps combined with program edits.

## Evidence
`EVIDENCE.json` (summary); `out/GSWAP-base.jsonl`, `out/GSWAP-extra.jsonl`, `out/XGROUPS-extra.jsonl`,
`out/REGIONS-base.json`, `out/SPAIRS-base.json`, `out/SSWAP-base.jsonl`, `out/UNCERT-BOUNDS.json`, `out/PROBE-base.json`,
`words/swap-603-619.json.gz` with its audit receipt. Scripts: `scripts/gswap.py`, `xgroups.py`, `regions.py`, `sswap.py`,
`bound_uncert.py`, `audit_swap.py`, `analyze_g.py`, `probe.py`, and `wcore.py` (r4 D-widths', unchanged). At most 4
workers (fork, per-task deadline, RSS check, maxtasksperchild); about 40 minutes of solves.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
