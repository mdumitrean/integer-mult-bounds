# r7 / U-factory: feasibility probe for a factory redesign that makes one more full-c1 width-9 helper entering

Agent U-factory, round r7 (2026-10-15, from 10:51Z). Local only: nothing committed, pushed or posted. Upstream sources are
read-only copies of r7 T-generator's `src/` (main 17ce0c79 subtrees, PR635 a6895a69, PR1148, main 0fdd7d82 gauge44-slots);
two opt-in hooks were added to my copy of `cgx_leaver.py` (carrier order `regorder`, partition `select`), default behaviour
unchanged (the baseline still reproduces the pinned word).

**Verdict: (b) blocked at the factory level.** None of the factory's dirt-routing knobs zeroes the target response of any
full-c1 width-9 helper: 2,192 factory variants, 1,736 of them valid, and in every valid variant the number of zero-response
helpers stays the same or drops; no full-c1 helper ever reaches zero response. The structural reason is below.

## 1. Setup and calibration
- `scripts/resp.py`: exact target-response analysis (helper columns of the target rows of the A+cut+B map after the
  precondition = what the derived compensation reads). Current base word: 240 read, 192 entering, 78 ended; the k8
  ancestor (T's `lvc/frames`) has **identical** read/entering/ended sets, so helper indices are preserved from k8 to today.
  The leaver cell word differs only by 6 pivot-swapped entrances and 24 later cold ends; all 104 full-c1 helpers are
  already compensation-read there (`out/RESP-*.json`, `out/FULL-C1.json`).
- `scripts/vleaver.py`: the k8 leaver cell-word pipeline (reproduce_leaver.py steps 1-5: gauge-forward = cgx_leaver.py,
  port0-3, regroup, HPE, cold44) for an XPARAM variant, without pins. **Baseline reproduces the pinned cold44 word
  `58e14a02...` exactly** (pairing ranks [0,0,0,4,4,4,4,4,4,4,4,0,0,0]), 2.4 s per variant.
- Factory numbering: block b owns copy helpers 224+16b .. 224+16b+15 (source position j's copies are 224+16b+2j, +2j+1).
  Full-c1 helpers 224-271 and 400-447 are copy helpers of blocks 0-2 and 11-13 (pairing rank 0 in k8); 460-570 are extras.

## 2. Degrees of freedom and screens (`scripts/batch.py`, `scripts/summ.py`, `out/SUMMARY-*.json`)
| Knob (CONSTRUCTION.md) | Variants | Valid | Read-set size in valid variants | New zero-response helpers |
|---|---:|---:|---|---|
| A. source/copy exchanges at event 15: every single change (14 blocks x 8 positions x {none, copy1, copy2}) + none/first-copy per block | 252 | 108 | 256 in all 108 | 0 |
| A. all pairwise exchange changes in the six free blocks 0,1,2,11,12,13 | 672 | 672 | 256 in all | 0 |
| B. complement-basis priority: 50 four-row completions per block | 700 | 700 | 256-260 (354 at 256) | 0 (rank sum 28-32: only loses cold directions) |
| C. carrier order of the retired registers: 40 permutations per block | 560 | 256 | 256 in all | 15 trades in cold blocks 3-10 (one cold helper replaces another, e.g. 272 for 282); never a full-c1 helper |
| SELECT partition choice: all 8 alternatives | 8 | 0 | - | factory invariant `len(early)==8` fails |
- Exchanges in cold blocks 3-10 are locked: every change drops the cold44 pairing rank (e.g. r = 3 of 4) - CONSTRUCTION.md's
  point that the exchanges are what give K dimension four.
- No valid variant gives an entering helper a target response, so all port-stage promotions stay legal.

## 3. Why (structural)
- Within each source's equal-frame triple (source x_j and its two copies, frame (P_j,)), the targets read both copies'
  dirt independently: **all 48 copy pairs of the free blocks have response rank 2** (they cover 78 full-c1 helpers;
  `out/COPY-PAIR-RANKS.json`). Every frame-free re-routing inside the triple (exchange, carrier placement, transvection) is
  an invertible change of those two directions, so both still leak; a zero-response copy is reachable only by a
  non-invertible overwrite (T's mu = 1 result).
- Each free block's 16 copy helpers have response rank 12, so zero-response directions exist (4 per block), but they mix
  copies of different sources (different frames). Realising one needs reads of the narrowed helper q at frame zero
  (illegal once q has start frame [u]) or by registers whose frames do not contain u (a frame climb, ~2.1e6 units/call
  against the 3,728 budget). The word-level screens of r6/r7 (A, B, F, H, T) cover the later-time partners.
- So a zero-response copy helper requires a packet design whose targets read one copy difference fewer, i.e. one copy
  fewer: a change to the frozen PACKET-PROGRAMS / K-triangle schedule (CP-SAT output) and LeaverSAT cells, not a factory
  knob.

## 4. Downstream plan if such a packet redesign were made (code availability, cost)
- factory .. cold44: re-runnable here, ~2.4 s per variant.
- leaver chain (`reproduce_leaver_chain.py`, ~260 s per pass, mostly layer-end controls): builders plus frozen recipes.
  HPE greedy re-derivable; frames re-derivable with our #1186 toolkit; `promo/make_recipe.py` present; NP/p6n layer search
  (LeaverSAT) and U8 hybrid search are **not vendored**.
- slots: frozen PR987 slot-search output (only `verify_slots.py`).
- PR1148 eight-ends / three-demotions / joint-entrances: search code vendored (`discovery/search_*.py`); their logs show
  HiGHS solves hitting 180 s limits.
- #1193 FOUR and #1297: recipes and builders (r6 K reproduced them); #1297 `search_relations.py` vendored.
- #1319 T74 owners: `reconstruct.py` moves only width-4/5 roles; no general exact-fill constructor (r6 C-hosting built a
  one-helper min-change map). #1625 kernel search ours; #1672 has EDITS only.
- strict T74 replay (~13 min) and the outer on the #2220 line (1e-60000 recertification, hours).
- Estimated cost: days, dominated by a new packet/cell design and re-implementing the LeaverSAT layer and slot searches.

## Evidence
`EVIDENCE.json`; `out/RESP-*.json`, `out/FULL-C1.json`, `out/COPY-PAIR-RANKS.json`, `out/SUMMARY-{A1,A2,B,C,S}.json`,
`out/JOBS-*.json`, per-variant `out/{A1,A2,B,C,S}/v-*/RESULT.json`; scripts `scripts/{resp,vleaver,batch,summ}.py`.
Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).

## 5. Next stage: the "one copy fewer" packet, built concretely (2026-10-15 ~11:30-11:55Z)
Hooks in my copy of `cgx_leaver.py` (all opt-in; the baseline still reproduces `58e14a02...`): `drop` removes one copy from
a block's packet program. The copy stays allocated and is never touched, so it has zero response by construction and no
later index shifts. Three modes: `twin` (its events use the twin copy), `source` (they use the source register) and `omit`
(events touching it become no-ops). `sidedump`/`sidefix` dump or patch the targets' clean values at the factory's
side-identity check.

**All 288 variants (6 free blocks x 16 copies x 3 modes) fail in the factory itself (gauge-forward); no stage after it is
reached.** The pattern is the same in all six blocks (`out/DROP-FAILURES.json`):
- `twin` / `source` (192): frame violation. The substitute register has already climbed to its own role's frame and
  cannot take the dropped copy's role.
- `omit` (96):
  - basis copies 8, 9, 11, 13, 14, 18 lose the retired span (no pivot in the basis replacement);
  - leaver-source copies 17, 19, 21, 23 leave a target without its own row;
  - face-packet copies 10, 12, 15, 16, 20, 22 break the clean map: 16 targets each lose one four-source face packet,
    e.g. -1/2 (x64 + x65 + x68 + x69) for helper 226.
- **Repair attempt** for the six face-packet omissions in block 0 (`scripts/repair.py`, `out/side/REPAIR2-*.json`):
  extra B reads of non-entering registers (never the dropped helper) with the frame union inside each target's
  hyperplane, solved jointly in exact rationals. **0 of 16 damaged targets repairable** for every copy (8-14 legal
  candidate registers per target; their clean values never span the missing packet).

So every copy in the packet carries a value something downstream consumes, with frames that admit no substitute. A
packet with one copy fewer needs a new packet program, which means a re-solved K-triangle schedule and LeaverSAT cells.
Those are frozen CP-SAT outputs with no search code vendored. The downstream re-application test (step 2) was not
reached, because no valid modified word exists.
