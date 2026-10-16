"""Registered exact same-call fill exchanges for CONTINUATION-01.

This is a finite residual/exchange calculation.  It assumes no sandpile
Laplacian, group, recurrence, or abelianity.  At one call, swapping two existing
physical bins preserves the used family set and both eligibility windows.
The complete literal fill is still rechecked before accepting a witness.

For widths a,b, let d=a-b and let rA,rB be old idle remainders. The new
remainders are rA+d,rB-d. Their sum is unchanged. If feasible and
d*(rA-rB+d)>0, their sum of squares strictly increases, hence this two-term
vector strictly majorizes the old one. Strict concavity of x**p, 0<p<1,
gives a strictly smaller residual moment. Local paid profiles are unchanged.
All profile ranks are below dimension 73, so their positive moment is strictly
increasing in kappa. A complete-profile root in (0,1) therefore increases.
Separate native/supplier/outer admission remains necessary for a full claim.

The parent calls prepare() once. Only pipeline/pool.py may launch c1_task().
No execution occurs on import. No fetched package code is ever imported.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import math
import os
import random
import sys
import time

PIPELINE = Path(__file__).resolve().parent.parent
RR = PIPELINE.parent
_STATE = None


def _modules():
    if str(PIPELINE) not in sys.path:
        sys.path.insert(0, str(PIPELINE))
    import fill
    import heldout_data
    return fill, heldout_data


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _artifact(path, raw):
    path = Path(path)
    if path.exists():
        _need(path.read_bytes() == raw, "refuse to replace a different candidate artifact")
    else:
        path.write_bytes(raw)
    return dict(path=str(path.relative_to(RR)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def _checkpoint(directory, value):
    temporary = directory / "CHECKPOINT.tmp.json"
    temporary.write_bytes(_json_bytes(value))
    os.replace(temporary, directory / "CHECKPOINT.json")


def prepare(pr=2853):
    """Load heavy held data and immutable lookup tables once in the parent."""
    global _STATE
    _need(str(pr) == "2853", "C1 is registered only on the pinned #2853 fill")
    fill, heldout = _modules()
    if _STATE is None:
        prepared = heldout.prepare((pr,))
        record = heldout.RECORDS[str(pr)]
        _need(record["prepare_error"] is None, "held-out parent loading failed")
        model = record["model"]
        used = Counter()
        row_widths, row_bins = [], []
        bycall = [[] for _ in range(model.calls)]
        for index, row in enumerate(model.rows):
            t, h, owner, child, port, offset = row
            width = model.widths[t][h]
            key = (owner, child, port)
            row_widths.append(width)
            row_bins.append(key)
            bycall[t].append(index)
            used[key] += width
        row_caps = tuple(model.win[owner, child][0] for owner, child, port in row_bins)
        row_residuals = tuple(cap - used[key] for cap, key in zip(row_caps, row_bins))
        source = heldout.provenance(pr)
        _STATE = dict(pr=str(pr), record=record, model=model, row_widths=tuple(row_widths),
                      row_bins=tuple(row_bins), row_caps=row_caps, row_residuals=row_residuals,
                      bycall=tuple(tuple(x) for x in bycall), source=source,
                      expected_pairs=sum(math.comb(len(x), 2) for x in bycall))
    return dict(pr=_STATE["pr"], calls=_STATE["model"].calls,
                roles=len(_STATE["model"].rows), expected_pairs=_STATE["expected_pairs"],
                parent_load_once=True, **_STATE["source"])


def _state():
    _need(_STATE is not None, "prepare() must run in the parent before pool launch")
    return _STATE


def _exchange(ra, rb, ca, cb, a, b):
    d = a - b
    na, nb = ra + d, rb - d
    feasible = 0 <= na <= ca and 0 <= nb <= cb
    half_square_gain = d * (ra - rb + d)
    return feasible and half_square_gain > 0, na, nb, 2 * half_square_gain


def _controls(model):
    fill, _ = _modules()
    baseline = fill.audit(model)
    rows = list(model.rows)
    first = 0
    t, h, owner, child, port, offset = rows[first]
    cap = model.win[owner, child][0]
    residual = _state()["row_residuals"][first]
    self_improves = _exchange(residual, residual,
                              cap, cap, model.widths[t][h], model.widths[t][h])[0]
    _need(not self_improves, "self exchange must not be improving")
    bad = list(rows)
    bad[first] = (t, h, owner, child, port, cap)
    errors = {}
    try:
        fill.audit(model, bad, require_profile=False)
    except ValueError as exc:
        errors["overcapacity"] = str(exc)
    _need(errors.get("overcapacity") == "offset capacity", "overcapacity control rejected for expected reason")
    same = next(i for i in range(first + 1, len(rows)) if rows[i][0] == t)
    bad = list(rows)
    other = list(bad[same])
    other[2:5] = [owner, child, port]
    bad[same] = tuple(other)
    try:
        fill.audit(model, bad, require_profile=False)
    except ValueError as exc:
        errors["duplicate_family"] = str(exc)
    _need(errors.get("duplicate_family") == "same-call family collision", "family control rejected for expected reason")
    return dict(status="PASS", unchanged_literal_baseline=baseline,
                no_op_improving=False, rejected_mutants=errors)


def c1_task(seed, output_dir, max_seconds=180):
    """Exhaust the registered same-call pair family; preserve selected data."""
    state = _state()
    fill, _ = _modules()
    model = state["model"]
    directory = Path(output_dir)
    if not directory.is_absolute():
        directory = RR / directory
    directory = directory.resolve()
    _need(directory.is_relative_to(RR.resolve()), "candidate output must stay inside research/styles-r11")
    directory.mkdir(parents=True, exist_ok=True)
    _need(0 < max_seconds <= 540, "internal guard must leave time under the 600-second pool timeout")
    started = time.process_time()
    controls = _controls(model)
    row_widths, caps, residuals = state["row_widths"], state["row_caps"], state["row_residuals"]
    rng = random.Random(int(seed))
    calls = list(range(model.calls))
    rng.shuffle(calls)
    counts = Counter()
    signatures = Counter()
    best, best_key, best_score = None, None, None
    completed_calls = []
    complete = True
    for t in calls:
        if time.process_time() - started > max_seconds:
            complete = False
            break
        indices = list(state["bycall"][t])
        rng.shuffle(indices)
        for position, i in enumerate(indices):
            a, ra, ca = row_widths[i], residuals[i], caps[i]
            hi = model.rows[i][1]
            for j in indices[position + 1:]:
                counts["all_pairs"] += 1
                b = row_widths[j]
                if a == b:
                    counts["equal_width_pairs"] += 1
                    continue
                counts["unequal_width_pairs"] += 1
                rb, cb = residuals[j], caps[j]
                d = a - b
                na, nb = ra + d, rb - d
                if na < 0 or na > ca or nb < 0 or nb > cb:
                    counts["infeasible_capacity_pairs"] += 1
                    continue
                counts["feasible_unequal_pairs"] += 1
                half_gain = d * (ra - rb + d)
                if half_gain <= 0:
                    counts["nonimproving_feasible_pairs"] += 1
                    continue
                counts["strictly_improving_pairs"] += 1
                signature = (min(ra, rb), max(ra, rb), min(na, nb), max(na, nb))
                signatures[signature] += 1
                hj = model.rows[j][1]
                key = (t, min(hi, hj), max(hi, hj))
                score = 2 * half_gain
                if best is None or score > best_score or (score == best_score and key < best_key):
                    best, best_key, best_score = (i, j), key, score
        completed_calls.append(t)
        if len(completed_calls) % 16 == 0 or len(completed_calls) == model.calls:
            _checkpoint(directory, dict(seed=int(seed), complete=False,
                         completed_calls=sorted(completed_calls), counts=dict(counts),
                         selected_pair=best_key, selected_square_gain=best_score,
                         elapsed_cpu_seconds=time.process_time() - started))
    complete = complete and len(completed_calls) == model.calls
    if complete:
        _need(counts["all_pairs"] == state["expected_pairs"] == 55296648,
              "complete registered 666 by choose(408,2) pair coverage")
    result = dict(seed=int(seed), baseline_pr=2853, status="EXPLORATORY" if not complete else "NULL",
                  complete=complete, expected_pairs=state["expected_pairs"], counts=dict(counts),
                  completed_calls=sorted(completed_calls), controls=controls, solver_calls=0,
                  selection="Largest integer increase in sum of squared residuals, then lexicographically smallest (call,helper,helper); no root-based selection.",
                  null_scope="Only exhaustive same-call two-role exchanges on the pinned #2853 fill.",
                  candidate=None, residual_signatures=[dict(before=list(k[:2]), after=list(k[2:]), count=n)
                                                     for k, n in sorted(signatures.items())],
                  scope="Constructive fill gain only. Complete native/supplier/outer admission remains mandatory.",
                  **state["source"])
    if best is not None:
        i, j = best
        # Canonical helper order makes the selected witness seed-independent.
        if model.rows[i][1] > model.rows[j][1]:
            i, j = j, i
        old_i, old_j = model.rows[i], model.rows[j]
        _need(old_i[0] == old_j[0], "same-call witness")
        bare = [list(row[:5]) for row in model.rows]
        bare[i][2:5], bare[j][2:5] = bare[j][2:5], bare[i][2:5]
        changed = fill.compact_rows(model, bare)
        audited = fill.audit(model, changed, require_profile=False)
        before = controls["unchanged_literal_baseline"]["profile"]
        after = audited["profile"]
        delta = {r: after.get(r, 0) - before.get(r, 0) for r in sorted(set(before) | set(after))
                 if after.get(r, 0) != before.get(r, 0)}
        ra, rb = residuals[i], residuals[j]
        good, na, nb, square_gain = _exchange(ra, rb, caps[i], caps[j], row_widths[i], row_widths[j])
        expected_delta = Counter(r for r in (na, nb) if r)
        expected_delta.subtract(r for r in (ra, rb) if r)
        expected_delta = {r: n for r, n in expected_delta.items() if n}
        _need(good and square_gain == best_score and delta == expected_delta, "selected exact residual/profile delta")
        _need(sum(r * n for r, n in delta.items()) == 0, "exact conserved rank mass")
        _need(sum(before.values()) >= 1 and all(0 < r < 73 for r in before)
              and sum(after.values()) >= 1 and all(0 < r < 73 for r in after),
              "strictly increasing complete-profile moments")
        _need(sum(r * n for r, n in before.items()) < 73 * 66304
              and sum(before.values()) > 66304 and sum(after.values()) > 66304,
              "baseline and candidate profile roots in (0,1)")
        fill_data = dict(columns=fill.COLUMNS,
                         dispatch_overrides=state["record"]["data"]["new/borrow-fill/FILL.json.gz"]["dispatch_overrides"],
                         rows=changed)
        fill_ref = _artifact(directory / "FILL.json.gz", gzip.compress(_json_bytes(fill_data), compresslevel=6, mtime=0))
        profile_ref = _artifact(directory / "PROFILE.json", _json_bytes(after))
        call = model.order[old_i[0]]
        provider = state["record"]["dispatch"][call]
        helpers = state["record"]["words"][provider].helpers
        result["candidate"] = dict(fill_artifact=fill_ref, profile_artifact=profile_ref,
                                    pair=list(best_key), provider=provider,
                                    helper_registers=[helpers[old_i[1]], helpers[old_j[1]]],
                                    row_indices=[i, j], old_rows=[list(old_i), list(old_j)],
                                    new_rows=[list(changed[i]), list(changed[j])],
                                    widths=[row_widths[i], row_widths[j]], capacities=[caps[i], caps[j]],
                                    residuals_before=[ra, rb], residuals_after=[na, nb],
                                    square_gain=square_gain, complete_profile_delta=delta,
                                    baseline_profile=before, complete_profile=after, literal_audit=audited,
                                    exact_strict_moment_decrease=True,
                                    proof="Same local profile and residual mass; feasible two-bin strict majorization. Strict concavity gives lower complete moment for every 0<kappa<1, and both complete moments strictly increase in kappa.",
                                    admission_status="PENDING separate native/supplier/outer and explicit rational separator validation")
        if complete:
            result["status"] = "PASS"
    result["cpu_seconds"] = time.process_time() - started
    _checkpoint(directory, dict(seed=int(seed), complete=complete, status=result["status"],
                 completed_calls=sorted(completed_calls), counts=dict(counts),
                 selected_pair=best_key, selected_square_gain=best_score,
                 elapsed_cpu_seconds=result["cpu_seconds"],
                 candidate_artifact=result["candidate"]["fill_artifact"] if result["candidate"] else None))
    return result
