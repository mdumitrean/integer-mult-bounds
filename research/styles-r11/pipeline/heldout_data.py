"""Inert-data adapter for the preregistered M4 packages, PRs #2833/#2853.

Only JSON, gzip JSON and README bytes are present under data/heldout.  No
module, checker, recipe program or executable from either package is imported
or executed.  Canonical extraction and Bounds use the already pinned trusted
wordio/toolkit modules.  PASS concerns the stated frame and literal-fill
bookkeeping checks; it is not a replay of the supplier's native admission or
outer theorem proof.

Call prepare() once in the parent before pipeline/pool.py forks.  Workers call
audit_package(pr, seed).  Large data and canonical objects remain in RECORDS;
prepare() and provenance() return JSON-safe summaries only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
import gzip
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
RR = HERE.parent
PACKAGE = "research/gmx-t74-borrow43-handoff"
HEADS = {
    "2833": "e9307b48d7d1b690939935ecef0f8e524e6d92f4",
    "2853": "d01045dfb67428679618027dff552f1d032fa999",
}
AUTHORS = {"2833": "jeremykothe2", "2853": "philippeVV"}
WORD_FILES = {
    "gauge44": "new/borrow/words/BORROW-WORD-43base.json.gz",
    "extra": "new/borrow/words/BORROW-WORD-43extra.json.gz",
}
RECORDS = {}


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _profile(value):
    _need(isinstance(value, dict), "profile must be an object")
    result = {}
    for rank, count in value.items():
        r = int(rank)
        _need(str(r) == str(rank) and r > 0, "positive canonical rank key")
        _need(type(count) is int and count >= 0, "nonnegative integer profile count")
        if count:
            result[r] = count
    return dict(sorted(result.items()))


def _modules():
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import fill
    import wordio
    return fill, wordio


def _manifest(pr):
    pr = str(pr)
    _need(pr in HEADS, "unregistered held-out PR")
    directory = RR / "data/heldout" / pr
    manifest = _read(directory / "DATA-MANIFEST.json")
    fetch = _read(directory / "FETCH.json")
    _need(manifest["commit"] == fetch["selected_commit"] == HEADS[pr], "held-out commit pin")
    _need(manifest["author_login"] == fetch["metadata"]["author_login"] == AUTHORS[pr], "PR author pin")
    _need(manifest["package"] == PACKAGE, "registered package path")
    _need(manifest["fetch_sha256"] == _sha(directory / "FETCH.json"), "fetch receipt hash")
    return directory, manifest


def provenance(pr=None):
    """Held word pins and all acquired data; records.py merges the prior PINS."""
    prs = tuple(HEADS) if pr is None else (str(pr),)
    attributes = []
    files, manifests = [], []
    for number in prs:
        directory, manifest = _manifest(number)
        files.extend(deepcopy(list(manifest["files"].values())))
        for rel in WORD_FILES.values():
            pin = deepcopy(manifest["files"][rel])
            pin.update(format="BORROW-WORD", pin_key=pin["path"],
                       lineage_attribution="Retains all data/words/PINS.json source credits; see package README.md for this PR's additional credits.")
            attributes.append(pin)
        manifests.append(dict(path=str((directory / "DATA-MANIFEST.json").relative_to(RR)),
                              sha256=_sha(directory / "DATA-MANIFEST.json"),
                              commit=manifest["commit"], pr=int(number), author=manifest["author_login"],
                              fetch_sha256=manifest["fetch_sha256"],
                              preregistration_sha256=manifest["preregistration_sha256"],
                              prediction_snapshot_sha256=manifest["prediction_snapshot_sha256"]))
    return dict(source_attribution=attributes, source_files=files, manifests=manifests,
                inherited_pins=dict(path="data/words/PINS.json", sha256=_sha(RR / "data/words/PINS.json")))


def _load_package(pr):
    fill, wordio = _modules()
    directory, manifest = _manifest(pr)
    data = {}
    for rel, pin in manifest["files"].items():
        _need(rel.endswith((".json", ".json.gz", "/README.md")) or rel == "README.md", "inert file extension")
        path = (directory / "package" / rel).resolve()
        _need(path.is_relative_to((directory / "package").resolve()), "data path confinement")
        raw = path.read_bytes()
        _need(len(raw) == pin["bytes"], "source byte count: " + rel)
        _need(hashlib.sha256(raw).hexdigest() == pin["sha256"], "source SHA256: " + rel)
        _need(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == pin["git_blob"], "source Git blob: " + rel)
        _need(pin["commit"] == manifest["commit"] and pin["author_login"] == manifest["author_login"], "source commit/author: " + rel)
        if rel.endswith(".md"):
            data[rel] = raw.decode("utf-8")
        else:
            data[rel] = json.loads(gzip.decompress(raw) if rel.endswith(".gz") else raw)
    plan = data["new/PLAN.json"]
    template = data["GLOBAL-TEMPLATE.json.gz"]
    order = [tuple(x) for x in data["new/borrow-fill/ORDER.json"]]
    dispatch = {(s, r): pid for s, r, pid in data["new/borrow-fill/DISPATCH.json"]}
    literal = data["new/borrow-fill/FILL.json.gz"]
    providers = data["new/BORROW-PROVIDERS.json"]
    for s, r, pid in literal["dispatch_overrides"]:
        _need((s, r) in dispatch and pid in providers, "dispatch override coordinates/provider")
        dispatch[s, r] = pid
    words, bounds = {}, {}
    _, boundmod, _ = wordio.borrow_modules()
    for pid, rel in WORD_FILES.items():
        path = directory / "package" / rel
        pin = deepcopy(manifest["files"][rel])
        pin.update(format="BORROW-WORD", pin_key=pin["path"])
        # WordData receives the same already parsed inert word.  Bounds performs
        # its own trusted canonical replay, once per word in the parent.
        words[pid] = wordio.WordData(data[rel], pin, path)
        bounds[pid] = boundmod.Bounds(str(path))
    widths = [tuple(len(words[dispatch[call]].end[h]) - len(words[dispatch[call]].start[h])
                    for h in words[dispatch[call]].helpers) for call in order]
    profiles = [dict(words[dispatch[call]].paid) for call in order]
    attrs = [deepcopy(manifest["files"][rel]) for rel in WORD_FILES.values()]
    model = fill.FillModel(name="heldout-" + str(pr), rows=[tuple(x) for x in literal["rows"]],
                          order=order, widths=widths, local_profiles=profiles,
                          win=fill.windows(template, order),
                          family={int(c): 2 * p + plan["sides"][c] for c, p in plan["pairs"].items()},
                          expected_profile=_profile(data["PROFILE.json"]),
                          expected_mass=plan["M"] * plan["live"] - plan["deficit"],
                          sources=deepcopy(list(manifest["files"].values())), attributions=attrs,
                          source_notes=dict(profile_source="Canonical held-out word paid children plus literal fill idle remainders",
                                            order_source="new/borrow-fill/ORDER.json",
                                            dispatch_source="new/borrow-fill/DISPATCH.json plus FILL.dispatch_overrides",
                                            plan_source="new/PLAN.json", parent_load_once=True),
                          ports=112)
    return dict(pr=str(pr), directory=directory, manifest=manifest, data=data, model=model,
                words=words, bounds=bounds, dispatch=dispatch, providers=providers,
                dimension=plan["M"], wires=plan["live"], prepare_error=None)


def prepare(prs=(2833, 2853)):
    """Parent-only loading; contains no solver call and never imports PR code."""
    summary = []
    for pr in map(str, prs):
        if pr not in RECORDS:
            try:
                RECORDS[pr] = _load_package(pr)
            except Exception as exc:
                RECORDS[pr] = dict(pr=pr, prepare_error=dict(type=type(exc).__name__, message=str(exc)))
        record = RECORDS[pr]
        summary.append(dict(pr=pr, loaded=record["prepare_error"] is None,
                            prepare_error=record["prepare_error"],
                            roles=len(record["model"].rows) if "model" in record else None,
                            calls=record["model"].calls if "model" in record else None,
                            words=sorted(record.get("words", {}))))
    return dict(packages=summary, **provenance())


def _validate_binding(record):
    """Bind all active schema layers, leaving inherited executable hashes data."""
    fill, wordio = _modules()
    d, m = record["data"], record["model"]
    plan, spec, template = d["new/PLAN.json"], d["new/SPEC.json"], d["GLOBAL-TEMPLATE.json.gz"]
    providers, dispatch = record["providers"], record["dispatch"]
    g = spec["geometry"]
    _need((plan["M"], plan["live"], m.calls, g["replicas"], g["stages"], g["pairs"])
          == (73, 66304, 666, 74, 9, 4), "registered T74 geometry")
    _need(template["m"] == g["dimension"] == plan["M"], "dimension binding")
    _need(template["replica_lift"]["data_stock"] == plan["live"], "data stock binding")
    _need(template["replica_lift"]["replicas"] == plan["T"] == g["replicas"], "replica binding")
    _need(plan["K"] == g["pairs"] and plan["L"] == g["stages"], "controller binding")
    _need(d["new/borrow-fill/FILL.json.gz"]["columns"] == fill.COLUMNS, "literal fill columns")
    original_dispatch = d["new/borrow-fill/DISPATCH.json"]
    _need(len(original_dispatch) == len(dispatch) == m.calls and set(dispatch) == set(m.order), "unique complete dispatch")
    _need(set(providers) == set(record["words"]) == {"extra", "gauge44"}, "provider word coverage")
    _need(all(pid in providers for pid in dispatch.values()), "known dispatched provider")
    for name in ("PLAN.json", "new/PLAN.json"):
        p = d[name]
        _need([tuple(x) for x in p["order"]] == m.order, name + " call order")
        _need(p["M"] == plan["M"] and p["live"] == plan["live"] and p["deficit"] == plan["deficit"], name + " geometry")
        _need(p["pairs"] == plan["pairs"] and p["sides"] == plan["sides"], name + " physical families")
        _need(_profile(p["profile"]) == m.expected_profile, name + " profile")
        bytime = {row["time"]: row for row in p["per_call_widths"]}
        _need(len(bytime) == len(p["per_call_widths"]) == m.calls and set(bytime) == set(range(m.calls)), name + " width coverage")
        pc = {row["time"]: row for row in p["provider_calls"]}
        _need(len(pc) == len(p["provider_calls"]) == m.calls and set(pc) == set(range(m.calls)), name + " provider-call coverage")
        for t, call in enumerate(m.order):
            w, c = bytime[t], pc[t]
            _need((w["stage"], w["replica"]) == call == (c["stage"], c["replica"]), name + " call coordinates")
            _need(tuple(w["widths"]) == m.widths[t] and c["provider"] == dispatch[call], name + " per-call width/provider")
        windows = {f"{o},{c}": [cap, list(range(start + 1, stop + 1))] for (o, c), (cap, start, stop) in m.win.items()}
        _need(p["windows"] == windows, name + " exact literal windows")
        for pid, word in record["words"].items():
            registry = p["provider_registry"][pid]
            _need(_profile(registry["actual_paid_profile"]) == dict(word.paid), name + " provider profile")
            _need(tuple(registry["widths"]) == tuple(len(word.end[h]) - len(word.start[h]) for h in word.helpers), name + " ordered provider widths")
    _need([tuple(x) for x in spec["call_order"]] == m.order, "current SPEC order")
    _need(len(spec["dispatch"]) == m.calls and {(s, r): p for s, r, p in spec["dispatch"]} == dispatch, "current SPEC dispatch")
    _need(_profile(d["new/PROFILE.json"]) == m.expected_profile, "root/current PROFILE parity")
    ledger = d["outer/LEDGER.json"]
    _need((ledger["m"], ledger["W"]) == (plan["M"], plan["live"]), "outer ledger geometry")
    _need(_profile(ledger["profile"]) == m.expected_profile, "outer ledger profile")
    # The physical family is (replica, pair, side, port), not an individual
    # idle interval. Each sweep orders its children by physical side. The
    # controller also records a terminal sweep from level 8 to itself: its
    # two rank-zero children are absent from the paid idle-bin inventory.
    # Omit only such exact zero-increment events, never an undeclared positive
    # child. Bind every positive child to both the template inventory and PLAN.
    children, seen_children, zero_children, zero_sweeps = {}, set(), set(), []
    positive_ranks = {}
    # In this fixed T74 controller level_mask(l,s) has dimension
    # 8*(l+1) + int(s == 0), hence a sweep gains 8*(stop-start) axes.
    # This is also (M-1)/L for the already bound M=73, L=9 geometry.
    _need((plan["M"] - 1) % plan["L"] == 0, "integer controller rank scale")
    rank_scale = (plan["M"] - 1) // plan["L"]
    for event in template["execution_schedule"]:
        if event["kind"] == "idle_cover_sweep":
            _need(len(event["child_indices"]) == 2, "two physical sides per idle sweep")
            start, stop = event["from_level"], event["to_level"]
            _need(type(start) is int and type(stop) is int and -1 <= start <= stop < plan["L"], "monotone integer idle levels")
            if start == stop:
                zero_sweeps.append(dict(pair=event["pair"], children=list(event["child_indices"]),
                                       from_level=start, to_level=stop, rank_increment=0))
            for side, child in enumerate(event["child_indices"]):
                _need(child not in seen_children, "one creation event per idle child")
                seen_children.add(child)
                if start == stop:
                    zero_children.add(child)
                else:
                    children[child] = (event["pair"], side)
                    positive_ranks[child] = rank_scale * (stop - start)
    declared_children = {x["child"] for x in template["idle_children"]}
    _need(not set(children).intersection(zero_children) and set(children).union(zero_children) == seen_children,
          "disjoint complete positive/zero child partition")
    _need(set(children) == declared_children == set(map(int, plan["pairs"]))
          == set(map(int, plan["sides"])), "positive template child family coverage")
    _need(not zero_children.intersection(declared_children), "zero-increment child has no paid idle bin")
    _need(not zero_children.intersection(map(int, plan["pairs"]))
          and not zero_children.intersection(map(int, plan["sides"])), "zero-increment child has no PLAN family")
    _need(all(c not in zero_children for _, c in m.win), "zero-increment child has no fill window")
    _need(all(row[3] not in zero_children for row in m.rows), "zero-increment child has no assigned role")
    for c, (pair, side) in children.items():
        _need(plan["pairs"][str(c)] == pair and plan["sides"][str(c)] == side, "template physical pair/side")
    bins = {(x["child"], x["port"]): x for x in template["idle_children"]}
    _need(len(bins) == len(template["idle_children"]) == len(children) * m.ports, "idle port coverage")
    for c in children:
        for port in range(m.ports):
            cell = bins[c, port]
            _need(cell["replicas"] == plan["T"] and cell["rank"] == m.win[0, c][0] == positive_ranks[c], "idle rank increment/replica binding")
    _, boundmod, _ = wordio.borrow_modules()
    word_checks = []
    for pid, word in record["words"].items():
        b = record["bounds"][pid]
        widths = tuple(len(word.end[h]) - len(word.start[h]) for h in word.helpers)
        _need((word.v, word.h) == (112, 9), "registered local word geometry")
        _need(word.profile_match and dict(b.Wd.paid) == dict(word.paid), "two trusted canonical profile replays")
        _need(b.Wd.helpers == word.helpers and all(type(w) is int and w > 0 for w in widths), "active helper ordering/widths")
        _need(tuple(providers[pid]["widths"]) == widths, "canonical ordered helper widths")
        _need(_profile(providers[pid]["actual_paid_profile"]) == dict(word.paid), "canonical provider paid profile")
        _need(_profile(spec["providers"][pid]["expected_profile"]) == dict(word.paid), "current SPEC local profile")
        _need(_profile(spec["providers"][pid]["inventory"]) == dict(Counter(widths)), "current SPEC inventory")
        _need(not b.stat_bad and not b.infeasible and not b.ctrl_bad, "exact Bounds feasibility/static pins")
        _need(set(b.lo) == set(b.hi) == set(b.Wd.gateframe), "Bounds framed-gate coverage")
        for t in b.lo:
            _need(boundmod.contained(b.lo[t], b.Wd.gateframe[t]) and boundmod.contained(b.Wd.gateframe[t], b.hi[t]), "literal frame lies in exact Bounds")
        word_checks.append(dict(provider=pid, word=WORD_FILES[pid], canonical_profile=dict(word.paid),
                                width_inventory=dict(sorted(Counter(widths).items())), helpers=len(widths),
                                framed_gates=len(b.lo), exact_bounds_verified=True,
                                centre_paid=dict(word.centre_paid), profile_replays=2))
    rank_mass = (plan["M"] - 1) * plan["live"] + (9 - 1) ** 2 * m.calls
    _need(rank_mass == m.expected_mass, "independent coverage/rank-mass identity")
    return word_checks, rank_mass, dict(positive_children=sorted(children),
                                       positive_child_ranks=positive_ranks, rank_per_level=rank_scale,
                                       level_dimension_formula="8*(level+1) + int(side == 0)",
                                       zero_increment_sweeps=zero_sweeps,
                                       excluded_only_exact_zero_increments=True,
                                       zero_children_absent_from_bins_windows_and_roles=True)


def audit_package(pr, seed):
    """Deterministic literal/bookkeeping check, called by the registered pool."""
    pr = str(pr)
    out = dict(pr=int(pr), seed=int(seed), status="ERROR", complete_profile=None,
               aggregate_local_profile=None, role_width_counts=None, capacity_counts=None,
               dimension=None, wires=None, calls=None, coverage_rank_mass=None,
               distinct_local_profiles=[], stage_orientation_profiles=[], validation={},
               scope="Literal owner fill, canonical paid profiles and widths, fixed-gate Bounds; no fetched code, native admission or outer theorem replay.",
               **provenance(pr))
    try:
        _need(pr in RECORDS, "prepare() must run in the parent before pool launch")
        record = RECORDS[pr]
        _need(record["prepare_error"] is None, "parent preparation failed: " + str(record["prepare_error"]))
        fill, _ = _modules()
        checks, mass, family_binding = _validate_binding(record)
        model, data = record["model"], record["data"]
        literal = fill.audit(model)
        _need(_profile(data["CONSTRUCTION.json"]["idle"]) == literal["idle"], "CONSTRUCTION idle parity")
        _need(data["CONSTRUCTION.json"]["roles"] == literal["roles"], "CONSTRUCTION role count")
        _need(data["CONSTRUCTION.json"]["helpers_per_call"] == len(model.widths[0]) and len(set(map(len, model.widths))) == 1, "CONSTRUCTION helper count")
        _need(data["CONSTRUCTION.json"]["dispatch"] == dict(Counter(record["dispatch"].values())), "CONSTRUCTION dispatch count")
        aggregate, widths, capacities = Counter(), Counter(), Counter()
        grouped = defaultdict(Counter)
        stages = {e["stage"]: e for e in data["GLOBAL-TEMPLATE.json.gz"]["recipe"] if e["kind"] == "local"}
        pc = {x["time"]: x for x in data["new/PLAN.json"]["provider_calls"]}
        for t, (stage, replica) in enumerate(model.order):
            profile = model.local_profiles[t]
            aggregate.update(profile)
            widths.update(model.widths[t])
            orientation = "backward" if stages[stage]["reverse"] else "forward"
            _need(pc[t]["orientation"] == orientation, "stage orientation binding")
            grouped[stage, orientation, record["dispatch"][stage, replica]][tuple(sorted(profile.items()))] += 1
        for cap, _, _ in model.win.values():
            capacities[cap] += model.ports
        distinct = sorted({tuple(sorted(p.items())) for p in model.local_profiles})
        groups = [dict(stage=stage, orientation=orientation, provider=provider,
                       profiles=[dict(profile=dict(profile), calls=n) for profile, n in sorted(profiles.items())])
                  for (stage, orientation, provider), profiles in sorted(grouped.items())]
        out.update(status="PASS", complete_profile=literal["profile"],
                   aggregate_local_profile=dict(sorted(aggregate.items())),
                   role_width_counts=dict(sorted(widths.items())), capacity_counts=dict(sorted(capacities.items())),
                   dimension=record["dimension"], wires=record["wires"], calls=model.calls,
                   coverage_rank_mass=mass, distinct_local_profiles=[dict(p) for p in distinct],
                   stage_orientation_profiles=groups,
                   validation=dict(words=checks, literal_fill=literal, schema_binding_verified=True,
                                   template_family_binding=family_binding,
                                   geometry_binding="M=73; W=PLAN.live=template.replica_lift.data_stock=outer ledger W; template.live also contains inherited bank stock",
                                   inherited_root_order_matches_active=data["ORDER.json"] == data["new/borrow-fill/ORDER.json"],
                                   inherited_root_dispatch_matches_active=data["DISPATCH.json"] == data["new/borrow-fill/DISPATCH.json"],
                                   executable_program_hashes="Retained as source metadata; fetched executable/native programs are never executed by this adapter.",
                                   numerical_root="fill.audit includes a diagnostic float only; registered M4 predictions independently recompute the prescribed high-precision roots."),
                   source_claims=dict(supplier_only_kappa=data["CLAIM.json"].get("kappa_decimal"),
                                      outer_headline_kappa=data["outer/OUTER-CLAIM.json"].get("kappa"),
                                      claim_validation="Claims retained as data; exact profile reconstructed independently."))
    except Exception as exc:
        out["validation"]["error"] = dict(type=type(exc).__name__, message=str(exc))
    return out
