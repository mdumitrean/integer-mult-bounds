"""G3: source-bound scalar triangle contractions; coordinator execution only.

Elementary transvection identities are credited to the classical Steinberg
relations and Dugongue's PR548 guarded contractions. Current literal words:
Jeremy Kothe/PR2957, with the full PR2917/2930 and inherited source attribution.
No fetched implementation is imported. No experiment runs at import time.
"""
from __future__ import annotations

from collections import Counter
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

RR = Path(__file__).resolve().parents[2]
REPO = RR.parents[1]
ENDPOINT = Q(1723717415070738170971, 10**24)
MAX_SPAN = 15
PRICE_CAP = 128
SECTIONS = ("A", "B", "restore")
EXPECTED_LOCAL = {1: 2412, 2: 636, 3: 276, 4: 116, 5: 26, 8: 8}
EXPECTED_WIDTHS = {4: 26, 5: 2, 7: 62, 8: 96, 9: 222}
TRUSTED = {
    "wordio": (RR / "pipeline/wordio.py", "a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4"),
    "admission": (RR / "pipeline/continuation/admission.py", "4feb94bb7b53d37a97233ef7a2556f9931d78f8ac6776f6d16fd458373002ec5"),
    "ceiling": (REPO / "research/t74-joint-twelve-retired7/vendor/ceiling.py", "86a1432870b3b21d8454106ec9162fddc0471472d9214c590a1420f2426cedfc"),
}
_MODULES = {}
_WORDS = {}
_COSTS = None
_CHILD_COSTS = None


def need(test, message):
    if not test:
        raise ValueError(message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode())


def _module(name):
    if name not in _MODULES:
        path, expected = TRUSTED[name]
        need(sha(path.read_bytes()) == expected, "trusted source drift: " + str(path))
        need(not sys.flags.optimize, "G3 requires enabled assertions")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_g3_" + name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _MODULES[name] = module
    return _MODULES[name]


def _json(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json(x) for x in value]
    if isinstance(value, set):
        return [_json(x) for x in sorted(value)]
    if hasattr(value, "item"):
        return value.item()
    return value


def _profile(value):
    return {int(k): int(v) for k, v in sorted(value.items(), key=lambda p: int(p[0])) if v}


def _mass(value):
    return sum(r*n for r, n in value.items())


def _widths(word):
    return [len(word.end[r])-len(word.start[r]) for r in word.helpers]


def _boundary_signature(raw):
    fields = ("ports", "centers", "center_frames", "cut", "helper_final",
              "initial_corrections", "removed", "start_extra", "target_levels",
              "prelude_events", "compensation", "precondition", "kind")
    return {key: deepcopy(raw.get(key)) for key in fields}


def prepare(records):
    """Parent-only once preparation; records contain inert raw dicts + credits.

    The coordinator authenticates acquisition bytes before calling. This binds
    the complete raw object, exact published profile, inventory and endpoints.
    Cost tables and large canonical words are loaded once before pool forks.
    """
    global _COSTS, _CHILD_COSTS
    need(not _WORDS, "G3 prepare is once-only")
    need(set(records) == {"base", "extra"}, "both pinned providers required")
    W = _module("wordio")
    F, _ = W.toolkit()
    # Import the trusted graph adapter before the coordinator snapshots loaded
    # source hashes and forks; candidate graphs themselves are task-specific.
    W.borrow_modules()
    ceiling = _module("ceiling")
    _COSTS = F.Costs(str(ENDPOINT))
    _CHILD_COSTS = {r: ceiling.child_cost(r, 73, ENDPOINT) for r in range(1, 10)}
    summary = {}
    for provider in sorted(records):
        rec = records[provider]
        # Source adapter owns the once-loaded immutable raw payload. A complete
        # word copy is made only when a selected contraction is constructed.
        raw, attribution = rec["raw"], deepcopy(rec["attribution"])
        word = W.WordData(raw, attribution)
        widths = _widths(word)
        need(word.paid == EXPECTED_LOCAL, "published PR2957 paid profile")
        need(dict(Counter(widths)) == EXPECTED_WIDTHS, "published PR2957 width inventory")
        need(len(word.helpers) == 408 and len(raw["helper_final"]) == 82,
             "fixed helper and private-buffer counts")
        need(len(word.live) == 632 and word.v == 112 and word.n == 704,
             "pinned finite word geometry")
        _WORDS[provider] = dict(raw=raw, attribution=attribution,
            source_pin=deepcopy(rec.get("source_pin", {})), canonical=word,
            semantic_sha256=digest(raw), widths=widths,
            boundaries=_boundary_signature(raw))
        summary[provider] = dict(semantic_sha256=digest(raw), local_profile=word.paid,
            width_inventory=dict(Counter(widths)), ordered_helpers=list(word.helpers),
            private_buffers=82, physical_families=66804,
            source_attribution=attribution, source_pin=deepcopy(rec.get("source_pin", {})))
    return dict(status="PASS", providers=summary, endpoint=str(ENDPOINT),
                trusted_sources={str(p.relative_to(REPO)): h for p, h in TRUSTED.values()})


