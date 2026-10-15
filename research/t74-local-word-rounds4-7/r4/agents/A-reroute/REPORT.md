# r4 / A-reroute: A-section re-routing for the 13 never-written copy-window pivots

Round r4, 2026-10-15 01:55–02:35Z. Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz` (#1672 blobs 76c01583 / e86142b3).
Toolkit: #1186 rev3 (`r3/toolkit-rev3`), b = 0.001679754956125544. Local only: no commits, pushes or posts.

**Outcome: no gain (scoped negative result), plus one structural fact that closes the A-section port route.**

## Structural fact: the A section never touches a port
In both words, no A gate reads or writes any port register 112–223 (0 of 3,451). Ports have no A vertices, and their cut frames
are empty (`target_levels` is empty; no port is a centre). All 176 `cut` gates write ports, but the cut is not in the priced
frame graph: its cost is the constant centre-descent part of the profile. With cut equality, a port's last A frame must equal
its cut frame, which is empty. So **no A gate can deliver anything to a port.** q's 8 port coordinates can only be delivered by
B/tail meets (or by changing the cut, which is outside this frame model), and r3's cap K(q) cannot be lifted by moving q's
deliveries into A. An A-section edit can change only which carriers hold q's information when B starts.

## Families searched (all exact by construction, re-checked by a whole-program rational simulation)

| Family | Scope | Exact candidates | Outcome |
|---|---|---:|---|
| A-window re-delivery: delete q's B reads, re-deliver q's B+tail column with ≤ K dyadic q-reads, at least one in A after q's last A write (q is constant there), the rest in B/tail, plus frame-free cleanup prepends on FULL-end coordinates (r3 PFS extended into A) | 13 pivots × both words, K ≤ 4, exhaustive; K = 5 on 6 pivots (150 s budget each) | 0 solutions | No exact combination exists at K ≤ 4 (no budget hit; 0.3–1.3 M search nodes per pivot). K = 5: none found, budget-limited. Extra word: identical atoms, node counts and result. Control: without the A requirement the solver finds r3's B/tail re-delivery for 439, exact, compensation unchanged, Δ = 0. |
| Carrier substitution: replace a read `t += c·q` by reads of registers whose current values sum exactly to q's value (as functions of the initial state), so the main map and compensation are unchanged | all 41 B reads of the 13 pivots, singles and pairs | 0 | No carrier exists: q's value includes its own helpers' initial values, which no other register holds in that combination. |
| A-gate commuting re-timings: move an A gate past every commuting gate on its registers (only these change chain orders) | all gates in the two pivot construction blocks A1247–A1398 and A3249–A3400 | 459 | 424 exactly neutral (Δ = 0), 35 frame-infeasible, 0 gains. |

## Step 1: delivery-forced relaxation
- **The valid per-port relaxation is r3's cap.** "q must meet each port's chain somewhere in B/tail, with its frame inside that
  chain's upper frame" only requires q's frame inside the port's latest upper frame, because upper frames grow along each chain.
  That is r3 D's cap K(q); its optimum (−40,815 to −57,112 per call left) does not close these pivots.
- **What it misses is coupling,** which the single forced-meet scan (`scripts/forcedscan.py`, 439 and 226, every B/tail slot of
  each column register, base cone caps) shows:
  - 439 (deleted word −67,933): forcing one direct meet with any one port costs back 14,775–19,700 units, at best slots B911/B912
    (ports 121/122, −53,158) and B485, B519, B910, B940–B942 (the others, −48,233). A meet with the low-helper carrier 584 is free.
  - 226 (deleted word −51,636): one port meet costs back 19,700 for every one of its 8 ports; the low-helper carrier 449 is free.
  - A meet placed after the port's last gate is infeasible for every port of 439, 444, 438 and 226 (`out/FORCEDMEET-base.json`):
    q's own later meet with its low helper (e.g. tail gate 28, `584 −= 439`) puts that helper's frame onto q's chain, and it no
    longer fits any port's hyperplane.
- So the base word's routing (q meets its free carrier and a data register, and only two ports directly) is what keeps the
  coupling cheap. Every exact re-delivery found, in r3 and here, costs back exactly the saving. The per-port relaxation does not
  prove this; a proof needs a relaxation of q's chain with carriers.

## Harness rules
None relaxed for any priced candidate. A-window candidates insert into A (outside the harness's B/tail edit model), so they were
compiled by `scripts/awin.py` and checked with my own whole-program simulation (precondition + re-derived compensation + A + cut +
B + early tail + remaining cleanup). No candidate reached pricing, so `audit_local.py` had nothing to audit. Re-timings and carrier
substitutions leave the main map and compensation identical by construction (re-checked).

## Cross-lane note (agent C's lane, not run)
For the two direct port reads of each pivot (e.g. B912 into 126 and B1225 into 186 for 439), a carrier needs only q's data part
(d50+d51+d54+d55), because the helper part reaching a port is cancelled by the re-derived compensation. That is a
compensation-absorbed carrier substitution.

## Best next step
A carrier-aware relaxation of q's chain: let q meet any carrier, and charge each port the cost of absorbing q's data span at
its arrival meet. If its optimum equals the base cost, the copy-window pivots are closed for every B/tail edit. Otherwise its
optimum names the carrier slot to build. Changing the cut gates (the only frame-free port writes) needs the auditor's
centre-descent accounting and was not attempted.

## Evidence
- `RESULTS.json`: all counts.
- `out/AWIN-{base,extra}-<q>-K4.json`, `out/AWIN-base-<q>-K5.json`: atoms, coverage, solutions and search nodes.
- `out/CARRIER-base-*.json`, `out/AMOVE-base-*.json`, `out/FORCEDSCAN-base-439-226.json`, `out/FORCEDMEET-base.json`, `out/ASLOTS-base.json`, `out/ANATOMY-base.json`, plus `out/*.log`.
- Scripts: `common.py`, `anatomy.py`, `awin.py` (A-window solver; reuses r3 D's `r2h/sx.py` and `lucore.py`), `run_awin.py`, `aslots.py`, `carrier.py`, `amove.py`, `forcedmeet.py`, `forcedscan.py`, `summarize.py`, `capped.sh`.
- Runtime: about 40 minutes of searches, at most 3 processes, peak RSS 0.2 GiB.
