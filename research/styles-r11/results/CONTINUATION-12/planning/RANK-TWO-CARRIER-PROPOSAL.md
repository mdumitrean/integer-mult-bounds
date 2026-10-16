# Rank-two source-basis shear: bounded constructive proposal

This is a static algebra/frame proposal. No source census, numerical tariff,
solver, candidate construction, or experiment was run to prepare it. It is not
an admitted improvement or a claim of an intrinsic Laplacian.

The changed premise is a **rank-two** coefficient matrix on two sources and two
targets. CONT08 F1 factors one target's two reads; CONT09 J1 and CONT11 J2
require the two target coefficient rows to be proportional. Here one row is
eliminated in a changed source basis while the independent row retains a
charged residual read. A five-gate replacement can therefore remove an early
source contact without pretending that the independent covectors coincide.

## Exact production and scalar guards

Let all four registers `u,v,j,k` be distinct arbitrary dirty registers. The
original four commuting gates implement

```
u += a*j;  u += b*k;
v += c*j;  v += d*k.
```

Require all four coefficients to be nonzero admissible dyadics and
`a*d-b*c != 0`. Put `q=b/a`, require its reduced denominator to be a power of
two, and put `e=d-q*c`. The residual `e` is nonzero. Execute

```
j += q*k;
u += a*j;
v += c*j;
v += e*k;
j -= q*k.
```

The source `j` is restored, `k` is unchanged, and the two target increments are
exactly `a*j_old+b*k_old` and `c*j_old+d*k_old`. This proves the arbitrary-dirty
forward identity. Applying the inverse-transpose primitive to each gate in the
same execution order proves the dual identity. A retained candidate must also
pass an independent complete-window forward and dual sparse-matrix check.

Either source can be the encoded carrier and either target can supply the
cancelled row. The other target's two output reads are kept in the displayed
order and are assigned **one common frame**. This is a declared restriction,
not a claim to optimize all five independent gate frames. Every new coefficient
and the complete undo must be charged. The full forward-plus-cleanup word has
two additional scalar instructions; recursive profile savings do not erase
that finite implementation cost.

## Exact matched-frame tariff

Write the four gate-frame levels as `X ⊆ Y1 ⊆ Y2 ⊆ Z`: encode at `X`, cancelled
target's read at `Y1`, both residual target reads at `Y2`, and undo at `Z`.
Let `E_r,O_r` be actual exterior entry/exit frames of register `r` after the
chosen exact gather placement. Let `h(t)` be any increasing strictly concave
child tariff, with `h(0)=0`. The complete fourteen-term boundary bill is

```
j: h(x-ej)+h(y1-x)+h(y2-y1)+h(z-y2)+h(oj-z)
k: h(x-ek)+h(y2-x)+h(z-y2)+h(ok-z)
u: h(y1-eu)+h(ou-y1)
v: h(y2-ev)+h(0)+h(ov-y2).
```

The source `k`'s surviving contact is essential. Omitting it would incorrectly
price this rank-two production as the old rank-one production. First exterior
successor climbs are included once; cut/warp equality interfaces require exact
frame equality, not an invented extra climb. Centre descents outside the
unchanged A/B barrier segment cancel exactly.

Define, using actual subspace join and meet,

```
L=Ej∨Ek, A1=L∨Eu, A2=A1∨Ev, D=Oj∩Ok,
U2=D∩Ov, U1=U2∩Ou, K=A2∩U1, J=A2∨U1.
```

Feasibility requires `A1⊆U1` and `A2⊆U2`. The exact same feasible rank polygon
as the CONT09 two-target flag proof applies. Its five realized middle-frame
vertices are

```
(Y1,Y2)=(A1,A2),(K,A2),(U1,J),(U1,U2),(A1,U2).
```

For each, use `X∈{L,Y1}` and `Z∈{Y2,D}`, preserving all twenty labels even when
frames coincide. The displayed tariff is jointly concave in these four ranks.
Minimizing the outer ranks at endpoints and then minimizing over the middle
rank polygon proves completeness for the **matched residual-read frame class**.
Filter the exact equality faces for any constrained exterior exits. The
intersection/join vertices are necessary in nonnested boundary geometry.

## Strict positive fixture beyond the previous domains

Take `R=0 ⊂ S=span(1) ⊂ T=span(1,2)`. The target `u` enters/exits `S`, target
`v` enters/exits `T`, and both sources enter `R` and exit `T`. The original
execution order is interleaved:

```
u += j @S;  v += j @T;  u += k @S;  v -= k @T.
```

