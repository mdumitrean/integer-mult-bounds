# Two-target common-ratio carrier production

This is a source-only mathematical proposal and independent review, prepared before the continuation09 experiments. No source census, model import, frame search, or candidate price was executed for this note. The companion [JOINT-CARRIER-PROOF.md](JOINT-CARRIER-PROOF.md) gives the independently derived frame polygon. The proposed implementation is `pipeline/continuation09/shared_carrier.py`.

The changed premise is sharing one carrier preparation and one restoration across **two targets**. Continuation08 priced one target at a time with its actual exterior contacts frozen. Those single-target negatives remain valid. The joint fixture below has a strict fully charged boundary saving while both constituent single-target minima are neutral. This is not a larger-distance version of the single-target hypothesis.

## Exact dirty-register identities

Let `i1`, `i2`, `j`, and `k` be four distinct non-centre registers. The scalar coefficients `a1,a2,b1,b2` are nonzero admitted dyadics, with the common ratio `q=b1/a1=b2/a2`. The chosen orientation is admitted only if reduced `q` is also dyadic; that property does not follow from the four input coefficients. The reverse carrier orientation tests `1/q` independently.

The four fan-in additions, in any literal order,

```
i1 += a1*j; i1 += b1*k;
i2 += a2*j; i2 += b2*k;
```

have the same exact action on arbitrary dirty inputs as

```
j += q*k;
i1 += a1*j;
i2 += a2*j;
j -= q*k;
```

The two middle additions may be exchanged. The original additions all commute because their targets and source registers are disjoint. The new carrier `j` finishes with precisely its original value. The second carrier construction swaps `(j,a1,a2)` and `(k,b1,b2)`.

The fan-out identity is

```
j += a1*i1; k += b1*i1;
j += a2*i2; k += b2*i2;
```

replaced by

```
k -= q*j;
j += a1*i1;
j += a2*i2;
k += q*j;
```

It has the same contact graph and tariff. The old dirty contribution `q*j_old` cancels. Equality of the complete invertible scalar maps also gives equality of their inverse transposes. The implementation separately compares exact chronological rational matrices in both orientations, including the entire exposed interval, rather than relying only on this deduction.

Each two-target replacement has four scalar additions before and after. This fact is not a complete native-cost certificate: the coefficients, primitive frame payloads, inverse cleanup, and full native invoice still require checking.

## Literal domain and interfaces

The finite primary domain is two-by-two rank-one scalar packets in A after its fixed prelude and in B between successive warp barriers. Restore is excluded: Jeremy Kothe's PR3015 reports a search over all two-to-four-gate restore blocks of PR2979. No scientific conclusion is drawn from its unshipped search implementation.

Every gate between the first and last selected additions is either one of those four additions or an `add`/`scale` whose registers are disjoint from all four packet registers. Thus the four chosen additions can be exposed at the beginning of the interval, while all intervening gates retain their relative order and frames. No warp, cut, section boundary, prelude boundary, or additional contact on any of the four registers may be crossed. All 24 literal orders of the four selected edges are permitted.

A complete enumeration can group consecutive contact-pairs of each inner register by their two outer registers and exact coefficient ratio, then match distinct inner registers and check the full four-register window. Any admissible packet necessarily appears in this grouping: an unselected intervening contact on either inner register would violate the packet guard. The same scalar rank-one rectangle may qualify as both fan-in and fan-out; these are different carrier placements and must retain separate candidate IDs.

The fixed boundary graph supplies actual preceding and succeeding contacts, virtual warp aliases, and equality-exit flags. Old floors are not reused to optimize a changed graph. An equality exit at an A cut or warp entrance forbids an invented paid climb into that boundary.

## Complete boundary bill

Let `E_r` and `O_r` denote each register's actual entry and exit subspace, with dimensions `e_r,o_r`. The new gate frames in execution order are `X,Y1,Y2,Z`; the shared carrier enforces

`X ⊆ Y1 ⊆ Y2 ⊆ Z`.

For `H(t)=(t/73)^(1-c)`, with `0<c<1` and `H(0)=0`, the whole changed boundary bill is

```
H(x-ej) + H(x-ek)
+ H(y1-e1) + H(y1-x)
+ H(y2-e2) + H(y2-y1)
+ H(z-y2) + H(z-x)
+ H(o1-y1) + H(o2-y2) + H(oj-z) + H(ok-z).
```

