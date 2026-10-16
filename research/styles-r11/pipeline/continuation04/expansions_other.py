"""E2: first/middle corrections on the frozen E1 adjacent-pair domain.

CubeJerry/PR1533 is the direct expansion predecessor. Source PR2966 and all
retained lineage notices remain credited. The E1 end-correction result stays
immutable. This module imports only hash-pinned trusted local utilities; no
fetched program is executed and no scientific work runs at import time.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib.util
import itertools
from pathlib import Path
import random
import sys
import time

RR = Path(__file__).resolve().parents[2]
E1_PATH = RR / "pipeline/continuation04/expansions.py"
E1_SHA256 = "5f358c2084cd39f669758cd42c077dbb93726ef79bc8a2055d7ea1f17f7f7442"
PLACEMENTS = ("FIRST", "MIDDLE")
SECTIONS = ("A", "B", "restore")
_E = None


def need(test, message):
    if not test:
        raise ValueError(message)


def _e1():
    global _E
    if _E is None:
        need(hashlib.sha256(E1_PATH.read_bytes()).hexdigest() == E1_SHA256,
             "frozen E1 utility source drift")
        need(not sys.flags.optimize, "enabled assertions required")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_e2_frozen_e1", E1_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _E = module
    return _E


def prepare(records, endpoint, profile, inventory):
    """Once-parent immutable-source preparation; no E1 candidate rerun."""
    result = _e1().prepare(records, endpoint, profile, inventory)
    result.update(method="eight explicit fixed-exterior corners for each of FIRST and MIDDLE corrections; no solver",
                  placements=list(PLACEMENTS), labels_per_adjacent_pair=16,
                  frozen_e1_utility=dict(path=str(E1_PATH.relative_to(RR)), sha256=E1_SHA256))
    return result


def _candidate(state, provider, section, position, variant, placement):
    E = _e1()
    if placement not in PLACEMENTS:
        return None
    result = E._candidate(state, provider, section, position, variant)
    if result is None:
        return None
    result["placement"] = placement
    core = {key: result[key] for key in ("provider", "section", "positions",
                                        "orientation", "variant", "placement")}
    result["candidate_id"] = E.digest(core)
    return result


def _sort_key(candidate):
    return (SECTIONS.index(candidate["section"]), candidate["positions"][0],
            candidate["orientation"], PLACEMENTS.index(candidate["placement"]),
            _e1().VARIANTS.index(tuple(candidate["variant"])))


def census_task(spec):
    provider, seed = spec["provider"], int(spec["seed"])
    E = _e1()
    state, T = E._WORDS[provider], E._trusted()
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
            candidate = _candidate(state, provider, section, p, E.VARIANTS[0], PLACEMENTS[0])
            if candidate is None:
                counts["ineligible_pairs"] += 1
                continue
            counts["eligible_pairs"] += 1
            counts[candidate["orientation"]] += 1
            for placement in PLACEMENTS:
                for variant in E.VARIANTS:
                    candidates.append(_candidate(state, provider, section, p, variant, placement))
                    counts["candidate_variants"] += 1
    candidates.sort(key=_sort_key)
    need(len(candidates) == 16*counts["eligible_pairs"], "two placements times eight labels per pair")
    need(len({c["candidate_id"] for c in candidates}) == len(candidates), "unique literal E2 addresses")
    return dict(status="PASS", provider=provider, seed=seed, complete=True,
        counts=dict(counts), candidates=candidates, candidate_set_sha256=E.digest(candidates),
        parent_semantic_sha256=state["semantic_sha256"], placements=list(PLACEMENTS),
        source_attribution=deepcopy(state["attribution"]), source_pin=deepcopy(state["source_pin"]),
        schedule=dict(seed=seed, section_segments=work), pricing_cap=None, unpriced_if_cap_applied=0,
        cpu_seconds=time.process_time()-begin)


enumerate_task = census_task


def _order(candidate):
    """The reversed old pair with its signed correction inserted first/middle."""
    chain = candidate["chain"]
    coefficient = Q(chain["chord"])
    chord = ["add", chain["i"], chain["k"], coefficient.numerator, coefficient.denominator, []]
    gates = [deepcopy(candidate["original_gates"][1]), deepcopy(candidate["original_gates"][0])]
    gates.insert(0 if candidate["placement"] == "FIRST" else 1, chord)
    return gates


def _frames(boundaries, ordered_gates, variant):
    E = _e1()
    entries = {rec["register"]: E._basis(rec["entry"]) for rec in boundaries.values()}
    exits = {rec["register"]: E._basis(rec["exit"]) for rec in boundaries.values()}
    first, last = ordered_gates[0][1:3], ordered_gates[-1][1:3]
    need(len(set(entries)) == 3 and set(first) <= set(entries) and set(last) <= set(entries),
         "generic boundary addresses match three-gate triangle")
    L1 = E._join(*(entries[r] for r in first))
    L2 = E._join(*entries.values())
    U2, U3 = E._meet(*exits.values()), E._meet(*(exits[r] for r in last))
    frame = dict(L1=L1, L2=L2, U2=U2, U3=U3)
    frame["S"] = frame[variant[0]]
    frame["R"] = frame[variant[1]]
    frame["T"] = frame[variant[2]]
    failures = []
    for left, right in (("L1", "R"), ("R", "S"), ("L2", "S"),
                        ("S", "U2"), ("S", "T"), ("T", "U3")):
        if not E._leq(frame[left], frame[right]):
            failures.append(dict(predicate="frame_inclusion", lower=left, upper=right,
                                 lower_frame=list(frame[left]), upper_frame=list(frame[right])))
    final = {}
    for gate, label in zip(ordered_gates, ("R", "S", "T")):
        for register in gate[1:3]:
            final[register] = frame[label]
    for name, rec in boundaries.items():
        actual, required = final[rec["register"]], exits[rec["register"]]
        if not E._leq(actual, required):
            failures.append(dict(predicate="exit_inclusion", register=name))
        if rec["equality_exit"] and actual != required:
            failures.append(dict(predicate="exit_equality", register=name,
                                 actual=list(actual), required=list(required)))
    return frame, failures


def _replacement(candidate, frames):
    result = _order(candidate)
    for gate, label in zip(result, ("R", "S", "T")):
        gate[-1] = list(frames[label])
    return result


def _construct(state, candidate):
    E = _e1()
    T, raw = E._trusted(), state["raw"]
    need(candidate["parent_semantic_sha256"] == state["semantic_sha256"], "stale parent word")
    expected = _candidate(state, candidate["provider"], candidate["section"],
                          candidate["positions"][0], candidate["variant"], candidate["placement"])
    need(expected is not None and expected == candidate, "stale preimage or unregistered E2 address")
    boundaries = E._boundaries(state, candidate)
    ordered = _order(candidate)
    frames, failures = _frames(boundaries, ordered, candidate["variant"])
    last_registers = set(ordered[-1][1:3])
    absent_last = next(name for name, rec in boundaries.items() if rec["register"] not in last_registers)
    witness = dict(boundaries=boundaries, frames={k: list(v) for k, v in frames.items()},
        predicates_passed=not failures, failures=failures, placement=candidate["placement"],
        new_operand_order=[list(g[1:3]) for g in ordered],
        first_gate_registers=list(ordered[0][1:3]), last_gate_registers=list(ordered[-1][1:3]),
        middle_exit_register=absent_last,
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
    before_bill, after_bill = E._local_bill(old_window, boundaries), E._local_bill(new_window, boundaries)
    need(before_bill["rank_mass"] == after_bill["rank_mass"], "complete boundary rank-mass identity")
    section, position = candidate["section"], candidate["positions"][0]
    edited = deepcopy(raw)
    edited[section] = deepcopy(raw[section][:position] + new_window + raw[section][position+2:])
    need(edited[section][:position] == raw[section][:position]
         and edited[section][position+3:] == raw[section][position+2:],
         "exact frozen exterior prefix/suffix")
    if section == "B":
        need(all(rec[0] != position+1 for rec in raw["warps"]), "no hidden warp between gates")
        edited["warps"] = [[rec[0] + int(rec[0] > position+1)] + deepcopy(rec[1:])
                           for rec in raw["warps"]]
    for other in SECTIONS:
        if other != section:
            need(edited[other] == raw[other], "every other scalar section stays literal")
    need(T._boundary_signature(edited) == state["boundaries"], "fixed cut/endpoint/compensation ABI")
    witness.update(complete_window_matrix_identity=True,
        complete_window_inverse_transpose_identity=True,
        exact_exterior_prefix_suffix_identity=True, scalar_instruction_delta=1,
        compensation_reuse="Exact scalar interval identity on non-target registers; all cut/warp interfaces frozen",
        original_window_bill=before_bill, expanded_window_bill=after_bill,
        private_buffers=86, physical_families=66808, semantic_warp_order_preserved=True)
    return edited, witness


def price_task(spec):
    E = _e1()
    provider, seed, candidate = spec["provider"], int(spec["seed"]), spec["candidate"]
    state, T, W = E._WORDS[provider], E._trusted(), E._W()
    need(candidate["provider"] == provider, "candidate provider binding")
    begin = time.process_time()
    result = dict(provider=provider, seed=seed, candidate_id=candidate["candidate_id"],
        candidate=deepcopy(candidate), source_pin=deepcopy(state["source_pin"]),
        source_attribution=deepcopy(state["attribution"]), local_profile=None,
        width_inventory=None, moment_delta=None, word=None, optimizer=None,
        scope="One explicit corner for FIRST/MIDDLE correction on a fixed-exterior adjacent pair; no whole-word optimum or native/kappa admission")
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
    need(E._mass(canonical.paid) == E._mass(old.paid), "complete paid mass unchanged")
    expected = Counter(old.paid)
    expected.subtract(witness["original_window_bill"]["profile"])
    expected.update(witness["expanded_window_bill"]["profile"])
    need(all(n >= 0 for n in expected.values()), "nonnegative complete child counts")
    need(E._profile(expected) == canonical.paid, "canonical full delta equals boundary-chain delta")
    edited["report"]["local_profile"] = {str(r): n for r, n in sorted(canonical.paid.items())}
    edited["cleanup"] = W.derived_borrow_cleanup(canonical)
    complete = W.WordData(edited, state["attribution"])
    need(complete.paid == canonical.paid, "cleanup regeneration preserves paid profile")
    need(T._boundary_signature(edited) == state["boundaries"], "final fixed ABI")
    npre = int(edited.get("prelude_events", 0))
    need(edited["A"][:npre] == state["raw"]["A"][:npre], "entry prelude literal identity")
    moment = E._moment_delta(complete.paid, old.paid)
    result.update(local_profile=complete.paid, width_inventory=dict(Counter(T._widths(complete))),
        ordered_widths=T._widths(complete), moment_delta=moment,
        built_semantic_sha256=E.digest(edited), cleanup_sha256=E.digest(edited["cleanup"]),
        compensation_sha256=E.digest(edited["compensation"]),
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
    E, begin = _e1(), time.process_time()
    seed = int(spec["seed"]) if isinstance(spec, dict) else int(spec)
    # Registered control reuse, not a rerun of E1's scientific candidate census.
    inherited = E.controls_task(seed)
    T = E._trusted()
    checks = []

    def check(name, condition):
        need(condition, "E2 control failed: " + name)
        checks.append(dict(name=name, status="PASS"))

    def gate(target, source, coefficient, frame=()):
        coefficient = Q(coefficient)
        return ["add", target, source, coefficient.numerator, coefficient.denominator, list(frame)]

    for a, b in itertools.product((-2, -1, Q(-1, 2), Q(1, 2), 1, 2), repeat=2):
        A, B = gate(3, 4, a), gate(4, 5, b)
        for old in ([A, B], [B, A]):
            chain = E._chain(old, 112)
            for placement in PLACEMENTS:
                candidate = dict(original_gates=old, chain=chain, placement=placement)
                new = _order(candidate)
                name = f"{chain['orientation']}_{placement}_{a}_{b}"
                chord_position = 0 if placement == "FIRST" else 1
                for dual in (False, True):
                    check(f"identity_{dual}_"+name, T._sequential_matrix(old, dual) == T._sequential_matrix(new, dual))
                    wrong = deepcopy(new); wrong[chord_position][3] *= -1
                    check(f"wrong_sign_{dual}_"+name, T._sequential_matrix(old, dual) != T._sequential_matrix(wrong, dual))
                    wrong = deepcopy(new); wrong[chord_position][3] *= 2
                    check(f"wrong_magnitude_{dual}_"+name, T._sequential_matrix(old, dual) != T._sequential_matrix(wrong, dual))

    fixture_reports = []
    for old in ([gate(3, 4, 1, [1]), gate(4, 5, 1, [1])],
                [gate(4, 5, 1, [1]), gate(3, 4, 1, [1])]):
        chain = E._chain(old, 112)
        for placement in PLACEMENTS:
            candidate = dict(original_gates=old, chain=chain, placement=placement)
            ordered = _order(candidate)
            first, middle, last = (set(g[1:3]) for g in ordered)
            x, y, z = next(iter(first & middle)), next(iter(first & last)), next(iter(middle & last))
            check("triangle_contact_roles_"+chain["orientation"]+placement,
                  len({x, y, z}) == 3 and x not in last and z not in first)
            boundaries = {name: dict(register=register, entry=([1] if register == z else []),
                                     exit=([1] if register == x else [2, 1]), equality_exit=False)
                          for name, register in (("i", chain["i"]), ("j", chain["j"]), ("k", chain["k"]))}
            before = E._local_bill(old, boundaries)
            check("positive_fixture_old_"+chain["orientation"]+placement, before["profile"] == {1: 4})
            observations = []
            for variant in E.VARIANTS:
                frames, failures = _frames(boundaries, ordered, variant)
                check("corner_feasible_"+chain["orientation"]+placement+str(variant), not failures)
                after = E._local_bill(_replacement(candidate, frames), boundaries)
                check("corner_mass_"+chain["orientation"]+placement+str(variant),
                      after["rank_mass"] == before["rank_mass"] == 4)
                observations.append(dict(variant=list(variant), profile=after["profile"],
                                         moment=E._moment_delta(after["profile"], before["profile"])))
            favorable = [r for r in observations if Q(r["moment"]["upper"]) < 0]
            check("strict_positive_"+chain["orientation"]+placement,
                  bool(favorable) and any(r["profile"] == {1: 2, 2: 1} for r in favorable))
            fixture_reports.append(dict(orientation=chain["orientation"], placement=placement,
                contact_roles=dict(x=x, y=y, z=z), original_profile=before["profile"], corners=observations))
            for equality_register in (x, y):
                equality = {name: dict(register=register, entry=[], exit=[1],
                                      equality_exit=(register == equality_register))
                            for name, register in (("i", chain["i"]), ("j", chain["j"]), ("k", chain["k"]))}
                _, failures = _frames(equality, ordered, ("L2", "L1", "S"))
                check(f"equality_is_not_inclusion_{chain['orientation']}_{placement}_{equality_register}",
                      any(f["predicate"] == "exit_equality" for f in failures)
                      and not any(f["predicate"] in ("frame_inclusion", "exit_inclusion") for f in failures))
            impossible = deepcopy(boundaries)
            next(rec for rec in impossible.values() if rec["register"] == x)["exit"] = []
            _, failures = _frames(impossible, ordered, ("L2", "L1", "U3"))
            check("inclusion_reject_"+chain["orientation"]+placement, bool(failures))

    A, B = gate(3, 4, 1), gate(4, 5, 1)
    raw = dict(A=[A, B], B=[], restore=[], warps=[], prelude_events=0, report={"v": 112})
    state = dict(raw=raw, semantic_sha256=E.digest(raw))
    check("END_is_not_E2", _candidate(state, "base", "A", 0, E.VARIANTS[0], "END") is None)
    for placement in PLACEMENTS:
        good = _candidate(state, "base", "A", 0, E.VARIANTS[0], placement)
        for field in ("preimage", "source"):
            bad = deepcopy(good)
            if field == "preimage":
                bad["original_gates"][0][3] = 2
            else:
                bad["parent_semantic_sha256"] = "0"*64
            try:
                _construct(state, bad)
            except ValueError:
                rejected = True
            else:
                rejected = False
            check("stale_"+field+"_"+placement, rejected)
    return dict(status="PASS", seed=seed, checks=checks, fixtures=fixture_reports,
        inherited_e1_controls=inherited,
        unchanged_local_audits="Separate mandatory source2966.baseline_task for both providers and seeds",
        source_attribution={k: deepcopy(v["attribution"]) for k, v in E._WORDS.items()},
        frozen_e1_utility_sha256=E1_SHA256,
        scope="Only FIRST and MIDDLE corrections on the unchanged adjacent-pair domain; E1 remains immutable",
        cpu_seconds=time.process_time()-begin)