The coefficient determinant is `-2`. The original complete bill is `4h(1)`.
Use `X=R,Y1=S,Y2=Z=T` in the five-gate production; the complete bill is
`2h(1)+h(2)`, strictly smaller, with identical rank mass four.

Both individual fan-in pairs fail F1's disjoint-intervener exposure rule: the
intervening gate touches one of their sources. The two adjacent fan-out pairs
cannot have a legal dirty target-carrier factor: their carrier entry join
contains `T`, while one carrier must exit `S`. J1/J2 exclude the block because
its coefficient rows are independent. Thus this fixture establishes headroom in
the broadened exposure domain; it does not establish that the current source
words contain an improving instance.

There is an important domination caveat. With ordinary source exits, the
matched-frame joint construction is weakly dominated by the broader exposed
single-row sequence `encode@X; u-read@Y1; undo@Y2; v-read-j@Y2;
v-read-k@Y2`. Its final source climbs merge `Y2→Z→O` into `Y2→O` and cannot cost
more by concavity. This hypothetical broader exact-commutation exposure was
not F1's disjoint-intervener domain. The positive fixture therefore does not
prove irreducible shared-restoration benefit. A source equality exit can block
this domination when the final actual touch must equal `O` and `Y2 != O`.

## Proposed finite source domain and obligations

Use a freshly pinned source chosen by the coordinator, retaining its complete
source credits. In A after the prelude and in B split at every warp, form pairs
of consecutive contacts of each target register. Group pairs by their same two
source registers, without the old common-ratio key. Combine distinct targets,
require exactly one nonzero edge for each target/source pair, four distinct
non-C registers, and determinant nonzero. Preserve all four original edge
interleavings. This is a complete census of the stated consecutive-contact
domain, not every possible four-gate subset.

For each packet, try stable gather-left and gather-right within its original
window. Certify every selected/unselected crossing as an exact scalar
commutation. Intermediate moved-frame words need not be feasible; the final
whole-window frame chains must be. Preserve all unselected gate frames/order,
barriers, helper endpoints and widths, cut/warp interfaces, and physical stock.
Derive the frame boundaries from the gathered order and bill all touched
registers, including unchanged interveners and their first outside successors.

Each packet has at most `2 placements × 2 source carriers × 2 cancelled rows ×
20 frame labels = 160` proposed labels. The five-gate replacement changes raw
length by one, so every later B warp position must be reindexed mechanically.
Retained candidates need complete canonical profile/cleanup regeneration,
exact full-window-versus-canonical delta parity, all independent-input forward
and dual admission checks, and a fully charged complete allocation/root and
finite native/outer admission path. A local tariff improvement alone is not a
κ improvement; prior native receipts do not become a fresh changed-word replay.

Mandatory controls should cover the interleaved positive fixture, all signed
dyadic identities and both carrier/anchor choices, nondyadic quotient rejection,
wrong residual coefficient, omitted undo, false rank-one classification,
noncommuting crossings, hidden barriers, stale preimages, equal-rank wrong
subspaces, missing surviving-k contact, and missing successor charges. A tiny
independent subspace oracle should verify the twenty-label minimum in the
matched-frame class, including nontrivial `K` and `J` vertices.

Do not infer novelty from the production. The elementary source-basis shear is
standard. Prior PR2979's undocumented read merge/split census may partially
overlap; active shared-covector work must be checked again before registration.
The distinguishing registered hypothesis is independent rows plus a charged
residual read, on a named current source, with the explicit finite frame class.

## Resources and stopping

No data-dependent packet count has been measured. Indexing uses the scalar
word length and grouped consecutive-contact records; pricing is a small exact
subspace/boundary calculation per label, with no solver. Reuse one cached
gathered-window geometry per packet/placement and dispatch plan shards through
the central pool. A reasonable registered upper envelope is two million labels
per provider, 64 shards/provider/seed, at most eight paired retained addresses,
and a 12,000 CPU-second family budget. These are bounds, not runtime estimates
from an unrun census. Any domain-cap/budget failure is incomplete and must not
be converted into a scientific null; retain all exact exclusions. Complete
nonempty coverage with no strict tariff improvement is a null only for this
matched-frame rank-two family. Do not broaden or rerun after that decision
without a separately justified premise and registration.

Prior immutable proof/code references: `results/CONTINUATION-09/planning/JOINT-CARRIER-PROOF.md`,
`pipeline/continuation09/shared_carrier.py`, and the whole-window invoice and
commutation obligations in `results/CONTINUATION-10/planning/GATHERED-WINDOW-PROOF.md`.
