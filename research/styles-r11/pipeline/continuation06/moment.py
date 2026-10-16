"""Exact T370 profile moment for the registered five-copy packing cycle.

The module has no import-time science, subprocesses, pools, or fetched-code
execution.  ``prepare`` is called once in the registered parent; workers call
``controls_task`` and ``assess_task``.  A moment certificate is conditional on
the independent literal allocation producing this complete paid profile.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
RR = HERE.parents[1]
ROOT = RR.parents[1]
DIMENSION = 73
SOURCE_LIVE = 66304
SOURCE_CALLS = 666
COPIES = 5
LIVE = COPIES * SOURCE_LIVE
CALLS = COPIES * SOURCE_CALLS
REPLICAS = 370
GRID = Q(1, 10**24)
SOURCE_ENDPOINT = Q(1729033982646513517717, 10**24)
OUTER_LOSS = Q(1, 10**46) + Q(1, 10**70)
CYCLE = {1: 20, 3: 19, 5: -25, 48: 1}
SOURCE_HEAD = 'be191346391661f4d35fc0d1508d0a6029572576'
TRUSTED = {
    'path': 'research/t74-joint-twelve-retired7/vendor/ceiling.py',
    'sha256': '86a1432870b3b21d8454106ec9162fddc0471472d9214c590a1420f2426cedfc',
    'used_function': 'child_cost only; obsolete outer interpretation unused',
}
PINS = {
    'claim': ('data/continuation-05/pr2979/package/CLAIM.json',
              '436e0d297cbdf195445d3697d496ac675e95210b79e70ce602a6a6667a4c6ce9'),
    'profile': ('data/continuation-05/pr2979/package/allocation/PROFILE.json',
                '94a819747f3ced41f1544ada0036c983fc0c92847b9644380f877a06cd7931cf'),
    'acquisition': ('data/continuation-05/pr2979/ACQUISITION.json',
                    'e5ad48ac05e897dcc2e073d29be451cfd1493ba3077e7e2de0f9460aa11a7d71'),
    'original_words': ('data/words/PINS.json',
                       '4d62f7caf94a102ebb83feb3beca6ebeb1ab9637901ff51cc84e5beeb15d2a65'),
}
_STATE = None
_COST = None
_CACHE = {}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def encode(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(encode(value), sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def decimal(value):
    with localcontext() as context:
        context.prec = 80
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def _read_pin(name):
    relative, expected = PINS[name]
    raw = (RR / relative).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'source pin: ' + name)
    return json.loads(gzip.decompress(raw) if relative.endswith('.gz') else raw)


def _load_cost():
    global _COST
    if _COST is None:
        path = ROOT / TRUSTED['path']
        need(hashlib.sha256(path.read_bytes()).hexdigest() == TRUSTED['sha256'],
             'trusted rational child-cost source pin')
        need(not sys.flags.optimize, 'assertions must remain enabled')
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('styles_cont06_exact_cost', path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _COST = module
    return _COST


def _profile(raw, signed=False):
    need(isinstance(raw, dict) and raw, 'nonempty profile mapping')
    out = {}
    for key, count in raw.items():
        rank = int(key)
        need(str(rank) == str(key) and 1 <= rank <= 48 and type(count) is int,
             'canonical integer rank/profile multiplicity')
        need(signed or count >= 0, 'nonnegative full profile')
        if count:
            out[rank] = count
    return dict(sorted(out.items()))


def _add(left, right):
    return {r: left.get(r, 0) + right.get(r, 0)
            for r in sorted(set(left) | set(right))
            if left.get(r, 0) + right.get(r, 0)}


def _mass(profile):
    return sum(r * count for r, count in profile.items())


def _validate_cycle(delta):
    delta = _profile(delta, signed=True)
    need(_mass(delta) == 0, 'cycle preserves exact rank mass')
    need(delta == CYCLE, 'exact registered directed cycle')
    return delta


def _validate_claim(endpoint):
    need(Q(endpoint) == SOURCE_ENDPOINT, 'claimed source endpoint agrees with pinned CLAIM')


def _costs(endpoint):
    endpoint = Q(endpoint)
    need(0 <= endpoint <= Q(1, 100), 'registered moment exponent range')
    if endpoint not in _CACHE:
        cost = _load_cost()
        _CACHE[endpoint] = {r: cost.child_cost(r, DIMENSION, endpoint)
                            for r in range(1, 49)}
    return _CACHE[endpoint]


def _moment(profile, endpoint, live=LIVE):
    need(type(live) is int and live > 0, 'positive exact live-family denominator')
    costs = _costs(endpoint)
    lower = upper = Q(0)
    for rank, count in profile.items():
        a, b = costs[rank]
        lower += count * (a if count >= 0 else b)
        upper += count * (b if count >= 0 else a)
    return lower / live, upper / live


def _evaluation(profile, endpoint, live=LIVE, include_costs=True):
    low, high = _moment(profile, endpoint, live)
    result = dict(endpoint=Q(endpoint), lower=low, upper=high,
                  below_one_margin=1-high, above_one_margin=low-1,
                  normalization_live=live, dimension=DIMENSION)
    if include_costs:
        result['child_cost_intervals'] = _costs(endpoint)
    return result


def _certify_endpoint(profile, endpoint):
    value = _evaluation(profile, endpoint)
    need(value['upper'] < 1, 'claimed endpoint must have strict moment upper below one')
    return value


def _bracket(profile, live=LIVE):
    """General monotone complete-profile root bracket, no LP or numerical root."""
    low, high = Q(0), Q(1, 100)
    need(_moment(profile, low, live)[1] < 1, 'positive-root lower bracket')
    need(_moment(profile, high, live)[0] > 1, 'positive-root upper bracket')
    steps = 0
    while high-low > GRID:
        middle = ((low+high) // (2*GRID)) * GRID
        if middle <= low:
            middle = low+GRID
        lo, hi = _moment(profile, middle, live)
        if hi < 1:
            low = middle
        elif lo > 1:
            high = middle
        else:
            raise ArithmeticError('rational interval does not resolve a registered root-grid point')
        steps += 1
        need(steps <= 100, 'bounded monotone root search')
    low_eval, high_eval = (_evaluation(profile, x, live) for x in (low, high))
    need(low_eval['upper'] < 1 < high_eval['lower'], 'strict exact root bracket')
    need(0 < high-low <= GRID, 'registered root-grid width')
    return dict(lower=low, upper=high, width=high-low, grid=GRID,
                lower_endpoint=low_eval, upper_endpoint=high_eval,
                decimal_interval=[decimal(low), decimal(high)], iterations=steps)


def _state():
    need(_STATE is not None, 'registered parent prepare must precede worker calls')
    return _STATE


def prepare(state):
    """Parent-only preparation; source costs at the fixed endpoint loaded once.

    Optional state keys: candidate_profile, source_profile, copies, live, calls,
    dimension, source_endpoint, source_attribution, allocation_evidence.  Every
    supplied scientific value is checked against the pinned registered model.
    No allocation feasibility or native reuse is inferred from this input.
    """
    global _STATE
    started = time.process_time()
    need(_STATE is None and isinstance(state, dict), 'exactly one parent preparation')
    claim = _read_pin('claim')
    source = _profile(_read_pin('profile'))
    acquisition = _read_pin('acquisition')
    original_pins = _read_pin('original_words')
    need(source == _profile(claim['profile']), 'CLAIM complete profile/source equality')
    need((claim['calls'], claim['live_families'], claim['replicas']) ==
         (SOURCE_CALLS, SOURCE_LIVE, 74), 'pinned T74 source geometry')
    _validate_claim(claim['complex_lower'])
    need(Q(claim['kappa']) == SOURCE_ENDPOINT-OUTER_LOSS,
         'pinned modern outer endpoint-to-kappa convention')
    for key, value in dict(copies=COPIES, live=LIVE, calls=CALLS,
                           dimension=DIMENSION).items():
        need(state.get(key, value) == value, 'registered scale: '+key)
    _validate_claim(state.get('source_endpoint', SOURCE_ENDPOINT))
    if 'source_profile' in state:
        need(_profile(state['source_profile']) == source, 'supplied unscaled source profile')
    base = {r: COPIES*n for r, n in source.items()}
    candidate = _profile(_add(base, _validate_cycle(CYCLE)))
    if 'candidate_profile' in state:
        need(_profile(state['candidate_profile']) == candidate,
             'literal candidate profile must equal complete five-copy cycle profile')
    mass = 72*LIVE+64*CALLS
    need(_mass(base) == _mass(candidate) == mass == 24082560,
         'five-copy full local-plus-idle coverage mass')
    local = _profile(claim['local_profile'])
    idle = _add(candidate, {r: -CALLS*n for r, n in local.items()})
    need(all(n >= 0 for n in idle.values()), 'nonnegative fully charged idle profile')
    _load_cost()
    _costs(SOURCE_ENDPOINT)
    attribution = dict(pr=2979, head=SOURCE_HEAD,
        author=acquisition['author'], acquisition=dict(path=PINS['acquisition'][0],
            sha256=PINS['acquisition'][1]), original_words_PINS=original_pins,
        inherited_credits='All acquired CREDITS.md, NOTICE, SOURCES.json and PINS.json remain in force.',
        supplied=deepcopy(state.get('source_attribution')))
    _STATE = dict(source=source, baseline=base, candidate=candidate, local=local, idle=idle,
        attribution=attribution, allocation_evidence=deepcopy(state.get('allocation_evidence')),
        source_claim=claim, mass=mass)
    return encode(dict(parent_loaded_once=True, live=LIVE, calls=CALLS, replicas=REPLICAS,
        source_endpoint=SOURCE_ENDPOINT, complete_profile=candidate, cycle=CYCLE,
        rank_mass=mass, exact_source_cost_ranks=list(range(1,49)),
        trusted_cost=TRUSTED, source_pins=PINS, source_attribution=attribution,
        cpu_seconds=time.process_time()-started))


def controls_task(seed):
    started = time.process_time()
    s = _state()
    _validate_cycle(CYCLE)
    need(_mass(CYCLE) == 20+57+48-125 == 0, 'independent integer cycle mass')
    need(_moment({}, SOURCE_ENDPOINT) == (0,0), 'exact no-op signed delta')
    need(_moment(s['baseline'], SOURCE_ENDPOINT) ==
         _moment(s['source'], SOURCE_ENDPOINT, SOURCE_LIVE),
         'five-copy normalization equals the source moment exactly')
    bad_mass = dict(CYCLE)
    bad_mass[48] -= 1
    bad_mass[47] = 1
    probes = dict(
        reversed_directed_cycle=lambda: _validate_cycle({r:-n for r,n in CYCLE.items()}),
        wrong_rank_mass=lambda: _validate_cycle(bad_mass),
        false_source_endpoint=lambda: _validate_claim(SOURCE_ENDPOINT+GRID),
        overstated_candidate_endpoint=lambda: _certify_endpoint(s['candidate'], Q(1,100)),
    )
    rejections = {}
    for label, check in probes.items():
        try:
            check()
        except ValueError as error:
            rejections[label] = dict(rejected=True, reason=str(error))
        else:
            rejections[label] = dict(rejected=False)
    need(all(x['rejected'] for x in rejections.values()), 'every registered moment mutant rejects')
    return encode(dict(status='PASS', seed=int(seed), cycle_mass=0,
        no_op_delta=[Q(0),Q(0)], five_copy_normalization_exact=True,
        controls=rejections, source_pins=PINS, trusted_cost=TRUSTED,
        source_attribution=s['attribution'], cpu_seconds=time.process_time()-started,
        scope='Exact profile/moment controls only; no allocation or native admission.'))


def assess_task(seed):
    started = time.process_time()
    s = _state()
    target_source = _evaluation(s['baseline'], SOURCE_ENDPOINT)
    target_candidate = _evaluation(s['candidate'], SOURCE_ENDPOINT)
    delta = _evaluation(CYCLE, SOURCE_ENDPOINT)
    # Difference uses signed outward intervals directly, avoiding cancellation
    # from independently summed large positive profile moments.
    need(delta['upper'] < 0, 'strict exact registered cycle moment improvement')
    need(target_source['upper'] < 1 and target_candidate['upper'] < 1,
         'source and candidate strictly admit the pinned source endpoint')
    baseline_root = _bracket(s['baseline'])
    candidate_root = _bracket(s['candidate'])
    endpoint = candidate_root['lower']
    need(endpoint > baseline_root['upper'] >= SOURCE_ENDPOINT,
         'candidate lower root is above the entire exact baseline-root bracket')
    kappa = endpoint-OUTER_LOSS
    source_kappa = Q(s['source_claim']['kappa'])
    need(kappa > source_kappa and endpoint-SOURCE_ENDPOINT == kappa-source_kappa,
         'modern outer proposal improves the source by the exact endpoint gap')
    return encode(dict(status='PASS_CONDITIONAL_PROFILE_MOMENT', seed=int(seed),
        dimension=DIMENSION, live=LIVE, calls=CALLS, replicas=REPLICAS,
        source_profile=s['source'], five_copy_baseline_profile=s['baseline'],
        complete_profile=s['candidate'], complete_profile_sha256=digest(s['candidate']),
        local_per_call=s['local'], aggregate_idle_profile=s['idle'],
        profile_delta=CYCLE, delta_rank_mass=0, exact_full_rank_mass=s['mass'],
        source_target_evaluation=target_source, candidate_target_evaluation=target_candidate,
        cycle_target_delta=delta, baseline_root=baseline_root, candidate_root=candidate_root,
        complex_lower=endpoint, complex_lower_decimal=decimal(endpoint),
        proposed_kappa=kappa, proposed_kappa_decimal=decimal(kappa),
        source_complex_lower=SOURCE_ENDPOINT, source_kappa=source_kappa,
        gain_over_source=endpoint-SOURCE_ENDPOINT,
        gain_over_actual_source_root_lower=endpoint-baseline_root['upper'],
        modern_outer_loss=OUTER_LOSS, source_pins=PINS, trusted_cost=TRUSTED,
        source_attribution=s['attribution'], allocation_evidence=s['allocation_evidence'],
        solver_calls=0, cpu_seconds=time.process_time()-started,
        proof='For this complete nonnegative profile, normalized moment is strictly increasing in the complex exponent because every child rank is between1 and48<73. Each bracket endpoint is checked using exact outward rational child costs. Direct signed cost arithmetic certifies the cycle improvement; five-copy scaling cancels exactly against live331520.',
        scope='Conditional full-profile moment certificate and proposed modern outer parameter only. Literal T370 allocation, interval/family/offset guards, unchanged-word native source binding, scaled physical/primitive invoice, global prefix/blocknorm, supplier strict gates and outer inequalities must be independently closed before any admitted kappa claim. The old a/(1+a) interpretation is not used.'))
