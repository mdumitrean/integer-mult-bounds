# Lane D REPORT: data pipeline, controls, evaluation criteria, prior art, document skeleton (r11 styles round, 2026-10-15)

Companion files in this directory: `DATA-INVENTORY.md` (every lineage word/fill/profile, formats, blob ids, loaders, sizes, run
times), `CONTROLS.md` (null models, statistics, multiple-comparison discipline, pattern criteria, stop rules, compute rules),
`SKELETON.md` (outline of `new_research_styles.md`, two-week schedule, deliverables, feedback into the kappa work), and the
grounding scripts `inventory_scan.py`, `fill_scan.py`, `fill_bins.py`, `string_cost.py`, `word_timing.py` with their `.out` files.
Nothing was fetched or posted; the only network access was one read-only `git ls-remote` of PR heads. Compute used: < 2 CPU-minutes.

## 1. Mapping: data inventory and loader design

**What we hold (data only, read-only).** Ten word files from seven constructions in two formats, plus the global objects of #2802:

| construction | kappa | format | where | held |
|---|---|---|---|---|
| #1094 selected (seven-slot k8, T16) | 0.001672660197076918 | FULL-WORD | `$S/k8/K8S7-WORD.json.gz` = blob 723decbc inside `origin/main:research/community-frontier1094-audit/selected-replay.tar.gz` | yes |
| #1195 ours (k8 fusions) | 0.001675658002271934 | FULL-WORD | branch `k8-source-holder-fusions-merge` 99a8a424 | yes |
| #1625 ours (pivot-566 kernel) | 0.001676896669021299 | FULL-WORD | `$S/wt-566` branch `t74-pivot566-kernel` | yes |
| #1672 (pivot-554 on #1625: "566+554 words") | 0.001676938111022438 | FULL-WORD | head b8ab040d (local commit); copies `$S/r3/inputs/*-566-554.json.gz` (blobs 76c01583 / e86142b3) | yes |
| #2679 philippeVV (source of the borrow machinery) | not recorded | BORROW-WORD | head 2e2cf565 (local commit) | yes |
| #2745 jeremykothe2 | 0.0017161404259974415 | BORROW-WORD | head 4f485de0; copies `$S/r9/inputs/` (33524d8f / 583a98c6) | yes |
| #2751 tekuuu | 0.001717141586348426338109 | BORROW-WORD | head 4cfbb0cc; `$S/wt-claim7/.../inputs/WORD2751-*` (f1fc67a6 / f06e80c4) | yes |
| #2766 DavidAriasC | 0.001717256973467002308270 | BORROW-WORD | head e6df920c reachable only via `.git/FETCH_HEAD` (fragile) | yes |
| retired5 ours (unpublished) | 0.001717409316335491643448 | BORROW-WORD | `$S/wt-claim5` | yes |
| **#2802 ours** | 0.001717794984118634663827 | BORROW-WORD | `$S/wt-claim7/research/t74-joint-twelve-retired7/` + FILL/PLAN/DISPATCH/GLOBAL-TEMPLATE, 8 stage inputs, 142 controls, census | yes |
| #2833, #2853 philippeVV (dirt-entry) | unverified (#2853 ~0.00171938) | BORROW-WORD (expected) | NOT held; remote heads e9307b48 / d01045df | no |

Each row has local/complete profiles, width inventories, idle parts and blob ids in `DATA-INVENTORY.md` section 2. Complete profiles
and exact kappas for #2733/#2745/#2751/#2766/#2767 are pinned in `$S/wt-claim7/.../evidence/`.

