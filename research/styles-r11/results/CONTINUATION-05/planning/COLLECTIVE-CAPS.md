# A cost-bearing closed-set refit after a changed scalar production

Planning and proof only. No candidate enumeration, source preparation, control,
flow, frame optimizer, moment test, or admission was executed for this note.
All earlier stopped protocols and their exact null scopes remain unchanged.
This is not a proposal to repeat CONT04's closed adjacent-expansion family.

The coordinator has now authenticated the public L27R source, PR2979 by
Marius-Paul Dumitrean, head `be191346391661f4d35fc0d1508d0a6029572576`, at
`data/continuation-05/pr2979/package`. The proposed scalar production is owned
by the other proof/implementation lane: re-pair the B-side normal-7 pivots
363/73 or 395/5 so that output restoration can use free carriers, with the
corresponding exact input-side change. Those addresses and the production are
coordinator-supplied hypotheses, not validated candidates in this note. Their
complete dirty operator identity must be established before this refit stage
is eligible. The active Hall/cost-neutral swap audit and the previously closed
endpoint-lowering/expansion families are excluded.

The proposed contribution is an exact optimization of a restricted collective
frame move on the resulting **changed** scalar graph. It couples arbitrarily
many internal gate frames while keeping that graph's declared external and
private-buffer endpoints fixed. It can be priced and certified by a cut
problem. It does not identify a physical sandpile Laplacian.

## 1. Existing optimization coverage is a necessary gate

For a fixed scalar word, a certified global optimum over all feasible frame
assignments already covers every cap move described below. Calling the move a
toppling does not evade that certificate. The trusted toolkit explicitly
documents `optimal_frames` as an optimum of its **integer surrogate**, with a
separate rigorous true-moment interval when requested. Surrogate certification
alone is not a proof of exact true-cost optimality. The exact objective,
endpoint, fallback charges, admissible frame domains and interval gap must be
compared before claiming either coverage or a remaining opportunity.

The inspected PR2966 producer and declared rewrite source replay literal frame
edits and recount their profiles; that observation alone is not a global
optimality certificate. Conversely, absence of a certificate in those few
files is not evidence of a profitable refit. The current coordinator scope
requires a genuinely different legal production on PR2979 first. An unchanged
word will not be searched merely because a certificate was not located.

CONT03's cap-closure PASS proved feasibility and schedule independence, not
cost optimization. S-2's strict single-lowering null did not test the collective
objective here. CONT04's two nulls cover all three placements and all frame
choices at fixed literal exterior contacts for its adjacent expansion; that
family remains closed. A distinct B-side paired production changes the scalar
graph and its constraints, which is the material premise change required here.

## 2. Exact state and legal one-bit frame choices

Input a fresh scalar graph and a **feasible** complete frame labeling F. Each
vertex has its actual F2 subspace, with a shared frame for the two operands of
a scalar add. Register-chain edges u->v require `F_u subset F_v`. Warp lives
are split into virtual registers, and start/end, centre/cut and warp entrance
constraints retain their exact equality semantics. All fixed vertices remain
fixed. If an upstream production changes an authorized endpoint, that new
endpoint belongs to this fresh input contract; the cap stage does not change it
again.

Choose one nonzero ambient normal h and its hyperplane `H=ker(h)`. The variable
vertices have only two permitted labels:

```text
F'_v = F_v                  if x_v=0;
F'_v = F_v intersect H      if x_v=1.
```

If F_v is already contained in H, these are identical and there is no variable.
Otherwise intersection loses exactly one rank. For every affected edge u->v,
the predecessor is either also affected or already contained in H. The case
"affected predecessor, H-contained successor" is impossible by original
inclusion.

When both ends are affected, the lowered labels are feasible exactly when

```text
x_v <= x_u.
```

