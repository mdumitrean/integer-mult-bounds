# Lane C REPORT: sandpile / chip-firing analysis of the integer-mult-bounds work (#2802 package)

Planning round r11, 2026-10-15. No kappa claim. Read-only everywhere except this directory. Scripts and their outputs
are in this directory: `ground_fill.py` (+`ground_fill.out.json`), `ground_fill_walk.py` (+`.out.json`),
`ground_bipartite.py` (+`.out.json`), `ground_ceiling.py` (+`.out.json`). Total compute used: about 1 core x 2 minutes.

## 0. Verdict in one paragraph

Of the four candidate mappings, none is an abelian sandpile in the strict sense (threshold toppling with the
least-action/abelian property). What IS exact in each case is a classical combinatorial structure that the sandpile
vocabulary points at: (3) aliasing is bipartite matching with Hall/Koenig certificates found by a burning-style
alternating search (the 74-vs-72 pigeonhole is reproduced exactly below); (2) frame climbs are a monotone lattice
labelling with per-chain conservation and a confluent least/greatest-fixpoint closure, plus a concave cost, which gives
an exact (loose) coalescence ceiling and an exact merge price list; (1) the owner fill is a capacity/threshold system
whose conservation and stability conditions are exact but which has no toppling dynamics and no abelian property
(indivisible chips of five sizes); its optimum is maximally clumped, the opposite of a recurrent sandpile state;
(4) the butterfly recursion is a weighted tree with a sink (conservation with deficit exact), nothing more. Ranking by
exactness: **(3) > (2) > (1) > (4)**. The useful deliverables are certificates and screens (E1, E6), one falsifiable
structural test (E2), and null-model discipline for the fill (E4, E5), not a new mechanism.

## 1. Mapping (objects, rules, invariants; exact vs heuristic)

Hosting rules read from `independent_owners.py` (and `PROOF.md`, `README.md`) of
`$S/wt-claim7/research/t74-joint-twelve-retired7/`: windows = (owner replica 0..73, child 0..17) with capacity = the
rank of the child's idle child (8/16/32/48: children 1,3,5,7,9,11 -> 8; 0,2,16,17 -> 16; 4,6,14,15 -> 32; 8,10,12,13 -> 48),
each with 112 ports = bins; a window is eligible at call t iff start < t <= stop, where start is the previous call or
bridge of the child's pair on that replica and stop is the call whose idle sweep lists the child
(`GLOBAL-TEMPLATE.execution_schedule`, `ORDER.json`); a role = (call t, helper h) of width `PROVIDERS.widths[h]`
occupies width cells of one bin; at most one role per helper per call, one role per family
(replica, 2*pair(child)+side(child), port) per call (`PLAN.pairs/sides`), prefix-compact bins, and leftover cells of a
bin = one idle child of that rank. A paid child of rank r (`vendor/generate_words.py: paid_profile`) is a
frame-dimension jump of r along one register chain (gates A, warps, B, restore, final climb to the end frame), plus the
eight rank-8 private cut copies. Rank mass = 73*2*live - 2*deficit = 4,816,512 = bin cells used + idle + 666 x (local
climb not hosted in bins).

### 1.1 (rank 1) Lender/follower aliasing = bipartite matching; burning = Koenig's alternating search. EXACT (classical)

- Objects: lives L = helpers entering in B with a non-empty start frame (`start_extra`), split into followers (private
  register still present) and hosted lives (one per `warps` record); slots S = retired register segments: free retired
  registers and the own-life segments of the 72 current lenders (`warps[i][1]`, `removed`, `helper_final`).
- Edge (l, s) iff last(s) < first(l) and floor lo(s) <= ceiling hi(l) (the alias rule of #2679/#2802: warp with
  invertible G maps the refit lender frame U onto the entrance frame E, dim U = dim E). Floors/ceilings come from the
  exact L/U propagation (toolkit `frames.py`; r10 census `J-dim1/out/CENSUS-b.json`).
- Exact invariants: one slot per life (a hosted life runs to the end of the word, so a register hosts at most once);
  max matching = max number of aliases; Hall deficiency max_S |S| - |N(S)| = number of unhostable lives (Koenig);
  augmenting paths = hostee moves (the #2802 gain is literally two augmenting paths of length 3:
  667 -> slot 401 (occupied by hostee 603) -> 603 moves to free slot 564; same for 669/403/605/565).
- Chip-firing content: Dhar's burning and Koenig's alternating search have the same shape (monotone spreading from a
  seed until a fixpoint; the unburnt/unreached set is the certificate), but the local inequalities differ
  (c(v) < burning neighbours vs matched/unmatched alternation). No chips, thresholds, sandpile group or identity
  element are defined. "Non-stabilisability certificate" = Hall violator; that is the whole exact content.
