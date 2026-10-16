"""Exact optimistic paid-local packing screen for one new rank-seven endpoint.

Parent-only prepare; registered worker entry screen_task; no import-time tests,
internal parallelism, solver, subprocess or fetched-code execution. The trusted
packing lemma is a lower bound on moments, so a passing screen is only possible
headroom. It is not a feasible allocation, native admission or released kappa.
"""
from __future__ import annotations

from collections import Counter
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
GRID = Q(1, 10**20)
TRUSTED = {
    'wordio': ('research/styles-r11/pipeline/wordio.py',
               'a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4'),
    'ceiling': ('research/t74-joint-twelve-retired7/vendor/ceiling.py',
                '86a1432870b3b21d8454106ec9162fddc0471472d9214c590a1420f2426cedfc'),
}
ALLOWED_CHANGED_FIELDS = frozenset(('A', 'B', 'restore', 'helper_final',
                                    'compensation', 'report', 'cleanup'))
_MODULES = {}
_STATE = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def decimal(value):
    with localcontext() as context:
        context.prec = 60
        return str(Decimal(value.numerator)/Decimal(value.denominator))


def _module(name):
    relative, digest = TRUSTED[name]
    path = ROOT/relative
    need(sha(path) == digest, 'trusted source pin: '+relative)
    if name not in _MODULES:
        need(not sys.flags.optimize, 'assertions must remain enabled')
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('styles_continuation02_cap_'+name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _MODULES[name] = module
    return _MODULES[name]


def _target(entry):
    """Read only a pinned inert JSON field; no live-head or exponent guessing."""
    reference = entry['source']
    path = Path(reference['path'])
    if not path.is_absolute():
        path = RR/path
    path = path.resolve()
    need(path.is_relative_to(RR.resolve()), 'target artifact confinement')
    need(path.name.endswith(('.json', '.json.gz')), 'inert JSON target required')
    need(sha(path) == reference['sha256'], 'incorrect target pin')
    raw = path.read_bytes()
    value = json.loads(gzip.decompress(raw) if path.name.endswith('.gz') else raw)
    fields = entry['endpoint_field']
    need(isinstance(fields, list) and fields, 'explicit complex endpoint field')
    for field in fields:
        value = value[field]
    need(isinstance(value, (str, int)) and not isinstance(value, bool), 'exact complex endpoint representation')
    endpoint = Q(value)
    need(0 < endpoint < Q(1, 500), 'complex endpoint in fixed registered range')
    if 'endpoint' in entry:
        need(Q(entry['endpoint']) == endpoint, 'target endpoint/source mismatch')
    return dict(label=entry['label'], source=deepcopy(reference), endpoint_field=deepcopy(fields),
                endpoint=str(endpoint), kind='complex_lower_endpoint',
                source_status=entry.get('source_status', 'pinned reported source; not independently admitted here'))


def _profile(value):
    out = {}
    for rank, count in value.items():
        r = int(rank)
        need(str(r) == str(rank) and 0 < r < 73 and type(count) is int and count >= 0,
             'canonical nonnegative paid profile')
        if count:
            out[r] = count
    need(out, 'nonempty paid-local profile')
    return out


def _paid_mass(paid, widths):
    need(len(widths) == 408 and all(type(w) is int and 0 < w <= 9 for w in widths),
         '408 actual positive helper widths')
    mass = sum(r*n for r, n in paid.items())
    # 112 input rises, 112 output paths, eight rank-eight centre payments.
    need(mass == sum(widths)+112*8+112*8+8*8, 'paid-local/ordered-width mass identity')
    return mass


def _physical_stock(buffers, declared):
    stock = 66304+408+8+buffers+2
    need(type(buffers) is int and buffers == 83 and declared == stock == 66805,
         'one additional private buffer must be charged:83 buffers,66805 physical families')
    return stock


def prepare(record, target):
    """Once-parent source preparation, after registration; no cap evaluated.

    target={label,source:{path,sha256},endpoint_field:[...],endpoint?}.
    record is the untouched latest_fill.get_record() for PR2917.
    """
    global _STATE
    need(_STATE is None, 'packing cap preparation exactly once')
    need(str(record['pr']) == '2917' and record.get('prepare_error') is None,
         'unchanged parent-loaded PR2917 source')
    need((record['dimension'], record['wires'], record['model'].calls) == (73, 66304, 666),
         'fixed source geometry')
    need(set(record['words']) == {'gauge44', 'extra'}, 'both literal providers')
    for name in TRUSTED:
        _module(name)
    comparison = _target(target)
    _STATE = dict(record=record, target=comparison, target_spec=deepcopy(target),
                  dispatch_counts=Counter(record['dispatch'].values()))
    return dict(parent_loaded_once=True, target=deepcopy(comparison),
                dispatch_counts=dict(_STATE['dispatch_counts']), trusted_sources=dict(TRUSTED),
                target_ranks=[48, 51], nominee_ceiling_grid=str(GRID), no_cap_evaluated=True)


def _state():
    need(_STATE is not None, 'parent prepare required before pool launch')
    return _STATE


def _candidate(provider, raw, attribution):
    state, W = _state(), _module('wordio')
    record = state['record']
    need(provider in record['words'], 'known dispatched provider')
    original = record['words'][provider]
    changed = {k for k in set(original.raw)|set(raw) if original.raw.get(k) != raw.get(k)}
    need(changed <= ALLOWED_CHANGED_FIELDS, 'only registered rank-seven production fields may change')
    word = W.WordData(raw, attribution)
    need(word.helpers == original.helpers and word.v == original.v == 112,
         'unchanged ordered408 helper roles and112 ports')
    old_ends, new_ends = original.raw['helper_final'], raw['helper_final']
    need(len(old_ends) == 82 and len(new_ends) == 83 and
         all(new_ends.get(k) == value for k, value in old_ends.items()), 'all82 old endpoints retained plusone')
    added = set(new_ends)-set(old_ends)
    need(len(added) == 1, 'one new endpoint')
    helper = int(next(iter(added)))
    need(helper != 408 and helper in word.helpers and len(word.end[helper]) == 7 and
         len(word.start[helper]) == 0, 'fresh cold rank-seven endpoint; activehelper408 excluded')
    widths = [len(word.end[h])-len(word.start[h]) for h in word.helpers]
    old_widths = [len(original.end[h])-len(original.start[h]) for h in original.helpers]
    deltas = {h: widths[i]-old_widths[i] for i,h in enumerate(word.helpers) if widths[i] != old_widths[i]}
    need(deltas == {helper: -2}, 'only selected rank-nine to rank-seven helper width changes')
    paid, old_paid = _profile(word.paid), _profile(original.paid)
    mass, old_mass = _paid_mass(paid, widths), _paid_mass(old_paid, old_widths)
    need(mass == old_mass-2, 'one rank-seven extraction saves exactlytwo local massunits')
    return dict(provider=provider, paid_profile=paid, ordered_widths=widths,
                width_inventory=dict(Counter(widths)), buffers=len(new_ends), helper=helper,
                local_mass=mass, paid_profile_delta={r:paid.get(r,0)-old_paid.get(r,0)
                    for r in sorted(set(paid)|set(old_paid)) if paid.get(r,0)!=old_paid.get(r,0)},
                raw_semantic_sha256=hashlib.sha256(json.dumps(raw, sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                source_attribution=deepcopy(attribution),
                local_free_operator_and_native_admission='SEPARATE_REQUIRED')


def screen_task(spec):
    """spec={seed,words:{provider:{raw,attribution}},include_brackets?:bool}.

    This registered round requires both providers at one paired address. Their
    actual call counts are retained even when their paid profiles differ.
    """
    started = time.process_time()
    state, C = _state(), _module('ceiling')
    record = state['record']
    changes = spec['words']
    need(set(changes) == set(record['words']), 'both providers required by the bounded paired-address protocol')
    nominees = {pid: _candidate(pid, item['raw'], item['attribution']) for pid,item in changes.items()}
    aggregate, providers = Counter(), {}
    for pid, word in record['words'].items():
        if pid in nominees:
            providers[pid] = nominees[pid]
        else:
            widths = [len(word.end[h])-len(word.start[h]) for h in word.helpers]
            paid = _profile(word.paid)
            providers[pid] = dict(provider=pid, paid_profile=paid, ordered_widths=widths,
                width_inventory=dict(Counter(widths)), buffers=len(word.raw['helper_final']),
                local_mass=_paid_mass(paid,widths), unchanged_source=True,
                source_attribution=deepcopy(word.attribution))
        count = state['dispatch_counts'][pid]
        aggregate.update({r:n*count for r,n in providers[pid]['paid_profile'].items()})
    need(sum(state['dispatch_counts'].values()) == 666, 'literal666-call dispatch')
    buffers = max(p['buffers'] for p in providers.values())
    physical = _physical_stock(buffers, spec.get('physical_families', 66805))
    local = {r:Q(n,666) for r,n in aggregate.items()}
    total_mass = 72*66304+64*666
    need(total_mass == 4816512, 'fixed total coverage mass')
    need(max(cap for cap,start,stop in record['model'].win.values()) == 48,
         'unchanged template bins have maximum rank48')
    local_mass = sum(r*n for r,n in aggregate.items())
    endpoint = Q(state['target']['endpoint'])
    caps = []
    for rank_cap in (48,51):
        kwargs = dict(local=local,m=73,families=66304,stages=666,centre=64,R=rank_cap,unpaid=1)
        quantities = C.model(**kwargs)
        need(quantities['local_mass']*666 == local_mass and
             quantities['idle_mass']*666 == total_mass-local_mass, 'exact aggregate local/idle mass split')
        low,high = C.relax(**kwargs,a=endpoint)
        classification = ('OPTIMISTIC_CAP_ABOVE_TARGET' if high < 1 else
                          'NO_CAP_HEADROOM_AT_TARGET' if low >= 1 else 'UNRESOLVED_INTERVAL')
        report = dict(rank_cap=rank_cap, classification=classification,
            target_moment_lower=low,target_moment_upper=high,margin_above=low-1,margin_below=1-high,
            model=quantities, exact_coverage_mass=total_mass, aggregate_local_mass=local_mass,
            idle_mass=total_mass-local_mass)
        if spec.get('include_brackets',False):
            cap_low,cap_high = C.ceiling(**kwargs,grid=GRID)
            lo_m,hi_m = C.relax(**kwargs,a=cap_low),C.relax(**kwargs,a=cap_high)
            need(lo_m[1] < 1 < hi_m[0] and 0 < cap_high-cap_low <= GRID, 'exact nominee cap bracket')
            report.update(complex_cap_lower=cap_low,complex_cap_upper=cap_high,
                decimal_interval=[decimal(cap_low),decimal(cap_high)],grid=GRID,
                lower_endpoint_moment=lo_m,upper_endpoint_moment=hi_m,
                target_fraction_of_cap_interval=[endpoint/cap_high,endpoint/cap_low])
        caps.append(encode(report))
    primary = caps[0]['classification']
    status = ('PASS_OPTIMISTIC_LOCAL_COST_SCREEN' if primary == 'OPTIMISTIC_CAP_ABOVE_TARGET' else
              'NULL_OPTIMISTIC_CAP_NO_HEADROOM' if primary == 'NO_CAP_HEADROOM_AT_TARGET' else 'EXPLORATORY')
    return dict(status=status,seed=int(spec['seed']),target=deepcopy(state['target']),
        nominated_providers=sorted(nominees),providers=encode(providers),
        dispatch_counts=dict(state['dispatch_counts']),aggregate_paid_local_profile=dict(aggregate),
        per_call_rational_average=encode(local),physical_stock=dict(data_and_owner_families=66304,
            helpers=408,centres=8,private_zero_buffers=buffers,coefficient_work=2,total=physical),
        caps=caps,primary_rank_cap=48,fully_charged_local_profile=True,
        physical_stock_is_bound_not_fresh_native_invoice=True,
        source_attribution=deepcopy(record['model'].attributions),
        trusted_sources=dict(TRUSTED),solver_calls=0,n_permutations=0,
        cpu_seconds=time.process_time()-started,
        proof='For fixed aggregate paid-local histogram and total coverage mass, cost per unit idle mass decreases with rank at every positive saving. Fractional rank-R idle mass gives a rigorous optimistic lower moment. Its crossing upper-bounds every admissible packing under the stated rank cap.',
        heterogeneity_caveat='Exact actual provider dispatch is retained; candidate providers are not silently cloned into other calls. The rational average is justified by linearity in profile multiplicities, not by equality of provider words.',
        outer_relation='Compare complex endpoints directly. The obsolete a/(1+a) interpretation in the trusted ceiling source is not used.',
        scope='Necessary optimistic packing-cap screen only. An actual legal allocation, all-column word proof, fresh changed-word native/phase/wrapper replay, full83-buffer finite invoice, exact actual-profile moment and modern outer arithmetic remain required. No independent admission of the compared public claim is implied.')


def controls_task(seed):
    """Meaningful source-pin, width-mass and extra-buffer rejection controls."""
    started = time.process_time()
    state = _state()
    word = state['record']['words']['gauge44']
    paid = _profile(word.paid)
    widths = [len(word.end[h])-len(word.start[h]) for h in word.helpers]
    baseline_mass = _paid_mass(paid,widths)
    bad_widths = widths[:]
    bad_widths[0] -= 1
    wrong_pin = deepcopy(state['target_spec'])
    wrong_pin['source']['sha256'] = '0'*64
    probes = dict(wrong_width_mass=lambda:_paid_mass(paid,bad_widths),
                  uncharged_private_buffer=lambda:_physical_stock(83,66804),
                  incorrect_target_pin=lambda:_target(wrong_pin))
    controls = {}
    for label,check in probes.items():
        try:
            check()
        except (ValueError,AssertionError) as error:
            controls[label] = dict(rejected=True,reason=str(error))
        else:
            controls[label] = dict(rejected=False)
    need(all(x['rejected'] for x in controls.values()), 'all registered cap controls reject')
    return dict(status='PASS',seed=int(seed),baseline_paid_width_mass=baseline_mass,
        valid83buffer_stock=_physical_stock(83,66805),target=deepcopy(state['target']),
        controls=controls,solver_calls=0,n_permutations=0,cpu_seconds=time.process_time()-started,
        source_attribution=deepcopy(state['record']['model'].attributions),trusted_sources=dict(TRUSTED))
