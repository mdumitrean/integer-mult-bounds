#!/usr/bin/env python3
"""Exact growth bookkeeping for the pre-registered r11 experiment families.

Source attribution: the moment equation and initial implementation are Lane B's
``planning/B-lsys-growth/parikh_kappa.py`` (Marius-Paul Dumitrean); canonical
climbs are supplied by Lane A's ``wordio`` implementation.  Pinned words and
stage JSON are data.  This module never imports them.  It has no internal pool:
the coordinator must call ``task`` through ``pipeline.pool`` after registration.

An algebraic profile identity is deliberately distinct from a guarded word
derivation.  Missing source profiles or unaudited production guards cannot pass
L-6/L-7 by being filled with plausible assumptions.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, localcontext
from functools import lru_cache
import gzip
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import statistics
import time

D = Decimal
HERE = Path(__file__).resolve().parent
STYLES = HERE.parent
ROOT = HERE.parents[2]
PKG = ROOT / "research/t74-joint-twelve-retired7"
PINS = STYLES / "data/words/PINS.json"
PROFILES = STYLES / "data/PROFILES.json"
DIMENSION, REFERENCE_WIRES, CALLS = 73, 66304, 666
LINEAGE = ("2679", "2745", "2751", "2766", "retired5", "2802")


def read_json(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def clean(profile):
    return {int(r): int(c) for r, c in sorted(profile.items(), key=lambda x: int(x[0])) if c}


def delta(before, after):
    return {r: after.get(r, 0) - before.get(r, 0)
            for r in sorted(set(before) | set(after)) if after.get(r, 0) != before.get(r, 0)}


def mass(profile):
    return sum(int(r) * c for r, c in profile.items())


def add_profile(profile, change):
    result = dict(profile)
    for r, count in change.items():
        result[r] = result.get(r, 0) + count
    if any(c < 0 for c in result.values()):
        raise ValueError("negative profile multiplicity")
    return {r: c for r, c in sorted(result.items()) if c}


def profile_key(profile):
    return tuple(sorted((int(r), str(c)) for r, c in profile.items() if c))


@lru_cache(maxsize=8192)
def _root_cached(key, wires):
    # Same 90-digit/280-bisection protocol as pipeline/root.py; logarithms are
    # computed once, rather than repeated at every evaluation.
    with localcontext() as ctx:
        ctx.prec = 90
        terms = [(D(c) * D(r) / DIMENSION, (D(DIMENSION) / r).ln()) for r, c in key]
        def moment(k):
            return sum(weight * (k * delay).exp() for weight, delay in terms)
        lo, hi = D("-0.1"), D("0.1")
        target = D(wires)
        if not moment(lo) <= target <= moment(hi):
            raise ValueError("root outside preregistered [-0.1,0.1] bracket")
        for _ in range(280):
            mid = (lo + hi) / 2
            if moment(mid) < target:
                lo = mid
            else:
                hi = mid
        return lo, hi


def root(profile, wires=REFERENCE_WIRES):
    return _root_cached(profile_key(profile), wires)[0]


def root_interval(profile, wires=REFERENCE_WIRES):
    lo, hi = _root_cached(profile_key(profile), wires)
    return {"lo": str(lo), "hi": str(hi), "precision_digits": 90,
            "iterations": 280,
            "scope": "Decimal bisection bracket; not an interval-arithmetic transcendental certificate"}


def phi(profile):
    with localcontext() as ctx:
        ctx.prec = 90
        return sum(D(r) * D(c) * D(r).ln() for r, c in profile.items() if c)


def derivative(profile, k, wires=REFERENCE_WIRES):
    del wires
    with localcontext() as ctx:
        ctx.prec = 90
        return sum(D(c) * D(r) / DIMENSION * (k * (D(DIMENSION) / r).ln()).exp()
                   * (D(DIMENSION) / r).ln() for r, c in profile.items() if c)


def sources(all_words=False):
    out = []
    for key, pin in read_json(PINS)["files"].items():
        if all_words or str(pin.get("pr")) in LINEAGE or key.startswith("retired5-"):
            out.append(dict(path=key, **pin))
    return out


def resolve_word(name, tag="base"):
    names = {
        "2679": f"2679-BORROW-WORD-43{tag}.json.gz",
        "2745": f"2745-BORROW-WORD-43{tag}.json.gz",
        "2766": f"2766-WORD-{tag}.json.gz",
        "retired5": f"retired5-WORD-{tag}.json.gz",
        "2751": f"research/t74-joint-twelve-retired7/inputs/WORD2751-{tag}.json.gz",
        "2802": f"research/t74-joint-twelve-retired7/inputs/WORD-{tag}.json.gz",
    }
    key = names[name]
    path = ROOT / key if "/" in key else STYLES / "data/words" / key
    pin = read_json(PINS)["files"][key]
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin["sha256"]:
        raise ValueError(f"pinned source digest mismatch: {key}")
    return path, dict(path=key, **pin)


def _profile_records():
    records = {}
    for name, entry in read_json(PROFILES)["constructions"].items():
        if "complete_profile" not in entry:
            continue
        profile = clean(entry["complete_profile"])
        calls = 144 if name == "1094" else CALLS
        numerator = mass(profile) - 64 * calls
        if numerator % 72:
            raise ValueError(f"coverage identity not integral for {name}")
        wires = numerator // 72
        if wires != (14336 if name == "1094" else REFERENCE_WIRES):
            raise ValueError(f"unexpected geometry for {name}: {wires}")
        records[name] = dict(profile=profile, calls=calls, wires=wires,
            attribution={k: entry.get(k) for k in ("author", "complete_profile_source", "claim_file", "kappa")},
            source_status="quoted" if "quoted" in entry.get("complete_profile_source", "") else "pinned_profile")
    # These two exact predecessor commits were already reachable in the local
    # object database. Their JSON profiles are copied as data, with the source
    # word hashes tied back to PINS.json; no common-idle reconstruction is used.
    supplemental = HERE / "growth_sources.json"
    if supplemental.exists():
        for name, entry in read_json(supplemental)["constructions"].items():
            profile = clean(entry["complete_profile"])
            if mass(profile) != 72 * entry["wires"] + 64 * entry["calls"]:
                raise ValueError(f"supplemental coverage identity failure: {name}")
            records[name] = dict(profile=profile, calls=entry["calls"], wires=entry["wires"],
                attribution=entry, source_status="pinned_predecessor_git_json_with_word_bindings")
    return records


def exchange_support(profile, size, max_rank=51):
    """Finite exact-L1, mass-neutral two-rank-exchange control distribution.

    Uniform sampling from this set is explicitly not uniform over all neutral
    integer deltas and does not assert that a control is a feasible word edit.
    """
    out = []
    for a in range(1, max_rank + 1):
        for b in range(a + 1, max_rank + 1):
            g = math.gcd(a, b)
            primitive_l1 = (a + b) // g
            if size % primitive_l1:
                continue
            scale = size // primitive_l1
            for sign in (-1, 1):
                move = {a: sign * (b // g) * scale, b: -sign * (a // g) * scale}
                if all(profile.get(r, 0) + c >= 0 for r, c in move.items()):
                    assert mass(move) == 0 and sum(abs(c) for c in move.values()) == size
                    out.append(move)
    if not out:
        raise ValueError(f"no admissible exact-L1 exchanges for L1={size}")
    return out


def _summary(values, real=None, tail="ge"):
    if not values:
        return {"n": 0, "mean": None, "sd": None, "empirical_p": None}
    ordered = sorted(values)
    out = {"n": len(values), "mean": statistics.fmean(values),
           "sd": statistics.pstdev(values), "min": min(values), "max": max(values),
           "q005": ordered[max(0, math.ceil(.005 * len(values)) - 1)],
           "q995": ordered[min(len(values) - 1, math.ceil(.995 * len(values)) - 1)]}
    out["empirical_p"] = ((1 + sum((v >= real if tail == "ge" else v <= real) for v in values))
                          / (1 + len(values))) if real is not None else None
    return out


def audit_law(seed, n_permutations=2000):
    if n_permutations < 2000:
        raise ValueError("L-6 requires at least 2000 controls per supported step")
    records = _profile_records()
    ref = records["2802"]["profile"]
    kref = root(ref)
    with localcontext() as ctx:
        ctx.prec = 90
        lam = kref / (DIMENSION * derivative(ref, kref))
    _root_cached.cache_clear()
    root_cpu = phi_cpu = 0.0
    ordered_profiles = []
    for name, rec in records.items():
        start = time.process_time()
        k = root(rec["profile"], rec["wires"])
        root_cpu += time.process_time() - start
        start = time.process_time()
        raw_phi = phi(rec["profile"])
        concentration = raw_phi * D(REFERENCE_WIRES) / rec["wires"]
        phi_cpu += time.process_time() - start
        ordered_profiles.append(dict(name=name, root=str(k), raw_phi=str(raw_phi), normalized_phi=str(concentration),
            root_bracket=root_interval(rec["profile"], rec["wires"]), rank_mass=mass(rec["profile"]),
            **rec))
    disagreements, raw_disagreements = [], []
    for a, b in itertools.combinations(ordered_profiles, 2):
        kp = D(a["root"]) - D(b["root"])
        pp = D(a["normalized_phi"]) - D(b["normalized_phi"])
        if (kp > 0) != (pp > 0) or (kp < 0) != (pp < 0):
            disagreements.append([a["name"], b["name"]])
        raw_difference = D(a["raw_phi"]) - D(b["raw_phi"])
        if (kp > 0) != (raw_difference > 0) or (kp < 0) != (raw_difference < 0):
            raw_disagreements.append([a["name"], b["name"]])
    rng = random.Random(seed)
    edges = []
    for before, after in zip(LINEAGE, LINEAGE[1:]):
        if before not in records or after not in records:
            edges.append({"before": before, "after": after, "status": "EXPLORATORY",
                "reason": "complete profile absent from pinned inputs; no common-idle reconstruction assumed"})
            continue
        pa, pb = records[before]["profile"], records[after]["profile"]
        change = delta(pa, pb)
        if mass(change):
            raise ValueError("lineage step is not mass neutral")
        exact = root(pb) - root(pa)
        law = lam * phi(change)
        error = abs(law - exact) / abs(exact) if exact else D(0)
        support = exchange_support(pa, sum(abs(v) for v in change.values()))
        control_cache = []
        for move in support:
            gain = root(add_profile(pa, move)) - root(pa)
            estimate = lam * phi(move)
            relerr = abs(estimate - gain) / abs(gain) if gain else D(0)
            control_cache.append((float(gain), float(relerr), (gain > 0) != (estimate > 0)))
        draws = [rng.choice(control_cache) for _ in range(n_permutations)]
        edges.append(dict(before=before, after=after, complete_delta=change,
            exact_dkappa=str(exact), dphi=str(phi(change)), law_dkappa=str(law),
            relative_error=str(error), within_two_percent=error <= D("0.02"),
            status="PASS" if error <= D("0.02") else "NULL",
            null={"protocol": "uniform with replacement from feasible exact-L1 two-rank exchanges on ranks 1..51",
                  "support_size": len(support), "rank_mass": 0,
                  "L1": sum(abs(v) for v in change.values()),
                  "law_relative_error": _summary([row[1] for row in draws], float(error), tail="le"),
                  "exact_gain": _summary([row[0] for row in draws]),
                  "sign_disagreements": sum(row[2] for row in draws),
                  "inferential_scope": "accuracy controls only; not reachable word edits; no pattern claim or FDR discovery"}))
    supported = [e for e in edges if "within_two_percent" in e]
    numerical_pass = bool(supported) and all(e["within_two_percent"] for e in supported) and not disagreements
    unavailable = [e for e in edges if "within_two_percent" not in e]
    status = "NULL" if not numerical_pass else ("EXPLORATORY" if unavailable else "PASS")
    return dict(experiment="L-6", seed=seed, n_permutations=n_permutations, status=status,
        decision="all available complete-profile numeric checks pass; full-lineage bar incomplete" if numerical_pass and unavailable
                 else "numeric criterion passed" if numerical_pass else "pre-registered numeric criterion failed",
        lambda_reference="2802", lambda_value=str(lam), profiles=ordered_profiles, lineage=edges,
        normalized_phi="Phi * 66304 / W; T16 W=14336 and T74 W=66304 from stated coverage geometry",
        pairwise_order_disagreements=disagreements, raw_pairwise_order_disagreements=raw_disagreements,
        timing={"profile_root_cpu_seconds": root_cpu, "profile_phi_cpu_seconds": phi_cpu,
                "scope": "one pass over held profiles with root cache cleared before measurement; control-root cost excluded"},
        pattern_criteria={"non_circular": False, "reason": "Phi is a function of the complete profile; this is bookkeeping, not a pattern"},
        attribution=sources(all_words=True))


def _word_load(path, pin):
    # Imported only here so root-only utilities remain usable independently.
    import wordio
    return wordio.load(path, pin=pin)


def register_ledger(a, b):
    rows = []
    accounted = Counter()
    for reg in sorted(set(a.climbs) | set(b.climbs)):
        ca, cb = a.climbs.get(reg, {}), b.climbs.get(reg, {})
        sa = [j["rank"] for j in ca.get("jumps", [])]
        sb = [j["rank"] for j in cb.get("jumps", [])]
        if sa == sb:
            continue
        change = delta(Counter(sa), Counter(sb))
        accounted.update(change)
        rows.append(dict(register=reg, before=sa, after=sb, delta=change,
                         before_role=ca.get("role", "removed"), after_role=cb.get("role", "removed"),
                         before_width=ca.get("width"), after_width=cb.get("width")))
    accounted = {r: c for r, c in sorted(accounted.items()) if c}
    expected = delta(a.paid, b.paid)
    if accounted != expected:
        raise ValueError(f"per-register deltas fail canonical profile parity: {accounted} != {expected}")
    return rows, accounted


def audit_derivation(seed, n_permutations=2000, audit_guards=True):
    import growth_replay
    records = _profile_records()
    words = {}
    for tag in ("base", "extra"):
        for name in LINEAGE:
            path, pin = resolve_word(name, tag)
            words[name, tag] = _word_load(path, pin)
    edges = []
    for before, after in zip(LINEAGE, LINEAGE[1:]):
        variants = []
        for tag in ("base", "extra"):
            a, b = words[before, tag], words[after, tag]
            rows, local_delta = register_ledger(a, b)
            variants.append(dict(variant=tag, registers=rows, local_delta_per_call=local_delta,
                                 local_mass_delta=mass(local_delta), exact_profile_sum=True))
        full = None
        if before in records and after in records:
            full = delta(records[before]["profile"], records[after]["profile"])
            local = variants[0]["local_delta_per_call"]
            idle = {r: full.get(r, 0) - CALLS * local.get(r, 0) for r in set(full) | set(local)}
            idle = {r: c for r, c in sorted(idle.items()) if c}
        else:
            idle = None
        edges.append(dict(before=before, after=after, variants=variants,
            complete_delta=full, idle_delta=idle,
            idle_status="derived from two pinned complete profiles and canonical local difference" if idle is not None
                        else "unavailable: complete predecessor profile not pinned",
            sum_mass_neutral=mass(full) == 0 if full is not None else None))
    replay = growth_replay.audit(seed=seed, n_permutations=n_permutations) if audit_guards else {
        "status": "EXPLORATORY", "reason": "guarded production replay not requested"}
    all_proven = replay.get("all_lineage_guards_proven", False) and all(e["complete_delta"] is not None for e in edges)
    return dict(experiment="L-7", seed=seed, n_permutations=n_permutations,
        status="PASS" if all_proven else "EXPLORATORY", lineage=edges, guarded_replay=replay,
        decision="guarded decomposition proven" if all_proven else
                 "canonical per-register ledger exact; early compound-production guard validation remains unresolved despite complete held source data",
        attribution=sources(),
        pattern_criteria={"non_circular": False, "reason": "a ledger is bookkeeping; only separately tested guards could become predictions"})


def task(spec):
    """Pool entry point. Caller owns preregistration, limits and RESULT.json."""
    experiment = spec["experiment"]
    if experiment == "L-6":
        return audit_law(int(spec["seed"]), int(spec.get("n_permutations", 2000)))
    if experiment == "L-7":
        return audit_derivation(int(spec["seed"]), int(spec.get("n_permutations", 2000)),
                                bool(spec.get("audit_guards", True)))
    if experiment in {"L-8", "L-9", "L-10", "L-11", "S-3"}:
        import growth_m3
        return growth_m3.task(spec)
    raise ValueError(f"unsupported growth experiment: {experiment}")
