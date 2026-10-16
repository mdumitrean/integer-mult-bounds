# The two remaining correction positions

This source-level supplement extends [FRAMES.md](FRAMES.md) to the first and
middle corrective positions. It does not alter the frozen E1 domain, source,
receipts, or null. It is a proof and review document, not an execution of E2.
CubeJerry's PR1533 already studied all three corrective positions on PR589's
bit word; the attribution and primary source pins in FRAMES.md apply here.
The changed domain is Jeremy Kothe's PR2966 complex base and extra words, head
`e62d3eb9005117d82a9babcfa937ecc53237c490`.

## Exact operators and registered orders

Retain the definitions `A: i += a*j`, `B: j += b*k`, with three distinct
registers and nonzero dyadic a,b. The correction `C: i += c*k` commutes with
both A and B. It has the same target as A and shares only an unchanged source
with B; neither commutation requires a clean or zero initial register.
Consequently the four additional execution orders are

| Original order | Correction | Correction first | Correction middle |
|---|---|---|---|
| A,B | c=-ab | C,B,A | B,C,A |
| B,A | c=+ab | C,A,B | A,C,B |

These are exact scalar operator identities on arbitrary contents. The chord
sign is independent of its placement. Exact forward and inverse-transpose
matrix checks must cover each order independently. Framed feasibility is
separate: commuting scalar operators do not license moving one across a
fixed exterior frame, warp, cut, prelude, or other excluded interface.

## A formula independent of register names or chord position

Let the three new gates, in their actual execution order, have unordered
operand pairs e1,e2,e3. They are the three different edges of a triangle.
Define distinct registers

```text
x = the unique register in e1 intersect e2;  # absent from the last gate
y = the unique register in e1 intersect e3;  # absent from the middle gate
z = the unique register in e2 intersect e3.  # absent from the first gate
```

Thus e1={x,y}, e2={x,z}, e3={y,z}. This naming is geometric; it does not change
the actual scalar destinations, coefficients, or correction sign.

Use the exact fixed exterior entry and exit contacts E and O already defined
in FRAMES.md, including virtual lender aliases and exact cut/warp equality
flags. For new gate frames R,S,T the necessary inclusions are

```text
L1 = E_x join E_y;
L2 = E_x join E_y join E_z;
U2 = O_x meet O_y meet O_z;
U3 = O_y meet O_z;

L1 <= R <= S <= T <= U3;
L2 <= S <= U2.
```

The last state is S on x and T on y,z. The absence of x from the last gate is
essential; using E1's fixed register name j for every order would be wrong.
For E2's two orders derived from old AB, x=k and the last gate is A. For E2's
two orders derived from old BA, x=i and the last gate is B. The first-gate
operand join must likewise come from the actual new order.

Put r=dim R, s=dim S, t=dim T, e_q=dim E_q, o_q=dim O_q. The complete affected
chain tariff, in this notation, is always the same nine-term expression:

```text
f(r-e_x) + f(r-e_y) + f(s-e_z)
+ f(s-r) + f(t-r) + f(t-s)
+ f(o_x-s) + f(o_y-t) + f(o_z-t).
```

The first line charges each register's first contact; the second charges the
three internal chain intervals; the last charges the first unchanged exterior
successor. The chronological local-bill implementation may derive these terms
directly by following the three registers, rather than hard-coding the formula.
Each positive rank contributes one child. All rank increments telescope to
`(o_x-e_x)+(o_y-e_y)+(o_z-e_z)`, matching the original two-gate boundary mass.

For a common concave tariff f with f(0)=0, this is jointly concave in r,s,t.
An inclusion-feasible schedule exists exactly when `L2 <= U2`; then
`L1 <= L2 <= U2 <= U3`. The nested flag basis construction realizes precisely
the integer rank domain

```text
dim(L1) <= r <= s <= t <= dim(U3);
dim(L2) <= s <= dim(U2).
```

Minimize first over r, then t, then s. Concavity puts their minima at their
interval endpoints, giving the eight explicit corners

```text
S in {L2,U2}; R in {L1,S}; T in {S,U3}.
```

Each restriction to a preceding endpoint branch remains a concave function
of the remaining variables. Every corner has integral ranks and is realized
by its actual flag subspaces. All eight labels are retained even if some
actual assignments coincide. This proves completeness for the chosen order
without a solver or a sample of intermediate orientations.

An exact equality exit on x forces S=O_x. Since feasibility then requires
O_x to be contained in O_y and O_z, `U2=O_x`; this is the upper S face. An
equality exit on y or z forces T to its exit frame, which must be contained
in the other last-gate operand's exit frame. Thus `U3` equals that frame, the
upper T face. If both require equality, their exit frames must agree. The
same corner theorem therefore covers equality-constrained feasible schedules.
No equality is relaxed to a paid climb.

The BORROW accounting conclusion is unchanged: the recursive rank profile is
charged once, while the added chord and its inverse cleanup are two additional
primitive scalar instructions. The cleanup must be regenerated, compensation
and physical endpoints must remain fixed, and the complete canonical profile
delta must equal the affected-chain delta. Those facts do not replace fresh
changed-word native, supplier/fill, and outer admission.

## A control fixture for every placement

Use the geometric register labels x,y,z derived from the actual new order.
Let R=0, S=span(1), T=span(1,2), and set

```text
E_x=E_y=R, E_z=S;
O_x=S, O_y=O_z=T.
```

Give both original gates frame S. Whichever triangle edge is the correction,
the original two edges touch all three registers. The original bill has two
rank-one entry climbs and two rank-one exit climbs, hence `{1:4}`. The new
gate frames R,S,T give `{1:2,2:1}`. The mass is four in both, and the strict
power-tariff gain is `f(2)-2*f(1)<0`. Thus all four E2 orders can carry an
independent positive fixture. This is a relabeling of the known boundary
fixture in PR1533; no occurrence in the real word is inferred from it.

For every order, an equality-only mutant can give all entries zero and all
exits the same line, then require exact equality on x while selecting S=0.
Inclusion passes and equality fails. Wrong sign/magnitude, stale window,
non-dyadic coefficient, target/repeated register, hidden warp/prelude crossing,
and omitted successor/cleanup controls have the same meaning as in E1.

## What the saved E1 result does and does not imply

The immutable E1 v1 aggregate records 134 eligible pairs per provider:
65 AB and 69 BA. Each seed covers all 2,144 labels across both providers;
its saved outcome counts are 1,840 `NO_GAIN` and 304 `REJECTED_GUARD`, with
no unresolved cases and no favorable local word. Both seeds agree. The run
records 2,360.4972810319996 CPU seconds, 46.155810445547104 wall seconds and
61 workers. These are readings of stored aggregate receipts, not reruns.

L2 and U2 depend only on the three entry/exit contacts, so an actual
`L2 not contained in U2` obstruction rules out every triangle order at the
same exterior boundary. However, L1 changes with the first gate, U3 changes
with the last gate, and the S-ending register changes with the last gate's
absent operand. E1's nonnegative-cost result or an order-specific equality
rejection cannot alone exclude the two other correction positions. Its
aggregate outcome counts do not identify which geometric reason caused every
rejection, and no such additional classification is claimed here.

The existing receipts therefore justify keeping E1's null scope exact while
testing E2 as the two remaining fixed-boundary orders. If E2 also completes
with a confirmed null, the lane's two-null stop applies. No conclusion about
nonadjacent exposure, coupled edits, changed boundaries, another source word,
or a global optimum follows.
