# Two coordinated carrier factors: exact fixed-boundary proof

This is independent algebraic planning, written before registration or execution of the continuation09 census. No source census, feature extraction, solver, cost evaluation, control or candidate audit was run to obtain it. Earlier single-factor NULLs and all prior stop scopes remain unchanged.

The scalar identity generalizes the carrier factoring directly realized in Jeremy Kothe's PR3015 R1. The fixed-boundary concavity/flag precedent is credited to CubeJerry's PR1533, with its original scope retained. The proposed test concerns a named current word and a precisely guarded four-gate packet; it does not claim an unsearched identity, an intrinsic physical Laplacian, or a general L-system pattern.

## Exact scalar productions, including both orientations

Let `i1,i2,j,k` be four distinct active registers, none a centre. All incoming values are independent and may be dirty. Let `a1,a2,b1,b2` be nonzero exact coefficients satisfying the common-ratio guard

`q = b1/a1 = b2/a2`.

For two same-target fans, the four old adds are

```
i1 += a1*j; i1 += b1*k;
i2 += a2*j; i2 += b2*k.
```

All four commute as scalar operators. For either middle-target order `(s,t)=(1,2)` or `(2,1)`, replace them with

```
j += q*k;
i_s += a_s*j;
i_t += a_t*j;
j -= q*k.
```

j is restored exactly, k is unchanged, and each target receives `a_l*j_original+b_l*k_original`. This proves the full dirty-input map, not a zero-buffer specialization.

The dual fan-out orientation starts with

```
j += a1*i1; k += b1*i1;
j += a2*i2; k += b2*i2
```

and replaces it with

```
k -= q*j;
j += a_s*i_s;
j += a_t*i_t;
k += q*j.
```

The sources i1 and i2 remain unchanged. The final j is its old value plus `a1*i1+a2*i2`; the subtraction and final addition give k exactly `b1*i1+b2*i2`. The preprocessing/undo signs therefore differ between the two orientations. The exact inverse-transpose identity follows from equality of the invertible full maps and should also be checked independently in controls.

The second carrier choice exchanges j and k and exchanges every a coefficient with the corresponding b coefficient, replacing q by `1/q`. A native dyadic grammar must test the reduced denominator of the chosen transport coefficient. q can be dyadic while `1/q` is not; for example q=3. Therefore eighty frame/order/carrier labels per packet require either both carriers to be admissible or explicit coefficient-guard dispositions for the inadmissible labels. Excluded orientations must be counted, never silently rounded or treated as losses.

## Exposure and fixed exterior

The four selected gates must occur inside one exact A/B barrier segment. Every other gate between the first and last selected gate must be disjoint from all four registers. Thus they may be commuted past the selected packet while preserving their own order and frames. Do not cross the A prelude boundary, any B warp gap, a cut, a section boundary or an alias split. A warp affecting a register touched by only one selected gate is still a barrier.

All predecessor and first successor frames are fixed. Let `E1,E2,Ej,Ek` be those entry frames and `O1,O2,Oj,Ok` the corresponding exit contacts or canonical endpoints. The following argument uses target order1,2; exchange indices1,2 and their entire boundary records for the other order. Both scalar orientations have the same chronological support pattern:

```
{j,k}, {i1,j}, {i2,j}, {j,k}.
```

Give these gates frames `X,Y1,Y2,Z`. Scalar coefficients and directions do not change their required common subspace supports.

## The complete twelve-jump bill

Write lower-case letters for frame dimensions, and `h(r)=(r/73)^p` for positive r, `h(0)=0`, at the registered exponent `0<p<1`. The new fixed-boundary recursive bill is

```
h(x-ej)  + h(x-ek)
+ h(y1-e1) + h(y1-x)
+ h(y2-e2) + h(y2-y1)
+ h(z-y2)  + h(z-x)
+ h(oj-z)  + h(ok-z)
+ h(o1-y1) + h(o2-y2).
```

All twelve terms are necessary, including the four first-unchanged-successor climbs. The two k contacts contribute `h(x-ek)` and `h(z-x)`; k does not touch either middle gate. The j chain runs through all four gates. Each i target/source touches exactly its own middle gate and then its frozen successor.

