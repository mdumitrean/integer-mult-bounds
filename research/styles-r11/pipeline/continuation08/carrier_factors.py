"""Exact fixed-exterior carrier factors; coordinator execution only.

Direct realized predecessor: Jeremy Kothe/PR3015 R1.  Fixed-boundary
flag/concavity precedent: CubeJerry/PR1533.  Full inherited source credits
are retained in every result.  No fetched implementation is executed.
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
UTILITY_PATH = RR / "pipeline/continuation04/expansions.py"
UTILITY_SHA256 = "5f358c2084cd39f669758cd42c077dbb93726ef79bc8a2055d7ea1f17f7f7442"
SECTIONS = ("A", "B")
CORNERS = tuple((y, x, z) for y in ("A", "C")
                for x in ("L", "Y") for z in ("Y", "D"))
_U = None
_WORDS = {}
_FIXTURES = {}
_DECLARATION = None
_ENDPOINT = None
_COSTS = {}
_INSTALLED = {}


def need(test, message):
    if not test:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def _util():
    global _U
    if _U is None:
        need(hashlib.sha256(UTILITY_PATH.read_bytes()).hexdigest() == UTILITY_SHA256,
             "frozen fixed-frame utility source drift")
        need(not sys.flags.optimize, "enabled scientific assertions required")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles08_fixed_utilities", UTILITY_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _U = module
    return _U


def _T():
    return _util()._trusted()


def _W():
    return _util()._W()


def _profile(value):
    return {int(k): int(v) for k, v in sorted(value.items(), key=lambda p: int(p[0])) if v}


def _mass(value):
    return sum(int(k)*int(v) for k, v in value.items())


def _dyadic(value):
    value = Q(value)
    return value != 0 and value.denominator & (value.denominator-1) == 0


def _load_record(record):
    raw, attribution = record["raw"], deepcopy(record["attribution"])
    W, T = _W(), _T()
    canonical = W.WordData(raw, attribution)
    widths = T._widths(canonical)
    need(canonical.family == "BORROW-WORD", "registered BORROW word family")
    need(canonical.paid == _profile(record["expected_profile"]), "source paid profile binding")
    need(dict(Counter(widths)) == _profile(record["expected_inventory"]), "source inventory binding")
    need(len(raw["helper_final"]) == int(record["expected_buffers"]), "source buffer binding")
    need(len(canonical.live) == int(record["expected_independent_inputs"]), "source live-input binding")
    need(len(canonical.helpers) == int(record["expected_helpers"]), "source helper binding")
    need(canonical.h == 9 and canonical.v == 112 and canonical.n == 704,
         "registered finite geometry")
    need(not raw.get("early_cleanup"), "fixed cleanup regime")
    need(all(g[0] != "warp" or i < int(raw.get("prelude_events", 0))
             for i, g in enumerate(raw["A"])), "post-prelude A has no hidden warp")
    semantic = digest(raw)
    need(semantic == record["original_semantic_sha256"], "source semantic hash binding")
    return dict(raw=raw, attribution=attribution, canonical=canonical,
                widths=widths, semantic_sha256=semantic,
                source_pin=deepcopy(record.get("source_pin", {})),
                boundaries=T._boundary_signature(raw),
                fixed=_util()._fixed_graph(raw, canonical),
                centres=set(raw["centers"]), private_buffers=int(record["expected_buffers"]),
                physical_families=int(record["expected_physical_families"]))


def prepare(records, endpoint, fixtures=None, declaration=None):
    """Registered parent-only preparation: source objects/costs loaded once."""
    global _ENDPOINT, _COSTS, _DECLARATION
    need(not _WORDS, "once-only carrier-factor preparation")
    need(set(records) == {"base", "extra"}, "both source providers")
    _ENDPOINT = Q(endpoint)
    need(0 < _ENDPOINT < 1, "strictly concave registered tariff")
    ceiling = _T()._module("ceiling")
    _COSTS = {r: ceiling.child_cost(r, 73, _ENDPOINT) for r in range(1, 10)}
    summaries = {}
    for provider, record in sorted(records.items()):
        state = _load_record(record)
        _WORDS[provider] = state
        summaries[provider] = dict(parent_semantic_sha256=state["semantic_sha256"],
            local_profile=state["canonical"].paid, width_inventory=dict(Counter(state["widths"])),
            private_buffers=state["private_buffers"], physical_families=state["physical_families"],
            fixed_nodes=len(state["fixed"]["nodes"]), source_pin=state["source_pin"],
            source_attribution=state["attribution"])
    need(fixtures is not None and declaration is not None, "registered PR2979/3015 positive fixture inputs")
    need(set(fixtures) == {"base", "extra"}, "both positive-control providers")
    for provider, record in sorted(fixtures.items()):
        _FIXTURES[provider] = _load_record(record)
    _DECLARATION = deepcopy(declaration)
    return dict(status="PASS", endpoint=str(_ENDPOINT), providers=summaries,
        source_sections=list(SECTIONS), corners=[list(x) for x in CORNERS],
        fixture_sources={p: dict(source_pin=s["source_pin"], source_attribution=s["attribution"],
                                semantic_sha256=s["semantic_sha256"]) for p, s in _FIXTURES.items()},
        utility_source=dict(path=str(UTILITY_PATH.relative_to(RR)), sha256=UTILITY_SHA256),
        scope="Contact-adjacent A/B fans with disjoint interveners; eight exact fixed-exterior corners. Restore is control-only.")


def _fan(gates, centres=(), carrier=0):
    T = _T()
    if len(gates) != 2 or not all(T._add(g) for g in gates) or carrier not in (0, 1):
        return None
    first, second = gates if carrier == 0 else gates[::-1]
    if first[1] == second[1]:
        kind, i, j, k = "in", first[1], first[2], second[2]
    elif first[2] == second[2]:
        kind, i, j, k = "out", first[2], first[1], second[1]
    else:
        return None
    if len({i, j, k}) != 3 or set((i, j, k)).intersection(centres):
        return None
    a, b = Q(first[3], first[4]), Q(second[3], second[4])
    ratio = b/a
    return dict(kind=kind, i=i, j=j, k=k, a=str(a), b=str(b), ratio=str(ratio),
                carrier=carrier, coefficient_admissible=_dyadic(ratio))


def _cid(address):
    return ".".join(str(x) for x in address)


def _address(value):
    if isinstance(value, str):
        parts = value.split(".")
        need(len(parts) == 6, "candidate address arity")
        sec, p, q, kind, carrier, corner = parts
        return [sec, int(p), int(q), kind, int(carrier), int(corner)]
    if isinstance(value, dict):
        result = list(value.get("address") or _address(value["candidate_id"]))
        if "candidate_id" in value:
            need(_cid(result) == value["candidate_id"], "candidate ID/address equality")
        return result
    return list(value)


def _candidate(state, provider, address, allow_restore=False):
    section, p, q, kind, carrier, corner = _address(address)
    raw = state["raw"]
    allowed = SECTIONS + (("restore",) if allow_restore else ())
    if section not in allowed or not (type(p) is int and type(q) is int
            and 0 <= p < q < len(raw[section])) or carrier not in (0, 1) or corner not in range(8):
        return None
    if not _T()._same_segment(raw, section, (p, q)):
        return None
    old = [raw[section][p], raw[section][q]]
    fan = _fan(old, state.get("centres", set(raw.get("centers", []))), carrier)
    if fan is None or fan["kind"] != kind or not fan["coefficient_admissible"]:
        return None
    support = {fan[name] for name in ("i", "j", "k")}
    if any(g[0] not in ("add", "scale") or support.intersection(_W().registers(g))
           for g in raw[section][p+1:q]):
        return None
    compact = dict(candidate_id=_cid(address), pair_key=_cid(address), address=list(address))
    return dict(**compact, provider=provider, section=section, positions=[p, q], chain=fan,
        corner=corner, variant=list(CORNERS[corner]), parent_semantic_sha256=state["semantic_sha256"],
        original_gates=deepcopy(old), interval_sha256=digest(raw[section][p:q+1]),
        disjoint_intervening_count=q-p-1)


def _resolve(state, provider, value, allow_restore=False):
    if isinstance(value, dict):
        if "parent_semantic_sha256" in value:
            need(value["parent_semantic_sha256"] == state["semantic_sha256"], "stale source binding")
    result = _candidate(state, provider, _address(value), allow_restore)
    need(result is not None, "invalid or excluded registered address")
    if isinstance(value, dict) and "interval_sha256" in value:
        need(value["interval_sha256"] == result["interval_sha256"], "stale interval preimage")
    return result


def _enumerate(provider):
    state, W, T = _WORDS[provider], _W(), _T()
    counts = Counter(segments=0, examined_contact_pairs=0, nonfan_contact_pairs=0,
        centre_rejected_pairs=0, intervening_contact_rejected_pairs=0,
        eligible_pairs=0, literal_adjacent_pairs=0, exposed_pairs=0,
        ratio_rejected_orientations=0, admissible_carrier_choices=0, candidates=0)
    candidates = []
    for section in SECTIONS:
        gates = state["raw"][section]
        for first, last in T._segments(state["raw"], section):
            counts["segments"] += 1
            previous = {}
            for q in range(first, last):
                gate = gates[q]
                regs = W.registers(gate)
                if T._add(gate):
                    for p in sorted({previous[r] for r in regs if r in previous}):
                        counts["examined_contact_pairs"] += 1
                        old = [gates[p], gate]
                        fan = _fan(old, (), 0)
                        if fan is None:
                            counts["nonfan_contact_pairs"] += 1
                            continue
                        support = {fan[k] for k in ("i", "j", "k")}
                        if support & state["centres"]:
                            counts["centre_rejected_pairs"] += 1
                            continue
                        if any(g[0] not in ("add", "scale") or support.intersection(W.registers(g))
                               for g in gates[p+1:q]):
                            counts["intervening_contact_rejected_pairs"] += 1
                            continue
                        counts["eligible_pairs"] += 1
                        counts["literal_adjacent_pairs" if q == p+1 else "exposed_pairs"] += 1
                        counts["kind_"+fan["kind"]] += 1
                        counts["max_disjoint_gap"] = max(counts["max_disjoint_gap"], q-p-1)
                        for carrier in (0, 1):
                            selected = _fan(old, state["centres"], carrier)
                            if not selected["coefficient_admissible"]:
                                counts["ratio_rejected_orientations"] += 1
                                continue
                            counts["admissible_carrier_choices"] += 1
                            for corner in range(8):
                                address = [section, p, q, fan["kind"], carrier, corner]
                                candidates.append(dict(candidate_id=_cid(address), pair_key=_cid(address), address=address))
                                counts["candidates"] += 1
                for r in regs:
                    previous[r] = q
    candidates.sort(key=lambda c: (SECTIONS.index(c["address"][0]), *c["address"][1:]))
    need(len({c["candidate_id"] for c in candidates}) == len(candidates), "unique contact addresses")
    need(len(candidates) == 8*counts["admissible_carrier_choices"], "complete eight-corner coverage")
    return candidates, dict(counts)


def census_task(spec):
    begin = time.process_time()
    provider, seed = spec["provider"], int(spec["seed"])
    candidates, counts = _enumerate(provider)
    state = _WORDS[provider]
    return dict(status="PASS", provider=provider, seed=seed, complete=True,
        candidates=candidates, counts=counts, domain_sha256=digest(candidates),
        candidate_set_sha256=digest(candidates), parent_semantic_sha256=state["semantic_sha256"],
        source_attribution=state["attribution"], source_pin=state["source_pin"],
        source_sections=list(SECTIONS), restore_search=False, pricing_cap=None,
        cpu_seconds=time.process_time()-begin)


def install_census(provider, receipt):
    """Parent installs a saved, agreed census before workers fork; no re-test."""
    need(receipt["provider"] == provider and receipt["complete"] and receipt["status"] == "PASS",
         "complete registered census")
    need(receipt["parent_semantic_sha256"] == _WORDS[provider]["semantic_sha256"], "census parent binding")
    need(digest(receipt["candidates"]) == receipt["domain_sha256"], "census domain binding")
    _INSTALLED[provider] = deepcopy(receipt["candidates"])


def _frames(boundaries, corner):
    U = _util()
    E = {k: U._basis(v["entry"]) for k, v in boundaries.items()}
    O = {k: U._basis(v["exit"]) for k, v in boundaries.items()}
    L, A = U._join(E["j"], E["k"]), U._join(*E.values())
    D, C = U._meet(O["j"], O["k"]), U._meet(*O.values())
    f = dict(L=L, A=A, C=C, D=D)
    y, x, z = CORNERS[corner]
    f["Y"] = f[y]; f["X"] = f[x]; f["Z"] = f[z]
    failed = []
    for low, high in (("L", "X"), ("X", "Y"), ("A", "Y"), ("Y", "C"),
                      ("Y", "Z"), ("Z", "D")):
        if not U._leq(f[low], f[high]):
            failed.append(dict(predicate="frame_inclusion", lower=low, upper=high,
                               lower_frame=list(f[low]), upper_frame=list(f[high]),
                               excluded_vector=next(v for v in f[low] if not U._leq((v,),f[high]))))
    final = dict(i=f["Y"], j=f["Z"], k=f["Z"])
    for name in ("i", "j", "k"):
        if not U._leq(final[name], O[name]):
            failed.append(dict(predicate="exit_inclusion", register=name,
                               actual=list(final[name]), required=list(O[name]),
                               excluded_vector=next(v for v in final[name] if not U._leq((v,),O[name]))))
        if boundaries[name]["equality_exit"] and final[name] != O[name]:
            failed.append(dict(predicate="exit_equality", register=name,
                               actual=list(final[name]), required=list(O[name])))
    return f, failed


def _gate(target, source, coefficient, frame=()):
    q = Q(coefficient)
    return ["add", target, source, q.numerator, q.denominator, list(frame)]


def _replacement(candidate, frames):
    c = candidate["chain"]
    i, j, k = (c[x] for x in ("i", "j", "k"))
    a, t = Q(c["a"]), Q(c["ratio"])
    if c["kind"] == "in":
        return [_gate(j, k, t, frames["X"]), _gate(i, j, a, frames["Y"]),
                _gate(j, k, -t, frames["Z"])]
    return [_gate(k, j, -t, frames["X"]), _gate(j, i, a, frames["Y"]),
            _gate(k, j, t, frames["Z"])]


def _moment(delta):
    lower = upper = Q(0)
    for r, n in delta.items():
        lo, hi = _COSTS[r]
        lower += n*(lo if n >= 0 else hi)
        upper += n*(hi if n >= 0 else lo)
    return dict(lower=str(lower), upper=str(upper), endpoint=str(_ENDPOINT),
                exact_profile_identity=not delta)


def _screen(state, candidate, detailed=False):
    U, T = _util(), _T()
    boundary = U._boundaries(state, candidate)
    frames, failures = _frames(boundary, candidate["corner"])
    result = {key: deepcopy(candidate[key]) for key in ("candidate_id", "pair_key", "address")}
    result.update(status="REJECTED_GUARD", profile_delta=None, moment_delta=None)
    if failures:
        result["guard_failures"] = failures
        if detailed:
            result["proof"] = dict(boundaries=boundary, frames={k: list(v) for k, v in frames.items()}, failures=failures)
        return result
    new = _replacement(candidate, frames)
    old = candidate["original_gates"]
    need(T._sequential_matrix(old) == T._sequential_matrix(new), "exact fan factor forward identity")
    need(T._sequential_matrix(old, True) == T._sequential_matrix(new, True), "exact fan factor dual identity")
    before, after = U._local_bill(old, boundary), U._local_bill(new, boundary)
    need(before["rank_mass"] == after["rank_mass"], "complete boundary mass identity")
    delta = Counter(after["profile"]); delta.subtract(before["profile"])
    delta = _profile(delta)
    need(_mass(delta) == 0, "signed delta exact mass neutrality")
    moment = _moment(delta)
    if Q(moment["upper"]) < 0:
        status = "PASS_CANDIDATE"
    elif not delta or Q(moment["lower"]) >= 0:
        status = "NO_GAIN"
    else:
        status = "EXPLORATORY"
    result.update(status=status, profile_delta=delta, moment_delta=moment,
                  boundary_mass=before["rank_mass"], forward_dual_identity=True)
    if detailed:
        result["proof"] = dict(boundaries=boundary, frames={k: list(v) for k, v in frames.items()},
            original_window_bill=before, factored_window_bill=after, new_gates=new,
            failures=[], equality_exits=[k for k, v in boundary.items() if v["equality_exit"]],
            interval_sha256=candidate["interval_sha256"],
            disjoint_intervening_count=candidate["disjoint_intervening_count"],
            literal_exterior_frames_frozen=True, corner=list(CORNERS[candidate["corner"]]))
    return result


def shard_task(spec):
    begin = time.process_time()
    provider, seed = spec["provider"], int(spec["seed"])
    shard, shards = int(spec["shard"]), int(spec.get("shards", 64))
    need(shards == 64 and 0 <= shard < shards, "registered 64-shard partition")
    candidates = _INSTALLED.get(provider)
    if candidates is None:
        candidates, _ = _enumerate(provider)
    indexed = [(i, c) for i, c in enumerate(candidates) if i % shards == shard]
    random.Random(seed).shuffle(indexed)
    rows, favorable = [], []
    counts = Counter(candidates=len(indexed), PASS_CANDIDATE=0, NO_GAIN=0,
                     REJECTED_GUARD=0, EXPLORATORY=0)
    for ordinal, compact in indexed:
        candidate = _resolve(_WORDS[provider], provider, compact)
        row = _screen(_WORDS[provider], candidate)
        row["ordinal"] = ordinal
        rows.append(row)
        counts[row["status"]] += 1
        if row["status"] == "PASS_CANDIDATE":
            favorable.append(deepcopy(row))
    rows.sort(key=lambda r: r["ordinal"])
    favorable.sort(key=lambda r: r["ordinal"])
    counts["unresolved"] = counts["EXPLORATORY"]
    state = _WORDS[provider]
    return dict(status="PASS", provider=provider, seed=seed, shard=shard, shards=shards,
        complete=True, counts=dict(counts), rows=rows, favorable=favorable,
        domain_sha256=digest(candidates), shard_rows_sha256=digest(rows),
        parent_semantic_sha256=state["semantic_sha256"],
        source_attribution=state["attribution"], source_pin=state["source_pin"],
        canonical_full_words_built=0, primitive_cost_included=False,
        scope="Exact fixed-exterior recursive boundary screen; favorable rows are not full-word/native/supplier admissions.",
        cpu_seconds=time.process_time()-begin)


def _window_matrix(gates, dual=False):
    """Sparse independent sequential oracle including disjoint scalar scales."""
    registers = sorted({r for gate in gates for r in _W().registers(gate)})
    rows = {r: {r: Q(1)} for r in registers}
    for gate in gates:
        if gate[0] == "add":
            target, source, coefficient = gate[1], gate[2], Q(gate[3], gate[4])
            if target == source:
                multiplier = 1 + coefficient
                need(multiplier != 0, "invertible self-add in intervening context")
                if dual:
                    multiplier = 1 / multiplier
                rows[target] = {k: v*multiplier for k, v in rows[target].items() if v*multiplier}
                continue
            if dual:
                target, source, coefficient = source, target, -coefficient
            result = dict(rows[target])
            for k, value in rows[source].items():
                result[k] = result.get(k, Q(0)) + coefficient*value
            rows[target] = {k: v for k, v in result.items() if v}
        elif gate[0] == "scale":
            target, coefficient = gate[1], Q(gate[2], gate[3])
            need(coefficient != 0, "invertible intervening scale")
            if dual:
                coefficient = 1 / coefficient
            rows[target] = {k: v*coefficient for k, v in rows[target].items() if v*coefficient}
        else:
            raise ValueError("unregistered scalar opcode inside exposure")
    return rows


def _materialize(state, candidate, screening):
    T, U, W = _T(), _util(), _W()
    need(screening["profile_delta"] is not None, "only feasible corner can be materialized")
    need(digest(state["raw"]) == state["semantic_sha256"], "unchanged parent bytes in memory")
    section, (p, q) = candidate["section"], candidate["positions"]
    raw = state["raw"]
    middle = raw[section][p+1:q]
    new_gates = screening["proof"]["new_gates"]
    old_window = raw[section][p:q+1]
    new_window = new_gates + deepcopy(middle)
    need(_window_matrix(old_window) == _window_matrix(new_window), "complete exposed-window forward identity")
    need(_window_matrix(old_window, True) == _window_matrix(new_window, True), "complete exposed-window dual identity")
    edited = deepcopy(raw)
    edited[section] = deepcopy(raw[section][:p] + new_window + raw[section][q+1:])
    need(edited[section][:p] == raw[section][:p]
         and edited[section][q+2:] == raw[section][q+1:], "exact external scalar prefix/suffix")
    need(edited[section][p+3:q+2] == middle, "intervening gate order and frames preserved")
    if section == "B":
        need(not any(p < rec[0] <= q for rec in raw["warps"]), "no B barrier in exposed interval")
        edited["warps"] = [[rec[0]+int(rec[0] > q)] + deepcopy(rec[1:]) for rec in raw["warps"]]
    for other in ("A", "B", "restore"):
        if other != section:
            need(edited[other] == raw[other], "other scalar sections unchanged")
    need(T._boundary_signature(edited) == state["boundaries"], "fixed interface/compensation signature")
    npre = int(raw.get("prelude_events", 0))
    need(edited["A"][:npre] == raw["A"][:npre], "literal entry prelude preserved")
    word = W.WordData(edited, state["attribution"], assert_profile=False)
    old = state["canonical"]
    need(word.helpers == old.helpers and word.start == old.start and word.end == old.end,
         "ordered helpers and exact endpoint interfaces")
    need(T._widths(word) == state["widths"], "ordered helper widths")
    expected = Counter(old.paid); expected.update(screening["profile_delta"])
    need(all(n >= 0 for n in expected.values()), "nonnegative full paid counts")
    need(_profile(expected) == word.paid, "independent full canonical/boundary delta parity")
    need(_mass(word.paid) == _mass(old.paid), "complete canonical rank mass")
    edited["report"]["local_profile"] = {str(r): n for r, n in sorted(word.paid.items())}
    edited["cleanup"] = W.derived_borrow_cleanup(word)
    checked = W.WordData(edited, state["attribution"])
    need(checked.paid == word.paid, "regenerated cleanup keeps canonical paid ledger")
    return edited, checked


def build_candidate(provider, candidate_id):
    """Build one address, with canonical ledger; no artifact write or full audit."""
    state = _WORDS[provider]
    candidate = _resolve(state, provider, candidate_id)
    screening = _screen(state, candidate, detailed=True)
    if screening["profile_delta"] is None:
        return None, screening
    raw, canonical = _materialize(state, candidate, screening)
    screening.update(local_profile=canonical.paid, width_inventory=dict(Counter(state["widths"])),
        ordered_widths=state["widths"], canonical_profile_and_boundary_delta_agree=True,
        semantic_sha256=digest(raw), cleanup_sha256=digest(raw["cleanup"]))
    return raw, screening


def validate_selected(spec):
    begin = time.process_time()
    provider, seed = spec["provider"], int(spec["seed"])
    candidate_id = spec.get("candidate_id") or spec["candidate"]["candidate_id"]
    raw, result = build_candidate(provider, candidate_id)
    state = _WORDS[provider]
    result.update(provider=provider, seed=seed, word=None,
        source_pin=state["source_pin"], source_attribution=state["attribution"],
        private_buffers=state["private_buffers"], physical_families=state["physical_families"],
        native_admission=False, scalar_instruction_delta=1,
        fresh_all_column_audit="Required separate coordinator phase; not claimed by this constructor")
    if raw is not None and result["status"] == "PASS_CANDIDATE":
        directory = Path(spec["output_dir"])
        if not directory.is_absolute():
            directory = RR / directory
        directory = directory.resolve()
        need(directory.is_relative_to((RR/"data/continuation-08/candidates").resolve()),
             "retained full words restricted to continuation08 data candidates")
        result["word"] = _T()._write_word(raw, directory/provider, candidate_id)
    result["cpu_seconds"] = time.process_time()-begin
    return result


def _small_flag_controls(check):
    """Independent exhaustive GF(2)^3 set oracle; no source-word search."""
    def span(vectors):
        result = {0}
        for vector in vectors:
            result |= {x ^ vector for x in tuple(result)}
        return frozenset(result)
    spaces = sorted({span(v for v in range(1,8) if mask & (1 << (v-1)))
                     for mask in range(128)}, key=lambda x:(len(x), tuple(sorted(x))))
    check("small_flag_all_16_subspaces",len(spaces)==16)
    def dim(space):
        value = len(space)
        check_value = value.bit_length()-1
        need(1 << check_value == value, "oracle subspace cardinality")
        return check_value
    fixtures = [
        ("nested_positive", [[1],[],[]], [[1],[1,2],[1,2]], ()),
        ("noncoordinate", [[3],[],[]], [[3],[3,4],[3,4]], ()),
        ("independent_entrances", [[1],[2],[]], [[1,2],[1,2,4],[1,2,4]], ()),
        ("middle_exit_equality", [[],[],[]], [[3],[1,2,4],[1,2,4]], ("i",)),
        ("outer_exit_equality", [[],[],[]], [[1],[1,2],[1,2]], ("j",)),
        ("all_exit_equalities", [[],[],[]], [[1],[1,2],[1,2]], ("i","j","k")),
        ("impossible_exit", [[1],[2],[]], [[1],[1],[1,2]], ()),
    ]
    tariffs = [(Q(0),Q(6),Q(10),Q(13)), (Q(0),Q(1),Q(2),Q(3)),
               (Q(0),Q(1),Q(3,2),Q(7,4))]
    reports=[]
    for name,entry,exit_frames,equalities in fixtures:
        names=("i","j","k")
        E={k:span(v) for k,v in zip(names,entry)}
        O={k:span(v) for k,v in zip(names,exit_frames)}
        boundary={k:dict(register=r,entry=entry[z],exit=exit_frames[z],equality_exit=k in equalities)
                  for z,(k,r) in enumerate(zip(names,(3,4,5)))}
        def feasible(X,Y,Z):
            return (E["j"] <= X and E["k"] <= X and E["i"] <= Y
                    and X <= Y <= Z and Y <= O["i"] and Z <= O["j"] and Z <= O["k"]
                    and all((Y if k=="i" else Z)==O[k] for k in equalities))
        def ranks(X,Y,Z):
            x,y,z=dim(X),dim(Y),dim(Z)
            return (x-dim(E["j"]),x-dim(E["k"]),y-dim(E["i"]),y-x,
                    z-y,z-x,dim(O["i"])-y,dim(O["j"])-z,dim(O["k"])-z)
        all_flags=[(X,Y,Z) for X,Y,Z in itertools.product(spaces,repeat=3) if feasible(X,Y,Z)]
        corner_flags=[]
        for corner in range(8):
            frames,failed=_frames(boundary,corner)
            flag=tuple(span(frames[k]) for k in ("X","Y","Z"))
            check("small_flag_corner_guard_"+name+"_"+str(corner),feasible(*flag)==(not failed))
            if not failed:corner_flags.append(flag)
        check("small_flag_feasibility_"+name,bool(all_flags)==bool(corner_flags))
        minima=[]
        for index,tariff in enumerate(tariffs):
            all_min=min((sum(tariff[r] for r in ranks(*f)) for f in all_flags),default=None)
            corner_min=min((sum(tariff[r] for r in ranks(*f)) for f in corner_flags),default=None)
            check("small_flag_minimum_"+name+"_"+str(index),all_min==corner_min)
            minima.append(None if all_min is None else str(all_min))
        reports.append(dict(fixture=name,exhaustive_flags_examined=16**3,
                            feasible_flags=len(all_flags),feasible_corner_labels=len(corner_flags),
                            exact_rational_tariff_minima=minima,includes_all_successor_terms=True))
    return reports


def controls_task(spec):
    seed = int(spec["seed"]) if isinstance(spec, dict) else int(spec)
    begin = time.process_time()
    T, U = _T(), _util()
    checks = []
    def check(name, value):
        need(value, "carrier-factor control: "+name)
        checks.append(dict(name=name, status="PASS"))
    def rejects(name, fn):
        try:
            fn()
        except (ValueError, AssertionError):
            check(name, True)
        else:
            check(name, False)
    for a, b in itertools.product((-2, -1, Q(-1,2), Q(1,2), 1, 2), repeat=2):
        for kind in ("in", "out"):
            old = ([_gate(3,4,a), _gate(3,5,b)] if kind == "in"
                   else [_gate(4,3,a), _gate(5,3,b)])
            for carrier in (0,1):
                fan = _fan(old, (), carrier)
                check(f"recognizer_{kind}_{carrier}_{a}_{b}", fan is not None and fan["coefficient_admissible"])
                new = _replacement(dict(chain=fan), dict(X=(),Y=(),Z=()))
                for dual in (False,True):
                    name = f"{kind}_{carrier}_{a}_{b}_{dual}"
                    expected = T._sequential_matrix(old, dual)
                    check("identity_"+name, expected == T._sequential_matrix(new, dual))
                    wrong = deepcopy(new); wrong[-1][3] *= -1
                    check("wrong_undo_sign_"+name, expected != T._sequential_matrix(wrong, dual))
                    check("omitted_undo_"+name, expected != T._sequential_matrix(new[:-1], dual))
                    wrong = deepcopy(new); wrong[0][3] *= 2
                    check("wrong_ratio_"+name, expected != T._sequential_matrix(wrong, dual))
    check("non_dyadic_ratio", not _fan([_gate(3,4,Q(3,2)),_gate(3,5,1)])["coefficient_admissible"])
    check("repeated_registers", _fan([_gate(3,4,1),_gate(3,4,2)]) is None)
    check("centre_exclusion", _fan([_gate(3,4,1),_gate(3,5,1)],{4}) is None)
    check("zero_coefficient", _fan([_gate(3,4,0),_gate(3,5,1)]) is None)
    check("nondyadic_original", _fan([_gate(3,4,Q(1,3)),_gate(3,5,1)]) is None)
    check("exact_eight_labels", len(CORNERS)==len(set(CORNERS))==8)
    fixtures=[]
    for kind in ("in","out"):
        for carrier in (0,1):
            old = ([_gate(3,4,1,[1]),_gate(3,5,1,[1])] if kind=="in"
                   else [_gate(4,3,1,[1]),_gate(5,3,1,[1])])
            fan = _fan(old,(),carrier)
            boundary={n:dict(register=fan[n],entry=([1] if n=="i" else []),
                         exit=([1] if n=="i" else [2,1]),equality_exit=False) for n in ("i","j","k")}
            before=U._local_bill(old,boundary)
            check(f"positive_old_{kind}_{carrier}",before["profile"]=={1:4})
            rows=[]
            for corner in range(8):
                frames,failed=_frames(boundary,corner)
                check(f"positive_feasible_{kind}_{carrier}_{corner}",not failed)
                after=U._local_bill(_replacement(dict(chain=fan),frames),boundary)
                delta=Counter(after["profile"]);delta.subtract(before["profile"]);delta=_profile(delta)
                check(f"positive_mass_{kind}_{carrier}_{corner}",_mass(delta)==0)
                rows.append(dict(corner=corner,profile=after["profile"],moment_delta=_moment(delta)))
            check(f"strict_positive_{kind}_{carrier}",any(x["profile"]=={1:2,2:1} and Q(x["moment_delta"]["upper"])<0 for x in rows))
            equality={n:dict(register=fan[n],entry=[],exit=[1],equality_exit=(n=="i")) for n in ("i","j","k")}
            _,bad=_frames(equality,0)
            check(f"equality_not_inclusion_{kind}_{carrier}",any(x["predicate"]=="exit_equality" for x in bad) and not any(x["predicate"] in ("exit_inclusion","frame_inclusion") for x in bad))
            impossible=deepcopy(boundary);impossible["j"]["exit"]=[]
            check(f"infeasible_exit_{kind}_{carrier}",bool(_frames(impossible,0)[1]))
            neutral={n:dict(register=fan[n],entry=[1],exit=[1],equality_exit=False) for n in ("i","j","k")}
            frames,failed=_frames(neutral,0)
            check(f"neutral_{kind}_{carrier}",not failed and U._local_bill(_replacement(dict(chain=fan),frames),neutral)["profile"]=={})
            omitted=Counter(before["profile"]);omitted[1]-=1
            check(f"omitted_successor_mass_{kind}_{carrier}",_mass(omitted)!=before["rank_mass"])
            fixtures.append(dict(kind=kind,carrier=carrier,corners=rows))
    g1,g2=_gate(3,4,1),_gate(3,5,1)
    fake=dict(A=[g1,_gate(8,9,1),g2],B=[],restore=[],warps=[],centers=[],prelude_events=0)
    state=dict(raw=fake,centres=set(),semantic_sha256=digest(fake))
    address=["A",0,2,"in",0,0]
    good=_candidate(state,"base",address)
    check("disjoint_exposure",good is not None)
    for dual in (False, True):
        local = _replacement(dict(chain=_fan([g1,g2])),dict(X=(),Y=(),Z=()))
        scale = ["scale",8,-3,2,[]]
        check("disjoint_scale_full_oracle_"+str(dual),
              _window_matrix([g1,scale,g2],dual)==_window_matrix(local+[scale],dual))
    hidden=deepcopy(fake);hidden["A"][1]=["warp",8,[],[],[]]
    check("literal_hidden_warp",_candidate(dict(raw=hidden,semantic_sha256=digest(hidden)),"base",address) is None)
    bad=deepcopy(good);bad["parent_semantic_sha256"]="0"*64
    rejects("stale_source",lambda:_resolve(state,"base",bad))
    bad=deepcopy(good);bad["interval_sha256"]="0"*64
    rejects("stale_preimage",lambda:_resolve(state,"base",bad))
    touched=deepcopy(fake);touched["A"][1]=_gate(8,4,1)
    check("intervening_contact",_candidate(dict(raw=touched,semantic_sha256=digest(touched)),"base",address) is None)
    prelude=deepcopy(fake);prelude["prelude_events"]=1
    check("prelude_barrier",_candidate(dict(raw=prelude,semantic_sha256=digest(prelude)),"base",address) is None)
    warp=dict(A=[],B=[g1,g2],restore=[],warps=[[1,4,[],[],[]]],centers=[],prelude_events=0)
    check("all_B_warp_barriers",_candidate(dict(raw=warp,semantic_sha256=digest(warp)),"base",["B",0,1,"in",0,0]) is None)
    split=dict(A=[g1],B=[g2],restore=[],warps=[],centers=[],prelude_events=0)
    check("section_crossing",_candidate(dict(raw=split,semantic_sha256=digest(split)),"base",["A",0,1,"in",0,0]) is None)
    restored=deepcopy(fake);restored["restore"]=[g1,g2]
    check("restore_not_scientific_domain",_candidate(dict(raw=restored,semantic_sha256=digest(restored)),"base",["restore",0,1,"in",0,0]) is None)
    exhaustive_flags=_small_flag_controls(check)
    source_fixtures=[]
    for provider in sorted(_FIXTURES):
        state=_FIXTURES[provider]
        edits=_DECLARATION["edits"][provider]
        need(len(edits)==1,"one declared R1 source positive fixture")
        declared=edits[0];sec=declared["section"];p=int(declared["start"]);q=int(declared["stop"])-1
        check("R1_old_preimage_"+provider,state["raw"][sec][p:q+1]==declared["old"] and q==p+1)
        matched=[]
        for carrier in (0,1):
            for corner in range(8):
                candidate=_candidate(state,provider,[sec,p,q,"in",carrier,corner],allow_restore=True)
                if candidate is None:continue
                row=_screen(state,candidate,detailed=True)
                if row["profile_delta"] is not None and row["proof"]["new_gates"]==declared["new"]:
                    matched.append((candidate,row))
        check("R1_declared_corner_"+provider,bool(matched))
        candidate,row=matched[0]
        built,canonical=_materialize(state,candidate,row)
        target=_WORDS[provider]
        check("R1_paid_delta_"+provider,row["profile_delta"]=={1:-2,2:1})
        check("R1_strict_price_"+provider,Q(row["moment_delta"]["upper"])<0)
        check("R1_exact_scalar_sections_"+provider,all(built[s]==target["raw"][s] for s in ("A","B","restore")))
        check("R1_exact_cleanup_"+provider,built["cleanup"]==target["raw"]["cleanup"])
        check("R1_complete_profile_"+provider,canonical.paid==target["canonical"].paid)
        check("R1_unchanged_interfaces_"+provider,_T()._boundary_signature(built)==target["boundaries"])
        check("R1_stale_cleanup_rejected_"+provider,state["raw"]["cleanup"]!=built["cleanup"])
        bad=deepcopy(built);rank=next(iter(bad["report"]["local_profile"]));bad["report"]["local_profile"][rank]-=1
        rejects("R1_missing_paid_child_"+provider,lambda:_W().WordData(bad,state["attribution"]))
        wrong=deepcopy(declared["new"]);wrong[-1][3]*=-1
        check("R1_wrong_undo_"+provider,T._sequential_matrix(declared["old"])!=T._sequential_matrix(wrong))
        source_fixtures.append(dict(provider=provider,candidate_id=candidate["candidate_id"],matching_corner_labels=len(matched),
            local_profile=canonical.paid,profile_delta=row["profile_delta"],moment_delta=row["moment_delta"],
            source_pin=state["source_pin"],source_attribution=state["attribution"],
            declared_source_pin=target["source_pin"],declared_source_attribution=target["attribution"],
            scalar_sections_cleanup_and_profile_equal=True))
    return dict(status="PASS",seed=seed,checks=checks,fixtures=fixtures,exhaustive_small_flag_controls=exhaustive_flags,source_positive_fixtures=source_fixtures,
        source_attribution={p:s["attribution"] for p,s in _WORDS.items()},
        no_full_dirty_native_claim=True,cpu_seconds=time.process_time()-begin)
