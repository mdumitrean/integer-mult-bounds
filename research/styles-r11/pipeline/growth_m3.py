"""M3 growth experiments. Import/preparation is separate from pool execution.

The bin-pattern relaxation is a classical linear program. Rational lower
bounds for logarithms/exponentials follow the pinned exact_moment.py method
(Tekalign), extended to 32 exponential terms. No claimed construction is
changed or priced by this code.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import itertools
import json
import math
import random
import statistics

import growth as G

_MODELS = {}
_TEMPLATE = None
_OPTIMA = {}
L10_KEYS = (
    "1094-K8S7-FULL-WORD.json.gz", "1672-gauge44-word-566-554.json.gz", "1672-extra-word-566-554.json.gz",
    "2745-BORROW-WORD-43base.json.gz", "2745-BORROW-WORD-43extra.json.gz", "2766-WORD-base.json.gz",
    "research/t74-joint-twelve-retired7/inputs/WORD2751-base.json.gz",
    "research/t74-joint-twelve-retired7/inputs/WORD-base.json.gz",
    "research/t74-joint-twelve-retired7/inputs/WORD-extra.json.gz")


def prepare(fill_names=("2802", "2751", "1672"), optima=None):
    """Call once in the parent before a forked pool; never launch a pool here."""
    import fill
    global _TEMPLATE
    for name in fill_names:
        _MODELS[name] = fill.load_fill(G.ROOT, name)
    if _TEMPLATE is None:
        _TEMPLATE = G.read_json(G.PKG / "inputs/GLOBAL-TEMPLATE.json.gz")
    if optima:
        _OPTIMA.update(optima)
    return {"fills": list(_MODELS), "template_loaded": _TEMPLATE is not None,
            "optima": list(_OPTIMA)}


def _model(name):
    if name not in _MODELS:
        raise RuntimeError("growth_m3.prepare must load large fill objects in the parent before launch")
    return _MODELS[name]


@lru_cache(maxsize=None)
def _log_bounds(rank):
    x = F(73, rank)
    power = 0
    while x >= 2:
        x /= 2
        power += 1
    def reduced(y):
        z = (y - 1) / (y + 1)
        lo = sum((2 * z ** (2 * j + 1) / (2 * j + 1) for j in range(40)), F(0))
        return lo, lo + 2 * z ** 81 / (81 * (1 - z*z))
    a, b = reduced(x)
    c, d = reduced(F(2))
    return a + power * c, b + power * d


def _exp_bounds(x):
    if not 0 <= x < 1:
        raise ValueError("rational exponential protocol requires argument in [0,1)")
    term = lo = F(1)
    for n in range(1, 33):
        term *= x / n
        lo += term
    return lo, lo + term * x / 33 / (1 - x / 34)


def _floor_grid(value, digits=30):
    scale = 10 ** digits
    return F(value.numerator * scale // value.denominator, scale)


def _ceil_grid(value, digits=30):
    return -_floor_grid(-value, digits)


@lru_cache(maxsize=16384)
def rational_cost(rank, exponent):
    if rank == 0:
        return F(0), F(0)
    k = F(exponent)
    lo, hi = _log_bounds(rank)
    a, _ = _exp_bounds(k * lo)
    _, b = _exp_bounds(k * hi)
    return _floor_grid(F(rank, 73) * a), _ceil_grid(F(rank, 73) * b)


def _float_cost(rank, exponent):
    return (rank / 73) ** (1 - float(exponent)) if rank else 0.0


def _decimal_fraction(value):
    return D(value.numerator) / value.denominator


def _round_upper(value, digits=12):
    return (D(str(value)) * 10**digits).to_integral_value(rounding=ROUND_CEILING) / 10**digits


def _rational_root_bracket(profile, proposal):
    """Certify a conservative comparison interval around a numeric proposal."""
    low = (D(str(proposal))*10**12).to_integral_value(rounding=ROUND_FLOOR)/10**12-D("1e-12")
    high = _round_upper(proposal)+D("1e-12")
    record = None
    for attempt in range(7):
        lower_moment_upper = sum(F(c)*rational_cost(r,str(low))[1] for r,c in profile.items())
        upper_moment_lower = sum(F(c)*rational_cost(r,str(high))[0] for r,c in profile.items())
        lower_valid = lower_moment_upper < G.REFERENCE_WIRES
        upper_valid = upper_moment_lower > G.REFERENCE_WIRES
        record = dict(lo=str(low),hi=str(high),
            moment_upper_at_lo=str(lower_moment_upper),moment_lower_at_hi=str(upper_moment_lower),
            lower_certified=lower_valid,upper_certified=upper_valid,
            proof="exact rational cost intervals; positive-profile moment strictly increases with kappa")
        if lower_valid and upper_valid:
            break
        step = D("1e-12")*10**(attempt+1)
        low -= step
        high += step
    return record


def patterns(capacity, widths):
    """Enumerate every unordered feasible multiset, including the empty bin."""
    def rec(i, remain, counts):
        if i == len(widths):
            yield tuple(counts), remain
            return
        w = widths[i]
        for n in range(remain // w + 1):
            yield from rec(i+1, remain - n*w, counts+[n])
    return list(rec(0, capacity, []))


def _inventory(model, use_overlay=False):
    bin_counts = Counter(cap for cap, start, stop in model.win.values())
    bin_counts = {cap: count * model.ports for cap, count in sorted(bin_counts.items())}
    inventory = Counter(w for row in model.widths for w in row)
    local = Counter()
    chosen_profiles = model.overlay_local_profiles if use_overlay and model.overlay_local_profiles is not None else model.local_profiles
    for profile in chosen_profiles:
        local.update(profile)
    return bin_counts, dict(sorted(inventory.items())), dict(local)


def pattern_ceiling(model, word=None, use_overlay=False, time_limit=300):
    """One LP solve plus an independently checked rational dual root ceiling.

    For every capacity c and feasible multiset p, x[c,p]>=0.  Equalities fix
    bin counts per capacity and role counts per width.  This drops time and
    family constraints.  A dual value above W at exponent k rules out any fill
    in this class with root >= k.
    """
    import numpy as np
    from scipy.optimize import linprog
    del word
    if not 0 < time_limit <= 600:
        raise ValueError("pattern LP time limit must be in (0,600] seconds")
    bins, demand, local = _inventory(model, use_overlay)
    caps, widths = tuple(bins), tuple(demand)
    columns = []
    for cap in caps:
        for counts, remainder in patterns(cap, widths):
            column = [int(c == cap) for c in caps] + list(counts)
            columns.append((cap, counts, remainder, column))
    A = np.asarray([col[3] for col in columns], dtype=float).T
    b = np.asarray([bins[c] for c in caps] + [demand[w] for w in widths], dtype=float)
    reference_profile = dict(model.expected_profile)
    overlay_active = use_overlay and model.overlay_local_profiles is not None
    if overlay_active:
        inherited_local = _inventory(model,False)[2]
        reference_profile = G.add_profile(reference_profile,G.delta(inherited_local,local))
        if G.mass(reference_profile) != G.mass(model.expected_profile):
            raise ValueError("fixed-fill held-word overlay changed rank mass despite unchanged helper widths")
    reference = G.root(reference_profile)
    objective = np.asarray([_float_cost(c[2], reference) for c in columns])
    # This installed SciPy wrapper accepts a boolean parallel option; its
    # warning rejects the raw HiGHS string spelling "off".  Explicit threads=1
    # remains necessary because BLAS/OpenMP environment settings do not bind
    # HiGHS' own worker count.
    solver_options={"time_limit":float(time_limit),"threads":1,"parallel":False}
    solved = linprog(objective, A_eq=A, b_eq=b, bounds=(0, None), method="highs",options=solver_options)
    if not solved.success:
        return {"model":model.name,"status": "TIMEOUT" if solved.status == 1 else "ERROR", "solver": solved.message,
                "attribution":model.attributions,"source_files":model.sources,"solver_calls":1,
                "solver_options":solver_options,"solver_resource_policy":"one HiGHS thread; SciPy boolean parallel=False"}
    active = np.flatnonzero(solved.x > 1e-7)
    idle = defaultdict(D)
    active_patterns = []
    for i in active:
        cap, counts, remainder, column = columns[int(i)]
        count = D(str(float(solved.x[i])))
        if remainder:
            idle[remainder] += count
        active_patterns.append(dict(capacity=cap, widths=dict(zip(widths, counts)), remainder=remainder, count=str(count)))
    primal_profile = {r: D(c) for r, c in local.items()}
    for r, c in idle.items():
        primal_profile[r] = primal_profile.get(r, D(0)) + c
    primal_root = G.root(primal_profile)
    target = _round_upper(primal_root) + D("1e-12")
    certificates = None
    marginals = np.asarray(solved.eqlin.marginals, dtype=float)
    if marginals.shape != (len(caps)+len(widths),) or not np.all(np.isfinite(marginals)):
        raise ValueError("successful LP did not return finite equality marginals")
    marginal_record = dict(
        capacity={str(c):str(float(marginals[i])) for i,c in enumerate(caps)},
        width={str(w):str(float(marginals[len(caps)+i])) for i,w in enumerate(widths)},
        convention="SciPy eqlin.marginals = derivative of the minimized objective with respect to b_eq; dual uses the same sign",
        proposal_exponent=str(reference))
    candidate_history = []

    def certify(proposed, target_string, source):
        # The proposal need not itself be feasible. Repair capacity multipliers
        # against every exact rational lower cost before treating it as a bound.
        width_dual = {w: F(str(float(proposed[len(caps)+i]))) for i, w in enumerate(widths)}
        cap_dual = {}
        for cap in caps:
            cap_dual[cap] = min(rational_cost(rem, target_string)[0] - sum(
                n * width_dual[w] for w, n in zip(widths, counts))
                for c, counts, rem, _ in columns if c == cap)
            cap_dual[cap] = _floor_grid(cap_dual[cap])
        violations = []
        for i, (cap, counts, rem, _) in enumerate(columns):
            lhs = cap_dual[cap] + sum(n*width_dual[w] for w, n in zip(widths, counts))
            if lhs > rational_cost(rem, target_string)[0]:
                violations.append(i)
        dual_idle = sum(bins[c]*cap_dual[c] for c in caps) + sum(demand[w]*width_dual[w] for w in widths)
        local_lower = sum(F(count)*rational_cost(r, target_string)[0] for r, count in local.items())
        lower_moment = local_lower + dual_idle
        certificate = dict(exponent=target_string, proposal_source=source,
            capacity_multipliers={str(c): str(q) for c, q in cap_dual.items()},
            width_multipliers={str(w): str(q) for w, q in width_dual.items()},
            dual_idle_moment_lower=str(dual_idle), local_moment_lower=str(local_lower),
            total_moment_lower=str(lower_moment), total_moment_lower_decimal=str(_decimal_fraction(lower_moment)),
            rejection_margin=str(_decimal_fraction(lower_moment - G.REFERENCE_WIRES)),
            all_column_inequalities=len(columns), inequality_violations=violations,
            exact_rational_verification=True, cost_rounding_grid="1e-30",
            root_rejected=lower_moment > G.REFERENCE_WIRES)
        return lower_moment, certificate

    # No solver inside this loop. Positive-column equalities may leave a
    # degenerate dual face undetermined. Check both the active-column fit and
    # the original LP's equality marginals, then select the larger exact lower
    # bound. All capacities are repaired against ALL columns for each proposal.
    for attempt in range(7):
        target_string = str(target)
        target_cost = np.asarray([_float_cost(c[2], target) for c in columns])
        proposed, _, rank, singular = np.linalg.lstsq(A[:, active].T, target_cost[active], rcond=None)
        candidates = [certify(proposed,target_string,"active_positive_columns_lstsq_at_target"),
                      certify(marginals,target_string,"original_lp_equality_marginals")]
        feasible = [item for item in candidates if not item[1]["inequality_violations"]]
        lower_moment, certificates = max(feasible or candidates, key=lambda item:item[0])
        candidate_history.append(dict(exponent=target_string,
            active_system=dict(positive_columns=len(active), equality_multipliers=A.shape[0],
                               lstsq_rank=int(rank), singular_values=[str(float(x)) for x in singular]),
            candidates=[certificate for _,certificate in candidates],
            selected_source=certificates["proposal_source"],
            selection="maximum exact rational total_moment_lower among all-column feasible candidates"))
        if not certificates["inequality_violations"] and lower_moment > G.REFERENCE_WIRES:
            break
        target += D("1e-12") * (10**(attempt+1))
    return dict(status="PASS" if certificates["root_rejected"] and not certificates["inequality_violations"] else "EXPLORATORY",
        model=model.name, pattern_count=len(columns), capacity_counts=bins, role_width_counts=demand,
        local_profile=local, solver_message=solved.message, solver_calls=1,solver_options=solver_options,
        solver_resource_policy="one HiGHS thread; SciPy boolean parallel=False",
        primal_residual_max=float(np.max(np.abs(A @ solved.x - b))),
        primal_idle_profile={r: str(c) for r, c in idle.items()}, active_patterns=active_patterns,
        primal_profile_root=str(primal_root), certified_ceiling=certificates["exponent"], dual=certificates,
        lp_equality_marginals=marginal_record, dual_candidate_history=candidate_history,
        dual_recovery_protocol="Exactly two proposals at each of at most seven unchanged target exponents; one LP total; every proposal repaired and checked against every column with exact rational costs.",
        certificate_kind="certified LP dual ceiling; floating primal is a proposal, not an exact optimum certificate",
        literal_root=str(reference), literal_profile=reference_profile,
        inherited_literal_root=str(G.root(model.expected_profile)) if overlay_active else None,
        literal_control_scope="same recorded owner fill with exact held-word local-profile overlay" if overlay_active
                              else "literal pinned provider metadata and recorded fill",
        ceiling_dominates_literal=reference < D(certificates["exponent"]),
        scope="fixed role-width inventory and physical capacity multiplicities; arbitrary fractional bin patterns; eligibility/family constraints relaxed",
        violating_construction_must_change="local paid profile, role-width inventory, bin capacities/counts, or coverage geometry",
        local_profile_source="explicit held-word overlay at unchanged helper widths" if use_overlay and model.overlay_local_profiles is not None
                             else "literal pinned provider metadata",
        inherited_provider_notes=model.source_notes,
        inherited_local_profile=_inventory(model,False)[2] if use_overlay and model.overlay_local_profiles is not None else None,
        attribution=model.attributions, source_files=model.sources)


def _helper_payment_partition(word):
    """Physical helper width partitions ascending climbs, not centre descents.

    Keep each nonascending helper payment fixed, with its actual partition.
    Calling this helper does not remove a register or assert deletion feasibility.
    """
    helpers, fixed = [], []
    for reg in word.helpers:
        jumps = word.climbs[reg]["jumps"]
        if any(j["kind"] not in ("climb", "centre_descent") for j in jumps):
            raise ValueError("unregistered helper payment kind")
        seq = tuple(j["rank"] for j in jumps if j["kind"] == "climb")
        if sum(seq) != word.climbs[reg]["width"]:
            raise ValueError("ascending helper climb mass differs from physical width")
        helpers.append((reg, seq, sum(seq)))
        other = [j["rank"] for j in jumps if j["kind"] != "climb"]
        if other:
            fixed.append(dict(register=reg, kind="centre_descent", paid_parts=other,
                              mass=sum(other)))
    return helpers, dict(per_register=fixed, total_mass=sum(x["mass"] for x in fixed),
        profile=dict(Counter(r for x in fixed for r in x["paid_parts"])),
        scope="Only nonascending payments on helpers are fixed here, each with its actual paid partition; other registers are not added again.")


def _helper_envelope(word, local, idle_mass, ks):
    helpers, fixed = _helper_payment_partition(word)
    out = []
    for count in ks:
        if not 0 <= count <= len(helpers):
            raise ValueError("helper envelope count out of range")
        def minimum(k):
            concentration = _float_cost(51, k) / 51
            all_moment = sum(c*_float_cost(r, k) for r, c in local.items()) + idle_mass*concentration
            benefits = sorted((sum(_float_cost(r, k) for r in seq) - width*concentration
                               for _, seq, width in helpers), reverse=True)
            return all_moment - G.CALLS*sum(benefits[:count])
        lo, hi = 0.0, .02
        for _ in range(70):
            mid = (lo+hi)/2
            if minimum(mid) < G.REFERENCE_WIRES:
                lo = mid
            else:
                hi = mid
        target = _round_upper(hi) + D("1e-12")
        certified = None
        for attempt in range(5):
            k = str(target)
            low51, high51 = rational_cost(51, k)
            base_lower = sum(F(c)*rational_cost(r, k)[0] for r, c in local.items()) + F(idle_mass,51)*low51
            # A rigorous upper bound on each removed helper's benefit gives a
            # lower bound on the moment remaining after the best k removals.
            benefits = sorted(((sum(rational_cost(r,k)[1] for r in seq) - F(width,51)*low51, reg)
                               for reg, seq, width in helpers), reverse=True)
            lower = base_lower - G.CALLS*sum(q for q, _ in benefits[:count])
            certified = dict(k_removed=count, ceiling=str(target), total_moment_lower=str(lower),
                total_moment_lower_decimal=str(_decimal_fraction(lower)),
                rejected=lower > G.REFERENCE_WIRES, maximizing_relaxed_helper_ids=[r for _,r in benefits[:count]],
                proof="original global local+rank51-idle lower moment minus 666 times largest k rigorous upper ascending-chain removal benefits; all centre descents stay fixed")
            if lower > G.REFERENCE_WIRES:
                break
            target += D("1e-12") * 10**(attempt+1)
        out.append(certified)
    return out, fixed


def ceilings(seed, removal_counts=(0,1,2,4,8,16,32,64,128,256,408)):
    import wordio
    rows = [pattern_ceiling(_model(name),use_overlay=(name=="1672")) for name in ("2802", "2751", "1672")]
    word = wordio.load(G.resolve_word("2802")[0])
    profile = G._profile_records()["2802"]["profile"]
    local = {r: G.CALLS*c for r, c in word.paid.items()}
    idle = {r: profile.get(r,0)-local.get(r,0) for r in set(profile)|set(local)}
    idle_mass = G.mass(idle)
    n48, rem = divmod(idle_mass,48)
    integral = dict(local)
    integral[48] = integral.get(48,0)+n48
    if rem:
        integral[rem] = integral.get(rem,0)+1
    old_recipe = dict(local)
    old_recipe[48] = old_recipe.get(48,0)+n48
    old_recipe[1] = old_recipe.get(1,0)+rem
    fractional = {r:D(c) for r,c in local.items()}
    fractional[51] = D(idle_mass)/51
    packing = G.root(fractional)
    exact_fractional = {r:F(c) for r,c in local.items()}
    exact_fractional[51] = F(idle_mass,51)
    packing_bracket = _rational_root_bracket(exact_fractional,packing)
    integral_root = G.root(integral)
    integral_bracket = _rational_root_bracket(integral,integral_root)
    envelope, fixed_helper_payments = _helper_envelope(word, local, idle_mass, removal_counts)
    valid = (all(r["status"] == "PASS" and r["ceiling_dominates_literal"] for r in rows)
             and all(r["rejected"] for r in envelope)
             and all(r["lower_certified"] and r["upper_certified"] for r in (packing_bracket,integral_bracket)))
    tight = next(r for r in rows if r["model"]=="2802")
    comparison = (tight.get("status")=="PASS" and packing_bracket["lower_certified"]
                  and D(tight["certified_ceiling"]) < D(packing_bracket["lo"]))
    source_path = G.PKG / "packing_cap.py"
    return dict(experiment="L-8", seed=seed, n_permutations=0, status="PASS" if valid else "EXPLORATORY",
        decision="all stated relaxations have independently checked dual bounds" if valid else "some ceiling certificate remains unresolved",
        fixed_inventory=rows, packing_cap=str(packing), integral_rank48_cap=str(integral_root),
        packing_cap_certified_bracket=packing_bracket, integral_rank48_certified_bracket=integral_bracket,
        packing_comparator_source=dict(path=str(source_path.relative_to(G.ROOT)),
            sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),handling="read as source only, never imported",
            class_identity="same fixed #2802 local paid profile and coverage law; remaining idle mass becomes fractional rank51 children"),
        integral_rank48_profile=integral,
        planning_rounding_note={"remainder":rem,"proper_integral_remainder":"one rank-remainder child",
            "planning_recipe":"remainder many rank-1 children", "planning_recipe_root":str(G.root(old_recipe)),
            "reason":"concavity places the integral remainder in one child; splitting it into ones is not a universal ceiling"},
        tighter_than_packing_cap=comparison,
        ceiling_comparison_protocol="certified LP upper < independently rational-certified packing lower; no numerical-overlap assertion",
        helper_removal_envelope=envelope,
        helper_removal_fixed_payments=fixed_helper_payments,
        helper_removal_scope="up to k whole ascending helper climb strings removed, freed physical width joins fractional idle rank51; centre descents and all other local paid children stay fixed; no feasibility of deleting these strings or registers asserted",
        ceiling_falsification_classes={
            "rank48_integral":"a violation changes the local word/coverage law or introduces idle children of rank >48",
            "rank51_fractional":"a violation changes the local word/coverage law or the maximum idle rank",
            "helper_removal":"a violation removes additional ascending helper strings or changes remaining climbs, fixed centre descents, other local paid children, or the coverage law"},
        attribution=G.sources(all_words=True),
        pattern_criteria={"non_circular":False,"reason":"class ceilings condition on profiles and inventories; certificates, not five-criterion patterns"})


def merge_calibration():
    recs = G._profile_records()
    before, after = recs["2751"]["profile"], recs["2766"]["profile"]
    merge = {1:-2*G.CALLS,2:G.CALLS}
    predicted = G.root(G.add_profile(before,merge))-G.root(before)
    observed = G.root(after)-G.root(before)
    return dict(label="2751->2766 (1,1)->2 once per call", delta=merge,
        profile_identity=G.add_profile(before,merge)==after, predicted=str(predicted), observed=str(observed),
        relative_error=str(abs(predicted-observed)/abs(observed)), within_one_percent=abs(predicted-observed)<=abs(observed)/100,
        scope="one supported realised refit step; no invented calibration margin")


def partitions(seed, n_permutations=2000, keys=L10_KEYS):
    import numpy as np
    import wordio
    if n_permutations<2000:
        raise ValueError("partition inference requires n>=2000")
    rng = np.random.default_rng(seed)
    reference = G.root(G._profile_records()["2802"]["profile"])
    pins = G.read_json(G.PINS)["files"]
    rows=[]
    for key in keys:
        path = G.ROOT/key if "/" in key else G.STYLES/"data/words"/key
        word=wordio.load(path)
        configs=Counter()
        observed_moment=observed_phi=0.0
        helpers, fixed_helper_payments = _helper_payment_partition(word)
        fixed_moment=sum(c*_float_cost(r,reference) for r,c in fixed_helper_payments["profile"].items())
        fixed_phi=sum(c*r*math.log(r) for r,c in fixed_helper_payments["profile"].items())
        for reg,seq,width in helpers:
            configs[width,len(seq)]+=1
            observed_moment+=sum(_float_cost(r,reference) for r in seq)
            observed_phi+=sum(r*math.log(r) for r in seq)
        observed_moment+=fixed_moment
        observed_phi+=fixed_phi
        null_moment=np.full(n_permutations,fixed_moment)
        null_phi=np.full(n_permutations,fixed_phi)
        mutable_registers=0
        for (width,parts),count in configs.items():
            if parts == 0:
                if width != 0:
                    raise ValueError("positive helper width has no paid parts")
                compositions=[()]
            else:
                compositions=[]
                for cuts in itertools.combinations(range(1,width),parts-1):
                    ends=(0,)+cuts+(width,)
                    compositions.append(tuple(b-a for a,b in zip(ends,ends[1:])))
            costs=np.asarray([sum(_float_cost(r,reference) for r in seq) for seq in compositions])
            phis=np.asarray([sum(r*math.log(r) for r in seq) for seq in compositions])
            if len(compositions)>1:
                mutable_registers+=count
            samples=rng.integers(len(compositions),size=(n_permutations,count))
            null_moment+=costs[samples].sum(axis=1)
            null_phi+=phis[samples].sum(axis=1)
        # Fixed tolerance prevents different addition orders from promoting
        # mathematically tied histograms to strict extremality discoveries.
        tie_tolerance=1e-10
        p=(1+int(np.count_nonzero(null_moment<=observed_moment+tie_tolerance)))/(1+n_permutations)
        below_fraction=float(np.count_nonzero(null_moment>observed_moment+tie_tolerance))/n_permutations
        rows.append(dict(word=key,family=word.family,attribution=dict(path=key,**pins[key]),
            statistic="sum of helper paid moment at fixed #2802 kappa; lower is better",
            moment=observed_moment,phi=observed_phi,mutable_helpers=mutable_registers,
            fixed_nonascending_helper_payments=dict(fixed_helper_payments,moment=fixed_moment,phi=fixed_phi),
            ascending_partition_scope="Each physical helper width and ascending part count is preserved; actual nonascending helper payments are fixed and included exactly once in both real and null statistics.",
            null={"protocol":"independent uniform ordered positive compositions of each physical helper width with unchanged ascending part count; actual nonascending helper payments fixed",
                  "moment":{**G._summary(null_moment.tolist(),observed_moment,tail="le"),"empirical_p":p},
                  "phi":G._summary(null_phi.tolist(),observed_phi),"permutation_p":p,
                  "moment_tie_tolerance":tie_tolerance},
            fraction_of_null_above_real=below_fraction,passes_99_percent=below_fraction>=.99 and p<=.01))
    # The registered family is the nine per-word moment tests.  Phi summaries
    # are descriptive; they are not a second family of discoveries.
    order=sorted(range(len(rows)),key=lambda i:rows[i]["null"]["permutation_p"])
    q=1.0
    for rank in reversed(range(len(order))):
        index=order[rank]
        q=min(q,rows[index]["null"]["permutation_p"]*len(rows)/(rank+1))
        rows[index]["null"]["bh_q"]=q
        rows[index]["passes_99_percent"] &= q<=.05
    calibration=merge_calibration()
    passed=(all(r["passes_99_percent"] for r in rows) and calibration["profile_identity"]
            and calibration["within_one_percent"])
    return dict(experiment="L-10",seed=seed,n_permutations=n_permutations,status="PASS" if passed else "NULL",
        words=rows,merge_calibration=calibration,
        multiple_testing="BH-FDR 5% across the fixed per-word moment family; Phi is descriptive",
        decision="every word meets partition bar and realised merge calibration" if passed else "registered every-word partition/margin conjunction fails",
        pattern_criteria={"non_circular":False,"reason":"total Phi/moment is invariant under profile-preserving N2; headroom bookkeeping, not a non-circular pattern"})


def multitype(seed):
    if _TEMPLATE is None:
        raise RuntimeError("parent must call prepare before the multitype check")
    model=_model("2802")
    orientation={row["stage"]:row["reverse"] for row in _TEMPLATE["recipe"] if row["kind"]=="local"}
    groups=defaultdict(Counter)
    profiles={}
    for (stage,replica),profile in zip(model.order,model.local_profiles):
        key=tuple(sorted(profile.items()))
        profiles[str(key)]=profile
        groups[stage,orientation[stage]][str(key)]+=1
    call_count=sum(sum(c.values()) for c in groups.values())
    count_valid=(call_count==model.calls==G.CALLS and len(model.local_profiles)==model.calls)
    if not count_valid:
        raise ValueError(("registered L11 call-count mismatch", call_count, model.calls,
                          len(model.local_profiles), G.CALLS))
    same=len(profiles)==1
    return dict(experiment="L-11",seed=seed,n_permutations=0,status="PASS" if same else "NULL",
        decision="all dispatched local-call paid profiles identical" if same else "stage/orientation local profiles differ",
        total_calls=call_count,expected_calls=G.CALLS,call_count_valid=count_valid,
        distinct_local_profiles=list(profiles.values()),
        stage_orientation_profiles=[dict(stage=s,reverse=o,counts=dict(c)) for (s,o),c in sorted(groups.items())],
        scope="tests paid child profile of dispatched local providers per stage/orientation; varying idle allocations are a fill layer, not evidence of inherited recursive types",
        recursive_type_inheritance="not inferred from stage labels alone; persistent child-type transitions would require a separate semantic derivation",
        attribution=model.attributions,source_files=model.sources)


def saturation(seed,n_permutations=2000):
    import matching
    if n_permutations<2000:
        raise ValueError("saturation control requires n>=2000")
    path,pin=G.resolve_word("2802")
    census=matching.census(path)
    lives,slots=matching.graph_data(census)
    graph=matching.adjacency(lives,slots)
    pairs=census["pairs"]
    candidates=[]
    for life,ld in lives.items():
        if not life.startswith("follower:"):
            continue
        for occupied in graph[life]:
            host=slots[occupied].get("occupied_by")
            if host is None:
                continue
            for free in graph.get(host,[]):
                if slots[free].get("occupied_by") is None:
                    candidates.append([life,occupied,host,free])
    rng=random.Random(seed)
    ll=list(lives.values());ss=list(slots.values())
    controls=[]
    for _ in range(n_permutations):
        ld,sd=rng.choice(ll),rng.choice(ss)
        controls.append(int(sd["last"]<ld["first"] and sd["lo"]<=ld["hi"] and sd["register"]!=ld.get("register")))
    optimum=_OPTIMA.get(str(path),_OPTIMA.get("2802"))
    empty_alias=len(pairs)==0
    return dict(experiment="L-9",seed=seed,n_permutations=n_permutations,
        status="EXPLORATORY",decision="exact alias/hostee necessary-guard census; other production classes need their constructive guards",
        direct_alias_pairs=pairs,direct_alias_guard_class_empty=empty_alias,
        hostee_augmenting_paths=candidates,hostee_guard_class_empty=not candidates,
        refit_optimum_control=optimum,
        bounds=census["bounds"],random_pair_feasibility=G._summary(controls),
        null_protocol="uniform independent life/slot pairs; exact time/dimension guards only",
        predicted_empty_classes=["direct aliases satisfying current pinned time/dimension guards"] if empty_alias else [],
        unresolved=["constructive simultaneous hostee-refit gains", "restorable width-cut class", "kernel identity classes"],
        phi_scope="no positive Phi claimed from necessary guards alone; exact production and fill deltas required",
        attribution=[pin])


def task(spec):
    exp,seed=spec["experiment"],int(spec["seed"])
    if exp=="L-8":
        return ceilings(seed,tuple(spec.get("removal_counts",(0,1,2,4,8,16,32,64,128,256,408))))
    if exp=="L-9":
        return saturation(seed,int(spec.get("n_permutations",2000)))
    if exp in ("L-10","S-3"):
        result=partitions(seed,int(spec.get("n_permutations",2000)),tuple(spec.get("word_keys",L10_KEYS)))
        result["experiment"]=exp
        return result
    if exp=="L-11":
        return multitype(seed)
    raise ValueError(exp)
