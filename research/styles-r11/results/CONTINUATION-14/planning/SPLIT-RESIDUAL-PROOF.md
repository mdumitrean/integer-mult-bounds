# Two ordered rank-two factors with separate residual-read frames

This is a static algebra and boundary-cost proof, written before the new
constructor is executed. It contains no source census, computed candidate,
solver result or tariff evaluation. The CONT08 F1, CONT11 J2 and CONT12
matched-frame R2 outcomes and their original stopping scopes remain unchanged.

The changed constraint is precise: the two reads into the residual target may
use different frames. This proof covers the carrier-first chain and its exact
time-reversed, orthogonal-complement chain, eighty labels in total. Both were
chosen before source execution. The scalar production is the same elementary
source-basis shear used in CONT12. These full five-frame classes were not the
matched-frame class tested there. No claim of an unsearched identity, priority,
physical Laplacian or new κ follows.

## Exact dirty-register identity

Let `u,v,j,k` be distinct active non-centre registers. The old four commuting
adds implement

```
u += a*j; u += b*k;
v += c*j; v += d*k.
```

All four coefficients are nonzero admissible dyadics. Require `a*d-b*c != 0`.
Put `q=b/a` and `e=d-c*q`; require the reduced denominators of `q` and `e` to
be powers of two. In particular, `e != 0`. The replacement is

```
j += q*k   @ X
u += a*j   @ Y
v += c*j   @ P
v += e*k   @ Q
j -= q*k   @ Z
```

After encoding, `j=j_old+q*k_old`. Thus u receives `a*j_old+b*k_old`, and v
receives `c*j_old+(c*q+e)*k_old=c*j_old+d*k_old`. The final subtraction restores
j; k is unchanged. This identity holds for arbitrary independent dirty input
values. The inverse-transpose identity follows from equality of the invertible
maps; the implementation must also check that orientation independently.

Either source may be the carrier and either target may supply the eliminated
row. These are four separately identified coefficient choices. Inadmissible
dyadic quotients are recorded exclusions, never rounded coefficients. This
family includes only the additional reverse chain proved below, not arbitrary
central-gate ordering, more consumers, changed interfaces, noncommuting context
conjugation or arbitrary word resynthesis.

## Complete boundary ledger

Let `E_r,O_r` be the actual fixed entry and first-successor frames of register
r after a permitted whole-window gather. A scalar gate's two operands must
share its frame. The chronological support pattern forces the full flag

`X ⊆ Y ⊆ P ⊆ Q ⊆ Z`.

Use lower-case letters for dimensions. Let `h(0)=0` and let h be increasing and
concave on the relevant nonnegative ranks. The exact fourteen-term bill is

```
j: h(x-ej)+h(y-x)+h(p-y)+h(z-p)+h(oj-z)
k: h(x-ek)+h(q-x)+h(z-q)+h(ok-z)
u: h(y-eu)+h(ou-y)
v: h(p-ev)+h(q-p)+h(ov-q).
```

Here lower-case q denotes the dimension of frame Q, not the scalar quotient.
The distinct k contact at Q and v climb P→Q are both charged. Every exterior
successor appears exactly once. At a cut/warp/end equality, the last actual
contact must equal the prescribed frame; an invented successor climb cannot
repair a failed equality. Both old and new bills have rank mass
`sum(dim O_r - dim E_r)`.

For the recursive comparisons the inherited exact tariff is a positive common
normalization of `r^α`, with `0<α<1`; implementation uses the frozen rational
child-cost enclosures. A symbolic profile difference is priced with signed
interval arithmetic. Native scalar work, coefficients, prefixes and cleanup
still require their own fresh admission. No scalar instruction is free merely
because the recursive child histogram improves.

## Forty actual-subspace labels contain the minimum

Define actual subspace joins and meets:

```
L  = Ej ∨ Ek              A1 = L ∨ Eu
A2 = A1 ∨ Ev             D  = Oj ∩ Ok
U2 = D ∩ Ov              U1 = U2 ∩ Ou
K  = A2 ∩ U1             J  = A2 ∨ U1.
```

The inclusion-only domain is nonempty exactly when `A1⊆U1` and `A2⊆U2`.
Together with the flag, its constraints are

```
L⊆X, A1⊆Y⊆U1, A2⊆P⊆Q⊆U2, Z⊆D.
```

For fixed X,Y,P,Q, the bill is concave in z. Its endpoints are realized by
`Z=Q` or `Z=D`. Substitute either choice. The resulting bill is concave in q
on `dim P ≤ q ≤ dim U2`, so choose `Q=P` or `Q=U2`. These endpoints are actual
feasible subspaces, not merely allowable ranks. For each resulting branch,
concavity in x permits `X=L` or `X=Y`.

