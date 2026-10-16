"""One registered inventory-preserving 55-bin packing circuit on PR2979.

Only the coordinator prepares data or launches experiments, through pool.py.
Acquired programs are never imported.  This is an integer pattern circuit
with exact indivisible-role transport, not an intrinsic sandpile Laplacian.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from copy import deepcopy
from fractions import Fraction as Q
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys
import time
from types import SimpleNamespace

RR = Path(__file__).resolve().parents[2]
REPO = RR.parents[1]
CEILING = REPO / "research/t74-joint-twelve-retired7/vendor/ceiling.py"
CEILING_SHA = "86a1432870b3b21d8454106ec9162fddc0471472d9214c590a1420f2426cedfc"
ENDPOINT = Q("1729033982646513517717/1000000000000000000000000")
TIE_SEED = 61129
DELTA = {1: 20, 3: 19, 5: -25, 48: 1}
Z = (4, 8, 9, 9, 9, 9)
G = (9, 9, 9)
A = (7, 9)
_STATE = None
_CTX = None
_COST = None


def need(test, message):
    if not test:
        raise ValueError(message)


def _json_keys(value):
    # Persisted JSON always has string keys; use that same ordering before save.
    if isinstance(value, dict):
        return {str(k): _json_keys(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_keys(v) for v in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(_json_keys(value), sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _tie(value, variant):
    return digest([TIE_SEED, variant, value])


class Limit(Exception):
    pass


class Guard:
    def __init__(self, seconds):
        self.begin = time.process_time()
        self.until = self.begin + seconds

    def tick(self):
        if time.process_time() > self.until:
            raise Limit("registered internal CPU guard")


class Flow:
    """Integral unit-flow network, independently checked on its original arcs."""
    def __init__(self, n):
        self.adj = [[] for _ in range(n)]
        self.arcs = []

    def arc(self, u, v, cap):
        need(type(cap) is int and cap >= 0 and u != v, "integer flow arc")
        i, j = len(self.adj[u]), len(self.adj[v])
        self.adj[u].append([v, j, cap])
        self.adj[v].append([u, i, 0])
        self.arcs.append((u, i, v, cap))
        return u, i

    def solve(self, s, t, guard):
        value = 0
        while True:
            guard.tick()
            previous = {s: None}
            queue = deque([s])
            while queue and t not in previous:
                u = queue.popleft()
                for i, (v, _reverse, residual) in enumerate(self.adj[u]):
                    if residual and v not in previous:
                        previous[v] = (u, i)
                        queue.append(v)
            if t not in previous:
                reached = set(previous)
                break
            amount, v = 10**9, t
            while v != s:
                u, i = previous[v]
                amount = min(amount, self.adj[u][i][2])
                v = u
            v = t
            while v != s:
                u, i = previous[v]
                edge = self.adj[u][i]
                edge[2] -= amount
                self.adj[v][edge[1]][2] += amount
                v = u
            value += amount
        balance = [0]*len(self.adj)
        cut, checked = 0, []
        for u, i, v, cap in self.arcs:
            flow = cap-self.adj[u][i][2]
            need(0 <= flow <= cap, "integral capacity bounds")
            balance[u] += flow
            balance[v] -= flow
            if u in reached and v not in reached:
                cut += cap
            checked.append([u, v, cap, flow])
        need(all(x == (value if v == s else -value if v == t else 0)
                 for v, x in enumerate(balance)), "flow conservation")
        need(cut == value, "integer max-flow/min-cut equality")
        return value, dict(value=value, cut=cut, nodes=len(self.adj), arcs=len(checked),
                           arc_flow_sha256=digest(checked), source_side=sorted(reached))


class Context:
    def __init__(self, base, model):
        self.base, self.model = base, model
        self.by_role = {}
        self.bins = defaultdict(list)
        self.family_use = {}
        for row0 in base.rows:
            row = tuple(row0)
            t, h, o, c, p, _ = row
            role, bin_ = (t, h), (o, c, p)
            need(role not in self.by_role, "unique baseline role")
            self.by_role[role] = row
            self.bins[bin_].append(role)
            key = (t, base.family_id(o, c, p))
            need(key not in self.family_use, "baseline family injectivity")
            self.family_use[key] = role
        self.bins = {b: tuple(sorted(rows)) for b, rows in self.bins.items()}
        self.pattern = {b: tuple(sorted(self.width_base(r) for r in rows))
                        for b, rows in self.bins.items()}
        self.z = sorted(b for b in self.bins if self.cap_base(b) == 48 and self.pattern[b] == Z)
        self.g = sorted(b for b in self.bins if self.cap_base(b) == 32 and self.pattern[b] == G)
        self.a = sorted(b for b in self.bins if self.cap_base(b) == 16 and self.pattern[b] == A)

    def width_base(self, role):
        return self.base.widths[role[0]][role[1]]

    def width(self, role):
        return self.width_base((role[0]//5, role[1]))

    def cap_base(self, b):
        return self.base.win[b[:2]][0]

    def family_base(self, b):
        return self.base.family_id(*b)

    def family(self, b):
        return self.model.family_id(*b)

    @staticmethod
    def clone_bin(b, k):
        return b[0]+74*k, b[1], b[2]

    @staticmethod
    def clone_role(role, k):
        return 5*role[0]+k, role[1]

    def roles(self, b, width=None):
        return [self.clone_role(r, k) for r in self.bins[b]
                if width is None or self.width_base(r) == width for k in range(5)]

    def row(self, role):
        t, h = role
        base = self.by_role[t//5, h]
        return t, h, base[2]+74*(t % 5), base[3], base[4], base[5]

    def members(self, bin_):
        o, c, p = bin_
        original, k = (o % 74, c, p), o//74
        return [self.clone_role(r, k) for r in self.bins[original]]

    def eligible(self, role, bin_, removed):
        t, h = role
        o, c, p = bin_
        cap, start, stop = self.model.win[o, c]
        if not start < t <= stop or not 0 <= p < self.model.ports or self.width(role) > cap:
            return False
        family = self.family(bin_)
        # The untouched five-copy fill uses only owner families from its own copy.
        if o//74 != t % 5:
            return True
        original_family = (family[0] % 74, family[1], family[2])
        previous = self.family_use.get((t//5, original_family))
        return previous is None or self.clone_role(previous, t % 5) in removed


def _transport(ctx, roles, demands, removed, guard):
    roles, bins = sorted(roles), sorted(demands)
    need(len(roles) == len(set(roles)) and sum(demands.values()) == len(roles),
         "exact transport supplies and demands")
    edges = [(r, b) for r in roles for b in bins if ctx.eligible(r, b, removed)]
    pairs = sorted({(r[0], b) for r, b in edges})
    node = 1
    rn = {r: node+j for j, r in enumerate(roles)}
    node += len(rn)
    cn = {x: node+j for j, x in enumerate(pairs)}
    node += len(cn)
    bn = {b: node+j for j, b in enumerate(bins)}
    node += len(bn)
    sink, net = node, Flow(node+1)
    for r in roles:
        net.arc(0, rn[r], 1)
    handles = {}
    for r, b in edges:
        handles[r, b] = net.arc(rn[r], cn[r[0], b], 1)
    for (t, b), u in cn.items():
        net.arc(u, bn[b], 1)  # one role from this call in this physical family
    for b in bins:
        net.arc(bn[b], sink, demands[b])
    value, certificate = net.solve(0, sink, guard)
    assignment = {}
    if value == len(roles):
        for (r, b), (u, i) in handles.items():
            if net.adj[u][i][2] == 0:
                need(r not in assignment, "one selected destination per role")
                assignment[r] = b
        need(set(assignment) == set(roles), "complete indivisible matching")
        need(Counter(assignment.values()) == Counter(demands), "exact destination multiplicities")
        need(len({(r[0], ctx.family(b)) for r, b in assignment.items()}) == len(roles),
             "transport call-family injectivity")
    certificate.update(required=len(roles), eligible_edges=len(edges), complete=value == len(roles))
    return assignment if value == len(roles) else None, certificate


def _cost_delta():
    global _COST
    if _COST is None:
        need(hashlib.sha256(CEILING.read_bytes()).hexdigest() == CEILING_SHA, "trusted tariff source pin")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles06_topple_ceiling", CEILING)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        intervals = {r: module.child_cost(r, 73, ENDPOINT) for r in DELTA}
        lo = sum(n*(intervals[r][0] if n >= 0 else intervals[r][1]) for r, n in DELTA.items())
        hi = sum(n*(intervals[r][1] if n >= 0 else intervals[r][0]) for r, n in DELTA.items())
        need(sum(r*n for r, n in DELTA.items()) == 0, "cycle exact rank mass")
        _COST = dict(endpoint=str(ENDPOINT), profile_delta=DELTA,
                     lower=str(lo), upper=str(hi), certified_strict_gain=hi < 0,
                     intervals={str(r): [str(a), str(b)] for r, (a, b) in intervals.items()},
                     child_count_delta=sum(DELTA.values()),
                     scope="Complete profile difference at the fixed endpoint, not native/outer admission")
    return deepcopy(_COST)


def prepare(adapterstate):
    global _STATE, _CTX
    need(_STATE is None, "once-only parent preparation")
    _STATE = adapterstate
    _CTX = Context(adapterstate["base_model"], adapterstate["model"])
    need(len(_CTX.z) == 6, "source T74 has six exceptional full48 bins")
    need(_CTX.base.calls == 666 and _CTX.model.calls == 3330, "exact five-copy chronology")
    need(callable(adapterstate["audit_rows"]), "trusted complete audit adapter")
    cost = _cost_delta()
    return dict(status="PASS", original_pattern_counts={"Z": len(_CTX.z), "G": len(_CTX.g), "A": len(_CTX.a)},
        outercases=60, variants_per_selected_neighborhood=300, moved_roles=69,
        touched_bins=55, touched_roles=215, delta=cost, source=adapterstate["source"],
        selection=dict(tie_seed=TIE_SEED, variants=4, A_bins=64, A_pairs=64, D_bins=16, F_bins=64))


def census_task(seed):
    need(_CTX is not None, "parent prepared context")
    cases = []
    for z in itertools.combinations(_CTX.z, 4):
        for variant in range(4):
            core = dict(z=[list(b) for b in z], variant=variant, selection_seed=TIE_SEED)
            cases.append(dict(**core, case_id=digest(core)))
    need(len(cases) == 60 and len({c["case_id"] for c in cases}) == 60, "complete immutable sixty-case domain")
    canonical = sorted(cases, key=lambda c: c["case_id"])
    random.Random(int(seed)).shuffle(cases)
    return dict(status="PASS", seed=int(seed), cases=cases, cases_sha256=digest(canonical),
                count=len(cases), source=_STATE["source"], scope="restricted sufficient constructor; selection runs inside each worker")


def _case_check(case):
    z = tuple(tuple(b) for b in case["z"])
    core = dict(z=[list(b) for b in z], variant=case["variant"], selection_seed=TIE_SEED)
    need(case == dict(**core, case_id=digest(core)), "registered immutable outercase")
    need(tuple(sorted(z)) == z and len(set(z)) == 4 and set(z) <= set(_CTX.z), "canonical four-Z choice")
    need(case["variant"] in range(4), "registered deterministic tie variant")
    return z, case["variant"]


def _bin_score(ctx, roles, b, remove_all=False):
    removed = set(ctx.roles(b)) if remove_all else set()
    targets = [ctx.clone_bin(b, k) for k in range(5)]
    eligible = {(r, target) for r in roles for target in targets if ctx.eligible(r, target, removed)}
    return {r for r, _b in eligible}, len(eligible)


def _injective(edges, left):
    selected = {}
    def visit(u, seen):
        for v in edges[u]:
            if v in seen:
                continue
            seen.add(v)
            if v not in selected or visit(selected[v], seen):
                selected[v] = u
                return True
        return False
    for u in left:
        if not visit(u, set()):
            return None
    return {u: v for v, u in selected.items()}


def _select(ctx, z, variant, guard, counts):
    zfamilies = {ctx.family_base(b) for b in z}
    if len(zfamilies) != 4:
        counts["Z_family_collision"] += 1
        return None
    r8 = [r for b in z for r in ctx.roles(b, 8)]
    scored_a = []
    for b in ctx.a:
        guard.tick()
        if ctx.family_base(b) in zfamilies:
            continue
        covered, edges = _bin_score(ctx, r8, b, remove_all=True)
        if covered:
            scored_a.append(((-len(covered), -edges, _tie(b, variant), b), b, covered))
    top_a = sorted(scored_a)[:64]
    counts["A_scored"] = len(scored_a)
    counts["A_retained"] = len(top_a)
    pairs = []
    for left, right in itertools.combinations(top_a, 2):
        a, b = left[1], right[1]
        if ctx.family_base(a) == ctx.family_base(b):
            continue
        covered = left[2] | right[2]
        key = (-len(covered), max(left[0][0], right[0][0]), _tie(sorted((a, b)), variant), tuple(sorted((a, b))))
        pairs.append((key, tuple(sorted((a, b)))))
    pairs = sorted(pairs)[:64]
    counts["A_pairs_retained"] = len(pairs)
    r4groups = {b: ctx.roles(b, 4) for b in z}
    r4 = [r for group in r4groups.values() for r in group]
    scored_g = []
    for b in ctx.g:
        guard.tick()
        if ctx.family_base(b) in zfamilies:
            continue
        covered, edges = _bin_score(ctx, r4, b)
        if covered:
            scored_g.append(((-len(covered), -edges, _tie(b, variant), b), b))
    top_f = [b for _score, b in sorted(scored_g)[:64]]
    counts["F_scored"] = len(scored_g)
    counts["F_retained"] = len(top_f)
    # Exact five-clone placement of each original width4 group is cached once.
    f_edges = {b: [] for b in z}
    for original in z:
        for target in top_f:
            demands = {ctx.clone_bin(target, k): 1 for k in range(5)}
            assignment, _cert = _transport(ctx, r4groups[original], demands, set(r4groups[original]), guard)
            counts["five_role_F_flows"] += 1
            if assignment is not None:
                f_edges[original].append(target)
    for _key, aa in pairs:
        guard.tick()
        counts["A_pairs_tried"] += 1
        removed_a = {r for b in aa for r in ctx.roles(b)}
        demands8 = {ctx.clone_bin(b, k): 2 for b in aa for k in range(5)}
        assignment8, _cert8 = _transport(ctx, r8, demands8, removed_a | set(r8), guard)
        if assignment8 is None:
            counts["A_flow_rejected"] += 1
            continue
        forbidden = zfamilies | {ctx.family_base(b) for b in aa}
        r7 = [r for b in aa for r in ctx.roles(b, 7)]
        scored_d = []
        for b in ctx.g:
            if ctx.family_base(b) in forbidden:
                continue
            # Optimistic removal of all three9s only ranks candidates; exact flow removes one.
            covered, edges = _bin_score(ctx, r7, b, remove_all=True)
            if covered:
                scored_d.append(((-len(covered), -edges, _tie(b, variant), b), b))
        top_d = [b for _key_d, b in sorted(scored_d)[:16]]
        counts["D_ranked"] += len(scored_d)
        for d in top_d:
            guard.tick()
            counts["D_tried"] += 1
            available = {b: [f for f in f_edges[b]
                              if ctx.family_base(f) not in forbidden | {ctx.family_base(d)}] for b in z}
            # Candidate F families must also be pairwise distinct, not merely bins.
            family_to_bin = {}
            family_edges = {}
            for b in z:
                family_edges[b] = []
                for f in available[b]:
                    fam = ctx.family_base(f)
                    family_to_bin.setdefault((b, fam), f)
                    if fam not in family_edges[b]:
                        family_edges[b].append(fam)
            matched = _injective(family_edges, list(z))
            if matched is None:
                counts["F_group_matching_rejected"] += 1
                continue
            ff = tuple(sorted(family_to_bin[b, matched[b]] for b in z))
            need(len(ff) == len(set(ff)) == 4, "four different F originals")
            for remove in range(3):
                old = ctx.bins[d][remove]
                removed9 = {ctx.clone_role(old, k) for k in range(5)}
                demands7 = {ctx.clone_bin(d, k): 2 for k in range(5)}
                assignment7, _cert7 = _transport(ctx, r7, demands7, removed_a | removed9, guard)
                counts["D_seven_flows"] += 1
                if assignment7 is not None:
                    return dict(z=z, g=tuple(sorted(ff+(d,))), a=aa,
                                selector_D=d, selector_removed9=remove,
                                family_distinct=True)
                counts["D_seven_rejected"] += 1
    return None


def _variant(ctx, neighborhood, d, remove, empty):
    z, g, a = (tuple(tuple(b) for b in neighborhood[k]) for k in ("z", "g", "a"))
    ff = tuple(b for b in g if b != d)
    need(len(z) == 4 and len(g) == 5 and len(a) == 2 and len(ff) == 4, "55-bin original grouping")
    all_original = z+g+a
    need(all(ctx.pattern[b] == Z and ctx.cap_base(b) == 48 for b in z)
         and all(ctx.pattern[b] == G and ctx.cap_base(b) == 32 for b in g)
         and all(ctx.pattern[b] == A and ctx.cap_base(b) == 16 for b in a),
         "exact source pattern and capacity identities")
    need(len({ctx.family_base(b) for b in all_original}) == 11, "eleven distinct original physical families")
    zcopies = [ctx.clone_bin(b, k) for b in z for k in range(5)]
    need(empty in zcopies and remove in range(3), "registered empty bin and removed9 choice")
    supplies = {
        4: [r for b in z for r in ctx.roles(b, 4)],
        8: [r for b in z for r in ctx.roles(b, 8)],
        7: [r for b in a for r in ctx.roles(b, 7)],
        9: ([r for b in a for r in ctx.roles(b, 9)] +
            [ctx.clone_role(ctx.bins[d][remove], k) for k in range(5)] +
            [r for r in ctx.members(empty) if ctx.width(r) == 9]),
    }
    demands = {
        4: {ctx.clone_bin(b, k): 1 for b in ff for k in range(5)},
        8: {ctx.clone_bin(b, k): 2 for b in a for k in range(5)},
        7: {ctx.clone_bin(d, k): 2 for k in range(5)},
        9: {b: 1 for b in zcopies if b != empty},
    }
    removed = {r for roles in supplies.values() for r in roles}
    need({w: len(rs) for w, rs in supplies.items()} == {4: 20, 8: 20, 7: 10, 9: 19}
         and len(removed) == 69, "exact69-moving-role decomposition")
    expected = {ctx.clone_bin(b, k): ((4, 9, 9, 9) if b in ff else (7, 7, 9, 9))
                for b in g for k in range(5)}
    expected.update({ctx.clone_bin(b, k): (8, 8) for b in a for k in range(5)})
    expected.update({b: (() if b == empty else (9, 9, 9, 9, 9)) for b in zcopies})
    return dict(supplies=supplies, demands=demands, removed=removed, expected=expected,
                D=d, removed9=remove, empty=empty)


def _validate_patch(ctx, variant, patch):
    need(set(patch) == variant["removed"], "all69 transported roles present exactly once")
    bins = {b: [r for r in ctx.members(b) if r not in variant["removed"]]
            for b in variant["expected"]}
    before_roles = {r for b in bins for r in ctx.members(b)}
    need(len(bins) == 55 and len(before_roles) == 215, "complete55-bin215-role block")
    for role, target in patch.items():
        need(target in bins and ctx.eligible(role, target, variant["removed"]),
             "transported role passes exact window and outside-family guards")
        bins[target].append(role)
    after_roles = [r for rows in bins.values() for r in rows]
    need(len(after_roles) == len(set(after_roles)) == 215 and set(after_roles) == before_roles,
         "complete actual role inventory conserved")
    seen = set()
    before_idle, after_idle = Counter(), Counter()
    updates = {}
    for b, roles in bins.items():
        cap = ctx.model.win[b[:2]][0]
        widths = tuple(sorted(ctx.width(r) for r in roles))
        need(sum(widths) <= cap, "actual destination capacity")
        need(widths == variant["expected"][b], "exact prescribed destination pattern")
        old_used = sum(ctx.width(r) for r in ctx.members(b))
        if old_used < cap:
            before_idle[cap-old_used] += 1
        if sum(widths) < cap:
            after_idle[cap-sum(widths)] += 1
        offset = 0
        for role in sorted(roles):
            need(ctx.eligible(role, b, before_roles), "all touched final role windows")
            key = role[0], ctx.family(b)
            need(key not in seen, "fresh simultaneous call-family injectivity")
            seen.add(key)
            updates[role] = tuple(role)+tuple(b)+(offset,)
            offset += ctx.width(role)
    delta = Counter(after_idle)
    delta.subtract(before_idle)
    need({r: n for r, n in delta.items() if n} == DELTA, "independent complete idle delta")
    need(sum(ctx.width(r) for r in before_roles) == 1795, "exact touched helper-width mass")
    return updates, dict(touched_bins=55, touched_roles=215, transported_roles=69,
        before_idle=dict(sorted(before_idle.items())), after_idle=dict(sorted(after_idle.items())),
        profile_delta=DELTA, rank_mass_delta=0, idle_child_count_delta=15,
        changed_call_family_sha256=digest(sorted((t, list(fam)) for t, fam in seen)))


def _attempt(ctx, variant, guard):
    patch, certificates = {}, {}
    for width in (8, 4, 7, 9):
        assignment, cert = _transport(ctx, variant["supplies"][width], variant["demands"][width],
                                      variant["removed"], guard)
        certificates[str(width)] = cert
        if assignment is None:
            return None, certificates, width
        patch.update(assignment)
    _updates, verified = _validate_patch(ctx, variant, patch)
    return patch, certificates, verified


def task(spec):
    guard = Guard(float(spec.get("max_seconds", 240)))
    case, seed, counts = spec["case"], int(spec["seed"]), Counter()
    result = dict(seed=seed, case=case, source=_STATE["source"],
                  scope="bounded selected-neighborhood constructor; no global allocation optimum or intrinsic Laplacian")
    try:
        z, variant = _case_check(case)
        neighborhood = _select(_CTX, z, variant, guard, counts)
        if neighborhood is None:
            result.update(status="NULL", outcome="NO_SELECTED_NEIGHBORHOOD", complete=True)
        else:
            result["neighborhood"] = neighborhood
            found = None
            for d in neighborhood["g"]:
                for remove in range(3):
                    for b in neighborhood["z"]:
                        for k in range(5):
                            guard.tick()
                            counts["transport_variants"] += 1
                            data = _variant(_CTX, neighborhood, d, remove, _CTX.clone_bin(b, k))
                            patch, certificates, verified = _attempt(_CTX, data, guard)
                            if patch is None:
                                counts["failed_width_"+str(verified)] += 1
                                continue
                            cost = _cost_delta()
                            need(cost["certified_strict_gain"], "registered exact circuit cost is strictly improving")
                            witness = dict(case=case, neighborhood=neighborhood, D=d, removed9=remove,
                                empty=data["empty"], moves=[[r[0], r[1], *dest] for r, dest in sorted(patch.items())],
                                verification=verified, flow_certificates=certificates, cost=cost)
                            witness["sha256"] = digest(witness)
                            found = witness
                            break
                        if found is not None:
                            break
                    if found is not None:
                        break
                if found is not None:
                    break
            if found is None:
                need(counts["transport_variants"] == 300, "all selected-neighborhood variants exhausted")
                result.update(status="NULL", outcome="NO_FLOW_WITNESS", complete=True)
            else:
                result.update(status="PASS", outcome="EXACT_ROLE_TRANSPORT_WITNESS", complete=True,
                              witness=found, native_supplier_outer="PENDING_SCALED_ADMISSION")
    except Limit as error:
        result.update(status="TIMEOUT", outcome="INCOMPLETE", complete=False, error=str(error))
    result.update(counts=dict(counts), cpu_seconds=time.process_time()-guard.begin)
    return result


def materialize_task(spec):
    begin = time.process_time()
    witness = deepcopy(spec["witness"])
    saved_hash = witness.pop("sha256")
    need(digest(witness) == saved_hash, "saved exact witness hash")
    registered_z, _variant_id = _case_check(witness["case"])
    neighborhood = {k: tuple(tuple(b) for b in witness["neighborhood"][k]) for k in ("z", "g", "a")}
    need(neighborhood["z"] == registered_z, "witness retains the registered exceptional-bin choice")
    if "case" in spec:
        need(spec["case"] == witness["case"], "materializer case binding")
    data = _variant(_CTX, neighborhood, tuple(witness["D"]), witness["removed9"], tuple(witness["empty"]))
    patch = {(t, h): (o, c, p) for t, h, o, c, p in witness["moves"]}
    need(len(patch) == len(witness["moves"]) == 69, "literal unique moved roles")
    updates, verified = _validate_patch(_CTX, data, patch)
    rows = [updates.get((row[0], row[1]), row) for row in _CTX.model.rows]
    expected = Counter(_CTX.model.expected_profile)
    expected.update(DELTA)
    expected = {int(r): n for r, n in sorted(expected.items()) if n}
    audit = _STATE["audit_rows"](rows, expected_profile=expected, require_profile=True, lift=True)
    need(audit["all_literal_rules_verified"] and audit["profile"] == expected,
         "fresh complete T370 literal audit")
    output = Path(spec["output_dir"]).resolve()
    need(output.is_relative_to(RR.resolve()), "artifacts stay inside authorized subtree")
    output.mkdir(parents=True, exist_ok=True)
    destination = output / "FILL.json.gz"
    need(not destination.exists(), "immutable new candidate fill")
    payload = dict(columns=_STATE["fill_module"].COLUMNS, dispatch_overrides=[], rows=rows,
        method="Five-copy PR2979 baseline plus one exact55-bin inventory-preserving circuit; all69 moved roles certified.")
    with destination.open("wb") as out:
        with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as compressed:
            compressed.write(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    profile_path = output / "PROFILE.json"
    need(not profile_path.exists(), "immutable new candidate profile")
    profile_path.write_text(json.dumps(expected, sort_keys=True, indent=2)+"\n")
    return dict(status="PASS", seed=int(spec["seed"]), witness_sha256=saved_hash,
        profile=expected, idle=audit["idle"], audit=audit, verification=verified,
        cost=_cost_delta(), fill_artifact=dict(path=str(destination.relative_to(RR)),
            sha256=hashlib.sha256(destination.read_bytes()).hexdigest(), bytes=destination.stat().st_size),
        profile_artifact=dict(path=str(profile_path.relative_to(RR)),
            sha256=hashlib.sha256(profile_path.read_bytes()).hexdigest()),
        source=_STATE["source"], cpu_seconds=time.process_time()-begin,
        native_supplier_outer="PENDING_SCALED_ADMISSION")


def _toy():
    original_bins = [(i, 48 if i < 4 else 32 if i < 9 else 16, 0) for i in range(11)]
    patterns = [Z]*4+[G]*5+[A]*2
    rows, widths = [], []
    for b, pattern in zip(original_bins, patterns):
        offset = 0
        for width in pattern:
            t = len(rows)
            rows.append((t, 0, *b, offset))
            widths.append([width])
            offset += width
    family = lambda o, c, p: (o, c, p)
    base = SimpleNamespace(rows=rows, widths=widths, win={b[:2]: (b[1], -1, 42) for b in original_bins},
                           family_id=family)
    model = SimpleNamespace(win={(b[0]+74*k, b[1]): (b[1], -1, 214)
                                 for b in original_bins for k in range(5)}, family_id=family, ports=112)
    context = Context(base, model)
    neighborhood = dict(z=tuple(original_bins[:4]), g=tuple(original_bins[4:9]), a=tuple(original_bins[9:]))
    data = _variant(context, neighborhood, original_bins[8], 0, original_bins[0])
    return context, data


def controls_task(seed):
    guard = Guard(60)
    context, data = _toy()
    patch, certificates, verified = _attempt(context, data, guard)
    need(patch is not None and len(patch) == 69, "complete synthetic55-bin215-role positive fixture")
    checks = ["synthetic_55_bins_215_roles_69_moves", "all_four_integral_transport_certificates"]
    role = sorted(patch)[0]
    target = patch[role]
    old_window = context.model.win[target[:2]]
    context.model.win[target[:2]] = (old_window[0], role[0], old_window[2])
    try:
        _validate_patch(context, data, patch)
    except ValueError:
        checks.append("strict_start_window_rejected")
    else:
        raise ValueError("illegal start-equality window accepted")
    context.model.win[target[:2]] = old_window
    broken = dict(patch)
    del broken[role]
    try:
        _validate_patch(context, data, broken)
    except ValueError:
        checks.append("omitted_role_rejected")
    else:
        raise ValueError("omitted transported role accepted")
    broken = dict(patch)
    nine = next(r for r in sorted(patch) if context.width(r) == 9)
    full_f = next(b for b, pattern in data["expected"].items() if pattern == (4, 9, 9, 9))
    broken[nine] = full_f
    try:
        _validate_patch(context, data, broken)
    except ValueError:
        checks.append("overcapacity_rejected")
    else:
        raise ValueError("overcapacity role assignment accepted")
    mini = SimpleNamespace(eligible=lambda r, b, removed: True, family=lambda b: b)
    match, certificate = _transport(mini, [(0, 0), (0, 1)], {(2, 8, 0): 2}, {(0, 0), (0, 1)}, guard)
    need(match is None and certificate["value"] == 1, "same-call family node has capacityone")
    checks.append("same_call_family_collision_rejected")
    cost = _cost_delta()
    need(cost["certified_strict_gain"], "exact signed circuit tariff")
    return dict(status="PASS", seed=int(seed), synthetic=True, checks=checks,
        verification=verified, flow_certificates=certificates, family_negative=certificate,
        cost=cost, cpu_seconds=time.process_time()-guard.begin,
        scope="Synthetic controls only; actual owner realization remains a separate registered task")
