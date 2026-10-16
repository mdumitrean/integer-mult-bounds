"""Exact cost-bearing collective caps on one fresh feasible BORROW graph.

Coordinator-registered execution only.  No scientific work runs at import.
The scalar producer must separately prove its changed dirty operator.  This
module preserves that word's scalar gates, endpoints and physical inventory.
Its saturating cap closure is abelian; its optimization graph is not an
intrinsic physical Laplacian.  See planning/COLLECTIVE-CAPS.md.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

RR = Path(__file__).resolve().parents[2]
E1_PATH = RR / "pipeline/continuation04/expansions.py"
E1_SHA256 = "5f358c2084cd39f669758cd42c077dbb93726ef79bc8a2055d7ea1f17f7f7442"
_E1 = None
_COSTS = {}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _trusted():
    global _E1
    if _E1 is None:
        need(not sys.flags.optimize, "assertions must remain enabled")
        need(hashlib.sha256(E1_PATH.read_bytes()).hexdigest() == E1_SHA256,
             "frozen literal-graph utility drift")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_collective_caps_e1", E1_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _E1 = module
    return _E1


def prime(endpoint, dimension=73, max_rank=9):
    """Load trusted code/cost intervals once in a registered parent if useful."""
    endpoint = Fraction(endpoint)
    need(0 < endpoint < 1 and dimension > max_rank > 0, "child-cost geometry")
    key = (endpoint, int(dimension), int(max_rank))
    if key not in _COSTS:
        ceiling = _trusted()._trusted()._module("ceiling")
        table = [(Fraction(0), Fraction(0))]
        table.extend(ceiling.child_cost(r, dimension, endpoint)
                     for r in range(1, max_rank+1))
        need(all(0 <= lo <= hi for lo, hi in table), "outward child-cost intervals")
        _COSTS[key] = tuple(table)
    return _COSTS[key]


class UnresolvedSign(Exception):
    pass


class CpuLimit(Exception):
    pass


class Oracle:
    """Exact coefficient vectors with a rigorous, deliberately partial order oracle."""
    def __init__(self, table, seconds):
        self.table = tuple(table)
        self.zero = (0,)*len(table)
        self.until = time.process_time()+seconds
        self.signs = {self.zero: 0}
        self.intervals = {self.zero: (Fraction(0), Fraction(0))}
        self.calls = 0

    def tick(self):
        if time.process_time() > self.until:
            raise CpuLimit("collective-cap internal CPU guard")

    def unit(self, rank):
        out = [0]*len(self.zero)
        if rank:
            need(0 < rank < len(out), "child rank in cost table")
            out[rank] = 1
        return tuple(out)

    def add(self, a, b):
        return tuple(x+y for x, y in zip(a, b))

    def sub(self, a, b):
        return tuple(x-y for x, y in zip(a, b))

    def neg(self, a):
        return tuple(-x for x in a)

    def bounds(self, value):
        self.calls += 1
        if self.calls % 256 == 0:
            self.tick()
        if value not in self.intervals:
            lo = hi = Fraction(0)
            for coefficient, (lower, upper) in zip(value, self.table):
                lo += coefficient*(lower if coefficient >= 0 else upper)
                hi += coefficient*(upper if coefficient >= 0 else lower)
            self.intervals[value] = (lo, hi)
        return self.intervals[value]

    def sign(self, value):
        if value not in self.signs:
            lo, hi = self.bounds(value)
            if lo > 0:
                sign = 1
            elif hi < 0:
                sign = -1
            elif lo == hi == 0:
                sign = 0
            else:
                raise UnresolvedSign(json.dumps(dict(coefficients=value,
                    lower=str(lo), upper=str(hi)), sort_keys=True))
            self.signs[value] = sign
        return self.signs[value]

    def minimum(self, a, b):
        return a if self.sign(self.sub(a, b)) <= 0 else b


class Network:
    def __init__(self, count, oracle):
        self.ora = oracle
        self.adj = [[] for _ in range(count)]
        self.original = []

    def arc(self, u, v, capacity, kind):
        need(u != v and self.ora.sign(capacity) >= 0, "nonnegative nonself capacity")
        forward = [v, len(self.adj[v]), capacity]
        reverse = [u, len(self.adj[u]), self.ora.zero]
        self.original.append((u, len(self.adj[u]), v, capacity, kind))
        self.adj[u].append(forward)
        self.adj[v].append(reverse)

    def reachable(self, source):
        reached = {source}
        queue = deque([source])
        while queue:
            self.ora.tick()
            u = queue.popleft()
            for v, _reverse, residual in self.adj[u]:
                if v not in reached and self.ora.sign(residual) > 0:
                    reached.add(v)
                    queue.append(v)
        return reached

    def flow(self, source, sink):
        """Deterministic Dinic, iterative DFS to avoid long-chain recursion."""
        ora = self.ora
        total, phases, augmentations = ora.zero, 0, 0
        while True:
            ora.tick()
            level = [-1]*len(self.adj)
            level[source] = 0
            queue = deque([source])
            while queue:
                u = queue.popleft()
                for v, _reverse, residual in self.adj[u]:
                    if level[v] < 0 and ora.sign(residual) > 0:
                        level[v] = level[u]+1
                        queue.append(v)
            if level[sink] < 0:
                break
            phases += 1
            position = [0]*len(self.adj)
            while True:
                ora.tick()
                vertices, path, limits = [source], [], []
                found = False
                while vertices:
                    u = vertices[-1]
                    if u == sink:
                        amount = limits[-1]
                        need(ora.sign(amount) > 0, "positive augmentation")
                        for a, index in path:
                            edge = self.adj[a][index]
                            edge[2] = ora.sub(edge[2], amount)
                            reverse = self.adj[edge[0]][edge[1]]
                            reverse[2] = ora.add(reverse[2], amount)
                        total = ora.add(total, amount)
                        augmentations += 1
                        found = True
                        break
                    while position[u] < len(self.adj[u]):
                        edge = self.adj[u][position[u]]
                        if level[edge[0]] == level[u]+1 and ora.sign(edge[2]) > 0:
                            break
                        position[u] += 1
                    if position[u] == len(self.adj[u]):
                        level[u] = -1
                        vertices.pop()
                        if path:
                            parent, _index = path.pop()
                            limits.pop()
                            position[parent] += 1
                        continue
                    edge = self.adj[u][position[u]]
                    limit = edge[2] if not limits else ora.minimum(limits[-1], edge[2])
                    path.append((u, position[u]))
                    vertices.append(edge[0])
                    limits.append(limit)
                if not found:
                    break
        return total, dict(phases=phases, augmentations=augmentations)

    def certificate(self, source, sink, total, reached):
        """Independently check original-arc feasibility, conservation and cut equality."""
        ora = self.ora
        need(sink not in reached and source in reached, "separating residual cut")
        balance = [ora.zero for _ in self.adj]
        cut = ora.zero
        arcs = []
        for u, index, v, capacity, kind in self.original:
            ora.tick()
            residual = self.adj[u][index][2]
            flow = ora.sub(capacity, residual)
            need(ora.sign(flow) >= 0 and ora.sign(residual) >= 0, "flow capacity bounds")
            balance[u] = ora.add(balance[u], flow)
            balance[v] = ora.sub(balance[v], flow)
            crossing = u in reached and v not in reached
            if crossing:
                cut = ora.add(cut, capacity)
                need(not kind.startswith("hard_"), "minimum cut never crosses a hard constraint")
            arcs.append(dict(u=u, v=v, capacity=list(capacity), flow=list(flow), kind=kind))
        for v, value in enumerate(balance):
            expected = total if v == source else ora.neg(total) if v == sink else ora.zero
            need(value == expected, "exact coefficientwise flow conservation")
        need(cut == total, "exact formal max-flow/min-cut equality")
        return dict(source=source, sink=sink, source_side=sorted(reached),
                    value_coefficients=list(total), cut_coefficients=list(cut), arcs=arcs,
                    independent_checks="capacity bounds, coefficientwise conservation, exact cut equality, hard arcs")


def _edges(fixed):
    nodes, eq = fixed["nodes"], fixed["eq_end"]
    result = []
    for (v, register), u in sorted(fixed["previous"].items()):
        equal = ((nodes[u]["section"] == "A" and nodes[v]["section"] == "cut")
                 or (nodes[v]["section"] == "end" and register in eq))
        result.append((u, v, register, equal))
    return result


def _floors(nodes, edges, mutable):
    E = _trusted()
    incoming = [[] for _ in nodes]
    equal_successors = [[] for _ in nodes]
    for u, v, _register, equal in edges:
        need(u < v, "literal split graph is topological")
        incoming[v].append(u)
        if equal:
            need(nodes[u]["frame"] == nodes[v]["frame"], "literal exact interface equality")
            need(v not in mutable, "supported equality successor is fixed")
            equal_successors[u].append(v)
    floor = []
    for v, node in enumerate(nodes):
        if v in mutable:
            value = E._join(*(floor[u] for u in incoming[v]),
                            *(nodes[q]["frame"] for q in equal_successors[v]))
        else:
            value = node["frame"]
        need(E._leq(value, node["frame"]), "literal frame contains attained floor")
        floor.append(value)
    return floor


def _network(nodes, edges, mutable, floors, normal, ambient, ora):
    E = _trusted()
    need(type(normal) is int and 0 < normal < (1 << ambient), "nonzero ambient normal")
    intersections = []
    intersection_cache = {}
    active = []
    for v, node in enumerate(nodes):
        if node["frame"] not in intersection_cache:
            intersection_cache[node["frame"]] = E._basis(x for x in E._span(node["frame"])
                if (x & normal).bit_count() % 2 == 0)
        intersection = intersection_cache[node["frame"]]
        need(E._leq(intersection, node["frame"]), "actual intersection containment")
        difference = len(node["frame"])-len(intersection)
        need(difference in (0, 1), "hyperplane changes rank by at most one")
        intersections.append(intersection)
        if difference:
            active.append(v)
    active_set = set(active)
    index = {v: i for i, v in enumerate(active)}
    source, sink = len(active), len(active)+1
    network = Network(len(active)+2, ora)
    prizes = {v: ora.zero for v in active}
    finite, hard = [], []
    forbidden = set()
    for v in active:
        if v not in mutable or not E._leq(floors[v], intersections[v]):
            forbidden.add(v)
            hard.append((index[v], sink, "hard_fixed_or_floor"))
    for u, v, register, equality in edges:
        d = len(nodes[v]["frame"])-len(nodes[u]["frame"])
        need(d >= 0, "nonnegative literal rank increment")
        if u in active_set:
            need(v in active_set, "an H-exterior predecessor has H-exterior successor")
            cost = ora.sub(ora.unit(d+1), ora.unit(d))
            need(ora.sign(cost) > 0, "strictly positive rank tariff increment")
            finite.append((index[u], index[v], cost, "boundary_climb"))
            hard.append((index[v], index[u], "hard_predecessor_closure"))
            if equality:
                hard.append((index[u], index[v], "hard_exit_equality"))
        elif v in active_set:
            need(d >= 1 and not equality, "entry saving has positive rank and no equality")
            prize = ora.sub(ora.unit(d), ora.unit(d-1))
            need(ora.sign(prize) > 0, "strictly positive entry saving")
            prizes[v] = ora.add(prizes[v], prize)
    total_prize = ora.zero
    for v in active:
        if prizes[v] != ora.zero:
            finite.append((source, index[v], prizes[v], "entry_prize"))
            total_prize = ora.add(total_prize, prizes[v])
    finite_sum = ora.zero
    for _u, _v, capacity, _kind in finite:
        finite_sum = ora.add(finite_sum, capacity)
    hard_capacity = ora.add(finite_sum, ora.unit(1))
    need(ora.sign(ora.sub(hard_capacity, finite_sum)) > 0, "hard capacity exceeds every finite cut")
    for u, v, capacity, kind in finite:
        network.arc(u, v, capacity, kind)
    for u, v, kind in hard:
        network.arc(u, v, hard_capacity, kind)
    return network, dict(active=active, active_set=active_set, index=index,
        intersections=intersections, source=source, sink=sink, total_prize=total_prize,
        forbidden=forbidden, hard_capacity=hard_capacity, normal=normal, ambient=ambient)


def _validate_selection(nodes, edges, mutable, floors, data, selected):
    E = _trusted()
    normal, ambient = data["normal"], data["ambient"]
    need(type(normal) is int and type(ambient) is int and
         ambient > 0 and 0 < normal < (1 << ambient), "registered hyperplane geometry")
    need(selected <= data["active_set"] and not selected & data["forbidden"],
         "selection uses only permitted affected vertices")
    assignment = [data["intersections"][v] if v in selected else node["frame"]
                  for v, node in enumerate(nodes)]
    exact_intersections = {}
    for v, frame in enumerate(assignment):
        need(E._leq(floors[v], frame) and E._leq(frame, nodes[v]["frame"]),
             "frame remains between exact floor and literal cap")
        if v in selected:
            original = nodes[v]["frame"]
            need(all(0 <= x < (1 << ambient) for x in original),
                 "literal frame lies in registered ambient space")
            need(all((x & normal).bit_count() % 2 == 0 for x in frame),
                 "selected frame lies in the registered hyperplane")
            need(len(original)-len(frame) == 1, "selected cap has exact codimension one")
            if original not in exact_intersections:
                exact_intersections[original] = E._basis(x for x in E._span(original)
                    if (x & normal).bit_count() % 2 == 0)
            need(frame == exact_intersections[original],
                 "selected frame is independently reconstructed actual intersection")
        if v not in mutable:
            need(frame == nodes[v]["frame"], "fixed literal vertex unchanged")
    for u, v, _register, equality in edges:
        need(E._leq(assignment[u], assignment[v]), "selected full chain inclusion")
        if equality:
            need(assignment[u] == assignment[v], "selected exact cut/warp equality")
    return assignment


def _edge_profile(nodes, edges, assignment=None):
    profile = Counter()
    frames = assignment if assignment is not None else [n["frame"] for n in nodes]
    for u, v, _register, _equality in edges:
        d = len(frames[v])-len(frames[u])
        need(d >= 0, "edge profile has no descent")
        if d:
            profile[d] += 1
    return dict(sorted(profile.items()))


def _profile_vector(profile, ora):
    result = list(ora.zero)
    for rank, count in profile.items():
        need(0 < int(rank) < len(result), "profile rank bound")
        result[int(rank)] += int(count)
    return tuple(result)


def _check_objective(delta, before, after, ora):
    need(all(int(n) >= 0 for n in after.values()), "nonnegative complete paid counts")
    need(sum(int(r)*int(n) for r, n in before.items()) ==
         sum(int(r)*int(n) for r, n in after.items()), "complete paid rank-mass equality")
    actual = ora.sub(_profile_vector(after, ora), _profile_vector(before, ora))
    need(delta == actual, "formal optimal cut objective equals complete canonical delta")


def _close_selected(initial, edges, data, reverse=False):
    """Single-H saturating fact processors; used for the registered schedule control."""
    predecessors = {}
    for u, v, register, _equality in edges:
        if u in data["active_set"] and v in data["active_set"]:
            predecessors.setdefault(v, set()).add((u, register))
    queue = deque(sorted(set(initial), reverse=reverse))
    selected, emissions = set(), set()
    while queue:
        v = queue.popleft()
        if v in selected:
            continue
        need(v in data["active_set"] and v not in data["forbidden"], "closure reached prohibited frame")
        selected.add(v)
        for u, register in sorted(predecessors.get(v, ()), reverse=reverse):
            emissions.add((v, u, register))
            queue.append(u)
    return selected, emissions


class Prepared:
    def __init__(self, raw, attribution, endpoint, dimension=73, frozen_fields=None):
        E = _trusted()
        W = E._W()
        self.raw = deepcopy(raw)
        self.attribution = deepcopy(attribution)
        self.endpoint = Fraction(endpoint)
        self.dimension = int(dimension)
        self.word = W.WordData(self.raw, self.attribution)
        need(self.word.family == "BORROW-WORD" and not raw.get("early_cleanup"),
             "supported BORROW word without early cleanup")
        need(W.cleanup_check(self.word)["exact"], "input literal cleanup production")
        self.fixed = E._fixed_graph(self.raw, self.word)
        self.nodes = self.fixed["nodes"]
        self.edges = _edges(self.fixed)
        npre = int(raw.get("prelude_events", 0))
        self.mutable = {v for v, node in enumerate(self.nodes)
                        if node["section"] in ("B", "restore")
                        or (node["section"] == "A" and node["raw_index"] >= npre)}
        self.floor = _floors(self.nodes, self.edges, self.mutable)
        self.table = prime(self.endpoint, self.dimension, self.word.h)
        self.semantic_sha256 = digest(self.raw)
        self.graph_sha256 = digest(dict(nodes=self.nodes, edges=self.edges,
            floors=self.floor, mutable=sorted(self.mutable)))
        self.signature = E._trusted()._boundary_signature(self.raw)
        self.signature["warps"] = deepcopy(raw.get("warps", []))
        self.signature["prelude"] = deepcopy(raw["A"][:npre])
        self.extra_frozen = tuple(frozen_fields or ())
        self.last_certificate = None

    def summary(self):
        return dict(status="PASS", input_semantic_sha256=self.semantic_sha256,
            graph_sha256=self.graph_sha256, node_count=len(self.nodes), edge_count=len(self.edges),
            mutable_nodes=len(self.mutable), local_profile=self.word.paid,
            ordered_helpers=list(self.word.helpers), endpoint=str(self.endpoint),
            private_buffers=len(self.raw.get("helper_final", {})),
            source_attribution=self.attribution,
            caveat="Feasible input and cleanup checked; upstream changed scalar identity remains a separate obligation")

    def _materialize(self, assignment, selected):
        E, result = _trusted(), deepcopy(self.raw)
        W = E._W()
        edits = []
        for v in sorted(selected):
            node = self.nodes[v]
            section, position = node["section"], node["raw_index"]
            need(section in ("A", "B", "restore") and position is not None, "mutable gate address")
            before = result[section][position][-1]
            result[section][position][-1] = list(assignment[v])
            edits.append(dict(node=v, section=section, position=position,
                              before=before, after=list(assignment[v])))
        canonical = W.WordData(result, self.attribution, assert_profile=False)
        need(canonical.helpers == self.word.helpers and canonical.start == self.word.start
             and canonical.end == self.word.end, "ordered roles and all endpoints unchanged")
        need(E._trusted()._widths(canonical) == E._trusted()._widths(self.word), "ordered physical widths unchanged")
        need(canonical.centre_paid == self.word.centre_paid, "fixed centre descents unchanged")
        old_edges = _edge_profile(self.nodes, self.edges)
        new_edges = _edge_profile(self.nodes, self.edges, assignment)
        expected = Counter(self.word.paid)
        expected.subtract(old_edges)
        expected.update(new_edges)
        need(all(n >= 0 for n in expected.values()) and E._profile(expected) == canonical.paid,
             "independent full canonical profile equals edge-delta profile")
        need(E._mass(canonical.paid) == E._mass(self.word.paid), "exact complete rank mass unchanged")
        result["report"]["local_profile"] = {str(r): n for r, n in canonical.paid.items()}
        result["cleanup"] = W.derived_borrow_cleanup(canonical)
        complete = W.WordData(result, self.attribution)
        need(complete.paid == canonical.paid and W.cleanup_check(complete)["exact"],
             "regenerated literal cleanup and complete paid bill")
        signature = E._trusted()._boundary_signature(result)
        signature["warps"] = deepcopy(result.get("warps", []))
        signature["prelude"] = deepcopy(result["A"][:int(result.get("prelude_events", 0))])
        need(signature == self.signature, "all cut/warp/prelude/endpoint/buffer interfaces fixed")
        for name in self.extra_frozen:
            need(result.get(name) == self.raw.get(name), "additional fixed field: "+name)
        for section in ("A", "B", "restore"):
            need(len(result[section]) == len(self.raw[section]) and
                 all(a[:-1] == b[:-1] for a, b in zip(result[section], self.raw[section])),
                 "scalar event word unchanged by refit")
        return result, complete, edits

    def optimize_one(self, normal, endpoint=None, cpu_seconds=120, include_word=True,
                     include_full_certificate=False):
        begin = time.process_time()
        need(endpoint is None or Fraction(endpoint) == self.endpoint, "registered objective endpoint fixed")
        need(cpu_seconds > 0, "positive internal CPU budget")
        ora = Oracle(self.table, cpu_seconds)
        base = dict(normal=normal, endpoint=str(self.endpoint), dimension=self.dimension,
            input_semantic_sha256=self.semantic_sha256, graph_sha256=self.graph_sha256,
            source_attribution=self.attribution, original_profile=self.word.paid,
            native_admission="UNRUN_REQUIRED_FOR_CHANGED_FRAMES",
            scope="one fixed hyperplane and all simultaneous predecessor-closed caps on this feasible input labeling")
        try:
            network, data = _network(self.nodes, self.edges, self.mutable, self.floor,
                                     normal, self.word.h, ora)
            total, counts = network.flow(data["source"], data["sink"])
            reached = network.reachable(data["source"])
            selected = {v for v in data["active"] if data["index"][v] in reached}
            assignment = _validate_selection(self.nodes, self.edges, self.mutable, self.floor, data, selected)
            certificate = network.certificate(data["source"], data["sink"], total, reached)
            delta = ora.sub(total, data["total_prize"])
            need(ora.sign(delta) <= 0, "empty cap set gives zero objective upper bound")
            candidate, word, edits = self._materialize(assignment, selected)
            _check_objective(delta, self.word.paid, word.paid, ora)
            lo, hi = ora.bounds(delta)
            outcome = "IMPROVED" if ora.sign(delta) < 0 else "NO_GAIN"
            certificate.update(vertex_to_graph_node=data["active"],
                total_prize_coefficients=list(data["total_prize"]),
                hard_capacity_coefficients=list(data["hard_capacity"]),
                objective_coefficients=list(delta), selected_graph_nodes=sorted(selected),
                cost_intervals=[[str(lo), str(hi)] for lo, hi in self.table])
            self.last_certificate = certificate
            certificate_hash = digest(certificate)
            compact_certificate = dict(status="PASS", verified_in_memory=True,
                graph_sha256=self.graph_sha256, full_certificate_sha256=certificate_hash,
                arc_count=len(certificate["arcs"]),
                arc_capacity_flow_sha256=digest(certificate["arcs"]),
                cost_table_sha256=digest(certificate["cost_intervals"]),
                selected_graph_nodes=sorted(selected),
                value_coefficients=list(total), cut_coefficients=certificate["cut_coefficients"],
                total_prize_coefficients=list(data["total_prize"]),
                objective_coefficients=list(delta),
                checks=certificate["independent_checks"],
                reconstruct="Rebuild sorted active-node network from pinned feasible input graph and normal; retained nominees may export the full witness")
            base.update(status="PASS", outcome=outcome, exact_optimum_verified=True,
                candidate_semantic_sha256=digest(candidate), profile=word.paid,
                profile_delta={r: value for r, value in enumerate(delta) if value},
                delta_interval=[str(lo), str(hi)], frame_edits=edits,
                selected_count=len(selected), active_count=len(data["active"]),
                flow_statistics=counts,
                certificate=certificate if include_full_certificate else compact_certificate,
                certificate_sha256=certificate_hash,
                word=candidate if include_word else None)
        except UnresolvedSign as error:
            base.update(status="EXPLORATORY", outcome="UNRESOLVED_SIGN", error=str(error),
                        exact_optimum_verified=False)
        except CpuLimit as error:
            base.update(status="TIMEOUT", outcome="INCOMPLETE", error=str(error),
                        exact_optimum_verified=False)
        base["cpu_seconds"] = time.process_time()-begin
        base["comparison_count"] = ora.calls
        return base

    def export_certificate(self):
        """Full already-checked witness for a retained nominee, without rerunning flow."""
        need(self.last_certificate is not None, "no completed exact certificate available")
        return deepcopy(self.last_certificate)


def prepare(raw, attribution, endpoint, dimension=73, frozen_fields=None):
    return Prepared(raw, attribution, endpoint, dimension, frozen_fields)


def optimize_one(prepared, normal, endpoint=None, cpu_seconds=120, include_word=True,
                 include_full_certificate=False):
    return prepared.optimize_one(normal, endpoint, cpu_seconds, include_word, include_full_certificate)


def controls_task(endpoint, seed, cpu_seconds=60):
    """Synthetic graph controls; execute only in a registered pool task."""
    E = _trusted()
    ora = Oracle(prime(endpoint), cpu_seconds)
    full = E._basis([1, 2, 4, 8])
    frame = E._basis([1, 2])
    nodes = [dict(frame=()) for _ in range(3)] + [dict(frame=frame) for _ in range(2)]
    nodes += [dict(frame=full) for _ in range(3)]
    edges = [(0, 3, 0, False), (1, 3, 1, False), (3, 4, 1, False),
             (2, 4, 2, False), (3, 5, 0, False), (4, 6, 1, False), (4, 7, 2, False)]
    mutable, floors = {3, 4}, [n["frame"] if i not in (3, 4) else () for i, n in enumerate(nodes)]
    network, data = _network(nodes, edges, mutable, floors, 1, 4, ora)
    total, counts = network.flow(data["source"], data["sink"])
    reached = network.reachable(data["source"])
    selected = {v for v in data["active"] if data["index"][v] in reached}
    assignment = _validate_selection(nodes, edges, mutable, floors, data, selected)
    before, after = _edge_profile(nodes, edges), _edge_profile(nodes, edges, assignment)
    need(before == {2: 6} and after == {1: 3, 3: 3} and selected == {3, 4},
         "collective fixture exact optimum and profiles")
    delta = ora.sub(total, data["total_prize"])
    need(delta == ora.sub(_profile_vector(after, ora), _profile_vector(before, ora))
         and ora.sign(delta) < 0, "strict collective exact gain")
    certificate = network.certificate(data["source"], data["sink"], total, reached)
    single = _validate_selection(nodes, edges, mutable, floors, data, {3})
    single_delta = ora.sub(_profile_vector(_edge_profile(nodes, edges, single), ora),
                           _profile_vector(before, ora))
    need(ora.sign(single_delta) > 0, "first single lowering is strictly worse")
    checks = ["exact_collective_gain", "single_lowering_strictly_worse", "exact_flow_cut_certificate"]
    brute = []
    for bits in range(4):
        choice = {v for j, v in enumerate((3, 4)) if bits & (1 << j)}
        try:
            frames = _validate_selection(nodes, edges, mutable, floors, data, choice)
        except ValueError:
            brute.append(dict(selected=sorted(choice), feasible=False))
            continue
        cost = ora.sub(_profile_vector(_edge_profile(nodes, edges, frames), ora),
                       _profile_vector(before, ora))
        need(ora.sign(ora.sub(cost, delta)) >= 0, "flow optimum beats every exact tiny-domain candidate")
        brute.append(dict(selected=sorted(choice), feasible=True, delta_coefficients=list(cost)))
    need(sum(row["feasible"] for row in brute) == 3, "complete four-subset control domain")
    checks.append("all_four_subsets_bruteforce")
    forward_schedule = _close_selected({3, 4}, edges, data)
    reverse_schedule = _close_selected({3, 4}, edges, data, reverse=True)
    need(forward_schedule == reverse_schedule and forward_schedule[0] == selected,
         "fixed cap set has identical assignment and emitted-message set under reversed schedules")
    need(_close_selected({4}, edges, data)[0] == selected, "successor fact closes onto predecessor")
    checks.append("cap_schedules_and_emission_sets_agree")
    try:
        _validate_selection(nodes, edges, mutable, floors, data, {4})
    except ValueError:
        checks.append("missing_predecessor_rejected")
    else:
        raise ValueError("illegal isolated successor cap accepted")
    bad_floor = list(floors)
    bad_floor[3] = frame
    network2, data2 = _network(nodes, edges, mutable, bad_floor, 1, 4, ora)
    try:
        _validate_selection(nodes, edges, mutable, bad_floor, data2, {3, 4})
    except ValueError:
        checks.append("fixed_floor_rejected")
    else:
        raise ValueError("excluded floor cap accepted")
    equal_nodes = deepcopy(nodes)
    equal_nodes[5]["frame"] = frame
    equal_edges = [(u, v, r, (u, v) == (3, 5)) for u, v, r, _ in edges]
    equal_floors = [n["frame"] if i not in mutable else () for i, n in enumerate(equal_nodes)]
    _network3, data3 = _network(equal_nodes, equal_edges, mutable, equal_floors, 1, 4, ora)
    try:
        _validate_selection(equal_nodes, equal_edges, mutable, equal_floors, data3, {3, 4})
    except ValueError:
        checks.append("equality_not_inclusion_rejected")
    else:
        raise ValueError("cut equality was relaxed to inclusion")
    off_frame = dict(data, intersections=list(data["intersections"]))
    off_frame["intersections"][3] = E._basis([1])
    try:
        _validate_selection(nodes, edges, mutable, floors, off_frame, {3})
    except ValueError:
        checks.append("same_rank_wrong_orientation_rejected")
    else:
        raise ValueError("same-rank frame inside literal cap but outside registered hyperplane accepted")
    for rank, name in ((1, "missing_paid_child"), (3, "missing_successor_climb")):
        damaged = dict(after)
        damaged[rank] -= 1
        try:
            _check_objective(delta, before, damaged, ora)
        except ValueError:
            checks.append(name+"_rejected")
        else:
            raise ValueError(name+" passed complete objective checker")
    try:
        network.certificate(data["source"], data["sink"], ora.add(total, ora.unit(1)), reached)
    except ValueError:
        checks.append("forged_flow_value_rejected")
    else:
        raise ValueError("forged max-flow equality accepted")
    uncertain = Oracle([(Fraction(0), Fraction(0)), (Fraction(0), Fraction(1))], cpu_seconds)
    try:
        uncertain.sign((0, 1))
    except UnresolvedSign:
        checks.append("straddling_sign_not_zero")
    else:
        raise ValueError("unresolved nonzero coefficient vector treated as zero")
    return dict(status="PASS", seed=seed, synthetic=True, checks=checks,
        original_profile=before, collective_profile=after,
        collective_delta_coefficients=list(delta), single_delta_coefficients=list(single_delta),
        exact_certificate=certificate, flow_statistics=counts,
        brute_force_subsets=brute,
        closure_schedule=dict(selected=sorted(forward_schedule[0]),
                              emitted_edges=[list(e) for e in sorted(forward_schedule[1])]),
        caveat="Analytic fixture until this registered control task is executed; no claim about source-word gains")
