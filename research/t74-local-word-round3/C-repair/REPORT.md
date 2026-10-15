# C-repair (round r3): the #1186 toolkit's frame-structure sweeps on the 566+554 T74 words

**Result: scoped negative, no gain.** Every move class of our toolkit that applies to these words was swept on both
supplier words (base gauge44 `eeb6a236`, extra `cd417b90`; #1672's `new/*-word-566.json.gz`). Pricing used toolkit
revision 3 (`c37dfb07`, copied to `toolkit/`) with exact screens, certified surrogate-optimal frames and true-moment
intervals at b = 0.001679754956125544. No candidate has a negative delta. Every feasible candidate is **exactly neutral**
(Δ = 0). No priced non-gain could hide a true gain above **2.9e-11 units** (about 6e-22 in κ).

## What #1957 did not cover
#1957 ran deletion relaxation, single-gate commuting moves (4,461), compensation searches, A-section samples and owner
ILPs. Its tools import only `exchange.coef_mod` from the toolkit. It ran no fusion or repair sweep, no read-set exchange
moves and no joint triangle-hybrids; #2142 ran none either. These are the classes swept here.

## Coverage (identical on both words, record by record)

| Class | Candidates | Pricings | Feasible (all Δ = 0) | Infeasible | Other | Negative |
|---|---:|---:|---:|---:|---:|---:|
| Fusion + enlarged-reader repair (`repair.py`, unchanged generator and repair step) | 2,261 fusions (501 t/A/H triples) | 2,787 | 963 (170 triples) | 1,487 | 284 inexact, 53 static-rule | 0 |
| Fusion position-class completion (new: every event class of A/H for the donation and the B restore) | 3,243 | 3,243 | 279 (168 triples) | 2,909 | 55 static-rule | 0 |
| Read-set exchanges (sw4 rule): 27 single swaps, 351 swap pairs, 13 full copy-pair exchanges, 78 unions | 469 | 469 | 0 | 469 | 0 | 0 |
| Joint triangle-hybrids (`joint.py`, ≤3 fused, partial swaps, canonical + after restores) | 127 | 127 | 24 | 103 | 0 | 0 |
| Shared multi-target fusions (new: one donation serving ≥2 targets) | 0 | — | — | — | — | — |

- No timeouts: every pricing's status is recorded (`repair_rec.py` wraps the unchanged `repair.repair`).
- Interval bound (largest possible true gain among priced non-gains): base 2.88e-11 units (fusions, position classes)
  and 1.97e-11 (exchange/joint); extra 2.64e-11, 2.52e-11 and 2.03e-11.
- Not applicable: `slots.py`, `compose.py` and `transplant.py` need #1018's k8 slot recipe or the k8 words. `joint.py` is
  the generic form of those triangle-hybrid slots. `sites.py` is a subset of `repair.py`.

## Why the fusion family is neutral here
Cross-checked against #1957's deletion relaxation (base word, keyed by B index): 2,216 of the 2,261 fusions delete a
gain-carrying read (deleting the read alone, without compensation, would save 4,913 to 19,639 units). In every case where the donation H += qA and its
restore are frame-feasible (960 fusions, deleted-read savings 9,826 to 16,576 units, and 278 position classes), they cost back exactly that saving (all
Δ = 0). The donated component climbs the same frame on H's chain that it climbed on t's. The only way to beat this inside
the class would be one donation serving several targets. The words have 10 (A, H, q) groups with two targets, but each has
another reader or scale of H and a write of A between the two targets' reads, so no shared fusion is valid.

The two words have the same scalar program (B differs only in 12 stored frames; start frames differ on 627/629/630/631).
All 6,081 distinct candidates have identical statuses on both words.

## Runtime and limits
- 3 workers; base and extra fusion sweeps 936 s and 953 s, position classes 536 s and 530 s, exchange/joint 94 s and 95 s.
- Peak process RSS 0.19 GiB under a 6 GiB process-tree cap (`capped.py`); per-pricing timeout 90 s.
- Scope: finite move families in the #1186 frame model (cone caps, tail-mutable frames, cut equality), single moves of
  each family at the stated b. Multi-step sequences of neutral moves are not covered (see next step).

## Next step
A two-step neutral walk: apply each of the 170 neutral fusion triples (one representative each) and re-price the fusions
and costly-read deletions that touch its registers on the new word. Neutral moves change which chain carries a climb, which
might open a second move. Otherwise, the remaining levers are outside this class (kernels with new compensations, agents
A/B/D, or changed interfaces).

## Evidence
- `EVIDENCE.json`: all counts, status histograms, bounds, word comparison, shared-fusion diagnosis.
- `runs/repair-{gauge44,extra}.json`: every fusion with every pricing's status, delta and bound.
- `runs/pos-*.json`, `runs/xj-*.json`, `runs/count-*.json` (base frames: certified; profiles base
  {1:2348,2:500,3:416,4:130,5:82}, extra {1:2340,2:508,3:420,4:126,5:82}), and the `*.log` files.
- Scripts: `repair_rec.py`, `fusion_pos.py` + `posweep.py`, `xjsweep.py`, `shared_fusion.py`, `summarize.py`, `capped.py`, `chain.sh`.
