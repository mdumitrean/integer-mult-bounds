# DATA-INVENTORY (Lane D, r11 styles round, 2026-10-15)

`$S` = `$S`.
`$REPO` = `/Users/mdumitrean/Desktop/dev/aigent/math/prime/integer-mult-bounds` (checkout on `imb-upstream-merge-2026-10-13`; `origin/main` = c719a5e0).
All paths are read-only data. Blob ids are `git hash-object` of the file (10 hex). Nothing was fetched in this round; the
`ls-remote` column is what `git fetch origin pull/N/head` would bring (read-only listing taken 2026-10-15).

## 1. Two word formats (the loader must know which one it holds)

| format | lineage | top-level keys that identify it | sections (counts on the example word) | loader |
|---|---|---|---|---|
| FULL-WORD | gauge44 / k8 / T74 kernel line (#1094, #1195, #1625, #1672) | `early_cleanup`, `refactored_cleanup`, `root_lines`, `scatter`; no `warps` | `precondition` 192, `A` 3451, `cut` 176, `B` 1846-1853, `cleanup` 6796-6802 (ranks 4/8/9); `helper_final` 78, `start_extra` 192 | toolkit `word.inline(word, targets_empty)` -> `frames.Graph`; `word.recount(word)`; `frames.full_profile` |
| BORROW-WORD | T74 borrow line (#2474 ... #2679, #2745, #2751, #2766, retired5, #2802) | `warps` (65-72 records), `compensation` (7130 rank-0 adds), `restore` 87, `initial_corrections` 36, `removed`, `prelude_events`, `kind`, `base` | `precondition` 192, `compensation` 7130, `A` 3535 (3028 add, 483 scale, 24 warp records), `cut` 176, `B` 1870-1872, `cleanup` 4536-4547 (all rank 9 = inverse-reverse of forward), `restore` 87 | `wordmodel.Word(path)` (time-ordered events incl. B warps), `bounds.Bounds(path)` (exact lo/hi frame lattice); both from `$S/wt-r10pub/research/t74-r10-hosting-leads/J-dim1/code/` (byte-identical copies of #2745's handoff code) |

Common fields: `report {R:480, h:9, v:112, local_profile, width_inventory}`, `ports` (112), `centers` (8), `center_frames`,
`target_levels`, `helper_final`, `start_extra`. Gate syntax is identical in both: `["add", tgt, src, num, den, frame]`,
`["scale", tgt, num, den, frame]`, `frame` = list of F_2^9 basis bitmasks (rank = length), `[]`/`null` = rank 0.
Measured on #2802 base: 17,575 gates in all sections; forward string A+cut+B = 5,583 gates; 632 live registers (112 sources,
112 targets, 408 helpers); coefficient classes: A 7, B 10, cleanup 13, compensation 8; B gate ranks {1:259,2:112,3:154,4:269,
5:136,6:214,7:448,8:280}; A gate ranks {0:1194,1:510,2:387,3:112,4:1260,8:48}; warps: 72, lender-frame dims {4:62, 5:10}.

## 2. Lineage words, fills and profiles

kappa values are the exact package endpoints (decimal, truncated); "complete" = global paid profile c_r used by the moment
equation; "local" = per-call paid profile; "inv" = helper width inventory.

| PR / object | kappa | local profile / inv | complete profile (idle part) | where (path; head; blob) | format | held? |
|---|---|---|---|---|---|---|
| **#1094** selected on main (Jeremy Kothe seven-slot k8 word, T16, 144 calls) | 0.001672660197076918 (= 836330098538459/5e17) | local {1:2412,2:418,3:432,4:142,5:82,8:8}; inv {4:56,5:32,7:30,8:122,9:240} | complex {1:349604,2:60192,3:62585,4:20448,5:11808,7:7,8:1152,48:4866}; idle {1:2276,3:377,7:7,48:4866} (toolkit README) | `$S/k8/K8S7-WORD.json.gz` (blob 723decbc, 57,222 B) == `origin/main:research/community-frontier1094-audit/selected-replay.tar.gz` -> `candidate/strict/global/base/providers/gauge44/FULL-WORD.json.gz`; `ASSEMBLY.json` (85 KB), `PLAN.json` (975 KB) inside the archive; PR head 0fc329d0 (local commit) | FULL-WORD | yes |
| #1094 pre-slot word | - | {1:2412,...} minus slots (toolkit README `db2c7cfb` = replay-archive id, not a blob) | - | `$S/k8/K8PRE-WORD.json.gz` (blob e9d9317f) | FULL-WORD | yes |
| **#1195** (ours, open): two source-holder fusions on #1148's joint-entrance k8 word | 0.001675658002271934 | see package README | - | `$REPO` branch `k8-source-holder-fusions-merge` (99a8a424): `research/k8-source-holder-fusions/FULL-WORD.json.gz`, `PLAN.json.gz`; also `k8-joint-entrances/`, `k8-eight-ends/`, `k8-three-demotions/` words | FULL-WORD | yes |
| **#1625** (ours, open): pivot-566 helper-donor kernel on #1319's T74 exact fill | 0.001676896669021299 | gauge44 {1:2347,2:502,3:415,4:130,5:82,8:8}; extra {1:2339,2:510,3:419,4:126,5:82,8:8} | {1:1559766,2:337668,3:278058,4:84912,5:54612,8:5328,48:22748}; dispatch gauge44 249 / extra 417 | `$S/wt-566` (branch `t74-pivot566-kernel` c7cac078): `research/t74-pivot566-kernel/inputs/{gauge44,extra}-word-566.json.gz` (blobs ecf75c27 / ac08516e, 57.4 KB), `data/PLAN.json` (6.9 MB), `data/SPEC.json` | FULL-WORD | yes |
| **#1672** (open): pivot-554 kernel k554-signed-001 stacked on #1625 ("566+554 words") | 0.001676938111022438 | gauge44 {1:2348,2:500,3:416,4:130,5:82,8:8}; inv {4:44,5:44,7:38,8:114,9:240} | OWNERS/GLOBAL-TEMPLATE in package | head b8ab040d (local commit, no ref): `research/gmx-t74-k554-signed-001/new/{gauge44,extra}-word-566.json.gz` (blobs 76c01583 / e86142b3, 57.4 KB), `OWNERS.json.gz` (3.7 MB), `GLOBAL-TEMPLATE.json.gz` (2.0 MB); copies `$S/r3/inputs/{gauge44,extra}-word-566-554.json.gz` | FULL-WORD | yes |
| #2679 (philippeVV): pre-life hostings + refit + alias 653<-563 (source of the borrow machinery) | not recorded locally | - | - | head 2e2cf565 (local commit): `research/gmx-t74-borrow43-handoff/new/borrow/words/BORROW-WORD-43{base,extra}.json.gz` (blobs 86dbe403 / 697af5b3, 71.4 KB); 491-file handoff incl. `new/borrow/{build_word,emit_word,alias_build,refit/,prelife/}` | BORROW-WORD | yes (git object) |
| **#2745** (jeremykothe2): window-optimal fill on #2733's composition | 0.0017161404259974415 (= #2733) | {1:2370,2:646,3:297,4:120,5:26,7:4,8:4}; inv {4:26,5:9,7:62,8:78,9:240}; 415 helpers | {1:1595736,2:430236,3:204396,4:79920,5:22532,7:2664,8:2664,32:1,48:26558}; 276,390 roles | head 4f485de0 (local commit): same path as #2679 (blobs 33524d8f / 583a98c6, 71.2 KB); copies `$S/r9/inputs/BORROW-WORD-43{base,extra}.json.gz`, package `$S/r9/vendor/pr2745` | BORROW-WORD | yes |
| **#2751** (tekuuu): joint twelve-source recovery | 0.001717141586348426338109 - 1e-46 - 1e-70 | {1:2366,2:646,3:297,4:120,5:26,8:8}; inv {4:26,5:9,7:62,8:78,9:240}; 415 helpers | {1:1593072,2:430236,3:204396,4:79920,5:22532,8:5328,32:1,48:26558}; idle {1:17316,3:6594,5:5216,32:1,48:26558}; 276,390 roles | head 4cfbb0cc (local): `research/t74-joint-twelve/inputs/WORD-{base,extra}.json.gz` (blobs f1fc67a6 / f06e80c4, 72.5 KB) == `$S/wt-claim7/research/t74-joint-twelve-retired7/inputs/WORD2751-{base,extra}.json.gz`; `FILL2751.json.gz`, `PROVIDERS2751.json`; also `$S/r9/vendor/pr2751` | BORROW-WORD | yes |
| **#2766** (DavidAriasC): frame refit B1151 6->5 on #2751's words | 0.001717256973467002308270 - ... | per call H1 -2, H2 +1 vs #2751 -> {1:2364,2:647,3:297,4:120,5:26,8:8} | {1:1591740,2:430902,3:204396,4:79920,5:22532,8:5328,32:1,48:26558} | head e6df920c (local commit reachable only from `.git/FETCH_HEAD`; a `git gc` could drop it -> re-fetch `pull/2766/head`): `research/complex-routing-leaf-fusion/inputs/WORD-{base,extra}.json.gz` (blobs 9a49a909 / a3fdc91b, 72.2 KB) + vendored #2751 inputs | BORROW-WORD | yes (fragile) |
| #2767 (jeremykothe2): same kappa, other route | 0.0017172569734670023 | - | - | only `$S/wt-claim7/.../evidence/PR2767-OUTER-CLAIM.json` (3000-digit outer claim); no words | - | evidence only |
| retired5 (ours, local, unpublished) | 0.001717409316335491643448 | {1:2386,2:642,3:274,4:128,5:26,8:8}; inv {4:26,5:4,7:62,8:78,9:240} | {1:1606392,2:427572,3:189078,4:85248,5:25862,8:5328,32:1,48:26558}; idle {1:17316,3:6594,5:8546,32:1,48:26558} | `$S/wt-claim5` (branch `t74-joint-twelve-retired5` b295183e): `research/t74-joint-twelve-retired5/inputs/WORD-{base,extra}.json.gz`, stage inputs `refit5/alias5/refit5c_43*.json` | BORROW-WORD | yes |
| **#2802** (ours, open): two hostee moves + seven retired-lender aliases | 0.001717794984118634663827 - 1e-46 - 1e-70 (80-digit root in README) | {1:2382,2:648,3:268,4:128,5:26,8:8}; inv {4:26,5:2,7:62,8:78,9:240}; 408 helpers | {1:1603728,2:431568,3:185082,4:85248,5:27194,8:5328,32:1,48:26558}; idle {1:17316,3:6594,5:9878,32:1,48:26558}; mass 4,816,512; 271,728 roles | `$S/wt-claim7/research/t74-joint-twelve-retired7/` (head 17b2ee6e): `inputs/WORD-{base,extra}.json.gz` (blobs 91bd9c68 / 6c4a9a43, 72.4 KB), `FILL.json.gz` (blob 6441c0be, 1.27 MB), `PLAN.json.gz`, `DISPATCH.json.gz`, `GLOBAL-TEMPLATE.json.gz`, `SOURCE-FILL.json.gz`, 8 stage inputs (refit5, alias5, refit5c, refit7, hostmove2, alias7, refit7c), `PROFILE.json`, `CLAIM.json`, `evidence/` (142 tamper controls, `retired7/CENSUS-AND-AUGMENTING-PATHS.json`, `OWNER-CHECK.json`) | BORROW-WORD | yes |
| #2802 certified double-move words (same construction, different serialisation of `cleanup`/`warps`/`removed`) | same | same | - | `$S/wt-r10pub/research/t74-r10-hosting-leads/J-dim1/base-words/{b,e}-30_564_667-31_565_669.cert.json.gz` (blob fbd94e7b) + 152 auditor-passing hosted variants `J-dim1/out/eh/w-*.json.gz` (negative-kappa words: useful as "near-miss" controls) | BORROW-WORD | yes |
| #2833 (philippeVV, dirt-entry rewrite; details not held locally) | unverified | - | - | NOT held. `ls-remote`: refs/pull/2833/head = e9307b48. Would fetch with `git fetch origin pull/2833/head` (data only; never execute its code) | BORROW-WORD (expected) | no |
| #2853 (philippeVV, dirt-entry A-phase; ~0.0017193776587 per the 2026-10-16 comment sweep, unverified) | unverified | - | - | NOT held. refs/pull/2853/head = d01045df | BORROW-WORD (expected) | no |
| other machine's line: #2843 (T124, 0.00171865827784172), #2848 (T248 on #2843's fill), #2852 (0.0017186583707) | unverified | - | - | NOT held. heads 47a7227c / c50d12e4 / 2715d686 | - | no |

