# Lane A - L-system encoding of the local word (string level)

Planning report, r11 "styles" round. No kappa claim. Everything below was measured on the real #2802 words
(`WORD-base/extra.json.gz`), the #2751 parent word and the #2462 positive word, with the scripts in this directory
(`extract_strings.py`, `measures.py`, `lineage_checks.py`; outputs `OUT-measures.txt/.json`, `OUT-lineage.txt`).
Total compute used: about 4 CPU-minutes, one core.

## 1. Mapping

**Objects.** A BORROW-WORD `w` is seven gate lists plus annotations. Registers are indexed 0..703
(`n = 2v + R = 224 + 480`): 0..111 ports (start frame `[ports[r]]`), 112..223 target rows (start frame empty, end
frame `perp(port)`), 224..703 helpers (start frame `start_extra[r]` or empty, end frame `helper_final[r]` for the 72
cold ends, else FULL). The word splits into two layers that behave differently under rewriting:

1. **Gate skeleton** (op, coefficient, register pattern), the part a constructor emits from a recipe. Exact facts
   measured on #2802: `cut` is the product 8 centres x 22 targets (every centre scatters to exactly 22 of 88 targets,
   each target receives 2 centres, coefficients +-1/4); `precondition` is a fixed per-target motif
   (`add -1` x80, `scale -1/2` x56, `add +1/2` x56); `compensation` (7130 adds, 234 sources x 104 targets,
   coefficients +-1/4, +-1/2) is algebraically derived from the forward word's dirty-response columns (not a string
   rewrite; its gate order is not lexicographic in either (source,target) order); `cleanup` is EXACTLY the
   reverse-inverse at FULL of the recorded forward word (the auditor derives it: `derived = [conv(e) for e in
   reversed(recorded)]`, buffers `r -> r+n` for restored registers): 4395 of 4475 cleanup gates are inverses of
   forward gates and 3931/4394 consecutive pairs run in decreasing forward position; the 80 others are the restore and
   warp images. So `cleanup = rev o inv o buf (A_ord + warps + B + restore)` is a genuine **anti-homomorphic
   production** (reversal composed with a letter-to-letter morphism), the one exact L-system-style rule in the word.
2. **Frame layer** (the `frame` list of every A/B/restore gate, the warp records, the centre frames). It is not
   emitted by a local rule: it is the solution of a global min-moment nested-subspace assignment on the event graph
   (toolkit `frames.optimal_frames`: L/U propagation + chain dual decomposition, certified). The paid profile is the
   histogram of positive rank jumps along each register chain.

