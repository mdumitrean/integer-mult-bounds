# A concrete fixed-word packing circuit and its admission boundary

This is source analysis and an analytic construction proposal, written before
the continuation06 experiment. No candidate, matching, control or numerical
root was executed to obtain it. Earlier nulls and EXPLORATORY receipts are
unchanged. The proposed implementation is `pipeline/continuation06/topple.py`;
only a separately registered coordinator pool may execute it.

The most direct remaining route is a literal allocation change with the
PR2979 local words unchanged. It avoids the changed-word native gap that
blocked the preceding scalar-context proposal. A state-independent physical
Laplacian has not been established. The operation below is an exact integer
pattern circuit with a genuine cost effect and explicit indivisible-role
guards; its incidence matrix must not be relabeled an intrinsic sandpile.

## Source and the small available gap

The reference is Marius-Paul Dumitrean's PR2979, head
`be191346391661f4d35fc0d1508d0a6029572576`, acquired as inert data under
`data/continuation-05/pr2979/package/`. Its inherited PINS, CREDITS, NOTICE and
SOURCES remain attached to every result. In particular, the owner chronology
and engines credit Tekalign, the paired extraction credits Jeremy Diviney and
Mason Hale, and the composed rewrites and supplier lineage credit Jeremy Kothe.

The source declares a complete conditional finite release at
`0.001729033982646513517717 - 10^-46 - 10^-70`, with 74 replicas, 666 calls,
408 helpers per call, 632 independent local inputs and 91 private buffers.
The fixed words have ordered width inventory
`{4:26,5:2,6:16,7:52,8:99,9:213}` and local profile
`{1:2445,2:706,3:232,4:108,5:18,8:8}`. The literal idle profile is
`{1:17310,3:4956,5:1728,48:28190}`.

`certificates/RELAX-CAP.json` declares the fixed-capacity fractional cap in
`[0.001729035764875516181444, 0.0017290357648755161814441]`.
The saved literal gap is about `1.782229e-9`. That cap drops chronology and
integrality, and is not a claim of an attainable owner fill. PR2979 explicitly
leaves integral packing open. The present constructor is a sufficient concrete
realization question, separate from necessary interval-Hall obstructions such
as the newly observed PR2987 scope.

## An exact 55-bin circuit

Write a pattern as its helper widths followed by the bin capacity. The saved
T74 mix has six exceptional full bins

`Z = [4,8,9,9,9,9] @48`.

It also contains `G=[9,9,9]@32` and `A=[7,9]@16`. The following integer
replacement preserves the count of every width and the number of bins of
each capacity:

| Remove | Add |
|---|---|
|20 Z@48|19 [9,9,9,9,9]@48 and one empty48|
|25 G@32|20 [4,9,9,9]@32 and five [7,7,9,9]@32|
|10 A@16|10 [8,8]@16|

Both sides contain exactly 215 actual roles, with widths
`4×20, 7×10, 8×20, 9×165`. Their used rank is 1795, their total capacity is
1920, and their idle rank is 125. All positive local paid children are
unchanged. The exact complete-profile difference is

`Δ = +20 H1 +19 H3 -25 H5 +H48`.

The idle-child count increases by 15. An old fill-transfer condition requiring
a nonincreasing residual-child count therefore cannot be reused verbatim.
Every new child must be paid in the fresh conservative invoice.

The saved fractional dual predicts that replacing these non-tight Z patterns
by tight patterns is beneficial at the reference endpoint. The registered
implementation must independently prove the sign using outward rational
intervals for `g(r)=(r/73)^(1-k)` at the exact reference `k`. Neither a sum of
squares nor a numerical root is the acceptance criterion. This residual
change is not a universal majorization improvement at every exponent.

