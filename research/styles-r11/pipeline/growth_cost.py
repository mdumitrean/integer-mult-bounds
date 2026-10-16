"""Optional L6-COST-N6 calibration on held local-profile result rows.

Only JSON data is loaded.  The source producer overwrites hyperplane word
filenames, so the immutable result-file/key pair, never the referenced word,
identifies a row.  The root below is an explicitly conditional LOCAL block
sensitivity.  It is not a global construction root or a candidate price.
No work is performed on import, and this module never starts a pool.
"""
from __future__ import annotations

from decimal import Decimal as D, localcontext
import hashlib
import itertools
import random
import statistics
import time

import growth as G

DATA = G.ROOT / "research/t74-r10-hosting-leads/J-dim1/out/eh"
PRIMARY = ("ALL-b-0.json", "ALL-b-1.json", "ALL-b-2.json", "ALL-b-3.json", "HYP-b.json")
COMPANIONS = ("EH-b.json", "EH-e.json", "HYP-e.json")
EXPECTED_COUNTS = dict(zip(PRIMARY + COMPANIONS, (23, 23, 22, 22, 62, 1, 1, 31)))
_ROWS = None
_MANIFEST = None


def manifest():
    """Return source hashes, schema keys and counts, without metric values."""
    rows = []
    for filename in PRIMARY + COMPANIONS:
        path = DATA / filename
        raw = path.read_bytes()
        data = G.read_json(path)
        rows.append(dict(path=str(path.relative_to(G.ROOT)), sha256=hashlib.sha256(raw).hexdigest(),
                         records=len(data), record_fields=sorted({key for row in data.values() for key in row})))
    producer = G.ROOT / "research/t74-r10-hosting-leads/J-dim1/code/ehost_build2.py"
    return dict(files=rows, producer_source=dict(path=str(producer.relative_to(G.ROOT)),
        sha256=hashlib.sha256(producer.read_bytes()).hexdigest(), handling="read as text only, never imported"),
        primary_enrollment="all 152 rows in ALL-b-0..3 and HYP-b, with no outcome filtering",
        companions="33 rows in EH-b, EH-e and HYP-e; separate descriptive stratum",
        word_binding="hyperplane records overwrite their word paths; no row-to-word identity is assumed")


def prepare():
    """Parent-owned loading before pool launch; no metrics are computed here."""
    global _ROWS, _MANIFEST
    _MANIFEST = manifest()
    _ROWS = []
    for filename in PRIMARY + COMPANIONS:
        data = G.read_json(DATA / filename)
        if len(data) != EXPECTED_COUNTS[filename]:
            raise ValueError(f"N6 preregistered enrollment count changed: {filename}")
        for key, row in sorted(data.items()):
            _ROWS.append(dict(id=f"{filename}:{key}", filename=filename, record_key=key,
                             stratum="primary" if filename in PRIMARY else "companion", data=row))
    return dict(records=len(_ROWS), primary=sum(r["stratum"] == "primary" for r in _ROWS),
                companions=sum(r["stratum"] == "companion" for r in _ROWS), manifest=_MANIFEST)


def _sign(value, tolerance=D("1e-60")):
    return 0 if abs(value) <= tolerance else (1 if value > 0 else -1)


