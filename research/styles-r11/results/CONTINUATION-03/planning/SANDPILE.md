**Sandpile proposal: exact closure after a changed scalar word**

Planning only, 2026-10-16. No scientific preparation, candidate search, control,
native replay or new cap evaluation was executed for this note. Source heads,
the finite domain, resource limits and decision rules must be frozen separately
before execution. The old r11 stops and receipts remain unchanged.

The useful exact structure is an abelian family of frame-cap closure maps on a
fixed feasible-labeling lattice. This is stronger than an analogy: its maps
commute by an elementary greatest-element argument below. It is not a
state-independent Laplacian on rank heights, and it does not optimize the
concave child cost. To seek a competitive improvement, change the scalar-word
constraint graph by a legal production, then use collective closure as a
feasibility operation and certify the complete cost. A generic repeat of
single-gate lowering, fill overflow repair, or ordinary fan retiming is not the
proposed experiment.

**What the preserved experiments establish.**

The [M2 review](../../M2/C-EXACTNESS.md) reports that every one of the 600 S-2
orders reached an individually verified maximal terminal worse than a feasible
reference. Each word had only one observed terminal assignment, identical
across seeds. Thus S-2 rejects the registered strict-single-lowering optimality
criterion; it does not demonstrate nonconfluence. It did not test neutral
moves, collective closures, or a different scalar-word graph.

S-6 checked a divisible-cell relaxation and contiguous call intervals. All
2,219,112 cells flowed, and none of the 222,111 intervals was binding; the
smallest slack was 18,172. Family exclusion and indivisible role sizes were
relaxed. Its NULL does not prove that an exact allocation is insensitive to
width edits, and it supplies no forced-rank-one conclusion. S-4/S-5 were
stopped, not experimentally rejected.

One mathematical correction to [PLAN section 4](../../../PLAN.md) is necessary:
acyclicity alone does not make a sandpile group trivial. Consider vertices
v,w,s, with s a sink and arcs v→w, v→s, w→s. Under the column convention the
reduced toppling matrix is

```
L = [[ 2, 0],
     [-1, 1]].
```