def _add(g):
    return (isinstance(g, (tuple, list)) and len(g) == 6 and g[0] == "add"
            and type(g[1]) is int and type(g[2]) is int and g[1] != g[2]
            and type(g[3]) is int and type(g[4]) is int and g[4] > 0
            and g[3] != 0 and (g[4] & (g[4]-1)) == 0)


def commute(g, h):
    """Exact registered sufficient scalar-add commutation predicate."""
    return _add(g) and _add(h) and g[2] != h[1] and h[2] != g[1]


def _segments(raw, section):
    gates = raw[section]
    if section == "A":
        cuts = [int(raw.get("prelude_events", 0)), len(gates)]
    elif section == "B":
        cuts = sorted({0, len(gates)} | {int(w[0]) for w in raw["warps"]})
    else:
        cuts = [0, len(gates)]
    for first, last in zip(cuts, cuts[1:]):
        need(0 <= first <= last <= len(gates), "invalid scalar segment boundary")
        yield first, last


def _same_segment(raw, section, positions):
    return any(first <= min(positions) and max(positions) < last
               for first, last in _segments(raw, section))


def _triangle(gates, positions, target_v):
    selected = [gates[p] for p in positions]
    if not all(_add(g) for g in selected):
        return None
    targets = Counter(g[1] for g in selected)
    if sorted(targets.values()) != [1, 2]:
        return None
    i = next(r for r, n in targets.items() if n == 2)
    j = next(r for r, n in targets.items() if n == 1)
    B = next(p for p in positions if gates[p][1] == j)
    k = gates[B][2]
    if len({i, j, k}) != 3 or any(target_v <= r < 2*target_v for r in (i, j, k)):
        return None
    As = [p for p in positions if gates[p][1:3] == [i, j]]
    Cs = [p for p in positions if gates[p][1:3] == [i, k]]
    if len(As) != 1 or len(Cs) != 1:
        return None
    A, C = As[0], Cs[0]
    a, b, c = (Q(gates[p][3], gates[p][4]) for p in (A, B, C))
    orient = "AB_plus" if A < B else "BA_minus"
    if c != (a*b if A < B else -a*b):
        return None
    return dict(i=i, j=j, k=k, A=A, B=B, C=C, a=str(a), b=str(b),
                chord=str(c), orientation=orient)


def _exposure(gates, positions):
    """All stable splits; first valid split and explicit adjacent swaps."""
    first, last = min(positions), max(positions)
    selected = set(positions)
    others = [p for p in range(first, last+1) if p not in selected]
    for split in range(len(others)+1):
        before, after = others[:split], others[split:]
        if any(not commute(gates[p], gates[q]) for p in before for q in positions if q < p):
            continue
        if any(not commute(gates[p], gates[q]) for p in after for q in positions if q > p):
            continue
        target = before + list(positions) + after
        order, swaps = list(range(first, last+1)), []
        for dest, origin in enumerate(target):
            loc = order.index(origin)
            while loc > dest:
                left, right = order[loc-1], order[loc]
                need(commute(gates[left], gates[right]), "exposure inversion did not commute")
                swaps.append([left, right])
                order[loc-1], order[loc] = right, left
                loc -= 1
        need(order == target, "stable exposure permutation")
        return dict(split=split, before=before, after=after, exposed_order=target,
                    adjacent_swaps=swaps)
    return None


