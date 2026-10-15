# T74 566+554 supplier: rounds 4–7 (no new κ)

**Status:** FINDING · 2026-10-15 12:17Z · priority revision 4 (main `0fdd7d82`). Author-checked local replays; not maintainer-reviewed;
not a PR. This follows round 3 (fork branch `t74-local-word-round3`, discussion
[#2143](https://github.com/CrocSwap/integer-mult-bounds/discussions/2143)).

**Question.** Can any change make the pivot-566+554 T74 supplier cheaper? That supplier carries #2044, #2161, #2180 and
#2220. Round 3 searched only exact local edits with A, the cut and the compensation fixed. Rounds 4–7 attack that premise,
the hosting interface, the generators, and the outer's ceiling.

**Outcome: no κ improvement.** Every lever reachable with existing code is closed or proven infeasible in its model.
Each folder holds that search's `REPORT.md`, or `FINDINGS.md` where the subagent harness blocked the report, with
evidence JSON and scripts.

## Results by lever

| Lever | Folders | Result |
|---|---|---|
| Re-routing in the A section; neutral-move walks; port dirt; widths | r4/A, B, C, D | No A gate touches a port, so A edits cannot reach ports. Walks: 3,397 first moves and 13,160 second moves, all net 0. The compensation is re-derived by the auditor and native chain, but every pure-dirt read comes from entering helpers. Width = paid rank mass, and the extra word is already the cheapest interface. |
| Frame-solver slack; cut and precondition; hosting packing; compensation-aware kernels | r5/A, B, C, D | Solver and checkers agree on every frame rule, and dropping all caps leaves the cost unchanged. The cut's only price is 8 centre descents, which can't shrink. The current fill is optimal (CP-SAT, matching bound). Projected kernels: 91 runs, none feasible. |
| Narrowing a width-9 helper (the entrance rule) | r6/A, B, C, F, H, K; r7/T, U | A valid narrowed owner map exists (C: PR1319 checks pass, about +8.4e-8 κ per helper), but no construction zeroes a helper's entrance response once narrowed: copies, re-routing, joint search, recipe and generator variants all fail. The generator is reproduced byte-for-byte (T), and the factory admits no zero-response helper (U). |
| Deeper and other kernels | r6/D, E, G, I, M, N, Q | Depth-2 keys, 3–4 repair rounds, A-section inserts, large-deletion censuses on A and B, and block deletions: no profitable kernel. Superadditive port-delivery pairs (B1407–1408 jointly −49,210) are settled infeasible apart from 24 neutral compensations. |
| Rewrites, swaps, variants | r6/O, P, R, S | Peephole rewrites of 2–5 B gates and 2–4 A gates, same-inventory width swaps, and all 45 extra-word interfaces: best Δ = 0. |
| Hosting geometry; parent; outer ceiling | r6/L; r7/V, W, X | Idle is already as concentrated as possible. The pair-2 octet merge needs a new parent algorithm, at most +6.6e-7. κ ≤ q is not a general theorem (W), but the complex leaf cannot be done by the bit primitive (X), so κ < C holds for this algorithm family. |

## Corrections and side findings

- **Oracle artifact.** #1957's per-insert cost oracle returns 2^60 for some cone-valid inserts, because it measures against
  the deleted word's re-solved frames. That produced #2142's "shape-infeasible" verdicts for B822/B840/B858/B876. With the
  sentinels re-priced exactly, all four are proven infeasible (r6/I, with HiGHS confirming), so #2142's conclusion stands
  on a correct basis.
- **Auditor gap.** `audit_local.py` does not frame-check non-centre cut gates (r6/B). The guard is filed as
  [PR #2478](https://github.com/CrocSwap/integer-mult-bounds/pull/2478).
- **Scale.** Total rank mass is fixed by the rank deficit, so gains are concavity effects. Removing the extra word is
  worth about +6.6e-7 κ, not the 1e-4 an early brief assumed.

## What is left

- **Factory redesign:** a new packet with one copy fewer, a re-solved K-triangle schedule and LeaverSAT cells. Most
  downstream searches are not vendored (r7/Y), so about 1–2 weeks of re-implementation. The payoff is at most about
  +8.4e-8 κ per narrowed helper.
- **New parent algorithm:** at most +6.6e-7 κ.
- **A different multiplication algorithm** whose leaves are not complex-network kernels (r7/X).

## Layout

The folders mirror the round directories: `r4/agents/*`, `r5/agents/*`, `r6/agents/*`, `r7/agents/*`. Inputs are as in
round 3 (`INPUTS.json`). Local paths were rewritten relative to the round scratch root. Toolkit copies, scratch work, fetched
upstream sources, edited word dumps and files over 512 KB are omitted; r7/U's 59k variant outputs are reduced to their
summaries.

## Credit

Rohan Arun (#1957, #1319/#1297), Ian Libânio (#2142), Jeremy Kothe / LeverRank (#1672), icekylinx (gauge44-frames-x and
its auditor), Vlado Vojdanovski (PR1673 outer), chafreaky / Tim Trudgian (PR1786), and the k8/PR635/PR987/PR1148 lineage.
See `NOTICE.md`.

Prepared by Marius-Paul Dumitrean with substantial AI assistance (Anthropic Claude, via Claude Code). Apache-2.0.