The final four terms are the climbs into the first unchanged successors, including ordinary final frames. Equality successors force the corresponding term to zero by subspace equality, not by dropping its charge. The old bill is computed from the actual four old gate frames and these same boundaries. Both totals telescope to the same rank mass. Centre payments are outside this interval and are retained exactly once by the canonical whole-word ledger.

## Exact twenty-label minimum

For a chosen middle-register order, define

```
L  = Ej ∨ Ek
A1 = L ∨ E1
A2 = A1 ∨ E2
D  = Oj ∩ Ok
U2 = D ∩ O2
U1 = U2 ∩ O1
K  = A2 ∩ U1
J  = A2 ∨ U1.
```

Feasibility requires and is implied by `A1 ⊆ U1` and `A2 ⊆ U2`. Write lower-case letters for dimensions, and `h=dim K`. The attainable middle-frame ranks are precisely

```
a1 ≤ y1 ≤ u1,
a2 ≤ y2 ≤ u2,
y2-y1 ≥ a2-h.
```

Necessity follows because `Y2` contains `A2+Y1`, while `dim(Y1∩A2)≤min(y1,h)`. For sufficiency, extend `A1` inside `K` first to rank `min(y1,h)`, then inside `U1` to rank `y1`. The span with `A2` has rank `a2+max(0,y1-h)` and can be extended inside `U2` to any admitted `y2`. This constructs actual subspaces; dimension feasibility is not being substituted for word feasibility.

This rectangle cut by one half-plane has at most five vertices, with explicit frames

```
(A1,A2), (K,A2), (U1,J), (U1,U2), (A1,U2).
```

For each vertex take `X=L` or `Y1`, and `Z=Y2` or `D`, retaining all twenty labels even when assignments coincide. With the middle ranks fixed, concavity places a minimum at those endpoints for `x,z`. Each resulting tariff is concave in `(y1,y2)`, hence has a minimum at one of the five polygon vertices. The proposed controls independently enumerate actual small finite-field subspaces and compare complete tariff minima; they include a four-dimensional fixture where all five vertices are distinct.

A target equality exit requires `Y1=O1` or `Y2=O2`. If feasible, this forces `O1=U1` or `O2=U2`, respectively, selecting the right or top polygon face. Carrier equality exits require `Z=D`. These are faces whose vertices are already in the list, so exact filtering of the twenty labels preserves completeness. Both middle orders are separately enumerated.

## Joint headroom with neutral single factors

Choose nested frames `R ⊂ S ⊂ T`, and let `x=dim S-dim R>0`, `y=dim T-dim S>0`. Both inner registers start and end at `S`; `j,k` start at `R` and end at `T`. The four old additions occur in target-pair order, all at `S`.

The original full boundary bill is `2H(x)+2H(y)`. The joint replacement uses frames `R,S,S,T` and costs `H(x)+H(y)+H(x+y)`. Its exact delta is

`H(x+y)-H(x)-H(y) < 0`.

For `x=y=1`, the old profile is `4H1`, the new profile is `2H1+H2`, and the signed delta is `-2H1+H2`, with identical rank mass and identical scalar-add count.

For the first target alone, the other target's unchanged contacts force both outer successors to `S`; its single-target minimum is exactly `2H(x)`. For the second target alone, the first target's unchanged contacts force both outer entries to `S`; its minimum is exactly `2H(y)`. Their sum ties the original. The shared production changes those internal contacts jointly and charges the shared preparation and restoration once. This is a mathematical fixture, not a claim that the source words contain such an improving packet.

## Evidence, attribution, and stopping scope

The local word source is Jeremy Kothe's PR3015, with its retained PR2979 and earlier source credits. The current comparison source is Nick Petalas's PR3028, which reuses the same words in a different allocation. The constructor receives the exact comparison endpoint from the coordinator. The inherited word-source physical count must not be reported as the PR3028 allocation count or as a fresh global candidate invoice.

PR2979's reported 5,893 read-merge/split and related candidates leave possible historical overlap because the precise constructor domain is not public in the acquired artifacts. This proposal makes no novelty or previously-unsearched-domain claim. Continuation08's complete single-target result and the older triangle/expansion negatives are preserved with their original domains.

A scientific NULL is possible only after both seeds resolve the entire registered packet/order/carrier/twenty-label domain, with controls and source bindings intact, and no certified negative local moment delta. An unresolved interval or invalid execution is exploratory. A favorable boundary result requires fresh canonical full-profile and cleanup parity, all-column forward/dual audit, and fresh changed-word native/finite/prefix/outer validation before any complete κ claim. No unregistered move to three targets, larger exterior changes, or another candidate family follows automatically from a null result.
