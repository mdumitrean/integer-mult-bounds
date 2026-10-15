# r5 / B-cut: can priced work move into the cut or the precondition? (scoped negative, no κ change)

Round r5, 2026-10-15 ~03:03–03:20Z. Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz` (#1672 blobs 76c01583 /
e86142b3). Toolkit: #1186 rev3 (`r3/toolkit-rev3`), b = 0.001679754956125544. Local only: no commits, pushes or posts.
Every result below is identical on the two words.

**Outcome: no gain.** The cut is already at its minimum frame price, no B delivery or set of B deliveries can be replaced
by free cut gates, and the precondition is free only for zero-frame registers, where every gate is already free in place.
The only priced candidates (32 butterfly conjugations per word) are all frame-infeasible.

## 1. What the three sections are

| Section | Contents in these words | How it is priced | What enforces it |
|---|---|---|---|
| precondition | 192 target-only gates (136 adds, 56 scales) | frame-free: emitted at frame 0 | auditor: frames `[]`, no entering or cold-end helper; native `hpe_emit_local.py` phase `zero_frame_precondition` asserts every touched register has start frame 0 |
| compensation | derived (7,208 gates): target += helper | frame-free, same phase as the precondition | auditor and native chain re-derive it (r4 C) |
| cut | 176 gates `target += ±1/4·centre`; 8 centres (data 23, 31, 60, 61, 63; helpers 224, 240, 256), each with an 8-dimensional centre frame; 88 targets served, each by 2 centres of one group ({60,61,63,224} or {31,240,23,256}); `target_levels` empty | not in the priced frame graph; the price is the constant centre descents: per centre, rank dim(centre frame) − dim(lowest served target level), here 8 each, i.e. the profile's `8: 8` = 64 rank units/call | auditor: targets sit exactly at their levels and centres at their centre frames when B starts (cut equality); descent path nested; 8 distinct centres with frames pinned to the parent interface (`check_parent_interface`, `--main`). Native centre phase: copy the centre to a private stream at its frame, emit the paid descents, scatter the adds into the targets at their levels (frame 0), clear the stream. |

The precondition is exactly the inverse of B's 192 target-only mixing gates (34 butterfly groups): `precondition ∘ mixing = I`
on the targets (`out/PRECOND-*.json`). It makes B's mixing invisible to the targets' initial values. The cut gates are free in
frames, but each scatter add still counts native primitives (finite-invoice inputs).

## 2. Cut: the frame price is minimal and nothing can move into it
- **Centre descents cannot shrink.** A centre's descent ends at its lowest served target level L. The levels form a nested
  chain and each target's level lies in its end hyperplane perp(p_t), so L ⊆ C_c ∩ (∩ perp(p_t) over its 22 targets). That
  intersection is {0} for all 8 centres (`scripts/levels.py`), so every descent is a full rank 8. Nonzero levels would only
  split descents into more jumps.
- **Centres are untouched in B** (0 reads, 0 writes). A B delivery from a centre would need a frame containing C_c inside
  perp(p_t). Both are 8-dimensional, so C_c would have to equal perp(p_t), which is impossible for all 22 targets of a centre.
  So a centre's descent can never be dropped by delivering it in B.
- **No B delivery lies in the cut's span.** 921 B gates write targets, 785 of them from non-targets. None of the 785 source
  values lies in span(centre values at the cut) plus ordinary-helper coordinates, which the re-derived compensation absorbs
  (`scripts/cutspan.py`, exact rationals).
- **No set of B deliveries can be replaced either.** Cut gates can add any element of R^targets ⊗ span(centres) for free.
  So a set S of deliveries is replaceable iff Σ_S a_g · m_g ⊗ [v_g] = 0, where m_g is e_t pushed through every later
  target-only gate and [v_g] is the source value modulo the free span. The 785 tensors have full rank 785 mod 2^61−1
  (`scripts/cutrank.py`). Full mod-p rank implies full rational rank, so no subset of any size is replaceable. Self-test:
  an injected scaled duplicate and an injected two-term combination are both detected.

## 3. Precondition: free only where gates are already free
- Legitimately free means frame 0. The native emitter asserts zero start frames for every precondition and compensation
  register, and frames only grow, so a gate can run "in the precondition" only if both its registers are still at frame 0.
  That is exactly a frame-0 gate in place. A already has 1,182 such gates; B has none.
- **Moving A gates there:** 0 candidates. Of the 2,269 A gates with a nonzero frame, 1,354 touch a register that starts
  above frame 0 (data, or entering helpers). The other 915 cannot commute back past every nonzero-frame event on their
  registers (`scripts/afront.py`).
- **Moving B gates there:** 0 candidates. 1,641 involve a register already above frame 0 when B starts. The other 212
  cannot commute back far enough (`scripts/bfront.py`).
- **B mixing:** none of the 192 target-only gates commutes back to the start of B, where targets are still at frame 0. 77
  are blocked by a delivery and 115 by another gate of their own group (`scripts/mixback.py`).
- **Butterfly conjugation, the one priced family.** A simple butterfly (y' += y; y += −½y'; y *= −2) is the map
  (y, y') ↦ (y' − y, y + y'). Moving it to the start of B makes it free there, but every earlier delivery into y or y'
  must be replaced by its conjugate (into y: y −= a·s, y' += a·s; into y': y += a·s, y' += a·s).
  - All 32 simple butterflies were priced on both words with the unchanged harness: exact-map screen, unchanged
    compensation, recomputed caps (`scripts/price_bfly.py`). They cross 5–17 deliveries each.
  - Result: 32/32 frame-infeasible on both words ("L not inside U at mutable vertex"). Each conjugate delivers the source
    into both targets of the pair, which the frames cannot nest.
  - The 8-target and 40-target groups cross 13–89 deliveries and were not built.

## Soundness and rules
No harness rule was relaxed. The only priced edits are the conjugated butterflies. They are exact by construction, and the
harness re-checked each one (static rules, B+tail map mod p, unchanged derived compensation) before the frame solver
rejected it. No candidate reached a negative delta, so there was nothing to send to `audit_local.py` or the native chain,
and no hosting quantity changes. The rank and span statements are exact (rational values; mod-p rank with self-test).

## Best next step (outside this lane)
The cut and precondition are closed for these words. The cut's frame price is fixed by the pinned 8-centre interface and
the targets' end hyperplanes, and the precondition adds no freedom beyond frame-0 gates. A lever here would need different
centre values, i.e. a redesign of the A section that computes the centres, which is a new word construction rather than an
edit. Within the local words, the remaining open directions are r5's other lanes (solver-vs-auditor slack,
compensation-aware split-key kernels) and the hosting packing.

## Evidence
- `EVIDENCE.json`: all counts and results, per word.
- `out/CUTSPAN-*.json`, `out/CUTRANK-*.json`, `out/PRECOND-*.json`, `out/MIXBACK-*.json`, `out/BFLY-*.json`,
  `out/PRICE-BFLY-*.jsonl`, `out/AFRONT-*.json`, `out/BFRONT-*.json`.
- Scripts: `scripts/census.py`, `levels.py`, `cutspan.py`, `cutrank.py`, `precond.py`, `mixback.py`, `bfly.py`,
  `price_bfly.py`, `afront.py`, `bfront.py`.
- Runtime: about 20 minutes, at most 3 worker processes (pricing 10 s per word), peak memory well under 1 GiB.
