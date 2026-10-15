# r7 / V-parent: feasibility of removing the conjugating bridge that splits pair 2's idle levels 0-4

Agent V-parent, round r7. Local only: nothing committed, pushed or posted. Paths are relative to `scratchpad/`.

**Verdict: (b) blocked.** Within every recipe family searched, the parent's nine-stage recipe is the unique solution (up to
signs) of its own identity, and pair 2's idle levels are always split [4,1,2]. So the +6.64e-7 pair-2 merge (r6 L) has no
re-ordered or re-based bridge construction; it would need a different parent design, outside this lineage's recipe.

## 1. The bridge and its role
- Template: the 8-replica parent used by the T74 hosting
  (`r2/full566b/.../t16/global8/base/split-centres/GLOBAL-TEMPLATE.json.gz`), recipe from `global_k.py`'s `recipe(K=4)`
  (PR386/436/443 lineage; main `research/e8-bit-p111/vendor/pr510/e8-r480-nine-stage/vendor/e8-r715-eleven-stage-whole/code/global_k.py`).
- Per replica: events 9 and 12 are `bridge dst=1 src=2 c=+1` before and `c=-1` after local stage 4 (pair 1, forward).
  PR1319's `make_context` marks both src and dst as used, so the two reads of pair 2 bracket stage 4: idle sweep at event 8
  covers pair 2's levels 0-3 (children 4/6, rank 32), event 11 covers level 4 alone (children 5/7, rank 8).
- Why it is there: `global_k.py`'s integer eight-bank check. Local forward is Y_p += X_p, reverse X_p -= Y_p; a bridge
  (d,s,c) is the symplectic pair X_d += c X_s, Y_s -= c Y_d; the exchange maps (X_j,Y_j) -> (Y_j,-X_j). The whole recipe must
  compose to the identity, and each of the 18 bridge shears must be necessary. The F,R,F pair closes by itself; each R,F
  pair needs a correction, which the chain of conjugations supplies (pair j's forward call conjugated by pair j+1, plus the
  three closing bridges). The hosted audit also requires `t['recipe'] == parent['recipe']`, and PR1319's checker hardcodes 30
  source events and 9T bridges per replica.

## 2. Is there an equivalent recipe without the split?
Model (`scripts/recipe_algebra.py`, `scripts/search_orders.py`): exactly global_k's integer identity and shear controls, with
idle runs computed as PR1319's `make_context` does. It reproduces r6 L's geometry {0:[6], 1:[2,1,4], 2:[4,1,2], 3:[6,1]}
and recovers the parent's own recipe as an identity solution (calibration).

| Family searched | Size | Identity solutions | Geometries |
|---|---:|---:|---|
| Conjugations of 3 single calls (src != own, +-1) + 3 closing bridges, current stage order | 18,144 configs | 8 | current only |
| Same, all 1,260 canonical interleavings (pairs relabelled) | 22.9M configs | 8 (all in the current order) | current only |
| Up to 4 single interior bridges (any slot, one per slot), rest at the start/end, block orders | 1,695,140 | 0 (necessary condition fails) | - |
| 5-6 single interior bridges, block orders | 45,932,544 | 16 pass the necessary condition, all in the current order | current, and pair 1 [1,2,4] (no better) |
| Orientation variants (R,F/F,R and F,R,F/R,F,R), all interleavings, conjugation family | 18,900 orders | 24 | 3 geometries, each a relabelling of the current one |

- Lemma (start/end bridges are Levi elements): with no interior bridges, the middle product must have zero X->X and Y->Y
  blocks; the R,F pairs' product has a nonzero Y->Y entry, so interior bridges are required.
- The orientation variants move one isolated level between pairs (e.g. pair 2 becomes the three-call pair with runs [4,2] while
  pair 0 gets [1,6]), but every solution found has the same run multiset {6,6,4,4,2,2,1,1,1}, i.e. the same capacities
  48,48,32,32,16,16,8,8,8 per side as today, so the pattern-level value is unchanged and no 40-child exists.
- Every conjugation isolates one level of its source pair (both bridges touch it). The current recipe places each isolated
  level next to the source pair's own block, which is the least damaging position; pair 2 is [4,1,2] in every solution found.
- Not covered: several bridges per slot inside non-block interleavings, coefficients other than +-1, other call multisets,
  more than 9 bridges (PR1319 requires 9T), and recipes outside global_k's identity (a different parent algorithm).

## 3. Admission path, if a different parent were designed
A new recipe changes the template and every artifact derived from it: GLOBAL-TEMPLATE (global_k-style generator and identity
proof), DATA-PHASES (complex-nine-native per-port stage alignment and idle axes), the cover/terminal translations, the hosted
template (`audit_allcold.py` requires the parent recipe), PR1319's checker (30 events, 9T bridges hardcoded), PR1319's owner
reconstruction and lift (frozen OWNERS: a full re-solve), providers' native admission and PLAN, the strict T74 replay, and
the PR1673 outer. None of these generators accepts a different recipe as is. Expected value if a split-free parent existed:
r6 L's pattern bound +6.64e-7 (pattern relaxation, windows ignored).

## Evidence
`EVIDENCE.json`; `out/SEARCH-current-order.json`, `out/SEARCH-orders.json` (+ `.log`), `out/SEARCH-single.json`,
`out/SEARCH-single56.json`, `out/SEARCH-orient.json`; scripts in `scripts/`. At most 4 worker processes, per-task alarms,
RSS checks (peak well under 1 GiB).

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