**Two formats, two loaders.** The k8/gauge44/T74-kernel line (#1094, #1195, #1625, #1672) ships FULL-WORDs (keys `early_cleanup`,
`refactored_cleanup`, `root_lines`, `scatter`; no `warps`); the borrow line (#2679 ... #2802) ships BORROW-WORDs (`warps` 65-72,
`compensation` 7,130 rank-0 adds, `restore` 87, `initial_corrections` 36, `removed`, `prelude_events`). Gate syntax and `report`
are identical. The loader design is therefore: (i) `wordmodel.Word` + `bounds.Bounds` (byte-identical copies of #2745's handoff code in
`$S/wt-r10pub/.../J-dim1/code/`) for BORROW-WORDs: time-ordered events including B warps (13,064 events on #2802), per-register climb
strings (632 live registers, 3-9 jumps each), exact per-gate frame lattice `[lo, hi]` over all refits (875 of 5,470 gates have slack);
(ii) toolkit-rev3 `word.inline` + `frames.Graph` for FULL-WORDs (0.1 s: 1,662 variables, 137 components); `frames.move_window` gives the
exact commutation windows that define the commuting-window null; (iii) a thin normaliser that emits the same token stream
`(section, op, coefficient class, rank[, role])` from either format so every statistic runs on both families. Signatures, docstrings
and tested snippets are in `DATA-INVENTORY.md` sections 4-5. The fill loads as 271,728 rows `[time, helper, owner_replica, child,
port, offset]` (666 call times x 408 helpers), the 2,016 idle cells carry capacities 8/16/32/48 (`GLOBAL-TEMPLATE.idle_children`),
and the T37 `PLAN.windows` (666 entries, lifted to the 1,332 windows that `OWNERS.json` reports) give the time-eligibility structure.

**Exact vs heuristic.** Exact: profiles, rank mass, the moment root (`exact_moment.moment_bounds`, 90-digit bisection in 0.10 s),
frame lattices and certified optimal frames, the literal owner check, commutation windows. Heuristic: any string statistic, any null
sampler, the fill relaxation (an upper bound), and every "pattern" until it has produced a prediction that the exact chain confirms.

## 2. What is already known

- Local: the L-system corpus (`class_lsys*.md`, `lsys*`): an L-system description is useful only when the rewriting is local and the
  predicate is decidable from the rule, not from running it; D0L cannot generate Z-primes; F_q[t] irreducibles are D0L-generated. The
  sandpile corpus (`SANDPILE_SIEVE_TRIANGLES.md`, `SANDPILE_FACTORING_PRIOR_ART.md`, 102 drivers) contains a mod-p counter model and a
  circulant critical-group study; the only reusable chip-firing-group machinery is a sympy Smith-normal-form / avalanche prototype
  (`_exp_sandpile_beyond.py`); there is no Dhar-burning or recurrent-configuration library, so Lane C needs a ~200-line module
  (networkx 3.6, sympy 1.14, scipy 1.17, ortools 9.15 are in the venv). The prior-art file's lesson stands: never call a re-description a
  new method.
- Exact scoped negatives from r3-r10 (binding for every lane as "unavailable productions"): frames at fixed order are optimal; gate
  reorderings plateau; no lender with floor <= 1 (every non-target register reaches dim >= 4 before retiring); 670/671 have no lender
  (pigeonhole 74 lives / 72 registers); width cuts by restoring ordinary helpers: 0 of 15,017 feasible slots; promotions lose under real
  hosting; the fill is at its fixed-inventory optimum (#2733 lattice certificate, 5.8e-17); the generic packing cap is 0.00175037 (realized
  0.981). Reports: `$S/wt-r10pub/research/t74-r10-hosting-leads/{README.md,J-dim1/REPORT.md,context/*-REPORT.md}`.
- Literature (from memory; titles and venues I am confident of, page numbers not re-verified online in this round):
  grammar-based compression: Nevill-Manning and Witten 1997 (Sequitur, JAIR 7); Larsson and Moffat 2000 (Re-Pair, Proc. IEEE 88);
  Lempel and Ziv 1976 (IEEE Trans. IT 22) and Kaspar and Schuster 1987 (Phys. Rev. A 36) for LZ76; Kieffer and Yang 2000 (grammar-based
  codes, IEEE Trans. IT 46); Charikar et al. 2005 (smallest grammar, IEEE Trans. IT 51); Lohrey 2012 (SLP survey). Compression of
  programs and instruction streams: Larus 1999 "Whole program paths" (PLDI; Sequitur on instruction traces, the closest precedent);
  Debray, Evans, Muth, De Sutter 2000 (code compaction, TOPLAS 22); Lefurgy et al. 1997 (code density, MICRO-30); Burtscher et al. 2005
  (VPC3 trace compression, IEEE TC). L-systems for synthesis: Rozenberg and Salomaa 1980 (The Mathematical Theory of L Systems);
  Prusinkiewicz and Lindenmayer 1990; Kitano 1990 (graph-generation grammar for networks, Complex Systems 4); Gruau 1994 (cellular
  encoding); Hornby and Pollack 2001-2002 (evolved L-systems for designs, Artificial Life 8); Haddow, Tufte, van Remortel 2001
  ("Shrinking the genotype: L-systems for EHW?", ICES, LNCS 2210; details unverified). Growth functions: Parikh 1966 (JACM 13); Salomaa and
  Soittola 1978; Akra and Bazzi 1998 (Comput. Optim. Appl. 10). Chip-firing: Bak, Tang, Wiesenfeld 1987; Dhar 1990 (PRL 64) and 1999
  (Physica A 263; burning test); Bjorner, Lovasz, Shor 1991 (Europ. J. Combin. 12); Biggs 1999 (J. Algebraic Combin. 9, DOI
  10.1023/A:1018611014097, verified via the local prior-art file); Baker and Norine 2007 (Adv. Math. 215); Holroyd et al. 2008 (chip-firing
  and rotor-routing on directed graphs); Levine and Peres 2009 (divisible sandpile, Potential Analysis 30; the continuous relaxation that
  matches our fill relaxation); Levine and Propp 2010 (Notices AMS); Klivans 2018 and Corry and Perkinson 2018 (books). Abelian networks:
  Bond and Levine 2016 I-III (SIAM J. Discrete Math 30; Selecta Math 22; J. Algebraic Combin. 43); Cairns 2018 (undecidable halting in 3D);
  Kiss and Tothmeresz 2015 and Hujter, Kiss, Tothmeresz 2017 (hardness of reachability and rank). Chip-firing / token distribution in load
  balancing and scheduling: Bitar and Goles 1992 (parallel chip firing, TCS 92); Goles and Kiwi 1993 (TCS 115); Rabani, Sinclair, Wanka
  1998 (FOCS); Friedrich, Gairing, Sauerwald 2012 (quasirandom load balancing, SIAM J. Comput. 41); Berenbrink et al. 2015-2016
  (deterministic load balancing). Register allocation or bin packing phrased as chip-firing: I know of no reference (unverified absence;
  Lane C should not claim novelty either way). Multiple comparisons: Benjamini and Hochberg 1995; Phipson and Smyth 2010.
- Why the mappings could fail (documented in CONTROLS.md as nulls): the cleanup is the exact inverse-reverse of the forward program, so
  any whole-word string statistic is dominated by that mirror (measured below); helper numbering follows build order (index artefacts);
  the constructors are themselves grammars, so grammar size measures the constructor, not the kappa-relevant object; the fill's window
  graph may be a sink-DAG, on which the sandpile group is trivial; and any statistic that is a function of the local profile, mass or
  inventory is a restatement of the Parikh vector, which already determines kappa.

## 3. Candidate experiments (pipeline and control level; the lane experiments A/B/C live in the other reports)

| id | question | data | method | null / control | pass bar | cost | if positive |
|---|---|---|---|---|---|---|---|
| D1 format parity | do the two loaders emit the same token stream and the same profile on both families? | all 10 word files | normaliser; `word.recount` vs `report.local_profile`; `Word.paid` vs profile | none (exactness check) | 10/10 equal, warps counted once | 1 core x 1 min | unblocks cross-family statistics (criterion 1) |
| D2 null calibration | how wide are N1 / N1b / N1c / N2 distributions of LZ76, Re-Pair size, h_k on each word? | 10 words | 2,000 samples each, pool 12 | - | sd reported; N1b width > N1 width expected | 12 cores x 10 min | sets the achievable p-resolution and the CR margins used by Lane A |
| D3 pre-registration budget | how many tests can the FDR budget carry at n = 2,000? | - | compute q-value floors for 600 / 1,200 / 2,400 tests | - | q < 0.05 reachable for >= 300 tests | 0 | fixes the M1 screen size |
| D4 held-out protocol | can #2833/#2853 serve as held-out words? | `git fetch origin pull/{2833,2853}/head` (data only, M4) | load with the BORROW-WORD loader; D1 on them | - | both load; profiles match their CLAIM.json | 1 core x 2 min | predictions get a clean test set |
| D5 constructor null feasibility | can `generate.py` / `build_word.py` produce randomised synthetic words (N4)? | #2802 `generate.py`, #2679 source, #1297 `build_word.py` | identify seed points; regenerate the shipped words byte-for-byte first | regenerated = shipped | 1 day engineering, then minutes per word | the strongest null becomes available to all lanes |
| D6 fill mapping exactness (shared with C) | does within-window stabilisation from the literal roles reproduce the idle profile {1:17316,3:6594,5:9878,32:1,48:26558}? | #2802 FILL/PLAN/TEMPLATE | compute capacity - used per cell, compare | relaxation optimum (`relax_r10.py`) | exact equality | 1 core x 1 min | sandpile mapping (1) is exact; else heuristic |
| D7 run-time table | which analyses run in minutes vs hours on 12 cores? | measured numbers | extrapolate (DATA-INVENTORY.md section 6) | - | table | 0 | schedule and budgets |

## 4. Grounding measurement (done; scripts in this directory)

- `string_cost.py` on #2802 base, alphabet (section, op, coefficient class, rank): forward string A+cut+B = 5,583 tokens over 79 symbols;
  LZ76 complexity 302 vs 1,846 for one section-preserving shuffle (CR 6.1); Re-Pair grammar ~1,080 vs ~4,106 (CR 3.8). Whole word (17,539
  tokens, 114 symbols): LZ76 1,052 vs 3,928 (CR 3.7); Re-Pair ~3,535 vs ~8,817. The whole-word ratio is lower because `compensation`
  (7,130 rank-0 adds over 8 coefficient classes) is low-entropy in both the real word and its shuffle and dilutes the ratio, while the real
  word's `cleanup` is the exact mirror of the forward program (free structure for LZ76); both are derived text and must be excluded or
  re-derived in the null (CONTROLS.md N1). This is a pipeline demonstration, not a pattern: it is one word, one shuffle, no commuting-window null.
- `word_timing.py`: `Word` 0.05 s, `Bounds` 0.22 s, 90-digit root 0.10 s (reproduces 0.0017177949841186346638272299...). `fill_bins.py`:
  271,728 roles, 2,016 idle cells with caps {8:672,16:448,32:448,48:448}, 122,625 cells touched, <= 5 roles per cell over all times, one
  within-bin shuffle 0.17 s. Toolkit `Graph` on the k8 word 0.1 s. Everything word-level runs in seconds; permutation tests at n = 2,000
  take ~10 minutes per word on 12 cores (forward strings ~1-2 minutes); fill chip-firing ~0.5 s per sample; the only hour-scale items are
  Smith normal form of the 1,332-node window Laplacian in sympy (avoid; use python-flint/PARI or prove triviality first), constructor
  re-generation engineering (a day), and `full_replay.py` (411 s, not needed in this plan).

## 5. Risks and non-claims

- No kappa claim and no "new method": a re-description that reproduces the profile/root bookkeeping is a restatement. Research does not
  close; nulls are protocol-specific.
- #2766's head exists locally only through `FETCH_HEAD` (no ref); a `git gc` would drop it. Re-fetching `pull/2766/head` restores it.
- #2833/#2853 are not held; everything said about them is from the comment sweep and is unverified.
- The literature list is from memory and was not re-verified online in this round (only `git ls-remote` was run); every entry is marked
  as such in `SKELETON.md` appendix B and should be checked before the document is circulated.
- The grounding CR values are expected to shrink sharply under the commuting-window null and must not be quoted as evidence of structure.
- The fill is at its fixed-inventory optimum, so fill-level patterns can only redistribute idle remainders; gains require word changes.
- Compute: the plan fits 12 cores and ~40 core-hours; the pool caps in CONTROLS.md section 4 are mandatory (mp.Pool timeout + RSS watchdog).

## 6. Open questions for the coordinator

1. Frozen word set: accept W = {#1094, #1672 (2), #2745 (2), #2751, #2766, #2802 (2)} with #2833/#2853 as held-out (fetched at M4 only)?
   Should #2679 and retired5 be added as "intermediate lineage" words for the derivation analysis of Lane B?
2. Margins: CR >= 1.5 vs N1 and >= 1.2 vs N1b, motif enrichment >= 2x at q < 0.01: too strict, too loose? They were chosen so that a
   positive result is worth an exact census run (<= 1 core-hour).
3. Is one engineering day for the constructor null (N4) worth it in a two-week plan, or do we accept N1b as the strongest string null?
4. Lane C's group-theoretic items (sandpile group, burning, identity) are conditional on the window graph not being a sink-DAG; should the
   exactness audit (M2) gate them, as proposed, or run regardless as a tooling exercise?
5. Who owns the merge of alphabets (Lane A) with the normaliser (Lane D) at M0, so that the FULL-WORD family is covered from day one?
