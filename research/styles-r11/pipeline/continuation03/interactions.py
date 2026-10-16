"""G4 joint contractions of the frozen G3 census; no work runs on import.

The changed premise is collective frame pricing, not addition of single costs.
All source attribution and the modern native/admission boundary remain intact.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction as Q
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
RR = HERE.parent.parent
G3_SHA = "14bd46dd6be68f9e2337a6359ebe2f79ae61423a7306932b1a2a2c7cd98207dc"
PREREG_SHA = "486b75d92edc4f47c595f83c75af1c48dcbb7d6182e0ad86253b8184c5006175"
G = None
_SINGLES = {}
_SOURCE = {}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def _read_ref(ref):
    path = (RR / ref["path"]).resolve()
    need(path.is_relative_to(RR), "G4 input confinement")
    data = path.read_bytes()
    need(hashlib.sha256(data).hexdigest() == ref["sha256"], "G4 input source pin")
    return json.loads(gzip.decompress(data) if path.name.endswith(".gz") else data)


def prepare(records):
    global G, _SOURCE
    need(G is None, "G4 prepare once in parent")
    reg_path = RR / "results/CONTINUATION-03/G4/PREREGISTRATION.json"
    raw = reg_path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PREREG_SHA, "frozen G4 preregistration")
    reg = json.loads(raw)
    path = HERE / "triangles.py"
    need(hashlib.sha256(path.read_bytes()).hexdigest() == G3_SHA, "immutable G3 source")
    spec = importlib.util.spec_from_file_location("styles_g4_frozen_g3", path)
    G = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = G
    spec.loader.exec_module(G)
    prepared = G.prepare(records)
    run = _read_ref(reg["inputs"]["g3_run"])
    need(run["status"] == "NULL" and run["confirmed"], "confirmed original G3 disposition")
    grouped = {}
    for i in range(4):
        item = _read_ref(reg["inputs"]["g3_census_"+str(i)])
        need(item["status"] == "OK", "saved G3 census completed")
        row = item["result"]
        need(row["status"] == "PASS" and row["complete"], "saved exhaustive G3 census")
        grouped.setdefault(row["provider"], []).append(row)
    for provider in ("base", "extra"):
        one, two = grouped[provider]
        need({one["seed"], two["seed"]} == {14051, 33073}, "both frozen G3 seeds")
        need(one["candidates"] == two["candidates"] and one["counts"] == two["counts"],
             "saved G3 census exact confirmation")
        need(one["parent_semantic_sha256"] == G._WORDS[provider]["semantic_sha256"],
             "G3 census belongs to unchanged PR2957 word")
        need(len(one["candidates"]) == 16, "registered sixteen-member source domain")
        _SINGLES[provider] = one["candidates"]
    _SOURCE = {k: deepcopy(v) for k, v in reg["inputs"].items() if k.startswith("g3_")}
    return dict(status="PASS", original_prepare=prepared, g3_inputs=_SOURCE,
                counts={p: len(v) for p, v in _SINGLES.items()},
                scope=reg["source_attribution"]["fresh_comparison"])


def _support(c):
    return {c["triangle"][k] for k in ("i", "j", "k")}


def _compatible(a, b):
    if a["candidate_id"] == b["candidate_id"] or _support(a) & _support(b):
        return False
    return (a["section"] != b["section"] or
            a["positions"][-1] < b["positions"][0] or
            b["positions"][-1] < a["positions"][0])


def _batch(provider, members, kind):
    singles = _SINGLES[provider]
    members = list(members)
    core = dict(provider=provider, kind=kind, member_indices=members,
                member_ids=[singles[i]["candidate_id"] for i in members])
    return dict(**core, candidate_id=G.digest(core),
                parent_semantic_sha256=G._WORDS[provider]["semantic_sha256"])


def census_task(spec):
    provider, seed = spec["provider"], int(spec["seed"])
    singles = _SINGLES[provider]
    candidates, rejected = [], 0
    for i, j in itertools.combinations(range(len(singles)), 2):
        if _compatible(singles[i], singles[j]):
            candidates.append(_batch(provider, [i, j], "pair"))
        else:
            rejected += 1
    maximal = []
    for i, c in enumerate(singles):
        if all(_compatible(c, singles[j]) for j in maximal):
            maximal.append(i)
    if len(maximal) > 2:
        candidates.append(_batch(provider, maximal, "maximal_batch"))
    need(len({c["candidate_id"] for c in candidates}) == len(candidates), "deduplicated G4 batches")
    return dict(status="PASS", provider=provider, seed=seed, complete=True,
        candidates=candidates, counts=dict(source_singles=len(singles),
        unordered_pairs=len(singles)*(len(singles)-1)//2, rejected_pairs=rejected,
        eligible_pairs=len(candidates)-int(len(maximal)>2), maximal_batch_size=len(maximal),
        exposed_candidates=len(candidates)),
        candidate_set_sha256=G.digest(candidates), g3_inputs=deepcopy(_SOURCE),
        source_attribution=deepcopy(G._WORDS[provider]["attribution"]))


def _validated_members(candidate):
    provider = candidate["provider"]
    indices = candidate["member_indices"]
    need(len(indices) >= 2 and indices == sorted(set(indices)), "unique canonical member indices")
    need(all(type(i) is int and 0 <= i < len(_SINGLES[provider]) for i in indices), "member index domain")
    need(candidate == _batch(provider, indices, candidate["kind"]), "stale joint source preimage")
    need(candidate["kind"] in ("pair", "maximal_batch"), "registered batch kind")
    if candidate["kind"] == "pair":
        need(len(indices) == 2, "pair cardinality")
    else:
        maximum = []
        for i, c in enumerate(_SINGLES[provider]):
            if all(_compatible(c, _SINGLES[provider][j]) for j in maximum):
                maximum.append(i)
        need(indices == maximum and len(indices) > 2, "canonical maximal batch")
    members = [_SINGLES[provider][i] for i in indices]
    need(all(_compatible(a, b) for a, b in itertools.combinations(members, 2)),
         "overlapping intervals or selected register supports")
    return members


def _construct_joint(candidate):
    provider = candidate["provider"]
    state = G._WORDS[provider]
    members = _validated_members(candidate)
    proofs = []
    for member in members:
        _discard, proof = G._construct(state, member)
        proofs.append(proof)

    def splice(order):
        raw = deepcopy(state["raw"])
        ids = {sec: list(range(len(raw[sec]))) for sec in G.SECTIONS}
        for member in order:
            section, tri, exp = member["section"], member["triangle"], member["exposure"]
            first, last = member["positions"][0], member["positions"][-1]
            lo, hi = ids[section].index(first), ids[section].index(last)+1
            need(ids[section][lo:hi] == list(range(first, last+1)), "original interval still untouched")
            kept = [tri["B"], tri["A"]] if tri["orientation"] == "AB_plus" else [tri["A"], tri["B"]]
            replacement = exp["before"] + kept + exp["after"]
            ids[section][lo:hi] = replacement
            raw[section][lo:hi] = [deepcopy(state["raw"][section][i]) for i in replacement]
        removed = [c["triangle"]["C"] for c in members if c["section"] == "B"]
        raw["warps"] = [[r[0]-sum(i < r[0] for i in removed)] + deepcopy(r[1:])
                        for r in state["raw"]["warps"]]
        return raw

    descending = sorted(members, key=lambda c: (G.SECTIONS.index(c["section"]), c["positions"][0]), reverse=True)
    raw = splice(descending)
    reverse = splice(list(reversed(descending)))
    need(raw == reverse, "joint construction differs by application order")
    need(G._boundary_signature(raw) == state["boundaries"], "joint fixed boundary ABI")
    return raw, dict(status="PASS", member_count=len(members),
        pairwise_disjoint_original_intervals=True, pairwise_disjoint_selected_registers=True,
        ascending_descending_same_literal_word=True, individual_scalar_proofs=proofs,
        removed_scalar_gates=len(members), private_buffers=82, physical_families=66804)


def price_task(spec):
    begin = time.process_time()
    provider, seed, candidate = spec["provider"], int(spec["seed"]), spec["candidate"]
    need(candidate["provider"] == provider, "joint provider binding")
    state = G._WORDS[provider]
    result = dict(provider=provider, seed=seed, candidate_id=candidate["candidate_id"],
        candidate=deepcopy(candidate), local_profile=None, width_inventory=None,
        moment_delta=None, word=None, word_artifact=None, optimizer=None, guards={},
        source_attribution=deepcopy(state["attribution"]), source_pin=deepcopy(state["source_pin"]),
        scope="Joint registered surrogate output only; PR2957 is superseded, no frontier/native/kappa claim")
    edited, result["guards"] = _construct_joint(candidate)
    W = G._module("wordio")
    F, _ = W.toolkit()
    _, _, bp = W.borrow_modules()
    try:
        need(0 < int(spec.get("solver_timeout", 300)) <= 300, "pool task timeout")
        inline, meta = bp.build_problem(edited)
        graph = bp.BorrowGraph(inline, meta["eq_end"], check_literal=False,
                               tail_mutable=True, cut_equality=True)
        priced = F.optimal_frames(inline, G._COSTS, graph=graph,
                                 check_literal=False, interval=True)
    except F.Infeasible as error:
        result.update(status="REJECTED_GUARD", guard_failure=str(error), cpu_seconds=time.process_time()-begin)
        return result
    except (TimeoutError, ValueError) as error:
        if not isinstance(error, TimeoutError) and "domain too large" not in str(error):
            raise
        result.update(status="EXPLORATORY", unresolved=str(error), cpu_seconds=time.process_time()-begin)
        return result
    result["optimizer"] = G._json({k: priced[k] for k in ("certified", "cost", "profile", "parts", "interval")})
    built = G._materialize(edited, graph, meta, priced["assign"])
    word = W.WordData(built, state["attribution"])
    old = state["canonical"]
    need(word.helpers == old.helpers and word.start == old.start and word.end == old.end,
         "joint helper/start/end invariant")
    need(G._widths(word) == state["widths"] and G._boundary_signature(built) == state["boundaries"],
         "joint ordered width and ABI invariant")
    npre = built.get("prelude_events", 0)
    if built["A"][:npre] != state["raw"]["A"][:npre]:
        result.update(status="EXPLORATORY", unresolved="optimizer changed frozen prelude", cpu_seconds=time.process_time()-begin)
        return result
    need(G._mass(word.paid) == G._mass(old.paid), "joint complete paid rank mass")
    moment = G._moment_delta(word.paid, old.paid)
    ref = G._write_word(built, spec["output_dir"], candidate["candidate_id"])
    result.update(local_profile=word.paid, width_inventory=dict(Counter(G._widths(word))),
        ordered_widths=G._widths(word), moment_delta=moment, word=ref, word_artifact=ref,
        cleanup_sha256=G.digest(built["cleanup"]), compensation_sha256=G.digest(built["compensation"]),
        cpu_seconds=time.process_time()-begin,
        mixed_cost_interpretation="All saved single deltas are zero; joint delta is the measured mixed effect, never a sum of predictions")
    if not priced["certified"]:
        result.update(status="EXPLORATORY", unresolved="uncertified integer-surrogate optimization")
    elif Q(moment["upper"]) < 0:
        result["status"] = "PASS_CANDIDATE"
    elif Q(moment["lower"]) >= 0 or moment["exact_profile_identity"]:
        result["status"] = "NO_GAIN"
    else:
        result.update(status="EXPLORATORY", unresolved="actual moment interval straddles zero")
    return result


def controls_task(seed):
    seed = int(seed.get("seed")) if isinstance(seed, dict) else int(seed)
    frozen = G.controls_task(seed)
    checks = []
    for provider in ("base", "extra"):
        candidates = census_task(dict(provider=provider, seed=seed))["candidates"]
        need(candidates, "registered joint control requires eligible pair")
        pair = candidates[0]
        _raw, proof = _construct_joint(pair)
        checks.append(dict(provider=provider, name="opposite_application_orders", status="PASS", proof=proof))
        bad = deepcopy(pair); bad["member_indices"][1] = bad["member_indices"][0]
        try:
            _validated_members(bad)
        except ValueError:
            pass
        else:
            raise ValueError("duplicate/overlap control was accepted")
        checks.append(dict(provider=provider, name="duplicate_overlapping_member", status="PASS"))
        member, other = (_SINGLES[provider][i] for i in pair["member_indices"])
        # Mutate metadata from a known eligible pair. Different IDs and
        # disjoint supports force the first rejection through interval overlap.
        overlap = deepcopy(other)
        overlap["section"] = member["section"]
        overlap["positions"] = deepcopy(member["positions"])
        need(member["candidate_id"] != overlap["candidate_id"] and
             not (_support(member) & _support(overlap)), "isolated interval control premise")
        need(not _compatible(member, overlap), "interval overlap must reject")
        checks.append(dict(provider=provider, name="distinct_ids_interval_overlap", status="PASS"))
        shared = deepcopy(other)
        shared["triangle"]["i"] = member["triangle"]["i"]
        need(member["candidate_id"] != shared["candidate_id"] and
             (member["section"] != shared["section"] or
              member["positions"][-1] < shared["positions"][0] or
              shared["positions"][-1] < member["positions"][0]), "isolated support control premise")
        need(not _compatible(member, shared), "shared register support must reject")
        checks.append(dict(provider=provider, name="disjoint_intervals_shared_support", status="PASS"))
        bad = deepcopy(pair); bad["parent_semantic_sha256"] = "0"*64
        try:
            _construct_joint(bad)
        except ValueError:
            pass
        else:
            raise ValueError("wrong source preimage was accepted")
        checks.append(dict(provider=provider, name="wrong_source_preimage", status="PASS"))
    return dict(status="PASS", seed=seed, checks=checks, frozen_g3_controls=frozen,
                g3_source_sha256=G3_SHA, g3_inputs=deepcopy(_SOURCE))

