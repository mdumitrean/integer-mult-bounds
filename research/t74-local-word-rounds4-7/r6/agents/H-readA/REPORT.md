# r6 / H-readA: width-9 narrowing for the helpers read in A (the 78 untested full-c1 pairs)

Agent H-readA, round r6 (2026-10-15, 04:29–05:31Z). Words `r3/inputs/{gauge44,extra}-word-566-554.json.gz`, toolkit rev3
(`r3/toolkit-rev3`, read-only), b = 0.001679754956125544. At most 2 worker processes, each with a timeout and a 6 GiB RSS
cap. Local only: nothing committed, pushed or posted.

**Outcome: blocked in every searched family; κ unchanged; no word reached pricing.** The width-9 narrowing lever
(+8.4e-8 κ with r6 C-hosting's owner map) has now been tested on all 104 full-c1 helpers: the 22 not read in A by r6 B/F,
and these 78 here.

## 1. The 78 pairs
- r5 C's `NARROW-base.jsonl` has 104 full-c1 (8,1,9) narrowings (Δ = −2,116,454), one start vector per helper. 78 helpers
  are read in A: 224–241, 245, 251, 253–257, 261, 267, 269–271 and 400–447 (`out/PAIRS-{base,extra}.json`).
- **No pure reads.** Every q is first written in A, and every A read of q comes after that write (1–13 A reads per helper).
  So no existing gate reads pure q0: reweighting existing reads cannot be a pure-dirt edit, and r6 B's in-B construction
  (q pure at the delivery slot) does not apply, because q's A-written value is read later in A.
- **The cut carries part of the leak.** For 62 of the 78, q0 reaches the cut centres (23, 31, 60, 61, 63, 224, 240, 256)
  by the end of A, so part of the leak enters the targets frame-free through the cut. Leaks reach 16–60 target rows.
- Re-timings alone cannot help: they keep the map, hence the leak.

## 2. Pure-copy family: closed for all 78 (sound, both words)
Only q holds pure q0, and only before its first write. Any exact copy construction (r6 A's family; also the pre-cancel
structure entering helpers like 506/518 have) copies ±q0 into holders c before that point and undoes them in the frame-free
cleanup. `scripts/cscreen.py` generalises r6 A's screen: a copy at insertion point p ≤ t0 is admissible iff the exact
single-insert cone test (r3 B `cone.py`: L_a ∨ L_c ⊆ U_b ∧ U_d ∧ caps) passes in the narrowed word, with frames re-solved,
a superset of A's "existing frames already contain u" holders. Inserting more gates only adds frame constraints, so an
inadmissible copy stays inadmissible in any larger edit: the screen is a necessary condition.
- **0 of 78 pass**, on both words, with the narrowed word's cone caps and with all cone caps removed (the loosest upper
  frames, so the verdict does not depend on how the final compensation changes the caps).
- At most 3 admissible copy columns per pair (rank ≤ 2) against leaks of 16–60 target rows.
- Without the frame test all 78 pass algebraically: the obstruction is frames, not algebra.
- **Cold-end completion** (`CSCREEN-COLD-NOCAPS-*`): r6 A's screen, and the first runs here, excluded cold-end holders
  without a rule requiring it. Adding all 78 cold ends (no caps) still gives 0 of 78 on both words: at most 5 admissible
  columns, rank ≤ 4. So the screen now covers every holder except the targets (untouchable in A) and q itself.

## 3. B/tail inserts, projected model
The narrowing is fed to r5 D-compsplit's projected split-key model (`pk/tools/run_h.py` on sk3.PRound) in place of a
deletion: q is entering, so its target-row column is not absorbable and must become exactly zero; every other
non-absorbable entry must stay exact; ordinary-helper dirt on target rows is absorbed by the re-derived compensation.
Inserts x += λ·y anywhere in B or the early tail (sk3's scope), keys = values held by or added into q and its readers,
≤ 12 inserts, quarter-step |λ| ≤ 4, cone-aware admission on the narrowed word, exactness and frame set-tests with lazy
cuts. The narrowed cost reproduces r5 C exactly (11,681,173,796 = base − 2,116,454).

| Helper | Leak rows | Budget (units/call) | Candidates | Result |
|---:|---:|---:|---:|---|
| 232 | 16 | 3,728 | 5,677 | INFEASIBLE |
| 231 | 16 | 3,728 | 5,736 | INFEASIBLE |
| 236 | 16 | 3,728 | 5,735 | INFEASIBLE |
| 404 | 16 | 3,728 | 3,589 | INFEASIBLE |
| 407 | 16 | 3,728 | 3,685 | INFEASIBLE |
| 228 | 16 | 2,000,000 | 7,303 | INFEASIBLE |
| 232 | 16 | 2,000,000 | 5,884 | INFEASIBLE |
| 225 | 45 | 3,728 | 32,674 | shape-infeasible (target outside the candidates' span) |
| 240 | 21 | 3,728 | — | timed out at 1,200 s, no verdict |

The 2,000,000 budget admits every insert that does not need an extra rank level. A construction that does costs at least
c1 = 2,116,454 and erases the narrowing saving, so those two runs cover every net-positive construction in this model.
Not run for lack of time: the other 69 helpers, including all with 37 or 60 leak rows; sk3's candidate generation grows
fast with the leak (helper 225: 17 minutes).

## 4. What remains untested
- A-section inserts that read non-pure q-derived values (q after its first write, q's A readers, the centres) and cancel
  their data content inside A. sk3 places no A inserts; targets cannot be touched in A, and the cut is off limits (r6 B's
  auditor gap: non-centre cut reads pass `audit_local.py` but fail the native chain).
- More than one round of interacting inserts beyond sk3's lazy interaction cuts.
- A generator-level redesign, as r6 B noted: the pre-cancel structure that existing entering helpers get from the word
  construction, with frames designed around it.

## Evidence
`EVIDENCE.json` (summary); `out/PAIRS-{base,extra}.json`, `out/CSCREEN-{base,extra}.json`,
`out/CSCREEN-NOCAPS-{base,extra}.json` (+ logs), `out/PK-*.json` and `.cap.log`; scripts `scripts/pairs.py`,
`scripts/cscreen.py`, `scripts/cone.py` (r3 B's, copied), `scripts/summarize.py`, `pk/tools/run_h.py` (r5 D's sk3 tools
copied with its `work/`), `pk/q.sh`.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
