# Lane B - L-system growth functions, Parikh vectors and the kappa equation

Planning report (no kappa claim). Script: `parikh_kappa.py` (this directory, 0.3 s, standard library), output `OUT.txt`.
All numbers below are from that run on the #2802 package inputs (`$S/wt-claim7/research/t74-joint-twelve-retired7/`).

## 1. Mapping

### 1.1 What recurses and why the exponent equation has its form (exact)

Manuscript (`upstream/build/sections/05-layers.tex:632-683`, "Unrolling the recurrence"): one invocation of the finite
network at parameter `e = mf` on a stream of volume `V` makes `s` child calls at parameter `f = e/m`, each on volume
`V/W` (`W` wires, `m` = dimension of the binary label space, `s` = sum of the residual dimensions of the edges,
`s < Wm`). With `F(e)` = time / volume, `F(e) <= (s/W) F(e/m) + O(e^lambda)`, so `F(e) = O(e^sigma)` with
`sigma = log_m(s/W)`, i.e. `kappa = 1 - log_m(s/W)`. Every residual dimension is one child at the same, uniformly
shrunk parameter.

Community model (`vendor/ceiling.py` docstring; `exact_moment.py`; `independent_owners.py`): a paid child of rank
`r` (an edge whose nested frame subspace grows by `r` dimensions, `00-introduction.tex` "their dimension changes
count the smaller operations needed on an edge") is one smaller call at parameter `e * r/m`, not `r` calls at `e/m`.
The recursion becomes

    F(e) = sum_r (c_r / W) F(e * r / 73) + lower order,      F(e) ~ e^(1-kappa)

and the exponent equation is `sum_r c_r (r/73)^(1-kappa) = W = 66304` (`DIMENSION = 73`), exactly the brief's form.
Rank mass `sum_r r c_r = 4,816,512 = (m-1) W + 64 * 666` is the coverage identity (every live family keeps one
unpaid coordinate, every call pays its 8 centre paths of rank 8); it is fixed by the template, not by the word, so
every word/fill move is a mass-neutral Parikh delta. Since `(r/73)^(1-kappa)` is strictly subadditive in `r`
(0 < kappa < 1), merging two children of ranks `r1, r2` into one of rank `r1+r2` lowers the paid moment and raises the
root; the uniform manuscript model (every unit of mass a rank-1 child) gives `kappa = log_73(73 W / mass) =
0.001143089` (row G of the ladder) and all of the community's 0.0017178 above that is rank concentration.

### 1.2 The L-system / growth-function reading (exact, and where it ends)

| L-system notion | here | exact? |
|---|---|---|
| alphabet | ranks `{1..9, 16, 32, 48, 51}`; one call type (single nonterminal `A(e)`) | exact |
| production | `A(e) -> prod_r A(e r/73)^{c_r}`, each child weighted `1/W` (volume) | exact (05-layers recursion) |
| Parikh vector of the right-hand side | the complete profile `c_r` (`PROFILE.json`; `independent_owners.py` builds it as `sum over 666 calls of providers[..].actual_paid_profile + Counter(cap - used)` per window) | exact |
| what is rewritten | one network invocation (parameter, volume) | exact |
| what grows | normalised cost `F(e) = time/volume` = volume-weighted number of leaf kernels; `F ~ e^(1-kappa)` | exact |
| growth rate | the root of `sum_r (c_r/W) (r/73)^(1-kappa) = 1` | exact |
| D0L growth matrix / Perron root | degenerate case: all children at the same parameter -> 1x1 matrix, `rho = s/W`, `kappa = 1 - log_m rho` (manuscript) | exact |
| multi-type branching (Crump-Mode-Jagers) | reproduction measure `mu = sum_r (c_r/W) delta_{ln(73/r)}` ("time" = log-parameter shrink); `1 - kappa` is the Malthusian parameter, the root of its Laplace transform `= 1` | exact (same equation) |
| Akra-Bazzi | `sum_i a_i b_i^p = 1` with `a_r = c_r/W`, `b_r = r/73`, `p = 1 - kappa` | exact (same equation) |
| timed D0L (real delays) | one symbol, delay `ln(73/r)/ln 73` generations per rank-`r` child; growth rate `73^(1-kappa)` per generation | exact |
| output language | none beyond the one equation: with one symbol the "word" at depth `j` is a multiset of parameters | the view is exhausted here |

So the global structure is an L-system growth problem in the precise sense that kappa is a Malthusian growth rate of a
one-symbol timed production whose right-hand side Parikh vector is `c`. The statement is exact but thin: everything
the lineage does happens in the right-hand side `c` (the Parikh vector) and in the context-sensitive preconditions that
decide which deltas are feasible. That is where the analysis must live (sections 1.4-1.6).

### 1.3 Where the local profile comes from (climb strings; exact up to one convention)

The local profile is the Parikh vector of per-register climb strings. `parikh_kappa.climb_strings` reads a word's
forward sections `A, cut, B`, takes each register's timeline of gate-frame dimensions (`len(frame)`, skipping unpaid
dim-0 incidences), starts at `dim(start_extra)` (0 if absent), ends helper registers (224..703, not `removed`) at
`dim(helper_final)` or 9, and counts positive differences; each centre adds one rank-8 child (`center_frames`).
Checks on the real words: the width inventory `{4:26, 5:2, 7:62, 8:78, 9:240}` (and #2751's `{4:26, 5:9, ...}`) is
reproduced exactly (width = sum of a helper's climb string); the reported mass decomposes as helpers 3332 + centres 64
+ ports 1792 (= 112 x 16) = 5188 per call; the #2751 -> #2802 diff is reproduced exactly: `{1:+16, 2:+2, 3:-29, 4:+8}`
per call, mass -35 = 7 aliased width-5 followers. A fixed offset `{1:8, 2:36, 4:-10}` (mass 40) remains between my
histogram and the reported profile; it is identical in both words, sits on untouched registers (the centres' gate
climbs `(1,1,1,1,4)` and the twelve `target_levels` registers are the suspects), and cancels in every lineage diff.
Pinning it against `deps/toolkit-rev3/frames.py` (`Graph`, `optimal_frames`) is experiment B2.

### 1.4 The move alphabet as productions on climb strings (Parikh deltas, preconditions, known values)

State = (multiset of climb strings per register, owner fill). Local Parikh delta per call is multiplied by 666; the fill
converts freed cells into idle remainder children (one child per window = `capacity - used`, capacities 8/16/32/48).

| production | string / fill effect | Parikh delta (per call unless noted) | precondition (context) | known value |
|---|---|---|---|---|
| refit (frame lowering at fixed gate order) | re-partition one register's climb at fixed endpoints | mass 0; e.g. #2766 B1151 6->5: `{1:-2, 2:+1}` = `(1,1)->2` merge; refit7c 504/505: `(1,2,3,1,1,1)->(1,2,2,2,1,1)` | exact propagated floor allows it; certified optimal frames (`frames.py`) say none remain at fixed order (scoped negative) | #2766 step +1.154e-7 exact = `{1:-1332, 2:+666}` global |
| retired-lender alias (follower `f` enters retired lender `l` through one B warp, invertible `G`) | delete `f`'s string (width `w`); extend `l`'s string by `f`'s remaining climb; fill loses one width-`w` role | local mass `-w`, idle `+w`; e.g. 606<-550: `(2,1,1,1)` deleted, 550 `(2,3,3)->(2,2,1,1,1,1)`; net `{1:+1, 3:-2}` local, idle `+1 x rank 5` | `dim(U_l) = entrance dim of f`, `l` retires before `f` enters, `G(U)=E`; floor >= 4 for every lender here (so the 48 rank-1 followers are infeasible) | retired5: five aliases +1.523e-7 total; the fill-only upper bound of one width-5 alias with a clean rank-5 remainder is +5.5e-7, the lender's string splitting eats most of it |
| hostee move (warp record replaced in place) | transplant a hosted climb from lender `a` to free retired lender `b` (with a refit of `b`'s last gate) | mass 0 by itself; frees `a` for an alias | `b` free, floor <= entrance dim, retires before the hostee enters; 192 augmenting paths, only 564/565 qualified | enables +3.857e-7 (#2802 step, with 2 aliases) |
| width cut (end frame 9->8 ...) | shorten a helper's string by its last piece; cell freed | local `{1:-1}`, idle `+1` (or merged) | restorable end frame; H-widths lane: all exact cuts negative on these words | relaxation +5.9e-7/step, exact edits negative |
| helper deletion (donor kernel, twelve-source recovery) | delete a width-`w` string; `w` cells freed | local `-string`, idle `+w` | kernel-level identity (symbolic replay) | width 8: +1.1..1.9e-6 (fill-relaxed); my clean-remainder bound +8.8e-7 for climb `(1,2,2,3)`, +1.39e-6 for `(1^8)` |
| cold-host merge (4,8)->7 | two strings become one of width 7 | local `{3:-1, 2:-1}` ("-H3-H2"), 5 cells freed | exact undo of follower writes (open lead J) | +2.8e-7 with clean rank-5 remainders; **+8.703e-7 with the recorded relaxed fill - reproduced exactly from the Parikh vectors** (`RELAX-host7.json`) |
| pre-life hosting | a helper lives inside a host before the host's own life | one role fewer per call | PR2679 rule, 6 found | +6.7e-7 each |
| owner-fill evacuation / re-tiling | no local change; idle histogram re-optimised | idle delta only (pattern lattice) | window time-eligibility, capacities | fill lever "closed" within 5.8e-17 at #2733 (dual certificate) |
| dirt-entry rewrite (#2833/#2853), T124/T248 composition | A-phase kernel change: new strings | unknown to us (fetch as data) | kernel identity | +8.6e-7, +7.2e-7 steps |

Deltas commute as vectors (kappa depends on `c` only); preconditions do not (a refit enables an alias; an alias consumes
a lender). The lineage is therefore a derivation in a guarded vector addition system, not in a context-free grammar.

### 1.5 The kappa landscape on the Parikh cone (exact statements)

1. `M(kappa; c) = sum_r c_r (r/73)^(1-kappa)` is linear in `c` and increasing in `kappa`. Hence
   `{c : kappa(c) >= k} = {c : M(k; c) <= W}` is a half-space. kappa is quasi-concave and quasi-convex on the mass
   hyperplane: its level sets are hyperplanes, it has no interior local optima, and its maximum over any polytope of
   reachable profiles is attained at a vertex and is a parametric LP (this is exactly what `packing_cap.py` and
   PR2679's `ceil74.py` compute, with dual certificates).
2. Price table at the #2802 root (`dM/dkappa = 189,435.57`): one added rank-`r` child costs
   `-(r/73)^(1-kappa)/(dM/dkappa)`, i.e. -7.285e-8 (r=1) ... -5.279e-6 (r=73); per unit of mass it is nearly flat,
   -7.285e-8 (r=1) to -7.231e-8 (r=73). All gains are the small differences of this per-mass price.
3. First-order law (mass-neutral delta `d`): `dkappa = -(1/(73 D)) sum_r r d_r (73/r)^kappa ~ lambda * dPhi`,
   `Phi(c) = sum_r r c_r ln r`, `lambda = kappa/(73 D) = 1.2422e-10`. Maximising kappa is, to first order,
   maximising the mass-weighted mean log-rank. Verified: unit merges `(1,1)->2` exact +1.7337e-10 vs law +1.7220e-10;
   `(4,4)->8` +6.9185e-10 vs +6.8882e-10; `(48,3)->51` +1.4208e-9 vs +1.4173e-9; every lineage step within 1.1%
   (table in section 1.6). The linear price form agrees with the exact root to six digits on all moves, so the
   landscape is effectively linear at the scale of any PR.
4. Ceiling ladder (each row relaxes the reachable set; same bisection; "what would falsify" = a PR exceeding it
   while staying inside the stated class):

| relaxation | kappa | falsified by |
|---|---|---|
| A. actual #2802 | 0.00171779498411863466 | - |
| B. fixed local word, all idle mass in rank-48 children (bin capacity bound, integral) | 0.0017473945 | any fill of #2802's words above it -> bins > 48 or a different local word |
| C. fixed local word, idle in fractional rank-51 children (halving guard; = `packing_cap.py` 0.00175808593463) | 0.0017580859 | any hosting/packing of this word above it -> coverage identity or R<=51 guard broken |
| PR2679 `ceil74` class-level (every fill of the 415-helper inventory, pattern-lattice LP + integrality) | 0.0017151404 | a fill of THAT inventory above it; the lineage passed it (#2751 0.0017171) by leaving the class (twelve-source recovery changed the local word), not by a better fill |
| D. helper mass + idle at rank 51, ports at 9, centres 8 | 0.0060803 | a word/fill above it -> frame rank > 9 or idle > 51 |
| E. all local children at rank 9 (h = 9) + idle at 51 | 0.0030578 | same |
| F. all mass at rank 73 | no root (`M = 65979.6 < W` for all kappa) | - |
| G. uniform manuscript model (all rank 1) | 0.0011431 | - |

The headroom is dominated by local climb fragmentation (A -> E: +1.34e-3), not by idle fragmentation (A -> B:
+2.96e-5; small idle remainders carry only 86,520 of the 1,361,304 idle units). Since certified frames are optimal at
fixed gate order, that headroom sits behind gate order and kernel structure, i.e. behind the context-sensitive
productions (dirt-entry, compositions), which is where the newest PRs gained (+8.6e-7, +7.2e-7).

### 1.6 Analysing the PR lineage as a derivation

Represent each PR as `(local delta per call, idle delta, Phi gain, productions used, preconditions consumed/created)`.
Tested on the four words we hold:

| step | global Parikh delta | exact dkappa | log-rank law | Phi/call | registers changed |
|---|---|---|---|---|---|
| #2751 -> #2766 (refit) | `{1:-1332, 2:+666}` | +1.15387e-7 | +1.14688e-7 | +1.386 | 1 frame |
| #2766 -> retired5 (5 aliases + refits) | `{1:+14652, 2:-3330, 3:-15318, 4:+5328, 5:+3330}` | +1.52343e-7 | +1.54013e-7 | +1.862 | 49 |
| retired5 -> #2802 (2 moves + 2 aliases + refits) | `{1:-2664, 2:+3996, 3:-3996, 5:+1332}` | +3.85668e-7 | +3.83628e-7 | +4.637 | 10 |

Proposed analysis: (i) commutation - deltas on disjoint register sets commute exactly; test precondition commutation
by applying production pairs in both orders through the pinned auditor; (ii) saturation - a production class is
saturated when its census is empty (alias: no lender with floor <= entrance dim; here 670/671 lack a lender by the
74-lives/72-registers pigeonhole), and the lineage is a sequence of class exits (each class-level ceiling was passed
by a production outside the class); (iii) gain per application - `Phi` per call per production, which the lineage
shows is not diminishing (1.4, 1.9, 4.6, then +8.6e-7 and +7.2e-7 steps from new classes).

## 2. What is already known

Local: `class_lsys.md` (D0L cannot generate Z-primes; lesson: an L-system description helps only when the predicate is
decidable from the rule, not from running it) - here the predicate kappa is decidable from the Parikh vector alone, so
Lane B is the favourable case of that lesson, but a one-symbol one; `lsys4_1_formalism.md` (M-DT0L with guards) is the
right vocabulary for the guarded productions of 1.4. The memory digest states the same root equation
(`sum n_r r (73/r)^b = 73 W`) and the hosting model (one idle child per window); `_imb_host_milp.py` / PR2679's
`ceil74.py` are Parikh LPs over bin patterns with a lattice integrality correction; the r10 reports give the scoped
negatives used in 1.4 (frames optimal at fixed order, promotions lose under real hosting, no floor <= 1 lender,
width cuts negative, restorable helpers never below full width). Literature: Akra-Bazzi (1998) and Leighton's notes
(characteristic equation `sum a_i b_i^p = 1`); Crump-Mode-Jagers / Bellman-Harris branching (Malthusian parameter as
the root of the Laplace transform of the reproduction measure); Rozenberg-Salomaa, *The Mathematical Theory of L
Systems* (growth matrices, Perron-Frobenius, growth functions); Parikh's theorem (semilinear images of context-free
languages) with the caveat that guarded productions are not context-free, so the reachable Parikh set need not be
semilinear - ceilings must come from LP relaxations with dual certificates, as `ceil74`/`packing_cap` already do;
vector addition systems with guards (reachability decidable but expensive; the practical tool is bounded ILP).
Why the mapping could fail to be useful: the growth-function view is one equation and is exhausted in 1.2; the Parikh
vector says nothing about feasibility; ceilings are class-relative and the lineage advances by leaving classes.

## 3. Candidate experiments

| id | question | data | method | null model / control | pass bar | cost | if positive |
|---|---|---|---|---|---|---|---|
| B1 | Does the log-rank law `dkappa = lambda dPhi` predict every lineage step? | complete profiles of #1094, #1672, #2474.., #2751, #2766, #2802, #2833, #2853 (CLAIM.json, fetched as data) | exact roots vs `lambda dPhi` per step | random mass-neutral deltas of the same L1 size (law must hold there too; the test is that the REAL deltas are the ones with large positive Phi) | every step within 2 %; pairwise kappa order of all words reproduced by Phi | 1 core x 5 min | use `Phi` (integer-linear) as the objective inside searches; exact root only for certification |
| B2 | Pin the climb-string convention | WORD files of every held word; `frames.py` Graph | reproduce reported local profiles with offset 0 | shuffled-section control must NOT reproduce them | offset 0 on >= 3 words | 1 core x 10 min | climb strings become the shared state for Lanes A and C |
| B3 | Decompose each lineage step into productions of 1.4 | consecutive word pairs | per-register climb diff -> production labels; sum of labelled deltas = recorded delta; auditor runs of swapped orders | random register re-labelling (should not decompose) | every step decomposes exactly; non-commuting pairs identified | 2 cores x 15 min | a derivation DAG with gain per application; predicts which productions remain |
| B4 | Tighter falsifiable ceilings per class | #2802 words + PLAN windows | parametric LP with dual certificate: (a) fixed inventory pattern LP (ceil74 on 408 helpers), (b) row B (idle <= 48 integral), (c) helper-removal envelope (kappa_max vs number of helpers aliased) | relaxations must dominate every held fill (sanity) | each ceiling exceeds the realised value by a stated margin and names what a violating PR must have changed | 2 cores x 10 min | ceiling ladder published with each claim; PR triage |
| B5 | Saturation census as a guarded VAS | current word | enumerate feasible productions per class (alias paths, refits, hostee moves, cuts) and their `Phi` | random lender/follower pairings (expected 0 feasible) | a predicted empty class (e.g. "no alias with floor <= 5 remains") that a later PR could violate | 1 core x 10 min | frontier map: which class must be exited next |
| B6 | Is the real word's `Phi` extremal in its class? | climb strings of #2802 | compare `Phi` with random re-partitions of each helper's width (same inventory) | random compositions of the same widths | z > 3 and `Phi` at the class maximum (consistent with "frames optimal at fixed order") | 1 core x 2 min | quantifies how much of E - A is partition vs order |
| B7 | Any multi-type structure? | GLOBAL-TEMPLATE (333 calls x 2 orientations, forward/backward programs) | child profile per orientation / per stage | - | prediction: all types identical (1x1 growth matrix); falsified if a stage has a different profile | 1 core x 2 min | if falsified, the exponent equation becomes a Perron root of a matrix |

## 4. Grounding measurement (done; `OUT.txt`)

Root reproduced: `0.0017177949841186346638272299...` (certified endpoint `0.001717794984118634663827`), `M(0) = mass/73
= 65979.616 < 66304`. Unit moves on the real profile (exact roots): merge two rank-4 into one rank-8 once per call
+4.609e-7; split one idle 48 into 48 x 1: -2.318e-8 (into 6 x 8: -1.071e-8; into 32+16: -3.80e-9); merge all 6594 idle
rank-3 with rank-48 into 51: +9.42e-6; refit kind `{1:-2, 2:+1}` per call +1.155e-7 (the #2766 step is exactly this);
remove one width-8 helper with climb `(1,2,2,3)` into a clean rank-8 remainder +8.79e-7 (climb `(1^8)`: +1.385e-6;
into eight rank-1 remainders: -5.05e-7, so packing decides the sign); remove one width-5 follower `(2,1,1,1)` into a
rank-5 remainder +5.54e-7 (upper bound; the realised alias steps are 3e-8..2e-7 because the lender's string splits);
cold-host "-H3-H2" with the recorded relaxed idle histogram +8.70325e-7 = the stored `RELAX-host7` value exactly.
Lineage steps and the log-rank law: section 1.6. Fixed-offset diagnostic: section 1.3.

## 5. Risks and non-claims

No kappa is claimed; nothing here changes any PR. The growth-function mapping is exact but one-symbol, so "output
language patterns" do not exist at this level; the content is in the Parikh deltas and their guards. The log-rank law
is first order in kappa (errors ~1 %): it ranks and screens, it does not certify - certification stays with the exact
rational bracket (`exact_moment.py`). Every ceiling is relative to a stated class (coverage identity, bin capacities,
halving guard, fixed inventory or fixed local word); the lineage shows ceilings being passed by leaving the class, so a
ceiling is a prediction about a class, never about the problem. The brief's value scale includes fill re-optimisation
(an ILP), which is not a Parikh delta that can be written down a priori; my clean-remainder numbers are bounds of the
local part only. The climb-string convention carries a fixed offset of mass 40 (1.3) until B2 pins it. The constants
are galactic; this is theory and verification tooling, and research does not close: the nulls cited are
protocol-specific (fixed gate order, these words, this auditor model).

## 6. Open questions for the coordinator

1. Should `Phi = sum_r r c_r ln r` (integer-linear, 1 % accurate) replace root evaluations inside all search loops
   (hosting MILP objectives, alias/refit censuses), keeping the exact root for certification only?
2. Which lineage words/fills can Lane D fetch as data for B1/B3 (we hold #2751, #2766 profile, retired5, #2802; need
   #1094, #1672, #2474-#2745, #2833, #2853)?
3. Are window capacities <= 48 fixed by the template for every admissible fill? If so, row B (0.0017474) is the
   binding cap for every fill of #2802's local word and should be stated with the claim instead of 0.001758.
4. The convention behind the fixed offset `{1:8, 2:36, 4:-10}` (centres' gate climbs vs centre paths, target levels):
   is it documented in the toolkit's `Graph`, or in PR1012's coverage note?
5. Do we want a community-facing "Parikh ledger" (local delta per call, idle delta, `Phi` gain, productions,
   consumed/created preconditions) as the standard description of a PR step, since it reproduces every step we hold
   from data alone?
