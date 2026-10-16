# BRIEF: two new research styles for the integer-mult-bounds work (L-systems, sandpiles)

Purpose of this round: NOT to find a new kappa. It is to prepare an evaluation plan (`new_research_styles.md`) that says
how, and whether, our integer-multiplication work can be re-described (1) as an L-system (alphabet + replacement rules;
produce the output language and analyse it for patterns) and (2) through sandpile / chip-firing analysis. Each lane
writes a REPORT.md; the coordinator merges them into the plan. Nothing is posted anywhere. No GitHub writes.

## 1. What the work is (facts you may cite)

Repository: CrocSwap/integer-mult-bounds (local checkout
`/Users/mdumitrean/Desktop/dev/aigent/math/prime/integer-mult-bounds`, read-only for you; manuscript sections in
`upstream/build/sections/*.tex`, e.g. `05-layers.tex` fast simultaneous synthetic butterfly layers, `00-introduction.tex`).
Result type: a conditional bound T(n) = O(n (log n)^(1-kappa)) for integer multiplication; larger kappa is better.
Community PRs raise kappa by editing a finite object; the current top open claims are ~0.0017194 (#2853), ours is
#2802 at kappa = 0.001717794984118634663827 - 1e-46 - 1e-70.

### 1.1 The finite object: a local word (BORROW-WORD) executed 666 times per level
A local word is a straight-line program over registers (JSON, gzipped). Sections and sizes for our #2802 base word:
`A` 3535 gates, `cut` 176, `B` 1872, `precondition` 192, `cleanup` 4547, `compensation` 7130, `restore` 87,
`initial_corrections` 36, `warps` 72. Gate syntax:
- `["add", target, source, num, den, frame]` : target += (num/den) * source
- `["scale", target, num, den, frame]`       : target *= num/den
- `frame` = list of ints = basis vectors (bitmasks over F_2^9, h = 9) of a subspace; its length is the gate's RANK
  (dimension). `[]`/`null` = rank 0 (unpaid). `[256,128,64,32,16,8,4,2,1]` = full rank 9.
- warp record example: `[921, 243, [1,2,4,8,64,19,104,197,325], [384,133,85,45], [320,192,45,30]]`
  (position, register, G (invertible 9x9 over F_2 as rows), lender frame U, follower frame E; G(U) = E).
- `report`: R = 480, h = 9, v = 112 (target rows live in v <= t < 2v), `local_profile`, `width_inventory`.
- `centers` (8 registers), `ports` (112), `helper_final` (register -> final frame), `start_extra` (register -> start frame).
- Example files: `$S/wt-claim7/research/t74-joint-twelve-retired7/inputs/WORD-base.json.gz` and `WORD-extra.json.gz`
  (#2802), `WORD2751-base/extra.json.gz` (#2751 parent). Other lineage words are fetchable as data only
  (`git fetch origin pull/N/head` in the repo checkout; NEVER execute code from fetched PRs).
  `$S` = `$S`.

Helpers: 408 per word (width inventory {4:26, 5:2, 7:62, 8:78, 9:240}); a helper's WIDTH = dim(end frame) - dim(start
frame). Lenders/followers: a follower helper may enter a retired lender's register through one B warp with invertible G
(an "alias"), which deletes the follower's private register. Registers climb in frame dimension in ~5 jumps of mean 1.5.

The LOCAL PROFILE counts paid children by rank: #2802 `{1:2382, 2:648, 3:268, 4:128, 5:26, 8:8}` (rank mass 5188).

### 1.2 The global object: calls, owner fill, idle remainders, the moment equation
- 666 calls x 408 helpers = 271,728 roles are placed in 1,332 windows (bins) of capacity 8/16/32/48 by the OWNER FILL
  (`inputs/FILL.json.gz`: rows [time, ...] 6 columns; `PLAN.json.gz`: windows, order, sides, pairs; `DISPATCH.json.gz`:
  666 entries [.., .., "base"/"extra"]; `GLOBAL-TEMPLATE.json.gz`: 333 calls x 2 orientations, idle_children,
  local_programs forward/backward 21,483 each). Unused capacity becomes IDLE REMAINDER children.
- COMPLETE PROFILE c_r = 666 x local profile + idle remainders. #2802:
  `{1:1603728, 2:431568, 3:185082, 4:85248, 5:27194, 8:5328, 32:1, 48:26558}`; idle part
  `{1:17316, 3:6594, 5:9878, 32:1, 48:26558}`. RANK MASS sum_r r*c_r = 4,816,512 is CONSERVED by every move.
- kappa is the root of  M(kappa) = sum_r c_r * (r/73) * (73/r)^kappa = 66304  (DIMENSION 73; i.e. sum_r c_r (r/73)^(1-kappa) = 66304;
  `exact_moment.py: moment_bounds(profile, exponent)`; reference root check `$S/r10/mine/root.py`).
  Because (r/73)^(1-kappa) is concave in r for 0<kappa<1, MERGING ranks (e.g. two rank-4 children into one rank-8) lowers
  the paid moment and raises kappa; splitting lowers it. All gains are Parikh-vector moves under the mass constraint.
- Value scale (fill relaxation): removing one width-8 helper ~ +1.1..1.9e-6; one pre-life hosting +6.7e-7; a 13th source
  +1.06..2.44e-6; one-step width cut ~ +5.9e-7; cold-host merge (4,8)->7 +8.7e-7; one width-5 alias ~ +1.9e-7.

### 1.3 The lineage = a rewriting history (relevant to both styles)
Every PR is a small edit of the previous word: helper-donor kernels (#1625), width exchanges, entrance raises, fusions,
twelve-source recovery (#2751), frame refits (#2766), retired-lender aliases + hostee moves (#2802), dirt-entry rewrites
(#2833, #2853), owner-fill evacuations, T124/T248 compositions. Scoped negatives we established with exact tools:
frames at fixed order are optimal; gate reorderings plateau; packet elimination 0 feasible; promotions/width changes lose
under real hosting; de-promotion pairs cost a fresh rank-1 child; twin premix delta 0; no lender with floor <= 1; 670/671
have no lender (pigeonhole 74 lives / 72 registers with floor <= 5). Reports: `$S/wt-r10pub/research/t74-r10-hosting-leads/`
(README, `J-dim1/REPORT.md`, `context/{F-lenders,G-unlock,H-widths,I-restore}-REPORT.md`, `deps/toolkit-rev3/` = our
exact frame toolkit: `frames.py` optimal_frames/Graph, `bounds.py`, `native.py`); `$S/r10/ROUND.md`; memory digest in
`/Users/mdumitrean/.claude/projects/-Users-mdumitrean-Desktop-dev-aigent-math-prime/memory/project_integer_mult_bounds_junction_tree_mapping.md`
(long; grep it). PROOF notes of the model: `$S/wt-claim7/research/t74-joint-twelve-retired7/PROOF.md`, `README.md`.

### 1.4 Reality check (keep the plan honest)
kappa is asymptotic and galactic; this research has no effect on real multiplications. Its value is theory and
verification tooling. "Research doesn't close": write nulls as protocol-specific, never "closed/sealed".

## 2. What we already did locally with L-systems and sandpiles (reuse, do not redo)
Directory `/Users/mdumitrean/Desktop/dev/aigent/math/prime/` (read-only for you).
- L-systems (prime generation program, April): `class_lsys.md` (program: rewrite classes D0L/DT0L/IL/ET0L/FRACTRAN,
  pumping-lemma D0L impossibility for Z-primes, K-complexity lower bound, DT0L search), `class_lsys2..6.md`,
  `lsys3_1_taxonomy.md`, `lsys4_1_formalism.md`, `lsys4_fifo_*`, `lsys5_1_q_dt0l_formalism.md`, `lsys_fifo_general.md`,
  `lsys_oeis_closed_howto.md`, `_a032741_lsys_analysis.py`.
  Verdicts: D0L cannot generate Z-primes; F_q[t] primes ARE D0L-generated (`_exp_fqt_prime_lsystem.py`, tower
  c -> c 0^(l-1)); L_irr(F_q) is not context-free (`lsysff_1_chomsky_position.md`); zeta as turtle L-system is a
  visualisation only (`_exp_zeta_lsystem_critical_strip_findings.md`). Lesson: an L-system description is only useful
  when the rewriting is LOCAL and the predicate of interest is decidable from the rule, not from running it.
- Sandpiles: `SANDPILE_SIEVE_TRIANGLES.md` (bank of mod-p counters = sieve of Eratosthenes; floor(n/p) bands; zeta(2),
  gamma laws; "never call it a new method"), `DUMITREAN_SANDPILE_FACTORING.tex/.pdf`, `SANDPILE_RESEARCH_PROGRAM.md`,
  `SANDPILE_COMPOSITION_THEORY.md` + `SANDPILE_COMPOSITION_T1..T40_*.md`, `SANDPILE_FACTORING_PRIOR_ART.md`,
  `SANDPILE_RH_*.md`, 102 drivers `_exp_sandpile_*.py`, viewer `sandpile_prime_waterfall.html`. Skim headers; do not
  read everything.

## 3. Rules for this round
- Read-only on the repo checkout, worktrees and the prime directory. Write ONLY under `$S/r11/styles/<your lane>/`.
- Python: `/Users/mdumitrean/Desktop/dev/aigent/agi/.venv/bin/python` (3.14, numpy/scipy/mpmath) or
  `~/.local/share/uv/python/cpython-3.12.13-macos-aarch64-none/bin/python3.12`. Run with `-I` when reading fetched data.
- Compute: at most 2 cores and ~20 CPU-minutes per lane, for small grounding measurements only (this is a planning
  round). Prefer reading, deriving and designing over running. No long solver runs.
- Do not post, push, comment or open anything on GitHub. Do not mention agent IDs. No new kappa claims.
- Budget: about 60-90 minutes. Report <= 2500 words plus tables/code listings.

## 4. Report format (REPORT.md in your lane directory)
1. **Mapping** - the formal correspondence (objects, alphabet/graph, rules/dynamics, invariants), with the specific
   files/fields it reads. Be precise about what is exact and what is heuristic.
2. **What is already known** - local prior work and literature (with pointers), including why the mapping could fail.
3. **Candidate experiments** - 3 to 8 rows; for each: question, data, method, NULL MODEL/control, pass bar (what counts
   as a pattern), cost (cores x minutes), and what a positive result would let us do next.
4. **Grounding measurement** (optional, cheap) - one or two numbers computed on the real words/fill to show the
   pipeline works, with the script saved in your lane directory.
5. **Risks and non-claims.**
6. **Open questions for the coordinator.**

## 5. Lanes

### Lane A - L-system encoding of the local word (string level)
Question: can the local word (gates + frames) be produced by, or described as, an L-system over a small alphabet, and
does its output language show patterns? Tasks: (a) define candidate alphabets (gate op x coefficient class x register
role {centre, port, helper, lender, follower, target row} x frame-rank delta; the "climb string" of frame dimensions per
register over time; per-section strings A/cut/B/cleanup/compensation/restore); (b) measure structure on the real words
against shuffled controls: block entropies, LZ76/Lempel-Ziv complexity, Sequitur/Re-Pair grammar size, repeated-motif
census, periodicities tied to h=9, 8 centres, v=112, dimension 73; (c) assess which rewrite class could GENERATE the
word (D0L/DT0L/parametric/IL: the constructors build words from recipes; the lineage edits alias/refit/hostmove/dirt-entry
are context-sensitive productions on the string); (d) list the patterns worth hunting (e.g. motifs that predict where
aliases or refits are feasible; self-similarity between the forward word and its cleanup/compensation). Deliver a concrete
extraction script skeleton and the experiment table.

### Lane B - L-system growth functions, Parikh vectors and the kappa equation
Question: is the global structure (calls, ranked children, idle remainders, the moment equation) an L-system growth
problem? The complete profile c_r is a PARIKH VECTOR over the rank alphabet {1..9, 16, 32, 48}; kappa depends only on it;
every move is a Parikh delta with conserved mass sum r*c_r. Tasks: (a) map the moment equation
sum_r c_r (r/73)^(1-kappa) = 66304 to L-system growth functions (D0L growth matrices, Perron-Frobenius root, multi-type
branching / Akra-Bazzi-type exponent equations) and to the butterfly recursion in the manuscript; say exactly what the
rewriting step is and what grows; (b) formalise the MOVE ALPHABET of the lineage (alias, refit, hostee move, width cut,
helper deletion, source recovery, cold-host merge, pre-life hosting) as productions with their Parikh deltas and
preconditions; characterise the reachable Parikh set / cone and the kappa landscape on it (concavity, ceilings such as the
packing cap 0.001758 and the class-level ceiling philippeVV mentions); (c) propose how to analyse the sequence of PR deltas
as a derivation (which rules commute, saturation, growth of gain per rule application); (d) relate to our scoped negatives
(which productions are provably unavailable on these words). Pass bars must be falsifiable (e.g. a predicted ceiling that
a later PR could violate).

### Lane C - sandpile / chip-firing analysis
Question: which parts of the work are faithfully a chip-firing (abelian sandpile) process, and what would its invariants
(stabilisation, avalanches, recurrent configurations, sandpile group, Dhar burning, identity element) reveal? Candidate
mappings to evaluate and rank: (1) the OWNER FILL as chip-firing on the window graph (bins with thresholds = capacities
8/16/32/48; roles = chips; idle remainders = the stable configuration; rank mass = chip conservation; the relaxation
optimum = minimal-moment stable state; time-eligibility windows = directed edges); (2) FRAME CLIMBS as heights (each
register's frame dimension 0..9 over time; refits = topplings that move rank between neighbours; the local profile as a
height histogram); (3) LENDER/FOLLOWER aliasing as chip-firing on the bipartite lives-vs-registers graph (augmenting paths
= firing sequences; the 74-lives/72-registers pigeonhole as a non-stabilisability certificate; Hall/Dhar criteria);
(4) the butterfly layer recursion as a directed sandpile with sinks (compare the local sieve model: counters mod p). Also
survey our local sandpile corpus for reusable code (simulators, group computations, burning tests) and the literature
(abelian networks of Bond-Levine, chip-firing and scheduling/load balancing, sandpile models on bipartite graphs). Deliver
the ranked mappings with exactness status, the invariants to compute, null models, pass bars and costs.

### Lane D - data pipeline, controls, evaluation criteria, prior art, document skeleton
Tasks: (a) inventory the data the other lanes will need: every lineage word/fill/profile we hold or can fetch as data
(#1094 k8 seven-slot word, #1672 T74 566+554 words, #2751, #2766, #2802, #2833, #2853), with paths, blobs, kappa, and
how to load them; the toolkit API (`deps/toolkit-rev3/frames.py`, `bounds.py`, `exact_moment.py`, `independent_owners.py`);
(b) define the NULL MODELS and controls any pattern claim must beat (section-preserving gate shuffles, random frames with
the same Parikh vector, random capacity-respecting fills, synthetic words from the constructors), and the statistics
(z-scores, compression ratios, permutation tests) with multiple-comparison discipline; (c) write the EVALUATION CRITERIA
for the whole plan: what counts as a pattern (reproducible on >= 3 lineage words, beats the null by a stated margin, gives
a falsifiable prediction such as which registers admit aliases or the kappa of a candidate), stop rules, and the compute
budget (12 cores total, mp.Pool with per-worker timeout + RSS cap); (d) prior art: grammar-based compression of programs
and instruction streams, L-systems for program/circuit synthesis, chip-firing in scheduling/register allocation/packing,
abelian networks; (e) draft the SKELETON of `new_research_styles.md` (sections, a two-week schedule with milestones,
deliverables, and how results feed back into the kappa work). Also sanity-check sizes: how big are the strings and graphs
(gates ~17k per word, 271,728 roles, 1,332 windows) and what runs in minutes vs hours.