- Where it could fail: refits change lo(s) (a lender's floor is lowered by an exact refit of its last gate, 564/565
  6 -> 5), so edges are not fixed: the right model is a matching with edge activation costs (refit = rank moved along the
  lender's chain, priced by the moment). That is weighted matching, still not chip-firing.

### 1.2 (rank 2) Frame climbs = monotone heights with per-chain conservation and a confluent closure. EXACT structure, heuristic dynamics

- Objects: register chains (the toolkit's event graph: one vertex per gate, immutable start/cut/end vertices, edges
  between consecutive occurrences of a register, nested subspaces of F_2^9 along every edge). Height of register r at
  time t = dim of its current frame, non-decreasing from dim(start) to dim(end); a child of rank k = a jump of k.
- Exact invariants: per-chain conservation (sum of jumps = width = dim end - dim start, fixed by `start_extra`,
  `helper_final`, ports perp(port) dim 8, targets dim 9); L/U propagation (joins forward, meets backward) is a monotone
  closure on the subspace lattice, so its least and greatest fixpoints are order-independent (the only place in this
  lane where an "abelian property" holds exactly; it is Knaster-Tarski/Newman confluence, the same mechanism that makes
  Dhar burning and sandpile stabilisation order-independent); the moment is concave in the jump size, so merging jumps
  on one chain always lowers the paid moment: coalescence ceiling and merge price list (section 4.4).
- Not exact: heights never decrease, so there is no toppling; a refit lowers one gate's frame inside [L, U] and moves
  rank along the (at most two) chains through that gate, which is a "chip transfer between neighbours" only as an
  analogy; the optimum is a chain-dual LP certified by the toolkit, not a stabilisation; whether greedy local lowering
  moves are confluent (reach the certified optimum in every order) is untested -> E2.

### 1.3 (rank 3) Owner fill = capacity/threshold system without dynamics. Conservation/thresholds exact, no abelian property

- Objects: 149,184 bins (1,332 windows x 112 ports) with thresholds 8/16/32/48; chips = 271,728 roles of sizes
  {4:26, 5:2, 7:62, 8:78, 9:240} per call; directed time structure = eligibility intervals (start, stop];
  stable configuration = every bin used <= cap, families distinct per call; idle remainders = cap - used.
- Exact: conservation (cells 3,580,416 = used 2,219,112 + idle 1,361,304; with the unhosted local climb this is the rank
  mass 4,816,512); stability = feasibility; the relaxation optimum is a min-cost flow/transportation problem with a
  concave objective (`PLAN.solver_status = "exact integer flow and matching"`).
- Not exact: there is no toppling rule in the object (nothing ever exceeds capacity; the fill is static); any invented
  overflow rule moves indivisible chips of five sizes under family/time constraints, so the final state depends on the
  order (no least-action principle; Bond-Levine abelian networks need processors whose output depends only on input
  counts); the concave objective wants bins either empty or full (grounded: 77% of bins are empty-or-full, 26,558 of the
  33,152 48-bins are empty and the other 6,594 hold five 9s) which is the opposite of a recurrent sandpile state (chips
  spread below threshold). The one sandpile that is an optimisation, the divisible sandpile (odometer = least
  superharmonic majorant, Levine-Peres 2009), is convex/spreading, the wrong sign for our concave/clumping objective.

### 1.4 (rank 4) Butterfly recursion = weighted tree with a sink. Conservation exact, nothing else

The moment equation sum_r c_r (r/73)^(1-kappa) = 66304 = 2 x 37 x 896 says: a parent of 66304 live units of
dimension 73 fires once into children of dimensions r, losing 2 x deficit = 23,680 rank units to a sink
(73 x 66304 - 4,816,512 = 23,680). Every node fires exactly once; there is no threshold, no order dependence and no
stabilisation question, so the sandpile language adds nothing beyond the conservation identity. This is the same
situation as our mod-p counter sieve (`SANDPILE_SIEVE_TRIANGLES.md`): an exact restatement with no lever. Compare
Dhar-Ramaswamy's directed sandpile only as vocabulary. Lane B owns the growth-function reading.

## 2. What is already known

Local corpus (headers read; nothing re-run):
- `SANDPILE_SIEVE_TRIANGLES.md` section 1: the bank of mod-p counters is a true abelian sandpile (two-vertex
  multigraphs with critical group Z/p), equal to trial division; "never call it a new method"; lesson: a sandpile
  restatement is exact when the graph is fixed and the dynamics is counting, and it yields no lever.
- `SANDPILE_RESEARCH_PROGRAM.md`, `SANDPILE_COMPOSITION_THEORY.md`, `DUMITREAN_SANDPILE_FACTORING.tex`,
  `SANDPILE_FACTORING_PRIOR_ART.md`: circulant critical-group orders via cyclic resultants = Williams p+1 / Lucas
  witnesses; the composition theory shows ordinary products do not multiply L-exponents; prior-art audit through
  2026-08-29 found the graph side classical (Biggs 1999, Lorenzini 1991, Hou-Woo-Chen 2006, Mednykh 2019,
  Pengo-Vallieres 2025). Reusable code: `circ_laplacian` (`_exp_sandpile_beyond.py`), signed `laplacian()`
  (`_exp_sandpile_composition_t1.py`), the mod-p `topple/land` of `sandpile_prime_waterfall.html`. There is NO general
  abelian-sandpile stabiliser, Dhar burning or Smith-normal-form group code in the 102 drivers; if E2/E5 need one it is
  a 40-line function (or SageMath's `Sandpile`, not installed).
- Scoped negatives on #2802's words (`$S/wt-r10pub/.../J-dim1/REPORT.md`, `context/F-lenders-REPORT.md`): no lender
  with floor <= 1 (every non-target register reaches dim >= 4 before retiring), followers' first event pinned at dim 1,
  670/671 unhostable by pigeonhole; frames at fixed order optimal; promotions/width changes lose under real hosting.

Literature (standard references; nothing here is new):
- Abelian sandpile / chip-firing: Bak-Tang-Wiesenfeld 1987; Dhar 1990 (abelian property, burning test);
  Bjoerner-Lovasz-Shor 1991 (chip-firing termination and order-independence), Bjoerner-Lovasz 1992 (directed graphs),
  Tardos 1988; Biggs 1999 and Cori-Rossin 2000 (critical group); Baker-Norine 2007 (divisors, reduced divisors =
  Dhar); Holroyd-Levine-Meszaros-Peres-Propp-Wilson 2008 (chip-firing and rotor-routing on directed graphs, least
  action); Levine-Peres 2009 (divisible sandpile, odometer = obstacle problem); Fey-Levine-Peres 2010; Klivans 2018
  (book); Dhar-Ramaswamy 1989 (directed sandpile with sinks, exactly solved).
- Abelian networks: Bond-Levine 2016 I (foundations: processors with input-count-only semantics, least action),
  II (halting), III (critical group); non-abelian counterexamples (oil-and-water: Bond-Levine; Candellero-Ganguly-
  Hoffman-Levine 2017). Our fill with five chip sizes under family constraints is outside the abelian class.
- Chip-firing and load balancing/scheduling: Rabani-Sinclair-Wanka 1998 (local divergence: discrete chip-based
  balancing stays O(log) from the idealised flow), Cooper-Spencer 2006 (rotor-router discrepancy O(1)); directed
  chip-firing = marked graphs of Petri nets (Commoner-Holt-Even-Pnueli 1971), the natural formal home for time-windowed
  capacity systems (reachability, not stabilisation).
- Bipartite graphs: Lorenzini 1991 / Jacobson-Niedermaier-Reiner 2003 (critical group of K_{m,n}); none of it concerns
  matching. Matching theory: Hall 1935, Koenig 1931, Hopcroft-Karp 1973; register allocation as interval colouring
  (Hashimoto-Stevens 1971, Chaitin 1982) is the correct classical frame for mapping (3).
- Why mappings can fail: (1) no dynamics, non-unit chips; (2) monotone heights; (3) matching not chip-firing;
  (4) deterministic tree.

## 3. Candidate experiments

| # | Question | Data | Method | Null / control | Pass bar (what counts as a pattern) | Cost | If positive |
|---|---|---|---|---|---|---|---|
| E1 | Hall-deficiency atlas: does the lives-vs-slots graph predict exactly which lives are hostable in every lineage word, and is any augmenting path left? | words of #2751, #2766, #2802, #2833, #2853 (`WORD-*.json.gz`), census via J-dim1 `code/` + toolkit L/U | `ground_bipartite.py` per word: matching, Koenig burning set, near-miss table (lo - hi = 1 slots) | lo values permuted among slots and first-times permuted among lives (histograms kept): expected deficiency under the null | the real violator set reproduces every realised alias/hostee move of the lineage (ground truth = PR edits) and gives a falsifiable statement per word ("no augmenting path" or an explicit one) | 1 core x 5 min/word | attach an exact alias-feasibility certificate to packages; extend to min-cost augmenting paths with refit costs (weighted matching) as the hostee-move search |
| E2 | Is greedy local frame lowering confluent (least-action-like) on the real words? | #2802 base/extra words; toolkit `frames.Graph` L/U propagation | from the U-labelling, apply random maximal sequences of single-gate lowerings that keep nestedness and lower the moment; record terminal profiles | the certified optimal profile (toolkit) as reference; random gate orders as the variation | >= 95 of 100 orders end at the certified profile = confluent (then a potential-function proof is worth attempting); many distinct terminals = the abelian analogy is dead for this object | 2 cores x 15 min | a monotone "which gates can still be lowered" test = cheap refit-feasibility screen replacing the chain-dual LP for screening |
| E3 | Do the real jump partitions beat a random-composition null, and does the merge price list predict realised PR margins? | local profiles and per-register jump lists of >= 3 lineage words | per register: partition of its width into jumps; moment vs random compositions with the same number of parts; merge prices as in `ground_ceiling.py` | random compositions (same width, same part count); shuffled gate order within sections (Lane A/D controls) | real partition moment below 99% of null compositions on every word; merge prices match realised margins within 1% (calibration: (1,1)->2 = 1.155e-7 vs #2766's 1.154e-7) | 1 core x 5 min | a price list for frame/order edits; the loose ceiling 0.00283 sharpened by lattice caps (L/U domains) into a falsifiable frame-only ceiling |
| E4 | How fast does kappa decay under rule-preserving randomisation of the fill, and is the initial slope the first-order concavity prediction? | fills of #2673/#2751/#2802/#2853 | `ground_fill_walk.py` at 1k..300k moves; clumping index; predicted slope = mean over moves of the split/merge moment delta | the walk itself is the null; seeds x 2 | measured initial slope within 10% of the first-order prediction on every fill (= additive local energy; then a sandpile-style "energy" exists); clumping index >= 0.75 on all fills | 1 core x 2 min/fill | justify local pricing of width edits by an additive energy; otherwise retire the fill-as-sandpile reading |
| E5 | Is there an order-independent local repair of an overflowing fill, and how far is it from the exact re-host? | #2802 fill + one width perturbation (9->8 cut or 8->9 raise on one helper) | overflow rule: a bin over capacity pushes one random role to a random eligible bin with room; 100 random orders; compare kappa with the hosting relaxation/MILP value | identical-profile rate across orders; exact re-solve as reference | >= 95% identical terminals = abelian (not expected); informative bar: repair within 1e-8 kappa of the exact re-host on >= 90% of perturbations | 2 cores x 10 min | a cheap hosting oracle for width edits (we now need MILP/relaxation per candidate) |
| E6 | Where is the window system tight (binding call intervals), and does that explain "promotions lose under real hosting"? | #2802 fill, windows, widths | calls-vs-windows transportation max-flow (scipy `maximum_flow`), min-cut slack per call set; Hall-type check demand(T) <= cap(W(T)) | the same flow on random eligibility shifts (start/stop jittered) | explicit binding intervals with slack 0 (grounded hint: min eligible windows per call = 6, greedy random fills strand 2.8-3.5% of roles); prediction: a width increase on helpers hosted in binding intervals forces >= 1 rank-1 idle child, verified against the recorded promotion losses | 1 core x 5 min | a feasibility screen per word edit before any owner fill; exact (max-flow/min-cut), reusable in the kappa work |

## 4. Grounding measurements (all on the #2802 package, base word / literal fill)

### 4.1 Fill as threshold system (`ground_fill.py`, 38 s)
- 1,332 windows x 112 ports = 149,184 bins; cells 3,580,416; used 2,219,112 (62.0%); kappa root of
  666 x local + idle reproduced: 0.00171779498411863466382723 (certified 0.001717794984118634663827).
- Occupancy by capacity: cap 8: 49,728 bins, all full, one role each; cap 16: 33,152 bins, all full, two roles each;
  cap 32: 5,957 full (4 roles), 17,316 at 31 (idle 1), 9,878 at 27 (three 9s, idle 5), 1 empty; cap 48: 26,558 empty,
  6,594 at 45 (five 9s, idle 3). Idle = {1:17316, 3:6594, 5:9878, 32:1, 48:26558} exactly as in `PROFILE.json`.
- Clumping: 77.35% of bins are empty-or-full (per-window mean); 237 windows fully empty, 770 fully used; a bin holds
  roles from 1..5 distinct calls {1:49728, 2:33152, 3:9878, 4:23273, 5:6594}. Eligible windows per call: min 6, mean 310,
  max 444; demand 3,332 cells per call.
- Greedy random fills that respect every rule but place roles one by one strand 7,581/7,646 (uniform) and
  9,388/9,426 (fill-up) of 271,728 roles (2.8-3.5%): the window system is tight; "random capacity-respecting fill" needs
  a flow-based construction (E6), not a greedy.

### 4.2 Rule-preserving random walk from the real fill (`ground_fill_walk.py`, 2 s per seed)
Single-role moves to a random eligible bin with room and a free family; every intermediate state is a valid fill.
kappa after 1k / 3k / 10k / 30k / 100k / 300k moves: 0.0017155 / 0.0017111 / 0.0016973 / 0.0016677 / 0.0016127 /
0.0015666 (two seeds agree to 4 digits). Initial slope about 2.3e-9 per accepted move; the 48-empties fall
26,558 -> 4,706 by 100k moves and rank-8 idle fragments reach 30k by 300k. The fill's lead over its own randomisation is
about 1.5e-4, two orders above the PR-scale gains (1e-7..1e-6).

### 4.3 Lives vs slots (`ground_bipartite.py`, < 1 s, from `J-dim1/out/CENSUS-b.json`)
- 122 lives (48 followers with hi = 1; 74 with hi >= 4: 68 at hi 5 and 6 at hi 4, including 670/671 and the 72 hosted
  lives); 402 slots (330 free with lo {6:124, 7:14, 8:192}; 72 occupied own-life segments with lo {4:62, 5:10}).
- Time-only graph: every life has >= 80 time-feasible slots; max matching 122 (time never blocks).
- Time+frame graph: the 48 hi-1 followers have degree 0; hi >= 4 lives have degree 24..72; max matching 72 = the
  current aliases; Koenig burning from the 50 unmatched lives burns all 122 lives and 72 slots (deficiency 50);
  restricted to hi >= 4: 74 lives, neighbourhood 72 slots = the pigeonhole for 670/671. 670/671's time-feasible slots
  by dim gap lo - hi: -1: 24 (all occupied), +1: 8, +2: 8, +3: 40 (so a floor-5 lender freed by a refit of one of the
  8 gap-1 lenders would be the only route, which is what the double move already consumed).

### 4.4 Coalescence ceiling and merge prices (`ground_ceiling.py`)
Every register climbing in one jump gives the profile {4:26, 5:2, 7:174, 8:86, 9:352} (640 children, mass 5188);
with the real idle its root is kappa_coalesced = 0.0028258, an exact but loose ceiling for all frame-only and
order-only edits at fixed widths and fixed fill (gap 1.1e-3; the packing cap 0.001758 and class ceilings are tighter
because they include other constraints). Merge prices per call on both words: (1,1)->2 +1.155e-7; (2,2)->4 +2.31e-7;
(1,8)->9 +2.61e-7; (4,4)->8 +4.61e-7; (4,5)->9 +5.14e-7; (1,3,5)->9 +7.01e-7; (1,1,2,5)->9 +8.60e-7, consistent with the
brief's value scale and with #2766's realised margin (B1151 rank 6->5, +1.154e-7).

## 5. Risks and non-claims

- Never call any of this a new method, a sandpile model of multiplication, or a lever: the exact parts are matching
  theory, lattice closure, min-cost flow and concavity; the sandpile vocabulary is a reading aid. No kappa claim.
- The sandpile group, recurrent configurations and identity element are undefined in all four mappings (no graph
  Laplacian is intrinsic to any of them; inventing edges between bins or gates would be a modelling choice to be
  justified, not an invariant of the object).
- Floors/ceilings (lo/hi) are exact only inside the auditor/toolkit frame model; E1's certificates inherit that scope.
- The random walk is a local-move chain started at the optimum, not a uniform sample of feasible fills; its decay curve
  is a property of the chain. The greedy nulls are infeasible and must not be used as controls.
- Multiple comparisons: E1-E6 report z-scores/margins per Lane D's discipline; a "pattern" needs >= 3 lineage words.
- kappa is asymptotic and galactic; nothing here affects real multiplications.

## 6. Open questions for the coordinator

1. Should the plan present mapping (3) honestly as "matching with a burning-style certificate" and drop the chip-firing
   label, keeping E1/E6 as toolkit items regardless of the style exercise?
2. Lane D inventory: which fills (not only words) are available as data for E4/E6 (#2673, #2751, #2853)?
3. Is a weighted-matching hostee-move search (refit costs as edge weights) in scope for the kappa rounds? It is the
   only item here with a plausible kappa consequence, and it is not a style question.
4. E2's confluence test needs the toolkit's L/U propagation on the repo checkout (read-only); confirm it may be imported
   in a later compute round.
