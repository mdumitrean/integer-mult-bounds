"""R1: exact whole-context shears at the two PR2979 B-pair leads.

Source-only until coordinator registration and pool execution.  PR2979's
author proposes a stronger free-carrier re-pairing; this finite family tests
contextual basis changes and does not claim to implement that stronger lead.
Every fetched program remains inert.  Only pinned, previously trusted r11
utilities and the separately frozen collective-cap implementation are loaded.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction as Q
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
TRIANGLES = RR / "pipeline/continuation03/triangles.py"
TRIANGLES_SHA = "14bd46dd6be68f9e2337a6359ebe2f79ae61423a7306932b1a2a2c7cd98207dc"
CAPS = RR / "pipeline/continuation05/collective_caps.py"
# Filled from the independently reviewed final source before implementation freeze.
CAPS_SHA = "57e137d9c1c166d73121fad2ed8efa14c604d98ce202853e39fb0369619aae2f"
CAP_NORMALS = (7,)
PAIRS = ((363, 73), (395, 5))
INTERVALS = {
    (363, 73): ((663, 679), (675, 793), (791, 817), (663, 817)),
    (395, 5): ((715, 729), (725, 803), (801, 819), (715, 819)),
}
COEFFICIENTS = (Q(-2), Q(-1), Q(-1, 2), Q(1, 2), Q(1), Q(2))
_T = None
_C = None
_WORDS = {}
_REFERENCES = {}
_ENDPOINT = None
_COSTS = None
_CHILD_COSTS = None


def need(test, message):
    if not test:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode())


def _load(path, expected, name):
    need(sha(path.read_bytes()) == expected, "trusted source drift: " + str(path))
    need(not sys.flags.optimize, "enabled assertions required")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _trusted():
    global _T
    if _T is None:
        _T = _load(TRIANGLES, TRIANGLES_SHA, "styles_r1_frozen_utilities")
    return _T


def _caps():
    global _C
    if _C is None:
        _C = _load(CAPS, CAPS_SHA, "styles_r1_collective_caps")
    return _C


def _W():
    return _trusted()._module("wordio")


def _profile(value):
    return {int(r): int(n) for r, n in sorted(value.items(), key=lambda z: int(z[0])) if n}


def _mass(profile):
    return sum(int(r)*int(n) for r, n in profile.items())


def _add(target, source, coefficient, frame=()):
    coefficient = Q(coefficient)
    need(target != source and coefficient, "nonself nonzero scalar add")
    need(coefficient.denominator & (coefficient.denominator-1) == 0,
         "dyadic scalar coefficient")
    return ["add", int(target), int(source), coefficient.numerator,
            coefficient.denominator, list(frame)]


def prepare(records, endpoint, profile, inventory):
    """Coordinator parent preparation, once, after registration."""
    global _ENDPOINT, _COSTS, _CHILD_COSTS
    need(not _WORDS, "R1 preparation is once-only")
    need(set(records) == {"base", "extra"}, "both pinned PR2979 providers")
    _ENDPOINT = Q(endpoint)
    need(0 < _ENDPOINT < 1, "strictly concave rank tariff")
    T, W = _trusted(), _W()
    F, _ = W.toolkit()
    W.borrow_modules()
    _caps().prime(_ENDPOINT)         # pin/import and exact costs once before pool forks
    _COSTS = F.Costs(str(_ENDPOINT))
    ceiling = T._module("ceiling")
    _CHILD_COSTS = {r: ceiling.child_cost(r, 73, _ENDPOINT) for r in range(1, 10)}
    summary = {}
    for provider in sorted(records):
        rec = records[provider]
        raw, attribution = rec["raw"], deepcopy(rec["attribution"])
        canonical = W.WordData(raw, attribution)
        widths = T._widths(canonical)
        need(canonical.paid == _profile(profile), "pinned PR2979 local profile")
        need(dict(Counter(widths)) == _profile(inventory), "pinned PR2979 inventory")
        need(canonical.v == 112 and canonical.n == 704 and canonical.h == 9,
             "finite source geometry")
        need(len(canonical.helpers) == 408 and len(canonical.live) == 632,
             "helper and live-column counts")
        need(len(raw["helper_final"]) == rec.get("expected_buffers", 91) == 91,
             "91 private endpoints preserved")
        need(rec.get("expected_physical_families", 66813) == 66813,
             "source physical-stock declaration")
        need(not raw.get("early_cleanup"), "registered source has no early cleanup")
        semantic = digest(raw)
        need(semantic == rec["original_semantic_sha256"], "adapter semantic binding")
        _WORDS[provider] = dict(raw=raw, attribution=attribution, canonical=canonical,
            semantic_sha256=semantic, source_pin=deepcopy(rec.get("source_pin", {})),
            widths=widths, boundaries=T._boundary_signature(raw))
        summary[provider] = dict(semantic_sha256=semantic, local_profile=canonical.paid,
            width_inventory=dict(Counter(widths)), ordered_helpers=list(canonical.helpers),
            private_buffers=91, physical_families=66813,
            source_attribution=attribution, source_pin=deepcopy(rec.get("source_pin", {})))
    return dict(status="PASS", providers=summary, endpoint=str(_ENDPOINT),
        candidate_count_per_provider=96, cap_normals=list(CAP_NORMALS),
        source_files={str(TRIANGLES.relative_to(REPO)):TRIANGLES_SHA,
                      str(CAPS.relative_to(REPO)):CAPS_SHA},
        scope="Exact scalar context change; certified surrogate refit then one restricted exact cap; no native/kappa admission")


def _candidate(state, provider, pair, interval, orientation, coefficient):
    pair, interval = tuple(pair), tuple(interval)
    coefficient = Q(coefficient)
    need(pair in PAIRS and interval in INTERVALS[pair], "registered named interval")
    need(orientation in (0, 1) and coefficient in COEFFICIENTS,
         "registered shear orientation/coefficient")
    first, last = interval
    need(0 <= first < last <= len(state["raw"]["B"]), "literal B interval address")
    p, q = pair if orientation == 0 else pair[::-1]
    core = dict(provider=provider, pair=list(pair), interval=list(interval),
                orientation=orientation, target=p, source=q, coefficient=str(coefficient))
    warps = [(op, rec) for op, rec in enumerate(state["raw"]["warps"], 1)
             if first <= rec[0] < last]
    return dict(**core, candidate_id=digest(core),
        parent_semantic_sha256=state["semantic_sha256"],
        interval_sha256=digest(state["raw"]["B"][first:last]),
        interval_warps_sha256=digest(warps))


def census_task(spec):
    provider, seed = spec["provider"], int(spec["seed"])
    state = _WORDS[provider]
    begin = time.process_time()
    domain = [(pair, interval, orientation, coefficient) for pair in PAIRS
              for interval in INTERVALS[pair] for orientation in (0, 1)
              for coefficient in COEFFICIENTS]
    order = list(range(len(domain)))
    random.Random(seed).shuffle(order)
    by_index = {j:_candidate(state, provider, *domain[j]) for j in order}
    candidates = [by_index[j] for j in range(len(domain))]
    need(len(candidates) == len({c["candidate_id"] for c in candidates}) == 96,
         "complete unique literal registered domain")
    return dict(status="PASS", provider=provider, seed=seed, complete=True,
        candidates=candidates, candidate_set_sha256=digest(candidates),
        counts=dict(named_pairs=2, intervals_per_pair=4, shear_orientations=2,
                    nonzero_dyadic_coefficients=6, candidate_variants=96),
        schedule=dict(seed=seed, canonical_domain_indices=order),
        source_attribution=deepcopy(state["attribution"]), source_pin=deepcopy(state["source_pin"]),
        cpu_seconds=time.process_time()-begin)


enumerate_task = census_task


def _gate_conjugate(gate, p, q, t):
    """M E M^-1 for M = I+t e_pq, expanded in commuting scalar adds.

    Pair scales/internal pair interactions are outside this finite production.
    The two emitted terms share a source or target and therefore commute.
    """
    t = Q(t)
    if gate[0] != "add":
        need(gate[0] == "scale" and gate[1] not in (p, q),
             "unsupported pair scale or non-scalar gate")
        return [deepcopy(gate)]
    target, source, c = gate[1], gate[2], Q(gate[3], gate[4])
    need(target != source, "nonself source add")
    need(not (target in (p, q) and source in (p, q)),
         "internal pair interaction excluded")
    frame = gate[-1]
    if source == p:
        return [_add(target, p, c, frame), _add(target, q, -c*t, frame)]
    if target == q:
        return [_add(q, source, c, frame), _add(p, source, t*c, frame)]
    return [deepcopy(gate)]


def _oracle(gates, warps=(), dual=False, registers=()):
    """Independent exact free-operator sequential matrix, including warps.

    Warp records are (relative position, stable operator id, register).  Each
    monomial is an input column and an ordered tuple of formal operators.
    All rows, including unchanged identities, are compared in both orientations.
    """
    regs = set(registers)
    for gate in gates:
        need(gate[0] in ("add", "scale"), "oracle scalar grammar")
        regs.add(gate[1])
        if gate[0] == "add":
            regs.add(gate[2])
    regs.update(r for _, _, r in warps)
    rows = {r:{(r, ()):Q(1)} for r in regs}
    by_pos = {}
    for position, operator, register in warps:
        need(0 <= position <= len(gates), "oracle warp position")
        by_pos.setdefault(position, []).append((operator, register))
    for pos in range(len(gates)+1):
        for operator, register in by_pos.get(pos, []):
            letter = (int(operator), int(bool(dual)))
            rows[register] = {(col, (letter,)+word):value
                              for (col, word), value in rows[register].items()}
        if pos == len(gates):
            continue
        gate = gates[pos]
        if gate[0] == "scale":
            c = Q(gate[2], gate[3])
            need(c, "nonzero scale")
            if dual:
                c = 1/c
            rows[gate[1]] = {key:c*value for key, value in rows[gate[1]].items() if c*value}
        else:
            target, source, c = gate[1], gate[2], Q(gate[3], gate[4])
            need(target != source, "oracle nonself add")
            if dual:
                target, source, c = source, target, -c
            result = rows[target].copy()
            for key, value in rows[source].items():
                result[key] = result.get(key, Q(0))+c*value
                if not result[key]:
                    del result[key]
            rows[target] = result
    return rows


def _same_operator(left, right, old_warps=(), new_warps=()):
    regs = {r for g in left+right for r in (g[1:3] if g[0] == "add" else g[1:2])}
    regs.update(r for _, _, r in list(old_warps)+list(new_warps))
    return all(_oracle(left, old_warps, dual=dual, registers=regs) ==
               _oracle(right, new_warps, dual=dual, registers=regs) for dual in (False, True))


def _rewrite_window(gates, warps, p, q, coefficient):
    """Pure constructor used by both source construction and algebra controls."""
    t = Q(coefficient)
    need(p != q, "distinct shear registers")
    need(all(r not in (p, q) for _, _, r in warps), "pair-touching warp excluded")
    out = [_add(p, q, t)]
    mapping = {0:0}                    # a start-boundary warp remains before encode
    for j, gate in enumerate(gates):
        if j:
            mapping[j] = len(out)
        out.extend(_gate_conjugate(gate, p, q, t))
    out.append(_add(p, q, -t))
    mapping[len(gates)] = len(out)     # an end-boundary warp remains after decode
    moved = [(mapping[position], operator, r) for position, operator, r in warps]
    return out, moved, mapping


def _construct(state, candidate):
    expected = _candidate(state, candidate["provider"], candidate["pair"],
                          candidate["interval"], candidate["orientation"], candidate["coefficient"])
    need(candidate == expected, "stale parent/preimage or unregistered shear")
    raw = state["raw"]
    first, last = candidate["interval"]
    p, q, t = candidate["target"], candidate["source"], Q(candidate["coefficient"])
    v = state["canonical"].v
    need(not any(v <= r < 2*v for r in (p, q)), "named pair excludes targets")
    window = raw["B"][first:last]
    warps = [(rec[0]-first, op, rec[1])
             for op, rec in enumerate(raw["warps"], 1) if first <= rec[0] < last]
    try:
        rewritten, moved, mapping = _rewrite_window(window, warps, p, q, t)
    except ValueError as error:
        return None, dict(status="REJECTED_GUARD", predicate=str(error))
    registers = {r for g in window+rewritten
                 for r in (g[1:3] if g[0] == "add" else g[1:2])}
    registers.update(r for _, _, r in warps)
    need(_oracle(window, warps, registers=registers) ==
         _oracle(rewritten, moved, registers=registers),
         "independent full-window forward free-operator identity")
    need(_oracle(window, warps, dual=True, registers=registers) ==
         _oracle(rewritten, moved, dual=True, registers=registers),
         "independent full-window inverse-transpose free-operator identity")
    result = deepcopy(raw)
    result["B"] = deepcopy(raw["B"][:first])+rewritten+deepcopy(raw["B"][last:])
    shift = len(rewritten)-(last-first)
    result["warps"] = []
    for rec in raw["warps"]:
        pos = rec[0]
        newpos = (pos if pos < first else
                  first+mapping[pos-first] if pos < last else pos+shift)
        result["warps"].append([newpos]+deepcopy(rec[1:]))
    need(result["B"][:first] == raw["B"][:first] and
         result["B"][last+shift:] == raw["B"][last:], "all exterior scalar gates identical")
    need(_trusted()._boundary_signature(result) == state["boundaries"], "unchanged finite ABI")
    need(all(a[1:] == b[1:] for a, b in zip(raw["warps"], result["warps"])),
         "every warp payload/operator id unchanged")
    return result, dict(status="PASS", scalar_operator_identity=True,
        inverse_transpose_identity=True, formal_warp_identity=True,
        original_interval=[first, last], rewritten_interval=[first, last+shift],
        shear_matrix=dict(target=p, source=q, coefficient=str(t)),
        scalar_instruction_delta=shift,
        original_window_sha256=digest(window), rewritten_window_sha256=digest(rewritten),
        warp_positions_before=[[x[0]+first, x[1], x[2]] for x in warps],
        warp_positions_after=[[x[0]+first, x[1], x[2]] for x in moved],
        scope="Exact context recoding; no claim of free output-carrier removal")


def _moment_delta(new, old):
    delta = {r:new.get(r, 0)-old.get(r, 0) for r in sorted(set(new)|set(old))
             if new.get(r, 0) != old.get(r, 0)}
    lo = hi = Q(0)
    intervals = {}
    for rank, count in delta.items():
        a, b = _CHILD_COSTS[rank]
        intervals[rank] = [str(a), str(b)]
        lo += count*(a if count >= 0 else b)
        hi += count*(b if count >= 0 else a)
    return dict(lower=str(lo), upper=str(hi), exact_profile_identity=not delta,
                profile_delta=delta, endpoint=str(_ENDPOINT), child_cost_intervals=intervals)


def _invariants(state, raw):
    T, W = _trusted(), _W()
    canonical = W.WordData(raw, state["attribution"])
    old = state["canonical"]
    need(canonical.helpers == old.helpers and canonical.start == old.start and canonical.end == old.end,
         "ordered helpers and all fixed entry/end frames")
    need(T._widths(canonical) == state["widths"], "all ordered physical widths unchanged")
    need(_mass(canonical.paid) == _mass(old.paid), "full local paid mass")
    need(T._boundary_signature(raw) == state["boundaries"], "fixed finite ABI")
    need(raw["A"][:raw.get("prelude_events", 0)] ==
         state["raw"]["A"][:raw.get("prelude_events", 0)], "literal entry prelude")
    need(len(raw["helper_final"]) == 91, "unchanged private-buffer stock")
    need(raw["cleanup"] == W.derived_borrow_cleanup(canonical), "complete cleanup invoice")
    return canonical


def _refit(state, edited):
    T, W = _trusted(), _W()
    F, _ = W.toolkit()
    _, _, bp = W.borrow_modules()
    try:
        inline, meta = bp.build_problem(edited)
        graph = bp.BorrowGraph(inline, meta["eq_end"], check_literal=False,
                               tail_mutable=True, cut_equality=True)
        fitted = F.optimal_frames(inline, _COSTS, graph=graph,
                                 check_literal=False, interval=True)
    except (F.Infeasible, TimeoutError) as error:
        return None, dict(status="EXPLORATORY", unresolved="fresh frame fit: " + str(error))
    except ValueError as error:
        if "domain too large" not in str(error):
            raise
        return None, dict(status="EXPLORATORY", unresolved="fresh frame-domain resource cap: " + str(error))
    certificate = T._json({k:fitted[k] for k in ("certified", "cost", "profile", "parts", "interval")})
    if not fitted["certified"]:
        return None, dict(status="EXPLORATORY", unresolved="uncertified integer-surrogate refit",
                          refit=certificate)
    built = T._materialize(edited, graph, meta, fitted["assign"])
    npre = int(built.get("prelude_events", 0))
    if built["A"][:npre] != state["raw"]["A"][:npre]:
        return None, dict(status="EXPLORATORY", unresolved="chosen refit changes frozen prelude",
                          refit=certificate)
    _invariants(state, built)
    ctx = _caps().prepare(built, state["attribution"], _ENDPOINT)
    capped = ctx.optimize_one(7, cpu_seconds=120, include_word=True)
    cap_meta = {k:v for k, v in capped.items() if k != "word"}
    if capped.get("status") != "PASS" or not capped.get("exact_optimum_verified"):
        return None, dict(status="EXPLORATORY", unresolved="restricted cap not exactly certified",
                          refit=certificate, cap=cap_meta)
    result = capped["word"]
    canonical = _invariants(state, result)
    need(canonical.paid == _profile(capped["profile"]), "cap/profile exact agreement")
    return result, dict(status="PASS", refit=certificate, cap=cap_meta,
        cap_normals=[7], cap_scope="Binary F-to-F-intersection-ker7 assignments on this fitted graph only",
        warning="Normal7 may be vacuous on already ker7-contained source contacts; DAG recoding is the tested premise")


def install_reference(provider, local_profile):
    """Parent installs the two-seed-confirmed unchanged-word reference."""
    need(provider in _WORDS and provider not in _REFERENCES, "once per provider reference")
    profile = _profile(local_profile)
    need(_mass(profile) == _mass(_WORDS[provider]["canonical"].paid), "reference paid mass")
    _REFERENCES[provider] = profile


def reference_task(spec):
    provider, seed = spec["provider"], int(spec["seed"])
    state = _WORDS[provider]
    begin = time.process_time()
    result = dict(provider=provider, seed=seed, attribution="FRAME_ONLY", word=None,
        source_attribution=deepcopy(state["attribution"]), source_pin=deepcopy(state["source_pin"]),
        scope="Unchanged scalar word with the identical endpoint refit/cap procedure; control, not production credit")
    built, optimizer = _refit(state, state["raw"])
    result["optimizer"] = optimizer
    if built is None:
        result.update(status="EXPLORATORY", unresolved=optimizer.get("unresolved"),
                      cpu_seconds=time.process_time()-begin)
        return result
    canonical = _invariants(state, built)
    moment = _moment_delta(canonical.paid, state["canonical"].paid)
    result.update(local_profile=canonical.paid, width_inventory=dict(Counter(state["widths"])),
                  moment_delta=moment, built_semantic_sha256=digest(built))
    if Q(moment["upper"]) < 0:
        result.update(status="PASS", outcome="REFERENCE_GAIN",
            word=_trusted()._write_word(built, spec["output_dir"], "reference-"+provider))
    elif Q(moment["lower"]) >= 0 or moment["exact_profile_identity"]:
        result.update(status="PASS", outcome="NO_GAIN")
    else:
        result.update(status="EXPLORATORY", unresolved="reference exact-cost interval straddles zero")
    result["cpu_seconds"] = time.process_time()-begin
    return result


def price_task(spec):
    provider, seed, candidate = spec["provider"], int(spec["seed"]), spec["candidate"]
    state = _WORDS[provider]
    need(candidate["provider"] == provider, "candidate provider binding")
    need(provider in _REFERENCES, "confirmed same-procedure reference installed before pricing")
    begin = time.process_time()
    result = dict(provider=provider, seed=seed, candidate_id=candidate["candidate_id"],
        candidate=deepcopy(candidate), source_attribution=deepcopy(state["attribution"]),
        source_pin=deepcopy(state["source_pin"]), local_profile=None, width_inventory=None,
        moment_delta=None, reference_moment_delta=None, word=None, optimizer=None,
        scope="Registered surrogate refit and one exact binary cap on a changed DAG; not all-frame/global optimum or native/kappa admission")
    edited, guards = _construct(state, candidate)
    result["guards"] = guards
    if edited is None:
        result.update(status="REJECTED_GUARD", cpu_seconds=time.process_time()-begin)
        return result
    built, optimizer = _refit(state, edited)
    result["optimizer"] = optimizer
    if built is None:
        result.update(status="EXPLORATORY", unresolved=optimizer.get("unresolved"),
                      cpu_seconds=time.process_time()-begin)
        return result
    canonical = _invariants(state, built)
    moment = _moment_delta(canonical.paid, state["canonical"].paid)
    reference_moment = _moment_delta(canonical.paid, _REFERENCES[provider])
    result.update(local_profile=canonical.paid, width_inventory=dict(Counter(state["widths"])),
        ordered_widths=state["widths"], moment_delta=moment,
        reference_moment_delta=reference_moment, reference_profile=_REFERENCES[provider],
        built_semantic_sha256=digest(built), cleanup_sha256=digest(built["cleanup"]),
        compensation_sha256=digest(built["compensation"]),
        scalar_instruction_delta=guards["scalar_instruction_delta"],
        cleanup_instruction_delta=len(built["cleanup"])-len(state["raw"]["cleanup"]),
        full_forward_cleanup_instruction_delta=(guards["scalar_instruction_delta"]
            +len(built["cleanup"])-len(state["raw"]["cleanup"])),
        private_buffers=91, physical_families=66813,
        fresh_native="UNRUN_REQUIRED_FOR_ANY_CANDIDATE", global_fill_and_outer="UNRUN_REQUIRED")
    if Q(moment["upper"]) < 0 and Q(reference_moment["upper"]) < 0:
        result["status"] = "PASS_CANDIDATE"
        result["word"] = _trusted()._write_word(built, spec["output_dir"], candidate["candidate_id"])
    elif any(Q(m["lower"]) >= 0 or m["exact_profile_identity"] for m in (moment, reference_moment)):
        result["status"] = "NO_GAIN"
    else:
        result.update(status="EXPLORATORY", unresolved="one exact comparison straddles zero")
    result["cpu_seconds"] = time.process_time()-begin
    return result


def controls_task(seed):
    seed = int(seed.get("seed")) if isinstance(seed, dict) else int(seed)
    begin = time.process_time()
    checks = []
    def check(name, condition):
        need(condition, "R1 control failed: " + name)
        checks.append(dict(name=name, status="PASS"))
    for orientation, coefficient in itertools.product((0, 1), COEFFICIENTS):
        p, q = (3, 4) if orientation == 0 else (4, 3)
        fixture = [_add(10, p, Q(1, 2)), _add(q, 11, -2), _add(12, q, 1),
                   _add(p, 13, -1), ["scale", 14, 2, 1, []], _add(15, 14, 1)]
        warps = [(2, 1, 14)]
        changed, moved, _ = _rewrite_window(fixture, warps, p, q, coefficient)
        tag = f"{orientation}_{coefficient}"
        for dual in (False, True):
            expected = _oracle(fixture, warps, dual=dual)
            check("forward_or_dual_identity_"+tag+"_"+str(dual),
                  expected == _oracle(changed, moved, dual=dual))
            bad = deepcopy(changed)
            bad[-1] = _add(p, q, coefficient)
            check("wrong_decode_sign_"+tag+"_"+str(dual),
                  expected != _oracle(bad, moved, dual=dual))
            bad = deepcopy(changed)
            bad[2] = _add(10, q, 2*Q(bad[2][3], bad[2][4]))
            check("missing_read_correction_"+tag+"_"+str(dual),
                  expected != _oracle(bad, moved, dual=dual))
            bad = deepcopy(changed)
            bad[4] = _add(p, 11, 2*Q(bad[4][3], bad[4][4]))
            check("missing_write_correction_"+tag+"_"+str(dual),
                  expected != _oracle(bad, moved, dual=dual))
    for name, gates, warps in (
        ("pair_scale", [["scale", 3, 2, 1, []]], []),
        ("internal_pair_add", [_add(3, 4, 1)], []),
        ("pair_warp", [_add(10, 3, 1)], [(0, 1, 3)]),
    ):
        rejected = False
        try:
            _rewrite_window(gates, warps, 3, 4, 1)
        except ValueError:
            rejected = True
        check(name+"_guard", rejected)
    for provider in sorted(_WORDS):
        state = _WORDS[provider]
        candidate = _candidate(state, provider, PAIRS[0], INTERVALS[PAIRS[0]][0], 0, Q(1))
        candidate["parent_semantic_sha256"] = "0"*64
        rejected = False
        try:
            _construct(state, candidate)
        except ValueError:
            rejected = True
        check("stale_preimage_"+provider, rejected)
    collective = _caps().controls_task(_ENDPOINT, seed, cpu_seconds=60)
    need(collective["status"] == "PASS", "registered exact collective-cap controls")
    return dict(status="PASS", seed=seed, checks=checks,
        collective_cap_controls=collective,
        checked_orientations=["forward", "inverse_transpose"],
        coefficients=[str(x) for x in COEFFICIENTS], cap_normals=list(CAP_NORMALS),
        cpu_seconds=time.process_time()-begin)
