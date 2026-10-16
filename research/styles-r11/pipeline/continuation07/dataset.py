"""Pinned historical E1/E2 data; coordinator-only preparation after registration.

No acquired source or previous experimental module is imported.  Features use
only a frozen proposal and its source-word exterior contacts.  Outcomes are
parsed separately.  All preparation/model work must be launched by the root.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import random
import time

RR = Path(__file__).resolve().parents[2]
SOURCE_HEAD = "e62d3eb9005117d82a9babcfa937ecc53237c490"
PINS_SHA = "4d62f7caf94a102ebb83feb3beca6ebeb1ab9637901ff51cc84e5beeb15d2a65"
PARENTS = {
    "base": {
        "path": "data/continuation-04/pr2966/package/rewrite/FINAL-WORD-base.json.gz",
        "sha256": "4e96cf33d2e0f85f6ff5ccc6165a6c8c0305ca0081ecaf40d72c5e1c4a13e9a5",
        "semantic_sha256": "96354832716139e4a66581ccaff6cb825908268185fbb60921ccc7cc94e63185",
    },
    "extra": {
        "path": "data/continuation-04/pr2966/package/rewrite/FINAL-WORD-extra.json.gz",
        "sha256": "440398ee0d2bfd9448be77fa0652512cb79c6ecda9ae030afc79259056f5c6dc",
        "semantic_sha256": "87cfc6f939add01e441eb830f48f6d6fb79436ca7faded768485e7ac7bbb4033",
    },
}
FAMILIES = {
    "E1": {
        "directory": "results/CONTINUATION-04/E1-ADJACENT-EXPANSIONS/v1",
        "run_sha256": "bc70b24a299c9c102da06152e51fc8eafa1e6af0fb6d770bd84d23be08f9b4c9",
        "tasks_sha256": "a8acf8514350c7c57bac72834f107bcb2d6f09cc8c96d8b47ebee458b573d8a5",
        "implementation": "pipeline/continuation04/expansions.py",
        "implementation_sha256": "5f358c2084cd39f669758cd42c077dbb93726ef79bc8a2055d7ea1f17f7f7442",
        "seeds": (22079, 51031), "rows": 2144, "tasks": 4288,
    },
    "E2": {
        "directory": "results/CONTINUATION-04/E2-OTHER-CORRECTION-POSITIONS/v1",
        "run_sha256": "7026ad525428d27014890a5f5faa77761c80f603e3c3728153c354cbd3540d53",
        "tasks_sha256": "33f233207d1582e0e855955e2962de49f608f5e6a904a9cff11b6249b2ecbfd7",
        "implementation": "pipeline/continuation04/expansions_other.py",
        "implementation_sha256": "3090a36a2b6daa7dad88fa5c3da1e6b08623a881d744ca5275b15c405055adb0",
        "seeds": (31081, 62039), "rows": 4288, "tasks": 8576,
    },
}
BOUNDARY_KEYS = {
    "register", "virtual_register", "entry", "exit", "equality_exit",
    "previous_node", "next_node", "previous_origin", "next_origin",
}
SECTIONS = ("A", "B", "restore")
ORIGINS = ("start", "A", "B", "restore", "cut", "end")
VARIANTS = tuple(itertools.product(("L2", "U2"), ("L1", "S"), ("S", "U3")))
_ROWS = None
_SUMMARY = None
_AUDIT = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _read(path, expected, size=None, payload_sha=None):
    p = RR / path
    need(p.resolve().is_relative_to(RR.resolve()), "input path confinement")
    packed = p.read_bytes()
    need(hashlib.sha256(packed).hexdigest() == expected, "input hash: " + path)
    if size is not None:
        need(len(packed) == size, "input byte count: " + path)
    data = gzip.decompress(packed) if path.endswith(".gz") else packed
    if payload_sha is not None:
        need(hashlib.sha256(data).hexdigest() == payload_sha, "payload hash: " + path)
    return json.loads(data)


def _read_ref(ref):
    return _read(ref["path"], ref["sha256"], ref.get("bytes"), ref.get("payload_sha256"))


def _rank(vectors):
    pivots = {}
    for item in vectors:
        need(type(item) is int and 0 <= item < 512, "F2^9 vector encoding")
        v = item
        while v:
            p = v.bit_length() - 1
            if p in pivots:
                v ^= pivots[p]
            else:
                pivots[p] = v
                break
    return len(pivots)


def _span(vectors):
    out = {0}
    for v in vectors:
        need(type(v) is int and 0 <= v < 512, "F2^9 vector encoding")
        out |= {x ^ v for x in tuple(out)}
    return out


def _meet_rank(*frames):
    values = _span(frames[0])
    for frame in frames[1:]:
        values.intersection_update(_span(frame))
    count = len(values)
    need(count > 0 and count & (count - 1) == 0, "intersection is a binary subspace")
    return count.bit_length() - 1


def _union_rank(*frames):
    return _rank([v for frame in frames for v in frame])


def _validate_proposal(candidate, raw, provider, experiment):
    need(candidate["provider"] == provider, "proposal provider")
    need(candidate["parent_semantic_sha256"] == PARENTS[provider]["semantic_sha256"],
         "proposal final-word semantic pin")
    section, positions = candidate["section"], candidate["positions"]
    need(section in SECTIONS and len(positions) == 2 and positions[1] == positions[0] + 1,
         "registered adjacent original pair")
    need(all(type(p) is int and 0 <= p < len(raw[section]) for p in positions),
         "source pair bounds")
    need(candidate["original_gates"] == [raw[section][p] for p in positions],
         "literal original gate preimage")
    need(digest(candidate["original_gates"]) == candidate["interval_sha256"],
         "source interval digest")
    need(tuple(candidate["variant"]) in VARIANTS, "registered frame-corner labels")
    need(candidate["orientation"] in ("AB_to_BAC_minus", "BA_to_ABC_plus"),
         "registered directed-chain orientation")
    need(candidate["chain"]["orientation"] == candidate["orientation"], "chain orientation")
    core = {k: candidate[k] for k in ("provider", "section", "positions", "orientation", "variant")}
    if experiment == "E2":
        need(candidate["placement"] in ("FIRST", "MIDDLE"), "E2 placement")
        core["placement"] = candidate["placement"]
    else:
        need("placement" not in candidate, "E1 implicit LAST placement")
    need(digest(core) == candidate["candidate_id"], "proposal identity")


def _validate_boundaries(boundaries, candidate):
    need(set(boundaries) == {"i", "j", "k"}, "three source registers")
    for name, rec in boundaries.items():
        need(set(rec) == BOUNDARY_KEYS, "source-boundary schema")
        need(rec["register"] == candidate["chain"][name], "boundary raw register")
        need(type(rec["equality_exit"]) is bool, "boundary equality flag")
        for key in ("entry", "exit"):
            need(_rank(rec[key]) == len(rec[key]), "independent source-frame basis")
        # Geometry features are defined even for nonnested source snapshots.
        # Do not impose an additional dataset-selection predicate here.
        for key in ("previous_origin", "next_origin"):
            origin = rec[key]
            need(len(origin) == 2 and origin[0] in ORIGINS, "source contact origin")
            need(origin[1] is None or type(origin[1]) is int, "source contact index")


def _context_features(candidate, boundaries):
    """Source-only geometry; no failure, post-edit frame, cost, or outcome input."""
    out = {}
    for n, gate in enumerate(candidate["original_gates"]):
        need(gate[0] == "add" and len(gate) == 6, "source addition schema")
        out[f"original_gate_{n}_frame_rank"] = _rank(gate[-1])
    for name, rec in boundaries.items():
        entry, exit_ = rec["entry"], rec["exit"]
        out[name + "_entry_rank"] = _rank(entry)
        out[name + "_exit_rank"] = _rank(exit_)
        out[name + "_rank_slack"] = _rank(exit_) - _rank(entry)
        out[name + "_equality_exit"] = int(rec["equality_exit"])
        out[name + "_entry_exit_union_rank"] = _union_rank(entry, exit_)
        out[name + "_entry_exit_intersection_rank"] = _meet_rank(entry, exit_)
        for side, key in (("previous", "previous_origin"), ("next", "next_origin")):
            section, index = rec[key]
            for value in ORIGINS:
                out[f"{name}_{side}_origin_{value}"] = int(section == value)
            same = section == candidate["section"] and index is not None
            out[f"{name}_{side}_same_section"] = int(same)
            edge = candidate["positions"][0 if side == "previous" else 1]
            out[f"{name}_{side}_contact_distance"] = abs(edge - index) if same else 0
        prev, nxt = rec["previous_origin"], rec["next_origin"]
        same = prev[0] == nxt[0] == candidate["section"] and prev[1] is not None and nxt[1] is not None
        out[name + "_exterior_same_section_span"] = nxt[1] - prev[1] if same else 0
    for a, b in itertools.combinations(("i", "j", "k"), 2):
        for side in ("entry", "exit"):
            frames = (boundaries[a][side], boundaries[b][side])
            out[f"{a}_{b}_{side}_union_rank"] = _union_rank(*frames)
            out[f"{a}_{b}_{side}_intersection_rank"] = _meet_rank(*frames)
    for a, b in itertools.permutations(("i", "j", "k"), 2):
        frames = boundaries[a]["entry"], boundaries[b]["exit"]
        out[f"{a}_entry_{b}_exit_union_rank"] = _union_rank(*frames)
        out[f"{a}_entry_{b}_exit_intersection_rank"] = _meet_rank(*frames)
    for side in ("entry", "exit"):
        frames = [boundaries[k][side] for k in ("i", "j", "k")]
        out[side + "_all_union_rank"] = _union_rank(*frames)
        out[side + "_all_intersection_rank"] = _meet_rank(*frames)
    return out


def _features(candidate, boundaries, context=None):
    out = {"context_" + key: value for key, value in
           (context if context is not None else _context_features(candidate, boundaries)).items()}
    for section in SECTIONS:
        out["proposal_section_" + section] = int(candidate["section"] == section)
    for orientation in ("AB_to_BAC_minus", "BA_to_ABC_plus"):
        out["proposal_orientation_" + orientation] = int(candidate["orientation"] == orientation)
    placement = candidate.get("placement", "TAIL")
    for value in ("FIRST", "MIDDLE", "TAIL"):
        out["proposal_placement_" + value] = int(placement == value)
    for n, (name, choices) in enumerate((("s", ("L2", "U2")), ("r", ("L1", "S")), ("t", ("S", "U3")))):
        for value in choices:
            out[f"proposal_corner_{name}_{value}"] = int(candidate["variant"][n] == value)
    for name in ("a", "b", "chord"):
        q = Fraction(candidate["chain"][name])
        out["proposal_" + name + "_sign"] = (q > 0) - (q < 0)
        out["proposal_" + name + "_abs_numerator"] = abs(q.numerator)
        out["proposal_" + name + "_denominator"] = q.denominator
    need(all(type(v) is int for v in out.values()), "finite integer covariates only")
    return dict(sorted(out.items()))


def _role_pattern(candidate, raw):
    v = int(raw["report"]["v"])
    n = 2*v + int(raw["report"]["R"])
    def role(register):
        if 0 <= register < v:
            return "data"
        if v <= register < 2*v:
            return "target"
        if 2*v <= register < n:
            return "helper"
        raise ValueError("source register role range")
    return tuple(role(candidate["chain"][name]) for name in ("i", "j", "k"))


def _labels(result):
    guards = result["guards"]
    if result["status"] == "REJECTED_GUARD":
        need(guards["predicates_passed"] is False and bool(guards["failures"]), "rejected frame certificate")
        need(result["local_profile"] is None and result["moment_delta"] is None,
             "frame rejection has no fabricated cost label")
        need(all(f["predicate"] in ("frame_inclusion", "exit_inclusion", "exit_equality")
                 for f in guards["failures"]), "only registered frame-failure labels")
        return dict(frame_legal=0, worse=None, profile_relation="unpriced_frame_rejection")
    need(result["status"] in ("NO_GAIN", "PASS_CANDIDATE", "EXPLORATORY"), "unsupported scientific status")
    need(guards["predicates_passed"] is True and not guards["failures"], "legal frame certificate")
    need(result["canonical_profile_and_boundary_delta_agree"] is True, "canonical boundary parity")
    moment = result["moment_delta"]
    if moment["exact_profile_identity"]:
        need(not moment["profile_delta"] and Fraction(moment["lower"]) == Fraction(moment["upper"]) == 0,
             "identical profile exact-zero label")
        relation, worse = "identical", 0
    elif Fraction(moment["lower"]) > 0:
        relation, worse = "worse", 1
    elif Fraction(moment["upper"]) < 0:
        relation, worse = "improving", None
    else:
        relation, worse = "unresolved_cost", None
    return dict(frame_legal=1, worse=worse, profile_relation=relation)


def prepare():
    """Call once in the registered coordinator parent; no model is fitted."""
    global _ROWS, _SUMMARY, _AUDIT
    need(_ROWS is None, "dataset preparation is once-only")
    begin = time.process_time()
    parents = {provider: _read(pin["path"], pin["sha256"]) for provider, pin in PARENTS.items()}
    for provider, raw in parents.items():
        need(digest(raw) == PARENTS[provider]["semantic_sha256"], "parent semantic hash")
    pins = _read("data/words/PINS.json", PINS_SHA)
    rows, contexts, group_boundaries, seed_seen, receipt_refs = {}, {}, {}, {}, []
    source_pins, result_refs, family_counts = {}, [], Counter()
    for experiment, family in FAMILIES.items():
        source_bytes = (RR / family["implementation"]).read_bytes()
        need(hashlib.sha256(source_bytes).hexdigest() == family["implementation_sha256"], "frozen old implementation")
        directory = family["directory"]
        run = _read(directory + "/RUN.json", family["run_sha256"])
        need(run["confirmed"] and run["failure"] is None and run["incomplete_phase"] is None,
             "complete confirmed historical run")
        receipt_index = {}
        for ref in run["results"]:
            seeded = _read_ref(ref)
            need(seeded["seed"] in family["seeds"] and seeded["confirmed"], "historical confirmation seed")
            result_refs.append(deepcopy(ref))
            for item in seeded["task_receipts"]:
                need(item["path"] not in receipt_index, "unique receipt path in seed results")
                receipt_index[item["path"]] = item
        tasks = _read(directory + "/PRICE-TASKS.json.gz", family["tasks_sha256"])
        need(len(tasks) == family["tasks"], "historical task-manifest count")
        for index, spec in enumerate(tasks):
            need(spec["kind"] == "price" and spec["seed"] in family["seeds"], "price-task identity")
            path = directory + f"/price/task-{index:05d}.json.gz"
            need(path in receipt_index, "price receipt bound by source RESULT")
            ref = receipt_index[path]
            receipt = _read_ref(ref)
            need(receipt["status"] == "OK", "historical pool task is complete")
            result, candidate, provider = receipt["result"], spec["candidate"], spec["provider"]
            need(result["candidate"] == candidate and result["candidate_id"] == candidate["candidate_id"],
                 "receipt exact proposal binding")
            need(result["provider"] == provider and result["seed"] == spec["seed"], "receipt source/seed binding")
            _validate_proposal(candidate, parents[provider], provider, experiment)
            pin = result["source_pin"]
            need(pin["pr"] == 2966 and pin["commit"] == SOURCE_HEAD
                 and pin["local_path"] == PARENTS[provider]["path"]
                 and pin["sha256"] == PARENTS[provider]["sha256"], "actual FINAL-WORD source pin")
            source_pins.setdefault(provider, deepcopy(pin))
            need(source_pins[provider] == pin, "consistent source attribution")
            boundary = result["guards"]["boundaries"]
            key = (provider, candidate["section"], tuple(candidate["positions"]))
            if key not in group_boundaries:
                _validate_boundaries(boundary, candidate)
                group_boundaries[key] = deepcopy(boundary)
                contexts[key] = _context_features(candidate, boundary)
            else:
                need(group_boundaries[key] == boundary, "source boundaries invariant across seeds, corners and placements")
            row_id = experiment + ":" + candidate["candidate_id"]
            labels = _labels(result)
            if row_id in rows:
                row = rows[row_id]
                need(row["proposal"] == candidate and row["labels"] == labels,
                     "confirmation proposal/label equality")
                need(spec["seed"] not in seed_seen[row_id], "no repeated seed within a proposal")
                row["provenance"]["receipts"].append(deepcopy(ref))
            else:
                pair_core = dict(lineage="PR2966:" + SOURCE_HEAD,
                                 section=candidate["section"], positions=candidate["positions"],
                                 register_role_pattern=_role_pattern(candidate, parents[provider]))
                pair_group = digest(pair_core)
                row = dict(row_id=row_id, experiment=experiment, candidate_id=candidate["candidate_id"],
                    provider=provider, pair_group=pair_group, pair_address=pair_core,
                    permutation_slot=(provider, candidate.get("placement", "TAIL"), tuple(candidate["variant"])),
                    permutation_stratum=(candidate["section"], candidate["orientation"],
                        *(str(Fraction(candidate["chain"][name])) for name in ("a", "b", "chord"))),
                    features=_features(candidate, boundary, contexts[key]), labels=labels,
                    proposal=deepcopy(candidate), source_boundaries=deepcopy(boundary),
                    provenance=dict(parent=deepcopy(PARENTS[provider]), source_pr=2966,
                        source_commit=SOURCE_HEAD, source_pin=deepcopy(pin),
                        original_implementation=family["implementation"],
                        original_implementation_sha256=family["implementation_sha256"],
                        task_manifest=directory + "/PRICE-TASKS.json.gz",
                        task_manifest_sha256=family["tasks_sha256"], receipts=[deepcopy(ref)]))
                rows[row_id] = row
                seed_seen[row_id] = set()
                family_counts[experiment] += 1
            seed_seen[row_id].add(spec["seed"])
            receipt_refs.append(deepcopy(ref))
    ordered = [rows[k] for k in sorted(rows)]
    need(len(ordered) == 6432 and dict(family_counts) == {"E1": 2144, "E2": 4288}, "historical unique row counts")
    for row in ordered:
        need(seed_seen[row["row_id"]] == set(FAMILIES[row["experiment"]]["seeds"]), "both historical confirmations")
        row["provenance"]["receipts"].sort(key=lambda ref: ref["path"])
    names = list(ordered[0]["features"])
    need(all(list(row["features"]) == names for row in ordered), "uniform feature schema")
    partitions = Counter(row["labels"]["profile_relation"] for row in ordered)
    need(dict(partitions) == {"identical": 5392, "worse": 128, "unpriced_frame_rejection": 912},
         "published historical label partition")
    groups = {}
    for row in ordered:
        groups.setdefault(row["pair_group"], []).append(row)
    need(len(groups) == 134, "source-pair groups, with provider twins kept together")
    for group in groups.values():
        need(len(group) == 48 and Counter(row["provider"] for row in group) == {"base": 24, "extra": 24},
             "all24 assignments of both provider twins share one group")
        slots = {row["permutation_slot"] for row in group}
        expected_slots = {(provider, placement, variant)
                          for provider in ("base", "extra")
                          for placement in ("TAIL", "MIDDLE", "FIRST") for variant in VARIANTS}
        need(slots == expected_slots and len(slots) == len(group), "uniform48 permutation slots per group")
        need(len({row["permutation_stratum"] for row in group}) == 1,
             "one section/orientation permutation stratum per pair group")
    summary = dict(status="PASS", rows=len(ordered), historical_receipts=len(receipt_refs),
        rows_by_experiment=dict(family_counts), labels=dict(partitions), frame_legal=5520,
        frame_rejected=912, pair_groups=len(groups), provider_pair_contexts=len(contexts),
        feature_names=names, features=len(names), parents=deepcopy(PARENTS),
        proposal_feature_names=[name for name in names if name.startswith("proposal_")],
        sourcecontext_names=[name for name in names if name.startswith("context_")],
        context_feature_names=[name for name in names if name.startswith("context_")],
        permutation_slots_per_group=48,
        permutation_stratum_definition=["section", "orientation", "canonical_a", "canonical_b", "canonical_chord"],
        permutation_scope="Permute complete48-slot label vectors only between pair groups in the same stratum; singleton strata stay fixed and cannot support significance",
        source_commit=SOURCE_HEAD, original_implementations=deepcopy(FAMILIES),
        source_result_refs=result_refs,
        source_attribution=[dict(deepcopy(pin), path=name) for name, pin in pins["files"].items()]
                           + list(source_pins.values()),
        receipt_manifest_sha256=digest(sorted(receipt_refs, key=lambda ref: ref["path"])),
        row_labels_sha256=digest([(row["row_id"], row["labels"]) for row in ordered]),
        features_sha256=digest([(row["row_id"], row["features"]) for row in ordered]),
        grouped_rows_sha256=digest([(row["row_id"], row["pair_group"]) for row in ordered]),
        confirmation_seed_duplicates_removed=True,
        source_boundaries_invariant_across_variants=True,
        source_context_validation_scope="Pinned historical source-only boundary receipts, exact parent/preimage binding and all-variant/seed invariance; no new frame-graph optimizer or independent boundary reconstruction",
        labels_and_features_are_separate=True,
        scope="Historical fixed-exterior frame feasibility on one PR2966 lineage; no kappa predictor or independent-lineage validation",
        cpu_seconds=time.process_time()-begin)
    _ROWS, _SUMMARY = ordered, summary
    _AUDIT = dict(boundary_contexts=len(contexts), source_results=len(result_refs),
                  row_digest=digest(ordered), source_raw=parents)
    return deepcopy(summary)


def get_rows():
    """Prepared rows, read-only by contract; workers inherit them from the parent."""
    need(_ROWS is not None, "prepare dataset once in coordinator parent")
    return _ROWS


def audit_task(seed):
    """Run registered data/feature controls through pool.py; never train a model."""
    need(_ROWS is not None, "parent-prepared dataset required")
    begin = time.process_time()
    checks = {}
    def check(name, value):
        need(bool(value), "dataset control: " + name)
        checks[name] = True
    def reject(name, fn):
        try:
            fn()
        except ValueError:
            checks[name] = True
        else:
            raise ValueError("negative dataset control accepted: " + name)
    check("dependent_binary_vectors", _rank([1, 2, 3]) == 2)
    check("oriented_equal_rank_frames", _rank([1]) == _rank([2]) == 1
          and _meet_rank([1], [2]) == 0 and _union_rank([1], [2]) == 2)
    check("triple_intersection", _meet_rank([1, 2], [1, 4], [1, 6]) == 1)
    check("empty_and_full_binary_spaces", _meet_rank([], [1]) == 0
          and _rank([1 << j for j in range(9)]) == 9)
    reject("out_of_ambient_vector", lambda: _rank([512]))
    check("unmodified_parent_loaded_rows", digest(_ROWS) == _AUDIT["row_digest"])
    order = list(range(len(_ROWS)))
    random.Random(int(seed)).shuffle(order)
    for index in order:
        row = _ROWS[index]
        check_key = list(row["features"]) == _SUMMARY["feature_names"]
        need(check_key and all(type(v) is int for v in row["features"].values()), "stable integer feature schema")
        need(len(row["provenance"]["receipts"]) == 2, "one confirmation pair per row")
    check("all_rows_schema_and_confirmations", True)
    first = _ROWS[0]
    bad = deepcopy(first["proposal"])
    bad["original_gates"][0][3] += 1
    reject("stale_original_gate_preimage", lambda: _validate_proposal(
        bad, _AUDIT["source_raw"][first["provider"]], first["provider"], first["experiment"]))
    no_outcome = deepcopy(first["proposal"])
    no_outcome["untrusted_posthoc_cost"] = "must not affect whitelisted features"
    check("nonwhitelisted_proposal_field_ignored", _features(no_outcome, first["source_boundaries"])
          == first["features"])
    bad_result = dict(status="UNKNOWN", guards={})
    reject("unsupported_status_not_a_negative", lambda: _labels(bad_result))
    check("provider_seed_placement_corner_not_split_groups", _SUMMARY["pair_groups"] == 134)
    check("published_label_partition", _SUMMARY["frame_legal"] == 5520 and _SUMMARY["frame_rejected"] == 912)
    return dict(status="PASS", seed=int(seed), controls=checks, rows=len(_ROWS),
        feature_names=_SUMMARY["feature_names"], features_sha256=_SUMMARY["features_sha256"],
        row_labels_sha256=_SUMMARY["row_labels_sha256"], grouped_rows_sha256=_SUMMARY["grouped_rows_sha256"],
        receipt_manifest_sha256=_SUMMARY["receipt_manifest_sha256"],
        source_attribution=deepcopy(_SUMMARY["source_attribution"]),
        source_result_refs=deepcopy(_SUMMARY["source_result_refs"]),
        scope=_SUMMARY["scope"], cpu_seconds=time.process_time()-begin)
