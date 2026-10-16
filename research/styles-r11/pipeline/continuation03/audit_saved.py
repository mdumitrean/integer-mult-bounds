"""Administrative hash/receipt audit only: no scientific modules are imported."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
ROUND = PKG / "results/CONTINUATION-03"
BASE = "1d6fa4557"
SEEDS = (14051, 33073)
FAMILIES = {
    "T1": ("T1-CAP-CLOSURE", "PASS", "2a4cc6608f4d25ff7eb31150de3e604ac4a3e4d2437df38d08db4dc79cb9864e"),
    "G3": ("G3-GUARDED-TRIANGLES", "NULL", "752227cd9874ada104a967e02c0574d0a280902a7f264a9a3ee0fb2392648906"),
    "G4": ("G4-JOINT-TRIANGLES", "NULL", "486b75d92edc4f47c595f83c75af1c48dcbb7d6182e0ad86253b8184c5006175"),
}
CHECKS = Counter()
BOUND = {}


def need(value, message):
    if not value:
        raise ValueError(message)
    CHECKS["assertions"] += 1


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value, newline=True):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + ("\n" if newline else "")).encode()


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def bind(path, expected=None):
    path = path.resolve()
    need(path.is_relative_to(ROOT), "bound artifact outside repository")
    h = sha(path.read_bytes())
    if expected is not None:
        need(h == expected, "hash mismatch: " + str(path))
    BOUND[str(path.relative_to(ROOT))] = h
    CHECKS["hash_references"] += 1
    return h


def reference(ref):
    path = (ROOT if ref.get("path_base") == "repository" else PKG) / ref["path"]
    bind(path, ref["sha256"])
    raw = path.read_bytes()
    if "bytes" in ref:
        need(len(raw) == ref["bytes"], "artifact size mismatch")
    if "payload_sha256" in ref:
        need(sha(gzip.decompress(raw) if path.suffix == ".gz" else raw) == ref["payload_sha256"],
             "payload hash mismatch")
    return path


def scientific(value):
    ignored = {"seed", "cpu_seconds", "wall_seconds", "elapsed_seconds", "seconds",
               "recorded_utc", "output_dir", "schedule", "delivered_payloads"}
    if isinstance(value, list):
        return [scientific(x) for x in value]
    if isinstance(value, dict):
        return {k: scientific(v) for k, v in value.items() if k not in ignored}
    return value


def source_archive(h):
    path = ROUND / "SOURCES" / (h + ".py.gz")
    bind(path)
    need(sha(gzip.decompress(path.read_bytes())) == h, "source archive preimage mismatch")
    CHECKS["source_archive_references"] += 1


def family_audit(family, name, status, prereg_sha, original):
    directory = ROUND / name / "v1"
    prereg_path = ROUND / family / "PREREGISTRATION.json"
    bind(prereg_path, prereg_sha)
    protocol = read(prereg_path)
    need(protocol["seeds"] == list(SEEDS), "registered distinct seeds")
    pin_path = ROUND / family / "IMPLEMENTATION-PINS-v1.json"
    pins = read(pin_path)
    pin_hash = bind(pin_path)
    need(pins["preregistration_sha256"] == prereg_sha and not pins["scientific_execution_started"],
         "preexecution source freeze")
    historical = []
    for p, h in pins["sha256"].items():
        source_archive(h)
        current = sha((ROOT/p).read_bytes())
        if current != h:
            historical.append(dict(path=p, recorded_sha256=h, current_sha256=current))
    implementation_path = directory / "IMPLEMENTATION.json"
    implementation = read(implementation_path)
    ih = bind(implementation_path)
    need(implementation["preregistration_sha256"] == prereg_sha, "implementation prereg binding")
    need(implementation["implementation_pins_sha256"] == pin_hash, "implementation pre-pin binding")
    need(implementation["workers"] == 61 and implementation["parent_load_once"], "parent preparation declaration")
    manifest = implementation["script_sha256"]
    for h in manifest.values():
        source_archive(h)
    for p, h in pins["sha256"].items():
        if p in manifest:
            need(manifest[p] == h, "runtime manifest versus frozen implementation pin")
    for ref in protocol["inputs"].values():
        reference(ref)
    run_path = directory / "RUN.json"
    run = read(run_path)
    bind(run_path)
    need(run["status"] == status and run["confirmed"] and run["scientific_decision_agreement"], "run decision")
    need(run["failure"] is None and run["incomplete_phase"] is None, "completed run")
    need(run["source_implementation_sha256"] == ih, "run implementation binding")
    need(run["workers"] == 61, "run worker count")
    need(run["total_cpu_seconds"] <= protocol["resources"]["cpu_budget_seconds_family"], "family CPU budget")
    results = [read(reference(ref)) for ref in run["results"]]
    need(len(results) == 2 and sorted(r["seed"] for r in results) == list(SEEDS), "distinct seed receipts")
    refs = {}
    for result in results:
        need(result["schema_version"] == 1 and result["experiment"] == name, "RESULT schema and family")
        need(result["status"] == status and result["decision"]["verdict"] == status, "RESULT decision")
        need(result["confirmed"] and result["scientific_decision_agreement"] and result["confirmation_required"], "RESULT confirmation")
        need(result["failure"] is None and result["incomplete_phase"] is None, "RESULT no technical error")
        need(result["no_kappa_claim"] and result["prior_stopped_protocols_unchanged"], "RESULT scope")
        need(result["preregistration_sha256"] == prereg_sha and result["implementation_pins_sha256"] == pin_hash,
             "RESULT frozen protocol links")
        need(result["script_sha256"] == manifest and result["script_manifest_sha256"] == sha(encoded(manifest)),
             "RESULT archived manifest")
        need(result["inputs"] == protocol["inputs"], "RESULT exact input pins")
        attributed = {v["path"]: v for v in result["source_attribution"]}
        need(len(attributed) == 23, "original21 plus current2 source credits")
        for p, source in original.items():
            need(attributed.get(p) == dict(source, path=p), "original PINS credit altered: " + p)
            need(result["word_blob_ids"][p] == source["git_blob"], "original word blob mapping")
        provenance = result["source_provenance"]
        need(provenance["source_attribution"] == result["source_attribution"], "provenance attribution agreement")
        for credit in provenance["source_credits"]:
            p = reference(credit)
            credit_payload = read(p) if p.suffix == ".json" else p.read_text()
            need(provenance["credit_contents"][p.name] == credit_payload, "complete literal source credits")
        reference(provenance["inherited_pins"])
        reference(provenance["source_acquisition"])
        for ref in result["task_receipts"]:
            need(ref["path"] not in refs, "task assigned to more than one seed")
            refs[ref["path"]] = (ref, result["seed"])
    need(results[0]["statistics"] == results[1]["statistics"] == run["statistics"], "decision summary equality")
    need(abs(sum(r["cpu_seconds"] for r in results)-run["total_cpu_seconds"]) < 1e-8, "CPU receipt accounting")
    phases, maxima, prices, census, controls = Counter(), dict(seconds=0, peak_rss_bytes=0), [], [], []
    for ref, seed in refs.values():
        p = reference(ref)
        task = read(p)
        need(task["status"] == "OK", "pool task error or timeout")
        need(task["seconds"] <= 300 and task["peak_rss_bytes"] <= 4*2**30, "actual task time/RSS cap")
        maxima["seconds"] = max(maxima["seconds"], task["seconds"])
        maxima["peak_rss_bytes"] = max(maxima["peak_rss_bytes"], task["peak_rss_bytes"])
        row = task["result"]
        need(row["seed"] == seed, "pool task seed binding")
        phases[p.parent.name] += 1
        if p.parent.name == "price":
            prices.append(row)
        elif p.parent.name == "census":
            census.append(row)
        else:
            need(row["status"] == "PASS", "mandatory control status")
            controls.append(row)
    need(dict(phases) == run["completed_by_phase"], "all pool phase receipts counted")
    files = [p for phase in phases for p in (directory/phase).glob("task-*.json.gz")]
    need(len(files) == len(refs), "no unreferenced pool task")
    for phase, n in phases.items():
        task_path = directory/(phase.upper()+"-TASKS.json.gz")
        bind(task_path)
        specs = read(task_path)
        need(len(specs) == n, "declared versus completed task count")
        need(Counter(s["seed"] for s in specs) == Counter({seed:n//2 for seed in SEEDS}), "balanced task seeds")
    projections = []
    for p in directory.glob("*-MEMORY-PROJECTION.json"):
        bind(p)
        projection = read(p)
        need(projection["workers"] == min(120, int(projection["ram_gib"]//4)) == 61, "RAM worker rule")
        need(projection["allocated_cores"] == 128 and projection["reserved_cores"] == 8, "core reservation")
        need(projection["worker_rss_cap_gib"] == 4, "projection RSS cap")
        need(projection["projected_peak_gib"] <= projection["ram_gib"], "projected peak fits")
        projections.append(projection)
    need(len(projections) == len(phases)+1, "projection before preparation and every pool phase")
    if family == "T1":
        need(len(controls) == 2 and scientific(controls[0]) == scientific(controls[1]), "T1 full saved scientific equality")
    else:
        by_census = {(v["provider"],v["seed"]):v for v in census}
        for provider in ("base", "extra"):
            one, two = (by_census[provider,s] for s in SEEDS)
            need(one["complete"] and two["complete"] and one["candidates"] == two["candidates"]
                 and one["counts"] == two["counts"], "complete identical census both seeds")
            need(run["statistics"]["coverage"][provider]["unpriced"] == 0, "no unpriced registered candidate")
        by_price = {(v["provider"],v["candidate_id"],v["seed"]):v for v in prices}
        need(len(by_price) == len(prices), "unique priced seed/candidate keys")
        for provider in ("base", "extra"):
            candidates = by_census[provider,SEEDS[0]]["candidates"]
            for candidate in candidates:
                one, two = (by_price[provider,candidate["candidate_id"],s] for s in SEEDS)
                for key in ("status", "local_profile", "width_inventory", "ordered_widths", "moment_delta"):
                    need(one[key] == two[key], "two-seed exact scientific decision field")
                need(one["word"]["semantic_sha256"] == two["word"]["semantic_sha256"], "identical saved word both seeds")
        for row in prices:
            need(row["status"] == "NO_GAIN" and row["optimizer"]["certified"], "scoped-null classified output")
            moment = row["moment_delta"]
            need(moment["exact_profile_identity"] and moment["profile_delta"] == {}
                 and moment["lower"] == moment["upper"] == "0", "reported exact zero delta")
            p = reference(row["word"])
            raw = read(p)
            need(sha(encoded(raw, newline=False)) == row["word"]["semantic_sha256"], "candidate semantic hash")
            need(raw["report"]["local_profile"] == row["local_profile"], "saved candidate reported profile binding")
            CHECKS["candidate_artifacts"] += 1
        need(not run["statistics"]["favorable"] and not run["statistics"]["unresolved"], "no unresolved/favorable candidate under NULL")
        need(len(prices) == 2*run["statistics"]["priced_candidates"], "priced decision count")
    CHECKS["result_receipts"] += 2
    CHECKS["pool_receipts"] += len(refs)
    return dict(status=status, seeds=list(SEEDS), result_count=2, pool_tasks=dict(phases),
        resource_maxima=maxima, memory_projections=len(projections), parent_load_once=True,
        runtime_manifest_entries=len(manifest), implementation_pin_entries=len(pins["sha256"]),
        historical_current_source_differences=historical,
        total_cpu_seconds=run["total_cpu_seconds"], total_wall_seconds=run["total_wall_seconds"],
        source_attribution_count_per_result=23, original_pins_per_result=21,
        coverage=run["statistics"].get("coverage"), scientific_decision_agreement=True,
        frozen_utc=implementation["frozen_utc"], last_result_utc=max(v["recorded_utc"] for v in results))


def main():
    begin = time.process_time()
    original = read(PKG/"data/words/PINS.json")["files"]
    need(len(original) == 21, "original pin count")
    families = {f: family_audit(f,*data,original) for f,data in FAMILIES.items()}
    need(sum(v["total_cpu_seconds"] for v in families.values()) <= 14400, "round CPU budget")
    for before, after in (("T1","G3"),("G3","G4")):
        need(families[before]["last_result_utc"] < families[after]["frozen_utc"], "serialized family completion")
    for p in (ROUND/"SOURCES").glob("*.py.gz"):
        source_archive(p.name[:-6])
    root_prefix = "research/styles-r11/"
    tree = subprocess.run(["git","ls-tree","-rz",BASE,"--",root_prefix],cwd=ROOT,capture_output=True,check=True).stdout
    old_files = 0
    for item in tree.split(b"\0"):
        if not item:
            continue
        metadata, p = item.split(b"\t",1)
        mode, kind, expected = metadata.split()
        path = ROOT/p.decode()
        need(kind == b"blob" and mode in (b"100644",b"100755"), "known original file mode")
        raw = path.read_bytes()
        actual = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        need(actual == expected.decode(), "original baseline evidence changed: "+p.decode())
        old_files += 1
    changed = subprocess.run(["git","diff","--name-only",BASE],cwd=ROOT,text=True,capture_output=True,check=True).stdout.splitlines()
    untracked = subprocess.run(["git","ls-files","--others","--exclude-standard"],cwd=ROOT,text=True,capture_output=True,check=True).stdout.splitlines()
    need(all(p.startswith(root_prefix) for p in changed+untracked), "Git-visible changes outside authorized r11")
    registry = read(ROUND/"EXPERIMENTS.json")
    need(registry["no_active_experiments"], "no active experiment")
    for row in registry["experiments"]:
        family = next(f for f,data in FAMILIES.items() if data[0] == row["id"])
        need(row["status"] == families[family]["status"] and row["confirmed"]
             and row["execution"] == "COMPLETED", "registry agrees with immutable decisions")
    lane = registry["lane_status"]["constructive-word"]
    need(lane["stopped"] and lane["consecutive_confirmed_nulls"] == 2, "binding two-null lane stop")
    byte_count = sum(p.stat().st_size for p in (PKG/"results").rglob("*") if p.is_file())
    need(byte_count < 500000000, "registered global result byte cap")
    report = dict(schema_version=1, status="PASS", recorded_utc=datetime.now(timezone.utc).isoformat(),
        scope="Administrative audit of saved hashes, receipts, resources, provenance and preservation; no scientific modules, solvers, word extractors, controls or experiments executed.",
        reviewer_source_sha256=sha(Path(__file__).read_bytes()), families=families, counts=dict(CHECKS),
        unique_bound_artifacts=len(BOUND), bound_artifacts=BOUND,
        original_preservation=dict(base_commit=BASE, git_blob_verified_files=old_files,
            git_visible_changes_outside_r11=0, changed_tracked_files=len(changed), new_untracked_files=len(untracked)),
        result_bytes_at_audit=byte_count, result_bytes_cap=500000000,
        measured_experiment_cpu_seconds=sum(v["total_cpu_seconds"] for v in families.values()),
        audit_cpu_seconds=time.process_time()-begin,
        limitations=["Recorded scientific statuses and certificates were not independently re-executed; this is a byte/provenance and decision-consistency audit.",
          "T1 is fixed-graph feasibility closure; G3/G4 NULLs cover registered constructions and selected surrogate-frame outputs only. No new kappa or intrinsic physical Laplacian is certified.",
          "Historical T1/G3 runner bytes intentionally differ from current G4 runner; exact source archives, not current files, bind those runs.",
          "The all-pipeline runtime snapshot contains additional non-executed sources; inclusion alone is not a claim that every module ran.",
          "Final prose and final manifest are coordinator-owned and outside this saved-science audit; Git scope excludes ignored environment files."])
    output = ROUND/"AUDIT.json"
    with output.open("xb") as handle:
        handle.write((json.dumps(report,sort_keys=True,indent=2)+"\n").encode())
    print(json.dumps(dict(status="PASS", path=str(output.relative_to(PKG)), sha256=sha(output.read_bytes()),
                         counts=dict(CHECKS), cpu_seconds=report["audit_cpu_seconds"], original_files=old_files)))


if __name__ == "__main__":
    main()
