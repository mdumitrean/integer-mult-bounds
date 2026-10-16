# Fixed-boundary fan factorizations: independent frame/cost review

This is algebraic planning and static review, not an executed experiment. It credits Jeremy Kothe's PR3015 restore edit as the immediate production precedent. The general concave fixed-boundary flag argument also has the prior scope documented for CubeJerry's PR1533; no new identity or general method is claimed. The contemplated source-bound domain is distinct from CONT04's directed-chain corrected swaps, subject to the coordinator's overlap review and preregistration.

## Two orientations and two carrier choices

Let `i,j,k` be three distinct actual registers and `a,b` nonzero exact coefficients. All statements are for arbitrary incoming dirty values.

For same-target fan-in,

```
i += a*j; i += b*k
    == j += (b/a)*k; i += a*j; j -= (b/a)*k.
```

For same-source fan-out,

```
j += a*i; k += b*i
    == k -= (b/a)*j; j += a*i; k += (b/a)*j.
```

The preprocessing and undo signs differ between these orientations. Both triples have first/last support `{j,k}` and middle support `{i,j}`. Swapping `(j,a)` with `(k,b)` gives the second carrier choice. These formulas preserve the full linear map on independent inputs, rather than only its zero-buffer specialization.

Native coefficient admissibility is separate from the rational algebra: the quotient of two dyadics need not be dyadic (`1/(3/2)=2/3`). A dyadic-only native grammar must test the reduced denominator of each new coefficient. Otherwise a separately proved broader scalar primitive is required.

## Exact flag and all eight corners

Let `E_i,E_j,E_k` be the fixed frames immediately before the old pair, and `O_i,O_j,O_k` the next fixed exterior contacts or canonical endpoints. The old internal gate frames are replaced, while all exterior frames remain fixed. In the new triple assign frames `X,Y,Z` chronologically. Define joins/meets over the actual F2 subspaces:

```
L = E_j join E_k
A = L join E_i
C = O_i meet O_j meet O_k
D = O_j meet O_k.
```

Feasibility is exactly

```
L <= X <= Y <= Z <= D,   A <= Y <= C.
```

Thus a feasible domain requires `A <= C`. With `l=dimL`, `a=dimA`, `c=dimC`, `d=dimD`, the rank domain is

`l <= x <= y <= z <= d`, `a <= y <= c`.

Every integral rank point in this domain is realizable by nested subspaces: first choose `Y` between A and C, then X between L and Y, and Z between Y and D. No orientation-based rank assumption substitutes for the actual inclusion checks.

Write `h(r)=(r/73)^p` for positive r and `h(0)=0`, with the registered exponent `0<p<1`. The entire new three-register boundary bill is the sum of **nine** jumps:

```
h(x-e_j) + h(x-e_k)
+ h(y-e_i) + h(y-x)
+ h(z-y)   + h(z-x)
+ h(o_i-y) + h(o_j-z) + h(o_k-z).
```

The last three terms are successor climbs, not optional corrections. The old two-gate boundary bill has seven terms, including its own three successor climbs.

The objective is concave in the three ranks, since each nonnegative rank difference is affine and h is concave. For a fixed y, a minimum exists at `x in {l,y}` and `z in {y,d}`. For each such endpoint choice, the remaining function of y is concave, so a minimum exists at `y in {a,c}`. Hence the eight actual-subspace corners

```
Y in {A,C},  X in {L,Y},  Z in {Y,D}
```

contain a global minimum for this fixed-boundary family. Duplicate corners are harmless and must follow the declared enumeration convention. This proves completeness for these two fan orientations and boundary-preserving triples; it does not cover arbitrary resynthesis, changing exterior frames or reordering surrounding gates.

## Equality faces and scalar barriers

If i's next edge is an equality, require `Y=O_i`. Feasibility then forces `C=O_i`, so this is already an upper corner face. If j or k has an equality exit, require `Z=O_j` or `Z=O_k`; whenever feasible, the corresponding frame is D. Multiple equality requirements must hold simultaneously. Thus filtering the eight corners by exact exit equalities does not lose a smaller feasible non-corner assignment.

Alias/warp splits must be respected. No scalar pair may straddle a B warp gap, even if the warped register is touched by only one of the old gates and the shared-register alias test would not notice it. Do not cross A's prelude boundary, a cut, a section boundary or a frozen endpoint interface. New operations and B warp indices must be placed by the exact source-bound edit convention. Removed or inactive registers remain prohibited.

## Positive fixture and falsifiers

Take strict nested subspaces `R < S < T`, with `x=dimS-dimR>0` and `y=dimT-dimS>0`. Let i enter and leave at S, while j and k enter at R and leave at T. The old two gate frames are S. Its boundary bill is `2h(x)+2h(y)`. Choosing `X=R,Y=S,Z=T` gives `h(x)+h(y)+h(x+y)`, so the difference is

`h(x+y)-h(x)-h(y) < 0`.

This is a strict positive cost mechanism for either scalar orientation with coefficients satisfying the native guard. It is an analytic fixture, not evidence of its occurrence in the named source word. The strict inequality follows from subadditivity of the concave power on positive arguments.

Independent negative controls should isolate a wrong undo sign, a non-distinct or zero-coefficient input, an inadmissible ratio, a violated subspace inclusion despite a legal rank, a required exit equality, a hidden warp barrier and omission of the successor bill. Exact full-map replay must use arbitrary independent dirty inputs. A complete candidate must reproduce the local boundary delta in its full canonical BORROW ledger; cleanup and compensation are derived from the changed word, not priced by assuming an unproved factor of one or two.

## Admission boundary

The identities preserve the net scalar map and fixed helper endpoints, but the changed word still needs complete frame/cut/warp validation, regenerated cleanup/compensation, and the source-bound native primitive/prefix invoice. A lower local profile is not by itself a modern conditional κ certificate. If the original literal allocation is reused, the unchanged ordered widths and all dispatch/owner bindings must be checked and the complete local-plus-idle profile re-derived. Any changed source claim or inherited theorem premise remains explicit.

No state-independent physical Laplacian follows from these identities or their flag geometry. The exact structure here is a guarded production plus a complete concave boundary tariff, with a finite eight-corner minimization proof.
