# B-walk (round r4): neutral-plateau walks on the 566+554 base word

**Outcome: no gain (scoped negative result). No κ change.** Local-only evidence in this directory; nothing committed, pushed
or posted. Base word `r3/inputs/gauge44-word-566-554.json.gz` (#1672 blob 76c01583, 249 calls), toolkit rev3 harness
(`r3/toolkit-rev3`), b = 0.001679754956125544 (base cost 11,683,290,250, profile {1:2348, 2:500, 3:416, 4:130, 5:82}).

**Question.** r3 found thousands of exact Δ = 0 moves. Can one of them (or a cheap positive one) change which chain carries
a climb so that a second move becomes profitable?

## Pre-move catalogue (`scripts/premoves.py`, `out/PREMOVES.json`)
3,397 unique exact r3 edits on the base word: 3,189 neutral (962 two-column re-deliveries and 892 compensated re-timings
and 94 multi-crossing moves from D-families; 962 fusions and 279 fusion position classes from C-repair), 137 small-positive
compensated re-timings (+4,925 ×92, +6,781 ×44, +7,984 ×1), and A-extra's 71 relocations.

## Two-step searches
1. **Shared-fusion unblocking** (`scripts/walk_struct.py`, `price2.py`; `out/STRUCT.json`, `out/SHARED2.jsonl`). On the
   base word, all 10 two-target (A, H, q) groups are blocked by another reader of H and a write of A inside the window
   (`out/GROUPS-base.json`). One donation serving two targets would save a whole read, since a single fusion is exactly
   neutral. A structural pass over all 3,397 pre-moves finds 6 that open a shared fusion (W0 opens none). All 36
   composites priced exactly on the moved word: 30 frame-infeasible, 6 neutral (total Δ = 0).
2. **Cancelling pairs** (`scripts/cancel_pairs.py`; `out/CANCEL-PAIRS*.json*`). 4,296 pre-move pairs insert the same
   gate at the same position with opposite coefficients; 43 merge without conflicting deletions. Priced on W0: 42 inexact
   (each move's compensation only works alone), 1 neutral.
3. **Local re-search** (`scripts/lr2.py`, `pick_premoves.py`; `out/LR2*.jsonl`). The 28 kernel-sized B reads (W0
   deletion relaxation −8,879..−3,000; these are #2142's 2+4+4+2+16) use 30 helper registers; 455 neutral and 29 small-positive pre-moves touch
   them. For each selected pre-move N: W1 = N(W0) with its own exact optimal frames; (a) the deletion relaxation on W1 of
   every kernel-sized read whose registers N touches, against W0; (b) the 40 second moves nearest to N among compensated
   single-crossing re-timings (r3 D's generator, run on W1) and read fusions (toolkit `fusion.py`, run on W1) touching N's
   registers, each priced exactly by the harness on W1 (screen, static rules, unchanged compensation).
| Batch | Pre-moves | Second moves generated / priced | Neutral | Infeasible | Positive | Other rejections | Gains |
|---|---:|---:|---:|---:|---:|---:|---:|
| Neutral 1 (round-robin over the 30 registers) | 150 | 18,128 / 6,000 | 2,529 | 3,007 | 114 | 350 (238 compensation-changed, 112 static rule) | 0 |
| Neutral 2 (all 40 fusions, 19 position classes, 68 multi-crossing moves, 23 re-timings left) | 150 | 23,876 / 6,000 | 2,903 | 2,826 | 49 | 222 (128 compensation-changed, 94 static rule) | 0 |
| Small-positive pre-moves (+4,925..+7,984) | 29 | 3,242 / 1,160 | 385 | 739 | 2 | 16 | 0 |

In the positive batch, 18 second moves have Δ2 = −4,925, −6,781 or −7,984, but each exactly undoes its own pre-move
(e.g. `FR-1231-past1361-to1853` then `BR-1853-before1360-to1360`), so every total is 0.
The two shared-fusion passes are also two-step walks: with both blockers of a 672/676 group cleared by two pre-moves
(118 pairs clear both kinds; 9 open a shared fusion; `out/STRUCT2.json`, `out/SHARED3.jsonl`), all 46 shared fusions are
frame-feasible and exactly neutral. Deleting both ports' reads saves exactly what the donation and restore cost.

## Three-step walks
Not triggered. The directive was to extend only walks whose relaxation improves, measured on the walk's total (Δ1 + the
deletion price on W1, against the deletion price on W0). On the 300 neutral pre-moves, 436 relaxations of kernel-sized reads are unchanged and 12 lose their saving (the pre-move re-times the read itself); none improves. On the 29 positive pre-moves, 19 relaxations improve on W1, but only by the pre-move's own cost: walk totals are 18 equal and 26 worse, none better.

## Why the second-order kernel words were not walked
r3 B found 16 exact second-order kernel words (early −4,925 reads) rejected only by cone-cap containment. The failing
register holds a parked helper value whose lower frame joins the parked register's frame; frames are monotone along chains,
so the end-of-B frame cannot drop back inside the cap whatever the order. No reordering pre-move can repair them; only a
different parking register can (r3 B's cone-aware search found none).

## Scope and limitations
- Base word only. r3 A showed the extra word is the same program (12 B frames and 4 start ranks differ), so any gain
  would only need re-pricing there.
- Pre-moves come only from r3's catalogues; second moves only from two families (compensated re-timings and fusions),
  40 nearest per pre-move; no CP-SAT kernel re-search on moved words (no kernel-sized relaxation improved).
- Aside for agent C (port-dirt): 238 of the second-move fusions were rejected only as `compensation-changed`.

## Evidence and runtime
`out/SUMMARY.json` (all counts), `out/PREMOVES.json`, `out/GROUPS-base.json`, `out/STRUCT.json`, `out/SHARED2.jsonl`,
`out/CANCEL-PAIRS.json` + `-base.jsonl`, `out/SEL*.json`, `out/LR2*.jsonl` + logs; scripts in `scripts/`.
About 65 minutes wall (02:00–03:00Z): 9,208 worker-seconds of local re-search, plus structural passes (seconds) and composite pricing (under a minute). 3 worker processes (fork pools with a 6 GiB RSS watchdog, per-pricing deadlines, maxtasksperchild).

## Best next step
To second order, the neutral plateau is flat for these families. Every exact second move near a neutral move is neutral, positive or infeasible; kernel-sized relaxations never improve; and the shared-fusion groups are neutral even when fully unblocked. What remains lies outside the plateau's families: edits to A or to the compensation, or an interface change (agents A, C and D of this round). A cheap extension of this negative result: run `lr2.py` on the remaining 155 eligible pre-moves and on D's 962 two-column re-deliveries (about 25 minutes per 150).

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