Within the eleven pattern types of the shipped mix, the coefficient20 is
forced. Let `z=ΔZ`, let F denote `[4,9,9,9]@32`, and I denote `[9^5]@48.
The width and bin-count equalities give

`ΔF=-z`, `ΔG=5z/4`, and `ΔI=-19z/20`.

Consequently any reduction of Z in this restricted pattern support is a
multiple of20. Six Z bins at T74 cannot execute this circuit. This is not an
integer-optimality theorem over the full 2551-pattern catalogue: adding other
patterns changes the congruence equations.

## Five-copy chronology and a 69-role realization

Lift the existing T74 chronology by replacing each original call `(s,r)` at
time `t` by `(s,r+74k)` at time `5t+k`, for `k=0,...,4`. Lift each literal row

`(t,h,o,c,p,offset)` to `(5t+k,h,o+74k,c,p,offset)`.

The same stage progression holds in every copy. The unchanged template is
replayed on the entire lifted order to derive exact `(start,stop]` windows.
The original role and its cloned owner use the same copy index, so the copied
fill is feasible by projection; a fresh full literal audit remains mandatory.
There are now370 replicas,3330 calls,1,358,640 roles and30 Z bins. Native words,
ordered helper widths, native phases and local programs remain byte-identical.

Choose four original Z bins, five original G bins and two original A bins,
and take all five copies of each. Require the eleven original physical
families to be distinct; different child intervals of one family do not count
as different families. Designate four G originals as F destinations and one
as D=`[7,7,9,9]` destinations. Empty exactly one of the twenty Z copies.
Keep the original nine-width roles except one removed nine from each D copy
and all four nines from the emptied Z copy. Then the only moved roles are:

| Width | Source | Destination | Count |
|---|---|---|---:|
|4|all twenty Z copies|one into each F copy|20|
|8|all twenty Z copies|two into each A copy|20|
|7|all ten A copies|two into each D copy|10|
|9|ten A nines, five D nines, four emptied-Z nines|one into each of nineteen nonempty Z copies|19|

Thus69 roles move, and146 of the215 roles keep their bin. Offsets are compacted
only after the entire simultaneous assignment is chosen.

Each destination family receives only one moved width class. Because all
55 destination physical families are distinct, four independent integral
flow problems suffice. For each width use source→role capacity1, role→
`(call,destination-bin)` capacity1, that intermediate node→destination capacity1,
and destination→sink equal to its prescribed number of new roles. Retain an
edge only if its exact window contains the call and no unchanged or retained
role from the same call uses that physical family. Remove all69 source roles
simultaneously when testing this last guard. The intermediate capacity1
prevents two moved roles of the same call from sharing a destination family.

A complete flow assigns whole roles, never fractions of width. Integer
capacity bounds, conservation and flow/cut equality are checked independently.
The selected assignments are then checked directly against every local role,
window, family, capacity, prefix offset and exact pattern. This is a sufficient
construction; replication alone does not guarantee those matchings exist.

## Frozen bounded neighborhood policy to register

There are15 choices of four of the six original Z bins and four fixed
tie variants, giving60 outercases. All tie hashes use selection seed61129;
confirmation seeds only change scheduling, not the candidate family. An
outercase worker performs its own selector work so it is charged to its
timeout and pool budget.

For A bins, rank by the number of the20 incoming width8 roles having any legal
clone edge, then by total legal clone edges, then the fixed tie hash and bin.
Remove that A bin's old rows for this ranking, since it will be emptied.
Exclude Z families. Retain64 bins. Rank distinct-family A pairs by union
coverage, then the weaker single-bin coverage, then the fixed pair tie hash;
retain64 pairs. Test their exact20-role width8 flow in that order.

Rank G/F bins similarly on the20 width4 roles with all old G nines retained;
keep64. Precompute an exact five-role flow for each original Z width4 group
to each original G candidate's five copies. For each feasible A pair, rank D
candidates on its ten width7 roles, optimistically removing all D rows only
for scoring; exclude Z and A families and keep16. Match the four Z groups
injectively to four F physical families after excluding D. Then test each of
D's three possible removed-nine choices using the exact ten-role7 flow.
Take the first successful neighborhood; if none exists, report this finite
selector's failure, not a general packing impossibility.

Within that neighborhood, try each of its five G originals as D, each of
three removed-nine positions (original `(time,helper)` order), and each of
twenty Z copies as the empty bin: at most300 variants. Stop on the first full
four-flow witness, or record complete exhaustion. Incomplete search is a
timeout/EXPLORATORY result. All pruning counts and the chosen original bins
are retained. Selection is not scored by unregistered numerical root gains;
every complete circuit has exactly the same full-profile delta.

The synthetic control has43 distinct original calls carrying exactly the43
roles in these eleven original bins, lifted to215 distinct calls. Universal
windows and distinct families make the full69-role transport realizable.
Negative controls isolate strict window-start equality, same-call family
capacity, an overcapacity destination and an omitted moved role. The exact
moment sign is also independently checked. Synthetic evidence remains
analytic until the registered pool actually executes the controls.

## Admission that is reusable, and admission that must change

`pipeline/continuation/admission_v2.py` is an existing trusted precedent for
source-bound native reuse with fresh changed owner geometry. It successfully
supported the prior continuation01 fill-only conditional gain. Its actual
functions separate local free-operator audit, literal owner audit, source
receipt binding, family charts, finite invoices, exact root separation and
outer arithmetic. It is not a drop-in T370/91-buffer adapter: its constants
include T74,66304 live families,82 buffers,66804 physical families and source
PR2917. Copying those constants or asserting its old receipt equality would
be invalid.

The concrete T370 stock here is331520 live/data-owner families plus408 helper
families,8 centres,91 private zero buffers and2 coefficient-work families:
332029 physical families. Native programs and their632-column universal
contracts can be reused only through the exact unchanged source-word mapping.
The controller still has nine active calls and nine bridges per owner block;
global call counts and bridge/shift/move invoices scale, while the active
depth bound18 is per block. Recompute the physical-stock sup-to-l2 factor,
actual and reserved prefixes, all primitive counts and all nine strict finite
supplier inequalities. The extra15 residual children are charged explicitly.
Retained oversized allowances are acceptable only with an explicit inequality
that they dominate this new recount.

PR2979's receipt maps source WORD hashes to native artifact hashes; they are
not byte-identical names. For example base source WORD has SHA
`abaf67bfcb257528658c906b612f57025617592bd7889828f92b97a5f4f4300d`,
while its native `local/FULL-WORD.json.gz` has SHA
`6e26a36f49934ad97531c1c321eb2dd36e2581e7d2609f388d934b15f847be0d`.
Authenticate the explicit provider map, cache-tree entries and receipt/claim
linkage. Do not silently retain the old PR2917 adapter's equality of these
two hashes. The acquired package contains native receipts and complete tree
hashes, but not the complete native cache or `PHYSICAL-INVOICE.json` used by
the old adapter. A source-bound conditional transfer must say precisely which
saved evidence is inherited and independently reconstruct its changed finite
invoice; it must not claim a fresh native replay.

The source's parameterized owner engine has SHA
`77a848729159e271ba64f403dfd59dddb13044b17b2950fa56700f442e2fe461`.
Its acquired `.py.txt` is data only. Use a pre-existing authenticated trusted
engine or a separately reviewed independent adapter; never import that
acquired file. The old generic `fill.audit` also has a fixed66304 diagnostic
root, so a source adapter must isolate that diagnostic from the exact T370
role audit without changing any exact guard. The private audit adapter must
be source-pinned and its limited diagnostic change disclosed.

One successful circuit has candidate profile `5*PR2979.profile + Δ`; its idle
profile is `{1:86570,3:24799,5:8615,48:140951}`. Exact mass is five times the
source mass. First compare normalized complete moments at a rational
separator, with baseline moment divided by66304 and candidate by331520.
Then recompute the modern outer inequalities at the newly admitted endpoint
using two independent exact arithmetic checks and bind a new immutable
release receipt. Source/native reuse is conditional and the inherited
all-size/compiler/theorem assumptions remain. A local matching PASS is not
that release.

## Why a fused scalar primitive is not the immediate alternative

The previous context-shear failure is an exact persistent-subspace conflict:
one orientation forces entrance line224 into target170's final `perp(88)`,
and the other forces line262 into target194's `perp(446)`. Both relevant
binary pairings are odd. Simultaneously evaluating the same two nonzero
cross-register corrections does not erase those forbidden directions from
the independent dirty-column map. A real fused primitive would have to
cancel the offending transfer in the net operator, change an input/target
interface, or provide a separately proved multi-frame native implementation
with its own transport, phase, buffer and primitive invoice. Calling several
scalar operations one toppling is not such a proof.

Fixed-hyperplane message closure is abelian on its declared Boolean cap state,
but its exact cost network depends on the current frames and word. It supplies
neither an intrinsic state-independent rank Laplacian nor a bypass around a
fixed entrance outside a fixed target hyperplane. A correctly priced
multi-register primitive is a different admissible-operator hypothesis and
would need substantially more native work than this unchanged-word circuit.

The circuit itself is reversible as a width-conserving combinatorial move;
the reverse must still satisfy the live role guards. Disjoint physical-bin
and call supports can commute, but shared supports and chronology make
arbitrary repeated circuits state-dependent. No general abelianity,
optimal stabilization or sandpile-group claim follows.

## Bounded execution and falsifier

The heavy baseline and five-copy model are loaded once in the parent, after
source/preregistration freeze and a memory projection. Only compact role
patches and flow witnesses return from the60 case tasks per seed. A successful
canonical witness alone is materialized into one full fill, audited and
compressed; no worker repeatedly copies the1.36-million-role baseline during
neighborhood search. Per-task timeouts and6GiB RSS caps apply, using the common
61-worker pool and the round's14400 CPU-second allowance. Source inspection
does not establish a benchmark runtime.

The finite falsifier is failure of all60 registered selectors/neighborhoods
with complete coverage, exact failed-flow cuts, controls and both seed
confirmations. That result concerns this sufficient constructor only.
Timeouts, missing source bindings, failed scaled invoices or absent current
benchmark admission leave the corresponding claim unresolved. The planned
positive outcome is one complete literal T370 fill, exact gain, fresh scaled
physical/supplier/outer certificate and clearly scoped inherited native
evidence. No outcome has been claimed in this planning document.
