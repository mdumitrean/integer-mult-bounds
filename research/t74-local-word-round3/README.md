# T74 566+554 supplier: round-3 local-word searches (no new κ)

**Status:** FINDING · 2026-10-15 01:45Z · priority revision 4 (main `0fdd7d82`). Author-checked local replays; not maintainer-reviewed; not a PR.
Follows Ian Libânio's handoff [#2143](https://github.com/CrocSwap/integer-mult-bounds/discussions/2143) (items 1–3).

**Question.** Can an exact local edit make the pivot-566+554 T74 supplier's words cheaper? These are PR #1672's gauge44 and
extra words (249 and 417 calls), which #2044, #2161 and #2180 use. In those PR1673-outer claims κ sits within 1e-10010 of this
supplier's complex endpoint, so only such an edit raises κ. One helper-donor kernel (−1,850 units per call on both words) is
worth about +4.1e-8.

**Common premise** of every search here, and of #1957 and #2142: edits only in B, the early-cleanup tail and the cleanup
prepend; A, the cut and the derived compensation unchanged; PR #1186's exact frame model (cone caps, tail-mutable frames,
cut equality), priced at b = 0.001679754956125544.

## Results: no exact profitable edit

| Folder | Search | Exact candidates | Outcome |
|---|---|---:|---|
| `A-extra` | Kernels on the extra word (#2143 item 2) | 1,797 B + 3,451 A deletion relaxations; #2142's 108 models rebuilt; 92 relocations; 5 multi-deletion CP-SAT runs | The extra word is the base word's program up to 12 B frames and 4 start ranks, so #2142's 104 infeasibility proofs carry over. No kernel. |
| `B-interact` | Second-order kernels: interacting inserts with residual repair, multi-deletion, recursive keys (#2143 items 1, 3) | 25 deletion sets (21 single, 4 pairs) over two rounds; then 7 targets rerun with a cone-cap filter | No kernel. Round 1 is proven infeasible for most targets, including the four −6,118 reads (shape-feasible with wider holders). B783/B802's zero-cost cores cannot be repaired within 12 inserts. The early −4,925 reads have 16 map-exact second-order words, all killed by cone caps; with a cone-cap filter (no false rejections on known feasible inserts), every repair is proven infeasible. |
| `C-repair` | The #1186 toolkit's fusions, read-set exchanges and triangle hybrids | 6,081 distinct | All neutral (Δ = 0) or infeasible, identically on both words |
| `D-families` | Compensated non-commuting re-timings, two-column port re-timings of copy-window pivots, merges, cleanup moves | 9,705 | All neutral or infeasible |

No priced non-gain in C can hide a true gain above 2.9e-11 units (interval certificates).

**Structural bound (D).** For the 13 never-written copy-window pivots (439/444/438 and ten others), q's column must still
reach the 8 ports of its butterflies, and frames only grow along chains. So q's frame at the end of A lies in the intersection
of those ports' end frames (dimension 4), for every exact B/tail/prepend edit. Capping it there costs 0 on the unedited word
but removes exactly 10,821 units per call from each of these pivots' deletion screens, on both words. The rest of each screen
(−40,815 to −57,112) is only an optimistic relaxation; every exact feasible re-delivery found prices at exactly 0.

## Open next questions

- **A-section re-routing.** The bound leaves one lever for the copy-window pivots: change which ports q's B-and-tail
  column must reach, which means editing A and re-deriving the compensation (outside the common premise).
- **Delivery-forced relaxation.** Price the deleted word with q forced to meet each of its port chains. If that equals the
  base cost, the pivot is closed for every B/tail edit; otherwise the optimum names the slot to build.
- **Two-step neutral walk.** Apply each of C's 170 neutral fusion triples, then re-price the fusions and costly-read
  deletions that touch its registers.
- **Complete round-1 enumeration (B).** B's round-1 exhaustion uses diversity cuts, so it is heuristic. A run without them on one target would make it a proof within the model; three or more rounds are untested.

## Layout and reproduction

Each folder has `REPORT.md` (start there), a summary JSON and its scripts. The scripts expect the round layout:
`r3/inputs/{gauge44,extra}-word-566-554.json.gz` (pins in `INPUTS.json`), `r3/toolkit-rev3` (PR #1186 at `c37dfb07`),
`r3/vendor/{pr1957,pr2142,pr1672}` (heads in `INPUTS.json`) and `r3/main` (main `0fdd7d82`). Local absolute paths in logs
were rewritten to these names. Two large regenerable candidate lists are omitted (`D-families/out/TS-cands.json`,
`TSM-cands.json`); their summaries are kept. Python 3.14 with NumPy; CP-SAT runs need OR-Tools 9.15.

These are finite searches on two fixed words in one frame model, not a lower bound for the supplier.

## Credit

Rohan Arun (#1957: relaxation data, compensation search, vendored toolkit); Ian Libânio (#2142: split-key search and
results, reused as references and calibration); Jeremy Kothe / LeverRank (#1672: pivot-554 kernel and words); our #1625
pivot-566 kernel and #1186 toolkit; the #1319/#1297 lineage. See `NOTICE.md`.

Prepared by Marius-Paul Dumitrean with substantial AI assistance (Anthropic Claude, via Claude Code). Apache-2.0.