def _candidate(raw, provider, section, positions, parent_sha):
    positions = tuple(positions)
    if not (len(positions) == 3 and positions == tuple(sorted(set(positions)))
            and positions[-1]-positions[0] <= MAX_SPAN):
        return None
    if not _same_segment(raw, section, positions):
        return None
    gates = raw[section]
    tri = _triangle(gates, positions, int(raw["report"]["v"]))
    if tri is None:
        return None
    exposure = _exposure(gates, positions)
    if exposure is None:
        return None
    first, last = positions[0], positions[-1]
    core = dict(provider=provider, section=section, positions=list(positions),
                orientation=tri["orientation"], split=exposure["split"])
    return dict(**core, candidate_id=digest(core), parent_semantic_sha256=parent_sha,
                triangle=tri, exposure=exposure,
                original_gates=[deepcopy(gates[p]) for p in positions],
                interval_sha256=digest(gates[first:last+1]))


def _sort_key(candidate):
    return (SECTIONS.index(candidate["section"]), tuple(candidate["positions"]),
            candidate["orientation"], candidate["split"])


def census_task(spec):
    provider, seed = spec["provider"], int(spec["seed"])
    state = _WORDS[provider]
    raw = state["raw"]
    work = [(sec, a, b) for sec in SECTIONS for a, b in _segments(raw, sec)]
    random.Random(seed).shuffle(work)
    counts = Counter(segments=len(work), raw_triples=0,
                     coefficient_identity_matches=0, exposure_rejections=0,
                     exposed_candidates=0)
    candidates = []
    begin = time.process_time()
    for section, first, last in work:
        gates = raw[section]
        for p in range(first, max(first, last-2)):
            for q in range(p+1, min(last-1, p+MAX_SPAN)):
                for r in range(q+1, min(last, p+MAX_SPAN+1)):
                    counts["raw_triples"] += 1
                    positions = (p, q, r)
                    tri = _triangle(gates, positions, int(raw["report"]["v"]))
                    if tri is None:
                        continue
                    counts["coefficient_identity_matches"] += 1
                    candidate = _candidate(raw, provider, section, positions, state["semantic_sha256"])
                    if candidate is None:
                        counts["exposure_rejections"] += 1
                    else:
                        candidates.append(candidate)
                        counts["exposed_candidates"] += 1
    candidates.sort(key=_sort_key)
    need(len({c["candidate_id"] for c in candidates}) == len(candidates), "unique candidate addresses")
    return dict(status="PASS", provider=provider, seed=seed, complete=True,
        candidates=candidates, counts=dict(counts), candidate_set_sha256=digest(candidates),
        pricing_cap=PRICE_CAP, unpriced_if_cap_applied=max(0, len(candidates)-PRICE_CAP),
        source_attribution=deepcopy(state["attribution"]), source_pin=deepcopy(state["source_pin"]),
        parent_semantic_sha256=state["semantic_sha256"],
        schedule=dict(seed=seed, section_segments=work), cpu_seconds=time.process_time()-begin)


def _sequential_matrix(gates, dual=False):
    """Independent exact sequential-row oracle; deliberately no recognizer use."""
    regs = sorted({r for g in gates for r in g[1:3]})
    rows = {r: {c: Q(int(c == r)) for c in regs} for r in regs}
    for g in gates:
        need(g[0] == "add" and g[1] != g[2], "matrix oracle supports nonself scalar adds")
        target, source, q = g[1], g[2], Q(g[3], g[4])
        if dual:
            # Inverse transpose of a chronological product applies each
            # elementary inverse transpose in that same chronological order.
            target, source, q = source, target, -q
        old_source = rows[source].copy()
        rows[target] = {c: rows[target][c]+q*old_source[c] for c in regs}
    return rows


