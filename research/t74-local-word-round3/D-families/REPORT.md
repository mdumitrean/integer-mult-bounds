# r3 / D-families: exact edit families outside prior scopes on the 566+554 words

Agent D-families (round r3, 2026-10-15 00:05Z start). Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz`
(#1672 blobs 76c01583 / e86142b3). Toolkit: our #1186 rev3 harness (`toolkit-rev3`), b = 0.001679754956125544
(base cost 11,683,290,250; profile {1:2348, 2:500, 3:416, 4:130, 5:82}, certified). Local only: no commits, pushes or posts.

**Outcome: no gain on either word in any family (scoped negative result), plus one structural bound.**

## Families and results

### 1a. Compensated single-crossing re-timings (two-column moves), all B gates
Move g = (y += c s) across its first non-commuting gate h, forward or backward, with the one compensating gate the
adjacent-swap identity forces, placed next to h (W: h writes s; S: h scales s; R: h reads y; Y: h scales y):
forward W `y += -c c' u`, S `y += -c(l-1) s` (before h), R `z += c'' c s`, Y `y += (l-1) c s`; backward with the
opposite signs. Two placements of g (just past h; far end of the free interval). Exact by construction; the harness
screen (static rules, B+tail map mod p, unchanged derived compensation) re-checks every candidate.
This is outside #1957 (4,461 commuting moves only) and round 2 (commuting pre-edits only).
- 4,824 candidates (FW 1,468, BW 1,386, FR 1,196, BR 662, FY 112) on BASE: 3,804 frame-infeasible, 892 exactly
  neutral (delta 0), 127 positive (+4,925 x82, +6,781 x45, +7,984 x1), 1 uncertified (+6,781). **0 gains.**
- By moved-gate class: delivery reads P+=H 1,510 (1,254 infeasible, 228 neutral, 28 positive); data mixes 768
  (587 / 149 / 32); port butterflies P+=P 320 (181 / 139 / 0); helper-helper 2,226 (1,782 / 376 / 69).
- EXTRA (which differs from BASE only in the start frames of 627/629/630/631 and stored frames of B397-B408): all
  1,020 base-feasible moves give identical results (892 neutral, 127 positive, 1 uncertified); the 109 base-infeasible
  moves touching those four registers are infeasible on EXTRA too. **0 gains.**

### 1b. Two-column edits for the never-written copy-window pivots (TASK.json open question 2)
Pivots: 439, 444 (deletion screen -67,933), 438 (-62,305) and 226/228/230/231/232/236/238/434/436/446 (-51,636).
Stage 1 = an exact compensated re-timing of a gate writing a port (or the copy register) in q's column, frame-feasible
on its own; stage 2 = round-2 agent H's PFS solver (delete q's B reads, all or one; re-deliver with <= 4 exact dyadic
q-reads in B or the tail plus free cleanup prepends on FULL-end coordinates; joint frame screen), composed into one edit.
- Single-crossing pre-edits: 13,704 composed candidates; 272 without pre-edit (PFS rerun on the new words) and 697 whose
  q-compensation exists only after the pre-edit (178 distinct). All 969 priced on BASE: **ok, delta 0** (no gain).
- Multi-crossing pre-edits (2-3 crossings, one compensation each; invariant y_trans = y_orig -/+ c s_current), for
  gates writing the 60 ports of these columns: 1,736 moves, 1,632 infeasible, 94 neutral, 10 at +4,925. TASK.json's
  own first step, B518 `190 += 74` past B843 with `190 += 554` and `190 += -381`, is frame-infeasible in every
  placement. Feasible ones as pre-edits open 39 new q-compensations: all **ok, delta 0**.
- EXTRA: all 1,008 two-stage candidates (969 + 39) price **ok, delta 0** as well.

### Structural bound (information-flow frame cap), all copy-window pivots
Within the harness's edit model (B / early-tail / prepend edits; A, cut, compensation untouched) the B+tail map is
unchanged and prepends may not touch ports or low helpers, so q's column on those coordinates must still be delivered
through B/tail meets. Frames are monotone along chains and every vertex of a port y lies in perp(p_y) (low helper:
helper_final); following any meet path from q to y gives: **q's A-end frame lies in K(q) = the intersection of the end
frames of the ports/low helpers in q's B+tail column**, for every exact edit (the 8 ports of each column give dim K = 4).
`capscreen.py` prices the uncompensated deletion with q's A-end frame capped at K(q) (cap on q's last A vertex only):
- control: the base word with the same cap costs exactly 0 for all 23 pivots (the base satisfies the bound);
- all 13 copy-window pivots: the cap removes **exactly 10,821 units/call** of the screen (439/444: -67,933 -> -57,112;
  438: -62,305 -> -51,484; the ten: -51,636 -> -40,815). That part (A-section merges needing vectors outside K,
  e.g. {289, 161, 6} for 439/444) is unrealizable by any exact edit, whatever is re-timed: K is fixed by the map.
