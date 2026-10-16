"""Exact fixed-cap closure controls for CONTINUATION-03/T1.

The caller freezes this source and uses pipeline/pool.py.  Import does not load
words, construct graphs, run controls, call a solver, or execute fetched code.
Frame masks contain ALL vectors in an F2 subspace.  The dual message processor
emits every newly acquired vector once per outgoing constraint edge; a chosen
basis is not its output alphabet.  Closure is a feasibility operation, not a
cost optimizer or a physical sandpile Laplacian.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

WORDIO_SHA = "a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4"
PREREGISTRATION_SHA = "2a4cc6608f4d25ff7eb31150de3e604ac4a3e4d2437df38d08db4dc79cb9864e"
_W = None
_STATES = {}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def wordio():
    global _W
    if _W is None:
        path = Path(__file__).resolve().parents[1] / "wordio.py"
        need(hashlib.sha256(path.read_bytes()).hexdigest() == WORDIO_SHA,
             "trusted wordio source drift")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_cont03_closure_wordio", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _W = module
    return _W


def _basis(vectors):
    # Canonical F2 row reduction, same descending-pivot convention as wordio.
    piv = {}
    for value in vectors:
        while value:
            bit = value.bit_length() - 1
            if bit in piv:
                value ^= piv[bit]
            else:
                piv[bit] = value
                break
    for bit in sorted(piv):
        for other in piv:
            if other > bit and (piv[other] >> bit) & 1:
                piv[other] ^= piv[bit]
    return tuple(piv[k] for k in sorted(piv, reverse=True))


def _elements(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


@lru_cache(None)
def _span(frame):
    values = {0}
    for vector in frame:
        values |= {x ^ vector for x in values}
    return sum(1 << x for x in values)


@lru_cache(None)
def _frame(mask):
    return _basis(_elements(mask))


@lru_cache(None)
def _annihilator(mask, h):
    basis = _frame(mask)
    return sum(1 << vector for vector in range(1 << h)
               if all((vector & row).bit_count() % 2 == 0 for row in basis))


@lru_cache(None)
def _join_masks(a, b):
    result = a
    for vector in _frame(b):
        if not (result >> vector) & 1:
            result |= sum(1 << (x ^ vector) for x in _elements(result))
    return result


def _inside(a, b):
    return a & ~b == 0


@dataclass(frozen=True)
class _Model:
    h: int
    lower: tuple
    upper: tuple
    edges: tuple
    predecessors: tuple
    successors: tuple


def _model(h, lower, upper, edges):
    lower, upper, edges = tuple(lower), tuple(upper), tuple(edges)
    n = len(lower)
    need(n == len(upper), "bound lengths")
    pred, succ = [[] for _ in range(n)], [[] for _ in range(n)]
    for left, right, label in edges:
        need(0 <= left < right < n, "registered graph must be topologically ordered")
        pred[right].append((left, label))
        succ[left].append(right)
    result = _Model(h, lower, upper, edges, tuple(map(tuple, pred)), tuple(map(tuple, succ)))
    _validate(result, lower)
    _validate(result, upper)
    return result


def _validate(model, assignment):
    need(len(assignment) == len(model.lower), "assignment length")
    for k, value in enumerate(assignment):
        need(value & 1 and _span(_frame(value)) == value, ("not a subspace", k))
        need(_inside(model.lower[k], value) and _inside(value, model.upper[k]),
             ("assignment outside exact bounds", k))
    for left, right, label in model.edges:
        need(_inside(assignment[left], assignment[right]),
             ("assignment inclusion failure", left, right, label))


def build_graph(raw):
    """Fresh trusted warp-split graph; no frame optimization and no old floors."""
    _, _, bp = wordio().borrow_modules()
    inline, meta = bp.build_problem(raw)
    graph = bp.BorrowGraph(inline, meta["eq_end"], check_literal=False,
                           tail_mutable=True, cut_equality=True)
    return graph, meta


def _graph_model(graph):
    edges = tuple(sorted((left, right, register)
                         for (right, register), left in graph.prev.items()))
    return _model(9, (_span(tuple(graph.lower[k])) for k in range(len(graph.nodes))),
                  (_span(tuple(graph.upper[k])) for k in range(len(graph.nodes))), edges)


def _caps(model, caps):
    items = caps.items() if isinstance(caps, dict) else caps
    answer = []
    for node, frame in items:
        need(type(node) is int and 0 <= node < len(model.lower), "cap node")
        frame = tuple(frame)
        need(all(type(x) is int and 0 <= x < (1 << model.h) for x in frame),
             "cap vector outside ambient space")
        answer.append((node, _span(_basis(frame))))
    return tuple(answer)


def _close(model, caps, assignment):
    """Independent reverse-topological meet formula; None means infeasible."""
    values = list(assignment)
    for node, cap in caps:
        values[node] &= cap
    for node in reversed(range(len(values))):
        for successor in model.successors[node]:
            values[node] &= values[successor]
        if not _inside(model.lower[node], values[node]):
            return None
    return tuple(values)


class ClosureInfeasible(ValueError):
    """The fixed cap list excludes an independently attained exact floor."""


def close_caps(graph, caps, assignment=None):
    """Return a full node->canonical-frame assignment, or reject bad floors.

    ``assignment`` can be a full assignment or a toolkit variable-only mapping.
    The default is the freshly computed maximal feasible labeling graph.upper.
    ``caps`` is either {node: frame} or a list of (node, frame) pairs.
    """
    model = _graph_model(graph)
    if assignment is None:
        initial = model.upper
    else:
        initial = tuple(_span(tuple(assignment.get(k, graph.nodes[k][1])))
                        for k in range(len(graph.nodes)))
        _validate(model, initial)
    result = _close(model, _caps(model, caps), initial)
    if result is None:
        raise ClosureInfeasible("fixed caps exclude an exact graph floor")
    _validate(model, result)
    return {k: _frame(value) for k, value in enumerate(result)}


def write_assignment(raw, graph, meta, assignment):
    """Materialize a valid full/toolkit assignment and derive the complete bill.

    Scalar coefficients, cut/warp/end interfaces and role widths are unchanged.
    This function is not a free-operator or native admission audit.
    """
    W = wordio()
    model = _graph_model(graph)
    values = tuple(_span(tuple(assignment.get(k, graph.nodes[k][1])))
                   for k in range(len(graph.nodes)))
    _validate(model, values)
    full = {k: _frame(value) for k, value in enumerate(values)}
    out = deepcopy(raw)
    for k, (_regs, _old, section, index) in enumerate(graph.nodes):
        if section == "A":
            out["A"][meta["A_idx"][index]][-1] = list(full[k])
        elif section == "B":
            out["B"][index][-1] = list(full[k])
        elif section == "tail":
            out["restore"][index][-1] = list(full[k])
    _, _, bp = W.borrow_modules()
    profile = Counter(graph.profile(full))
    profile.update(bp.centre_descents(out))
    need(all(k > 0 and v > 0 for k, v in profile.items()), "positive paid ranks")
    out["report"]["local_profile"] = {str(k): v for k, v in sorted(profile.items())}
    canonical = W.WordData(out, {"scope": "unadmitted closure materialization"})
    out["cleanup"] = W.derived_borrow_cleanup(canonical)
    return out


def _message_close(model, caps, assignment, schedule, seed):
    """Exact dual all-vector messages, with bitsets representing multisets.

    The initial constraints are already present at every vertex. Every new
    nonzero vector is sent exactly once along every predecessor edge. A bitset
    therefore represents the full emitted multiset with multiplicity one on
    that edge; duplicate incoming facts have no effect.
    """
    dual = [_annihilator(value, model.h) for value in assignment]
    initial_dual = tuple(dual)
    floors = tuple(_annihilator(value, model.h) for value in model.lower)
    pending = [(node, _annihilator(cap, model.h) & ~dual[node]) for node, cap in caps]
    pending = [item for item in pending if item[1]]
    queue = deque(pending) if schedule == "forward" else list(pending)
    rng = random.Random(seed)
    emitted = {}
    delivered = 0
    while queue:
        if schedule == "forward":
            node, incoming = queue.popleft()
        elif schedule == "reverse":
            node, incoming = queue.pop()
        else:
            need(schedule == "seeded", "message schedule")
            index = rng.randrange(len(queue))
            queue[index], queue[-1] = queue[-1], queue[index]
            node, incoming = queue.pop()
        delivered += 1
        joined = _join_masks(dual[node], incoming | 1)
        if not _inside(joined, floors[node]):
            return None, emitted, {"delivered_payloads": delivered, "infeasible_node": node}
        added = joined & ~dual[node]
        if not added:
            continue
        need(not added & 1, "zero vector must never be emitted as a new fact")
        dual[node] = joined
        for predecessor, label in model.predecessors[node]:
            edge = (node, predecessor, label)
            old = emitted.get(edge, 0)
            need(not old & added, "duplicate emitted vector on one edge")
            emitted[edge] = old | added
            queue.append((predecessor, added))
    result = tuple(_annihilator(value, model.h) for value in dual)
    _validate(model, result)
    for right, predecessors in enumerate(model.predecessors):
        for left, label in predecessors:
            need(emitted.get((right, left, label), 0) == dual[right] & ~initial_dual[right],
                 "all new vectors must be emitted on every predecessor edge")
    return result, emitted, {"delivered_payloads": delivered,
                            "emitted_vector_messages": sum(x.bit_count() for x in emitted.values()),
                            "emitting_edges": len(emitted)}


def _assignment_digest(assignment):
    return _digest([list(_frame(value)) for value in assignment])


def _emission_digest(emitted):
    return _digest([[*edge, hex(mask)] for edge, mask in sorted(emitted.items())])


def prepare(records):
    """Root-only preparation, loading each of the three source graphs once."""
    need(not _STATES, "closure prepare is once-only")
    need(set(records) == {"base", "extra", "original"}, "three registered source words")
    began = time.process_time()
    W = wordio()
    summary = {}
    for name in sorted(records):
        record = records[name]
        state = {"attribution": deepcopy(record["attribution"]), "raw": record["raw"]}
        try:
            canonical = W.WordData(record["raw"], record["attribution"])
            need(canonical.family == "BORROW-WORD" and canonical.h == 9,
                 "registered nine-dimensional BORROW word")
            graph, meta = build_graph(record["raw"])
            model = _graph_model(graph)
            _, _, bp = W.borrow_modules()
            literal_profile = Counter(graph.profile(graph.literal()))
            literal_profile.update(bp.centre_descents(record["raw"]))
            need(dict(literal_profile) == canonical.paid,
                 "fresh graph literal profile agrees with independent canonical word")
            selected = []
            for node in sorted(graph.mutable):
                if graph.lower[node] == graph.upper[node]:
                    continue
                rank = max(len(graph.lower[node]), len(graph.upper[node]) - 1)
                frame = min(tuple(frame) for frame in graph.dom[node] if len(frame) == rank)
                selected.append((node, frame))
                if len(selected) == 64:
                    break
            need(selected, "at least one proper real cap")
            state.update(graph=graph, meta=meta, model=model, selected=tuple(selected), status="READY")
            summary[name] = {"status": "READY", "nodes": len(graph.nodes), "edges": len(model.edges),
                             "variables": len(graph.var), "selected_caps": len(selected),
                             "virtual_registers": meta["virtual"],
                             "canonical_source_profile": {str(k): v for k, v in sorted(canonical.paid.items())}}
        except ValueError as error:
            # This is an implementation-domain limit, not mathematical infeasibility.
            if "domain too large" not in str(error):
                raise
            state.update(status="EXPLORATORY", unsupported=str(error))
            summary[name] = {"status": "EXPLORATORY", "unsupported": str(error)}
        _STATES[name] = state
    _, _, bp = W.borrow_modules()
    F, _ = W.toolkit()
    sources = {}
    for module in (W, bp, F):
        path = Path(module.__file__)
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"status": "READY" if all(s["status"] == "READY" for s in _STATES.values()) else "EXPLORATORY",
            "words": summary, "source_attribution": [deepcopy(_STATES[n]["attribution"]) for n in sorted(_STATES)],
            "trusted_source_sha256": sources, "prepare_cpu_seconds": time.process_time() - began}


def _subspaces3():
    spaces = {1}
    todo = [1]
    while todo:
        current = todo.pop()
        for vector in range(1, 8):
            joined = _join_masks(current, 1 | (1 << vector))
            if joined not in spaces:
                spaces.add(joined)
                todo.append(joined)
    answer = tuple(sorted(spaces, key=lambda x: (len(_frame(x)), _frame(x))))
    need(len(answer) == 16, "all 16 F2^3 subspaces")
    return answer


def _toy_control():
    spaces = _subspaces3()
    labels = tuple((a, b) for a in spaces for b in spaces if _inside(a, b))
    need(len(labels) == 66, "all 66 nested floor pairs")
    caps = tuple((node, frame) for node in (0, 1) for frame in spaces)
    need(len(caps) == 32, "all 32 one-vertex caps")
    full = (255, 255)
    count = feasible = infeasible = idempotence = 0
    for floors in labels:
        model = _model(3, floors, full, ((0, 1, 0),))
        permitted = tuple(x for x in labels if all(_inside(floors[k], x[k]) for k in (0, 1)))
        first = {cap: _close(model, (cap,), full) for cap in caps}
        for cap in caps:
            once = first[cap]
            twice = None if once is None else _close(model, (cap,), once)
            need(once == twice, ("toy idempotence", floors, cap))
            idempotence += 1
        for cap_c in caps:
            for cap_d in caps:
                count += 1
                c, d = first[cap_c], first[cap_d]
                cd = None if c is None else _close(model, (cap_d,), c)
                dc = None if d is None else _close(model, (cap_c,), d)
                union = _close(model, (cap_c, cap_d), full)
                candidates = tuple(x for x in permitted
                                   if _inside(x[cap_c[0]], cap_c[1])
                                   and _inside(x[cap_d[0]], cap_d[1]))
                if candidates:
                    oracle = max(candidates, key=lambda x: sum(v.bit_count() for v in x))
                    need(all(all(_inside(x[k], oracle[k]) for k in (0, 1)) for x in candidates),
                         "enumerated greatest toy labeling")
                    feasible += 1
                else:
                    oracle = None
                    infeasible += 1
                need(cd == dc == union == oracle,
                     ("toy closure equation", floors, cap_c, cap_d, cd, dc, union, oracle))
    need(count == 67584, "complete registered toy domain")
    return {"status": "PASS", "ambient_dimension": 3, "subspaces": len(spaces),
            "nested_floor_pairs": len(labels), "single_caps": len(caps),
            "ordered_cap_pair_cases": count, "feasible_cases": feasible,
            "infeasible_cases": infeasible, "idempotence_cases": idempotence,
            "oracle": "enumerate every feasible labeling and verify the greatest element"}


def _real_control(name, seed):
    state = _STATES[name]
    if state["status"] != "READY":
        return {"status": "EXPLORATORY", "unsupported": state["unsupported"],
                "source_attribution": deepcopy(state["attribution"])}
    graph, model = state["graph"], state["model"]
    selected = state["selected"]
    C, D = _caps(model, selected[::2]), _caps(model, selected[1::2])
    start = model.upper
    c = _close(model, C, start)
    d = _close(model, D, start)
    need(c is not None and d is not None, "registered real caps contain floors")
    cd = _close(model, D, c)
    dc = _close(model, C, d)
    together = _close(model, C + D, start)
    need(cd == dc == together and together is not None, "real cap commutation")
    need(_close(model, C, c) == c and _close(model, D, d) == d,
         "real cap idempotence")
    _validate(model, together)
    receipts = {}
    expected_emitted = None
    for schedule in ("forward", "reverse", "seeded"):
        result, emitted, stats = _message_close(model, C + D, start, schedule, seed)
        need(result == together, ("exact dual message state", name, schedule))
        if expected_emitted is None:
            expected_emitted = emitted
        else:
            need(emitted == expected_emitted, ("exact emitted multiset equality", name, schedule))
        receipts[schedule] = dict(stats, assignment_sha256=_assignment_digest(result),
                                  emitted_multiset_sha256=_emission_digest(emitted))
    bad = next(k for k, floor in enumerate(model.lower) if floor != 1)
    need(_close(model, ((bad, 1),), start) is None, "floor-excluding cap must reject")
    for schedule in ("forward", "reverse", "seeded"):
        result, _, _ = _message_close(model, ((bad, 1),), start, schedule, seed)
        need(result is None, "message processor must reject a floor-excluding cap")
    before = {k: _frame(x) for k, x in enumerate(start)}
    after = {k: _frame(x) for k, x in enumerate(together)}
    return {"status": "PASS", "source_attribution": deepcopy(state["attribution"]),
            "nodes": len(graph.nodes), "edges": len(model.edges), "variables": len(graph.var),
            "selected_caps": [{"node": node, "frame": list(frame), "set": "C" if i % 2 == 0 else "D",
                               "floor": list(graph.lower[node]), "upper": list(graph.upper[node])}
                              for i, (node, frame) in enumerate(selected)],
            "composition_equal": True, "idempotence_equal": True,
            "full_states_and_emitted_multisets_compared": True, "schedules": receipts,
            "maximal_assignment_sha256": _assignment_digest(start),
            "closed_assignment_sha256": _assignment_digest(together),
            "changed_vertices": sum(a != b for a, b in zip(start, together)),
            "graph_profile_before": {str(k): v for k, v in sorted(graph.profile(before).items())},
            "graph_profile_after": {str(k): v for k, v in sorted(graph.profile(after).items())},
            "profile_scope": "graph rank jumps only; fixed centre descents excluded; no cost or kappa assertion",
            "negative_floor_cap": {"node": bad, "floor": list(graph.lower[bad]), "cap": [],
                                   "meet_rejected": True, "all_message_schedules_rejected": True}}


def _obstruction_controls():
    # Same rank, different orientation, identical cap, different dimension loss.
    line1, line2 = _span((1,)), _span((2,))
    cap = ((0, line1),)
    model = _model(2, (1,), (15,), ())
    a, b = _close(model, cap, (line1,)), _close(model, cap, (line2,))
    losses = (len(_frame(line1)) - len(_frame(a[0])),
              len(_frame(line2)) - len(_frame(b[0])))
    need(losses == (0, 1), "rank-only projection obstruction")
    matrix = ((2, 0), (-1, 1))
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    need(determinant == 2, "acyclic reduced Laplacian determinant")
    return {"equal_rank_orientation": {"status": "PASS", "input_frames": [[1], [2]],
                                      "input_dimensions": [1, 1], "common_cap": [1],
                                      "dimension_losses": list(losses),
                                      "dimension_changes": [-x for x in losses],
                                      "scope": "obstruction to a fixed update on rank projection, not every enriched abelian model"},
            "acyclic_critical_group_correction": {"status": "PASS", "arcs": [["v", "w"], ["v", "sink"], ["w", "sink"]],
                                                 "column_convention_reduced_matrix": [list(row) for row in matrix],
                                                 "determinant": determinant, "smith_diagonal": [1, 2],
                                                 "critical_group": "Z/2Z", "scope": "DAG does not imply trivial critical group"}}


def controls_task(seed):
    """Registered root-pool task; all outputs are JSON serializable."""
    need(set(_STATES) == {"base", "extra", "original"}, "parent prepare required")
    if isinstance(seed, dict):
        seed = seed["seed"]
    need(type(seed) is int, "integer seed")
    began = time.process_time()
    toy = _toy_control()
    real = {name: _real_control(name, seed) for name in sorted(_STATES)}
    negative = _obstruction_controls()
    status = "PASS" if all(x["status"] == "PASS" for x in real.values()) else "EXPLORATORY"
    return {"experiment": "T1-CAP-CLOSURE", "status": status, "decision": status, "seed": seed,
            "preregistration_sha256": PREREGISTRATION_SHA,
            "toy": toy, "real": real, "negative_controls": negative,
            "source_attribution": [deepcopy(_STATES[n]["attribution"]) for n in sorted(_STATES)],
            "cpu_seconds": time.process_time() - began,
            "scope": "Exact fixed-graph cap feasibility and schedule independence only; no cost optimization, intrinsic physical Laplacian, or kappa claim."}
