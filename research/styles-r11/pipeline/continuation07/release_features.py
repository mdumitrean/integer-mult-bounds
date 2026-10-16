"""Paired-release structural measurements; no outcome enters a predictor.

Only trusted r11 readers are imported.  Acquired release artifacts are JSON data.
The grammar is a finite binary straight-line description, not an inferred
parametric L-system.  The incidence matrix below is the actual frame-constraint
DAG incidence operator, not a physical sandpile Laplacian.  No N2 comparison,
pattern claim, intrinsic toppling law, or complete packing analysis is implied.
Preparation and tasks are scientific work: the registered runner alone calls
them, and all tasks run through the common pool.
"""
from __future__ import annotations

import copy
import difflib
import gzip
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

RR = Path(__file__).resolve().parents[2]
PIPE = RR / "pipeline"
TRUSTED = {
    "wordio": (PIPE / "wordio.py", "a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4"),
    "measures": (PIPE / "measures.py", "ec7fd2264129b922f8988098d41ebc9200f742aad92a060b7b54af191fa7bf3a"),
    "fixed_graph": (PIPE / "continuation04/expansions.py", "5f358c2084cd39f669758cd42c077dbb93726ef79bc8a2055d7ea1f17f7f7442"),
}
SECTIONS = ("A", "B", "restore")
ROLES = ("P", "T", "C", "H", "L", "F", "X", "BUFFER", "OTHER")
STREAM_MEASURES = ("events", "vocabulary", "lz76", "lz78", "repair_size",
                   "repair_rules", "repair_axiom", "H1", "H6",
                   "repeat2_distinct", "repeat2_occurrences", "repeat3_distinct",
                   "repeat3_occurrences", "repeat4_distinct", "repeat4_occurrences")
GRAPH_MEASURES = ("vertices", "arcs", "alias_registers", "components", "incidence_rank",
                  "cycle_nullity", "max_chain_length", "max_depth", "branch_vertices",
                  "merge_vertices", "equality_arcs")
SCALAR_MEASURES = tuple(f"{sec}_{kind}" for sec in SECTIONS
                        for kind in ("events", "add", "scale", "warp")) + (
    "coefficient_negative", "coefficient_nonunit", "live_registers", "helpers") + tuple(
    f"role_{role}_contacts" for role in ROLES)
EDIT_MEASURES = ("scalar_insertions", "scalar_deletions", "scalar_replacements",
                 "frame_changed_on_matched_gates", "start_changed_registers",
                 "end_changed_registers", "cut_changed_registers")
FEATURE_NAMES = tuple(
    [f"delta_{alphabet}_{name}" for alphabet in ("op", "role") for name in STREAM_MEASURES]
    + [f"delta_scalar_{name}" for name in SCALAR_MEASURES]
    + [f"delta_graph_{name}" for name in GRAPH_MEASURES]
    + [f"edit_{name}" for name in EDIT_MEASURES])
