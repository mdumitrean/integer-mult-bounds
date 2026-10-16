"""Bounded rank-seven paired extraction from the pinned PR2917 words.

No preparation, control or search executes on import.  The coordinator freezes
the protocol and runs every task through pipeline/pool.py.  The source-pinned
G1 implementation supplies exact formal kernels, dyadic synthesis, guarded
refits and the eight paired identities; its globals and source are not changed.

This family intersects two rank-eight frames.  Its 763 dual planes contain at
least one of 7, 42, 45, and excludes the published helper408 lead.  Source and
mathematical attribution follow Jeremy Diviney, Mason Hale, Jeremy Kothe and
the complete per-word pins; these are continuing paired productions.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
import time

GENERIC_SHA = "685cd2a884f58eab9855296bc298cf62bc299c36047afe08c4935e522f1dd219"
ANCHORS = (7, 42, 45)
PLANE_COUNT = 763
PAIR_CAP = 8
PIVOT_CAP = 16
FRAME_BLOCK = 16
MODES = ("literal", "downward_cap")
PROTOCOL = "G2-ANCHORED-RANK7"
_G = None
_STATES = {}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def generic():
    global _G
    if _G is None:
        path = Path(__file__).resolve().parents[1] / "continuation/rewrite_search.py"
        need(hashlib.sha256(path.read_bytes()).hexdigest() == GENERIC_SHA,
             "frozen generic paired source drift")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_cont02_rank7_generic", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        need(module.PAIR_CAP == PAIR_CAP and module.PIVOT_CAP == PIVOT_CAP,
             "source-pinned bounded grammar constants")
        _G = module
    return _G


def planes():
    """All distinct anchored dual two-planes, in canonical lexical order."""
    result = sorted({tuple(sorted((a, b, a ^ b)))
                     for a in ANCHORS for b in range(1, 512) if b != a})
    need(len(result) == PLANE_COUNT, "763 distinct anchored dual two-planes")
    return tuple(result)


def frame_for(plane):
    G = generic()
    p = tuple(plane)
    need(len(p) == 3 and all(type(x) is int and 0 < x < 512 for x in p),
         "rank-seven plane must contain three nonzero nine-bit normals")
    need(tuple(sorted(set(p))) == p and p[0] ^ p[1] == p[2],
         "canonical dual two-plane triple")
    need(bool(set(p) & set(ANCHORS)), "dual plane lacks a registered anchor")
    frame = G._perp((p[0], p[1]))
    need(len(frame) == 7, "rank-seven output frame required")
    return frame


def _eligible_pivots(state, R):
    canonical = state["canonical"]
    result = [h for h in set(R) & set(state["H"]) - {408}
              if len(canonical.start[h]) == 0 and len(canonical.end[h]) == 9]
    result.sort(key=lambda h: (len(state["geometry"]["literal_terminal"][h]), h))
    return result


def prepare(records):
    """Parent-only formal matrices and geometry; no kernels or candidates."""
    need(not _STATES, "rank-seven prepare is once-only")
    need(set(records) == {"gauge44", "extra"}, "both pinned PR2917 providers required")
    started = time.process_time()
    G = generic()
    all_planes = planes()
    summary = {}
    for provider in sorted(records):
        record = records[provider]
        need(len(record["raw"]["helper_final"]) == 82,
             "PR2917 82-endpoint baseline required")
        state = G._prepare_one(record["raw"], record["attribution"])
        groups = []
        for mode in MODES:
            terminal = state["geometry"]["literal_terminal" if mode == "literal"
                                         else "minimum_terminal"]
            grouped = defaultdict(list)
            for plane in all_planes:
                frame = frame_for(plane)
                R = tuple(r for r in state["live"] if r not in state["restored"]
                          and G._inside(terminal[r], frame))
                grouped[R].append(plane)
            for R, pp in sorted(grouped.items()):
                groups.append(dict(mode=mode, output_registers=list(R),
                                   planes=[list(p) for p in pp]))
        state["groups"] = groups
        _STATES[provider] = state
        summary[provider] = dict(word_semantic_sha256=state["raw_sha256"],
            independent_non_target_inputs=len(state["live"]),
            eligible_input_helpers=len(state["H"]), restored_endpoints=82,
            groups=len(groups), frames_per_mode=PLANE_COUNT,
            frame_blocks=sum((len(g["planes"])+FRAME_BLOCK-1)//FRAME_BLOCK for g in groups),
            M_terms=sum(map(len, state["M"].values())),
            inverse_M_terms=sum(map(len, state["N"].values())),
            source_attribution=deepcopy(state["attribution"]))
    return dict(status="PREPARED", protocol=PROTOCOL, providers=summary,
        anchors=list(ANCHORS), distinct_dual_planes=PLANE_COUNT,
        frames_per_block=FRAME_BLOCK, pairs_per_frame=PAIR_CAP,
        pivots_per_pair=PIVOT_CAP, generic_source_sha256=GENERIC_SHA,
        excluded_helpers=[408], cpu_seconds=time.process_time()-started,
        scope="Declared endpoint rank9 to rank7; exact last-touched rank is separately recorded")


def get_state(provider):
    need(provider in _STATES, "parent preparation required")
    return _STATES[provider]


def get_states():
    need(_STATES, "parent preparation required")
    return _STATES


def task_specs(seed):
    need(_STATES, "parent preparation required")
    result = []
    for provider in sorted(_STATES):
        for i, group in enumerate(_STATES[provider]["groups"]):
            for block, start in enumerate(range(0, len(group["planes"]), FRAME_BLOCK)):
                result.append(dict(provider=provider, group=i, block=block, seed=int(seed),
                                   frame_start=start, frame_stop=min(start+FRAME_BLOCK,
                                                                   len(group["planes"]))))
    random.Random(seed).shuffle(result)
    return result


def _block(spec):
    state = get_state(spec["provider"])
    group = state["groups"][int(spec["group"])]
    start = int(spec["block"])*FRAME_BLOCK
    stop = min(start+FRAME_BLOCK, len(group["planes"]))
    need(0 <= start < stop and spec.get("frame_start", start) == start
         and spec.get("frame_stop", stop) == stop, "registered frame block binding")
    return state, group, start, stop


def _validate_production(state, transform):
    G = generic()
    h = transform["helper"]
    need(transform.get("parent_semantic_sha256") == state["raw_sha256"],
         "transform bound to a different parent word")
    need(h in state["H"] and h != 408, "fresh unprotected helper; helper408 excluded")
    need(len(state["canonical"].start[h]) == 0 and len(state["canonical"].end[h]) == 9,
         "pivot must have declared entrance rank0 and endpoint rank9")
    frame = frame_for(transform["plane"])
    need(transform.get("frame", list(frame)) == list(frame),
         "declared rank-seven output frame disagrees with dual plane")
    before, after = transform["before"], transform["after"]
    need(all(g[0] in ("add", "scale") and g[-1] == []
             and set(G._regs(g)) <= set(state["H"]) for g in before),
         "zero-frame input production on eligible helpers only")
    need(bool(after) and all(g[0] in ("add", "scale")
             and G._basis(tuple(g[-1])) == frame
             and set(G._regs(g)) <= set(state["live"])-state["restored"] for g in after),
         "common rank-seven output frame preserving old restored coordinates")
    for gate in before+after:
        q = Q(gate[3], gate[4]) if gate[0] == "add" else Q(gate[2], gate[3])
        need(G._dyadic(q) and (gate[0] != "scale" or G._unit(q)), "dyadic gate hygiene")
    return frame


def _check_paid_mass(old, new):
    old_mass = sum(int(r)*n for r, n in old.items())
    new_mass = sum(int(r)*n for r, n in new.items())
    need(new_mass == old_mass-2, "rank-seven extraction must save exactly two local rank units")
    return old_mass, new_mass


def _apply_transform(state, transform):
    G = generic()
    frame = _validate_production(state, transform)
    raw, h = state["raw"], transform["helper"]
    before, after = transform["before"], transform["after"]
    proof = G.certificate(state, transform)
    result, seen = deepcopy(raw), set()
    for edit in transform.get("frame_changes", []):
        section, index = edit["section"], edit["parent_index"]
        need(section in ("A", "B", "restore") and (section, index) not in seen,
             "unique frame edit")
        need(section != "A" or index >= raw.get("prelude_events", 0), "frozen entry prelude")
        seen.add((section, index))
        gate = result[section][index]
        need(gate[:-1] == edit["gate"] and gate[-1] == edit["old_frame"],
             "literal frame edit preimage")
        new = G._basis(tuple(edit["new_frame"]))
        need(list(new) == edit["new_frame"] and G._inside(new, G._basis(tuple(gate[-1]))),
             "downward canonical frame edit")
        gate[-1] = list(new)
    npre = raw.get("prelude_events", 0)
    result["A"] = result["A"][:npre]+deepcopy(before)+result["A"][npre:]
    result["restore"] += deepcopy(after)
    result["helper_final"][str(h)] = list(frame)
    C = deepcopy(state["C"])
    for gate in reversed(before):
        if gate[0] == "scale":
            C[gate[1]] = G._scale(C.get(gate[1], {}), Q(gate[2], gate[3]))
        else:
            t, s = gate[1:3]
            C[s] = G._add(C.get(s, {}), C.get(t, {}), Q(gate[3], gate[4]))
    need(not C.get(h), "new cold helper has nonzero compensation")
    result["compensation"] = [["add", t, r, q.numerator, q.denominator, []]
                              for r, col in sorted(C.items()) for t, q in sorted(col.items()) if q]
    W = G._wordio()
    canonical = W.WordData(result, state["attribution"], assert_profile=False)
    result["report"]["local_profile"] = {str(r): n for r, n in canonical.paid.items()}
    result["report"]["width_inventory"] = {str(r): n for r, n in sorted(Counter(
        len(canonical.end[r])-len(canonical.start[r]) for r in canonical.helpers).items())}
    result["cleanup"] = W.derived_borrow_cleanup(canonical)
    canonical = W.WordData(result, state["attribution"])
    changed = {key for key in set(raw)|set(result) if raw.get(key) != result.get(key)}
    need(changed <= G.ALLOWED_CHANGED_FIELDS, "undeclared word field changed")
    need(all(result["helper_final"].get(key) == old for key, old in raw["helper_final"].items()),
         "all82 old endpoints preserved")
    need(len(result["helper_final"]) == 83, "one charged additional buffer above82")
    old_mass, new_mass = _check_paid_mass(raw["report"]["local_profile"], canonical.paid)
    need(canonical.helpers == state["canonical"].helpers, "physical helper roles preserved")
    need(canonical.centre_paid == state["canonical"].centre_paid, "fixed centre descent invoice")
    old_widths = Counter(len(state["canonical"].end[r])-len(state["canonical"].start[r])
                         for r in state["canonical"].helpers)
    old_widths[9] -= 1
    old_widths[7] += 1
    actual_widths = Counter(len(canonical.end[r])-len(canonical.start[r]) for r in canonical.helpers)
    need(+old_widths == actual_widths, "exact single helper width9 to7 inventory change")
    proof.update(output_rank=7, dual_plane=transform["plane"], old_local_paid_mass=old_mass,
                 new_local_paid_mass=new_mass, private_buffers=83,
                 invoice_scope="Full canonical local profile and cleanup; complete native/owner/outer pending")
    return result, proof


def construct(provider, transform):
    return _apply_transform(get_state(provider), transform)


def _transform(state, group, pair, pair_index, helper, plane):
    G = generic()
    frame = frame_for(plane)
    before, after = G._synthesize(pair, helper, frame)
    support = {r for gate in after for r in G._regs(gate)}
    edits = [] if group["mode"] == "literal" else G._refit(state, frame, support)
    return dict(helper=helper, plane=list(plane), frame=list(frame), before=before, after=after,
                frame_changes=edits, mode=group["mode"], canonical_pair=pair_index,
                basis_indices=pair["basis_indices"], parent_semantic_sha256=state["raw_sha256"])


def reconstruct_nominee(address):
    state = get_state(address["provider"])
    group = state["groups"][int(address["group"])]
    plane, helper = list(address["plane"]), int(address["helper"])
    need(plane in group["planes"] and address["mode"] == group["mode"], "nominee frame group binding")
    if "block" in address:
        start = int(address["block"])*FRAME_BLOCK
        need(plane in group["planes"][start:start+FRAME_BLOCK], "nominee frame block binding")
    pairs, _ = generic()._pairs(state, tuple(group["output_registers"]))
    i = int(address["canonical_pair"])
    need(0 <= i < len(pairs), "canonical retained pair index")
    need(pairs[i]["basis_indices"] == address["basis_indices"], "canonical basis pair address")
    need(helper in _eligible_pivots(state, group["output_registers"])[:PIVOT_CAP],
         "canonical retained helper pivot")
    transform = _transform(state, group, pairs[i], i, helper, plane)
    raw, proof = _apply_transform(state, transform)
    need(address.get("semantic_sha256", generic().semantic_sha(raw)) == generic().semantic_sha(raw),
         "recorded nominee word hash")
    return raw, transform, proof


def screen_task(spec):
    """At most16 frames; an internal budget retains partial addresses as incomplete."""
    started = time.process_time()
    G = generic()
    state, group, start, stop = _block(spec)
    R = tuple(group["output_registers"])
    pairs, meta = G._pairs(state, R)
    pivots = _eligible_pivots(state, R)
    retained = pivots[:PIVOT_CAP]
    pp = group["planes"][start:stop]
    witnesses, rejects, attempted = [], Counter(), 0
    expected = len(pp)*len(pairs)*len(retained)
    complete, interruption = True, None
    max_seconds = float(spec.get("max_cpu_seconds", 240))
    try:
        for plane in pp:
            for i, pair in enumerate(pairs):
                for helper in retained:
                    if time.process_time()-started >= max_seconds:
                        raise G.ExactBudgetExceeded("internal block CPU guard reached")
                    attempted += 1
                    try:
                        transform = _transform(state, group, pair, i, helper, plane)
                    except G.CandidateRejected as exc:
                        rejects[str(exc)[:180]] += 1
                        continue
                    # Failed exact identities or canonical invariants are errors,
                    # never scientific rejections of this candidate.
                    raw, proof = _apply_transform(state, transform)
                    old = {int(r): n for r, n in state["raw"]["report"]["local_profile"].items()}
                    new = {int(r): n for r, n in raw["report"]["local_profile"].items()}
                    delta = {r: new.get(r, 0)-old.get(r, 0) for r in sorted(set(old)|set(new))
                             if new.get(r, 0) != old.get(r, 0)}
                    witnesses.append(dict(provider=spec["provider"], group=spec["group"],
                        block=spec["block"], mode=group["mode"], plane=list(plane), helper=helper,
                        canonical_pair=i, basis_indices=pair["basis_indices"],
                        certificate_status=proof["status"], local_profile=new, local_profile_delta=delta,
                        width_inventory=raw["report"]["width_inventory"], private_buffers=83,
                        declared_entrance_rank=0, declared_endpoint_rank=9, new_endpoint_rank=7,
                        last_touched_rank=len(state["geometry"]["literal_terminal"][helper]),
                        frame_edits=len(transform["frame_changes"]),
                        input_gates=len(transform["before"]), output_gates=len(transform["after"]),
                        semantic_sha256=G.semantic_sha(raw), independent_full_semantic_audit="PENDING",
                        native_admission="PENDING", complete_cost="PENDING"))
    except G.ExactBudgetExceeded as exc:
        complete, interruption = False, str(exc)
    if complete:
        need(attempted == expected, "complete bounded frame choices accounted")
        need(attempted == len(witnesses)+sum(rejects.values()), "candidate outcome partition")
    return dict(status=("NOMINEES" if witnesses else "NULL_BOUNDED_GRAMMAR") if complete else "TIMEOUT",
        complete=complete, interruption=interruption, protocol=PROTOCOL,
        provider=spec["provider"], seed=spec["seed"], group=spec["group"], block=spec["block"],
        frame_start=start, frame_stop=stop, mode=group["mode"], planes=pp,
        output_registers=list(R), spaces=meta, pair_cap=PAIR_CAP, pivot_cap=PIVOT_CAP,
        eligible_pivots=len(pivots), retained_pivots=retained,
        truncated_pivots_per_pair=max(0, len(pivots)-PIVOT_CAP),
        expected_constructions=expected, attempted_constructions=attempted,
        unattempted_constructions=expected-attempted, rejections=dict(rejects), witnesses=witnesses,
        unresolved_attempted_constructions=attempted-len(witnesses)-sum(rejects.values()),
        parent_semantic_sha256=state["raw_sha256"], source_attribution=deepcopy(state["attribution"]),
        cpu_seconds=time.process_time()-started,
        seed_effect="Traversal only; exact bases, bounded choices and nominal witnesses are seed-independent",
        completeness="763 anchored planes in two modes; canonical basis pairs and bounded pivots only",
        certification_scope="Exact paired identities, full canonical local profile and cleanup; complete admission pending")


def controls_task(seed):
    """Rank-seven algebra/guard fixtures; published full-word control is separate."""
    from types import SimpleNamespace
    started = time.process_time()
    G = generic()
    plane = [7, 42, 45]
    frame = frame_for(plane)
    full = tuple(1 << i for i in range(9))
    state = dict(raw_sha256="synthetic-rank7-identity", H=(2, 3), live=(2, 3), restored=set(),
                 canonical=SimpleNamespace(start={2: (), 3: ()}, end={2: full, 3: full}),
                 M={r: {(r, ()): Q(1)} for r in (2, 3)}, C={})
    pair = {key: {2: Q(1)} for key in ("u", "v", "alpha", "y")}
    before, after = G._synthesize(pair, 2, frame)
    transform = dict(helper=2, plane=plane, frame=list(frame), before=before, after=after,
                     parent_semantic_sha256=state["raw_sha256"])
    _validate_production(state, transform)
    certificate = G.certificate(state, transform)
    _check_paid_mass({9: 1}, {7: 1})
    negatives = []

    def reject(name, call, expected):
        try:
            call()
        except ValueError as exc:
            need(expected in str(exc), "negative control rejected for an unrelated reason: "+name)
            negatives.append(dict(name=name, status="PASS_REJECTED", reason=str(exc)))
        else:
            raise ValueError("negative control accepted: "+name)

    bad = deepcopy(transform)
    bad["frame"] = list(full[:8])
    reject("rank_eight_frame_in_rank_seven_production", lambda: _validate_production(state, bad),
           "declared rank-seven output frame")
    reject("wrong_paid_mass_decrement", lambda: _check_paid_mass({9: 1}, {8: 1}),
           "exactly two local rank units")
    inactive = deepcopy(transform)
    inactive["helper"] = 4
    reject("inactive_helper", lambda: _validate_production(state, inactive), "fresh unprotected helper")
    restored_state = dict(state, H=(2,), restored={3})
    restored = deepcopy(transform)
    restored["helper"] = 3
    reject("already_restored_protected_helper", lambda: _validate_production(restored_state, restored),
           "fresh unprotected helper")
    protected = deepcopy(transform)
    protected["helper"] = 408
    otherwise_eligible = dict(state, H=(2, 3, 408), live=(2, 3, 408),
        canonical=SimpleNamespace(start={2: (), 3: (), 408: ()},
                                  end={2: full, 3: full, 408: full}))
    reject("excluded_helper408", lambda: _validate_production(otherwise_eligible, protected),
           "helper408 excluded")
    reject("dependent_dual_normals", lambda: frame_for([7, 7, 0]), "three nonzero nine-bit normals")
    all_planes = planes()
    need(all(len(frame_for(p)) == 7 for p in all_planes), "every registered frame has rank7")
    return dict(status="PASS", seed=seed, protocol=PROTOCOL,
        distinct_dual_planes=len(all_planes), anchors=list(ANCHORS),
        synthetic_rank7_positive=certificate, negative_controls=negatives,
        generic_source_sha256=GENERIC_SHA, cpu_seconds=time.process_time()-started,
        source_attribution={provider: deepcopy(state["attribution"])
                            for provider, state in _STATES.items()},
        scope="Synthetic rank7 algebra and explicit guards only; coordinator separately replays published full-word controls")
