> Package copy of `/Users/mdumitrean/Desktop/dev/aigent/math/prime/new_research_styles.md` (2026-10-16). Paths are repository-relative;
> `$S` in the planning reports denotes the planning scratchpad, whose files are now under `research/styles-r11/planning/` and
> `research/styles-r11/data/`. See `README.md` and `RUNBOOK.md` in this directory.

# Two research styles for the integer-mult-bounds words: L-system descriptions and sandpile / chip-firing analysis. An evaluation plan.

Planning document, round r11, 2026-10-16. Prepared by Marius-Paul Dumitrean with substantial AI assistance (Anthropic Claude, via
Claude Code). No κ claim. Inputs: four lane reports written in this round (`research/styles-r11/planning/{A-lsys-word,B-lsys-growth,
C-sandpile,D-pipeline}/REPORT.md`, with scripts and outputs; about 10 CPU-minutes in total). Every number below was computed on the
real #2802 package (`research/t74-joint-twelve-retired7/`, head `17b2ee6e`) or on the lineage words we hold, by the scripts named in
Appendix C. Companion local work: `class_lsys*.md`, `lsys*_formalism.md`, `lsysff_1_chomsky_position.md` (L-systems);
`SANDPILE_SIEVE_TRIANGLES.md`, `SANDPILE_RESEARCH_PROGRAM.md`, `DUMITREAN_SANDPILE_FACTORING.tex` (sandpiles).

---

## 0. Purpose, scope, verdict of the planning round

Two questions were asked.

1. Can the work be described in L-system terms (an alphabet with replacement rules)? If so, produce the L-system output language and
   analyse it in that form, looking for patterns.
2. Can the work be analysed as a sandpile, looking for patterns that way?

This document says to what extent each description is exact, fixes the objects that the pipeline will produce, and lays out a two-week
evaluation: pre-registered experiments with null models, pass bars, stop rules, a compute budget and a schedule.