- group D (-44,073; no copy window): the cap costs 0; their screens are not reduced by this bound.
- EXTRA gives identical numbers for all 23 pivots (`out/CAPSCREEN-extra.json`).
Scale: one -1,850 kernel on both words is about +4.1e-8 kappa, so the ruled-out 10,821 units/call is about 2.4e-7
kappa per pivot; the optimistic remainder (-40,815 .. -57,112) is about 0.9-1.3e-6 kappa per pivot.
The rest of each screen (-40,815 .. -57,112) is an optimistic relaxation; every exact feasible re-delivery found so far
(here and in round 2) prices at exactly 0.

### 2. Delivery reads and data butterflies (#2142's excluded classes)
- Re-timings: covered by 1a (delivery reads, data mixes and the P+=P port butterflies are all moved gates there).
- Merges: 165 repeated (t, s) pairs in B+tail; **0 exactly mergeable** (each pair is separated by a read of t or a
  write of s). Port butterflies (y' += y; y += -1/2 y'; y *= -2) realize a fixed non-triangular 2x2 map, so no gate of
  one can be deleted without changing the map, and they are what fixes K(q) above (both ports of each pair are in q's
  column); re-timing them cannot change K.
- Compensated deletions of delivery reads of never-written pivots = family 1b (PFS); of written helpers = the kernel
  searches (agents A/B).

### 3. Cleanup-side corrections
- B -> cleanup-prepend relocation (frame-free): a B or tail gate on FULL-end registers whose target is never read and
  source never written later in B+tail. **0 candidates** on both words: of 1,853 B gates, 1,083 touch a port or low
  end, 292 have a later read of the target, 478 have both a later read and a later write; all 121 tail gates touch a
  port or low end.
- Tail placements of q-reads and free prepends on FULL-end coordinates are inside PFS (1b): all neutral.

## Runtime
00:05Z-01:05Z. Pricing: 4,824 + 1,020 + 1,736 + 969 + 39 + 1,117 = 9,705 harness evaluations (3 workers, ~0.4-1.2 s
each; peak worker RSS ~0.2 GB), plus 46 capped screens and 2 cap traces.

## Best next step
The copy-window screens left after the cap are B-section merges, and every exact feasible re-delivery found here or in
round 2 prices at exactly 0. Two concrete continuations:
1. A delivery-forced relaxation: price the deleted word with a disjunctive constraint that q meets each port chain of
   its column at some B/tail position (q's frame at that meet inside that chain's U). If it equals the base cost for a
   pivot, that pivot is closed for every B/tail edit; otherwise its optimum names the slot to build.
2. Edits in the A section (outside the harness's B/tail model) are the only way to change K(q): K is fixed by which
   ports q's B+tail column must reach, so re-routing q's contribution before B is the one lever this bound leaves open.

## Evidence (all in this directory)
- scripts/: gen_cmove.py, gen_cmove_multi.py, runner.py (3 workers, per-task deadline, 6 GiB RSS watchdog,
  maxtasksperchild), twostage.py, captrace.py, capscreen.py (+ frames_x.py: private copy of toolkit frames.py with an
  A-end-only cap hook), gen_relocate.py, r2h/ (round-2 agent H PFS code, adapted to rev3 and these words).
- out/CMOVE-cands.json + CMOVE-base.jsonl, CMOVE-extra-ok.jsonl; out/CMULTI-cands.json + CMULTI-base.jsonl;
  out/TS-cands.json (+summary), TS-prio.json + TS-base.jsonl; out/TSM-cands.json, TSM-prio.json + TSM-base.jsonl;
  out/EXTRA-batch.json + EXTRA-batch.jsonl; out/CAPTRACE-BASE.json, CAPSCREEN-base.json; out/RELOC-why.txt; SUMMARY.json.
