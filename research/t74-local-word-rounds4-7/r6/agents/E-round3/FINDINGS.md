# r6 E-round3: residual-repair kernels beyond two rounds (base word; no gain)

Written from the agent's final message: the subagent harness blocked its REPORT.md.

- **Calibration:** with r3's settings, rounds 1-2 reproduce r3 B "Lead 1" exactly on B1 and B783, matching its candidate
  counts, cone rejections, proposals and both INFEASIBLE verdicts.
- **Engine** (`tools/runjob3.py`): up to 4 rounds, with a summed budget and a per-insert cap equal to the remaining budget.
  Interaction is allowed in every round but the last, and every round uses the cone-aware filter. It adds
  merge-canonical cuts, a diagnosis of any empty round and, for B1, exact no-goods (r3's solution cut also excluded
  supersets).
- **Results:**
  - B1: 20 first-round proposals (no diversity cuts, exact no-goods); the second round is INFEASIBLE each time.
  - B3, B8, B39, B44: 2 proposals each; B783, B802: 1 each. The second round is INFEASIBLE every time.
  - No chain reached a third round.
- **Why:** the second round stays INFEASIBLE even with no summed budget and 24 terms. With the per-insert cap removed,
  repairs exist but cost exactly the deletion gain (4,925 or 6,781): they re-deliver the deleted value in halves, for
  example B1: `126 += 1/2*74`, `126 += 1/2*554`.
- **Not a proof for B1:** its enumeration hit the 20-proposal cap. No exact candidate arose, so nothing was priced.
- **Evidence:** `SUMMARY.json` (11 run/target records), `runs/{cal,b1x,b78,diag,early,early2}/`, `tools/`.