**Verdict on (1): yes, at three levels, two of them exact.**
- The *gate skeleton* is recipe output with genuine productions: the cut is the exact product "8 centres x 22 targets" and the cleanup is
  exactly `reverse o inverse o buffer` of the recorded forward program (an anti-homomorphic production; 4,395 of 4,475 cleanup gates are
  inverses of forward gates, the 80 others are restore and warp images). A and B are butterfly motifs (`t += s; s -= t/2` at rank 2 is
  168 of 3,534 A-bigrams: the manuscript's H_0 kernel).
- The *paid profile* is exactly the Parikh vector of per-register **climb strings** (the sequence of frame-rank jumps along each
  register's chain). The climb-string language of #2802 has **56 distinct strings over 632 climbing registers** (null: 358), and 53 of
  the 56 occur in the parent #2751. This is the output language worth analysing: it *is* the paid children, so any pattern in it is a
  pattern in what κ pays for.
- The *κ equation* `sum_r c_r (r/73)^(1-κ) = 66304` is exactly the growth-rate (Malthusian) equation of a one-symbol timed L-system
  `A(e) -> prod_r A(e r/73)^{c_r}`, the Akra-Bazzi / Crump-Mode-Jagers characteristic equation. Its Parikh vector is the complete profile,
  the uniform manuscript model gives κ = 0.001143, and all of 0.0017178 above that is rank concentration. Level sets of κ are hyperplanes
  in profile space (the moment is linear in the profile), so every ceiling is an LP over a reachable class and, to first order,
  **dκ = 1.2422e-10 x dΦ with Φ = sum_r r c_r ln r** (verified within 1.1% on every lineage step we hold). The PR lineage is therefore a
  derivation in a *guarded vector-addition system*: deltas commute, preconditions do not.
- What is **not** local: the frame layer, which decides κ, is a global min-moment certificate (`optimal_frames`), not a rule that reads a
  gate's context. So the plan analyses the climb-string language and the move derivation, not the raw gate string, and every string-level
  "pattern" must predict something the recipe does not already state.

**Verdict on (2): none of the four candidate mappings is an abelian sandpile.** What the sandpile vocabulary points at is exact classical
structure: (i) lender/follower aliasing is **bipartite matching** with Hall/Koenig certificates found by a burning-style alternating search
(the 74-lives-vs-72-registers pigeonhole for followers 670/671 is reproduced exactly; the #2802 gain is literally two augmenting paths of
length 3); (ii) frame climbs are monotone heights with **per-chain conservation and a confluent lattice closure** (the one exact
"abelian" property), plus a concave cost that gives exact merge prices ((1,1)->2 = +1.155e-7 per call, matching #2766's realised
+1.154e-7); (iii) the owner fill is a **capacity/flow system with a concave, clumping objective** (77% of bins are empty-or-full; all 8-
and 16-bins full; of the 33,152 48-bins, 26,558 are empty and 6,594 hold five 9s), the opposite of a recurrent sandpile state; (iv) the
butterfly recursion is a weighted tree with a deficit sink. Ranking by exactness: (i) > (ii) > (iii) > (iv). The plan keeps the exact
certificates (a Hall-deficiency atlas, a max-flow tightness map), one falsifiable structural test (confluence of greedy frame lowering)
and one energy test (decay slope of a rule-preserving random walk on the fill), and drops sandpile-group / identity / burning items
unless the exactness audit revives them. "Never call it a new method" applies.

**Non-claims.** κ is asymptotic and galactic; nothing here changes any real multiplication. No new κ. Every null is protocol-specific
(these alphabets, these statistics, these nulls, these words). Research does not close.

---

## 1. The objects, in one page

**Local word.** A straight-line program over 704 registers (0..111 ports, 112..223 target rows, 224..703 helpers), stored as gzipped
JSON. Sections (#2802 base): `A` 3,535 gates, `cut` 176, `B` 1,872 (+72 warps), `precondition` 192, `cleanup` 4,547, `compensation`
7,130, `restore` 87, `initial_corrections` 36. Gates are `["add", t, s, num, den, frame]` (t += num/den x s) or `["scale", t, num, den,
frame]`; `frame` is a basis (bitmasks over F_2^9) of a nested subspace and its length is the gate's RANK. Two formats exist in the
lineage: FULL-WORD (k8/gauge44/T74-kernel line: #1094, #1195, #1625, #1672) and BORROW-WORD (#2679 ... #2802; adds `warps`,
`compensation`, `restore`, `removed`). Gate syntax and `report` are identical.

**Helpers, lenders, followers.** 408 helpers per #2802 word, width inventory {4:26, 5:2, 7:62, 8:78, 9:240}; width = dim(end frame) -
dim(start frame) = the sum of the helper's climb string. A follower may enter a retired lender's register through one B warp with an
invertible G (an alias), deleting its private register.

**Paid profile and climb strings.** The local profile {1:2382, 2:648, 3:268, 4:128, 5:26, 8:8} (mass 5,188 per call) is the histogram
of positive rank jumps along every register chain plus one rank-8 child per centre. `extract_strings.py` (Lane A) reproduces it exactly
on all four words we tested (#2802 base/extra, #2751, #2462); this extraction is the canonical one for the plan (section 3.2).

**Owner fill.** 666 calls x 408 helpers = 271,728 roles placed in 1,332 windows x 112 ports = 149,184 bins of capacity 8/16/32/48,
under time-eligibility intervals, one role per helper per call, one role per family per call, prefix-compact bins. Unused cells are idle
remainder children: {1:17316, 3:6594, 5:9878, 32:1, 48:26558}.

**Complete profile and κ.** c = 666 x local + idle = {1:1603728, 2:431568, 3:185082, 4:85248, 5:27194, 8:5328, 32:1, 48:26558};
rank mass sum r c_r = 4,816,512 = 72 x 66304 + 64 x 666 (coverage identity: fixed by the template, so every word/fill move is
mass-neutral). κ is the root of `sum_r c_r (r/73)^(1-κ) = 66304`; `(r/73)^(1-κ)` is strictly subadditive in r, so merging children
raises κ and splitting lowers it. Root: 0.0017177949841186346638272299... (certified endpoint 0.001717794984118634663827).

**Lineage as rewriting history.** Each PR is a small edit: refits (frame lowering at fixed order), retired-lender aliases, hostee moves,
width cuts, helper deletions (donor kernels, twelve-source recovery), cold-host merges, pre-life hostings, dirt-entry rewrites,
owner-fill re-tilings. #2751 -> #2802 touches 88 B gates (63 relabelled, 25 frame-only), 12 A frames, 1 restore frame, 7 warps.

---

## 2. Findings of the planning round, in one table

| style / level | mapping | exact? | output object to analyse | grounding number (#2802) | go / no-go |
|---|---|---|---|---|---|
| L1 gate skeleton | recipe productions; cut = 8x22 product; cleanup = rev o inv o buf; A/B butterfly motifs | exact for cut, cleanup, compensation; recipe for A/B | per-section token strings (6 alphabets) | LZ76 1,066 vs 3,968+-9 (section shuffle) vs 3,094+-21 (dataflow-preserving); forward-only 302 vs 1,846 | go, as a screen only (most structure is the recipe's emission order) |
| L2 climb strings | per-register rank-jump strings = paid children | exact (profile reproduced) | the climb-string multiset per word; role-typed vocabulary | 56 distinct strings / 632 registers (null 358; within-register null 190); 53/56 shared with #2751, 49/56 with #2462 | **go: the main L-system output language** |
| L3 growth / Parikh | one-symbol timed L-system; κ = Malthusian rate; moves = guarded Parikh deltas | exact | the Parikh ledger of every lineage step; the move alphabet; the ceiling ladder | dκ = 1.2422e-10 dΦ within 1.1% on 3 steps; uniform model 0.001143; ceilings 0.0017474 (idle <= 48), 0.0017581 (packing cap) | **go: landscape, ceilings, search objective** |
| S1 aliasing | bipartite matching lives vs slots; hostee moves = augmenting paths | exact (classical) | Hall-deficiency atlas per word | 122 lives, 402 slots, max matching 72 = current aliases; hi >= 4 lives 74 vs 72 slots (670/671 pigeonhole); 48 hi-1 followers degree 0 | go, as certificate/screen (not chip-firing) |
| S2 frame climbs | monotone heights; per-chain conservation; confluent L/U closure; concave cost | structure exact; dynamics heuristic | merge price list; coalescence ceiling | (1,1)->2 +1.155e-7/call (= #2766); coalesced-climb ceiling 0.0028258 | go, one falsifiable test (confluence) |
| S3 owner fill | capacity/flow system; concave clumping objective; no toppling, not abelian | conservation/thresholds exact; no dynamics | occupancy histograms; walk decay curve; max-flow tightness map | 77.35% bins empty-or-full; κ after 1k/10k/300k random rule-preserving moves 0.0017155 / 0.0016973 / 0.0015666 | audit first; energy test only |
| S4 recursion | weighted tree with sink (deficit 2 x 11,840 = 23,680 rank units) | conservation only | none | 73 x 66304 - 4,816,512 = 23,680 | no-go (restatement) |

---

## 3. Style 1: L-system descriptions

### 3.1 Three levels, and what is exact at each

**Level 1, skeleton (Lane A).** Alphabets are exact functions of the JSON: token = (section, op, coefficient class, role(target),
role(source), rank, climb(target), climb(source)), roles P port / T target / C centre / H helper / L lender before its warp / F the same
register after the warp / X removed. Granularities: `full` (541 symbols), `mid` = (section, op, coef, rank) (116), `rank` = (section,
rank) (21), `op` (63). Exact productions found: `cut` = product of the 8 centres with 22 targets each (coefficients +-1/4, each target
receives two centres); `precondition` = a fixed per-target motif; `cleanup` = `rev o inv o buf (A + warps + B + restore)` (the auditor's
own rule); `compensation` = algebraically derived response columns (not a string rewrite). Consequence for every statistic: `cleanup` and
`compensation` are *derived text* and must be excluded from, or re-derived in, every null (including them inflates compressibility ~2x).
In Chomsky terms the skeleton is produced by a staged recipe (parametric D0L/DT0L with stages as tables); the κ-relevant edits are
context-sensitive productions with bounded support (an alias touches ~14 gates + one warp + one chain deletion) and a *global guard*
(frame feasibility of the whole lattice, certified by `optimal_frames`): outside ET0L.

**Level 2, climb strings (Lanes A, B, C).** For each register: `start -> A events -> (cut descents for centres) -> B events (warps =
unpaid frame replacement) -> restore events -> end`; the string is the sequence of positive rank deltas. Invariants: per-chain conservation
(jumps sum to width); mass 5,188 per word; the number of jumps is *not* invariant (merges are the only gains). Vocabulary on #2802:
ports 11 strings, targets 9, centres 2, followers 5, helpers 33; top strings `11112111` x64, `11141` x37 (ports), `11411` x30 (targets),
`1111` x26 (width-4 helpers), `32111` x25, `1151` x24. Per-register strings are identical on 704/704 registers base vs extra, 648/704
#2751 vs #2802, 591/704 #2462 vs #2802, and the differing registers are exactly the edited lenders/followers/targets.

*Convention note.* Lane B's simplified extraction (A, cut, B only; centres as one rank-8 child) carried a fixed offset {1:8, 2:36, 4:-10}
against the reported profile on both words, which cancels in every lineage diff; Lane A's extraction (restore events and centre paths
included) reproduces the profile exactly. The plan adopts Lane A's as canonical and checks parity on all 12 word files at M0 (P1).

**Level 3, growth functions and the move algebra (Lane B).** From `05-layers.tex` 632-683 generalised to one call at parameter
`e r/73` per rank-r child: `F(e) = sum_r (c_r/W) F(e r/73)`, `F ~ e^(1-κ)`, W = 66304. Mapping table:

| L-system notion | here |
|---|---|
| alphabet | ranks {1..9, 16, 32, 48, 51}; one nonterminal A(e) |
| production | A(e) -> prod_r A(e r/73)^{c_r}, each child weighted 1/W |
| Parikh vector of the right-hand side | the complete profile c |
| growth rate | root of sum_r (c_r/W)(r/73)^(1-κ) = 1 (Akra-Bazzi; Malthusian parameter of the reproduction measure sum (c_r/W) delta_{ln(73/r)}) |
| D0L growth matrix / Perron root | the degenerate 1x1 case (manuscript: κ = 1 - log_m(s/W)) |
| output language | none beyond the one equation: the view is exhausted here; all content sits in the Parikh deltas and their guards |

Landscape facts (exact): M(κ; c) is linear in c and increasing in κ, so {c : κ(c) >= k} is a half-space; κ has no interior local optima
on the mass hyperplane; its maximum over any polytope of reachable profiles is attained at a vertex and is a parametric LP (what
`packing_cap.py` and PR2679's `ceil74.py` compute, with dual certificates). Price table at the #2802 root: one added rank-r child costs
-7.285e-8 (r = 1) ... -5.279e-6 (r = 73); per unit of mass the price is nearly flat (-7.285e-8 to -7.231e-8), so every gain is a small
difference of per-mass prices. First-order law: dκ = λ dΦ, Φ = sum_r r c_r ln r, λ = κ/(73 D) = 1.2422e-10 (D = dM/dκ = 189,435.57).

The move alphabet (productions on climb strings with Parikh deltas and guards):

| production | string / fill effect | Parikh delta per call | guard | known value |
|---|---|---|---|---|
| refit | re-partition one register's climb at fixed endpoints | mass 0; #2766: {1:-2, 2:+1} | exact propagated floor; certified frames say none remain at fixed order | +1.154e-7 (#2766) |
| retired-lender alias | delete follower's string (width w); extend lender's string; fill loses one width-w role | local mass -w, idle +w | dim U_lender = entrance dim of follower; lender retires before follower enters; G(U) = E; every lender floor >= 4 here | five aliases +1.523e-7 total (retired5) |
| hostee move | transplant a hosted climb to a free retired lender (with a refit of its last gate) | 0 by itself; frees a lender | free, floor <= entrance dim, retires in time; 192 augmenting paths, only 564/565 qualified | enables +3.857e-7 (#2802 step) |
| width cut | shorten a helper's string by its last piece | local {1:-1}, idle +1 (or merged) | restorable end frame | relaxation +5.9e-7/step, all exact edits negative (lane H) |
| helper deletion | delete a width-w string | local -string, idle +w | kernel identity (symbolic replay) | width 8: +8.8e-7..+1.39e-6 clean, -5.1e-7 if packed as rank-1 remainders |
| cold-host merge (4,8)->7 | two strings become one of width 7 | local {3:-1, 2:-1}, 5 cells freed | exact undo of follower writes (open lead J) | +8.703e-7 with the recorded relaxed fill (reproduced from Parikh vectors) |
| pre-life hosting | one role fewer per call | idle +width | PR2679 rule | +6.7e-7 each |
| owner-fill re-tiling | idle histogram re-optimised | idle delta only | window eligibility, capacities | fill lever at its fixed-inventory optimum (#2733 certificate, 5.8e-17) |
| dirt-entry rewrite (#2833/#2853), T124/T248 | A-phase kernel change: new strings | unknown (fetch as data) | kernel identity | +8.6e-7, +7.2e-7 steps |

Ceiling ladder (each row relaxes the reachable set; "falsified by" = a PR above the row while staying inside the stated class):

| relaxation | κ | falsified by |
|---|---|---|
| A actual #2802 | 0.0017177949841 | - |
| B fixed local word, all idle mass in rank-48 children (bins <= 48, integral) | 0.0017473945 | any fill of #2802's words above it |
| C fixed local word, idle as fractional rank-51 children (= `packing_cap.py` 0.00175808593463, realised 0.977) | 0.0017580859 | any hosting of this word above it |
| PR2679 `ceil74` class level (every fill of the 415-helper inventory) | 0.0017151404 | a fill of THAT inventory above it; the lineage passed it by leaving the class (#2751 changed the local word) |
| S2 coalesced climbs (every register climbs in one jump, real idle) | 0.0028258 | any frame-only or order-only edit at fixed widths and fill above it |
| E all local children at rank 9, idle at 51 | 0.0030578 | frame rank > 9 or idle > 51 |
| G uniform manuscript model (all rank 1) | 0.0011431 | - |

The headroom is in local climb fragmentation (A -> E: +1.34e-3), not in idle fragmentation (A -> B: +2.96e-5; small idle remainders
carry 86,520 of 1,361,304 idle units). Since certified frames are optimal at fixed gate order, that headroom sits behind gate order and
kernel structure, i.e. behind the context-sensitive productions where the newest PRs gained.

Lineage as derivation (the three steps we hold, exact roots vs the log-rank law): #2751 -> #2766 {1:-1332, 2:+666} +1.15387e-7 vs
+1.14688e-7 (1 frame); #2766 -> retired5 {1:+14652, 2:-3330, 3:-15318, 4:+5328, 5:+3330} +1.52343e-7 vs +1.54013e-7 (49 registers);
retired5 -> #2802 {1:-2664, 2:+3996, 3:-3996, 5:+1332} +3.85668e-7 vs +3.83628e-7 (10 registers). Φ per call per step: 1.39, 1.86,
4.64 (not diminishing); the lineage is a sequence of class exits.

### 3.2 The output language the pipeline will produce

For every word in the frozen set W (section 5), `styles/pipeline/` emits:
1. **Section strings** at the six alphabets (forward sections A, cut, B with warps as letters; precondition; `cleanup`/`compensation`
   only as derived text with their derivation checked, never as independent strings).
2. **The climb-string multiset**: one string per register with role, entrance dim, width, first/last gate motif; the profile check
   against `report.local_profile` is part of the emission (exact equality required).
3. **The Parikh ledger** of every lineage step: (local delta per call, idle delta, Φ gain, productions used, preconditions consumed /
   created, registers touched, exact dκ, law dκ). The three steps above are the first entries.
4. **The move census** of the word: feasible productions per class (alias pairs by the exact lo/hi rule, refittable gates with slack,
   hostee augmenting paths, cuts), each with its Φ.
These four files are "the L-system output language" in the sense of the question; the experiments below analyse them.

### 3.3 Experiments (pre-registered; nulls in section 6)

| id | question | data | method | null / control | pass bar | cost | if positive |
|---|---|---|---|---|---|---|---|
| L-1 skeleton grammar (A-E1) | is the A/B skeleton a parametric D0L with position-independent rules? | A/B of >= 5 words incl. #2833/#2853 as data | Re-Pair/Sequitur on register-renamed k-grams; extract rules; replay | N1, N1b, N4 | one rule set <= 200 rules regenerates >= 3 skeletons exactly; cross-word rule overlap >= 90% | 1 core x 10 min | a declarative recipe; feeds the move alphabet |
| L-2 forward/cleanup production (A-E4) | `cleanup = rev o inv o buf(recorded)` on every word? | all of W | exact replay in our alphabet | none (verification) | exact equality on every word; a violation is a data error | minutes | fixes the first exact production; cleanup never a string of its own |
| L-3 periodicity census (A-E5) | periods tied to h = 9, 8 centres, 22, v = 112, 73, 666? | A/B strings + global template programs | lag-match spectra, autocorrelation per alphabet | N1b, N1 | a peak z >= 5 over N1b at a lag explained by a named parameter; current: peaks at multiples of 4 (butterfly fans), none at 9/73/112 | minutes | else record the protocol-specific null |
| L-4 climb-string predictability (A-E2) | is a register's jump string a function of local data (role, entrance dim, width, first/last motif)? | 632 strings x >= 5 words | lookup table / shallow tree, leave-one-word-out | strings permuted among registers of the same role (358 distinct vs 56) | >= 90% exact prediction on the held-out word vs <= 50% null | 1 core x 5 min | frames readable from the skeleton (an L-system labelling exists); negative confirms frames are global |
| L-5 alias-feasibility motif (A-E3) | does a local motif around (lender last gate, follower first gate) add information beyond the exact lo/hi rule? | 72 realised aliases + J-dim1 census (404 lenders x 52 followers) + S-1 atlas as ground truth | k-gram context with rank/role; logistic or rule screen; score the 192 augmenting paths | labels permuted; rank-only features (the floor rule) as the baseline model | AUC >= 0.9 held-out AND the two realised moves (401->564, 403->565) in the top 5 of 192, beyond the floor rule | 1 core x 20 min | a string-level pre-screen for aliases on new words before the exact lattice |
| L-6 log-rank law audit (B-B1) | does dκ = λ dΦ predict every lineage step and the κ order of all words? | complete profiles of #1094, #1672, #2474.., #2751, #2766, #2802, #2833, #2853 (CLAIM.json as data) | exact roots vs λ dΦ | random mass-neutral deltas of the same L1 size | every step within 2%; pairwise κ order reproduced by Φ | 1 core x 5 min | Φ (integer-linear) becomes the search objective; exact root for certification only |
| L-7 derivation decomposition (B-B3) | does each lineage step decompose into productions of the move alphabet? | consecutive word pairs | per-register climb diff -> production labels; sum of labelled deltas = recorded delta; auditor runs of swapped orders | random register relabelling (must not decompose) | every step decomposes exactly; non-commuting pairs identified | 2 cores x 15 min | a derivation DAG with gain per application |
| L-8 class ceilings with dual certificates (B-B4) | tighter falsifiable ceilings per class | #2802 words + PLAN windows | parametric LP with dual: fixed-inventory pattern LP (408 helpers), idle <= 48 integral, helper-removal envelope κ_max(k aliased) | relaxations must dominate every held fill | each ceiling names what a violating PR must have changed | 2 cores x 10 min | ceiling ladder published with each claim; PR triage |
| L-9 saturation census (B-B5) | which production classes are empty on the current word? | current word | enumerate feasible productions per class with Φ | random lender/follower pairings (expected 0) | a predicted empty class a later PR could violate | 1 core x 10 min | frontier map: which class must be exited next |
| L-10 partition extremality (B-B6, C-E3) | is the real word's Φ extremal among re-partitions of each helper's width? | climb strings of >= 3 words | compare Φ / moment with random compositions (same widths, same part counts) | random compositions | real below 99% of null on every word; merge prices match realised margins within 1% | 1 core x 5 min | quantifies partition vs order in the headroom |
| L-11 multi-type check (B-B7) | any orientation/stage with a different child profile? | GLOBAL-TEMPLATE (333 calls x 2 orientations) | child profile per orientation / stage | - | prediction: all identical (1x1 growth matrix); a difference makes κ a matrix Perron root | 1 core x 2 min | - |

---

## 4. Style 2: sandpile / chip-firing analysis

### 4.1 Exactness audit (done at planning time; to be re-run as M2 on >= 3 words)

| mapping | exact content | not exact / absent | status |
|---|---|---|---|
| (i) aliasing: lives L (helpers entering in B with non-empty start frame) vs slots S (free retired registers + the 72 lenders' own-life segments); edge iff last(s) < first(l) and lo(s) <= hi(l) | one slot per life; max matching = max aliases; Hall deficiency = unhostable lives; augmenting paths = hostee moves; Koenig alternating search = the "burning" | no chips, thresholds, group or identity; refits change lo(s), so the honest model is weighted matching with activation costs | keep as certificate (S-1) |
| (ii) frame climbs: heights = frame dim along each chain | per-chain conservation; L/U propagation is a monotone closure with order-independent least/greatest fixpoints (Knaster-Tarski; the same mechanism that makes Dhar burning order-independent); concave cost => merge prices, coalescence ceiling | heights never decrease (no toppling); the optimum is a chain-dual LP, not a stabilisation; confluence of greedy lowering untested | keep: one falsifiable test (S-2), price list (S-3) |
| (iii) owner fill: 149,184 bins, thresholds 8/16/32/48, chips = roles of five sizes, directed time structure | conservation (3,580,416 cells = 2,219,112 used + 1,361,304 idle); stability = feasibility; relaxation = min-cost flow with concave objective (`PLAN.solver_status`: exact integer flow and matching) | no toppling rule in the object; any invented overflow rule is order-dependent (indivisible chips of five sizes, family constraints: outside Bond-Levine abelian networks); the divisible sandpile (Levine-Peres) is convex/spreading, the wrong sign | audit first; energy test (S-4), repair test (S-5), tightness map (S-6) |
| (iv) recursion | conservation with a deficit sink | nothing else | drop |

Grounding on #2802 (scripts in Appendix C): all 49,728 cap-8 bins full (one role each); all 33,152 cap-16 bins full (two roles);
cap 32: 5,957 full, 17,316 at 31 (idle 1), 9,878 at 27 (three 9s, idle 5), 1 empty; cap 48: 26,558 empty, 6,594 at 45 (five 9s, idle 3).
Eligible windows per call: min 6, mean 310, max 444; demand 3,332 cells per call. Greedy random fills that respect every rule strand
2.8-3.5% of roles (the window system is tight: a random capacity-respecting fill needs a flow construction, not a greedy). Rule-preserving
single-role random walk from the real fill: κ 0.0017155 / 0.0017111 / 0.0016973 / 0.0016677 / 0.0016127 / 0.0015666 after 1k / 3k /
10k / 30k / 100k / 300k moves (two seeds agree to 4 digits; initial slope ~2.3e-9 per move; the fill's lead over its own randomisation is
~1.5e-4, two orders above PR-scale gains). Lives vs slots: 122 lives (48 followers at ceiling 1, 74 at ceiling >= 4), 402 slots (330 free
with floors {6:124, 7:14, 8:192}; 72 occupied with floors {4:62, 5:10}); time alone never blocks (matching 122); time + frame gives
matching 72 and Koenig deficiency 50; restricted to ceiling >= 4: 74 lives, neighbourhood 72 slots. For 670/671 the time-feasible slots
by (floor - ceiling) are -1: 24 (all occupied), +1: 8, +2: 8, +3: 40.

### 4.2 Experiments

| id | question | data | method | null / control | pass bar | cost | if positive |
|---|---|---|---|---|---|---|---|
| S-1 Hall-deficiency atlas (C-E1) | does the lives-vs-slots graph predict exactly which lives are hostable in every lineage word, and is any augmenting path left? | words of #2751, #2766, #2802, #2833, #2853; census via J-dim1 code + toolkit L/U | matching, Koenig burning set, near-miss table (floor - ceiling = 1) per word | floors permuted among slots and first-times among lives (histograms kept) | the violator set reproduces every realised alias/hostee move of the lineage and gives a per-word statement ("no augmenting path" or an explicit one) | 1 core x 5 min/word | an exact alias-feasibility certificate per package; extension to min-cost augmenting paths with refit costs = the hostee-move search |
| S-2 confluence of greedy frame lowering (C-E2) | do random maximal sequences of single-gate lowerings (nested, moment-decreasing) all end at the certified optimum? | #2802 base/extra; toolkit L/U | 100 random orders from the U-labelling; terminal profiles | certified optimal profile as reference | >= 95/100 orders end at the certified profile = confluent (then attempt a potential-function proof); many terminals = the abelian analogy is dead here | 2 cores x 15 min | a monotone "which gates can still be lowered" test as a cheap refit screen |
| S-3 merge prices vs realised margins (C-E3 = L-10) | see L-10 | | | | | | |
| S-4 fill energy (C-E4) | is the initial decay slope of the rule-preserving walk the first-order concavity prediction? | fills we hold (#2751 FILL2751, #2802 FILL, #1672 OWNERS) + #2853 at M4 | walk at 1k..300k moves; clumping index; predicted slope = mean split/merge moment delta | the walk is its own null; 2 seeds | slope within 10% of prediction on every fill; clumping >= 0.75 on all fills | 1 core x 2 min/fill | additive local energy justifies local pricing of width edits; otherwise retire the fill-as-sandpile reading |
| S-5 order-independent repair (C-E5) | is there an order-independent local repair of an overflowing fill, and how far from the exact re-host? | #2802 fill + one width perturbation (9->8 or 8->9 on one helper) | overflow rule: an over-capacity bin pushes one random role to a random eligible bin; 100 orders; compare with relaxation/MILP | identical-terminal rate across orders; exact re-solve as reference | >= 95% identical terminals = abelian (not expected); useful bar: repair within 1e-8 κ of the exact re-host on >= 90% of perturbations | 2 cores x 10 min | a cheap hosting oracle for width edits (today: MILP per candidate) |
| S-6 max-flow tightness map (C-E6) | where is the window system tight, and does that explain "promotions lose under real hosting"? | #2802 fill, windows, widths | calls-vs-windows transportation max-flow (scipy); min-cut slack per call set; Hall-type demand(T) <= cap(W(T)) | the same flow on jittered eligibility intervals | explicit binding intervals with slack 0; prediction: a width increase on helpers hosted in binding intervals forces >= 1 rank-1 idle child, checked against the recorded promotion losses | 1 core x 5 min | an exact feasibility screen per word edit before any owner fill |

Dropped unless M2 revives them: sandpile group, recurrent configurations, identity element, Smith normal form of a window Laplacian.
No graph Laplacian is intrinsic to any of the four objects; inventing edges between bins or gates would be a modelling choice, and the
time-eligibility structure makes the natural directed object a sink-DAG (trivial critical group). The local corpus has no general
stabiliser / burning / SNF code (only `circ_laplacian` in `_exp_sandpile_beyond.py` and the mod-p `topple/land` of the waterfall viewer);
if S-2 needs one it is a 40-line function.

---

## 5. Data, loaders, held-out words

**Frozen word set W** (10 word files, 7 constructions, both formats; all held as data; blob ids in `planning/D-pipeline/DATA-INVENTORY.md`):
FULL-WORD: #1094 selected seven-slot k8 (κ 0.001672660197076918; from `origin/main`'s `selected-replay.tar.gz`), #1672 "566+554"
gauge44 + extra (0.001676938111022438). BORROW-WORD: #2745 base + extra (0.0017161404), #2751 base (0.001717141586348426),
#2766 base (0.001717256973467002; its head e6df920c is reachable only through `FETCH_HEAD`: re-fetch `pull/2766/head` before M0),
#2802 base + extra (0.001717794984118634663827). Intermediate lineage words for the derivation analysis (held): #2679, retired5.
Global objects: #2802 FILL/PLAN/DISPATCH/GLOBAL-TEMPLATE, #2751 FILL2751, #1672 OWNERS. Near-miss controls: the 152 auditor-passing but
κ-negative hosted variants in `research/t74-r10-hosting-leads/J-dim1/out/eh/` and the 142 tamper mutants of #2802.
**Held-out** (fetched at M4 only, `git fetch origin pull/N/head`, data only, code never executed): #2833 (e9307b48), #2853 (d01045df).

**Loaders** (tested; snippets in `planning/D-pipeline/DATA-INVENTORY.md` section 5): `wordmodel.Word` + `bounds.Bounds` (byte-identical copies of #2745's
handoff code in `research/t74-r10-hosting-leads/J-dim1/code/`) for BORROW-WORDs (13,064 events, 632 registers, exact per-gate lattice [lo, hi]: 875 of 5,470 gates
have slack; 0.05 s + 0.22 s); toolkit-rev3 `word.inline` + `frames.Graph` for FULL-WORDs (1,662 variables, 137 components; 0.1 s);
`frames.move_window` gives exact commutation windows; a normaliser emits the same token stream from either format. Fill: 271,728 rows
`[time, helper, owner_replica, child, port, offset]`; 2,016 idle cells with capacities from `GLOBAL-TEMPLATE.idle_children`; T37
`PLAN.windows` lifted to the 1,332 windows. κ: `exact_moment.moment_bounds` (exact rational bracket, ms) and the 90-digit bisection
(`research/styles-r11/pipeline/root.py`, 0.10 s).

**Run times** (1 core): LZ76 on the forward string 0.03-0.2 s, whole word 0.4-1.7 s; Re-Pair 0.05-0.9 s; Word/Bounds/Graph < 0.3 s;
certified `optimal_frames` ~1 s; fill load + bins 0.2 s; one fill stabilisation pass 0.2-0.5 s; literal owner check ~1 min; registered hook
~1-2 min; `full_replay.py` 411 s (not needed). Permutation tests at n = 2,000: ~10 min per whole word on 12 cores, ~15 min single core on
forward strings; commuting-window null ~3 s per sample (5 min per 1,000 on 12 cores); Parikh-cone box of 10^6 points ~10 s in numpy.
Hour-scale and avoided: sympy Smith normal form of a 1,332-node Laplacian; constructor re-generation engineering (one day).

---

## 6. Controls, statistics, evaluation criteria, stop rules (Lane D; binding for all experiments)

**Null models** (a claim must beat N1 and the strongest null that applies):
- N0 i.i.d. token resampling (unigram); N1 section-preserving gate shuffle of the forward sections (cleanup/compensation excluded or
  re-derived); **N1b commuting-window shuffle** (each gate moved uniformly inside its exact commutation window `frames.move_window`;
  preserves every section's linear map); N1c register relabelling (kills index-numbering artefacts: helper numbers follow build order);
- N2 random frames with the same Parikh vector (profile-preserving lattice random walk on `bounds.Bounds` / `Graph.lower/upper`); N2b
  certified-optimal frames vs shipped frames (a pattern must be present in the optimum);
- N3 random capacity-respecting fills built by max-flow (greedy fills are infeasible: section 4.1), with the pattern relaxation optimum as
  the ceiling control; N4 constructor-synthetic words (randomised recipe choices; one engineering day, conditional, see section 10);
  N5 cross-family (FULL-WORD vs BORROW-WORD); N6 near-miss controls (152 PASS-but-losing words, 142 FAIL mutants).
- Sandpile-specific: random initial configurations with the same chip count; random graphs with the same capacity sequence; the
  relaxation optimum as the continuous control. Growth-specific: random mass-neutral deltas of the same L1 size; random orderings of the
  derivation (order must not change the end κ; an order effect is a bookkeeping bug).

**Statistics.** LZ76 (Kaspar-Schuster), Re-Pair / Sequitur grammar size, block entropies h_1..h_6, maximal-repeat census (length >= 4,
count >= 3, suffix array), periodogram peaks at 9/8/22/112/73/480/666/1332. Effect size = compression ratio CR = null mean / real;
motif enrichment = real / null mean. Significance = permutation p = (1 + #{null >= real}) / (1 + n) (never p = 0); z is reported but is
not the decision statistic (null distributions of compressibility are tight: |z| > 10 is routine and meaningless alone). Pre-register the
test family (example M1 screen: 6 alphabets x 5 statistics x 10 files x 2 nulls = 600 tests); BH-FDR 5% on permutation p with
n >= 2,000; tests added after seeing data are exploratory and get no q-value. Fixed seeds, blob ids and script sha256 in every result;
a decision stands only if a second seed reproduces it.

**A finding is a pattern only if all five hold:** (1) reproducible on >= 3 words of W including both families, or declared family-local
with >= 3 words of that family; (2) beats the null by the stated margin: CR >= 1.5 vs N1 and >= 1.2 vs N1b; motif enrichment >= 2x at
q < 0.01; sandpile invariants outside the central 99% of the matched null on each word; (3) yields a falsifiable prediction checkable
with the exact tools in <= 1 core-hour (which registers admit aliases; which gates sit at their floor; the cone and κ bound of the next
word; which window classes hold remainders); (4) passes a held-out check on a word not used to find it; (5) is non-circular: not a
function of the local profile, rank mass or width inventory (check: recompute on an N2 sample; if it does not move, it is a profile
restatement).

**Stop rules.** String lane: no (alphabet, statistic) pair at CR >= 1.2 vs N1b on >= 3 words after M1 -> stop and record the null.
Sandpile lane: fill mapping not exact (roles not conserved under the real rules, or stabilisation does not reproduce the literal idle
profile) -> heuristic, one experiment only; group/burning items stay dropped. Growth lane: if the move alphabet reproduces every lineage
delta but predicts no ceiling tighter than the packing cap -> bookkeeping result, stop. Any lane: two consecutive pre-registered
experiments at null -> stop that lane for the round. Whole plan: hard stop at the end of week 2; the deliverable is the document with the
nulls, whatever the outcome.

---

## 7. Compute plan

12 cores total; a lane holds at most 4 while another runs, 12 when alone. Screening runs <= 20 core-minutes; confirmation runs <= 2
core-hours; whole plan ~40 core-hours (M1 ~6, M2 ~4, M3 ~2, M4 ~6, slack). `multiprocessing.Pool(processes=n, maxtasksperchild=50,
initializer=_limits)`, every task via `apply_async(...).get(timeout=T)` (default 300 s; TIMEOUT recorded, never silently retried); RSS cap
4 GiB per worker (6 GiB for fill experiments) by `setrlimit` where enforced and a 2-second `ru_maxrss` watchdog with `os._exit(3)` on
macOS; peak RSS projected before launch (workers x (word 30 MB + fill 250 MB + working set) < 24 GiB); large PLAN/OWNERS files loaded once
in the parent; no solver > 10 min inside a permutation loop; MILP relaxations once per word, never per null sample. Every run writes
RESULT.json (blob ids, script sha256, seed, n, wall/CPU seconds, peak RSS).

---

## 8. Schedule (two weeks, 10 working days from kick-off K)

| day | milestone | work | deliverable |
|---|---|---|---|
| K+1-2 | **M0 pipeline + exact bookkeeping** | freeze W; re-fetch #2766; loaders for both formats; canonical climb extraction with profile parity on all 12 files (P1); the six alphabets; nulls N0/N1/N1b/N1c/N2/N3; statistics harness; pool with caps; result schema; smoke test reproduces the grounding numbers. Cheap exact items run now because everything else uses them: Parikh ledger of every held step (L-6, L-7 first pass), Hall-deficiency atlas and max-flow tightness map on #2802 (S-1, S-6), forward/cleanup production check (L-2) | `pipeline/`, `SMOKE.json`, `LEDGER.json`, `ATLAS-2802.json`, `FLOW-2802.json` |
| K+3-4 | **M1 string screen** | pre-registered L-1/L-3 screen (alphabets x statistics x W x {N1, N1b}, 2,000 permutations), motif census, period scan, FDR table, N5 split; L-4 climb-string predictability; L-5 alias motif screen scored against the S-1 atlas | `A-SCREEN.json`, surviving (alphabet, statistic) pairs with CR and q; `L4.json`, `L5.json` |
| K+5 | **M2 sandpile exactness audit** | within-window stabilisation parity with the literal idle profile; sink-DAG check of the window graph; S-2 confluence; S-4 walk slopes on >= 3 fills; decide keep/drop for S-5 | `C-EXACTNESS.md`, `C-FILL.json` |
| K+6-7 | **M3 growth / Parikh** | L-8 ceilings with dual certificates; L-9 saturation census; L-10 partition extremality; L-11 multi-type check; the lineage derivation re-played (commutation and saturation checks); unavailable productions from the scoped negatives | `B-MOVES.json`, `B-CONE.md`, ceiling ladder |
| K+8 | **M4 predictions + held-out** | each surviving pattern -> one falsifiable prediction; fetch #2833/#2853 as data; run the exact checks (census / bounds / fill / root), <= 1 core-hour each; record pass/fail | `PREDICTIONS.json` |
| K+9 | **M5 write-up** | fill the results sections of this document; nulls written as protocol-specific; prior-art appendix with verification flags | draft v1 |
| K+10 | **M6 review + feedback decision** | review; decide which predictions become census targets for the next κ round (handed over as targets, never as claims); memory digest; next-round questions | final document + digest |

Priority of first compute: the exact, reusable items (S-1, S-6, L-6/L-7 ledger, L-2) before any screen; then L-4 and L-5 (the two string
tests with a falsifiable outcome); then the M1 screen.

---

## 9. Deliverables and how results feed back into the κ work

Deliverables: `styles/pipeline/` (loaders, extraction, nulls, statistics harness, schema), the four output-language files per word
(section 3.2), the Hall atlas and flow map per word, the Parikh ledger and ceiling ladder, `PREDICTIONS.json` with outcomes, this document
completed, and a memory digest entry.

Feedback. A positive pattern produces a *census target* (register set, gate set, window class, Parikh move) that the existing exact
pipeline prices in the usual order: census -> stage build (`alias_build`, `refit`, hostmove) -> pinned PR2679 auditor -> certified frames
(`optimal_frames`) -> literal owner fill (`independent_owners.py`) -> exact root (`exact_moment.moment_bounds`) -> `full_replay.py`. Only
that chain changes κ; the styles propose targets. Specific hand-overs already visible from the planning round: Φ as the integer-linear
objective inside hosting/alias/refit searches (exact root for certification only); the Hall atlas as an alias-feasibility certificate
attached to packages, and its weighted-matching extension (refit costs as edge weights) as the hostee-move search; the max-flow map as a
feasibility screen before any owner fill; the ceiling ladder stated with each claim (for #2802's local word: 0.0017474 for any fill with
bins <= 48). A null is recorded with its protocol and prunes later rounds (e.g. "no motif predicts alias feasibility beyond the floor
rule" ends motif-driven alias hunts).

---

## 10. Decisions taken in this round, and questions for the user

Taken (coordinator): Lane A's auditor-equivalent climb extraction is canonical (parity check at M0); mapping (i) is presented as matching
with a burning-style certificate, not chip-firing; sandpile group / identity / burning items are dropped pending M2; Φ is adopted as the
screening objective; W as in section 5 plus #2679 and retired5 as intermediate words; #2833/#2853 are held-out and fetched as data at M4
only; the constructor null N4 is conditional (built only if a string pattern survives M1, since it costs an engineering day).

For the user:
1. Is a weighted-matching hostee-move search (refit costs as edge weights, S-1 extension) in scope for the κ rounds? It is the one item
   here with a plausible κ consequence and belongs to the κ track, not to this plan.
2. Should the "Parikh ledger" (local delta per call, idle delta, Φ gain, productions, consumed/created preconditions) be proposed to the
   community as the standard description of a PR step? It reproduces every step we hold from data alone. This is an outward action.
3. Approve the two-week schedule and the ~40 core-hour budget, or set a smaller first slice (M0 + the exact items of K+1-2 alone cost
   about 4 core-hours and already yield the ledger, the atlas and the flow map).
4. Margins (CR >= 1.5 / 1.2, enrichment >= 2x at q < 0.01): chosen so that a positive is worth an exact census run; adjust if desired.

---

## 11. Risks and non-claims

- No κ claim; no "new method"; the exact parts are classical (matching, lattice closure, min-cost flow, concavity, Akra-Bazzi). The
  sandpile vocabulary is a reading aid; the L-system vocabulary is exact at levels 2-3 and a recipe at level 1.
- Grammar size and LZ76 are proxies (smallest grammar is NP-hard; the batched Re-Pair is deterministic, not canonical); alphabet choice
  moves every statistic; z-scores at n ~ 17k are meaningless as evidence of a lever; the grounding CRs will shrink under N1b and must not
  be quoted as structure.
- The frame layer is a global certificate: no string-local rule decides it; any positive in L-4 is surprising and must be re-checked with
  `optimal_frames`. Reordering / exchange / promotion searches are protocol-specific nulls already run with exact tools (r3-r10) and are
  not re-run here.
- The log-rank law is first order (~1%): it ranks and screens, it never certifies. Every ceiling is relative to a stated class; the lineage
  advances by leaving classes, so a ceiling is a prediction about a class, never about the problem.
- The fill is at its fixed-inventory optimum (#2733 certificate); fill-level patterns can only redistribute idle remainders. Greedy random
  fills are infeasible and must not be used as controls. The random walk is a local chain started at the optimum, not a uniform sample.
- Data risks: #2766's head lives only in `FETCH_HEAD`; #2833/#2853 are not held and everything said about them is from the comment sweep.
- The literature list (Appendix B) is from memory and not re-verified online in this round; check before circulation.

---

## Appendix A. Grounding numbers from the planning round (#2802 base word unless stated)

| quantity | value | source |
|---|---|---|
| LZ76, `mid` alphabet (17,611 tokens, 116 symbols): real / N1 / N2 | 1,066 / 3,968+-9 / 3,094+-21 | A `extract_strings.py` |
| Re-Pair size, `mid`: real / N1 / N2 | 3,844 / 9,134 / 7,483 | A |
| LZ76, `full` (541 symbols) and `rank` (21): real / N1 / N2 | 1,998 / 5,821 / 4,471; 101 / 1,095 / 620 | A |
| forward-only string (A+cut+B, 5,583 tokens): LZ76 real / one N1 shuffle | 302 / 1,846 (CR 6.1); Re-Pair ~1,080 / ~4,106 | D `string_cost.py` |
| per section LZ76 real / N1: A, B, cleanup, compensation | 414/1,597; 429/995; 503/1,666; 603/1,450 | A |
| B lag-match (base 0.053): lags 4, 24, 12, 20, 8; lags 9, 73, 112 | 0.49, 0.48, 0.43, 0.41, 0.41; 0.23, 0.10, 0.19 | A |
| climb strings: distinct / entropy; across-register null; within-register null | 56 / 5.23 bits; 358.5 / 7.83; 190 / 6.93 | A |
| climb vocabulary shared with #2751, #2462, all three | 53, 49, 49 of 56 | A |
| per-register strings identical: base vs extra; #2751 vs #2802; #2462 vs #2802 | 704/704; 648/704; 591/704 | A |
| root of the moment equation | 0.0017177949841186346638272299... | B, C, D |
| uniform manuscript model (all rank 1) | 0.001143089 | B |
| λ (dκ/dΦ), D = dM/dκ | 1.2422e-10, 189,435.57 | B `parikh_kappa.py` |
| unit moves: merge two rank-4 -> 8 per call; split one idle 48 -> 48x1; refit {1:-2,2:+1}/call; width-8 removal (1,2,2,3) clean / (1^8) / as eight rank-1 | +4.609e-7; -2.318e-8; +1.155e-7; +8.79e-7 / +1.385e-6 / -5.05e-7 | B |
| cold-host (4,8)->7 with the recorded relaxed fill | +8.70325e-7 (= RELAX-host7) | B |
| ceilings: idle <= 48 integral; packing cap; ceil74 class; coalesced climbs; all rank 9 | 0.0017473945; 0.0017580859; 0.0017151404; 0.0028258; 0.0030578 | B, C |
| fill: bins; cells; used; idle | 149,184; 3,580,416; 2,219,112 (62.0%); 1,361,304 | C `ground_fill.py` |
| bins empty-or-full; windows fully empty / fully used | 77.35%; 237 / 770 | C |
| eligible windows per call: min / mean / max; demand per call | 6 / 310 / 444; 3,332 cells | C |
| greedy random fills: stranded roles | 2.8-3.5% of 271,728 | C |
| walk κ after 1k / 3k / 10k / 30k / 100k / 300k moves | 0.0017155 / 0.0017111 / 0.0016973 / 0.0016677 / 0.0016127 / 0.0015666 | C `ground_fill_walk.py` |
| lives / slots / max matching (time only; time + frame) / Koenig deficiency | 122 / 402 / 122; 72 / 50 | C `ground_bipartite.py` |
| merge prices per call: (1,1)->2; (2,2)->4; (1,8)->9; (4,4)->8; (4,5)->9; (1,3,5)->9; (1,1,2,5)->9 | +1.155e-7; +2.31e-7; +2.61e-7; +4.61e-7; +5.14e-7; +7.01e-7; +8.60e-7 | C `ground_ceiling.py` |
| Word / Bounds / Graph / root timings | 0.05 s / 0.22 s / 0.1 s / 0.10 s | D `word_timing.py` |

## Appendix B. Prior art (from memory; verify before circulation)

L-systems and growth: Rozenberg-Salomaa 1980 (The Mathematical Theory of L Systems; growth matrices, Perron-Frobenius); Salomaa-Soittola
1978; Prusinkiewicz-Lindenmayer 1990 (parametric L-systems); Parikh 1966; Cobham 1972 (uniform morphic iff automatic; corrected during execution, see results/PRIOR-ART.md); Akra-Bazzi 1998
(characteristic equation sum a_i b_i^p = 1); Crump-Mode-Jagers / Bellman-Harris branching (Malthusian parameter). Grammar-based
compression: Nevill-Manning-Witten 1997 (Sequitur); Larsson-Moffat 2000 (Re-Pair); Lempel-Ziv 1976 and Kaspar-Schuster 1987 (LZ76);
Kieffer-Yang 2000; Charikar et al. 2005 (smallest grammar NP-hard); Lohrey 2012 (SLP survey). Programs and instruction streams: Larus 1999
(Whole program paths: Sequitur on traces, the closest precedent); Debray-Evans-Muth-De Sutter 2000; Burtscher et al. 2005. L-systems for
synthesis: Kitano 1990; Gruau 1994; Hornby-Pollack 2001-2002; Haddow-Tufte-van Remortel 2001 (unverified). Sandpiles and chip-firing:
Bak-Tang-Wiesenfeld 1987; Dhar 1990, 1999 (abelian property, burning test); Dhar-Ramaswamy 1989 (directed sandpile with sinks);
Bjorner-Lovasz-Shor 1991; Bjorner-Lovasz 1992; Biggs 1999; Cori-Rossin 2000; Baker-Norine 2007; Holroyd et al. 2008 (least action);
Levine-Peres 2009 (divisible sandpile); Fey-Levine-Peres 2010; Klivans 2018; Corry-Perkinson 2018. Abelian networks: Bond-Levine 2016
I-III; Candellero-Ganguly-Hoffman-Levine 2017 (non-abelian oil-and-water); Cairns 2018; Kiss-Tothmeresz 2015, Hujter-Kiss-Tothmeresz 2017
(hardness). Load balancing / scheduling: Bitar-Goles 1992; Goles-Kiwi 1993; Rabani-Sinclair-Wanka 1998; Cooper-Spencer 2006;
Friedrich-Gairing-Sauerwald 2012; Berenbrink et al. 2015-2016; marked graphs of Petri nets (Commoner-Holt-Even-Pnueli 1971). Matching:
Hall 1935; Koenig 1931; Hopcroft-Karp 1973; register allocation as interval colouring (Hashimoto-Stevens 1971; Chaitin 1982). Register
allocation or bin packing phrased as chip-firing: no reference known (unverified absence; claim nothing either way). Multiple comparisons:
Benjamini-Hochberg 1995; Phipson-Smyth 2010.

## Appendix C. Files of the planning round (`research/styles-r11/planning/`)

`BRIEF.md` (the shared brief). Lane A: `REPORT.md`, `extract_strings.py` (loader, auditor-equivalent climbs, alphabets, nulls N1/N2,
motif census, lags), `measures.py` (LZ76, LZ78, Re-Pair, block entropies, lag-match, shuffles, random linear extension),
`lineage_checks.py`, `OUT-measures.txt/.json`, `OUT-lineage.txt`. Lane B: `REPORT.md`, `parikh_kappa.py`, `OUT.txt`. Lane C: `REPORT.md`,
`ground_fill.py`, `ground_fill_walk.py`, `ground_bipartite.py`, `ground_ceiling.py` (+ `.out.json`). Lane D: `REPORT.md`,
`DATA-INVENTORY.md`, `CONTROLS.md`, `SKELETON.md`, `inventory_scan.py`, `fill_scan.py`, `fill_bins.py`, `string_cost.py`,
`word_timing.py` (+ `.out`).

## 11. Execution results — 2026-10-16

This section records the completed finite evaluation; it does not change the binding controls or stop rules in section 6. The authoritative detailed report is [results/RESULTS.md](results/RESULTS.md), with immutable per-attempt receipts, preregistrations, amendments and source attributions. The delivered registry has 23 completed entries, including explicit not-run entries after stops, and 62 preserved RESULT receipts. No finding satisfies all five pattern criteria and no construction improvement is claimed here.

| Milestone | Recorded outcome |
|---|---|
| M0 pipeline/bookkeeping | Smoke PASS; canonical parity for all 21 frozen PINS files; exact acceleration controls and completed null calibration. Literal fill identities pass, with unresolved #1672 provider/held-word binding. L6 accuracy/order audit passes; L7 and S1 retain early lineage obligations; L2 and S6 are protocol-specific NULLs. |
| M1 strings | L1 fixed capped-RePair search is NULL on all 84 enrolled triples. L2 then L1 are consecutive confirmed Lane A NULLs, so the continuation screen and L3/L4/L5/N4 are not run. No compression-screen NULL is inferred from the stop. |
| M2 exactness | Literal conservation and eligibility DAG pass. No intrinsic Laplacian was established. S2 strict greedy lowering misses the reference in all 600 orders, reaching one worse terminal per word. S6 then S2 stop Lane C; S4/S5 and its S3 continuation remain unrun. |
| M3 growth | L8 rational class certificates pass after two preserved corrections; #2802 upper 0.001717795812 is tighter than the certified packing comparator. L9 broad constructive census remains exploratory. L10 composition conjunction is NULL; L11 identical local profiles and the optional conditional local-cost calibration pass. Proper named local guard-order replay passes; the two early compound derivations remain unresolved. |
| M4 held-out | Three bookkeeping predictions frozen before either fetch pass both seeds. Fixed-lambda errors are 0.293338% for #2802→#2833 and 0.053990% for #2833→#2853. Both held-out packages retain one dispatched profile and change local profile/width inventory. M4 is EXPLORATORY as preregistered because no eligible non-circular pattern entered it. |
| M5/M6 | Four language artifacts per original pinned word, detailed results, prediction outcomes, pipeline code, completed registry, source/compute inventory and hand-back prepared for coordinator review. |

The held-out heads match the planning pins exactly: #2833 `e9307b48d7d1b690939935ecef0f8e524e6d92f4` (Jeremy Kothe / jeremykothe2) and #2853 `d01045dfb67428679618027dff552f1d032fa999` (Philippe Van Velzen / philippeVV). Their content was read as inert data under isolated Python. Current fill order/dispatch, provider words and geometry were bound explicitly; fetched admission/native/outer proof code was never executed. A first M4 adapter error concerning two rank-zero terminal children is preserved, followed by a frozen exact schema correction and the successful second attempt.

Execution corrects several planning interpretations. The integral rank-48 ceiling uses one residual-rank child; the many-rank-1 remainder recipe is not a universal bound. Ascending helper width excludes fixed centre-descents; the L8 envelope and L10 composition control preserve those actual payments separately. The named local guard-order failures are inadmissible prefixes, not differing values for the same algebraic Parikh sum. S2 provides a greedy-optimality failure without sampled order dependence. Stage/profile bookkeeping does not by itself establish persistent recursive child types. The bibliography's general morphic-to-automatic parenthetical has been narrowed to uniform morphic sequences; [citation verification](results/PRIOR-ART.md) remains explicitly partial.

The conditional local full-moment score has maximum relative error 0.024346% on 152 primary records, with cached dot medians 1.694/1.793 μs versus 37.385/37.327 ms for the registered uncached conditional-root evaluation. Coefficient and derivative setup costs are separate. Raw Φ fails the sign check for nonzero local mass. These observations motivate a complete-profile screening census, not global candidate pricing or an end-to-end performance claim.

Measured experiment CPU is 8.429936397 core-hours; the L8 certificate review adds 7.273402129 seconds. Unmetered orchestration/review and missing aborted-worker CPU are excluded explicitly. Early failed runs and budget overshoot remain visible. All proposed levers and remaining proof/data obligations are in [results/HANDBACK.md](results/HANDBACK.md); outward posting waits for the coordinator.