The remaining pair `(Y,P)` has the same exact rank polygon as the earlier
two-target flag proof. Write `a1=dim A1`, `a2=dim A2`, `u1=dim U1`, `u2=dim U2`
and `k=dim K`. Its rank pairs are exactly

```
a1 ≤ y ≤ u1,  a2 ≤ p ≤ u2,  p-y ≥ a2-k.
```

Necessity follows because P contains both A2 and Y. For sufficiency, choose Y
inside K if `y≤k`; otherwise extend K inside U1. Then
`dim(Y∨A2)=a2+max(0,y-k)`, which can be extended inside U2 to the desired p.
The polygon's at most five vertices have these actual-subspace representatives:

```
(Y,P) = (A1,A2), (K,A2), (U1,J), (U1,U2), (A1,U2).
```

After the endpoint substitutions, every tariff argument is affine in y,p.
The remaining objective is concave, so one of these vertices minimizes it.
Combining the five pairs with the following choices gives forty labels:

```
20 matched labels: Q=P,  X∈{L,Y}, Z∈{P,D}
20 split labels:   Q=U2, X∈{L,Y}, Z∈{U2,D}.
```

Keep coincident labels under their registered identities. The first twenty
are exactly the matched-frame subclass; a new favorable split result must not
be attributed to rerunning the already closed subclass. The proof is complete
for this fixed gate order and fixed exterior, not for all source-basis words.

Equality exits preserve this finite optimizer. An equality on u forces
`Y=Ou=U1`, a right polygon face. An equality on v forces `Q=Ov=U2`; this is
already the split branch, or the matched top face `P=U2`. An equality on either
source forces `Z=D` when feasible. Filter actual subspace equality, including
simultaneous conditions; the retained vertices cover each nonempty face.

## Strict positive fixture beyond the matched class

Take coordinate-nested frames `0⊂S⊂T⊂U` with dimensions `0,2,4,5`. Let

```
u: entry S, exit S
v: entry S, exit T
j,k: entry 0, exit U.
```

Use the old interleaved word `u+=j; v+=j; u+=k; v-=k`, all at S. Its coefficient
matrix has entries `(1,1;1,-1)` and determinant `-2`. The carrier quotient is
1 and residual is -2, so all coefficients are nonzero admissible dyadics.
Its full boundary profile is `3H2+2H3`.

The split factor `X=0, Y=P=S, Q=T, Z=U` has full profile

`2H2 + H3 + H4 + H1`.

The difference is `H1+H4-H2-H3`, with zero rank mass. Strictly decreasing
increments of a strictly concave h give `h(4)-h(3)<h(2)-h(1)`, so the difference
is strictly negative. This comparison uses ordinary exits. The new labeling's
last contacts are S,T,U,U, but the old all-S word would not satisfy equalities
on v and the sources. It is therefore not an old-versus-new equality fixture.

For both source carriers and both anchor targets, the matched twenty-label
minimum on this fixture is the old profile. Its only distinct alternative
profiles are `3H2+H4+2H1` and `5H2+2H1`. Their excesses are respectively

`H4+2H1-2H3` and `2(H1+H2-H3)`.

The second is positive by strict subadditivity. The first is positive for the
actual power tariff: `f(α)=4^α+2-2·3^α` is strictly decreasing on `[0,1]`, since
`(4/3)^α log4 < 2log3` there, and `f(1)=0`. Therefore `f(α)>0` for `0<α<1`.
This matched-minimum comparison is power-specific; arbitrary concavity alone
does not establish that first inequality. Corner completeness above does hold
for general concave tariffs.

On these fixed boundary roles the strict split occurs with u as the first,
eliminated target. Swapping the anchor to v forces the two residual-read frames
inside S and need not give a strict gain. To check both anchor conventions with
positive fixtures, relabel the targets and their complete boundary records;
do not demand positivity for both anchors under the unchanged boundary roles.

This is a static fixture, not evidence of occurrence in PR3042 or a computed
source result. It supplies the earliest control falsifier: if exact all-corner
replay fails to preserve the operator, gives a different full profile, finds
a matched gain in this fixture, or misses the declared split gain, stop before
census.

## The reverse chain: forty more exact labels

Fix the same ambient F2 space for every complement. For original boundary
records E,O, define transformed records `E′=O⊥` and `O′=E⊥`. Factor the inverse
old matrix, whose coefficients are `-a,-b,-c,-d`. Its carrier quotient is still
q and its residual is -e. Apply the carrier-first forty-label optimizer to
these transformed records, then reverse and invert its five scalar gates and
complement each frame. The resulting original-forward word is exactly

```
j += q*k   @ Z′⊥
v += e*k   @ Q′⊥
v += c*j   @ P′⊥
u += a*j   @ Y′⊥
j -= q*k   @ X′⊥.
```

The transformed flag reverses to an increasing original flag. This is a
specific residual-first chain: its residual target has two reads before the
other target's read. It is not a claim to cover every interleaving of the three
central scalar operations. Negating the inverse coefficients before reversing
is essential; reversing a same-sign factor would implement the wrong map.

