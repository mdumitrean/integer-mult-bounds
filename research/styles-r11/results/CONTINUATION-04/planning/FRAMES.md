# Fixed exterior frames for the registered adjacent expansion

This is a source-level proof and implementation review for E1, not an executed
experiment or an admission of a changed supplier. E1 is frozen in
[`../E1/PREREGISTRATION.json`](../E1/PREREGISTRATION.json), SHA256
`1b9d4a5179e3a76f0cd2d5347c8143a89b08e1e8e2284881ae13f5f39c5ef253`.
No result follows from a planning document.

The input is Jeremy Kothe's PR2966, head
`e62d3eb9005117d82a9babcfa937ecc53237c490`, base and extra complex words. All
inherited source credits and PINS remain applicable. The registered change is
internal: every helper's initial and final frame, ordered width, caller port,
centre, cut, prelude, and all 86 private buffer endpoints stay fixed. This is
distinct from changing helper endpoints or adding an extraction buffer.

This mechanism and its fixed-contact analysis have direct prior work. CubeJerry's
[PR1533](https://github.com/CrocSwap/integer-mult-bounds/pull/1533), head
`992119779c195d861e3ad203f024551438af48bd`, studied all three corrective positions
on the older PR589 bit word and proved no gain in that domain. Its report also
contains the positive boundary fixture used below. The exact saved primary
[README](../../../data/continuation-04/checkpoint/pr1533/README.md) has SHA256
`850ef3c60cb58f1ded3b49884b0a58d53c1733f7d274423022c7c67f70b42e1d`;
the adjacent PINS and
[`PRIOR-EXPANSION-SCOPES.json`](../../../data/continuation-04/checkpoint/PRIOR-EXPANSION-SCOPES.json)
retain its author, head and scope. The current question concerns a different
source word and complex tariff. No priority claim is made for the scalar
identity, flag reduction, or positive fixture.

## 1. Two execution-order identities

Let `i,j,k` be three distinct registers and `a,b` nonzero dyadic rationals. Write

```text
A: i += a*j
B: j += b*k.
```

Execution order is left to right. The two registered rewrites are

```text
old A,B  ->  new B,A,C, where C: i += (-a*b)*k;
old B,A  ->  new A,B,C, where C: i += (+a*b)*k.
```

For the first identity, executing B before A adds an unwanted `a*b*k` to i;
the last correction removes it. For the second identity, executing A first
omits that term; the last correction supplies it. These are identities on
arbitrary initial contents, including arbitrary dirty helper contents. They
also imply equality of the inverse-transpose operators. The implementation
checks forward and inverse-transpose matrices independently using exact
rational arithmetic, rather than trusting the recognizer's sign.

The correction is always last in E1. The family includes adjacent pairs in A
after its fixed prelude, in B without an intervening warp, and in restore.
None of the three registers may lie in the target interval `[v,2*v)`. No
scalar operation is moved through a cut, a warp, a prelude boundary, another
exterior gate, or a section boundary. A and B may not be replaced solely on
the basis of an equal-rank frame: the actual subspace containment predicates
below are mandatory.

## 2. Exact fixed exterior contacts

For each touched register r, let `E_r` be its frame immediately before the
old pair's first touch of r. Let `O_r` be its first fixed frame constraint
after the old pair's last touch of r. This is a literal exterior contact,
not a whole-word optimized upper bound. All outside gate frames remain fixed.

The trusted `borrow_price.build_problem` adapter splits each lender life at
every warp. Its virtual register before a warp ends at the required entrance
frame; the successor life starts at the warp's declared output frame. Use
these aliases when locating contacts. Both old occurrences of the shared
register j must have the same virtual alias. The precise extraction is:

1. Map each raw A index through `meta['A_idx']`; B and restore indices are
   direct. Map raw operands to virtual operands using the same gate node.
2. For each raw register, find its first and last node in the selected pair.
   Read the predecessor of the first and successor of the last on that
   virtual register's chain. Both must be exterior nodes.
3. Save their actual canonical frames, source positions and virtual aliases.
   If the successor is the A cut equality, or an end node for a virtual
   register in `meta['eq_end']`, mark the exit as an exact equality.

The graph here is a literal-chain accounting device. Building it does not
request mutable frame domains, a solver, or a global refit. Its complete edge
profile plus the separately fixed centre descents must equal the canonical
`WordData.paid` profile before any candidate is evaluated.

An ordinary successor permits a paid climb from the last new frame to O_r.
A cut/warp entrance equality does not permit inventing such a climb: the last
new frame must equal O_r. An ordinary final endpoint permits its canonical
paid final climb. At a B edit beginning at p, an old warp at p stays before the
window, a warp at p+1 makes the pair ineligible, and every old warp at p+2 or
later is shifted by one. Relative warp ordering is preserved.

## 3. Flag geometry and both tariff formulas

Let `R,S,T` be the new first, second and final correction frames. Successive
triangle gates share a register, so every legal schedule has `R <= S <= T`.
Here `<=` denotes subspace inclusion, join means linear span, and meet means
intersection of full subspaces, not intersection of listed basis vectors.

For old AB, the new first gate is B and

```text
L1 = E_j join E_k.
```

For old BA, the new first gate is A and

```text
L1 = E_i join E_j.
```

In both orientations,

```text
L2 = E_i join E_j join E_k;
U2 = O_i meet O_j meet O_k;
U3 = O_i meet O_k.
```

Both orientations finish with frame T on i and k and frame S on j. A legal
schedule therefore requires

```text
L1 <= R <= S <= T <= U3;
L2 <= S <= U2.
```

Ignoring the additional exact exit equalities for a moment, a schedule exists
if and only if `L2 <= U2`. This implies the nested flag
`L1 <= L2 <= U2 <= U3`. Put `l1=dim(L1)`, `l2=dim(L2)`, `u2=dim(U2)`,
`u3=dim(U3)`. Every feasible schedule has ranks

```text
l1 <= r <= s <= t <= u3;
l2 <= s <= u2.
```

Conversely, extend a basis successively along that flag and take its first
r,s,t basis vectors. This realizes every such integer triple over F2. Thus
orientation-dependent geometry is fully represented by the actual flag and
these rank inequalities; no sample of frame orientations is being substituted
for this proof.

Write `e_x=dim(E_x)` and `o_x=dim(O_x)`. For a common concave tariff f with
`f(0)=0`, the complete affected-chain cost of AB -> BAC is

```text
f(r-e_j) + f(r-e_k) + f(s-e_i)
+ f(s-r) + f(t-s) + f(t-r)
+ f(o_i-t) + f(o_j-s) + f(o_k-t).
```

The corresponding cost of BA -> ABC is

```text
f(r-e_i) + f(r-e_j) + f(s-e_k)
+ f(s-r) + f(t-r) + f(t-s)
+ f(o_i-t) + f(o_j-s) + f(o_k-t).
```

Every displayed argument is nonnegative for a feasible flag assignment.
Each positive argument contributes one paid child of that rank; a zero
argument contributes no child. The last line is essential: the first
unchanged successor's frame is fixed, but its incoming paid climb can change.
The original two-gate bill must use exactly the same entry and exit contacts.

On each register, the rank increments telescope. Therefore both bills have
the same mass

```text
sum_x (o_x-e_x), for x in {i,j,k}.
```

This mass identity is an independent exact guard. It is not an additional
assumption required for the minimization proof below.

## 4. Why eight corners suffice, including equality exits

Each tariff above is jointly concave in the real variables `(r,s,t)`: it is a
sum of a concave f evaluated on affine nonnegative arguments. For fixed s,t,
its minimum over `l1 <= r <= s` occurs at `r=l1` or `r=s`. Restrict to either
branch; the resulting function remains jointly concave. For fixed s, its
minimum over `s <= t <= u3` occurs at `t=s` or `t=u3`. On each of these four
branches the remaining concave function of s has a minimum at `s=l2` or
`s=u2`. All endpoints are integer ranks, so the argument also covers the
integer rank domain without rounding.

The eight explicit actual-frame assignments are therefore

```text
S in {L2,U2};
R in {L1,S};
T in {S,U3}.
```

They realize the eight rank corners directly. The registered implementation
retains all eight `(S,R,T)` labels, even when some labels give identical
frames, so coverage is auditable without an implicit deduplication rule.

Exact exit equalities do not create an unenumerated interior optimum:

- If j must equal O_j, then S=O_j. Feasibility implies O_j is contained in
  both O_i and O_k, so `U2=O_j`; the upper S corner supplies the required frame.
- If i must equal O_i, then T=O_i and feasibility implies O_i is contained in
  O_k. Thus `U3=O_i`; the upper T corner supplies it. The argument for k is
  identical. If both i and k require equality, feasibility requires O_i=O_k.

With either equality the corresponding variable is fixed at an already
enumerated upper endpoint. Minimizing the remaining variables uses the same
concavity argument. Every corner is still checked for inclusion and exact
equality. If all corners fail those guards, no schedule exists in this fixed
corrective-at-end boundary model. An infeasible flag is a geometric rejection,
not evidence about another order or another word.

For E1, `f(d)=(d/73)^(1-k)` and `0<k<1`, with k the exact preregistered source
endpoint. The common positive normalization does not affect concavity or the
minimizing ranks. A different uniform positive multiplier would likewise
not affect the theorem. No assumption that an internal forward edit costs
twice its canonical rank tariff is made. The proof does not minimize primitive
scalar instruction costs, native norm/rounding envelopes, another corrective
position, a changed exterior frame, or a joint multi-window edit.

## 5. BORROW cleanup, compensation, and complete accounting

The trusted `pipeline/wordio.py` extractor charges frame climbs in A, B and
restore, fixed centre descents, and each live register's final climb. It then
emits ordinary cleanup gates unframed. Consequently the recursive paid-profile
delta of this internal expansion is counted **once**, not twice. Regenerating
cleanup does not create another copy of its frame-climb profile.

There are nevertheless two additional scalar instructions in the complete
forward-plus-cleanup word: one added forward chord and its inverse cleanup
gate. That primitive work and its native error envelope must be charged in
any later admission. It must not be confused with a second recursive child
profile. PR1533 makes the same distinction in its full-word ADD count.

For BORROW, `derived_borrow_cleanup` records A after its prelude, B with its
warps in the declared order, and restore; removes writes to target registers;
then reverses and inverts those events at the full frame. Registers restored
into private buffers are mapped to the corresponding buffer identifiers.
After the candidate is constructed, derive this list again from the edited
word. Keeping the old literal cleanup would be invalid even though the scalar
window map is unchanged. The expanded word and its inverse have the same
exact operator on arbitrary contents, but their instruction lists differ.

The frozen prelude, compensation, target/centre cut and all physical endpoints
remain literal. Reusing compensation relies on the exact complete interval
operator identity on non-target registers and unchanged exterior interfaces;
it is not justified merely by matching a histogram. Independent full-column
forward and inverse-transpose audits are mandatory for the retained favorable
candidates. Their cleanup must pass the canonical literal production check,
and the missing-cleanup control must fail.

The complete canonical profile is the authoritative bill. For each constructed
corner, independently extract it and check

```text
new complete profile
  = old complete profile - old affected-chain profile + new affected-chain profile.
```

Check that no count becomes negative; complete rank mass is unchanged; ordered
helpers, widths, start/end frames and all 86 private buffer endpoints are
identical; centre descents are unchanged; and cleanup regeneration leaves the
canonical paid profile unchanged. The source's complete literal-chain bill
must already have passed the independent baseline parity check. These checks
detect a missing outside climb, a wrong virtual alias, a hidden warp boundary,
an accidentally changed paid centre descent, or stale profile metadata.

Preserving endpoint geometry and width inventory does not by itself certify
the changed word's native or outer caller contract. Changed internal scalar
operations and internal frames require fresh corresponding checks. Any gain
from E1 is only a local candidate until the changed-word native obligations,
complete supplier/fill bill, and outer admission all pass against the current
benchmark. No intrinsic sandpile Laplacian or abelian cost-descent claim is
made here.

## 6. Controls and source-review observations

For an explicit improving boundary fixture, take `R=0`, `S=span(1)`,
`T=span(1,2)` and the fixed exits `(O_i,O_j,O_k)=(T,S,T)`. For old AB choose
entries `(E_i,E_j,E_k)=(S,R,R)`; for old BA choose `(R,R,S)`. Give both original
gates frame S. The original bill is `{1:4}`. Assign the new gates frames R,S,T;
the new bill is `{1:2,2:1}`. Mass remains four, and the cost change is
`f(2)-2*f(1)<0` for the strictly concave power tariff. This is the known positive
boundary fixture credited to PR1533, not an asserted occurrence in PR2966.

Required negative cases include a wrong correction sign or magnitude, a
non-dyadic or zero coefficient, a repeated/target register, a hidden warp or
prelude crossing, a stale source window, an incoming line omitted from the new
frame, and a proper-subspace exit where exact cut/warp equality is required.
The equality mutant should pass inclusion while failing equality, so it tests
the additional condition rather than a weaker guard. A missing paid child and
missing cleanup instruction must fail the complete-word checks.

Read-only review of `pipeline/continuation04/expansions.py`, SHA256
`5f358c2084cd39f669758cd42c077dbb93726ef79bc8a2055d7ea1f17f7f7442`, found its two chain
orientations, virtual-alias contacts, eight corner labels, explicit equality
filter, affected-chain bill, whole canonical delta parity and B-warp shifts
consistent with these formulas and the frozen E1 scope. This statement is a
static review, not execution of its controls or source preparation. Root owns
implementation pinning, pool execution, both confirmation seeds, and all
scientific decision records.
