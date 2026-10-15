# r5 / A-slack: slack between the #1186 frame solver and the acceptance checks

**Outcome: scoped negative, no gain, κ unchanged.** For the fixed programs of the 566+554 supplier words, the solver's
frame model coincides with the frame rules of the unchanged auditor (`main/research/gauge44-frames-x/independent/audit_local.py`)
and the native provider chain (`toolkit/native.py`: PR635's `hpe_audit_and_transport.py` → ledgers → local replay →
wrappers → phases), except for one solver-only constraint, which is redundant on both words. Even unsound relaxations
of the genuine rules do not lower the optimum. Local only: nothing committed, pushed or posted.

Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz` (#1672 blobs 76c01583 / e86142b3). Solver: a private copy of
toolkit rev3 (`c37dfb07`) in `r5/agents/A-slack/toolkit/`, with one added switch, `Graph(..., tail_caps=True)` (default
behaviour unchanged). b = 0.001679754956125544.

## 1. Correspondence table

| Constraint | Solver (`frames.Graph`) | `audit_local.py` | Native audit (`hpe_audit_and_transport.py`) |
|---|---|---|---|
| Monotone chain per register, one common frame per gate | yes | yes (`climb`) | yes (`climb`) |
| Start frames (port vectors, `start_extra`) and end frames (FULL, perp(port), `helper_final`) | fixed nodes | yes | yes |
| Cut equality: centres at `center_frames`, target rows at `target_levels` when B starts | `cut_equality=True` | yes | yes (also re-checked in the emitted ledgers) |
| Centre descents (paid, constant) | constant | yes | yes |
| Row/column cone caps on **end-of-B** frames | yes | yes | yes (cone pre-check) |
| Cone caps on **tail** (early-cleanup) vertices | **yes** | no | no |
| Tail frames free and monotone; remaining cleanup only on FULL-end registers | `tail_mutable=True`; cleanup rule in the harness | yes | yes |
| Paid profile = rank of each chain jump | yes | yes | yes |

Checker-only rules (not frame choices for a fixed program): dyadic additions and signed binary scales, non-target reads
target, exact forward and dual endpoint map with the derived compensation, no compensation or precondition on entering or
cold-ended helpers, `local_profile`/`width_inventory` bookkeeping, the parent centre/port interface (`--main`), and in the
native chain the 192-bit local payload bound, wrapper order, residual adapters and Clifford phases. The harness enforces or
runs these separately.

**The only gap:** `Graph` applies a register's end-of-B cone cap to every mutable vertex whose successor is a tail or end
vertex, which includes the tail vertices themselves. Both checkers cap only end-of-B frames.

## 2. Re-solves

- **Tail caps dropped (sound w.r.t. both checkers):** on both words the bounds of **0 vertices** change
  (`out/CAPBITE-{base,extra}.json`), so the optimum is identical: base 11,683,290,250 {1:2348, 2:500, 3:416, 4:130, 5:82},
  extra 11,691,748,602 {1:2340, 2:508, 3:420, 4:126, 5:82}, both certified (`out/TAILCAP-{base,extra}.json`). On these
  words the tail caps are already implied by the end frames and successor vertices.
- **Earlier rejections re-priced without tail caps:**
  - r3 B-interact's 16 exact second-order words (rebuilt with B's own unchanged tools, `scripts/rebuild16.py`; all
    map-exact, compensation unchanged): all 16 still infeasible, with the same reason and vertex (`out/PRICE16.json`).
  - r3 C-repair's 755 candidates per word that failed at a tail vertex (fusion position classes and read-set exchanges):
    all 755 still infeasible on both words, with the same reasons; 0 negative (`out/RETAIL-{base,extra}.jsonl`).
- **Shadow prices, diagnostic only (unsound relaxations):** dropping all cone caps, cut equality, or both leaves the optimal
  cost of both words exactly unchanged (`out/SHADOW-{base,extra}.json`). The current frames are optimal even for a strictly
  weaker model, so no frame-rule relaxation of any kind can lower these programs' cost.

No cheaper word arose, so there was nothing to write back, audit or run through the native chain.

## Scope and limits
- Frame choice for the two fixed programs, plus the rejected edited programs listed above.
- Not re-tested: r4 B-walk's 30 two-step shared-fusion composites that failed at tail vertices (`r4/agents/B-walk/out/SHARED2.jsonl`);
  the analogous r3 C candidates were all unaffected.

## Next step
Frame-level slack is closed for these words: any gain must change the program (gate sequence) or the interface
(start/end frames, widths), not the frame model. A possible toolkit cleanup is to restrict the cap to the last A/B vertex,
matching the checkers; it changes nothing here.

## Evidence
`SUMMARY.json`; `out/` (TAILCAP, CAPBITE, SHADOW, PRICE16, RETAIL, words16/ with INDEX.json); `scripts/` (tailcap.py,
capbite.py, shadow.py, rebuild16.py, price16.py, reprice_tail.py); `toolkit/frames.py` (the `tail_caps` switch).
Runtime about 15 minutes of computation; at most 3 workers; peak RSS well under 1 GiB.
Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