Indeed, lowering v while leaving an H-exterior vector in u would break
inclusion. The other three states preserve inclusion. Therefore the selected
vertices form a predecessor-closed subset of the affected graph. A fixed
H-exterior vertex is forced to x=0; its closure constraints may forbid lowering
downstream vertices. An explicit fixed floor L_v also forbids x_v=1 unless
`L_v subset F_v intersect H`.

An exact equality edge needs `x_u=x_v` when its equal original frames are
affected. In particular, equality to a fixed cut or warp entrance forces the
last mutable frame to remain unchanged. Merely preserving inclusion is not
enough. A lower-dimensional replacement outside the original F_v is outside
this family and must be rejected, even if its rank agrees.

## 3. The complete cost is an exact cut objective

Let g(d) be the complete registered charge of one positive rank-d child, and
g(0)=0. The ordinary local moment uses `g(d)=(d/m)^(1-k)`. A registered common
positive per-child fallback charge can also be included in g, provided its
increments are rigorously positive. The cut representation needs monotonicity
of g; concavity explains why useful concentration can occur, but is not needed
to derive the network.

For an original chain edge u->v let `d=dim(F_v)-dim(F_u)`.

* If both ends are affected, the new rank is `d+x_u-x_v`. Legal states are
  (0,0), (1,0), (1,1). Only (1,0) changes the cost, by the positive amount
  `c_uv = g(d+1)-g(d)`.
* If u is contained in H and v is affected, the new rank is `d-x_v`. Selecting
  v changes the cost by `b_uv = g(d-1)-g(d) < 0`. Here d>=1, so no negative
  rank is evaluated.
* If both ends are contained in H, the edge does not change. An affected fixed
  endpoint is represented with x=0, not removed from its incident cost terms.

Sum the second kind of contribution into b_v. The exact complete affected
profile change is therefore priced by

```text
Delta(x) = sum_v b_v*x_v
         + sum_(u,v both affected) c_uv*x_u*(1-x_v),
subject to predecessor closure, fixed vertices, and equality constraints.
```

Parallel register-chain edges must remain separate or carry their exact
multiplicity. Every first unchanged successor and final climb is included.
Fixed centre descents and all unaffected edges cancel exactly. This is the
full canonical paid profile change, not a count of changed vertices.

Build an s-t cut network with x=1 on the source side:

* Add source->v with capacity `-b_v` when b_v<0.
* For every affected edge, add u->v with finite capacity c_uv and v->u with a
  hard capacity enforcing closure.
* Force x=0 by a hard v->sink arc for fixed/prohibited vertices.
* Add the opposite hard direction when an equality interface requires it.

The cut capacity is `sum_v(-b_v)+Delta(x)`. Choose a finite hard capacity
strictly larger than the sum of all finite capacities; then no minimum cut
uses a hard arc because the empty selected set is feasible. Thus a minimum
cut is an exact minimizer over **every** simultaneous cap selection for this
fixed F,H. It is not a sequence of locally accepted single-node edits.

Along each register chain, the change in rank on an edge is the difference
between its endpoints' one-bit dimension losses. The sum telescopes to zero
because its physical or split-warp endpoints are fixed. Hence full rank mass,
ordered role widths, and the declared physical inventory remain unchanged.
No sink removes unpaid rank mass.

## 4. Exact certificate rather than a numerical surrogate decision

A practical exact-capacity implementation may represent each capacity and
flow as an integer coefficient vector in the at most nine child costs
`g(1),...,g(9)`. Addition and subtraction are exact vector operations. Compare
two expressions using outward rational child-cost intervals; a zero coefficient
vector is exactly zero. A nonzero expression whose interval still straddles
zero is unresolved and must halt that task as EXPLORATORY. It must not be
rounded into a sign or silently treated as equal.

A deterministic Dinic implementation can use this comparison oracle to select
bottlenecks and discover positive residual arcs. Its final certificate includes
every capacity and flow coefficient vector and the source-side vertex set.
An independent verifier checks flow conservation by exact vector equality,
nonnegative flows and residual capacities by rigorous sign bounds, no residual
source-to-sink path, all closure/equality constraints, and equality of the flow
value and cut capacity. It then checks

