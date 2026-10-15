# W-ceiling (r7): is kappa <= q a theorem or a family ceiling?

**Verdict: (b) family-specific.** No document in main (0fdd7d82) or in the top claims states a general theorem kappa <= q.
The cap is a consequence of the recurrence template shared by every outer in the repository's history, and the
repository itself calls it scoped.

## Where the ceiling comes from (#2220, fc09a70b; same formulas in #2180/#2161 and vendored PR1673)
- Binding row: `saving=eps*q_`, `kappa=floor(saving*FLOOR)/FLOOR-BACKOFF`, `main_transform=saving`
  (research/capped-fusion-t74-k554/outer/check_ledger.py:120-122,130); eps<1 strictly
  (outer/FINE-PADDING-COMPOSITION.md:19,33: "The hard cap on any outer of this form is kappa < q").
- Supplier chain: `bit=0.001733427039589844234749`, `b=certified_complex-B_GAP`, `q=b-GAP`, `a=(q+b)/2`
  (check_ledger.py:49-55); recurrence exponents `tau=1-a`, `sigma=1-b`, `internal=tau+(1-stop)*max(sigma-tau,0)`,
  `leaf=sigma+stop*(1-sigma)` (124-126); required `bit-a>0`, `b-a>0`, `(1-stop)*b-a>0`, `1-internal-q>0`,
  `1-leaf-q>0` (144-150). Hence kappa < eps*q < q < a < (1-stop)*b < C and a < bit.
- Grid/backoff ceiling: K <= C - 1/F - B "bounds the declared grid/backoff family, not arbitrary suppliers, other
  backoffs or finer grids" (outer/PROOF-GRID-MAX.md:5-9).
- Main's own statement: kappa < eps*q and kappa < 1-eps "is a scoped conversion bound, not a universal multiplication
  bound"; a < (1-beta)b is "the currently enforced supplier ordering" (docs/research/assembly-domain-audit.md:21-27).

## History: every outer uses the same two-primitive recurrence
- Structured bulk / balanced: kappa < a/(1+2a), a/(1+a) with a the effective bit saving, and `leaf_saving_above_bit`
  = (1-beta)b - a (docs/research/assembly-ceiling.md:22-37,56,61-63; scripts/structured_bulk_assembly.py:69,76-77,103:
  `recurrence=dict(internal=internal,leaf=leaf,...)`).
- Selected #1094: `phase_leaf_above_bit=(1-beta)*b-a`
  (research/coordinated-frames-and-entrance-banks/arithmetic/balanced_shared.py:43); "the complex side binds", kappa
  = a/(1+a) "describes the current construction, not a lower bound" (docs/research/bottleneck-brief.md:18-23).
- RaD derivation: internal nodes use the bit primitive (tau), compact leaves the complex primitive (sigma)
  (references/semantic-bulk/rad20/reports/downstream-semantic-bulk-assembly.md:24,33-34,57).
- Early records were bit-bound instead (docs/research/result-history.md:38-40). No outer ever exceeded
  min(effective bit, complex leaf).

## The degree of freedom
kappa is capped by the weaker primitive ON THE RECURRENCE PATH, through q_below_internal and q_below_leaf. PR1673
removed the 1-eps normalisation loss (kappa -> q), and within this family eps is the only free quantity (distance
to q: 1.68e-60083). Swapping which primitive sits at internal nodes or leaves does not help: both rows cap q.
The only outer-level route above C is a recurrence that keeps the complex primitive off its critical path, for
example compact leaves realised by the bit primitive. That route is bounded by bit - C = 5.367e-5
(about 1,300 helper-donor kernels). It is a new outer construction, not a parameter change, and whether a bit leaf
can implement the phase-leaf step is not addressed in any document read.

## Next step
Determine exactly what the compact complex leaf computes in the semantic-bulk/PR1673 recurrence (RaD report :24-34;
structured_bulk_assembly.py:69,103; the selected proof docs/research/community-batch1099-review.md). Then check
whether the selected bit primitive (research/e8-bit-p111-tuned) or any admitted bit word can realise that step. If
it can, rewrite the ledger with sigma := 1 - bit and re-derive every row.