def _construct(state, candidate):
    raw, provider = state["raw"], candidate["provider"]
    need(candidate["parent_semantic_sha256"] == state["semantic_sha256"], "stale parent word")
    expected = _candidate(raw, provider, candidate["section"], candidate["positions"], state["semantic_sha256"])
    need(expected is not None and expected == candidate, "stale preimage or invalid registered exposure")
    section, tri, exp = candidate["section"], candidate["triangle"], candidate["exposure"]
    first, last = candidate["positions"][0], candidate["positions"][-1]
    original = raw[section]
    kept = [tri["B"], tri["A"]] if tri["orientation"] == "AB_plus" else [tri["A"], tri["B"]]
    new_ids = exp["before"] + kept + exp["after"]
    old_window, new_window = original[first:last+1], [original[p] for p in new_ids]
    need(_sequential_matrix(old_window) == _sequential_matrix(new_window),
         "independent complete-window sequential identity")
    need(_sequential_matrix(old_window, dual=True) == _sequential_matrix(new_window, dual=True),
         "independent complete-window inverse-transpose identity")
    result = deepcopy(raw)
    result[section] = deepcopy(original[:first] + new_window + original[last+1:])
    if section == "B":
        # All warps lie outside the original window. The first warp following
        # its end sees one fewer gate; equal-position ordering stays unchanged.
        result["warps"] = [[rec[0] - int(rec[0] > last)] + deepcopy(rec[1:])
                           for rec in raw["warps"]]
        need(all(not first < rec[0] <= last for rec in raw["warps"]), "hidden warp crossed")
    need(_boundary_signature(result) == state["boundaries"], "fixed endpoint/cut/compensation ABI")
    return result, dict(status="PASS", complete_window_matrix_identity=True,
        complete_window_inverse_transpose_identity=True,
        compensation_reuse="Exact non-target scalar interval operator identity, boundaries unchanged",
        semantic_warp_order_preserved=True, removed_gate=deepcopy(original[tri["C"]]),
        exposure_adjacent_swaps=deepcopy(exp["adjacent_swaps"]), private_buffers=82,
        physical_families=66804)


def _materialize(raw, graph, meta, assignment):
    W = _module("wordio")
    _, _, bp = W.borrow_modules()
    result = deepcopy(raw)
    for k, (_regs, default, section, index) in enumerate(graph.nodes):
        if section not in ("A", "B", "tail"):
            continue
        frame = list(assignment.get(k, default))
        if section == "A":
            result["A"][meta["A_idx"][index]][-1] = frame
        elif section == "B":
            result["B"][index][-1] = frame
        else:
            result["restore"][index][-1] = frame
    paid = Counter(graph.profile(assignment))
    paid.update(bp.centre_descents(result))
    result["report"]["local_profile"] = {str(k): n for k, n in sorted(paid.items()) if n}
    canonical = W.WordData(result, {"scope": "internal candidate materialization"}, assert_profile=True)
    result["cleanup"] = W.derived_borrow_cleanup(canonical)
    return result


def _moment_delta(new, old):
    delta = {r: new.get(r, 0)-old.get(r, 0) for r in sorted(set(new)|set(old))
             if new.get(r, 0) != old.get(r, 0)}
    lo = hi = Q(0)
    ceiling = _module("ceiling")
    costs = {}
    for r, n in delta.items():
        a, b = _CHILD_COSTS[r] if r in _CHILD_COSTS else ceiling.child_cost(r, 73, ENDPOINT)
        costs[r] = [str(a), str(b)]
        lo += n*(a if n >= 0 else b)
        hi += n*(b if n >= 0 else a)
    return dict(lower=str(lo), upper=str(hi), endpoint=str(ENDPOINT),
                exact_profile_identity=not delta, profile_delta=delta,
                child_cost_intervals=costs)


