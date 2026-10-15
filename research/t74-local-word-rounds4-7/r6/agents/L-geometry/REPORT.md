# r6 / L-geometry: the hosting-geometry lever on the T74 566+554 supplier

Agent L-geometry, round r6 (2026-10-15, 06:05–06:20Z). Local only: nothing committed, pushed or posted. Paths are relative
to `scratchpad/`. Inputs: PR1319's hosting code and the retained T74 replay context (via r6 C-hosting's `ctx.py`), the
8-replica parent template and DATA-PHASES (`r2/full566b/.../global8/base`), r5 C-packing's pattern model, the retained moment
engine (`wt-566/research/complex-k492-owner-repair/vendor/multicold/engines/moment.py`), b = 0.001679754956125544.

**Outcome: closed for the current parent. No admissible geometry change raises κ; κ is unchanged.**

## 1. Where the capacities and the idle jump come from
- **Levels = stages.** Each live family (owner, pair, side, port) has a 73-axis owner basis: position 0 plus nine octets,
  positions 1–72 = levels 0–8. Every idle child's pending axes are a contiguous run of octets (`out/OCTETS.json`), and
  rank = 8·(to_level − from_level) in the template's `idle_cover_sweep` events. A pair's own local stages climb their own
  levels: pair 0 stages 0–2, pair 1 stages 3–4, pair 2 stages 5–6, pair 3 stages 7–8. Its idle children climb the other
  levels.
- **Windows** run between uses of the pair. `make_context` marks both the src and dst pair of every bridge as used, so a
  pair's idle levels are split by its own local stages and by the bridges that read it (`out/GEOMETRY.json`):

| Family | Idle children (levels → rank) | Split by |
|---|---|---|
| (0,s) | levels 3–8 → 48 | — |
| (1,s) | 0–1 → 16, 2 → 8, 5–8 → 32 | bridges reading pair 1 around stage 2; stages 3–4 |
| (2,s) | 0–3 → 32, 4 → 8, 7–8 → 16 | bridges reading pair 2 around stage 4; stages 5–6 |
| (3,s) | 0–5 → 48, 6 → 8 | bridges src 3 around stage 6 |

- **Bins:** 18 children × 112 ports × 74 replicas = 149,184, with capacities 8/16/32/48 (6/4/4/4 per replica-port).
  A bin's leftover is one idle jump. All idle is in 22,748 empty 48-bins: child 8 has 6,150, child 10 4,860, child 12 6,672
  and child 13 5,066. Every other bin is exactly full (`out/OCCUPANCY.json`).

## 2. Binding constraints (PR1319's `independent_core.check_roles`)
- **Halving reserve:** M·M > 2·max(profile)², so every jump must be ≤ 51 (M = 73). A rank-56 idle jump is inadmissible.
- **Rank deficit:** 73·live − mass = 320·T, so the global mass is fixed. Idle mass is capacity − role width = 1,091,904.
- **Prefix and row:** 1,441 < 2,048 and 19,545 < 20,161. The payload doubles once 233 + 18T ≥ 2,048, i.e. T ≥ 101, which
  breaks the row bound; r5 C already showed replication cannot help.
- **The moment engine** depends only on the global profile, and reproduces the supplier's C = 0.0016797549561255445213…
  exactly (`out/ENGINE-ceiling.json`).

## 3. What alternative geometries would be worth
Pattern model as r5 C (`scripts/gpat.py`: windows, families and call identity ignored, so these are upper bounds), with
arbitrary per-child ranks under the family sums and the halving reserve, priced with the moment engine (`scripts/engine.py`).

| Geometry | Units gained | κ gain | Status |
|---|---:|---:|---|
| All idle in rank-51 jumps (ceiling) | — | +7.90e-6 | not octet |
| All rank-52 | — | +1.05e-5 | breaks the halving reserve |
| C/B family → (51,5,0) | 200,741,911 | +6.78e-6 | not octet |
| D family splits 49/7 | 146,080 | +4.95e-9 | not octet |
| D family 51/5, 50/6 | negative | — | — |
| **Octet merges:** | | | |
| pair 3 windows merged → 56-child | 2,062,235 | +6.95e-8 | needs the stage-6 bridges that read pair 3 removed |
| pair 2 levels 0–4 merged → 40-child (extra word gone) | 19,731,991 | +6.64e-7 | needs the bridges that read pair 2 around stage 4 removed |
| pairs 1/2 (or 1, 2, 3) one 56-window each | 200.7M / 253.9M | +6.8e-6 / +8.6e-6 | impossible: spans the pair's own local stages |

The large values all come from idle jumps of 49–51 (214 units per idle unit cheaper than 48) plus dropping the extra word.

## 4. Admissibility verdict
- **Under the current nine-stage recipe nothing is free.** Ranks are 8 × (idle levels per window) and the windows are set by
  the recipe, so no hosting-side edit can change a capacity.
- **Empty children cannot exceed 48.** The octet granularity together with the halving reserve forbids it, so the current
  all-48 idle profile is already the most concentrated possible. r5 C proved the packing optimal.
- **Rank-51 geometries are not expressible**, because 51 is not a multiple of 8.
- **The only octet-compatible gains need a different bridge structure:**
  - removing the conjugating bridge reads (pair 3 around stage 6, worth +6.95e-8; pair 2 around stage 4, worth +6.64e-7);
  - this changes the computed map, so it means a new parent construction with its own correctness proof;
  - it must be re-admitted through the whole parent chain: template, DATA-PHASES, lift, controller emission, invoice and
    outer.
- **No concrete, checkable route exists at the hosting level.**

**Correction to the round brief:** eliminating the extra word is worth about 19.7M units (+6.6e-7 κ), not about 1e-4. The
freed local rank units become idle mass at almost the same per-unit cost (r5 C's 19.77M).

## Evidence
- `EVIDENCE.json` summarises everything.
- `out/`:
  - `GEOMETRY.json` (children, families, windows)
  - `OCTETS.json` (child axes as basis positions)
  - `OCCUPANCY.json`
  - `COSTS.json` (c[1..72])
  - `GEOMS-1/2.json`, `GPAT-1/2.json` (pattern relaxations)
  - `ENGINE-ceiling/gpat1/gpat2.json` (moment-engine endpoints)
  - `profiles/`
- `scripts/`: `geom.py`, `occupancy.py`, `gpat.py`, `engine.py`.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
