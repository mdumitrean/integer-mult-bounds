# r6 / A-zero478: making a width-9 narrowing auditor-valid (helpers 478, 479, 490, 491)

Agent A-zero478, round r6 (2026-10-15, 03:35–04:05Z). Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz`. Toolkit rev3
(copy in `toolkit/`), b = 0.001679754956125544, unchanged auditor `r3/main/research/gauge44-frames-x/independent/audit_local.py --main`.
Local only: nothing committed, pushed or posted.

**Outcome: blocked, κ unchanged.** The entrance response of each of the four helpers can be zeroed exactly and for free
while the helper is unnarrowed, but once the helper enters at its start vector, every cancelling construction is
frame-infeasible.

## 1. The entrance rule (audit_local.py)
- *Entering* = keys of `start_extra`; *cold end* = `helper_final` minus entering.
- The compensation is derived from the A+cut+B map: for each target row y (112–223) and helper k, the coefficient of k's
  initial value (after applying the precondition's row operations) is cancelled by a frame-free gate `y -= a·k`.
- The rule fails ("nonzero entrance response") if any compensation gate reads an entering helper. Precondition and
  compensation also may not touch entering or cold-end helpers. Targets must sit at their (empty) centre levels when B
  starts, so no A gate can touch a target.
- So narrowing q to (8,1,9) is legal only if q's initial value reaches no target in the A+cut+B map.

## 2. Where the four helpers leak (`scripts/leaks.py`, `scripts/qlife.py`, `out/LEAKS-*.json`)
- Each is first written in A as the pre-cancel partner of an entering helper: 478 −= 526 (A1219), 479 −= 527 (A1220),
  490 −= 538 (A1231), 491 −= 539 (A1232), where 526/527 enter at [96] and 538/539 at [102]. Their narrowing vectors are
  96 (478, 479) and 102 (490, 491).
- Each leaks with coefficient 1 into four of the targets 200–207, through the late-B delivery butterflies (for 478:
  B1149 680 += q, B1757–B1760 with 514, B1775–B1776 via 680/687; 203 reads q directly at B1759).
- Targets 200–207 receive the dirt of two frame clusters: {478, 479, 514, 515} (first frames [96]) and
  {490, 491, 502, 503} (first frames [102]). Identities: L478 + L479 = L490 + L491 (= all ones), L514 + L515 = L502 + L503.

## 3. Construction: cancelling copies
q's value is pure q_init only before its first write (in A), and targets cannot be touched in A. So the only exact way to
zero its response is to copy ±q_init into holders c while q is pure (`c += k·q`), chosen so that Σ k·L_c = −L_q, and to
remove the copies at the end of the frame-free cleanup (`c −= k·q`, q restored by then). Every candidate's whole call map
is checked by the unchanged auditor (`scripts/build.py`).
- **Unnarrowed, it is free and exact.** With copies at A0 (all registers still at frame ()), e.g. 478: 479 += q, 490 −= q,
  491 −= q: Δ = 0, the re-derived compensation drops from 7,208 to 7,204 gates and no longer reads q, `audit_local.py --main`
  PASS. Same for 479, 490, 491 on the base word, and for 478 and 490 on the extra word (`out/words/*copies-only*`).
- **Narrowed, every solution needs the other cluster.** −L_q is not in the span of q's own cluster; all 50 exact
  combinations with |k| ≤ 2 (and all with |k| ≤ 3) use at least one holder from the other cluster.
- With q entering at [96] (or [102]), every gate reading q has frame ⊇ the start vector, so a cross-cluster holder carries
  96 (resp. 102) from the copy onward. Those holders' frames contain the vector only from B1039–B1044, and the
  contamination spreads through their partners to chains whose upper frames exclude it.

## 4. Pricing (exact optimal frames, compensation and cone caps re-derived)
| Variant | Count | Result |
|---|---:|---|
| Narrowing alone (calibration, r5 C) | 1 per word | Δ = −2,116,454; auditor: nonzero entrance response |
| Narrowed + the 6 minimal exact copy sets, per helper | 24 | all infeasible: "L not inside U at mutable vertex" at B1692/B1720/B1724/B1752/B1756 |
| Narrowed + one cross-cluster copy (478: 490/491/502/503; 490: 478/479/514/515) | 8 | all infeasible (B1688–B1756) |
| Narrowed + one same-cluster copy (478: 479/514/515; 490: 491/502/503) | 6 | Δ = −2,116,454 but entrance response nonzero (not exact) |
| Extra word: narrowed minimal sets for 478 and 490, single cross copy | 3 | infeasible (B1692) |

Since every exact cancellation contains a cross-cluster copy and every cross-cluster copy alone is frame-infeasible, no
exact narrowed word exists in this copy family. Net value: none; the break-even (narrowing saving − ~17k) is not reached.

## 5. Next step
The obstruction is the start vector reaching the other cluster's chains before they naturally contain it (B1039+). A
cheap global check: for each of the 117 frame-feasible width-9 helpers, test whether −L_q lies in the span of the leaks of
holders that are frame-compatible with q's start vector (frame () or [u] at the copy, next frame containing u); only those
helpers can be unblocked by free copies (`scripts/multiholder.py` does this per helper in seconds). This overlaps agent
B-zero502's helpers, so it was not run here.

## 6. Follow-up: free-copy screen of all 117 narrowable width-9 helpers (`scripts/screen117.py`)
For every frame-feasible (8,1,9) narrowing (q, u) in r5 C's `NARROW-base.jsonl` (153 pairs, 117 helpers; 104 save the
full c1 = 2,116,454), on both words: holders = every register except targets, cold ends and q (data, ordinary and
entering helpers). A holder can take a copy at any position t ≤ q's first write where its frame is () or [u] and all its
later frames contain u (otherwise the copy contaminates its chain with u). Each distinct transfer P_c(t) is a column;
the pair passes if −L_q lies in their span (exact rational elimination, free holders first).
- **Result: 0 of 153 pairs pass, free or with splits, on either word** (full-c1: 0 of 104). Compatible holder sets are
  small (mostly 2–3 options; 11 for 478/490).
- **Positive control:** with unnarrowed holders at A0 the same elimination recovers 478's known cancellation
  {479: +1, 490: −1, 491: −1}.
- So no narrowing is unblocked by free copies; nothing was built. The frame-compatible holders always lie in q's own
  frame cluster, whose span excludes L_q.
Evidence: `out/SCREEN117-base.json`, `out/SCREEN117-extra.json` (per pair: leak size, holder options, pass flags,
saving, full-c1 flag).

## Evidence
`EVIDENCE.json` (summary); `out/LEAKS-base.json`, `out/LEAKS-cluster.json`, `out/QLIFE.json`, `out/COLSEARCH-478.json`,
`out/MULTI-{478,490}.json`, `out/{NARROW,SINGLE,EXTRA}-JOBS.jsonl`, `out/words/` (priced variants, audited words and receipts);
scripts `leaks.py`, `qlife.py`, `traj.py`, `holders.py`, `colsearch.py`, `multiholder.py`, `build.py`, `driver.py`
(≤ 3 processes, 900 s timeout, 6 GiB RSS cap). Peak RSS well under 1 GiB.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