def _float_summary(values):
    if not values:
        return dict(n=0)
    values = sorted(values)
    return dict(n=len(values), min=min(values), median=statistics.median(values),
                mean=statistics.fmean(values), p99=values[min(len(values)-1, (99*len(values))//100)],
                max=max(values))


def _assess(rows, algorithm):
    mismatches, errors = [], []
    for row in rows:
        truth, guess = D(row["conditional_root_delta"]), D(row[algorithm])
        if _sign(truth) != _sign(guess):
            mismatches.append(row["id"])
        if _sign(truth):
            errors.append((abs((guess-truth)/truth), row["id"]))
    pair_disagreements = []
    for left, right in itertools.combinations(rows, 2):
        exact_order = _sign(D(left["conditional_root_delta"]) - D(right["conditional_root_delta"]))
        score_order = _sign(D(left[algorithm]) - D(right[algorithm]))
        if exact_order != score_order:
            pair_disagreements.append([left["id"], right["id"]])
    errors.sort(reverse=True)
    return dict(rows=len(rows), sign_disagreement_count=len(mismatches), sign_disagreement_ids=mismatches,
        pairwise_comparisons=len(rows)*(len(rows)-1)//2,
        pairwise_order_disagreement_count=len(pair_disagreements), pairwise_disagreements=pair_disagreements,
        relative_error=_float_summary([float(value) for value, _ in errors]),
        relative_error_above_2pct=[name for error, name in errors if error > D(".02")],
        worst_error_ids=[name for _, name in errors[:5]])


def calibrate(seed, timing_repeats=1024):
    """Fixed rank dots versus 90-digit roots on exact before/after LOCAL rows.

    Let k0 be the held #2802 complete-profile moment root. For each result row,
    p_before = p_after - delta_local is exact from the held producer record.
    We solve M_after(k*) = M_before(k0), M_p(k)=sum p_r(r/73)**(1-k).
    Thus k*−k0 is a conditional block sensitivity, with no invented idle fill.
    """
    if _ROWS is None:
        raise RuntimeError("growth_cost.prepare must load held JSON data in the parent before launch")
    if timing_repeats != 1024:
        raise ValueError("L6-COST-N6 fixes 1024 dot repetitions per record")
    rng = random.Random(seed)
    rows = list(_ROWS)
    rng.shuffle(rows)
    start = time.process_time_ns()
    k0 = G.root(G._profile_records()["2802"]["profile"])
    with localcontext() as ctx:
        ctx.prec = 90
        log73 = D(73).ln()
        ranks = sorted({int(rank) for item in rows for field in ("profile", "delta_local")
                        for rank in item["data"][field]})
        log_rank = {r:D(r).ln() for r in ranks}
        phi_weight = {r:D(r)*log_rank[r] for r in ranks}
        moment_weight = {r:D(r)/73*(k0*(log73-log_rank[r])).exp() for r in ranks}
        derivative_weight = {r:moment_weight[r]*(log73-log_rank[r]) for r in ranks}
        mass_weight = {r:D(r) for r in ranks}
        phi_numerator_weight = {r:k0*phi_weight[r]/73 for r in ranks}
        corrected_numerator_weight = {r:(k0*phi_weight[r]-(1+k0*log73)*mass_weight[r])/73 for r in ranks}
        setup_ns = time.process_time_ns() - start
        output, timing = [], []
        for item in rows:
            data = item["data"]
            after = G.clean(data["profile"])
            change = G.clean(data["delta_local"])
            before = G.add_profile(after, {r:-c for r,c in change.items()})
            denominator_start = time.process_time_ns()
            derivative = sum(D(c)*derivative_weight[r] for r,c in before.items())
            target = sum(D(c)*moment_weight[r] for r,c in before.items())
            denominator_ns = time.process_time_ns()-denominator_start
            items = tuple((r,D(c)) for r,c in change.items())
            def phi_score():
                return sum(c*phi_numerator_weight[r] for r,c in items)/derivative
            def corrected_phi_score():
                return sum(c*corrected_numerator_weight[r] for r,c in items)/derivative
            def full_moment_score():
                return -sum(c*moment_weight[r] for r,c in items)/derivative
            def exact_root():
                # Bypass profile cache: each recorded root timing is a complete
                # 90-digit, 280-step bisection, even for repeated profiles.
                return G._root_cached.__wrapped__(G.profile_key(after), str(target))
            algorithms = [("phi_estimate",phi_score), ("mass_corrected_phi_estimate",corrected_phi_score),
                          ("full_moment_estimate",full_moment_score), ("conditional_root",exact_root)]
            rng.shuffle(algorithms)
            values, row_times = {}, {}
            for name, function in algorithms:
                repeats = 1 if name == "conditional_root" else timing_repeats
                then = time.process_time_ns()
                for _ in range(repeats):
                    value = function()
                elapsed = time.process_time_ns()-then
                values[name] = value
                row_times[name] = dict(total_cpu_ns=elapsed, repetitions=repeats, per_call_cpu_ns=elapsed/repeats)
            lo, hi = values.pop("conditional_root")
            row = dict(id=item["id"], stratum=item["stratum"], filename=item["filename"], record_key=item["record_key"],
                before_local_profile=before, after_local_profile=after, delta_local=change,
                local_mass_before=G.mass(before), local_mass_after=G.mass(after), delta_local_mass=G.mass(change),
                raw_phi_delta=str(sum(c*phi_weight[r] for r,c in items)),
                local_target_moment=str(target), derivative_before=str(derivative),
                denominator_and_target_setup_cpu_ns=denominator_ns,
                conditional_root_interval={"lo":str(lo), "hi":str(hi)}, conditional_root_delta=str(lo-k0),
                phi_requires_mass_neutrality=G.mass(change)==0,
                recorded_status=data.get("status"), recorded_audit=data.get("audit"),
                recorded_cost_delta=data.get("cost_delta"), recorded_inventory=data.get("inventory"),
                word_path_is_not_variant_identity=True, timing=row_times,
                **{name:str(value) for name,value in values.items()})
            output.append(row)
            timing.append(row_times)
        output.sort(key=lambda row:row["id"])
        assessment = {stratum:{name:_assess([r for r in output if r["stratum"]==stratum],name)
            for name in ("phi_estimate","mass_corrected_phi_estimate","full_moment_estimate")}
            for stratum in ("primary","companion")}
        cpu_summary = {name:_float_summary([r[name]["per_call_cpu_ns"] for r in timing])
                       for name in timing[0]}
        primary = assessment["primary"]["full_moment_estimate"]
        calibration_pass = not primary["sign_disagreement_count"] and not primary["relative_error_above_2pct"]
        return dict(experiment="L6-COST-N6", seed=seed, n_permutations=0,
            status="PASS" if calibration_pass else "NULL",
            decision="primary full-moment linearization signs agree and every nonzero conditional-root delta is within 2%"
                     if calibration_pass else "conditional local calibration fails the registered full-moment criterion",
            reference_kappa=str(k0), setup_cpu_ns=setup_ns, dot_repetitions=timing_repeats,
            root_precision_digits=90, root_iterations=280, root_cache_used=False,
            conditional_root_equation="M_after(k*) = M_before(k0), M_p(k)=sum p_r*(r/73)^(1-k)",
            rows=output, assessment=assessment, timing_cpu_ns_per_call=cpu_summary,
            manifest=_MANIFEST, attribution=G.sources(),
            excluded_from_global_kappa_pricing=True, noncircular_pattern=False,
            limitations=["Only local profiles are held for each near-miss; no global/idle profile is invented.",
                         "Conditional local roots are sensitivity diagnostics, not global construction exponents.",
                         "Hyperplane output word paths were overwritten by the producer and are not individual row witnesses.",
                         "Existing audit labels are retained as source data; this calibration does not re-audit absent variants.",
                         "Phi ignores nonzero local mass change; mass-corrected Phi is a first-order-in-kappa approximation.",
                         "Decimal brackets are numerical, not interval-arithmetic transcendental certificates."])


def task(spec):
    return calibrate(int(spec["seed"]), int(spec.get("timing_repeats",1024)))