Older material in the checkout (not in the brief's list, usable as extra FULL-WORD controls): refs `imbpr/858..1169`, `pr/1319..1549`
(e.g. `pr/1377` gmx-t74 exact fill), `$S/tree1148{,b}/research` (77 word-like json.gz), `$S/k566/full{1,2}`, `$S/r2/t1319`, `$S/latest/t1305`.

**Recommended frozen word set W for the two-week plan** (7 constructions, 2 families, 10 word files):
FULL-WORD: #1094 (K8S7), #1672 (gauge44 + extra). BORROW-WORD: #2745 (base + extra), #2751 (base), #2766 (base), #2802 (base + extra).
Held-out for predictions (fetch at M4, data only): #2833, #2853. Idle/fill objects: #2802 FILL/PLAN/DISPATCH/TEMPLATE; #2751 FILL2751; #1672 OWNERS.

## 3. Global objects (#2802; sizes measured)

| file | shape | notes |
|---|---|---|
| `FILL.json.gz` | dict `columns=[time, helper, owner_replica, child, port, offset]`, `rows` 271,728 = 666 times x 408 helpers | time 0..665 (call index), helper 0..407, owner_replica 0..73 (74 replicas), child 0..17, port 0..111, offset 0..36 (18 distinct). Each row is one helper role placed as a compact prefix of `width` cells in the idle cell (replica, child, port) at `offset`. 122,625 distinct (replica, child, port) cells touched; at most 5 roles per cell over all times. |
| `PLAN.json.gz` | T=37 parent plan: `windows` dict[666] `"stage,replica" -> [capacity, [children]]` with capacity hist {8:222,16:148,32:148,48:148}; `order` 333 calls; `sides`, `pairs`; `per_call_widths` 333 x 480 (parent word's inventory {4:40,5:48,7:38,8:114,9:240}); `profile` (T37) {1:779556,2:169496,3:138694,4:42458,5:27306,8:2664,48:11374}; `replica_lift` | the 666-call fill is the replica lift (x2) of this 333-call plan; OWNERS.json reports 1,332 windows |
| `DISPATCH.json.gz` | 666 x `[stage 0..8, replica 0..73, provider]`, providers extra 417 / gauge44 249 | which word runs in which call |
| `GLOBAL-TEMPLATE.json.gz` | `calls` 333 (owners, pair, replica, stage, window, orientation), `idle_children` 2016 `{child, port, rank, replicas:37}` with rank hist {8:672,16:448,32:448,48:448}, `execution_schedule` 32 events, `live` 55832, `bank_padding`, `cover` | capacities of the idle cells = the chip-firing thresholds Lane C needs |
| `evidence/OWNERS.json` | roles 276,390 (#2751 fill), windows 1332, idle, rank_mass 4,816,512 | literal owner check (`independent_owners.py check(plan, template, order, fill, providers, dispatch, expected_profile)`) |

## 4. Toolkit API surface (read; signatures as found)

`$S/wt-r10pub/research/t74-r10-hosting-leads/deps/toolkit-rev3/` (our #1186 rev 3; needs `IMB_ROOT` pointing at a checkout that has
`research/gauge44-frames-x`, `research/complex-k492-owner-repair/vendor/multicold`, `research/frame-domain-ceiling` -> use `IMB_ROOT=$S/wt-r10pub`).

- `frames.Costs(b, scale_bits=184)`: per-rank moment weights at endpoint b (`.c[r]` integer surrogate, `.exact[r]`/`.upper[r]` Fractions, `.profile_cost(H)`, `.moment_exact(H)`).
- `frames.Graph(w, check_literal=True, tail_mutable=False, caps=None, cut_equality=False)`: event graph (one vertex per A/B gate + start/cut/end), L/U domain propagation; attributes `nodes[(regs, frame, section, index)]`, `chains[reg]` (register chains = the climb strings), `lower/upper`, `var`, `dom`, `components`; `.profile(assign)`, `.literal()`, `.edge_list()`. Raises `Infeasible`.
- `frames.optimal_frames(w, costs, verbose=False, max_sweeps=300, ve_tuples=5e6, check_literal=True, graph=None, interval=False)` -> `dict(graph, cost, profile, assign, certified, parts, literal_profile, literal_cost, gain[, interval])`.
- `frames.moment_interval(g, costs, assign, bits=224, ...)` -> rigorous rational interval of the true per-call moment at b.
- `frames.move_window(gates, i)` -> `[lo, hi]` positions gate i can move to by commuting swaps; `frames.moved(gates, i, j)`; `frames.commute(g1, g2)`. (These give the exact **commuting-window null model**, CONTROLS.md N1b.)
- `frames.replay_map(w, sections=("A","cut","B"))` exact composed linear map; `frames.apply_frames(w, g, assign)`; `frames.full_profile(w)`; `frames.load_word(path)`; `frames.from_canonical(w)` (CANONICAL-WORD -> inline).
- `word.inline(word, targets_empty)`, `word.recount(word)` -> `(paid, centre, widths, starts, ends, endB)`; `model.cone_caps(word)`; `kappa.price(local, calls, T, idle)` -> `(kappa, complex_lower)` for the k8/gauge44 outer assembly (T16/T37; NOT the T74 borrow chain); `kappa.global_profile(calls_by_local, idle)`.
- J-dim1 code (BORROW-WORD): `wordmodel.Word(path)` -> `.events` (13,064 time-ordered `(section, item)` incl. `Bwarp`), `.live`, `.helpers`, `.paid`, `.climbs[reg] = [(time, rank, from, to)]`, `.gateframe[t]`, `.centre_paid`, `.start/.end`; `bounds.Bounds(path)` -> `.lo[t]`, `.hi[t]` exact per-gate frame lattice over all refits, `.byreg`, `.ev`; `census_r10.py CODE_DIR WORD OUT` (retired-lender alias census, pairs rules); `relax_r10.py` / `relax_host7.py` (owner-fill pattern relaxation MILP, scipy `milp`); `price_words.py` (certified frames + pinned auditor on a word, ~1 s); `show_life.py` (per-helper event listing).
- #2802 package: `exact_moment.moment_bounds(profile, exponent)` -> `(lower, upper)` Fractions of sum_r c_r (r/73)(73/r)^exponent (DIMENSION 73); root check `$S/r10/mine/root.py` (90-digit bisection, 0.10 s); `independent_owners.windows(template, order)`, `check(...)`; `packing_cap.py` (coverage-law ceiling 0.00175037 on #2751's word; realized fraction 0.981); `generate.py`/`joint_engine.py`/`vendor/generate_words.py` (constructors: rebuild the words from #2679's source; the synthetic-word null N4).

## 5. Loader snippets (tested in this round; run with `-I`)

```python
# strings from a BORROW-WORD (any of #2679/#2745/#2751/#2766/#2802)
import sys, gzip, json
S = "<scratchpad>"; CODE = S + "/wt-r10pub/research/t74-r10-hosting-leads/J-dim1/code"; sys.path.insert(0, CODE)
from wordmodel import Word; from bounds import Bounds
Wd = Word(S + "/wt-claim7/research/t74-joint-twelve-retired7/inputs/WORD-base.json.gz")   # 0.05 s
events = Wd.events                    # [(section, gate_or_warp)] in auditor time order (precondition, compensation, A, cut, B+warps, restore)
climb = {q: [(t, d) for (t, d, _, _) in v] for q, v in Wd.climbs.items()}   # 632 registers, 3-9 jumps each (Lane A "climb string")
b = Bounds(S + "/wt-claim7/research/t74-joint-twelve-retired7/inputs/WORD-base.json.gz")   # 0.22 s; b.lo[t], b.hi[t] per gate time
def token(sec, e):                      # Lane A alphabet (section, op, coefficient class, rank); roles added from Wd.helpers / ports
    if e[0] == "add": return (sec, "add", (e[3], e[4]), len(e[5] or []))
    if e[0] == "scale": return (sec, "scale", (e[2], e[3]), len(e[4] or []))
    return (sec, "warp", None, None)
forward = [token(s, e) for s, e in events if s in ("A", "cut", "B")]        # 5,583 tokens, alphabet 79

# frames graph from a FULL-WORD (#1094/#1672) with the toolkit
import os; os.environ["IMB_ROOT"] = S + "/wt-r10pub"; sys.path.insert(0, S + "/wt-r10pub/research/t74-r10-hosting-leads/deps/toolkit-rev3")
import frames as F, word as Wmod
w = F.load_word(S + "/k8/K8S7-WORD.json.gz"); g = F.Graph(Wmod.inline(w, True), check_literal=True)   # 0.1 s: 1662 vars, 137 comps
chains = g.chains                     # register -> list of event-graph vertices (climb strings with [L,U] domains in g.lower/g.upper)

# fill as bins
fill = json.load(gzip.open(P + "/FILL.json.gz")); rows = fill["rows"]      # 271,728 x [time, helper, owner_replica, child, port, offset]
tpl = json.load(gzip.open(P + "/GLOBAL-TEMPLATE.json.gz")); cap = {(c["child"], c["port"]): c["rank"] for c in tpl["idle_children"]}  # 2016 cells, caps 8/16/32/48
plan = json.load(gzip.open(P + "/PLAN.json.gz")); windows = plan["windows"]  # "stage,replica" -> [capacity, children]

# complete profile -> kappa (exact bracket) and 90-digit root
from exact_moment import moment_bounds   # from the #2802 package dir
```

## 6. Sizes and run times (measured on 1 core, Python 3.14 venv, this machine)

| object / step | size | time |
|---|---|---|
| load one word (gz) | 57-72 KB gz, ~0.5-1 MB JSON | 0.01 s |
| `wordmodel.Word` (events + climbs + frame replay) | 13,064 events, 632 registers | 0.05 s |
| `bounds.Bounds` (exact lo/hi lattice) | 5,470 gates (875 with lo < hi) | 0.22 s |
| toolkit `frames.Graph` on k8 FULL-WORD | 1,662 variables, 137 components, largest 612, max domain 16 | 0.1 s |
| certified `optimal_frames` on a BORROW-WORD (`price_words.py`, per README) | - | ~1 s |
| LZ76 (Kaspar-Schuster) on forward string / whole word | 5,583 / 17,539 tokens | 0.03-0.2 s / 0.4-1.7 s |
| plain Re-Pair (Counter-based, unoptimised) on forward / whole word | 412-526 / 1,127-1,300 rules | 0.05-0.2 s / 0.4-0.9 s |
| FILL load; bin build; one within-bin shuffle | 271,728 rows | 0.06 s; 0.15 s; 0.17 s |
| 90-digit moment root (bisection, 280 steps) | 8-rank profile | 0.10 s |
| exact rational `moment_bounds` at one exponent | - | ~ms |
| owner-fill pattern relaxation MILP (`relax_r10.py`, scipy milp over width patterns) | ~10^3-10^4 patterns | seconds to a few minutes (r10 ran it on 4 cores) |
| literal owner check `independent_owners.py` | 271,728 roles | ~1 min (part of the 50 s - 2 min hook) |
| registered hook `verify.py` + `verify_retired7.py` | 8 states x 2 words, 142 controls | ~50 s (ours) to 2 min; limit 17 min |
| cold `full_replay.py` | whole release | 411 s |

Estimates for what the other lanes propose (single core unless stated):
- Permutation test, 2,000 section-preserving shuffles x (LZ76 + Re-Pair + block entropies) on one whole word: ~2,000 x 3 s = 100 min -> ~10 min on 12 cores; forward-only strings: ~15 min single core. Across the 10-file word set: ~2 core-hours total. Fits the screening budget.
- Commuting-window shuffle (N1b): needs `frames.move_window` per gate (O(n) each) -> ~5,583 x 0.5 ms = 3 s per sample; 1,000 samples = 50 min single core -> 5 min on 12 cores.
- Random frames with fixed Parikh vector (N2): rejection sampling on the `Bounds` lattice is cheap per draw (0.2 s) but the acceptance rate for an exact profile match is unknown; use the profile-preserving lattice random walk (Metropolis on H) instead: ~10^4 steps/s. Budget 10 min per word.
- Chip-firing on the fill: one stabilisation / relaxation pass over 271,728 roles in 1,332 windows is O(roles) ~0.2-0.5 s in pure Python; 1,000 random capacity-respecting fills ~5-8 min single core. Sandpile group of the window graph: Smith normal form of a 1,332 x 1,332 integer Laplacian; `sympy.smith_normal_form` is far too slow at that size (estimate: hours; unverified); PARI/FLINT (`python-flint` `fmpz_mat.snf` if installed) seconds. Lane C should first check whether the window graph is a DAG with a sink (then the critical group is trivial and the question is moot) before computing anything.
- Parikh-cone enumeration (Lane B): rank alphabet {1,2,3,4,5,8,32,48}, mass 4,816,512 fixed; the move alphabet has <= 8 generators; a box of 10^6 lattice points evaluated in float64 numpy takes ~10 s; exact 90-digit roots at 0.1 s each -> reserve exact evaluation for < 10^3 selected points.
- Constructor-synthetic words (N4): `generate.py` rebuilds both #2802 words from #2679's 491-file source in minutes (the "regenerate" path of the README); randomised recipes need the generator's seed points identified first (r6/r7 found that the entering-helper generator is not vendored in the T74 line: FULL-WORD family only via #1297/#1193 `build_word.py` + `WORD-RECIPE.json`). Budget: 1 day of engineering before any sampling.

## 7. Scripts saved in this lane

`inventory_scan.py` (+ `.out`): formats, sections, ranks, coefficient classes, warps, fill/plan/template shapes for the six held words.
`fill_scan.py`, `fill_bins.py` (+ `.out`): FILL columns, PLAN windows, idle-cell capacities, bin occupancy, shuffle timing.
`string_cost.py` (+ `.out`): LZ76 and Re-Pair on the #2802 gate string vs one section-preserving shuffle (whole word and `--forward-only`).
`word_timing.py` (+ `.out`): `Word`/`Bounds` timings, climb-string length histogram, 90-digit root.