```text
cut capacity - sum(source prizes)
  = sum_rank (candidate_count - source_count) * g(rank)
```

by exact coefficient equality after an independent canonical whole-word
profile extraction. Symbolic flow/cut equality plus validated capacities is a
true objective certificate; it is not an integer-surrogate optimum being
promoted to true-cost optimality.

For a numerical-flow proposal engine, a safe weaker alternative is a
downward-rounded integer lower objective, followed by an independent exact
candidate bill. That can prove a profitable witness. If its global lower bound
is negative but the concrete candidate has no certified gain, it cannot prove
a null and remains EXPLORATORY. The symbolic certificate is preferable when
finite exhaustive null decisions are required.

## 5. The legitimate abelian component and its limits

For fixed F and H, selecting a cap at v sends the single fact "intersect with
H" to every affected predecessor. Each vertex stores one bit and emits this
fact along each predecessor edge at most once when its bit changes from zero
to one. Duplicate messages have no effect. The final selected set is exactly
the predecessor closure of the initial selections, independent of delivery
order; the emitted edge-message multiset is also fixed. Invalid fixed-floor or
equality contacts reject the selection.

This is a saturating abelian processor on an explicitly restricted state
space. The cut problem chooses the whole closed set with its actual cost.
It does not prove that an arbitrary moment-decreasing local policy stabilizes
optimally. Applying this optimization repeatedly with different H changes the
state-dependent cost network; the selected sets and resulting optima need not
commute. Such iterations are outside a one-pass registration unless explicitly
included before observing outcomes.

The capacity graph depends on the literal F, the chosen H, exact rank gaps and
the declared word. It is not a state-independent intrinsic physical Laplacian,
and its source/sink capacities are an optimization construction, not physical
loss or creation of recursive mass. Nothing here creates a sandpile recurrent
group or burning identity.

## 6. A strict collective-gain control

Use two scalar gates on pairs (a,b) then (b,c). Give both gates the same
rank-two frame F. All three entries are zero; all three fixed exits have rank
four. Choose H with `dim(F intersect H)=1`. Initially there are six rank-two
climbs, so the bill is `6*g(2)`.

Lowering only the first gate gives `3*g(1)+3*g(2)+g(3)`. Relative to the
baseline its cost is `3*g(1)-3*g(2)+g(3)`, strictly positive for the power tariff
with exponent in (0,1): it is the positive third forward difference of that
power at zero. Lowering only the second gate is infeasible because the shared
register would descend from rank two to rank one.

Lowering both gates gives `3*g(1)+3*g(3)`, with change
`3*(g(1)-2*g(2)+g(3))<0` by strict concavity. All six boundary frames on the three registers are fixed
and the rank mass is twelve throughout. Thus the exact closed-set operation
can improve where strict single-node descent stops. This is a control fixture,
not a claim about PR2979, and a full fixed-DAG optimizer would already cover
it. The scalar operations and dirty linear map themselves are unchanged.

Negative controls should isolate: a missing predecessor closure arc; omission
of a successor/end cost; a cut or warp equality relaxed to inclusion; a cap
excluding a fixed floor; a same-rank wrong-orientation frame; a forged
flow/cut equality; a nonzero interval-straddling expression treated as zero;
and an omitted cleanup or paid child in the materialized word. Compare at
least two cap-message schedules and independent task seeds, while preserving
the actual frame assignments and cost certificate, not just their ranks.

## 7. Executable boundary and finite falsifier to register

Suggested interface, contingent on coordinator approval and a separate frozen
implementation:

```text
prepare_graph(raw, attribution, fixed_interface_signature)
  -> parent-only canonical word and fresh literal split graph,
     source/candidate operator pins, complete profile and inventory,
     equality/floor/fixed-node sets, exact cost interval table;

hyperplane_task({normal, seed, internal_cpu_limit})
  -> status, selected closed vertex set, literal frame edits,
     full profile delta and rank-mass proof, flow/cut certificate,
     unchanged endpoint/width/buffer signature, elapsed resources;

materialize(verified_cap_result)
  -> complete literal word with canonical cleanup and source attribution.
```