def _write_word(raw, output_dir, candidate_id):
    directory = Path(output_dir)
    if not directory.is_absolute():
        directory = RR / directory
    directory = directory.resolve()
    need(directory.is_relative_to(RR), "candidate artifacts restricted to r11")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (candidate_id + ".json.gz")
    payload = gzip.compress(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode(), mtime=0)
    need(not path.exists(), "immutable candidate artifact already exists")
    path.write_bytes(payload)
    return dict(path=str(path.relative_to(RR)), sha256=sha(payload), bytes=len(payload),
                semantic_sha256=digest(raw))


def price_task(spec):
    provider, seed, candidate = spec["provider"], int(spec["seed"]), spec["candidate"]
    state = _WORDS[provider]
    need(candidate["provider"] == provider, "candidate provider binding")
    begin = time.process_time()
    result = dict(provider=provider, seed=seed, candidate_id=candidate["candidate_id"],
        candidate=deepcopy(candidate), source_attribution=deepcopy(state["attribution"]),
        source_pin=deepcopy(state["source_pin"]),
        local_profile=None, width_inventory=None, moment_delta=None, word_artifact=None, word=None,
        optimizer=None, guards={},
        scope="Registered certified-surrogate frame output per contraction; not all-frame/global optimum or kappa admission")
    edited, guards = _construct(state, candidate)
    result["guards"] = guards
    W = _module("wordio")
    F, _ = W.toolkit()
    _, _, bp = W.borrow_modules()
    try:
        # Exactly one optimizer invocation per pool task. The coordinator's
        # 300-second task timer also covers graph construction/materialization;
        # do not replace or restart its SIGALRM with an inner solver timer.
        need(0 < int(spec.get("solver_timeout", 300)) <= 300, "registered task timeout")
        inline, meta = bp.build_problem(edited)
        graph = bp.BorrowGraph(inline, meta["eq_end"], check_literal=False,
                               tail_mutable=True, cut_equality=True)
        priced = F.optimal_frames(inline, _COSTS, graph=graph,
                                 check_literal=False, interval=True)
    except F.Infeasible as error:
        result.update(status="REJECTED_GUARD", guard_failure=str(error),
                      cpu_seconds=time.process_time()-begin)
        return result
    except TimeoutError as error:
        result.update(status="EXPLORATORY", unresolved=str(error),
                      cpu_seconds=time.process_time()-begin)
        return result
    except ValueError as error:
        if "domain too large" not in str(error):
            raise
        result.update(status="EXPLORATORY", unresolved="exact frame-domain resource cap: " + str(error),
                      cpu_seconds=time.process_time()-begin)
        return result
    result["optimizer"] = _json({k: priced[k] for k in ("certified", "cost", "profile", "parts", "interval")})
    built = _materialize(edited, graph, meta, priced["assign"])
    canonical = W.WordData(built, state["attribution"])
    old = state["canonical"]
    need(canonical.helpers == old.helpers and canonical.start == old.start and canonical.end == old.end,
         "ordered helper/start/end invariant")
    need(_widths(canonical) == state["widths"], "ordered physical width invariant")
    need(_boundary_signature(built) == state["boundaries"], "materialized fixed ABI")
    if built["A"][:built.get("prelude_events", 0)] != state["raw"]["A"][:built.get("prelude_events", 0)]:
        result.update(status="EXPLORATORY", unresolved="chosen optimizer assignment changes frozen entry prelude",
                      cpu_seconds=time.process_time()-begin)
        return result
    need(_mass(canonical.paid) == _mass(old.paid), "complete local paid rank mass")
    moment = _moment_delta(canonical.paid, old.paid)
    word_ref = _write_word(built, spec["output_dir"], candidate["candidate_id"])
    result.update(local_profile=canonical.paid, width_inventory=dict(Counter(_widths(canonical))),
        ordered_widths=_widths(canonical), moment_delta=moment,
        word_artifact=word_ref, word=word_ref,
        cpu_seconds=time.process_time()-begin,
        cleanup_sha256=digest(built["cleanup"]), compensation_sha256=digest(built["compensation"]))
    if not priced["certified"]:
        result.update(status="EXPLORATORY", unresolved="uncertified integer-surrogate optimization")
    elif Q(moment["upper"]) < 0:
        result["status"] = "PASS_CANDIDATE"
    elif Q(moment["lower"]) >= 0 or moment["exact_profile_identity"]:
        result["status"] = "NO_GAIN"
    else:
        result.update(status="EXPLORATORY", unresolved="exact moment interval straddles zero")
    return result


