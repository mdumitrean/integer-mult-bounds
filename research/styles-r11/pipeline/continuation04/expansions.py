"""Fixed-exterior compensated adjacent transports; coordinator execution only.

Direct predecessor: CubeJerry/PR1533 (adjacent Steinberg expansions on the
PR589 bit word).  The current source is Jeremy Kothe/PR2966, with PR2942,
PR2957, PR2917 and every inherited notice retained in source attribution.
No fetched implementation is imported.  No experiment runs at import time.
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
TRIANGLES_PATH = RR / "pipeline/continuation03/triangles.py"
TRIANGLES_SHA256 = "14bd46dd6be68f9e2337a6359ebe2f79ae61423a7306932b1a2a2c7cd98207dc"
SECTIONS = ("A", "B", "restore")
# Keep all eight labels even when their actual assignments coincide.
VARIANTS = tuple((s, r, t) for s in ("L2", "U2")
                 for r in ("L1", "S") for t in ("S", "U3"))
_T = None
_WORDS = {}
_ENDPOINT = None
_CHILD_COSTS = None


def need(test, message):
    if not test:
        raise ValueError(message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode())


def _trusted():
    global _T
    if _T is None:
        need(sha(TRIANGLES_PATH.read_bytes()) == TRIANGLES_SHA256,
             "frozen triangle utility source drift")
        need(not sys.flags.optimize, "enabled assertions required")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_e1_frozen_utilities", TRIANGLES_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _T = module
    return _T


def _W():
    return _trusted()._module("wordio")


def _basis(frame):
    return _W().basis(frame)


def _leq(left, right):
    return _W().contained(tuple(left), tuple(right))


def _join(*frames):
    return _basis(x for frame in frames for x in frame)


def _span(frame):
    values = {0}
    for vector in frame:
        values |= {x ^ vector for x in tuple(values)}
    return values


def _meet(*frames):
    need(bool(frames), "intersection needs a frame")
    values = _span(frames[0])
    for frame in frames[1:]:
        values.intersection_update(_span(frame))
    return _basis(values)


def _profile(profile):
    return {int(r): int(n) for r, n in sorted(profile.items(), key=lambda p: int(p[0])) if n}


def _mass(profile):
    return sum(int(r)*int(n) for r, n in profile.items())


def _fixed_graph(raw, canonical):
    """Literal chains only: no variable domains, solver, or old optimal frames.

    The trusted adapter splits aliases at each warp.  Its node construction is
    reproduced without optimization to expose actual unchanged exterior
    contacts.  The complete edge bill is checked against canonical WordData.
    """
    W = _W()
    _, _, bp = W.borrow_modules()
    inline, meta = bp.build_problem(raw)
    starts, ends = inline["_start_frames"], inline["_final_frames"]
    nodes, chains, index = [], [[] for _ in starts], {}

    def node(regs, frame, section, position=None, raw_regs=None, raw_position=None):
        k = len(nodes)
        record = dict(registers=tuple(regs), frame=_basis(frame), section=section,
                      index=position, raw_registers=tuple(raw_regs or ()), raw_index=raw_position)
        nodes.append(record)
        for r in regs:
            chains[r].append(k)
        if raw_position is not None:
            index[section, raw_position] = k

    for r, frame in enumerate(starts):
        node((r,), frame, "start")
    for section in ("A", "B"):
        if section == "B":
            for r, frame in zip(inline["centers"], inline["center_frames"]):
                node((r,), frame, "cut")
            for t in range(canonical.v):
                node((canonical.v+t,), inline.get("target_levels", {}).get(str(t), []), "cut")
        for p, gate in enumerate(inline[section]):
            rp = meta["A_idx"][p] if section == "A" else p
            original = raw[section][rp]
            node(W.registers(gate), gate[-1] or (), section, p,
                 W.registers(original), rp)
    for p, gate in enumerate(inline["_tail"]):
        node(W.registers(gate), gate[-1] or (), "restore", p,
             W.registers(raw["restore"][p]), p)
    for r, frame in enumerate(ends):
        node((r,), frame, "end")
    previous, following = {}, {}
    bill = Counter()
    for r, chain in enumerate(chains):
        for before, after in zip(chain, chain[1:]):
            previous[after, r], following[before, r] = before, after
            left, right = nodes[before], nodes[after]
            need(_leq(left["frame"], right["frame"]), "literal source-chain inclusion")
            equal = ((left["section"] == "A" and right["section"] == "cut")
                     or (right["section"] == "end" and r in meta["eq_end"]))
            if equal:
                need(left["frame"] == right["frame"], "source cut/warp entrance equality")
            climb = len(right["frame"])-len(left["frame"])
            if climb:
                bill[climb] += 1
    bill.update(bp.centre_descents(raw))
    need(dict(sorted(bill.items())) == canonical.paid,
         "literal fixed-node bill plus centre descents equals canonical profile")
    return dict(nodes=nodes, chains=chains, previous=previous, following=following,
                index=index, eq_end=set(meta["eq_end"]), meta=meta,
                edge_profile=dict(sorted(bill.items())))


def prepare(records, endpoint, profile, inventory):
    """Coordinator parent-only preparation after registration, once per run."""
    global _ENDPOINT, _CHILD_COSTS
    need(not _WORDS, "E1 preparation is once-only")
    need(set(records) == {"base", "extra"}, "both source providers required")
    _ENDPOINT = Q(endpoint)
    need(0 < _ENDPOINT < 1, "strictly concave child-cost exponent")
    expected_profile, expected_inventory = _profile(profile), _profile(inventory)
    T, W = _trusted(), _W()
    ceiling = T._module("ceiling")
    _CHILD_COSTS = {r: ceiling.child_cost(r, 73, _ENDPOINT) for r in range(1, 10)}
    summary = {}
    for provider in sorted(records):
        rec = records[provider]
        raw, attribution = rec["raw"], deepcopy(rec["attribution"])
        canonical = W.WordData(raw, attribution)
        need(canonical.paid == expected_profile, "pinned paid local profile")
        widths = T._widths(canonical)
        need(dict(Counter(widths)) == expected_inventory, "pinned ordered-width inventory")
        need(len(canonical.helpers) == 408 and len(canonical.live) == 632,
             "source helper/input counts")
        need(canonical.v == 112 and canonical.n == 704 and canonical.h == 9,
             "source finite geometry")
        need(len(raw["helper_final"]) == int(rec.get("expected_buffers", 86)) == 86,
             "source private-buffer stock")
        need(int(rec.get("expected_physical_families", 66808)) == 66808,
             "source physical-stock declaration")
        need(not raw.get("early_cleanup"), "registered BORROW source has no early cleanup")
        need(all(g[0] != "warp" or p < int(raw.get("prelude_events", 0))
                 for p, g in enumerate(raw["A"])), "all A warps lie inside frozen prelude")
        fixed = _fixed_graph(raw, canonical)
        semantic = digest(raw)
        if rec.get("original_semantic_sha256"):
            need(semantic == rec["original_semantic_sha256"], "source adapter semantic binding")
        _WORDS[provider] = dict(raw=raw, attribution=attribution, canonical=canonical,
            semantic_sha256=semantic, source_pin=deepcopy(rec.get("source_pin", {})),
            widths=widths, boundaries=T._boundary_signature(raw), fixed=fixed)
        summary[provider] = dict(semantic_sha256=semantic, local_profile=canonical.paid,
            width_inventory=dict(Counter(widths)), ordered_helpers=list(canonical.helpers),
            private_buffers=86, physical_families=66808,
            fixed_node_count=len(fixed["nodes"]), virtual_register_count=len(fixed["chains"]),
            literal_edge_profile=fixed["edge_profile"],
            source_attribution=attribution, source_pin=deepcopy(rec.get("source_pin", {})))
    return dict(status="PASS", providers=summary, endpoint=str(_ENDPOINT),
        variants=[list(x) for x in VARIANTS],
        method="eight explicit fixed-exterior frame corners; no solver",
        trusted_utility=dict(path=str(TRIANGLES_PATH.relative_to(REPO)), sha256=TRIANGLES_SHA256))


def _chain(gates, target_v):
    T = _trusted()
    if len(gates) != 2 or not all(T._add(g) for g in gates):
        return None
    first, second = gates
    if first[2] == second[1]:
        i, j, k = first[1], first[2], second[2]
        a, b = Q(first[3], first[4]), Q(second[3], second[4])
        orientation, sign = "AB_to_BAC_minus", -1
    elif first[1] == second[2]:
        i, j, k = second[1], first[1], first[2]
        a, b = Q(second[3], second[4]), Q(first[3], first[4])
        orientation, sign = "BA_to_ABC_plus", 1
    else:
        return None
    if len({i, j, k}) != 3 or any(target_v <= r < 2*target_v for r in (i, j, k)):
        return None
    return dict(i=i, j=j, k=k, a=str(a), b=str(b), chord=str(sign*a*b),
                orientation=orientation)


def _candidate(state, provider, section, position, variant):
    T, raw = _trusted(), state["raw"]
    if section not in SECTIONS or tuple(variant) not in VARIANTS:
        return None
    if not (type(position) is int and 0 <= position < len(raw[section])-1):
        return None
    if not T._same_segment(raw, section, (position, position+1)):
        return None
    gates = raw[section][position:position+2]
    chain = _chain(gates, int(raw["report"]["v"]))
    if chain is None:
        return None
    core = dict(provider=provider, section=section, positions=[position, position+1],
                orientation=chain["orientation"], variant=list(variant))
    return dict(**core, candidate_id=digest(core), chain=chain,
                parent_semantic_sha256=state["semantic_sha256"],
                original_gates=deepcopy(gates), interval_sha256=digest(gates))


def _sort_key(candidate):
    return (SECTIONS.index(candidate["section"]), candidate["positions"][0],
            candidate["orientation"], VARIANTS.index(tuple(candidate["variant"])))


def census_task(spec):
    provider, seed = spec["provider"], int(spec["seed"])
    state, T = _WORDS[provider], _trusted()
    work = [(section, first, last) for section in SECTIONS
            for first, last in T._segments(state["raw"], section)]
    random.Random(seed).shuffle(work)
    begin = time.process_time()
    counts = Counter(segments=len(work), adjacent_pairs=0, eligible_pairs=0,
                     ineligible_pairs=0, candidate_variants=0)
    candidates = []
    for section, first, last in work:
        for p in range(first, max(first, last-1)):
            counts["adjacent_pairs"] += 1
            candidate = _candidate(state, provider, section, p, VARIANTS[0])
            if candidate is None:
                counts["ineligible_pairs"] += 1
                continue
            counts["eligible_pairs"] += 1
            counts[candidate["orientation"]] += 1
            for variant in VARIANTS:
                candidates.append(_candidate(state, provider, section, p, variant))
                counts["candidate_variants"] += 1
    candidates.sort(key=_sort_key)
    need(len(candidates) == 8*counts["eligible_pairs"], "all eight labels per eligible pair")
    need(len({c["candidate_id"] for c in candidates}) == len(candidates), "unique literal candidate addresses")
    return dict(status="PASS", provider=provider, seed=seed, complete=True,
        counts=dict(counts), candidates=candidates, candidate_set_sha256=digest(candidates),
        parent_semantic_sha256=state["semantic_sha256"],
        source_attribution=deepcopy(state["attribution"]), source_pin=deepcopy(state["source_pin"]),
        schedule=dict(seed=seed, section_segments=work),
        pricing_cap=None, unpriced_if_cap_applied=0,
        cpu_seconds=time.process_time()-begin)


enumerate_task = census_task


def _boundaries(state, candidate):
    fixed, section = state["fixed"], candidate["section"]
    ids = [fixed["index"][section, p] for p in candidate["positions"]]
    result = {}
    for name in ("i", "j", "k"):
        raw_register = candidate["chain"][name]
        contacts = []
        for node_id in ids:
            node = fixed["nodes"][node_id]
            mapping = dict(zip(node["raw_registers"], node["registers"]))
            if raw_register in mapping:
                contacts.append((node_id, mapping[raw_register]))
        need(bool(contacts), "every triangle register occurs in original pair")
        aliases = {r for _, r in contacts}
        need(len(aliases) == 1, "shared register cannot cross a hidden warp alias")
        virtual = contacts[0][1]
        before = fixed["previous"][contacts[0][0], virtual]
        after = fixed["following"][contacts[-1][0], virtual]
        need(before not in ids and after not in ids, "boundaries are exterior contacts")
        prev_node, next_node = fixed["nodes"][before], fixed["nodes"][after]
        equality = ((section == "A" and next_node["section"] == "cut")
                    or (next_node["section"] == "end" and virtual in fixed["eq_end"]))
        result[name] = dict(register=raw_register, virtual_register=virtual,
            entry=list(prev_node["frame"]), exit=list(next_node["frame"]),
            equality_exit=equality, previous_node=before, next_node=after,
            previous_origin=[prev_node["section"], prev_node["raw_index"]],
            next_origin=[next_node["section"], next_node["raw_index"]])
    return result


def _frames(boundaries, orientation, variant):
    E = {name: _basis(rec["entry"]) for name, rec in boundaries.items()}
    O = {name: _basis(rec["exit"]) for name, rec in boundaries.items()}
    first_outer = "k" if orientation == "AB_to_BAC_minus" else "i"
    L1 = _join(E["j"], E[first_outer])
    L2 = _join(*E.values())
    U2, U3 = _meet(*O.values()), _meet(O["i"], O["k"])
    frame = dict(L1=L1, L2=L2, U2=U2, U3=U3)
    frame["S"] = frame[variant[0]]
    frame["R"] = frame[variant[1]]
    frame["T"] = frame[variant[2]]
    failures = []
    for left, right in (("L1", "R"), ("R", "S"), ("L2", "S"),
                        ("S", "U2"), ("S", "T"), ("T", "U3")):
        if not _leq(frame[left], frame[right]):
            failures.append(dict(predicate="frame_inclusion", lower=left, upper=right,
                                 lower_frame=list(frame[left]), upper_frame=list(frame[right])))
    final = dict(i=frame["T"], j=frame["S"], k=frame["T"])
    for name in ("i", "j", "k"):
        if not _leq(final[name], O[name]):
            failures.append(dict(predicate="exit_inclusion", register=name))
        if boundaries[name]["equality_exit"] and final[name] != O[name]:
            failures.append(dict(predicate="exit_equality", register=name,
                                 actual=list(final[name]), required=list(O[name])))
    return frame, failures


def _local_bill(gates, boundaries):
    by_register = {rec["register"]: rec for rec in boundaries.values()}
    current = {r: _basis(rec["entry"]) for r, rec in by_register.items()}
    profile, jumps = Counter(), []
    for position, gate in enumerate(gates):
        frame = _basis(gate[-1])
        for r in gate[1:3]:
            need(r in current, "local bill contains only the three named registers")
            need(_leq(current[r], frame), "local explicit chain inclusion")
            rank = len(frame)-len(current[r])
            if rank:
                profile[rank] += 1
            jumps.append(dict(register=r, origin="gate", index=position, rank=rank,
                              before=list(current[r]), after=list(frame)))
            current[r] = frame
    for r, rec in by_register.items():
        frame = _basis(rec["exit"])
        need(_leq(current[r], frame), "exterior successor inclusion")
        if rec["equality_exit"]:
            need(current[r] == frame, "exterior cut/warp equality")
        rank = len(frame)-len(current[r])
        if rank:
            profile[rank] += 1
        jumps.append(dict(register=r, origin="first_unchanged_successor", rank=rank,
                          before=list(current[r]), after=list(frame),
                          equality_exit=bool(rec["equality_exit"])))
    return dict(profile=dict(sorted(profile.items())), jumps=jumps,
                rank_mass=_mass(profile))


def _replacement(candidate, frames):
    old = candidate["original_gates"]
    first, second = deepcopy(old[1]), deepcopy(old[0])
    first[-1], second[-1] = list(frames["R"]), list(frames["S"])
    chain = candidate["chain"]
    coefficient = Q(chain["chord"])
    chord = ["add", chain["i"], chain["k"], coefficient.numerator,
             coefficient.denominator, list(frames["T"])]
    return [first, second, chord]


def _construct(state, candidate):
    T, raw = _trusted(), state["raw"]
    need(candidate["parent_semantic_sha256"] == state["semantic_sha256"], "stale parent word")
    expected = _candidate(state, candidate["provider"], candidate["section"],
                          candidate["positions"][0], candidate["variant"])
    need(expected is not None and expected == candidate, "stale preimage or invalid registered address")
    boundaries = _boundaries(state, candidate)
    frames, failures = _frames(boundaries, candidate["orientation"], candidate["variant"])
    witness = dict(boundaries=boundaries, frames={k: list(v) for k, v in frames.items()},
                   predicates_passed=not failures, failures=failures,
                   literal_exterior_frames_frozen=True,
                   equality_exits=[k for k, v in boundaries.items() if v["equality_exit"]])
    if failures:
        return None, witness
    new_window = _replacement(candidate, frames)
    old_window = candidate["original_gates"]
    need(T._sequential_matrix(old_window) == T._sequential_matrix(new_window),
         "exact complete-window forward identity")
    need(T._sequential_matrix(old_window, dual=True) == T._sequential_matrix(new_window, dual=True),
         "exact complete-window inverse-transpose identity")
    before_bill, after_bill = _local_bill(old_window, boundaries), _local_bill(new_window, boundaries)
    need(before_bill["rank_mass"] == after_bill["rank_mass"], "boundary paid rank-mass identity")
    section, position = candidate["section"], candidate["positions"][0]
    edited = deepcopy(raw)
    edited[section] = deepcopy(raw[section][:position] + new_window + raw[section][position+2:])
    need(edited[section][:position] == raw[section][:position]
         and edited[section][position+3:] == raw[section][position+2:],
         "exact exterior prefix/suffix identity")
    if section == "B":
        need(all(rec[0] != position+1 for rec in raw["warps"]), "no hidden warp between adjacent gates")
        edited["warps"] = [[rec[0] + int(rec[0] > position+1)] + deepcopy(rec[1:])
                           for rec in raw["warps"]]
    for other in SECTIONS:
        if other != section:
            need(edited[other] == raw[other], "every other scalar section is frozen")
    need(T._boundary_signature(edited) == state["boundaries"], "fixed cut/endpoint/compensation ABI")
    witness.update(complete_window_matrix_identity=True,
        complete_window_inverse_transpose_identity=True,
        exact_exterior_prefix_suffix_identity=True, scalar_instruction_delta=1,
        compensation_reuse="Exact scalar interval identity on non-target registers; all cut/warp interfaces frozen",
        original_window_bill=before_bill, expanded_window_bill=after_bill,
        private_buffers=86, physical_families=66808,
        semantic_warp_order_preserved=True)
    return edited, witness


def _moment_delta(new, old):
    delta = {r: new.get(r, 0)-old.get(r, 0) for r in sorted(set(new)|set(old))
             if new.get(r, 0) != old.get(r, 0)}
    lower = upper = Q(0)
    intervals = {}
    for rank, count in delta.items():
        lo, hi = _CHILD_COSTS[rank]
        intervals[rank] = [str(lo), str(hi)]
        lower += count*(lo if count >= 0 else hi)
        upper += count*(hi if count >= 0 else lo)
    return dict(lower=str(lower), upper=str(upper), endpoint=str(_ENDPOINT),
                exact_profile_identity=not delta, profile_delta=delta,
                child_cost_intervals=intervals)


def price_task(spec):
    provider, seed, candidate = spec["provider"], int(spec["seed"]), spec["candidate"]
    state, T, W = _WORDS[provider], _trusted(), _W()
    need(candidate["provider"] == provider, "candidate provider binding")
    begin = time.process_time()
    result = dict(provider=provider, seed=seed, candidate_id=candidate["candidate_id"],
        candidate=deepcopy(candidate), source_pin=deepcopy(state["source_pin"]),
        source_attribution=deepcopy(state["attribution"]), local_profile=None,
        width_inventory=None, moment_delta=None, word=None, optimizer=None,
        scope="One explicit corner of the fixed-exterior swapped-pair/end-chord frame domain; no whole-word optimum or native/kappa admission")
    edited, witness = _construct(state, candidate)
    result["guards"] = witness
    if edited is None:
        result.update(status="REJECTED_GUARD", cpu_seconds=time.process_time()-begin)
        return result
    canonical = W.WordData(edited, state["attribution"], assert_profile=False)
    old = state["canonical"]
    need(canonical.helpers == old.helpers and canonical.start == old.start and canonical.end == old.end,
         "ordered helper/start/end invariants")
    need(T._widths(canonical) == state["widths"], "ordered physical widths unchanged")
    need(_mass(canonical.paid) == _mass(old.paid), "complete canonical paid mass unchanged")
    before = witness["original_window_bill"]["profile"]
    after = witness["expanded_window_bill"]["profile"]
    expected = Counter(old.paid)
    expected.subtract(before)
    expected.update(after)
    need(all(n >= 0 for n in expected.values()), "local delta cannot create negative complete counts")
    need(_profile(expected) == canonical.paid, "complete canonical delta equals boundary-chain delta")
    edited["report"]["local_profile"] = {str(r): n for r, n in sorted(canonical.paid.items())}
    edited["cleanup"] = W.derived_borrow_cleanup(canonical)
    complete = W.WordData(edited, state["attribution"])
    need(complete.paid == canonical.paid, "cleanup regeneration preserves exact paid profile")
    need(T._boundary_signature(edited) == state["boundaries"], "final fixed ABI")
    npre = int(edited.get("prelude_events", 0))
    need(edited["A"][:npre] == state["raw"]["A"][:npre], "entry prelude literal identity")
    moment = _moment_delta(complete.paid, old.paid)
    result.update(local_profile=complete.paid, width_inventory=dict(Counter(T._widths(complete))),
        ordered_widths=T._widths(complete), moment_delta=moment,
        built_semantic_sha256=digest(edited), cleanup_sha256=digest(edited["cleanup"]),
        compensation_sha256=digest(edited["compensation"]),
        canonical_profile_and_boundary_delta_agree=True,
        scalar_instruction_delta=1, private_buffers=86, physical_families=66808)
    if Q(moment["upper"]) < 0:
        result["status"] = "PASS_CANDIDATE"
        result["word"] = T._write_word(edited, spec["output_dir"], candidate["candidate_id"])
    elif Q(moment["lower"]) >= 0 or moment["exact_profile_identity"]:
        result["status"] = "NO_GAIN"
    else:
        result.update(status="EXPLORATORY", unresolved="outward exact-cost interval straddles zero")
    result["cpu_seconds"] = time.process_time()-begin
    return result


def controls_task(spec):
    seed = int(spec["seed"]) if isinstance(spec, dict) else int(spec)
    T = _trusted()
    begin = time.process_time()
    checks = []

    def check(name, condition):
        need(condition, "E1 control failed: " + name)
        checks.append(dict(name=name, status="PASS"))

    def gate(target, source, coefficient, frame=()):
        coefficient = Q(coefficient)
        return ["add", target, source, coefficient.numerator, coefficient.denominator, list(frame)]

    for a, b in itertools.product((-2, -1, Q(-1, 2), Q(1, 2), 1, 2), repeat=2):
        A, B = gate(3, 4, a), gate(4, 5, b)
        for orientation, old, sign in (("AB_to_BAC_minus", [A, B], -1),
                                       ("BA_to_ABC_plus", [B, A], 1)):
            new = [deepcopy(old[1]), deepcopy(old[0]), gate(3, 5, sign*a*b)]
            name = f"{orientation}_{a}_{b}"
            check("recognizer_"+name, _chain(old, 112)["orientation"] == orientation)
            for dual in (False, True):
                check(f"identity_{dual}_"+name, T._sequential_matrix(old, dual) == T._sequential_matrix(new, dual))
                wrong = deepcopy(new); wrong[-1][3] *= -1
                check(f"wrong_sign_{dual}_"+name, T._sequential_matrix(old, dual) != T._sequential_matrix(wrong, dual))
                wrong = deepcopy(new); wrong[-1][3] *= 2
                check(f"wrong_magnitude_{dual}_"+name, T._sequential_matrix(old, dual) != T._sequential_matrix(wrong, dual))

    check("three_distinct_registers", _chain([gate(3, 4, 1), gate(4, 3, 1)], 112) is None)
    check("target_register_excluded", _chain([gate(3, 112, 1), gate(112, 5, 1)], 112) is None)
    check("nonchain_pair_excluded", _chain([gate(3, 4, 1), gate(5, 6, 1)], 112) is None)
    check("zero_coefficient_excluded", _chain([gate(3, 4, 0), gate(4, 5, 1)], 112) is None)
    check("nondyadic_coefficient_excluded", _chain([gate(3, 4, Q(1, 3)), gate(4, 5, 1)], 112) is None)
    check("eight_rule_labels", len(VARIANTS) == len(set(VARIANTS)) == 8)

    A, B = gate(3, 4, 1), gate(4, 5, 1)
    fake = dict(A=[A, B], B=[], restore=[], warps=[], prelude_events=0, report={"v": 112})
    state = dict(raw=fake, semantic_sha256=digest(fake))
    good = _candidate(state, "base", "A", 0, VARIANTS[0])
    bad = deepcopy(good); bad["original_gates"][0][3] = 2
    try:
        _construct(state, bad)
    except ValueError:
        rejected = True
    else:
        rejected = False
    check("stale_preimage", rejected)
    bad = deepcopy(good); bad["parent_semantic_sha256"] = "0"*64
    try:
        _construct(state, bad)
    except ValueError:
        rejected = True
    else:
        rejected = False
    check("stale_source", rejected)
    prelude = deepcopy(fake); prelude["prelude_events"] = 1
    check("prelude_boundary", _candidate(dict(raw=prelude, semantic_sha256=digest(prelude)),
                                         "base", "A", 0, VARIANTS[0]) is None)
    warp = dict(A=[], B=[A, B], restore=[], warps=[[1, 9, [], [], []]],
                prelude_events=0, report={"v": 112})
    check("hidden_warp_boundary", _candidate(dict(raw=warp, semantic_sha256=digest(warp)),
                                             "base", "B", 0, VARIANTS[0]) is None)

    fixture_reports = []
    for orientation in ("AB_to_BAC_minus", "BA_to_ABC_plus"):
        entries = dict(i=[1], j=[], k=[]) if orientation == "AB_to_BAC_minus" else dict(i=[], j=[], k=[1])
        boundaries = {name: dict(register=r, entry=entries[name], exit=([1] if name == "j" else [2, 1]),
                                 equality_exit=False)
                      for name, r in zip(("i", "j", "k"), (3, 4, 5))}
        old = [gate(3, 4, 1, [1]), gate(4, 5, 1, [1])]
        if orientation == "BA_to_ABC_plus":
            old.reverse()
        candidate = dict(original_gates=old, chain=_chain(old, 112))
        before = _local_bill(old, boundaries)
        check("fixture_original_"+orientation, before["profile"] == {1: 4})
        observations = []
        for variant in VARIANTS:
            frames, failures = _frames(boundaries, orientation, variant)
            check("fixture_corner_feasible_"+orientation+str(variant), not failures)
            after = _local_bill(_replacement(candidate, frames), boundaries)
            check("fixture_mass_"+orientation+str(variant), after["rank_mass"] == before["rank_mass"] == 4)
            observations.append(dict(variant=list(variant), profile=after["profile"],
                                     moment=_moment_delta(after["profile"], before["profile"])))
        favorable = [x for x in observations if Q(x["moment"]["upper"]) < 0]
        check("strict_nested_positive_"+orientation,
              bool(favorable) and any(x["profile"] == {1: 2, 2: 1} for x in favorable))
        fixture_reports.append(dict(orientation=orientation, original_profile=before["profile"],
                                    corners=observations))
        # Inclusion alone permits j to end at S=0, but the exact exit below
        # requires equality with a line. This test isolates that equality gate.
        equality = {name: dict(register=r, entry=[], exit=[1], equality_exit=(name == "j"))
                    for name, r in zip(("i", "j", "k"), (3, 4, 5))}
        _, failure = _frames(equality, orientation, ("L2", "L1", "S"))
        check("equality_not_inclusion_"+orientation,
              any(x["predicate"] == "exit_equality" for x in failure)
              and not any(x["predicate"] in ("frame_inclusion", "exit_inclusion") for x in failure))
        impossible = deepcopy(boundaries); impossible["j"]["exit"] = []
        _, failure = _frames(impossible, orientation, ("L2", "L1", "U3"))
        check("insufficient_exit_"+orientation, bool(failure))
        neutral = {name: dict(register=r, entry=[1], exit=[1], equality_exit=False)
                   for name, r in zip(("i", "j", "k"), (3, 4, 5))}
        frames, failures = _frames(neutral, orientation, ("L2", "L1", "U3"))
        check("neutral_fixed_frame_"+orientation,
              not failures and _local_bill(_replacement(candidate, frames), neutral)["profile"] == {})
        check("successor_climb_must_be_charged_"+orientation,
              any(x["origin"] == "first_unchanged_successor" and x["rank"] > 0 for x in before["jumps"]))
        removed_rank = next(x["rank"] for x in before["jumps"]
                            if x["origin"] == "first_unchanged_successor" and x["rank"] > 0)
        omitted = Counter(before["profile"])
        omitted[removed_rank] -= 1
        check("omitted_successor_climb_breaks_complete_mass_"+orientation,
              _mass(omitted) != before["rank_mass"])
    return dict(status="PASS", seed=seed, checks=checks, fixtures=fixture_reports,
        direct_predecessor="CubeJerry/PR1533 adjacent expansions and improving boundary fixture; current complex source is the changed premise",
        unchanged_local_audits="Separate mandatory source2966.baseline_task for both providers and seeds",
        source_attribution={k: deepcopy(v["attribution"]) for k, v in _WORDS.items()},
        cpu_seconds=time.process_time()-begin)