Every original increasing jump `A⊆B` becomes `B⊥⊆A⊥`, with equal rank increment
`dim A⊥-dim B⊥=dim B-dim A`. The full boundary bill is therefore preserved by
this bijection, including its first predecessor and last successor terms.
Forty labels suffice for the reverse chain because they suffice for its
transformed carrier-first chain. No new rank-only approximation is introduced.

Original exit equality flags must **not** be copied to transformed exits.
They become first-touch equalities in the transformed carrier-first word:

```
source j/k: X′ = E′j/k, forcing X′=L′ when feasible
target u:  Y′ = E′u,   forcing Y′=A1′ when feasible
target v:  P′ = E′v,   forcing P′=A2′ when feasible.
```

These are existing lower faces of the outer interval or middle rank polygon.
Their vertices are among the same forty labels, including simultaneous lower
face requirements. Clear transformed exit flags and filter candidates against
the original complete boundary bill. This preserves the minimum on every
nonempty original-equality face. Ordinary original entries remain ordinary
transformed exits. Exact equalities of subspaces, not ranks, remain required.

A separate strict reverse-chain fixture uses `0⊂S⊂T` of dimensions0,1,2:
u enters/exits S, v enters0/exits S, and both sources enter0/exit T. The same
matrix `(1,1;1,-1)` with all four old frames S costs `5H1`. The reverse factor
at frames `0,0,S,S,T` costs `3H1+H2`, a strict decrease `H2-2H1`. This is an
analytic fixture, not a source observation. Its original exits are ordinary;
equality controls are tested separately.

The union has eighty labeled choices per admissible carrier/anchor/placement:
forty carrier-first and forty reverse-chain labels. Duplicate physical words
remain separately addressable, and no outcome-dependent order selection or
post-result expansion is permitted.

Only the forward matched twenty labels are inherited CONT12 negative controls.
The reverse-chain labels with `P′=Q′` are a different chronological production,
so their old-frame equality is not evidence of prior coverage or neutrality.
For example, the reverse fixture also gains with both v reads at frame0,
followed by the u read at S and undo at T. A reverse matched gain is legitimate
new-order coverage and must not trigger an erroneous negative-control failure.

## Why the earlier ordinary-exit domination does not close this family

The CONT12 matched proof could undo at the common residual-read frame and then
perform the original two v reads there. When P<Q, undoing at P adds a k contact
at P before the surviving k read at Q. That splits the k jump X→Q into X→P and
P→Q. Concavity permits a strict increase, so the old domination step is no
longer cost-preserving. Undoing later can instead violate the intervening j
contact's frame. The complete fixture above makes the omitted saving explicit.

This does not prove irreducibility against every broader single-row exposure,
schedule or upstream shared-covector construction. The live broad reuse claim
must remain credited and its scope disclosed. The registered difference is
the separate residual-read frame and its complete charged optimization, not
an assertion that a rank-two matrix alone establishes non-overlap.

## Required implementation controls and scope

Before any source pricing, require the strict 5D fixture with both source
carriers and appropriately relabeled positive anchor conventions, plus matched
neutrality under all four fixed-fixture choices; independent forward and
inverse-transpose maps; a
small-space oracle over actual subspaces and all five independent nested gate
frames in each ordered chain; nonnested K/J fixtures; ordinary and equality
exits, including reversed first-touch equality faces; exact eighty-label
inventory; rejected equal-rank wrong subspaces; nondyadic quotient; missing
residual, wrong residual, omitted undo and omitted successor mutants. The
surviving k contact and P→Q target climb need separate invoice mutants.

Use the preregistered source-bound packet domain, exact permitted gathers and
unchanged exterior/context contract. Whole-window tariffs must equal complete
canonical word/profile differences after literal materialization and derived
cleanup. Two provider words, both seeds, all independent input columns and
both orientations remain mandatory. Source widths, endpoints, buffers and
allocation are fixed, but a local gain still requires fresh native, physical,
owner, complete moment and outer admission before any κ claim.

Other central-gate orderings remain possible future census targets, excluded
from these two chains and not priced here. No post-null widening is authorized
by this proof.

Credit the elementary factorizations and prior conditional constructions:
Jeremy Kothe/PR3015; CubeJerry/PR1533's scoped flag/concavity precedent;
Marius-Paul Dumitrean/PR2979; dcharb78/PR3042; Nick Petalas and Jeremy Diviney's
PR3054/3051 comparison releases; all original PINS and retained predecessor
credits. The immediate formal machinery is recorded in
`results/CONTINUATION-09/planning/JOINT-CARRIER-PROOF.md` and
`results/CONTINUATION-12/planning/RANK-TWO-CARRIER-PROPOSAL.md`.
