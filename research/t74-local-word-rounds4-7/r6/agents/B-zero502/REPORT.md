# r6 / B-zero502: making a width-9 helper's narrowing auditor-valid (re-timing route)

Agent B-zero502, round r6 (2026-10-15, 03:35–04:10Z). Words `r3/inputs/{gauge44,extra}-word-566-554.json.gz`,
toolkit rev3 copy in `toolkit/` (one debug hook added in `frames.py`, behaviour unchanged), b = 0.001679754956125544,
unchanged auditor `r3/main/research/gauge44-frames-x/independent/audit_local.py --main`. Local only: nothing committed,
pushed or posted.

**Outcome: scoped negative, κ unchanged.** No construction makes any frame-feasible width-9 helper's (9,0,9) → (8,1,9)
narrowing both auditor- and native-valid. The exact cancellation exists and is free while the helper stays (9,0,9), but
with the helper entering it is frame-infeasible at every tested slot and start vector. One auditor gap was found (cut probe).

## 1. The rule and the leak
- `audit_local.py`: dirt = helper columns of the A+cut+B map on target rows, transformed by the precondition; the
  compensation is `y -= a·k` for each dirt entry and runs at frame 0 before A. It requires `not any(e[2] in entering for e
  in compensation)` ("nonzero entrance response") and that precondition/compensation touch no entering or cold-end helper.
  So an entering q needs a zero q column on every target row of the A+cut+B map.
- Helpers 502/503/515 (`out/LEAK-502-503-515.json`): each is the second input of a late-B butterfly with 490/491/479
  (agent A's helpers) and is copied at B1153–B1156 into a second butterfly (684/685/687). Its initial value q0 reaches 4
  target rows (raw, e.g. 502: 202 +1, 203 +1, 204 −1, 205 −1); the entrance response after the precondition sits on
  200/203/205/206 (±½). An entering helper (550/551/563, level 102/102/96) is relayed through q between its A-write and its
  B-write and cancels there, before q's first read.

## 2. Re-routing / re-timing so the leak never arises: impossible here
q0 can only leave q through a gate `q -= c·x` with x holding q0, and only q holds q0 before q's first read; it must also
come back to q at the end. So q0 has to be parked during q's reads (B1153–B1768) in a register that is idle until q is
restored (end of cleanup), or that is entering with non-leaking paths but then puts its own residual into q's paths.
No helper is idle in main (`out/USAGE-base.json`: 0 idle, none first used after B1700). The entering relays (550 → q at
A1233/B1041, etc.) give their content back to q before B1153. Re-timing q's own writes does not change the leak (the map is
unchanged). This matches agent A's cluster finding.

## 3. Cancellation inside B ("in-B compensation"): exact, free when not narrowed, infeasible when narrowed
Construction (`scripts/zcore.py` build/build_at): re-time q's A-writes (and B-writes before the slot) to just after slot t
(legal: q not read before t, each source not rewritten in between), and insert at t the target deliveries `y += d_y·q` with
M_t d = −L (M_t = B's target-only mixing from t; for t = 0 these are exactly the negated compensation gates, e.g. 502:
200 −= ½q, 203 += ½q, 205 += ½q, 206 += ½q). The q column on targets becomes zero and the re-derived compensation drops q.
- **Control, q kept (9,0,9)** (`out/CONTROL-inB.json`, `words/CONTROL-inB-*.json.gz`): Δ = 0 at certified optimal frames,
  compensation 7,208 → 7,204 gates, `audit_local.py --main` PASS for 502/503/515, PR635 native chain 5/5 PASS on 502's word.
- **Narrowed (q entering), all infeasible** (exact frame L/U propagation):

| Scan | Tasks | Result |
|---|---:|---|
| 502, every start vector u = 1..511, slot B0 (`out/USWEEP-502.jsonl`) | 511 | 511 infeasible |
| every frame-feasible (helper, basis) of r5 C except A's four, slots B0/B550/B705, base (`out/BULK-base.jsonl`) | 447 | 234 inapplicable (q read in A), 213 infeasible |
| same on the extra word (`out/BULK-extra.jsonl`) | 447 | identical |
| 502/503/515, every 25th slot up to the move limit (`out/TSCAN.jsonl`) | 105 | 105 infeasible |
| 22 applicable full-c1 helpers, every 50th slot (`out/TSCAN-FC1.jsonl`) | 836 | 381 infeasible, 455 slot not movable |

- **Why** (`out/SPREAD-502.json`): every gate gives both registers one frame, so each delivery forces its target to contain
  q's start vector from the delivery on. For 502 (u = 102) the vector then propagates through B's target-mixing network and
  the helpers later read into those targets: 72 targets and 464 helpers acquire it, including target 165, whose end frame
  lacks it, so the gate 166 −= 2·519 (base B1836) is forced to full rank. At later slots the re-timed first write forces its
  cold-end source (572/573/575) to the delivery frame, which its tail frame excludes. The frame-free compensation exists to
  avoid exactly this coupling.

## 4. Retarget (coordinator) and candidates against the 3,728-unit budget
C-hosting's valid narrowed owner map pays only for full-c1 narrowings (saving 2,116,454); 502/503/515 save 2,109,673 and
were dropped. Of the 100 full-c1 (helper, basis) pairs in my sweep, 78 are read in A (construction inapplicable) and the
22 applicable ones (460–463, 468–471, 480, 481, 492, 493, 530, 542, 546–549, 558, 560, 568, 570) are infeasible at every
movable slot. A-zero478's SCREEN117 shows 0 of 104 full-c1 helpers passing on either word. No candidate has a finite extra
cost, so none fits the 3,728 units/call budget.

## 5. Soundness finding: an auditor gap in the cut
The same deliveries placed in the **cut** section (`words/PROBE-cut-502.json.gz`) make 502 entering with a zero entrance
response; the toolkit certifies Δ = −2,109,673 and `audit_local.py --main` PASSES (193 entering, compensation 7,204,
widths {8:115, 9:239}), because neither the auditor nor the toolkit puts cut gates in the frame graph (the centre-path check
only looks at cut gates whose source is a centre). The native chain rejects it at step 2 (`hpe_emit_local.py`: emitted
column mismatch, register 153; `out/NATIVE-PROBE.log`), and the base word passes all 5 native steps. This is not a gain:
a non-centre cut add moves a level-102 residual into targets at frame 0, which is what the entrance rule forbids. Worth a
one-line auditor guard (cut gates must read centres only).

## Best next step
Unblocking needs the pre-cancel structure that the existing (8,1,9) entering helpers (e.g. 506/518) get from the word
construction: the residual delivered early through a partner before the helper's first write, with frames designed around
it. That is a generator-level change, not a local edit. A cheaper probe is a frame-aware CP-SAT that chooses per-target
delivery slots together with re-timings of the late helper reads that spread the vector.

## Files
`EVIDENCE.json` (summary); `out/`: LEAK-502-503-515, USAGE-base, CONTROL-inB, AUDIT-CONTROL-inB-*, NATIVE-{base,control502,PROBE}
logs, USWEEP-502, BULK-{base,extra}, TSCAN, TSCAN-FC1, SPREAD-502, AUDIT-PROBE-cut-502; `words/`; scripts `zcore.py`
(construction), `leak.py`, `gates.py`, `price1.py`, `usweep.py`, `bulk.py`, `tscan.py`. At most 3 workers, per-task
deadlines, RSS flag 6 GiB; peak RSS 0.15 GiB per process. Raw tool logs may contain local paths.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