Its determinant is 2, and the quotient is Z/2Z. No parallel edge is needed;
the still smaller example with two parallel v→s arcs also has matrix [2].
The objection for these fills is the missing physically justified toppling
rule, not the DAG alone. Sandpile recurrent states and their algebra concern
specified toppling operators. [Dhar, 1990](https://doi.org/10.1103/PhysRevLett.64.1613)
and [Bond–Levine, part III](https://arxiv.org/abs/1409.0170) provide the relevant
theory; neither assigns such operators to an arbitrary eligibility graph.

**Exact states and the obstruction to a height-only fill Laplacian.**

An exact fill state must retain every role (call,helper), its indivisible width,
its owner/child/port assignment, and a compact offset. A legal assignment obeys
the fixed time window, per-call physical-family injectivity, capacity,
nonoverlap and complete role inventory. Residual heights alone discard
information that determines legality. The implementation is
[fill.py](../../../pipeline/fill.py), with exact two-role guards in
[cross_call.py](../../../pipeline/continuation/cross_call.py).

A source-neutral counterexample uses three bins A,B,C of capacity 8, all
eligible at the two calls, and three width-4 roles. In state X, call 1 has
x in A and y in B, while call 2 has z in C. In state Y, exchange y and z:
call 1 has x in A and y in C, while call 2 has z in B. Both states have the
same residual vector (4,4,4). Moving x from A to B is capacity-feasible in
both, but violates call 1's family injectivity only in X. Additional fixed
roles may be added without changing this example. This is a counterexample
under the exact rule schema, not an assertion that this particular triple
has already been found in a pinned fill.

The full assignment can instead be encoded as a resource/transition system:
places record a role's current bin, free cells, and available per-call family
tokens. A move consumes one whole role, the required number of destination
cells and a destination family token; it returns the source cells and source
family token. This yields an exact integer incidence matrix for *specified*
role moves. Conflicting transitions are generally noncommuting. That matrix
is not a sandpile Laplacian, and introducing it is not a discovery of an
intrinsic sandpile group.

For a fixed complete local profile and total residual mass, the objective at
an exponent a in (0,1) is the sum of
f_a(r)=(r/m)^(1-a), with f_a(0)=0. Concavity favors concentration of residual
mass. A two-bin exchange has an exact majorization certificate when it makes
the two residuals more unequal. For three or more bins, an increase in the
sum of squared residuals alone is insufficient; check all majorization
partial sums or the exact moment interval. A divisible sandpile distributes
excess according to its selected graph, so its stabilization theorem supplies
no minimization theorem for this objective.
[Levine–Peres](https://arxiv.org/abs/0704.0688) define and analyze that distinct
divisible process. A sink that silently deletes rank mass is also invalid:
the actual fixed coverage deficit must remain in the full bill.

**The exact collective closure law.**

Fix one complete scalar word, its split-at-warp constraint graph, every
entrance/end frame, centre/cut pin and warp interface. Let F be the finite set
of feasible frame labelings between the propagated lower and upper labels
L and U. On this graph the constraints are inclusions and fixed linear
isomorphisms/pins, so F is closed under pointwise subspace join and meet.
This hypothesis must be checked for any adapter with additional constraints;
meet closure alone is not enough for the following existence argument.

For a finite list C of vertex caps (v,C_v), define K_C(X) to be the greatest
Y in F satisfying Y≤X and Y_v⊆C_v for every cap. Feasibility is equivalent
to L_v⊆C_v for all caps. Join closure implies the greatest element exists:
join all feasible capped labelings. Starting from X, intersect at capped
vertices and propagate the resulting upper restrictions backwards through
inclusion edges and through the inverse of any retained isomorphism. Reject
if a propagated cap excludes the independently attained floor. On the
split/pinned graph this computes K_C(X). Each nontrivial propagation lowers
the finite sum of frame dimensions, proving termination.

For two fixed feasible cap lists C,D on this **same graph**,

```
K_C K_D = K_D K_C = K_(C union D),       K_C K_C = K_C.
```

Proof: K_D(K_C(X)) satisfies both lists and lies below X. Any feasible Z≤X
satisfying both first lies below K_C(X), then below K_D(K_C(X)). Hence the
composition is the greatest jointly capped labeling. Reverse the lists for
the other equality. This proves schedule independence for the fixed cap
set; it proves neither independence of which caps are selected nor optimality
of a rule that accepts only moment-decreasing caps. The maps are idempotent
and generally noninvertible; their algebra is a commuting closure semilattice,
not a recurrent sandpile group.

There is also an exact message-passing formulation for these downward caps.
At vertex v, store the annihilator D_v=F_v-perp. An incoming cap adds its
annihilator by subspace sum; propagate each newly acquired nonzero vector to
every predecessor in the inclusion graph. Emit **every** new vector once,
not merely a selected basis: a basis-only output can depend on which facts
arrived first. The processor's final state is the span of its initial state
and all incoming constraints, and its total output on each edge is exactly
the set difference between its final and initial spans. Thus both state and
emitted-message multiset are independent of input order. A propagated span
outside L_v-perp certifies infeasibility. This is the local commutation
criterion of [Bond–Levine, part I](https://arxiv.org/abs/1309.3445), not a
claim that those messages are paid rank units. These processors are
saturating, not locally irreducible, so the production-matrix criterion for
finite irreducible networks in [part II](https://arxiv.org/abs/1409.0169)
cannot be imported without its hypotheses. Halting here follows directly
from the finite number of facts.

A fixed rank-height Laplacian still fails in general. Take a two-vertex
chain F1⊆F2 in span(e1,e2), with cap C2=span(e1). The two feasible states
(span(e2),span(e1,e2)) and (span(e1),span(e1,e2)) have the same dimensions
(1,2). The cap lowers dimensions respectively by (1,1) and (0,1). Thus the
same operation at the same height state has different effects depending on
subspace geometry. Any claim of a smaller invariant linear toppling model
must state a restricted invariant family and prove closure of that family.

**A cost-bearing production followed by closure.**

The current source may already have a certified fixed-order optimum. Its
certificate is not invalidated by calling a collective closure a toppling.
The useful hypothesis change is an exact scalar production which changes the
constraint graph, followed by fresh frame optimization/closure on that graph.
All start/end frames and role identities can stay fixed, so rank mass and
the owner fill may be retained even though the paid partition changes.

For elementary scalar matrices E_ij(a)=I+a e_i e_j^T with distinct i,j,k,
the exact matrix identity

```
E_ij(a) E_jk(b) = E_jk(b) E_ik(ab) E_ij(a)
```

provides a 2↔3 production. Matrix order must be translated explicitly into
the raw gate execution order. With all frames equal this normally changes
only the finite primitive count; a recursive-cost gain requires the changed
graph to admit a better paid partition. Dyadic coefficients, frame
compatibility and the entire finite primitive invoice remain mandatory.

For a two-shear block E and an intervening rank-one transvection G=I+cuv^T,
the exact transport identity is

```
E^(-1) G E = I + c (E^(-1)u) (v^T E).
```

This is a potential bounded interaction family, not a proved profitable
production. The transported operator may require more elementary gates and
may fail common-frame or dyadic-factorization guards. Inspecting two shears
together can reveal cancellations unavailable to either single transport.
Any common cap set is applied only after the full resulting scalar word is
fixed; closure maps from different graphs are not asserted to commute.

Every accepted replacement must preserve the full formal operator on
arbitrary dirty inputs, including all free warp symbols. A whole-word
endpoint equality does not imply that its intermediate non-target transfer
matrix M or compensation map C is unchanged. If a paired extraction is
subsequently reused, derive its eight identities on the changed M,C again.
Regenerate compensation and cleanup; do not import fetched producer code.
Do not cross a cut, warp, protected prelude or restored endpoint unless that
boundary is expressly included and proved in the registered identity.

If ordered helper widths and dispatch are unchanged, the existing owner
assignment and offsets remain combinatorially feasible. Its idle profile is
unchanged. The complete-profile change is exactly the dispatch-weighted sum
of the local-profile changes. At the current certified endpoint a0, a strict
negative exact moment delta then proves a supplier-profile improvement;
native scalar/frame, phase, wrapper, dirty restoration and full physical/
outer admission remain separate required gates. Local changes may affect
internal data frames even when the external ports and outer controller are
unchanged, so old native word hashes cannot be silently reused.

**Finite registration and falsification.**

The next registration should freeze a named source word pair, its original
middle/restore gate IDs, the exact two-shear or 2↔3 production templates,
coefficient bounds, section boundaries, protected registers, deterministic
ordering, task and family budgets, and the full deduplication rule. A count
of every eligible/rejected/retained candidate is required. Restricting to
disjoint gates is not useful for a paid-partition search: their per-register
chains are unchanged. Conversely, noncommuting operators cannot be retimed
without the explicit correction factors above.

First prove each finite operator identity on exact rational/free-operator
matrices. Then rebuild the changed graph, check the complete lower/upper
feasibility and cap-closure equations, and derive the full profile. Use an
available certified fixed-order optimizer as the cost reference, not greedy
lowering. Keep exact rational moment intervals; unresolved signs are
EXPLORATORY. Only a candidate with certified gain advances to fresh native
and physical admission. The current literal fill is retained only after the
unchanged-width/interface claims have been checked.

Controls should include the unchanged word; a deliberately wrong correction
coefficient; an omitted compensation term; a cap that excludes a fixed floor;
an illegally crossed warp/cut; and a missing finite primitive/buffer charge.
For closure, test cap-list reversal and several schedules on the same graph,
comparing actual frame labels and profiles rather than dimensions alone.
These finite tests audit the implementation of the theorem; they do not turn
an independently proved algebraic identity into a statistical pattern claim.
All parallel jobs use the root-controlled pool with source pins, two seeds,
timeouts and projected memory. A complete zero-gain census is a NULL only
for its specified productions/bounds; failed controls or missing coverage
are not NULLs. The old S-2/S-6 stop is not retroactively revised.

**Live overlap restrictions supplied by the coordinator.**

The refreshed source review reports that PR2957 covers generic retiming,
preload, carrier and A-phase commuting-swap/refit edits. The coordinator also
identified Discussion2612 comments18975387 and18975555 as active composition
work involving PR2942's four paired extractions and the added 41 restore /
122 input gates, including codimension-two work. Those direct families are
excluded here. The possible distinct question is a bounded simultaneous
two-shear/conjugation or 2↔3 identity on the **original** middle/restore of
the refreshed source, with all PR2942-added gates excluded. PR2952's reported
single-terminal-shear obstruction is a reason to distinguish simultaneous
changed-operator blocks; it is not evidence that the larger family succeeds.
These are coordinator-supplied overlap findings, not an independent claim of
exhaustive external coverage. Freeze the final source and recheck overlap
before execution.

This note supplies an exact closure law, an explicit obstruction to a
height-only Laplacian, and a falsifiable changed-word route. It claims no new
method, intrinsic sandpile group, profitable candidate, or kappa improvement.
