# J2: exact commutations, gathered carrier blocks and the complete window bill

This is source-neutral mathematical planning for CONTINUATION-10, written without importing scientific modules, inspecting source-word candidates, running a census, evaluating a source tariff or testing a fixture. All previous receipts and stop scopes remain unchanged. The proposed premise change is precise: an intervening gate may touch a selected register if every required adjacent crossing is an exact scalar commutation. Final frame feasibility is still mandatory.

The four-register carrier identity is credited to the shared-restoration derivation in CONTINUATION-09, building on Jeremy Kothe's PR3015 R1 carrier factor and CubeJerry's PR1533 fixed-boundary concavity precedent. The frozen proof is [JOINT-CARRIER-PROOF.md](../../CONTINUATION-09/planning/JOINT-CARRIER-PROOF.md), SHA256 691d77be0dda924bbc5c6faa8e6f815f46e2ab5a2363ad72a7654b87b12f40de. No intrinsic sandpile Laplacian or general confluence claim follows.

## 1. Exact finite transformation

Take one source-bound J1 structural exclusion with four selected positions p0<p1<p2<p3. They form the nonzero rank-one directed 2-by-2 coefficient block on four distinct non-centre registers. Retain its explicit fan-in/fan-out orientation, chosen dyadic carrier ratio, and middle order. The original window comprises every literal gate from p0 through p3. It must remain inside one A/B segment, outside the frozen A prelude, with no intervening B warp, cut, section transition or virtual-alias change. The separate source registration determines which saved exclusions are admitted; this proof does not extend that domain.

Label every original gate by its immutable original index. Gather-left is the stable partition with the four selected gates first, followed by all unselected gates in their original order. Gather-right puts all unselected gates first and the selected gates last. The selected four retain their original relative order during gathering. The carrier factor then replaces exactly those four gates by four gates. Every unselected scalar instruction and frame is retained exactly once, with its original relative order.

For gather-left, a selected gate at s crosses precisely the unselected gates originally at u<s within the window. For gather-right it crosses precisely those originally at u>s. These sets define a deterministic adjacent-transposition log. A certificate must bind all its crossed original-index pairs, not merely the final permutation or the number of crossings. There is no claim that other gather placements or other crossing sequences are exhausted.

For two ordinary, nonzero, non-self additions
E_uv(a): u += a*v and E_xy(b): x += b*y,
commutation holds exactly when v!=x and y!=u. This follows by comparing the two rank-one matrix products; in the exceptional opposing-edge case their diagonal cross terms differ. Same-target and same-source additions therefore commute, but a read of another gate's changed target generally does not. Two selected carrier-packet edges commute with each other.

For scales, self-additions and any degenerate ordinary-add case, use exact rational two-gate operator equality rather than extending the simple index rule. A self-addition is multiplication by 1+a, so reject 1+a=0; reject a zero scale. Source-admitted invertibility and coefficient guards remain mandatory. Check both chronological forward products and inverse-transpose products in the independent oracle. Do not accept equality only on zero or clean inputs.

Each allowed crossing preserves the whole dirty-input scalar operator. The factor identity preserves the gathered four-gate operator. Their composition proves equality of the original and final window. An independent whole-window sparse operator check is required for retained words. The crossing log is an algebraic derivation; no intermediate gathered word is claimed to be executable with the old selected frames. Only the final factored word is executed or admitted.

## 2. Outer contacts and actual block boundaries

Let R be every raw register touched by any original window gate, including unselected gates and scales. For each r in R, pin the frame E_r at its last contact before the window and O_r at its first contact after the window. Use the trusted fixed graph's virtual alias and literal origin to identify both contacts. Record any equality obligation at O_r, including an A cut or a virtual end before a warp. The window's barrier guard prevents a register from silently changing its virtual identity.

A full chronological chain walk must reject:
- an incoming frame not contained in the next literal gate frame;
- a final window frame not contained in O_r;
- an equality exit whose actual frame differs from O_r, even at equal rank;
- a missing/repeated literal gate, changed unselected frame, or unbound outer contact.

Ordinary fixed gates after the block are upper bounds, not equality bounds. Their own later forced equality still has to be checked.

For the gathered block's four support registers, define its boundary from the final order:
- Gather-left: block entry is E_r. Block exit is the first unselected contact's fixed frame, if there is one, otherwise O_r.
- Gather-right: block entry is the last unselected contact's fixed frame, if there is one, otherwise E_r. Block exit is O_r.

