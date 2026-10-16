#!/usr/bin/env python3
"""Frozen M3 families, in order, with two seeds and bounded pool execution.

Invoke with ``python -I -B .../run_m3.py FAMILY --attempt v1``.  ``all``
continues the registered sequence, reusing its completed family receipts.
Importing this file does not prepare data, run a task, or write a result.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[key] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import records as R
import pool

ORDER = ("L7-GUARD-ORDER", "L-8", "L-9", "L-10", "L-11", "L6-COST-N6")
GROWTH_ORDER = ORDER[1:]
SEEDS = (11031, 29063)
CAPS = {
    "L7-GUARD-ORDER": (300, 150, 4), "L-8": (1200, 600, 6),
    "L-9": (600, 300, 4), "L-10": (300, 150, 4),
    "L-11": (120, 60, 4), "L6-COST-N6": (600, 300, 4),
}
_GROWTH_PREPARED = False


def cpu_now():
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + child.ru_utime + child.ru_stime


def peak():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


def read(path):
    return json.loads(Path(path).read_text())


def relative(path):
    return str(Path(path).relative_to(R.PKG))


def reference(path):
    return dict(path=relative(path), sha256=R.sha256(path))


def registry_row(experiment):
    return next(x for x in read(R.PKG / "EXPERIMENTS.json")["experiments"]
                if x["id"] == experiment)


def recorded_runs(experiment, prereg_sha=None):
    """Use only explicitly registered result paths, never discover outcomes by glob."""
    row = registry_row(experiment)
    paths = [R.PKG / p for p in row.get("result_files", [])]
    runs = [read(p) for p in paths]
    if not runs:
        return row, paths, runs
    if any(r["experiment"] != experiment for r in runs):
        raise ValueError("registry/result experiment mismatch: " + experiment)
    if prereg_sha and any(r["preregistration_sha256"] != prereg_sha for r in runs):
        raise ValueError("previous M3 result belongs to a different preregistration: " + experiment)
    if set(r["seed"] for r in runs) != set(SEEDS) or len(runs) != 2:
        raise ValueError("two distinct registered seed receipts required: " + experiment)
    return row, paths, runs


def task_results(run):
    return [item["result"] for item in run["statistics"].get("tasks", [])
            if item.get("status") == "OK" and isinstance(item.get("result"), dict)]


def family_protocol(prereg, experiment):
    protocol = prereg["protocol"]
    if tuple(protocol.get("seeds", protocol.get("proposed_seeds", ()))) != SEEDS:
        raise ValueError("M3 seed enrollment differs from the frozen runner")
    sequence = protocol.get("execution_order", protocol.get("order"))
    if sequence is not None:
        sequence = tuple("L-10" if x == "L-10/S-3" else x for x in sequence)
        if sequence != ORDER:
            raise ValueError("M3 family order differs from the frozen runner")
    families = protocol["families"]
    key = "L-10/S-3" if experiment == "L-10" and "L-10" not in families else experiment
    definition = families[key]
    budget = float(definition["budget_core_minutes_total"]) * 60
    timeout = float(definition["per_seed_timeout_seconds"])
    cap_budget, cap_timeout, rss = CAPS[experiment]
    if budget <= 0 or budget > cap_budget or timeout <= 0 or timeout > cap_timeout:
        raise ValueError("family budget/timeout exceeds the source protocol: " + experiment)
    if experiment in ("L-9", "L-10") and definition["n_permutations"] != 2000:
        raise ValueError("fixed 2000-control enrollment required")
    return definition, budget, timeout, rss


def validate_sources(prereg, experiment):
    """Reject source drift before data preparation or worker launch."""
    # The coordinator froze scientific sources before this orchestration file
    # was finished. Its exact bytes are archived in every run's source manifest.
    names = {"records.py", "pool.py", "growth.py", "wordio.py"}
    if experiment == "L7-GUARD-ORDER":
        names.update(("growth_order.py", "growth_replay.py"))
    elif experiment == "L6-COST-N6":
        names.add("growth_cost.py")
    else:
        names.add("growth_m3.py")
        if experiment in ("L-8", "L-11"):
            names.add("fill.py")
        if experiment == "L-9":
            names.add("matching.py")
    frozen = prereg.get("pre_registered_script_sha256", prereg.get("script_sha256", {}))
    for name in sorted(names):
        path = R.PKG / "pipeline" / name
        key = str(path.relative_to(R.ROOT))
        if frozen.get(key) != R.sha256(path):
            raise ValueError("source is absent from, or differs from, frozen M3 preregistration: " + key)


def ensure_order(experiment, preg_sha):
    for previous in ORDER[:ORDER.index(experiment)]:
        row, _, runs = recorded_runs(previous, preg_sha)
        if row["status"] in ("planned", "running") or not runs:
            raise ValueError("finish and record both seeds before advancing: " + previous)


def deadline_check(prereg):
    value = prereg.get("hard_stop_utc", prereg["protocol"].get("hard_stop_utc"))
    origin = "explicit frozen M3 hard_stop_utc"
    if value is None:
        start = read(R.RESULTS / "M0" / "PREREGISTRATION.json")["registered_utc"]
        value = (datetime.fromisoformat(start.replace("Z", "+00:00")) + timedelta(days=14)).isoformat()
        origin = "M0 preregistration timestamp plus fourteen days (conservative fallback)"
    deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        raise ValueError("hard-stop timestamp must include a timezone")
    return dict(hard_stop_utc=deadline.isoformat(), origin=origin,
                reached=datetime.now(timezone.utc) >= deadline)


def lineage_evidence():
    row, paths, runs = recorded_runs("L-7")
    details = []
    for run in runs:
        results = task_results(run)
        result = results[0] if len(results) == 1 else {}
        replay = result.get("guarded_replay", {})
        complete = (replay.get("all_lineage_guards_proven") is True
                    and len(result.get("lineage", [])) == 5
                    and all(edge.get("complete_delta") is not None for edge in result.get("lineage", [])))
        details.append(dict(seed=run["seed"], all_lineage_guards_proven=complete,
                            unresolved=replay.get("unresolved", [])))
    return dict(all_lineage_guards_proven=len(details) == 2 and all(
                    x["all_lineage_guards_proven"] for x in details),
                results=[reference(p) for p in paths], seeds=details,
                correction_scope="L7-GUARD-ORDER does not discharge the two early compound-decomposition obligations.")


def growth_stop_check(prereg, preg_sha):
    """Evaluate only recorded outcomes; two seeds are one family, never two nulls."""
    deadline = deadline_check(prereg)
    if deadline["reached"]:
        return dict(binding=True, kind="two_week_hard_stop", reason="The frozen two-week deadline has been reached.",
                    trigger_results=[], deadline=deadline)
    stop_path = R.RESULTS / "M3" / "STOP.json"
    if stop_path.exists():
        previous = read(stop_path)
        if previous["preregistration_sha256"] != preg_sha:
            raise ValueError("M3 STOP belongs to another preregistration")
        return previous
    null_streak = []
    for experiment in GROWTH_ORDER:
        row, paths, runs = recorded_runs(experiment, preg_sha)
        if not runs or row["status"] in ("planned", "running"):
            break
        if row.get("not_run"):
            break
        if row["status"] == "NULL" and row.get("confirmed") and all(r["status"] == "NULL" for r in runs):
            null_streak.append((experiment, paths))
        else:
            null_streak = []
        if len(null_streak) == 2:
            return dict(binding=True, kind="two_consecutive_nulls", lane="B",
                reason="Two consecutive confirmed scientific NULLs in Lane B: " + " then ".join(x[0] for x in null_streak) + ". PLAN section 6 stops the lane.",
                trigger_results=[reference(p) for _, paths in null_streak for p in paths],
                skipped_items_are_not_nulls=True, deadline=deadline)
    lineage = lineage_evidence()
    row, paths, runs = recorded_runs("L-8", preg_sha)
    comparisons = []
    for run in runs:
        results = task_results(run)
        result = results[0] if len(results) == 1 else {}
        bracket = result.get("packing_cap_certified_bracket", {})
        upper_bounds = []
        if bracket.get("lower_certified"):
            lower = Decimal(bracket["lo"])
            for ceiling in result.get("fixed_inventory", []):
                if ceiling.get("model") == "2802" and ceiling.get("status") == "PASS":
                    upper_bounds.append(("fixed #2802 inventory", ceiling["certified_ceiling"]))
            integral = result.get("integral_rank48_certified_bracket", {})
            if integral.get("upper_certified"):
                upper_bounds.append(("fixed #2802 local profile, integral rank48", integral["hi"]))
            upper_bounds.extend(("helper removal k=" + str(x["k_removed"]), x["ceiling"])
                                for x in result.get("helper_removal_envelope", []) if x.get("rejected"))
            checks = [dict(class_name=name, certified_upper=value,
                           tighter_than_packing_lower=Decimal(value) < lower) for name, value in upper_bounds]
        else:
            checks = []
        comparisons.append(dict(seed=run["seed"], all_requested_certificates_valid=run["status"] == "PASS",
                                certified_comparisons=checks,
                                any_certified_tighter=any(x["tighter_than_packing_lower"] for x in checks)))
    binding = (lineage["all_lineage_guards_proven"] and len(comparisons) == 2
               and all(x["all_requested_certificates_valid"] and x["certified_comparisons"]
                       and not x["any_certified_tighter"] for x in comparisons))
    return dict(binding=binding, kind="growth_bookkeeping_stop" if binding else "no_binding_growth_stop",
                lane="B", lineage=lineage, ceiling_comparisons=comparisons, deadline=deadline,
                reason="Every lineage guard is proven and no certified ceiling tightens the packing cap." if binding
                    else "The registered growth-stop conjunction is not established by the retained evidence.",
                trigger_results=[reference(p) for p in paths] if binding else [])


def saved_s2_control():
    """Reuse the same pinned base-word control at its original endpoint and scope."""
    import growth as G
    import wordio
    path, pin = G.resolve_word("2802")
    endpoint = read(R.RESULTS / "M2" / "PREREGISTRATION.json")["protocol"]["S2"]["endpoint"]
    paths = [R.RESULTS / "S-2" / "v1" / ("seed-" + str(seed)) / "RESULT.json" for seed in SEEDS]
    candidates = []
    for seed, result_path in zip(SEEDS, paths):
        result = read(result_path)
        if result["experiment"] != "S-2" or result["seed"] != seed:
            raise ValueError("saved S2 receipt identity mismatch")
        if result["preregistration_sha256"] != R.sha256(R.RESULTS / "M2" / "PREREGISTRATION.json"):
            raise ValueError("saved S2 receipt preregistration mismatch")
        entries = [x for x in result["statistics"]["preparation"]["words"]
                   if x["word"]["sha256"] == pin["sha256"] and x["word"]["path"] == str(path.relative_to(R.ROOT))]
        if len(entries) != 1:
            raise ValueError("saved S2 control does not identify the exact #2802 base word")
        item = result["statistics"]["reference_controls"][str(entries[0]["index"])]
        control = item.get("result", {})
        if not (item["status"] == "OK" and control.get("certified")
                and control.get("integer_surrogate_certified") and control.get("endpoint") == endpoint):
            raise ValueError("saved S2 control is not certified in the requested scope")
        candidates.append(control)
    if candidates[0] != candidates[1]:
        raise ValueError("S2 seed receipts disagree about their shared deterministic control")
    word = wordio.load(path)
    if {int(k): v for k, v in candidates[0]["literal_profile"].items()} != dict(word.paid):
        raise ValueError("saved S2 literal profile differs from the exact pinned word")
    meta = dict(result_files=[reference(p) for p in paths], word=dict(pin), endpoint=endpoint,
                reused=True, new_solver_calls=0,
                source_script_sha256=read(paths[0])["script_sha256"],
                scope="Original exact integer-surrogate optimum and rational toolkit-cost interval only. No unique true-optimum profile or nonlinear global-root optimum is inferred.")
    return candidates[0], meta, path


def prior_p3_controls():
    """Log why the registered independent per-seed LP checks are distinct runs."""
    result_path = R.RESULTS / "P-3" / "v2" / "seed-11031" / "RESULT.json"
    result = read(result_path)
    source = str((R.PKG / "pipeline/growth_m3.py").relative_to(R.ROOT))
    old_sha = result["script_sha256"].get(source)
    current_sha = R.sha256(R.PKG / "pipeline/growth_m3.py")
    controls = []
    for index in range(3):
        path = R.RESULTS / "P-3" / "v2" / "controls" / ("task-%05d.json" % index)
        saved = read(path)
        control = saved.get("result", {})
        controls.append(dict(result_file=reference(path), model=control.get("model"),
            saved_status=saved["status"], saved_certificate_kind=control.get("certificate_kind"),
            saved_source_files=control.get("source_files"),
            saved_local_profile_source=control.get("local_profile_source"),
            exact_same_module_sha=old_sha == current_sha, reused=False,
            reason="#1672 uses the explicitly registered held-word overlay in M3; P3 used inherited provider metadata."
                if control.get("model") == "1672" else
                "The frozen M3 source differs from P3. Each seed independently reruns the registered LP and rational dual verification; the original control is retained and no repetition is hidden."))
    return dict(prior_result=reference(result_path), prior_module_sha256=old_sha,
                current_module_sha256=current_sha, controls=controls,
                registered_new_solver_calls_per_seed=3, registered_new_solver_calls_total=6,
                repeated_deterministic_controls_explicit=True)


def prepare(experiment, definition):
    global _GROWTH_PREPARED
    if experiment == "L7-GUARD-ORDER":
        import growth_order
        return growth_order.task, growth_order.prepare()
    if experiment == "L6-COST-N6":
        import growth_cost
        return growth_cost.task, growth_cost.prepare()
    import growth_m3 as G
    metadata = {}
    if experiment in ("L-8", "L-11"):
        names = tuple(name for name in ("2802", "2751", "1672") if name not in G._MODELS)
        metadata["models"] = G.prepare(fill_names=names)
        metadata["newly_loaded_models"] = list(names)
        metadata["model_sources"] = {name: dict(source_files=model.sources, attribution=model.attributions)
                                     for name, model in G._MODELS.items()}
        _GROWTH_PREPARED = True
    elif not _GROWTH_PREPARED:
        metadata["models"] = G.prepare(fill_names=())
        _GROWTH_PREPARED = True
    if experiment == "L-8":
        metadata["prior_p3_controls"] = prior_p3_controls()
    if experiment == "L-9":
        import matching
        optimum, reuse, path = saved_s2_control()
        G.prepare(fill_names=(), optima={"2802": optimum, str(path): optimum})
        bounds = matching.get_bounds(str(path.resolve()))
        metadata.update(saved_s2_control=reuse,
                        bounds_parent_loaded=dict(word=str(path.relative_to(R.ROOT)),
                                                  mutable_gates=len(bounds.lo)))
    if experiment == "L-10":
        if tuple(definition["word_keys"]) != G.L10_KEYS:
            raise ValueError("L10 word enrollment differs from the frozen implementation")
        metadata["lane_scope"] = "Lane B only; the stopped Lane C S3 family is not relaunched or counted again."
    return G.task, metadata


def s3_bookkeeping(prereg_sha, directory):
    stop_path = R.RESULTS / "M2" / "STOP.json"
    stop = read(stop_path)
    if stop.get("lane") != "C" or not stop.get("skipped_items_are_not_nulls"):
        raise ValueError("expected the recorded Lane C stop before M3")
    for experiment in ("S-6", "S-2"):
        row, _, runs = recorded_runs(experiment)
        if row["status"] != "NULL" or not row.get("confirmed") or any(r["status"] != "NULL" for r in runs):
            raise ValueError("Lane C stop trigger is not confirmed: " + experiment)
    record = dict(item="S-3", lane="C", not_run=True, counted_as_new_family=False,
                  counted_as_null=False, reason=stop["reason"], stop_source=reference(stop_path),
                  shared_family="L-10/S-3", permitted_execution="L-10 in Lane B only",
                  reuse_scope="The Lane B output may be referenced descriptively in the hand-back. It is not another Lane C experiment or a second confirmation.",
                  preregistration_sha256=prereg_sha, source_attribution=R.provenance())
    R.write_json(directory / "S3-BOOKKEEPING.json", record, immutable=True)
    return record


def stopped_run(experiment, attempt, prereg, stop):
    scripts = R.source_manifest()
    paths = []
    for seed in SEEDS:
        paths.append(R.run_record(experiment, "M3", seed, "EXPLORATORY",
            dict(not_run=True, skip_reason=stop["reason"], binding_stop=stop), n=0,
            null=dict(model="not run: binding registered stop", mean=None, sd=None, empirical_p=None, q=None),
            run_id=attempt + "/seed-" + str(seed), scripts=scripts,
            decision=dict(verdict="EXPLORATORY", not_run=True, skip_reason=stop["reason"])))
    R.confirm(experiment, paths)
    R.registry_update(experiment, "EXPLORATORY", not_run=True, skip_reason=stop["reason"],
                      stop_trigger_results=stop.get("trigger_results", []))
    print(json.dumps(dict(experiment=experiment, status="EXPLORATORY", not_run=True,
                          reason=stop["reason"])), flush=True)
    return "EXPLORATORY"


def save_binding_stop(check, prereg_sha):
    if check["binding"] and not (R.RESULTS / "M3" / "STOP.json").exists():
        R.write_json(R.RESULTS / "M3" / "STOP.json",
            dict(check, preregistration_sha256=prereg_sha, recorded_utc=R.utcnow(),
                 skipped_items_are_not_nulls=True), immutable=True)


def run_family(experiment, attempt):
    preg_path, experiment_definition = R.preregistration("M3", experiment)
    prereg, preg_sha = read(preg_path), R.sha256(preg_path)
    if prereg.get("state") != "FROZEN":
        raise ValueError("M3 preregistration must be frozen before any preparation")
    definition, budget, timeout, rss = family_protocol(prereg, experiment)
    validate_sources(prereg, experiment)
    ensure_order(experiment, preg_sha)
    directory = R.RESULTS / experiment / attempt
    if directory.exists():
        raise FileExistsError("attempt already has artifacts; no overwrite or automatic retry: " + str(directory))
    stop = growth_stop_check(prereg, preg_sha)
    if stop["binding"]:
        save_binding_stop(stop, preg_sha)
        return stopped_run(experiment, attempt, prereg, stop)
    started, c0 = time.monotonic(), cpu_now()
    scripts = R.source_manifest()
    R.registry_update(experiment, "running", attempt=attempt, not_run=False,
                      preregistration_sha256=preg_sha)
    done, failure, prep = {}, None, {}
    specs = [dict(experiment=experiment, seed=seed, n_permutations=definition["n_permutations"])
             for seed in SEEDS]
    if experiment == "L-10":
        for spec in specs:
            spec["word_keys"] = definition["word_keys"]
    if experiment == "L6-COST-N6":
        repetitions = definition["full_protocol"]["timing"]["dot_repetitions_per_row"]
        if repetitions != 1024:
            raise ValueError("N6 fixed timing repetition count changed")
        for spec in specs:
            spec["timing_repeats"] = repetitions
    projection, launched, pool_limit = None, False, None

    def checkpoint(index, item):
        done[index] = item
        R.write_json(directory / "checkpoints" / ("task-%03d.json" % index),
                     dict(spec=specs[index], **item), immutable=True)
        print(json.dumps(dict(experiment=experiment, seed=specs[index]["seed"],
                              completed=len(done), total=len(specs), status=item["status"],
                              family_cpu_seconds_so_far=cpu_now() - c0)), flush=True)

    try:
        target, metadata = prepare(experiment, definition)
        prep = dict(metadata=metadata, cpu_seconds=cpu_now() - c0, peak_rss_bytes=peak(),
                    parent_objects_loaded_once=True)
        if experiment == "L-10":
            prep["sandpile_shared_family"] = s3_bookkeeping(preg_sha, directory)
        R.write_json(directory / "PREPARATION.json", prep, immutable=True)
        if deadline_check(prereg)["reached"]:
            raise pool.PoolCpuBudgetExceeded("two-week hard stop reached during parent preparation")
        pool_limit = budget - (cpu_now() - c0)
        if pool_limit <= 0:
            raise pool.PoolCpuBudgetExceeded("registered family CPU budget exhausted during parent preparation")
        workers = pool.worker_count()
        projection = pool.project_memory(workers, rss_gib=rss, working_set_gib=1.0)
        R.write_json(directory / "MEMORY-PROJECTION.json", projection, immutable=True)
        R.write_json(directory / "LAUNCH.json",
            dict(specs=specs, worker_count=workers, timeout_seconds=timeout, rss_cap_gib=rss,
                 family_cpu_budget_seconds=budget, live_pool_cpu_budget_seconds=pool_limit,
                 no_internal_pools=True, no_retries=True, memory_projection=projection,
                 solver_policy="L8: three sequential LP calls per seed, each at most 300 seconds; no solver inside a permutation loop."),
            immutable=True)
        launched = True
        pool.run_pool(target, [(spec,) for spec in specs], workers=workers, timeout=timeout,
                      rss_gib=rss, working_set_gib=1.0, on_result=checkpoint,
                      cpu_budget_seconds=pool_limit)
    except BaseException as exc:
        failure = dict(kind=type(exc).__name__, budget_or_deadline=isinstance(exc, pool.PoolCpuBudgetExceeded),
                       message=str(exc), traceback=traceback.format_exc()[-6000:])
        R.write_json(directory / "FAILURE.json", failure, immutable=True)
    total_cpu, wall = cpu_now() - c0, time.monotonic() - started
    receipts = []
    for index, seed in enumerate(SEEDS):
        item = done.get(index)
        selected = [dict(spec=specs[index], **item)] if item is not None else []
        if item is not None:
            status = item["status"] if item["status"] != "OK" else item["result"].get("status", "ERROR")
        else:
            status = "TIMEOUT" if failure and failure["budget_or_deadline"] else "ERROR"
        if status not in R.STATUSES:
            status = "ERROR"
        result = item.get("result", {}) if item and item["status"] == "OK" else {}
        solver_calls = sum(x.get("solver_calls", 0) for x in result.get("fixed_inventory", []))
        n = result.get("n_permutations", 0)
        null_model = ("independent uniform life/slot pairs; necessary time/dimension guards" if experiment == "L-9"
                      else "uniform ordered positive helper compositions at fixed width/part count; nine-word BH family" if experiment == "L-10"
                      else "none: exact fixed-input audit or numerical calibration")
        stats = dict(tasks=selected, preparation=prep, stopped=failure, launched=launched,
                     total_family_cpu_seconds=total_cpu, family_cpu_budget_seconds=budget,
                     live_pool_cpu_budget_seconds=pool_limit, memory_projection=projection,
                     completed_seed_tasks=len(done), prelaunch_stop_check=stop,
                     solver_accounting=dict(completed_result_calls=solver_calls,
                         expected_calls_this_seed=3 if experiment == "L-8" else 0,
                         interrupted_task_call_count_unknown=item is None and launched and experiment == "L-8",
                         all_repeats_logged=True))
        receipts.append(R.run_record(experiment, "M3", seed, status, stats, n=n,
            null=dict(model=null_model, mean=None, sd=None, empirical_p=None, q=None,
                      detail="Per-word/control summaries and registered q-values are retained inside tasks."),
            wall_seconds=wall, cpu_seconds=total_cpu / 2,
            peak_rss_bytes=max(peak(), (item or {}).get("peak_rss_bytes") or 0),
            run_id=attempt + "/seed-" + str(seed), scripts=scripts,
            decision=dict(verdict=status, pass_bar=experiment_definition.get("pass_bar", definition.get("pass_bar")),
                          task_decision=result.get("decision"), pattern_claim=False,
                          scope=definition.get("scope")),
            additional=dict(cpu_allocation="Measured family CPU through pool collection is divided equally between the two seed receipts; individual task CPU is retained. Final receipt serialization is outside that timing window.")))
    status = R.confirm(experiment, receipts)
    check = growth_stop_check(prereg, preg_sha)
    R.write_json(directory / "STOP-CHECK.json", check, immutable=True)
    save_binding_stop(check, preg_sha)
    print(json.dumps(dict(experiment=experiment, status=status, family_cpu_seconds=total_cpu,
                          growth_lane_stopped=check["binding"])), flush=True)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=("all",) + ORDER)
    parser.add_argument("--attempt", default="v1")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.attempt):
        parser.error("attempt must be one simple directory name")
    if not sys.flags.isolated:
        parser.error("run this research runner with Python -I -B")
    os.chdir(R.ROOT)
    if args.experiment != "all":
        run_family(args.experiment, args.attempt)
        return
    preg_sha = R.sha256(R.RESULTS / "M3" / "PREREGISTRATION.json")
    for experiment in ORDER:
        row, _, runs = recorded_runs(experiment, preg_sha)
        if runs and row["status"] not in ("planned", "running"):
            print(json.dumps(dict(experiment=experiment, status=row["status"],
                                  action="reuse completed registered family; no repeat")), flush=True)
            continue
        run_family(experiment, args.attempt)


if __name__ == "__main__":
    main()
