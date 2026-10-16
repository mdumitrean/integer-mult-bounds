**T1: confirmed exact fixed-cap closure; no kappa result.**

Seeds 14051 and 33073 both passed the frozen
[registration](PREREGISTRATION.json), with identical scientific receipts.
The immutable results are [14051](../T1-CAP-CLOSURE/v1/seed-14051/RESULT.json)
and [33073](../T1-CAP-CLOSURE/v1/seed-33073/RESULT.json). This note reviews
those saved outputs and the proof; it runs no additional experiment.

Each seed checked all 16 subspaces of F2^3, all 66 nested two-vertex floor
pairs, and all 1,024 ordered pairs of one-vertex caps: **67,584 cases**.
Of these, 8,828 were feasible and 58,756 infeasible. Forward composition,
reversed composition and simultaneous closure agreed with an independent
enumeration of every feasible labeling and its greatest element. All 2,112
single-cap idempotence checks also passed. The second seed repeats this same
finite domain; it does not double the number of distinct cases.

The real tests started from each freshly constructed graph's maximal feasible
labeling U. The registered rule selected its first 64 mutable vertices with
L<U, chose the lexicographically first domain frame of rank
max(dim L, dim U−1), and alternated those caps between two lists.

| Word | Nodes | Inclusion edges | Variable vertices | Changed vertices | Emitted vector messages | Emitting edges |
|---|---:|---:|---:|---:|---:|---:|
| PR2957 base | 7,509 | 11,925 | 886 | 64 | 11,000 | 86 |
| PR2957 extra | 7,509 | 11,925 | 886 | 64 | 11,000 | 86 |
| PR2802 base | 7,190 | 11,300 | 875 | 64 | 10,512 | 88 |

Each row holds under both seeds and all three message schedules: forward,
reverse and seeded. Comparisons used full frame assignments and full emitted
multisets, with digests retained in the receipts. Messages count individual
nonzero vectors per constraint edge, not paid rank units or processor calls.
Cap zero at node 0, whose exact floor is span(11), was rejected by both the
meet formula and every message schedule. Source literal profiles agreed
between the fresh graph and the independent canonical word reader.

The general law requires a **fixed graph**, fixed endpoint/cut/warp pins,
attained feasible floors L and upper labels U, and inclusion constraints
whose feasible labelings are closed under pointwise join and meet. For a
feasible X and fixed cap list C, K_C(X) is the greatest feasible Y≤X obeying
C. It exists by finite join closure whenever every cap contains its floor.
Every jointly capped Z≤X lies below K_C(X), then below K_D(K_C(X)); hence
K_D K_C = K_C K_D = K_(C union D), and K_C is idempotent. The reverse
topological meet formula implements this law on the tested DAGs.

In the equivalent message system, vertex v stores D_v=F_v-perp. Its final
state is the span of its initial state and all incoming constraints. It emits
every newly acquired nonzero vector exactly once to each predecessor, so its
total output is precisely D_final minus D_initial, independent of arrival
order. Emitting only a chosen basis would not establish that property.
Finite vector sets and one-time emission imply termination. The split graph
already pins warp interfaces; this is not a theorem about arbitrary dynamic
warps, changed graphs, extra non-inclusion constraints, or adaptive cap choice.

The real tests changed exactly the 64 directly capped vertices, so they did
not exercise a larger cascade through additional real vertices. Their cap
selection is a bounded implementation control. The exhaustive toy checks
and the proof supply the separate structural justification. No solver was
called, no cost-selected cap rule was tested, and U is not asserted to be a
cost optimum. Recorded graph profiles exclude fixed centre descents and
must not be read as complete supplier bills.

The orientation control starts from span(1) or span(2), both rank one, and
applies cap span(1). Rank changes are respectively 0 and −1. Thus rank alone
does not determine this operation's update. This obstructs a fixed update on
the rank projection; it does not rule out enriched abelian state models.
The separate DAG correction has arcs v→w, v→sink, w→sink and reduced matrix
[[2,0],[-1,1]], determinant 2 and critical group Z/2Z. Acyclicity alone does
not force a trivial critical group. Neither control supplies an intrinsic
physical fill Laplacian, a sandpile cost theorem, or a kappa improvement.
The prior [S2/S6 null scopes](../../M2/C-EXACTNESS.md) remain unchanged.

The executed [module](../../../pipeline/continuation03/frame_closure.py) has
SHA256 `9e64af5bfb368b2899d2f2223df6619802303a01adb8d9dd4023d2ed83810428`.
The two-task run used the configured 61-worker pool, 4.179659525 CPU seconds
and 2.554594605 wall seconds, including parent preparation. Jeremy Kothe's
PR2957 source is commit `b74b25f3ccc84c16e1a801d73b2f47e5ea764c78`;
Marius-Paul Dumitrean's PR2802 source and all inherited credits remain bound
by [PINS.json](../../../data/words/PINS.json), the
[PR2957 acquisition](../../../data/continuation-03/checkpoint/pr2957/ACQUISITION.json),
and the complete provenance in both result files. See the
[planning proof](../planning/SANDPILE.md) for the changed-word cost route and
its native-admission obligations.