def controls_task(seed):
    seed = int(seed.get("seed")) if isinstance(seed, dict) else int(seed)
    begin = time.process_time()
    checks = []
    def check(name, condition):
        need(condition, "G3 control failed: " + name)
        checks.append(dict(name=name, status="PASS"))
    def gate(t, s, q):
        q = Q(q)
        return ["add", t, s, q.numerator, q.denominator, []]
    for a, b in itertools.product((-2, -1, 1, 2), repeat=2):
        A, B = gate(3, 4, a), gate(4, 5, b)
        for orientation in ("AB_plus", "BA_minus"):
            C = gate(3, 5, a*b if orientation == "AB_plus" else -a*b)
            before = [A, B, C] if orientation == "AB_plus" else [B, A, C]
            after = [B, A] if orientation == "AB_plus" else [A, B]
            check(f"identity_{orientation}_{a}_{b}", _sequential_matrix(before) == _sequential_matrix(after))
            check(f"dual_identity_{orientation}_{a}_{b}",
                  _sequential_matrix(before, dual=True) == _sequential_matrix(after, dual=True))
            check(f"recognizer_{orientation}_{a}_{b}", _triangle(before, (0, 1, 2), 112) is not None)
            bad = deepcopy(before); bad[2][3] *= -1
            check(f"wrong_sign_{orientation}_{a}_{b}", _triangle(bad, (0, 1, 2), 112) is None
                  and _sequential_matrix(bad) != _sequential_matrix(after)
                  and _sequential_matrix(bad, dual=True) != _sequential_matrix(after, dual=True))
            bad = deepcopy(before); bad[2][3] *= 2
            check(f"wrong_magnitude_{orientation}_{a}_{b}", _triangle(bad, (0, 1, 2), 112) is None
                  and _sequential_matrix(bad) != _sequential_matrix(after)
                  and _sequential_matrix(bad, dual=True) != _sequential_matrix(after, dual=True))
    A, B, C = gate(3, 4, 1), gate(4, 5, 1), gate(3, 5, 1)
    fake = dict(A=[], B=[A, B, C], restore=[], prelude_events=0,
                warps=[[1, 9, [], [], []]], report={"v": 112})
    check("hidden_warp_boundary", _candidate(fake, "base", "B", (0, 1, 2), digest(fake)) is None)
    repeated = [gate(3, 4, 1), gate(4, 3, 1), gate(3, 3, 1)]
    check("repeated_register", _triangle(repeated, (0, 1, 2), 112) is None)
    # Intervener writes both a chain target and source through one elementary
    # edge: it cannot move past A to the left or past B/C to the right.
    blocked = [A, gate(5, 3, 1), B, C]
    check("noncommuting_intervener", _exposure(blocked, (0, 2, 3)) is None)
    fake = dict(A=[A, B, C], B=[], restore=[], warps=[], prelude_events=0, report={"v": 112})
    fake_state = dict(raw=fake, semantic_sha256=digest(fake), boundaries=_boundary_signature(fake))
    good = _candidate(fake, "base", "A", (0, 1, 2), digest(fake))
    bad = deepcopy(good); bad["original_gates"][0][3] = 2
    try:
        _construct(fake_state, bad)
    except ValueError:
        stale_rejected = True
    else:
        stale_rejected = False
    check("stale_preimage", stale_rejected)
    return dict(status="PASS", seed=seed, checks=checks,
        unchanged_local_audits="Separate mandatory source2957.baseline_task for both providers and both seeds in coordinator runner",
        candidate_cleanup_controls="Deferred to retained-candidate independent validation; N/A only if no retained candidate",
        source_attribution={k: deepcopy(v["attribution"]) for k, v in _WORDS.items()},
        cpu_seconds=time.process_time()-begin)