**Alphabets (exact functions of the JSON).** Token of a gate = `(section, op, coefficient class, role(target),
role(source), rank = dim(frame), climb(target), climb(source))` with roles P port, T target, C centre, H helper,
L lender register before its B warp, F the same register after the warp (hosting a follower), X removed. Four
granularities were measured: `full` (541 symbols on #2802), `mid` = (section, op, coef, rank) (116), `rank` =
(section, rank) (21), `op` = (section, op, coef) (63). B warps are inserted as a `WARP` letter before gate `rec[0]`
(so the B string has 1872 + 72 letters); the 24 prelude warps of A are letters too.

**Climb strings (exact, auditor-equivalent).** For each register the sequence of positive rank deltas along its chain
`start -> A events -> (cut descents for centres) -> B events (warps = frame replacement, unpaid) -> restore events ->
end`. `extract_strings.py` reproduces `report.local_profile` exactly on all four words (#2802 base/extra
`{1:2382,2:648,3:268,4:128,5:26,8:8}`, #2751 `{1:2366,2:646,3:297,4:120,5:26,8:8}`, #2462
`{1:2363,2:632,3:326,4:120,5:34,7:4,8:4}`), i.e. the climb strings ARE the paid children. The climb alphabet is
{1..9} per register (plus section marks); the word's climb language has **56 distinct strings over 632 climbing
registers** (72 aliased registers have no chain), role-typed: ports 11 strings, targets 9, centres 2, followers 5,
helpers 33 (`OUT-lineage.txt` lists all 56 with counts and roles).

**Lineage edits as productions.** Measured gate-level diff #2751 -> #2802 (seven aliases + two hostee moves):
A 12 gates differ (all frame-only, the #2766 refit A0-A11), B 88 gates differ (25 frame-only, 63 relabelled), cut /
precondition / compensation identical, restore 1 frame, cleanup re-derived (56 gates out, 63 in), warps 65 -> 72,
removed 65 -> 72, start_extra 133 -> 126. #2462 -> #2751 (twelve-source recovery) is larger: A 3479 -> 3535, B 1893 ->
1872 (204 out / 183 in), compensation 7208 -> 7130. So an alias is a **context-sensitive production with bounded
support** (about 14 relabelled gates + one warp letter + one chain deletion) and a **global guard** (frame
feasibility of the whole lattice, certified by `optimal_frames`). In Chomsky terms the skeleton is produced by a
recipe (parametric D0L / DT0L with stages as tables: factory -> port stages -> regroup -> HPE -> cold44, see memory
r7 T-generator), and the kappa-relevant edits are guarded rewrites outside any L-system class.

**Invariants.** Rank mass per register chain = dim(end) - dim(start) (telescoping; the width inventory
`{4:26,5:2,7:62,8:78,9:240}` is exactly `Counter(dim(end)-dim(start))` over live helpers); total rank mass 5188 per
word; number of jumps per register is NOT invariant (merges are the only gains, cf. memory 03:05Z note).

## 2. What is already known

Local corpus (prime generation, April-July): `class_lsys.md` LSYS.2 pumping-lemma impossibility of D0L for Z-primes,
LSYS.6 K-complexity bound; `lsys3_1_taxonomy.md` section 5 **non-transfer rule** (results do not move between D0L /
DT0L / ET0L / CS) and section 6 **small-window rule** (an empirical null is `confirmed null (small-window: P)`, never
"impossible"); `lsys_oeis_closed_howto.md` section 13 "the grammar is a decider, not a generator" (Hartmanis-Shank
1968, Cobham 1972: morphic sequences are k-automatic); `lsysff_1_chomsky_position.md` (L_irr(F_q) not context-free;
D0L towers are a thin regular slice of a non-CF language); zeta turtle L-system = visualisation only. The brief's
lesson applies verbatim: an L-system description is useful only when the rewriting is LOCAL and the predicate of
interest is decidable from the rule. Here the skeleton is local (recipe output) but the predicate (paid ranks, hence
kappa) is a global LP/dual certificate. Prior kappa work already established, with exact tools, that frames at fixed
order are optimal, reorderings plateau (~15k moves, 5998 guided + 8 walks), adjacent commuting swaps give 0 gains
(411 + 3,251 moves), and every single-gate move only re-times rank steps; a string-level re-run of those searches is
not a new experiment.

Literature to cite in the plan: Rozenberg-Salomaa (D0L/DT0L/ET0L, growth functions), Prusinkiewicz-Lindenmayer
(parametric L-systems), Nevill-Manning-Witten 1997 (Sequitur), Larsson-Moffat 2000 (Re-Pair), Charikar et al. 2005
(smallest grammar is NP-hard, O(log(n/g)) approximation: grammar size is a proxy, never a canonical quantity),
Lempel-Ziv 1976 / Kaspar-Schuster 1987 (LZ76 complexity), Cobham 1972 (morphic => automatic). The nearest useful
analogue is **grammar-based compression of instruction streams with register renaming** (motif mining in straight-line
code); Lane D owns the full prior-art list.

Why the mapping can fail: (i) the frame layer is non-local, so no rule reads the paid rank of a gate from its context;
(ii) the word is one finite object executed 666 times, so "patterns" are properties of one constructor output, not of a
language; (iii) any compressibility we find is the recipe we already own (`generate.py` + stage inputs rebuild the
words byte for byte), so a pattern only counts if it predicts something the recipe does not state (alias feasibility,
a kappa-neutral rewrite, the climb string of a register from local data).

## 3. Candidate experiments

| # | question | data | method | null / control | pass bar | cost | if positive |
|---|---|---|---|---|---|---|---|
| E1 skeleton grammar | Is the A/B skeleton a parametric D0L (position-independent rules)? | A/B of #2462, #2751, #2802, #2833, #2853 (fetch as data) | Re-Pair/Sequitur on register-renamed k-grams; extract rule set; replay | N1 section shuffle, N2 random linear extension (dataflow-preserving), constructor words with randomised parameters | one rule set of <= 200 rules regenerates the skeleton of >= 3 words exactly; cross-word rule overlap >= 90% | 1 core x 10 min | a declarative recipe independent of the vendored generator; feeds Lane B's production alphabet |
| E2 climb-string predictability | Is a register's jump string a function of local data (role, entrance dim, width, first/last gate motif)? | 632 climb strings per word, 3-5 words | lookup table / shallow tree, leave-one-word-out | strings permuted among registers of the same role (across-register null: 358 distinct vs 56 real) | >= 90% exact string prediction on the held-out word vs <= 50% null | 1 core x 5 min | frames become readable from the skeleton => an L-system labelling exists; if negative, confirms frames are global |
| E3 alias-feasibility motif | Does a local motif around (lender last gate, follower first gate) separate feasible from infeasible pairs? | 72 realised aliases + J-dim1 census (`out/CENSUS-b.json`, 404 lenders x 52 followers, floors) | k-gram context with rank/role, logistic or rule screen; score the 192 augmenting paths of #2802 | labels permuted; motif replaced by rank-only features (the known floor rule) | AUC >= 0.9 held-out AND the motif ranks the two realised hostee moves (401->564, 403->565) in its top 5 among 192 paths, beyond what the exact floor rule already gives | 1 core x 20 min | a string-level pre-screen for aliases on new PR words (#2833/#2853) before running the exact lattice |
| E4 forward/cleanup production | Verify `cleanup = rev o inv o buf(recorded)` on every lineage word; measure the tail (early_cleanup) climbs in HPE-lineage words | all words we hold | exact replay of the auditor rule in our alphabet | none (verification row) | exact equality on every word (it is the auditor's rule); any word violating it is a data error | minutes | the first exact production of the plan; cleanup never needs to be a string of its own |
| E5 periodicity census | Are there periodicities tied to h=9, 8 centres, 22 targets/centre, v=112, dimension 73, 666 calls? | A/B strings + the global template (`GLOBAL-TEMPLATE` local_programs, 21,483 forward/backward) | lag-match spectra and autocorrelation per alphabet | N2 (random linear extension) and N1 | a peak with z >= 5 over N2 at lag L that is explained by a named parameter; current result: peaks at multiples of 4 (butterfly fans), NONE at 9/73/112 above the generic level | minutes | otherwise record a protocol-specific null: "no h/73/v periodicity in the gate order" |
| E6 rewrite class of the lineage | What class are the stage productions (refit5 -> alias5 -> refit5c -> refit7 -> hostmove2 -> alias7 -> refit7c)? | the 8 stage inputs in `inputs/` and the 8 intermediate words | measure support (gates touched) and guard (frames consulted by `optimal_frames` to certify) per stage | - | statement: support <= 30 gates, guard = all chains => context-sensitive with global guard, outside ET0L; a counterexample would be a stage whose guard is bounded-window | reading + 5 min | fixes the vocabulary of `new_research_styles.md`; tells Lane B which productions commute |
| E7 production of the newer PRs | Express #2833/#2853 dirt-entry rewrites in our alphabet; do they compose with #2802's aliases? | fetched words of #2833, #2853 (data only) | gate-level diff as in `lineage_checks.py`; check support overlap with #2802's 88 edited B gates and 7 warps | - | disjoint support and jointly feasible frames (toolkit) => composable; overlapping support => report the conflict | 1 core x 10 min + one certified frame solve | the only row with a direct kappa consequence; hand to the kappa track, not to this plan |

Multiple-comparison discipline (Lane D): z-scores at n = 17,611 are enormous by construction; the pass bars above
are stated as predictions on held-out words, not as z thresholds.

## 4. Grounding measurement

Script `extract_strings.py` (one core, ~28 s per word, 20 shuffles per null). N1 = section-preserving token shuffle,
N2 = random linear extension of the per-register gate order inside each section (keeps every chain, destroys the
emission order). Re-Pair is the batched greedy variant (grammar size = 2 x rules + final length).

| #2802 base word | n | alphabet | LZ76 real | N1 mean+-sd (z) | N2 mean+-sd (z) | Re-Pair real / N1 / N2 | h2 real / N1 / N2 (bits) |
|---|---|---|---|---|---|---|---|
| full | 17611 | 541 | 1998 | 5821+-13 (-299) | 4471+-19 (-131) | 6632 / 12470 / 10060 | 2.20 / 3.7 / 2.8 |
| mid | 17611 | 116 | 1066 | 3968+-9 (-308) | 3094+-21 (-98) | 3844 / 9134 / 7483 | 1.82 / 2.8 / 2.2 |
| rank | 17611 | 21 | 101 | 1095+-5 (-192) | 620+-8 (-63) | 568 / 2687 / 1651 | 0.15 / 0.7 / 0.4 |
| op | 17611 | 63 | 986 | 3237+-11 (-210) | 2763+-19 (-95) | 3575 / 7706 / 6870 | 1.96 / 2.3 / 2.1 |

Per section (full alphabet, N1): A 3535 gates, LZ76 414 vs 1597; B 1944 letters, 429 vs 995; cleanup 4547, 503 vs
1666; compensation 7130, 603 vs 1450. The extra word gives identical numbers (it differs in 12 B gates and 4 warps);
#2751 and #2462 give the same picture within 5% (`OUT-measures.txt`).

Climb strings (#2802): 56 distinct jump strings, entropy 5.23 bits, vs 358.5 distinct / 7.83 bits when jump sizes are
permuted across registers (same per-register counts) and 190 / 6.93 bits when permuted within registers. Vocabulary
stability: 53 of the 56 strings occur in #2751, 49 in #2462, 49 in all three; per-register strings identical on 704/704
registers base vs extra, 648/704 #2751 vs #2802, 591/704 #2462 vs #2802 (the differing registers are exactly the
edited lenders/followers/targets). Top strings: `11112111` x64 (43 helpers, 21 followers), `11141` x37 (ports),
`11411` x30 (28 targets), `1111` x26 (the width-4 helpers), `32111` x25, `1151` x24 (targets).

Motifs (register-renamed k-grams): A is dominated by the butterfly pair `t += s; s -= t/2` at rank 2 (168 of 3534
2-grams; chains of three such pairs x140 as 6-grams), i.e. the manuscript's H_0 kernel `(u+v, (v-u)/2)`; B by fans of
three `+1` adds on disjoint pairs at rank 6 (x92) and the integral Hadamard `t += s; s -= t/2; s *= -2` = `(u+v, u-v)`
(x56). Lag-match in B (mid alphabet, base 0.053): lags 4 (0.49), 24 (0.48), 12 (0.43), 20 (0.41), 8 (0.41); lag 9:
0.23, 73: 0.10, 112: 0.19 - no periodicity tied to h, the dimension 73 or v beyond the generic level; in A lags 2 and
4 (0.42). Identical on #2751 and #2462.

Reading: the word compresses 3.7x against the shuffle but only 2.9x against the dataflow-preserving null, so most of
the measured structure is the recipe's emission order and butterfly motifs - exactly what a generator output must show.
These numbers prove the pipeline (alphabet, auditor-equivalent climbs, nulls) and give baselines; they are not a
discovery.

## 5. Risks and non-claims

- No kappa claim and no new lever; nothing here changes the frontier reading (#2853 ~0.0017194 top open claim).
- Grammar size and LZ76 are proxies (smallest grammar is NP-hard); the batched Re-Pair variant is deterministic but
  not canonical; alphabet choice moves every z-score. Z-scores at n ~ 17k are meaningless as evidence of a lever.
- Measured on one lineage branch (#2462 -> #2751 -> #2802 + extra); the three-word reproducibility bar is met only
  for the climb vocabulary and the periodicity spectrum, and all three words share one constructor.
- The frame layer (hence kappa) is a global certificate; a string-local rule cannot decide it. Any positive in E2
  would be surprising and must be re-checked with `optimal_frames` before use.
- Reordering/exchange/promotion searches are protocol-specific nulls already run with exact tools (memory
  2026-10-13/15); E1-E7 do not re-run them. Nulls in this plan stay "small-window" per the LSYS.8 rule.
- `cleanup` and `compensation` must not be treated as independent strings: they are derived from A/B (anti-homomorphism
  and response columns). Counting them inflates every compression statistic by about 2x.

## 6. Open questions for the coordinator

1. E3 (alias-feasibility motif) is the only row with a falsifiable prediction on live PR words; should the plan spend
   its first compute there, and should the J-dim1 census (`out/CENSUS-b.json`, `WHY-HI-b.json`) be the labelled set?
2. Who owns the global template string (666 calls x 2 orientations, 21,483 local programs each way): Lane A's
   alphabet or Lane B/C's idle-remainder view? One owner avoids two incompatible alphabets.
3. Shall the move alphabet of Lane B reuse these roles (P/T/C/H/L/F/X) and the per-register jump strings, so that a
   production = (support in gates, chain splice, Parikh delta on the jump histogram)?
4. Fetching #2833 and #2853 words as data (brief 1.1) is needed for the >= 3-word reproducibility bar on anything
   beyond this branch; Lane D should pin their blobs.
5. Is a short note on the two butterfly normalisations (A: `(u+v,(v-u)/2)`, B: `(u+v,u-v)` via `scale -2`) worth a
   row, or is it already fixed by the manuscript's motif schedule (`03-motifs.tex` eq. motif-schedule)?

## Files

- `extract_strings.py` - loader, auditor-equivalent climb accounting, alphabets, nulls N1/N2, motif census, lags.
- `measures.py` - LZ76 (Kaspar-Schuster), LZ78, batched Re-Pair, block entropies, lag-match, shuffles, random linear
  extension, z-stats.
- `lineage_checks.py` - climb vocabulary stability, named-lag spectra, gate-level lineage diffs.
- `OUT-measures.txt`, `OUT-measures.json`, `OUT-lineage.txt` - outputs quoted above.
