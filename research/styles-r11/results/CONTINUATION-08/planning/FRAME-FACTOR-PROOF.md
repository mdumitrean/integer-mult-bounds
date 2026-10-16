# Exact carrier-factor frame reduction

This is a source-only derivation and finite control specification, not an experimental result. Direct realized rewrite credit belongs to Jeremy Kothe/PR3015 R1; CubeJerry/PR1533 supplies the prior fixed-boundary flag and concavity framework. All inherited source attribution remains in `PRODUCTIONS.md` and the source adapter. The scientific domain is A/B only; the known restore edit is a positive control.

For three distinct registers and nonzero dyadic a,b with admitted dyadic t=b/a, execution-order identities are:

```
fan-in:  i += a*j; i += b*k  =  j += t*k; i += a*j; j -= t*k
fan-out: j += a*i; k += b*i  =  k -= t*j; j += a*i; k += t*j.
```

Swap (j,a) and (k,b) for the second carrier orientation. Both preserve every dirty input exactly. The inverse-transpose equality follows by applying each gate's inverse transpose in the same chronological order, and is checked independently. A non-dyadic reduced t is rejected; dyadic inputs alone do not imply dyadic division.

In either case the outer support is {j,k} and the middle support is {i,j}. For literal source pairs separated by gates disjoint from {i,j,k}, those intermediates commute with both selected gates and all three replacements. Therefore stable exposure and restoration of their original order preserves the complete interval map and every intermediate scalar/frame payload. B warp barriers and section/cut/prelude boundaries are never crossed. The full retained interval is also checked with an independent sparse add/scale matrix oracle in both orientations.

Let E_r and O_r be the actual frames of the previous and next exterior contacts of register r, with exact virtual aliases at warps. Let X,Y,Z be the new frames. They necessarily form a flag X⊆Y⊆Z. Define

```
L=E_j∨E_k,  A=L∨E_i,  D=O_j∩O_k,  C=D∩O_i.
```

Feasibility without equality exits is equivalent to A⊆C. The chain L⊆A⊆C⊆D follows. With l,a,c,d their dimensions, every feasible rank triple satisfies l≤x≤y≤z≤d and a≤y≤c. Conversely a basis extending this chain realizes every such integer rank triple. This is an exact geometric characterization, not an assumption that dimensions alone imply arbitrary subspaces intersect correctly.

Writing H_r=(r/73)^(1−C0), H_0=0, the complete three-register boundary cost is

```
H_(x−ej)+H_(x−ek)+H_(y−ei)+H_(y−x)
 +H_(z−y)+H_(z−x)+H_(oi−y)+H_(oj−z)+H_(ok−z).
```

Each term is a genuine consecutive-chain jump. The last three are the newly affected successor climbs; omitting them changes the question. All coefficients of H are positive. Since 0<C0<1, the function is jointly concave in the rank variables. For fixed y,z, its minimum over x∈[l,y] occurs at l or y. For fixed x,y, its minimum over z∈[y,d] occurs at y or d. For each of these four substitutions the remaining function of y is concave on [a,c], so a minimum occurs at a or c. This yields exactly eight labeled attainable corners:

```
Y∈{A,C}, X∈{L,Y}, Z∈{Y,D}.
```

Duplicate frames retain separate labels. The conclusion is a minimum for this operator order and these exterior frames, for any concave tariff with H0=0. It does not make a global whole-word or native-cost claim.

A cut or warp entrance can require the last new frame to equal O_r rather than merely lie inside it. The last touch of i is Y, and the last touches of j,k are Z. Equality at i can be feasible only when O_i=C, forcing Y=C; equality at either outer register can be feasible only when its O equals D, forcing Z=D. Simultaneous outer equalities must agree. These are corner faces, so filtering the eight assignments for exact equality remains complete. The actual alias/equality predicates come from the trusted literal graph, not a claimed profile.

The old source pair is priced from its actual two possibly different frames and the same three entry/successor interfaces. Its rank mass and the new mass both telescope to Σ_r(dim O_r−dim E_r). Fast screening uses this exact boundary delta; retained constructions must independently reproduce it with the full canonical word, including fixed centre descents exactly once and regenerated cleanup.

A strict positive fixture uses R<S<T, E_i=O_i=S, E_j=E_k=R, O_j=O_k=T, old pair frames S,S and new frames R,S,T. If x=dimS−dimR and y=dimT−dimS, the old cost is 2Hx+2Hy and the new cost is Hx+Hy+H_(x+y). Strict concavity gives H_(x+y)−Hx−Hy<0. Dimensions 7,8,9 reproduce the known PR3015 increment pattern. This does not imply a new positive source address.

The independent small-frame control enumerates all16 subspaces of GF(2)^3 as explicit sets and all4096 ordered frame triples per fixed boundary fixture. It uses direct set containment and exact rational concave tariffs, independently of the production's corner construction. Fixtures include non-coordinate lines, separate entry directions, middle/outer/all exit equalities, and an infeasible exit. Complete-flag minima must match the eight corner minima, including all successor terms. This control is run only by the registered coordinator, twice; writing its source does not run it.

The changed scalar word still adds a primitive instruction and potentially its cleanup inverse. Full native, precision, prefix, physical and supplier/outer charges must be independently re-derived for a claimed κ improvement. A favorable recursive boundary delta, a short grammar, or a reference graph statistic is insufficient. The old native receipt cannot be transferred by an unchanged scalar matrix alone.