The producer must first provide an exact, source-bound scalar identity and a
feasible starting labeling. An unsupported fresh geometry is EXPLORATORY,
not an infeasible-word null. If the producer needs interface changes, register
and audit them upstream; this module cannot silently lower an endpoint or
allocate a buffer.

The coordinator has selected **only normal 7** for the initial R1 production
family, after a fresh certified integer-surrogate full-DAG frame fit. The
proposed ten-normal alphabet and the possible all-511 census are not part of
that registration. Because the named pivots' frames already lie in ker(7),
this cap may be locally vacuous. After a certified global surrogate fit, any
additional cap gain can arise only through the difference between that
surrogate and the registered true tariff (or a difference in their explicitly
declared domains/objectives). The changed scalar word/DAG is the actual
improvement route; the cap stage is a restricted collective correction and
certificate, not a second independent optimum claim.

R1 proposes 96 scalar contexts per provider, two providers and two seeds, or
384 price tasks. A 14,400 CPU-second round budget permits 37.5 CPU seconds per
task on average before controls and other overhead; it does not permit every
task to use its timeout. This is a budget allowance, not a measured runtime.
One normal builds O(V+E) arcs with coefficient vectors of length at most ten,
followed by exact max-flow. A small constant runtime is not established by
source inspection. Project memory from the actual graph before launch, load
heavy source words once in the parent, and retain the 300-second hard task
timeout with shorter stage guards. Record incomplete tasks without trimming
the registered domain or inferring a null.

To respect the remaining artifact budget, verify the full flow/cut witness in
memory for every completed task but return a compact checked summary: source
graph hash, capacity/flow hash, exact value/cut/objective coefficient vectors,
selected graph nodes, arc count and verification status. Retain the complete
already-verified witness only for favorable nominees, without rerunning the
search. The input labeling, normal, deterministic graph construction and
source hashes bind the omitted repeated capacity data.

A candidate advances only if the independently materialized complete moment
has a strict favorable bound at the freshest admitted comparator and all
local operator/cleanup checks pass. A complete null requires exact flow/cut
certificates proving no favorable selected set for every registered normal
on every registered changed word, both seeds agreeing and no unresolved sign,
missing domain or timeout. That null concerns only one hyperplane per fixed
starting labeling. It does not cover compositions of hyperplanes, changed
productions, arbitrary frame replacements or another source.

No standalone closure PASS is a research goal. If the scalar-production stage
finds no legal distinct changed word, this stage remains unrun. If its full
bill or native interface cannot beat the current source, stop before extending
the cap search. A useful positive output must retain a concrete complete word,
not merely a favorable graph statistic.

## 8. Native and physical admission remain concrete obligations

Internal re-framing changes the native realization even when the scalar word
and its external contract are unchanged. Materialize all affected frames,
derive the BORROW cleanup exactly, preserve compensation only under its proved
operator contract, and run all independent forward/dual dirty columns. Check
the new frame transports and phase/Clifford/Gaussian realization and recompute
primitive, prefix/block-norm and rounding invoices. Existing source hashes
cannot be rebound to changed word bytes.

If ordered endpoints and widths are unchanged, the existing allocation may
be retained only after fresh literal role/window/family/capacity/offset and
complete local-plus-idle accounting. If the upstream paired production changes
inventory or private buffers, the actual refill and all corresponding charges
are mandatory. Finally compare the complete moment and strict supplier/outer
inequalities with PR2979 and the fresh external checkpoint. A local cap gain
on an older or incomplete comparator is not a current kappa improvement.

Credit the exact PR2979 source and all inherited PINS/notices, the classical
closure/min-cut construction, the trusted frame-optimization and BORROW
adapters, and the prior cap-closure proof. No empirical gain or general
optimality claim is made in this planning note.
