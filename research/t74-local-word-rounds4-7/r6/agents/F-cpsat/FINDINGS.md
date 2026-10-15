# r6 F-cpsat: frame-aware joint search for a full-c1 width-9 narrowing (no valid word)

Written from the agent's final message: the subagent harness blocked its REPORT.md.

- **Model:** `y += d*q` deliveries into any target at a separately chosen B time per target. q's writes are re-timed to
  just after the last delivery, up to the move limit B784-B880. Exactness is solved in exact rationals through B's
  target mixing, and frames are checked exactly with `frames.Graph`.
- **Calibration:** with q not narrowed and deliveries at B0, it reproduces r6 B's construction: certified delta 0, the
  compensation goes from 7,208 to 7,200 gates and no longer reads q, and the unchanged auditor passes (460, 546).
- **Sound screen** (a bounding word with q's early writes removed gives valid frame bounds). All 22 full-c1 helpers not
  read in A are infeasible, with identical results on both words:
  - 16 helpers (460-463, 468-471, 546-549, 558, 560, 568, 570): the admissible deliveries do not span the leak;
  - 6 helpers (480, 481, 492, 493, 530, 542): deliveries join target lower frames into q, leaving only 2-3 dimensions.
    The 132-167 exact solutions per helper all fail, at B1827-B1829 or tail vertices 89/90.
- **Read re-timing probe:** moving q's reads late lifts its upper frame at the first read from 2 to 6 dimensions, but the
  write sources cap it at 1-2, so nothing survives.
- **Evidence:** `EVIDENCE.json`, `out/`, `scripts/` (`screen3.py` is the proof screen, `multi.py` the constructor).
