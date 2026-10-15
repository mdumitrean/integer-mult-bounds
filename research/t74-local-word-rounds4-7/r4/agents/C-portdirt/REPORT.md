# C-portdirt (round r4): compensation-absorbed ("port-dirt") edits on the 566+554 words

**Outcome: scoped negative result, no κ change.** The semantics hold, so the relaxation is legal at the local level.
But every edit it newly admits on these words is either frame-infeasible or exactly neutral.
Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz` (#1672 blobs 76c01583 / e86142b3). Toolkit #1186 rev3 (`r3/toolkit-rev3`),
b = 0.001679754956125544. Local only: no commits, pushes or posts. Runtime about 01:53–02:30Z, at most 3 processes, peak RSS < 1 GiB.

## 1. Semantics (confirmed on the real program)

- **Who derives the compensation.** Both the unchanged auditor (`main/research/gauge44-frames-x/independent/audit_local.py`) and the
  provider's native chain (`hpe_audit_and_transport.py`: "Rebuild arbitrary-dirt compensation") derive it from the word itself.
  It is `add y k -a` for every port row y in [112,224) and helper k >= 224 of the A+cut+B map, after the precondition.
  Neither stores or pins a compensation. The harness's rev2+ rule "compensation must equal the base's" is a conservative
  guard, because the cone caps depend on the compensation.
- **Which changes it can absorb.** The auditor also requires that no compensation gate reads an entering helper
  ("nonzero entrance response") and that none touches entering or cold-end helpers ("pre-wrapper touch of residual helper").
  So a change is absorbable only if it lies in port rows x **ordinary** helper columns (240 helpers: not entering, not low-end).
  Ports can only feed ports (rule "non-target reads target"), and no tail or cleanup gate touches a port, so a change in port
  rows never spreads to other rows.
- **Demonstration** (`scripts/demo.py`, `out/demo/`). Insert `112 += 482` (482 is an ordinary helper still holding only its initial value):
  - the compensation grows from 7,208 to 7,209 gates (new gate `add 112 482 -1`), and the cone caps are unchanged;
  - exact frames give Δ = 0, certified;
  - the written-back word passes the **unchanged `audit_local.py --main`**, PASS_INDEPENDENT_EXACT_FORWARD_AND_DUAL_ENDPOINT_FRAMES_ENTRANCES_CONES,
    with compensation_gates 7209.

## 2. Structure (both words identical)

| | Count |
|---|---:|
| B gates writing a port | 921 (P+=H 661, P+=D 124, P+=P 136) |
| Port reads of pure helper dirt | 275, **all** reading entering residual helpers, so none can be deleted alone |
| B adds whose source holds pure **ordinary** dirt | **0** (all 477 pure-dirt sources involve residual helpers) |
| Exactly cancelling pairs among the 921 port reads (same propagation, opposite non-ordinary part) | 0 |

Hence there are no absorbable single deletions or coefficient changes, no absorbed re-timings across ordinary-dirt writes,
and no cancelling pair deletions. Ordinary dirt reaches the ports only inside data-carrying reads.

## 3. Families searched

**S: one delete plus one insert** (`scripts/resourcing.py`, `pdprice.py`). Delete a port read `t += c s`; insert `t += c y` in t's port
window (no read or scale of t between), with y's value equal to s's on every non-ordinary column.
- Absorbed re-timings (y = s): 3,431 placements over 14 reads, all with deletion price 0.
  An insert only adds frame constraints, and the caps are unchanged, so these **cannot gain**.
- Re-sourcings (y != s): 52,981 placements over 48 reads, with deletion prices -10,503 to -16,863. Each read has exactly
  one alternative source, often a helper holding a data register's value plus ordinary dirt.
  - Priced: 465 placements per word, including both window extremes and the original slot, plus all 968 placements of the six
    -16,863 reads on base.
  - **All infeasible**: "L not inside U at mutable vertex" at a late B vertex. The compensation does change (7,204–7,212 gates)
    and the caps do not. The same failure occurs under the base caps, so the inserted read itself breaks y's later frames.
- Extra word: identical (465/465 infeasible).

**K: multi-insert absorbed kernels** (`scripts/census.py`, `sparse.py`, `iterate.py`).
- Set-up. For each deleted port read g: the 48 above, plus B1, B3, B8, B39, B44, B1177, B1178, B1185 and B1186 from round 3.
  - Census: every individually frame-feasible insert `t += y` in t's port window on W = base - g. This uses agent B's exact
    single-insert cone test, copied unchanged as `scripts/conelu.py`, and gives about 250–285 inserts per read.
  - Absorbed exactness: Σ λ_j nonord(y_j) = nonord(c s).
- **Span test, excluding re-reads of s** (re-inserting g itself is always feasible): for **46 of 57 reads the target is outside
  the span**, so no such kernel exists for them. That covers 36 of the 48 re-sourcing reads, and B1177/B1178/B1185/B1186.
- **B933, B938, B941, B943, B946, B948** (-16,863 each):
  - With non-port sources only the target is out of span, and no family with a single port source reaches it.
    So at least two distinct port sources ("port-difference" reads) are needed.
  - CP-SAT (at most 10 terms, |λ| <= 4 in quarter steps, minimum support) plus an exact set test with minimal-conflict cuts:
    each read's first solution fails on one jointly infeasible pair of late port reads, for example (179@507, 183@511) for B933.
    After that cut CP-SAT returns **INFEASIBLE**, so there is no feasible absorbed kernel in this model.
  - Other distinct-port pairs are mostly jointly feasible (20,645 of 20,652 for B933), so the obstruction is this specific pair.
- **B1, B3, B8, B39, B44** (-4,925): 25 conflict-cut iterations each give 125 jointly feasible solutions. **All are exact with
  the compensation unchanged, and Δ = 0.**
- Extra word: the census is identical (same feasible counts and ranks for all 57 reads; same 11 reads in span).

## 4. Hosting dependence

Native chain (`r3/toolkit-rev3/native.py`) on the base word and on the demonstration word: all 5 steps PASS on both, including phases.
- `RESIDUAL-ADAPTERS.json` and `WRAPPER-CHECKS.json` are **byte-identical**.
- `LOCAL-PROGRAMS` gains 2 events per direction (24,770 → 24,772); the precondition and compensation are emitted as
  zero-frame scalar steps.
- `LOCAL-CHECKS` real_component_primitive_bound: +16 (198,890 → 198,906 forward).
- `INDEPENDENT-LOCAL-REPLAY` prefix_l1_upper: relative change about 4e-15.
- `SCALAR-FRAME-AUDIT` compensation_additions: 7,208 → 7,209.

So a changed compensation leaves the residual interfaces and the paid profile unchanged. It changes the local programs and
two finite-invoice inputs (the primitive bound and the prefix L1 bound), which have slack (prefix 1,441 of 2,048 charged bits).
Re-admission would need the native chain, which rebuilds the compensation automatically, and then PR1319's strict T74 chain
on the new provider content. The strict chain was **not run** here, because no gain arose.

## Scope and limitations

- Finite families on two fixed words in the #1186 frame model at fixed b.
- Not covered:
  - absorbed kernels that insert into registers other than t (helpers, or ports read into t later) or outside t's port window;
  - more than 10 terms;
  - |λ| > 4.
- Families S and K are complete as stated, except that S on the extra word was sampled (465 placements). The census bounds
  each read by necessary conditions; CP-SAT INFEASIBLE verdicts are proofs within the stated model only.

## Next step

The relaxation is sound and auditor-accepted, but on these words every newly admitted move dies on frames.
- **Toolkit:** add a harness option that re-derives the compensation and recomputes the caps, instead of rejecting a change,
  and checks the auditor's residual rules. That lets future searches include absorbed moves at no extra cost.
- **Untested variant:** the general projected-port-row split-key model, with inserts into any register, a cone filter and the
  oracle cost. First target: the six -16,863 reads (B933–B948), since only their port-difference route was obstructed.

## Evidence (this directory)

- `EVIDENCE.json`: all counts, statuses, spans, loop outcomes and the demonstration.
- `out/`:
  - `CLASSIFY-*.json`, `FAMILIES-*.json`, `RESOURCE-*.json`: classification and family-S enumeration;
  - `S-*.jsonl`, `S-top6-gauge44.jsonl`, `WHYINF-gauge44.json`: family-S prices and infeasibility reasons;
  - `CENSUS-*.json` (large), `SPAN-*.json`, `SPARSE*.json`, `K*-gauge44.jsonl`, `PAIRS-B*.json`, `ITER-B*.json`, `CONFLICT-B933.json`: family K;
  - `demo/`, `native-{base,demo}/`: the demonstration and native-chain outputs.
- `scripts/`: classify, families, resourcing, pick, pdprice, whyinf, census, conelu (agent B's cone test), sparse, pairs,
  iterate, conflict, demo. CP-SAT parts run with the agi venv (OR-Tools 9.15); the rest with python3 -B.
