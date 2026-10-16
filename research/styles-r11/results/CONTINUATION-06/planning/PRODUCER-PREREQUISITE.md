# Why the changed-word branch is not ready for execution

This is source/proof planning, with no new candidate census, scientific import,
refit, cap computation, or experimental test. The independent packing-cycle
branch is the preferred executable construction this round.

The source is Marius-Paul Dumitrean's PR2979, commit
`be191346391661f4d35fc0d1508d0a6029572576`. Its authoritative README, lines
232–256, reports the lowering/extraction fixed point and the final-word
negative rewrite censuses, and leaves B re-pairing, later-A input changes, and
integral packing open. Its complete inherited CREDITS/NOTICE/SOURCES and
`data/words/PINS.json` remain the attribution here. The source bytes and
specific forced-frame witness are pinned in
`../../CONTINUATION-05/planning/FRAME-OBSTRUCTION.md`.

## The forbidden directions do not disappear through scalar cancellation

The immutable CONT05 post-run proof shows that `73` carries live line224 and
`363` carries line262 forced by the literal A3129 contact with live port30.
The two shear orientations emit a nonzero read of line224 into target170 or
line262 into target194, contrary to their final hyperplanes. Altering the
coefficient, cancelling a scalar value elsewhere, or renaming a carrier does
not remove that common-frame lower bound. The original R2 results remain
EXPLORATORY; the separate static obstruction is not a reclassified experiment.

The named capture quartet does not supply an immediate escape. In the pinned
word, B675 reads363 into532, B677 reads73 into533, B1226 reads532 into target205,
and B1228 reads533 into target118. Neither capture helper has a B warp/reset.
Thus a direct mixing of these capture helpers before those target reads
propagates the same forced directions: line224 is outside target205's
`perp(491)`, and line262 is outside target118's `perp(13)` (both binary dot
products have odd parity). This obstructs the direct corresponding scalar
shears, not all possible simultaneous four-register implementations.

Both source words have the same named B and restore blocks. Their gzip hashes
are `abaf67bfcb257528658c906b612f57025617592bd7889828f92b97a5f4f4300d`
(base) and `e0eaf64c4d5d324693d43889bce1b9e53e8da00402105c8c978fd102f208bed7`
(extra). No source byte or frozen CONT05 program was changed.

## A precise prerequisite for a later-A production

Fix an internal A cut. Let the exact free-operator prefix map on non-target
registers be `P`, its already accumulated target map be `E`, and the remaining
non-target and target maps be `M` and `Q`. Let the original front compensation
be `C`. These symbols must be extracted from the full dirty-input program,
including actual warps and all inputs; a profile or scalar-only projection is
insufficient.

Insert a scalar invertible map `S` at the cut and an output map `O`. Exact
preservation of the original non-target and target operators requires

```
O M S P = M P,
C_new = C - Q (S-I) P.
```

For a rank-one transvection `S=I+u v^T`, `v^T u=0`, a sufficient output choice
is

```
O = M S^-1 M^-1 = I - (M u)(v^T M^-1).
```

Before this becomes a candidate generator one must exhibit nonzero scalar
`u,v` for which the transported factors define an allowed scalar output map,
`C_new` is an allowed zero-frame scalar compensation on original input
columns, and every intermediate contact has a feasible frame. In particular,
the *actual attained frames* at this internal cut, not the prelude's zero
frames, enter the feasibility test. The naive basis vectors on363/73 fail
that last test at the named targets. Prefix warps can also make `C_new`
operator-valued, which is not an allowed scalar compensation.

The existing paired-extraction kernel routines provide a starting method for
exact linear constraints on these factors. Their prelude-specific input
placement and compensation rule cannot be transplanted without deriving the
prefix-aware formula above. No nonzero legal solution or cost-bearing kernel
direction has been established here. Removing an existing extraction is also
not automatically valid after later paired maps have been composed with it.
This missing construction, followed by a complete fresh native admission,
is a larger prerequisite than the available fixed-word packing cycle.

## The saved unchanged-word frame certificate

The four immutable CONT05 reference receipts (both providers and seeds) return
the source profile and no normal7 cap. Their exact interval frame optimizer
has `assignment_lower == lower`, with fine profile
`{1:2445,2:706,3:232,4:108,5:18}` and fixed centre payments omitted from that
mutable-frame optimization. The displayed certificate width is about
`1.30156043827621616425326590328e-64`; this is arithmetic on the already saved
bounds, not a new solve.

The trusted frame engine is
`research/t74-r10-hosting-leads/deps/toolkit-rev3/frames.py`, SHA256
`59d5f5725c50c5d6c22178e82ee79a5d7646f0133b1aa267081ec1ad228ec437`.
Its documented tariff uses normalization7168 and a per-child fallback term
in addition to the recursive rank cost. The saved exact bound therefore
leaves negligible headroom for that fixed-DAG, documented-tariff problem.
It is not a proof of global kappa optimality, nor a silent claim about a
different tariff after discarding the fallback. Repeating normal7 caps on
the unchanged certified graph has no demonstrated useful premise.

The representative receipt
`results/CONTINUATION-05/R2-B-RESTORE/v1/reference/task-00000.json.gz` has
SHA256 `cfaafc9809cf5ffffe7f1b00f96546eb1458dab86aa65af8ade9650b01e8e5ca`.
The CONT06 checkpoint at16:58 records no newly released changed-word lead or
active same-quartet construction within its stated recent-PR/four-thread
coverage; that metadata is not evidence of absence outside its coverage.