The old bill must likewise recount every selected gate and each register's first unchanged successor. One cannot sum isolated single-pair deltas whose exterior contacts are removed by the joint production. Both bills have the same rank mass, equal to the sum of exit dimensions minus the sum of entry dimensions. A full canonical BORROW recount must independently reproduce the claimed local delta, with cleanup regenerated from the changed word. No unexplained multiplicative cleanup factor is assumed.

## Exact feasible middle-frame domain

Define actual joins and intersections of subspaces:

```
L  = Ej join Ek
A1 = L join E1
A2 = A1 join E2
D  = Oj meet Ok
U2 = D meet O2
U1 = U2 meet O1
K  = A2 meet U1
J  = A2 join U1.
```

Feasibility is equivalent to the flag constraints

```
L <= X <= Y1 <= Y2 <= Z <= D,
A1 <= Y1 <= U1,
A2 <= Y2 <= U2.
```

In particular, the domain is nonempty exactly when `A1 <= U1` and `A2 <= U2`. These are genuine orientation-sensitive inclusion tests. If either fails, an excluded vector is a concrete infeasibility witness.

Assume those tests hold. Then `A1 <= K`, `K <= U1`, and both A2 and U1 lie inside U2. Write `a1=dimA1`, `a2=dimA2`, `u1=dimU1`, `u2=dimU2`, `k=dimK`, and `d0=a2-k`. The feasible **rank** pairs are exactly

```
a1 <= y1 <= u1,
a2 <= y2 <= u2,
y2-y1 >= d0.
```

Necessity of the last inequality follows because Y2 contains both A2 and Y1, while `dim(Y1 meet A2) <= k`.

For sufficiency, if `y1<=k`, choose Y1 between A1 and K at the desired dimension. If `y1>k`, extend K within U1 to dimension y1. In either case Y1 contains A1 and

`dim(Y1 join A2) = a2 + max(0,y1-k)`.

This is at most y2 under the displayed inequalities. Extend `Y1 join A2` inside U2 to dimension y2. Such extensions exist over F2 by extending bases. This constructs an actual nested pair with each feasible integral rank pair, rather than substituting ranks for orientations without proof.

The polygon has at most five distinct vertices, represented by these five actual subspace pairs:

| Label | Y1 | Y2 | Rank pair |
|---|---|---|---|
| 0 | A1 | A2 | `(a1,a2)` |
| 1 | K | A2 | `(k,a2)` |
| 2 | U1 | J | `(u1,u1+a2-k)` |
| 3 | U1 | U2 | `(u1,u2)` |
| 4 | A1 | U2 | `(a1,u2)` |

Coincident vertices are legitimate duplicate labels. Since `J<=U2`, the sloping boundary cannot cut the polygon above its top-right corner. No additional vertex or interpolated subspace is needed for the minimum below.

## Why exactly twenty frame labels suffice

For fixed Y1,Y2, concavity of the complete bill implies that a minimum in X and Z occurs at

`X in {L,Y1}`, `Z in {Y2,D}`.

These are actual feasible subspace endpoints. Once an endpoint choice is fixed, every tariff argument is an affine function of y1,y2. The remaining objective is therefore concave on the rank polygon. A minimum of a concave function on that compact polygon occurs at a vertex. The five explicit middle-frame pairs, each combined with the two X choices and two Z choices, yield **twenty labels** containing a global minimum for the fixed target order and chosen admissible carrier.

Two target orders and two carriers give up to eighty labels per oriented packet. A rank-one directed two-by-two support can qualify as both fan-in and fan-out; these give different source-side and target-side carrier productions, up to160 labels on that same four-edge support before coefficient exclusions. Each admissible carrier contributes40 labels per orientation. The kind must be retained in the candidate identity. This is a complete optimization for this particular fixed-exterior four-gate production; it does not cover arbitrary m, unrestricted resynthesis, changing exterior frames or larger word contexts. General m has a longer nested-flag domain and needs its own exact optimizer or proof.

## Exit equalities remain represented