More generally, the entry is the last fixed prefix contact, and the exit is the first fixed suffix contact. An equality flag transfers to the block exit only when that exit is the outside equality contact itself. When an unselected suffix exists, verify its remaining fixed chain and eventual outside equality separately.

The selected-only J1 contacts are not the new block contacts. In particular, an old unselected contact between selected gates can become the block's preceding or following bound and can make the entire block domain empty. No rank-only substitute for actual subspace containment is valid.

## 3. Whole-window invoice and a safe constant-time reduction

For each r in R, begin at E_r, visit every occurrence of r in the literal chronological window, and then visit O_r. At a monotone step F->G, pay H(dim G-dim F), where H(0)=0 and H(d)=(d/73)^(1-b) at the frozen endpoint. Sum over all registers. Each first outside successor is charged once for that register, even when one shared outside gate is the successor for multiple registers.

Use canonical operand semantics: an add visits its two operands; a scale visits only its target. A self-add can visit the same register twice in canonical order; the second visit has zero rank increment. The old add-only helper that blindly iterates gate[1:3] is not a valid general window invoice because it treats a scale's numerator as a register.

Let B_old and B_new be the resulting complete profile Counters. The scientific local delta is B_new-B_old. It is never the selected-only J1 delta. Every unchanged intervening contact remains in both chronological calculations. The full rank mass telescopes to sum_r(dim O_r-dim E_r), so exact mass equality is necessary but does not prove profile equality.

A production implementation may avoid rewalking a long window for every corner. For a fixed placement, remove the selected gates and split the fixed contacts into prefix and suffix. The new bill has the exact form

    B_new = C_fixed + B_block,

where B_block is the four-gate, four-register invoice through each actual block exit just defined. For a support register, C_fixed contains all prefix climbs and all suffix climbs after the first suffix contact, plus the outside climb if a suffix exists. The first suffix climb is already charged by B_block. When no suffix exists, B_block charges the outside climb and it must not be added again. For registers outside the block support, C_fixed includes their entire fixed chain and outside climb.

The constant's literal chains and equality obligations are checked once per placement. This decomposition is an exact accounting identity, not an approximation or a selected-only price. A direct full-window recount for retained candidates must reproduce C_fixed+B_block and B_new-B_old exactly. Native centre descents occur at the unchanged cut/section interface; no chosen window crosses that interface. Their charges, compensation, prelude and all other section charges cancel. The full canonical word audit remains authoritative; no assumed factor of two for cleanup is introduced.

## 4. Twenty-corner theorem survives, with the newly derived boundary

For a chosen orientation, carrier and inner order, write the block's support as i1,i2,j,k. Its support sequence is (j,k), (i1,j), (i2,j), (j,k), with frames X,Y1,Y2,Z. Use the actual block entries and exits from section2, not the source positions. Define

    L  = E_j join E_k
    A1 = L join E_i1
    A2 = A1 join E_i2
    D  = O_j meet O_k
    U2 = D meet O_i2
    U1 = U2 meet O_i1
    K  = A2 meet U1
    J  = A2 join U1.

Feasibility requires A1 contained in U1 and A2 contained in U2, together with X<=Y1<=Y2<=Z and the entry/exit bounds. The five actual middle-frame pairs are

    (A1,A2), (K,A2), (U1,J), (U1,U2), (A1,U2).

Combine each pair with X in {L,Y1} and Z in {Y2,D}: twenty labels, retaining duplicates.

The block tariff has all twelve terms:

    H(x-ej)+H(x-ek)
    +H(y1-e1)+H(y1-x)
    +H(y2-e2)+H(y2-y1)
    +H(z-y2)+H(z-x)
    +H(oj-z)+H(ok-z)
    +H(o1-y1)+H(o2-y2).

For fixed y1,y2, concavity puts the x,z minimum at their endpoints. The feasible middle ranks satisfy a1<=y1<=u1, a2<=y2<=u2 and y2-y1>=a2-dim K. The five listed actual frame pairs realize that polygon's vertices. Concavity therefore puts a minimum at one of the twenty labels. Exit equalities restrict the same right/top/end faces described in the frozen J1 proof; filtering by actual equality preserves the minimum of every nonempty restricted domain.