_MODULES = {}
_STATE = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def _normal(obj):
    if isinstance(obj, dict):
        return {str(k): _normal(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normal(v) for v in obj]
    return obj


def digest(obj):
    return hashlib.sha256(json.dumps(_normal(obj), sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def _module(name):
    if name not in _MODULES:
        path, wanted = TRUSTED[name]
        need(hashlib.sha256(path.read_bytes()).hexdigest() == wanted,
             "trusted implementation changed: " + name)
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_release_" + name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _MODULES[name] = module
    return _MODULES[name]


def _path(value):
    path = Path(value)
    if not path.is_absolute():
        path = RR / path
    path = path.resolve()
    need(path.is_relative_to(RR.resolve()), "artifact must be inside research/styles-r11")
    return path


def _read_ref(ref):
    path = _path(ref["path"])
    payload = path.read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    need(sha == ref["sha256"], "artifact byte hash mismatch: " + str(path))
    if path.suffix == ".gz":
        payload = gzip.decompress(payload)
    return path, json.loads(payload)


def _allocation_ref(entry, side):
    """An allocation ref must itself be an authenticated six-column FILL file."""
    value = entry.get("allocation", {}).get(side)
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("artifacts"), dict):
        value = value["artifacts"]
    for key in ("fill", "FILL", "rows"):
        if isinstance(value.get(key), dict):
            value = value[key]
            break
    if "path" in value and "sha256" in value and "fill" in value["path"].lower():
        return value
    return None


def prepare(cohort, cohort_sha256=None):
    """Parent-only: authenticate and load each inert source object once."""
    global _STATE
    need(_STATE is None, "one registered parent preparation")
    if isinstance(cohort, (str, Path)):
        path = _path(cohort)
        payload = path.read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        if cohort_sha256 is not None:
            need(actual == cohort_sha256, "cohort freeze changed")
        manifest = json.loads(payload)
        cohort_pin = {"path": str(path.relative_to(RR)), "sha256": actual}
    else:
        manifest = copy.deepcopy(cohort)
        cohort_pin = {"canonical_sha256": digest(manifest)}
    entries = manifest["entries"]
    need(bool(entries), "empty paired-release cohort")
    words, fills, records, allocation_data = {}, {}, {}, {}
    source_bytes = 0
    for entry in entries:
        pr = str(entry["pr"])
        need(pr not in records, "duplicate release")
        need(set(entry["providers"]) == {"base", "extra"}, "two declared providers required")
        records[pr] = copy.deepcopy(entry)
        for provider, pair in entry["providers"].items():
            for side in ("before", "after"):
                ref = pair[side]
                if ref["sha256"] not in words:
                    path, raw = _read_ref(ref)
                    words[ref["sha256"]] = {"path": path, "raw": raw, "ref": copy.deepcopy(ref)}
                    source_bytes += path.stat().st_size
        for side in ("before", "after"):
            ref = _allocation_ref(entry, side)
            if ref is not None and ref["sha256"] not in fills:
                path, data = _read_ref(ref)
                fills[ref["sha256"]] = {"data": data, "ref": copy.deepcopy(ref)}
                source_bytes += path.stat().st_size
            for name, source in entry.get("allocation", {}).get(side, {}).get("artifacts", {}).items():
                if name == "fill" or not isinstance(source, dict) or "sha256" not in source:
                    continue
                if source["sha256"] not in allocation_data:
                    path, data = _read_ref(source)
                    allocation_data[source["sha256"]] = data
                    source_bytes += path.stat().st_size
    for name in TRUSTED:
        _module(name)
    # Cache pinned mathematical readers in the parent; no fetched source import.
    _module("wordio").borrow_modules()
    _STATE = {"records": records, "words": words, "fills": fills,
              "allocation_data": allocation_data, "cohort": cohort_pin}
    return {"release_count": len(records), "provider_task_count_per_seed": 2*len(records),
            "unique_word_files": len(words), "unique_fill_files": len(fills),
            "compressed_source_bytes": source_bytes, "feature_names": list(FEATURE_NAMES),
            "feature_scope": "word/frame structural deltas; costs and child profiles excluded",
            "source_attribution": [v["ref"] for v in words.values()],
            "cohort": cohort_pin, "trusted_sources": {
                k: {"path": str(p.relative_to(RR)), "sha256": sha} for k, (p, sha) in TRUSTED.items()}}


def task_specs(seed):
    need(_STATE is not None, "prepare first")
    return [{"seed": int(seed), "pr": pr, "provider": provider}
            for pr in sorted(_STATE["records"], key=int) for provider in ("base", "extra")]


def _stream(tokens):
    M = _module("measures")
    size, rules, axiom = M.repair_size(tokens)
    repeats = M.ngram_repeat_census(tokens, 4)
    result = dict(events=len(tokens), vocabulary=len(set(tokens)), lz76=M.lz76(tokens),
                  lz78=M.lz78(tokens), repair_size=size, repair_rules=rules,
                  repair_axiom=axiom, H1=M.block_entropy(tokens, 1),
                  H6=M.block_entropy(tokens, 6))
    for k in (2, 3, 4):
        result[f"repeat{k}_distinct"], result[f"repeat{k}_occurrences"] = repeats[k][:2]
    need(set(result) == set(STREAM_MEASURES), "stream feature schema")
    return result


def _grammar(streams, max_rules=201):
    """Shared rank-free binary production system, with exact replay certificate."""
    vocabulary, ids = [], {}
    sequences = []
    for stream in streams:
        seq = []
        for token in stream:
            if token not in ids:
                ids[token] = len(vocabulary)
                vocabulary.append(token)
            seq.append(ids[token])
        sequences.append(seq)
    originals = copy.deepcopy(sequences)
    rules = []
    while len(rules) < max_rules:
        counts = Counter(pair for seq in sequences for pair in zip(seq, seq[1:]))
        if not counts or max(counts.values()) < 2:
            break
        pair = min(counts, key=lambda p: (-counts[p], p))
        replacement = -len(rules)-1
        changed, uses = [], 0
        for seq in sequences:
            out, i = [], 0
            while i < len(seq):
                if i+1 < len(seq) and (seq[i], seq[i+1]) == pair:
                    out.append(replacement); uses += 1; i += 2
                else:
                    out.append(seq[i]); i += 1
            changed.append(out)
        if uses < 2:
            break
        rules.append(pair)
        sequences = changed
    def expand(seq):
        stack, out = list(reversed(seq)), []
        while stack:
            letter = stack.pop()
            if letter >= 0:
                out.append(letter)
            else:
                left, right = rules[-letter-1]
                stack.extend((right, left))
        return out
    for old, seq in zip(originals, sequences):
        need(expand(seq) == old, "shared grammar exact replay")
    return {"operator": "finite binary straight-line productions", "max_rules": max_rules,
            "rules": rules, "axioms": sequences, "terminals": vocabulary,
            "exact_replay": True, "description_symbols": 2*len(rules)+sum(map(len, sequences)),
            "parametric_lsystem_inferred": False, "pattern_criterion_tested": False}


def _graph(raw, word):
    graph = _module("fixed_graph")._fixed_graph(raw, word)
    nodes, chains = graph["nodes"], graph["chains"]
    edges = [(a, b, r) for r, chain in enumerate(chains) for a, b in zip(chain, chain[1:])]
    n = len(nodes)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    incoming, outgoing, depth = Counter(), Counter(), [0]*n
    equalities = 0
    for a, b, r in edges:
        need(a < b, "frame constraint graph is not the declared acyclic order")
        ra, rb = find(a), find(b)
        parent[ra] = rb
        incoming[b] += 1; outgoing[a] += 1
        depth[b] = max(depth[b], depth[a]+1)
        if ((nodes[a]["section"] == "A" and nodes[b]["section"] == "cut")
                or (nodes[b]["section"] == "end" and r in graph["eq_end"])):
            equalities += 1
    # Edges are emitted chain-by-chain, so compute depth in actual node order.
    predecessors = [[] for _ in nodes]
    for a, b, _ in edges:
        predecessors[b].append(a)
    for b in range(n):
        depth[b] = max((depth[a]+1 for a in predecessors[b]), default=0)
    components = len({find(x) for x in range(n)})
    rank = n-components
    values = dict(vertices=n, arcs=len(edges), alias_registers=len(chains),
                  components=components, incidence_rank=rank, cycle_nullity=len(edges)-rank,
                  max_chain_length=max(map(len, chains), default=0), max_depth=max(depth, default=0),
                  branch_vertices=sum(outgoing[x] > 1 for x in range(n)),
                  merge_vertices=sum(incoming[x] > 1 for x in range(n)), equality_arcs=equalities)
    invariant = {"operator": "oriented vertex-edge incidence of the exact warp-split frame inclusion DAG",
                 "edge_multiset_sha256": digest(edges), "node_state_sha256": digest(nodes),
                 "integer_incidence_smith": {"unit_factors": rank, "nonunit_factors": [],
                     "proof": "oriented graph incidence is totally unimodular; a spanning forest has rank n-components"},
                 "reference_undirected_laplacian_nullity": components,
                 "physical_intrinsic_laplacian": "NOT_ESTABLISHED",
                 "physical_sandpile_critical_group": "NOT_DEFINED_BY_THIS_ANALYSIS",
                 "closure_operator": "fixed-boundary subspace join/intersection constraint propagation; state-dependent rank effects",
                 "physical_toppling_or_cost_confluence_tested": False,
                 "complete_literal_edge_profile_parity": True}
    return values, invariant


def _scalar(word):
    W = _module("wordio")
    values = {key: 0 for key in SCALAR_MEASURES}
    for section in SECTIONS:
        gates = word.raw.get(section, [])
        values[f"{section}_events"] = len(gates)
        for gate in gates:
            kind = gate[0]
            if f"{section}_{kind}" in values:
                values[f"{section}_{kind}"] += 1
            if kind in ("add", "scale"):
                coefficient = Fraction(W.coefficient(gate))
                values["coefficient_negative"] += coefficient < 0
                values["coefficient_nonunit"] += abs(coefficient) != 1
    values["live_registers"], values["helpers"] = len(word.live), len(word.helpers)
    for event in word.section_events(("A", "cut", "B", "restore")):
        for role in event.token[3:5]:
            if role == "-":
                continue
            role = "BUFFER" if role.startswith("BUFFER:") else role
            role = role if role in ROLES else "OTHER"
            values[f"role_{role}_contacts"] += 1
    return values


def _climbs(word):
    strings = {str(r): tuple((j["kind"], int(j["rank"])) for j in rec["jumps"])
               for r, rec in word.climbs.items()}
    tokens = [token for r in sorted(strings, key=int) for token in strings[r]]
    M = _module("measures")
    reproduced = Counter(rank for value in strings.values() for _, rank in value)
    need(dict(sorted(reproduced.items())) == word.paid, "canonical climb-to-child-profile reproduction")
    return {"strings_sha256": digest(strings), "register_strings": strings,
            "vocabulary": len(set(strings.values())), "H1": M.block_entropy(tokens, 1),
            "H6": M.block_entropy(tokens, 6), "paid_local_profile": word.paid,
            "entropy_sequence": "kind/rank jumps concatenated in increasing register order, preserving each register's jump order",
            "width_inventory": dict(Counter(rec["width"] for r, rec in word.climbs.items() if r in word.helpers)),
            "profile_reproduction": "PASS", "excluded_from_ML": True,
            "N2_null_tested": False, "possible_profile_restatement": True}


def _word(record):
    W = _module("wordio")
    word = W.WordData(record["raw"], record["ref"].get("attribution", {}), record["path"])
    need(word.family == "BORROW-WORD", "this registered release cohort requires BORROW providers")
    wm, _, _ = W.borrow_modules()
    # Independent pinned canonical constructor re-reads inert JSON, never code.
    original = wm.Word(record["path"])
    need(original.w == record["raw"], "canonical reader loaded a different literal word")
    tokens = {alphabet: word.section_tokens(alphabet, ("A", "cut", "B", "restore"))
              for alphabet in ("op", "role")}
    graph_values, graph_report = _graph(word.raw, word)
    values = {alphabet: _stream(stream) for alphabet, stream in tokens.items()}
    values["scalar"], values["graph"] = _scalar(word), graph_values
    return word, tokens, values, {"canonical_profile_assertions": "PASS",
                                  "frame_graph": graph_report, "climbs": _climbs(word)}


def _edits(before, after):
    W = _module("wordio")
    result = {key: 0 for key in EDIT_MEASURES}
    for section in SECTIONS:
        left, right = before.raw.get(section, []), after.raw.get(section, [])
        # Scalar identity includes the actual operands and exact coefficient;
        # frames are excluded from the alignment and checked on equal blocks.
        old = [digest(g[:-1]) for g in left]
        new = [digest(g[:-1]) for g in right]
        for kind, i, j, k, l in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
            if kind == "equal":
                for x, y in zip(left[i:j], right[k:l]):
                    result["frame_changed_on_matched_gates"] += W.basis(x[-1] or ()) != W.basis(y[-1] or ())
            elif kind == "insert":
                result["scalar_insertions"] += l-k
            elif kind == "delete":
                result["scalar_deletions"] += j-i
            else:
                result["scalar_replacements"] += max(j-i, l-k)
    for name in ("start", "end"):
        a, b = getattr(before, name), getattr(after, name)
        result[name+"_changed_registers"] = sum(
            (a[r] if r < len(a) else None) != (b[r] if r < len(b) else None)
            for r in range(max(len(a), len(b))))
    def cut(raw):
        return {int(r): W.basis(f) for r, f in zip(raw["centers"], raw["center_frames"])}
    a, b = cut(before.raw), cut(after.raw)
    result["cut_changed_registers"] = sum(a.get(r) != b.get(r) for r in a.keys() | b.keys())
    return result


def _fill_rows(data):
    if isinstance(data, dict):
        data = data.get("rows", data.get("fill", data.get("FILL")))
    need(isinstance(data, list), "unsupported FILL schema")
    need(all(isinstance(row, list) and len(row) == 6 and all(type(x) is int for x in row)
             for row in data), "expected exact six-column fill rows")
    mapping = {(row[0], row[1]): tuple(row[2:]) for row in data}
    need(len(mapping) == len(data), "duplicate literal call/helper role")
    return mapping


def _audit_fill_side(entry, side):
    """Checks supported by the pinned allocation quartet, without invented windows.

    These are a subset of the literal guards in trusted fill.audit.  Missing
    template/plan bindings are explicit; this is not a fresh full admission.
    """
    record = entry["allocation"][side]
    refs = record.get("artifacts", {})
    if not all(name in refs for name in ("fill", "order", "dispatch", "providers")):
        return {"status": "UNRESOLVED", "reason": "incomplete allocation quartet"}
    raw = _STATE["fills"][refs["fill"]["sha256"]]["data"]
    mapping = _fill_rows(raw)
    order, dispatch_rows, providers = [_STATE["allocation_data"][refs[name]["sha256"]]
                                       for name in ("order", "dispatch", "providers")]
    need(isinstance(order, list) and isinstance(dispatch_rows, list) and isinstance(providers, dict),
         "allocation quartet schema")
    dispatch = {(int(s), int(r)): pid for s, r, pid in dispatch_rows}
    for s, r, pid in (raw.get("dispatch_overrides", []) if isinstance(raw, dict) else []):
        need((s, r) in dispatch and pid in providers, "valid dispatch override")
        dispatch[s, r] = pid
    need(set(map(tuple, order)) == set(dispatch) and len(order) == len(dispatch), "dispatch/call bijection")
    widths = [tuple(providers[dispatch[tuple(call)]]["widths"]) for call in order]
    need(len(mapping) == sum(map(len, widths)), "complete role count against supplied providers")
    masks, family_candidates, bits = {}, set(), [0]*len(order)
    child_coordinate_collisions = 0
    for (t, helper), (o, child, port, offset) in mapping.items():
        need(0 <= t < len(order) and 0 <= helper < len(widths[t]) and 0 <= port < 112,
             "literal role and port ranges")
        need(offset >= 0, "nonnegative literal offset")
        bits[t] |= 1 << helper
        width = widths[t][helper]
        need(type(width) is int and width > 0, "positive integral source width")
        key = (o, child, port)
        mask = ((1 << width)-1) << offset
        need(not masks.get(key, 0) & mask, "literal bin-cell disjointness")
        masks[key] = masks.get(key, 0) | mask
        call_bin = (t, o, child, port)
        child_coordinate_collisions += call_bin in family_candidates
        family_candidates.add(call_bin)
    need(bits == [(1 << len(w))-1 for w in widths], "complete exact call/helper inventory")
    need(all(mask == (1 << mask.bit_count())-1 for mask in masks.values()), "compact occupied prefixes")
    need(child_coordinate_collisions == 0, "same-call exact-bin collision")
    # Bind the ordered helper inventory to the separately pinned local words.
    provider_bindings = {}
    W = _module("wordio")
    for tag, pid in (("base", "gauge44"), ("extra", "extra")):
        ref = entry["providers"][tag][side]
        word = W.WordData(_STATE["words"][ref["sha256"]]["raw"], ref.get("attribution", {}))
        actual = tuple(len(word.end[h])-len(word.start[h]) for h in word.helpers)
        need(pid in providers and actual == tuple(providers[pid]["widths"]),
             "literal word-to-provider ordered helper width binding")
        metadata_equal = word.paid == {
            int(k): v for k, v in providers[pid]["actual_paid_profile"].items()}
        provider_bindings[pid] = {"widths": "PASS", "reported_profile_metadata_match": metadata_equal,
            "profile_scope": "Metadata comparison only; supplied provider files may retain another local word profile. Never used as a cost label or fresh admission.",
            "metadata_mismatch": None if metadata_equal else "supplied provider profile differs from the pinned paired local word"}
    return {"status": "PASS_PARTIAL_LITERAL_CHECKS", "roles": len(mapping), "calls": len(order),
            "exact_role_inventory": True, "disjoint_cells": True, "compact_prefixes": True,
            "exact_bin_same_call_exclusion": True, "ordered_word_width_bindings": provider_bindings,
            "chronology_and_physical_family_admission": "UNRESOLVED_NO_TEMPLATE_PLAN_BINDING",
            "capacity_admission": "UNRESOLVED_NO_TEMPLATE_PLAN_BINDING",
            "source_attribution": record.get("attribution"), "sources": refs}


def _allocation(entry):
    refs = [_allocation_ref(entry, side) for side in ("before", "after")]
    result = {"full_literal_admission": "NOT_RUN_NO_COMPLETE_GEOMETRY_ADAPTER",
              "chronological_eligibility": "UNRESOLVED", "family_conflicts": "UNRESOLVED",
              "capacity": "UNRESOLVED", "missingness": []}
    if any(ref is None for ref in refs):
        result["missingness"].append("authenticated paired six-column fill artifacts unavailable")
        return result
    result["literal_checks"] = {side: _audit_fill_side(entry, side) for side in ("before", "after")}
    try:
        a, b = [_fill_rows(_STATE["fills"][ref["sha256"]]["data"]) for ref in refs]
    except (ValueError, TypeError) as exc:
        result["missingness"].append(str(exc))
        return result
    result.update(source_files=refs, before_roles=len(a), after_roles=len(b),
                  unique_literal_roles=True, same_literal_role_set=a.keys() == b.keys())
    left_norm = entry["allocation"]["before"].get("normalization", {})
    right_norm = entry["allocation"]["after"].get("normalization", {})
    same_scale = all(left_norm.get(key) == right_norm.get(key) for key in ("replicas", "calls", "live_families"))
    result["same_declared_scale"] = same_scale
    before_order = entry["allocation"]["before"].get("artifacts", {}).get("order", {}).get("sha256")
    after_order = entry["allocation"]["after"].get("artifacts", {}).get("order", {}).get("sha256")
    if a.keys() != b.keys() or not same_scale or before_order != after_order:
        result["missingness"].append("role sets or chronology scale differ; no unregistered fold/interleave")
        return result
    result.update(moved_roles=sum(a[k][:3] != b[k][:3] for k in a),
                  changed_offsets=sum(a[k][3] != b[k][3] for k in a),
                  role_conservation="PASS_EXACT_CALL_HELPER_KEYS", rows_comparable=True)
    result["missingness"].append("physical width/window/family/prefix bindings not independently replayed")
    return result


def task(spec):
    need(_STATE is not None, "prepare first")
    pr, provider = str(spec["pr"]), spec["provider"]
    entry = _STATE["records"][pr]
    pair = entry["providers"][provider]
    a = _STATE["words"][pair["before"]["sha256"]]
    b = _STATE["words"][pair["after"]["sha256"]]
    before, btokens, bstats, baudit = _word(a)
    if pair["before"]["sha256"] == pair["after"]["sha256"]:
        after, atokens, astats, aaudit = before, btokens, copy.deepcopy(bstats), copy.deepcopy(baudit)
    else:
        after, atokens, astats, aaudit = _word(b)
    features = {}
    for family, names in (("op", STREAM_MEASURES), ("role", STREAM_MEASURES),
                          ("scalar", SCALAR_MEASURES), ("graph", GRAPH_MEASURES)):
        for name in names:
            features[f"delta_{family}_{name}"] = astats[family][name]-bstats[family][name]
    edits = _edits(before, after)
    features.update({"edit_"+key: value for key, value in edits.items()})
    need(set(features) == set(FEATURE_NAMES), "dense structural feature schema")
    need(all(type(v) in (int, float) and math.isfinite(v) for v in features.values()),
         "finite numeric structural feature values")
    allocation = _allocation(entry)
    changed_words = a["raw"] != b["raw"]
    scope = entry.get("change_scope", "unspecified")
    scope_text = json.dumps(scope, sort_keys=True).lower()
    unobserved = []
    if not changed_words:
        unobserved.append("unchanged provider word: allocation/invoice/precision mechanism is outside predictor whitelist")
    if any(term in scope_text for term in ("packing", "allocation", "invoice", "precision", "fill-only", "fill_only")):
        unobserved.append("declared mechanism includes a component outside word/frame predictors")
    coverage = dict(word=True, frame=True, allocation=bool(allocation.get("rows_comparable")),
                    invoice=False, mechanism_complete=not unobserved,
                    regression_supported=not unobserved, unsupported_reasons=unobserved)
    labels = copy.deepcopy(entry.get("labels", {}))
    mechanism = scope if isinstance(scope, str) else json.dumps(scope, sort_keys=True, separators=(",", ":"))
    if "declared_rewrite" in scope_text or "declared_gate_rewrite" in scope_text:
        mechanism = "shared_declared_gate_rewrite_family_including_joint_descendants"
    old_strings, new_strings = baudit["climbs"]["register_strings"], aaudit["climbs"]["register_strings"]
    diagnostics = {"before": {"structural": bstats, "audit": baudit},
                   "after": {"structural": astats, "audit": aaudit},
                   "climb_changed_registers": sum(old_strings.get(r) != new_strings.get(r)
                       for r in old_strings.keys() | new_strings.keys()),
                   "joint_grammars": {alphabet: _grammar([btokens[alphabet], atokens[alphabet]])
                                      for alphabet in ("op", "role")},
                   "allocation": allocation, "scalar_alignment": "exact-gate SequenceMatcher; deterministic finite edit description",
                   "mechanism_group_scope": "Shared declared-rewrite family is grouped together, including joint2979; common ancestors and other mixed mechanisms still prevent independent-lineage interpretation.",
                   "conditional_native_admission_replayed": False, "null_controls_N2_run": False,
                   "production_system_scope": "descriptive finite shared grammar; no inferred iterative generative law"}
    row = dict(status="PASS", row_id=f"PR{pr}/{provider}", release_id=pr, pr=int(pr),
               parent_pr=entry["parent_pr"], provider=provider, seed=int(spec["seed"]),
               structural_features=features, features=features, labels=labels,
               source_group=str(entry["parent_pr"]), lineage_group=entry.get("lineage_group"),
               ancestral_lineage_group=entry.get("ancestral_lineage_group"),
               mechanism_group=mechanism, predictor_coverage=coverage,
               missingness=copy.deepcopy(entry.get("missingness", [])), diagnostics=diagnostics,
               provenance={"cohort": _STATE["cohort"], "before": pair["before"], "after": pair["after"],
                           "release_head": entry["head"], "release_author": entry["author"],
                           "source_credits": entry.get("source_credits", []),
                           "trusted_sources": {name: sha for name, (_, sha) in TRUSTED.items()}})
    row["integrity"] = {"feature_names_sha256": digest(FEATURE_NAMES),
                        "features_sha256": digest(features), "label_separation": True,
                        "canonical_word_and_graph_profile_checks": "PASS"}
    return row


def controls_task(seed):
    """Registered analytic fixtures; runner invokes only through pool."""
    M = _module("measures")
    repeated = [("A", "add", "1")]*12
    unique = [("A", "add", str(i)) for i in range(12)]
    grammar = _grammar([repeated, repeated])
    need(grammar["exact_replay"] and len(grammar["rules"]) > 0, "repeated grammar positive control")
    need(M.block_entropy(repeated, 1) == 0 and M.block_entropy(unique, 1) > 0,
         "entropy vocabulary control")
    need(_stream(repeated) == _stream(list(repeated)), "identical stream feature equality")
    # Actual graph-incidence theorem fixture: two vertices, two parallel arcs.
    # Rank=1, cycle nullity=1; reduced directed degree matrix is [2], so a DAG
    # does not by itself imply a trivial sandpile group. Neither is physical.
    incidence = [[-1, -1], [1, 1]]
    need(incidence[0][0]*incidence[1][1]-incidence[0][1]*incidence[1][0] == 0,
         "parallel-edge incidence rank fixture")
    bad = {"rows": [[0, 0, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]]}
    try:
        _fill_rows(bad)
    except ValueError:
        duplicate_guard = True
    else:
        duplicate_guard = False
    need(duplicate_guard, "duplicate role negative control")
    need(not any(any(term in name for term in ("paid", "profile", "moment", "kappa", "cost", "gain", "author"))
                 for name in FEATURE_NAMES), "outcome/cost feature exclusion")
    return {"status": "PASS", "seed": int(seed), "grammar_replay": True,
            "entropy_order_control": True, "identical_stream": True, "duplicate_role_rejected": True,
            "incidence_fixture": {"vertices": 2, "parallel_arcs": 2, "rank": 1,
                "smith_nonzero": [1], "cycle_nullity": 1, "reduced_degree_determinant": 2},
            "feature_whitelist": list(FEATURE_NAMES), "physical_toppling_claim": False}
