# CONTROLS (Lane D): null models, statistics, multiple-comparison discipline, compute rules

Scope: every pattern claim made by the string lane (A), the growth/Parikh lane (B) or the sandpile lane (C) must be run
against the null models below, with the statistics and the pre-registration rules stated here. Nulls are protocol-specific:
a null says "this statistic on these words does not beat this null"; it never closes a question.

## 1. Null models (ordered from weakest to strongest; a claim must beat N1, and the strongest null that applies)

| id | null | preserves | breaks | how (tools) | cost per sample |
|---|---|---|---|---|---|
| N0 | i.i.d. token resampling from the word's own token frequencies | unigram distribution, length | everything else | numpy | ms |
| N1 | **section-preserving gate shuffle**: permute gates within each of A, cut, B (forward sections only); `cleanup` and `compensation` are DERIVED from the forward program (inverse-reverse at FULL; dirty-column compensation) and must be excluded or re-derived, never shuffled as independent text (measured: including them inflates LZ76 compressibility from 6.1x to 3.7x and is not a pattern) | per-section token multiset, per-section Parikh vector, local profile (rank multiset) | gate order, register chains, semantics | `random.shuffle` per section | ms |
| N1b | **commuting-window shuffle**: move each gate to a uniformly random position inside its exact commutation window `frames.move_window` (then re-check with `frames.commute`); this preserves the linear map of every section exactly | semantics (exact), token multiset, chains up to commuting reorder | the constructor's specific order | toolkit `frames.move_window/moved` | ~3 s per sample on the forward string (estimate) |
| N1c | register-relabelling: apply a random permutation of helper indices (and of port/target indices within their classes) | everything structural | any "pattern" that is really an index-numbering artefact (the constructors assign helper numbers in build order) | 1 line | ms |
| N2 | **random frames with the same Parikh vector**: nested frame assignments drawn from the exact lattice `[lo, hi]` (`bounds.Bounds`, or `Graph.lower/upper` for FULL-WORDs), conditioned on the same local profile; sampler = Metropolis random walk on single-gate frame changes with the profile as a hard constraint (moves that keep H) | gate order, semantics, local profile, kappa | which gates carry the rank | `bounds.Bounds` + walk | 0.2 s build, ~10^4 steps/s |
| N2b | certified-optimal frames (`optimal_frames`) vs shipped frames: the "pattern" must be present in the optimum, not only in a historical frame choice | - | - | toolkit | ~1 s |
| N3 | **random capacity-respecting fills**: for each call time, re-place the 408 roles of that call into idle cells uniformly among placements that respect cell capacity (8/16/32/48), width (compact prefix), replica/time eligibility (`independent_owners.windows`); compare idle-remainder profile and kappa; the pattern relaxation optimum (`relax_r10.py`) is the ceiling control | inventory, mass, windows | the owner fill's packing order | own sampler + `independent_owners.check` on a subset | ~0.5 s per fill (pure Python) |
| N4 | **constructor-synthetic words**: regenerate words with the vendored constructors (`generate.py` / `vendor/generate_words.py` for the T74 borrow line; #1297/#1193 `build_word.py` + `WORD-RECIPE.json` for the FULL-WORD line) under randomised recipe choices (slot sites, pivot choice, alias set); any statistic that is constant across synthetic words is a property of the constructor, not of the kappa-relevant object | the construction family | the specific lineage edits | constructors (data only; run from our copies) | minutes per word; 1 day engineering first |
| N5 | **cross-family control**: the same statistic on the other family (FULL-WORD k8 #1094/#1672 vs BORROW-WORD #2745..#2802); a pattern present in one family only is reported as family-local | - | - | loaders | - |
| N6 | near-miss controls: the 152 auditor-passing but kappa-negative hosted variants in `J-dim1/out/eh/` and the 142 tamper-control mutants (auditor-FAIL) of #2802: a "predictive" motif must separate PASS-and-gaining words from PASS-but-losing and FAIL words | - | - | files held | 0 |

Sandpile-specific nulls (Lane C): (i) random initial chip configurations with the same total chip count on the same window graph
(tests whether the owner fill's stable configuration is special); (ii) random graphs with the same degree/capacity sequence
(tests whether invariants depend on the time-eligibility structure); (iii) the divisible-sandpile / relaxation optimum as the
continuous control (the fill relaxation already exists: `relax_r10.py`).

Growth-function nulls (Lane B): (i) random Parikh deltas of the same mass-zero type (the kappa gain of a random mass-preserving
move vs the lineage's moves); (ii) random orderings of the PR derivation (commutation test: does the order of rule applications
change the end kappa? it should not, since kappa depends only on the Parikh vector; a non-zero order effect is a bookkeeping bug).

## 2. Statistics

- Primary statistics per alphabet: LZ76 complexity (Kaspar-Schuster), Re-Pair grammar size (2 x rules + residual length; or Sequitur
  rule count), block entropies h_1..h_6 and their differences, repeated-motif census (maximal repeats of length >= 4 with count >= 3,
  via suffix array), autocorrelation / periodogram peaks at the structural periods (9, 8, 112, 73, 480, 666, 1332).
- Effect size: compression ratio CR = stat(null mean) / stat(real) for LZ76 and grammar size (CR > 1 = real is more structured);
  for motifs: enrichment = count(real) / mean count(null); for periods: spectral peak height over the null mean.
- Significance: empirical permutation p-value p = (1 + #{null >= real}) / (1 + n) (Phipson-Smyth; never report p = 0);
  z = (real - mean) / sd is reported but is NOT the decision statistic (null distributions of compressibility are tight, so |z| > 10
  is routine and meaningless on its own).
- Multiple comparisons: PRE-REGISTER the test family before running (alphabets x statistics x words x nulls). Example budget for
  the M1 screen: 6 alphabets x 5 statistics x 10 word files x 2 nulls = 600 tests. Decision at FDR 5% (Benjamini-Hochberg) on the
  permutation p-values, which needs n >= 2,000 permutations per test for a usable p-resolution of 5e-4; report q-values. Any test
  added after seeing data is labelled exploratory and gets no q-value.
- Reproducibility: fixed seeds per (test, word), the word blob ids and script sha256 in every result JSON; a result is accepted only
  when a second run with a different seed gives the same decision.

## 3. Evaluation criteria (what counts as a PATTERN; applies to all three lanes)

A finding is a pattern only if ALL of:
1. **Reproducible on >= 3 lineage words** from the frozen set W (DATA-INVENTORY.md section 2), including >= 1 word per family, or
   explicitly declared family-local (then >= 3 words of that family, e.g. #2745/#2751/#2802).
2. **Beats the null by the stated margin**: for compressibility CR >= 1.5 against N1 AND CR >= 1.2 against N1b (the commuting-window
   null, which already removes the trivial "same gates, random order" structure); for motif enrichment >= 2x with q < 0.01; for
   sandpile invariants, a value outside the central 99% of the matched-null distribution on each of the >= 3 words. The margin is
   fixed before the run and written in the experiment row.
3. **Yields a falsifiable prediction** checkable with the exact tools in <= 1 core-hour, for example: "registers whose climb string
   matches motif M admit a retired-lender alias" (checked by `census_r10.py` / pairs rules), "gates of class Y are at their frame floor
   `lo`" (checked by `bounds.Bounds`), "the next lineage word's complete profile lies in cone K and its kappa is <= X" (checked when
   #2833/#2853 are fetched as held-out data), "window class Z always holds an idle 5-remainder" (checked on `FILL.json.gz`).
4. **Held-out check**: the prediction is tested on at least one word NOT used to find the pattern (held-out set: #2833, #2853, and one
   of the FULL-WORD words), and the test outcome is recorded whether it passes or fails.
5. **Non-circularity**: the statistic must not be a restatement of the local profile, the rank mass or the width inventory (all three
   are invariants of the Parikh vector and determine kappa; a "pattern" that is a function of them predicts nothing new). Check by
   recomputing the statistic on an N2 sample (same profile): if it does not move, it is a profile restatement.

Stop rules:
- String lane: if after the M1 screen no (alphabet, statistic) pair reaches CR >= 1.2 against N1b on >= 3 words, stop the string lane
  and record the null (protocol-specific: these alphabets, these statistics, these nulls).
- Sandpile lane: if the owner-fill mapping is not exact (roles are not conserved chips under the real capacity/eligibility rules, or
  stabilisation does not reproduce the literal idle profile), downgrade it to heuristic and allow one experiment only; if the window
  graph is a sink-DAG (trivial critical group), drop the group/burning items without running them.
- Growth lane: if the reachable Parikh set under the formalised move alphabet reproduces every lineage delta but predicts no ceiling
  tighter than the packing cap 0.00175037, record it as a bookkeeping result and stop.
- Any lane: two consecutive pre-registered experiments at null -> stop that lane for this round.
- Whole plan: hard stop at the end of week 2; the deliverable is the document with the nulls, whatever the outcome.

## 4. Compute budget rules

- 12 cores total for the plan; a lane may hold at most 4 cores while another lane is running, 12 when alone. Screening runs <= 20
  core-minutes each; confirmation runs <= 2 core-hours each; whole plan <= 40 core-hours.
- `multiprocessing.Pool(processes=n, maxtasksperchild=50, initializer=_limits)`; every task through `apply_async(...).get(timeout=T)`
  with T set per experiment (default 300 s); on timeout the pool is terminated and the task recorded as TIMEOUT, not retried silently.
- RSS cap: `_limits` calls `resource.setrlimit(RLIMIT_AS/RLIMIT_DATA)` where enforced (Linux); on macOS (not enforced) a watchdog
  thread in each worker polls `resource.getrusage(RUSAGE_SELF).ru_maxrss` every 2 s and calls `os._exit(3)` above the cap
  (default 4 GiB per worker; 6 GiB for the fill experiments). Project peak RSS before launch: workers x (word 30 MB + fill 250 MB +
  statistic working set) and keep the sum under 24 GiB.
- Never load the 6.9 MB `PLAN.json` of #1625 or the 3.7 MB `OWNERS.json.gz` of #1672 in every worker: load once in the parent, pass
  indices.
- No solver runs longer than 10 minutes inside a permutation loop; MILP relaxations run once per word, not per null sample.
- Every run writes `RESULT.json` with: word blob ids, script sha256, seed, n permutations, wall and CPU seconds, peak RSS.