If i1's successor is an equality, require `Y1=O1`. Feasibility then forces `U1=O1`, so this is the right face `y1=u1` of the polygon. If i2's successor is an equality, require `Y2=O2`; feasibility forces `U2=O2`, the top face `y2=u2`. If j or k has a required equality exit, require `Z=Oj` or `Z=Ok`; whenever feasible, that frame equals D.

Every such feasible equality face has its vertices among the five listed middle pairs and corresponding endpoint choices. Multiple equalities are imposed simultaneously. Filtering the twenty labels by exact equality therefore preserves the minimum on any nonempty equality-restricted domain. Mere equal rank is insufficient; the actual frame must equal the pinned successor frame.

## Strict joint improvement with every isolated factor neutral

Take strict nested frames `R < S < T`, with `x=dimS-dimR>0` and `y=dimT-dimS>0`. Both i registers enter and leave at S. j and k enter at R and leave at T. Use the chronological old word

```
i1 += j; i1 += k; i2 += j; i2 += k,
```

with all four old frames S. Its complete bill is `2h(x)+2h(y)`: j and k each climb R to S and later S to T.

For the first isolated target pair, the second pair fixes both source successors at S. The minimum complete single-factor cost is exactly `2h(x)`. For the second isolated pair, the preceding contacts fix both source entries at S, and its minimum complete single-factor cost is exactly `2h(y)`. Both carriers give these neutral minima; other feasible intermediate frames can be worse. The crossed same-source pairs are not exposed single factors because an intervening gate touches their three-register support. Thus the previous single-factor census can legitimately find no gain on this fixture.

The joint production can choose

`X=R`, `Y1=Y2=S`, `Z=T`.

Its bill is `h(x)+h(y)+h(x+y)`, a strict decrease of

`h(x+y)-h(x)-h(y) < 0`.

For the smallest fixture `R={0}`, `S=span(1)`, `T=span(1,2)`, the exact paid-profile change is `H2-2H1`. The dual fan-out fixture has the same support sequence and bill. The strict inequality follows from the concave power's strict subadditivity on positive x,y.

This does not contradict an optimum for the old fixed DAG: the old gates force k through S, while the joint production removes its intermediate S contacts. The new scalar word therefore changes the DAG. It is a concrete shared-interface mechanism, not a promise that it occurs in the current named source.

## Required independent controls and admission scope

An implementation should check both scalar orientations, both orders and carriers on independent dirty inputs; reject unequal ratios, zero coefficients, repeated or centre registers, inadmissible dyadic ratios, wrong preprocessing/undo signs and missing undo. It should retain exact subspace and equality counterexamples, hidden-warp and touching-intervener controls, and full-boundary mass checks.

An independent small-space oracle should enumerate actual F2 subspaces and nested quadruples, not only ranks, and compare its true minimum with the twenty-label minimum. Include a case with `A1 < K < U1` and nontrivial `J`, so that the two intersection/join vertices are essential; tests using only coordinate-nested bounds would miss the central rank-polygon constraint. Include equality-restricted and infeasible domains. The shared-restoration fixture must also check that both isolated factors are neutral, not merely that the joint factor is favorable.

An accepted source candidate still requires whole-word canonical profile and cleanup parity, complete forward/dual semantic checks, preserved ordered widths and endpoints, the actual current literal allocation and full local-plus-idle profile, and a valid native/physical/supplier/outer invoice. Four scalar instructions replace four for m=2, but that does not by itself prove unchanged primitive cost: coefficients, frames, native phases and prefixes still matter. No screen-level negative local moment is a complete κ admission.

The operation is a guarded exact scalar production with a changed contact graph. Its cost-bearing effect is the merged recursive climb. Overlapping productions need not commute, and neither rank incidence nor this finite flag optimizer supplies an intrinsic abelian physical toppling law.

Retain the current source's full release attribution, original `data/words/PINS.json`, Jeremy Kothe's PR3015 credit, CubeJerry's scoped PR1533 precedent, and all predecessor CREDITS/NOTICE/SOURCES. Source metadata currently identifies PR3028 as the later complete T148 composition on the same R1 local words; the registered current comparator and its conditional native/outer scope must be pinned separately from this source-neutral algebra.