Since C_fixed and B_old are constant for this placement, minimizing the complete new window tariff minus the complete old tariff is precisely minimizing the block tariff. Thus the twenty labels are complete for each guarded deterministic placement, carrier and order with all remaining frames fixed. They do not optimize arbitrary retimings, all exterior frames or the original global DAG. A source's fixed-order optimum does not settle this changed-contact-order domain.

## 5. Analytic fixtures to be executed only under registration

All examples use coefficients1 and distinct registers i1,i2,j,k,ell. These are proofs by symbolic chain arithmetic, not executed control results.

**A strict J2 gain with a J1 touching-intervener rejection.** Let R=0, S=span(1), T=span(1,2). Give i1 and i2 entry=exit S, j/k entry R and exit T, and ell entry=exit S. The four old gates are i1+=j; i1+=k; i2+=j; i2+=k, all at S. Insert i1+=ell at S between the two target pairs. This touches the packet and is rejected by J1's disjointness rule, but commutes with every selected gate. Both gathers admit X=R, Y1=Y2=S, Z=T. The old complete profile is {1:4}; the new complete profile is {1:2,2:1}; delta H2-2H1 is strictly negative for0<1-b<1. The foreign register adds no paid climb. It must remain dirty and retain its actual scalar contribution, which is why full-window equality matters.

**Noncommuting crossings.** In the same old packet, instead insert j+=i2 between the pairs. Gather-left would cross the later i2 updates; gather-right would cross the earlier j reads. Both deterministic placements must reject with the actual crossed-pair certificate.

**A scalar-commuting gather rejected by frames.** Let S=span(1), Q=span(2), T=span(1,2). Set i1 entry=exit S, i2 entry Q and exit T, j/k entry0 and exit T, ell entry=exit S. Early i1 gates are at S; late i2 gates are at T; insert ell+=j at S between them. All needed scalar crossings commute. Gather-left nevertheless puts the final carrier frame below S because ell's fixed read is the next j contact, while Y2 must contain Q. Hence A2 is not contained in U2 and the placement is infeasible. A rank-equality or scalar-only check must not admit it.

**Omitting an intervener changes the profile without changing mass.** In F2^3 let S=span(1), T=span(1,2), U=span(1,2,4). Fix i1 at S, i2 at U, ell at T, and let j/k run0->U. Early i1 gates are at S, late i2 gates at U, and the intervening ell+=j gate is at T. The correct old profile is {1:4,2:1}, from j's three unit climbs and k's unit-plus-two climb. Deleting the intervening contact from the invoice gives {1:2,2:2}. Both have mass6, but different tariffs. This is a substantive negative control for selected-only pricing.

**Omitting outside successors creates a false gain.** In the strict-gain fixture, choose Z=S instead of T. The gate-only bill is2H1, but the two outside successor climbs add2H1 and the complete bill ties the old4H1. The implementation must detect the omitted-successor invoice.

Also retain wrong-sign/ratio/missing-undo mutants, scale and self-add crossing controls (including singularity rejection), equality-exit mutants, stale preimages, barrier crossings, and forward/dual whole-window checks. The independent small-subspace oracle from J1 verifies the twenty-corner lemma; the J2 fixtures must additionally validate the new boundary extraction and C_fixed decomposition.

## 6. Retention and admission boundary

For each retained favorable candidate: reconstruct from the pinned source, verify every crossing and the final window's forward/dual operator, check every final chronological frame chain, independently recount the complete window, and construct the whole BORROW word. Recompute its canonical paid profile, derive cleanup, preserve ordered helper endpoints/widths and fixed buffers, and require exact full-word profile delta parity and the independent all-column semantic audit.

Four gates becoming four preserves the total scalar length and all B-warp indices because the whole window remains within one barrier segment. It does not establish unchanged primitive instruction costs: transport coefficients and concrete frame paths can change native expansions or prefix bounds. A strict local moment reduction is a candidate, not a complete conditional kappa certificate. Fresh native, physical allocation, supplier and outer obligations remain. Fixed-DAG optimality, abelian closure or a generic graph incidence matrix cannot replace those checks.

Exact sign intervals that straddle zero remain unresolved. Source exclusion, empty exposed domains, timeouts and native-admission gaps retain their own protocol-specific statuses. No failed or omitted candidate may be converted into a claimed global obstruction.
