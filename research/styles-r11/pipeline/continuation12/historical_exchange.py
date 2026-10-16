"""Registered historical exchange corpus; imported only after source freeze.

This is an outcome-label and predictive-screening experiment on three historical
allocations, not a search for another admitted construction. All S pairs have
positive capacity/spread geometry BEFORE window and family checks. A distinct
uniform sample covers the complement with known inclusion probability. The two
execution seeds reproduce one corpus, and never double its statistical size.

Only hash-pinned trusted local adapters are imported. Acquired PR files remain
inert data. All parallel execution belongs to the root's common pool.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import gc
import gzip
import hashlib
import importlib.util
import io
import json
import os
import random
import resource
import sys
import time
import zipfile

HERE = Path(__file__).resolve().parent
PKG = HERE.parent.parent
CALLS, HELPERS, SHARDS = 666, 408, 84
ROLES = CALLS * HELPERS
DOMAIN = CALLS * (CALLS - 1) // 2 * HELPERS ** 2
UNIFORM_N = 2 ** 20
ROW_CAP = 2_000_000
CORPUS_SEED = 120071
EXECUTION_SEEDS = (61001, 122011)
SOURCES = (2853, 2917, 2979)
TRUSTED = {
    'heldout': ('pipeline/heldout_data.py', '847bf478bff50cc42a42f540c9f0b22c78a970946b1e3665c682b856bbd32fcd'),
    'latest': ('pipeline/continuation/latest_fill.py', '16ae9a6e4d451525bb6b2e5ad19c62adce2d93c620d5beaa332fd2512a199461'),
    'source2979': ('pipeline/continuation06/source_fill.py', 'a0131e58fafe171a9dd3d3c9e4808d17d00c6805f0f64d7322dfb690c67a8696'),
    'fill': ('pipeline/fill.py', '9ca05b47016ddbbb4a6713c981932d63a6eaecdd27f3604fcfb66877f239fc4a'),
    'wordio': ('pipeline/wordio.py', 'a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4'),
}
CORE = (
    'call_gap', 'stage_gap', 'replica_gap',
    'window_length_A', 'window_length_B',
    'own_start_margin_A', 'own_start_margin_B',
    'own_stop_margin_A', 'own_stop_margin_B',
    'cross_start_margin_A', 'cross_start_margin_B',
    'cross_stop_margin_A', 'cross_stop_margin_B',
    'family_call_degree_A', 'family_call_degree_B',
    'bin_role_degree_A', 'bin_role_degree_B',
    'same_physical_family', 'same_bin', 'same_port',
    'same_child_family', 'same_helper', 'window_overlap_length',
)
MECHANISM = ('widthA', 'widthB', 'residualA', 'residualB', 'capacityA', 'capacityB')
PROTOCOL = dict(corpus_seed=CORPUS_SEED, execution_seeds=list(EXECUTION_SEEDS),
    sources=list(SOURCES), calls=CALLS, helpers=HELPERS, shards_per_source=SHARDS,
    uniform_n=UNIFORM_N, cross_call_domain=DOMAIN, row_cap_per_fill=ROW_CAP,
    uniform_algorithm='random.Random(int(SHA256(ASCII("CONT12-UNIFORM-v1:120071:<PR>")),16)).sample(range(D),N)',
    domain_order='Lexicographic call pair (ta<tb), then helperA, helperB; canonical role i=408*t+h.',
    S='Distinct bins, unequal widths, both post-swap capacities feasible, d*(ra-rb+d)>0; no window/family selection.',
    shards='Earlier canonical role call //8; all 84 shards, including empty shards, are recorded.',
    call_group_identity='stage*74+replica; stable physical call identity across historical chronological orders. core call_gap remains chronological.',
    pair_purge_identity='Canonical time/helper coordinates only; this sensitivity is not a physical role identity match when order or provider layouts differ.',
    inclusion_probability=dict(on_S='1', outside_S=f'{UNIFORM_N}/{DOMAIN}'),
    scientific_scope='Historical exact owner-exchange outcome prediction; no new construction or native/outer admission.',
    lineage_scope='All three fills share substantial word/template ancestry; held-source validation is not held-ancestry validation.')
_STATE = None
_OWN_MODULES = []
_NEW_MODULE_NAMES = set()


def need(condition, label):
    if not condition:
        raise ValueError(label)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def feature_schema():
    return dict(core=list(CORE), mechanism=list(MECHANISM),
        groups=['callA', 'callB', 'physical_familyA', 'physical_familyB', 'binA', 'binB'],
        labels=['legal', 'gain_sign', 'inS', 'uniform_selected'],
        baseline=['capacity_feasible', 'positive_spread', 'reciprocal_windows', 'half_square_gain'],
        call_group_encoding='stage*74+replica (not chronological call time)',
        gain_sign='For legal pairs only: +1 strict concave-moment improvement, 0 tie, -1 harm. Illegal gain_sign is 0.',
        core_scope='Prospective temporal/role/physical-graph descriptors; no widths, ranks, residuals, costs, labels or IDs.',
        mechanism_scope='Explicitly width/residual/capacity-derived comparator; not rank-free ML.',
        full_oracle='legal AND gain_sign==1; an exact diagnostic upper bound, not a trainable predictor.')


def source_manifest():
    result = {}
    for path, expected in TRUSTED.values():
        actual = hashlib.sha256((PKG / path).read_bytes()).hexdigest()
        need(actual == expected, 'trusted source drift: ' + path)
        result[path] = actual
    return result


def _load(key):
    relative, expected = TRUSTED[key]
    path = PKG / relative
    need(hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'trusted adapter hash: ' + key)
    name = 'styles_cont12_historical_' + key
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    _OWN_MODULES.append(mod)
    return mod


def _memory():
    rss = available = None
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('VmRSS:'):
            rss = int(line.split()[1]) * 1024
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            available = int(line.split()[1]) * 1024
    return dict(rss_bytes=rss, peak_rss_bytes=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024,
        available_bytes=available)


def _array_digest(arrays):
    h = hashlib.sha256(b'CONT12-ARRAYS-v1\0')
    for name in sorted(arrays):
        a = arrays[name]
        h.update(json.dumps([name, a.dtype.str, list(a.shape)], separators=(',', ':')).encode() + b'\0')
        if a.size:
            h.update(memoryview(a).cast('B'))
    return h.hexdigest()


def _build_index(model, pr, np):
    need(model.calls == CALLS and len(model.rows) == ROLES and model.ports == 112,
         'registered T74 source geometry')
    need(set(map(len, model.widths)) == {HELPERS} and model.expected_mass == 4816512,
         'complete canonical roles and rank mass')
    need(set(map(tuple, model.order)) == {(s, r) for s in range(9) for r in range(74)},
         'stable stage/replica call identity domain')
    need(set(model.family.values()) <= set(range(8)), 'physical family index range')
    rows = np.empty((ROLES, 6), dtype='<i4')
    original = np.full(ROLES, -1, dtype='<i4')
    widths = np.empty(ROLES, dtype='<i4')
    windows = np.empty((ROLES, 3), dtype='<i4')
    families = np.empty(ROLES, dtype='<i4')
    bins = np.empty(ROLES, dtype='<i4')
    child_families = np.empty(ROLES, dtype='<i4')
    used = [set() for _ in range(CALLS)]
    bin_rows, family_calls, bin_mass = defaultdict(list), defaultdict(set), Counter()
    for oi, raw in enumerate(model.rows):
        t, h, owner, child, port, offset = map(int, raw)
        need(0 <= t < CALLS and 0 <= h < HELPERS and 0 <= owner < 74 and 0 <= child < 32
             and 0 <= port < 112, 'bounded literal role coordinates')
        i = t * HELPERS + h
        need(original[i] == -1, 'unique canonical role')
        original[i], rows[i] = oi, raw
        width = int(model.widths[t][h])
        cap, start, stop = map(int, model.win[owner, child])
        family = owner * 896 + int(model.family[child]) * 112 + port
        bin_id = (owner * 32 + child) * 112 + port
        need(width > 0 and -1 <= start < t <= stop < CALLS and width <= cap,
             'literal width and current owner interval')
        need(family not in used[t], 'source physical-family injectivity')
        used[t].add(family)
        widths[i], windows[i], families[i], bins[i] = width, (cap, start, stop), family, bin_id
        child_families[i] = int(model.family[child])
        bin_rows[bin_id].append(i)
        bin_mass[bin_id] += width
        family_calls[family].add(t)
    need(bool(np.all(original >= 0)), 'complete canonical role index')
    residuals = np.asarray([int(windows[i, 0]) - bin_mass[int(bins[i])] for i in range(ROLES)], dtype='<i4')
    need(bool(np.all((residuals >= 0) & (residuals <= windows[:, 0]))), 'source bin capacities')
    family_degree = np.asarray([len(family_calls[int(f)]) for f in families], dtype='<i4')
    bin_degree = np.asarray([len(bin_rows[int(b)]) for b in bins], dtype='<i4')
    byte_count = (ROLES + 7) // 8
    group_bytes = {}
    for i in range(ROLES):
        key = int(widths[i]), int(residuals[i])
        if key not in group_bytes:
            group_bytes[key] = bytearray(byte_count)
        group_bytes[key][i >> 3] |= 1 << (i & 7)
    groups = {k: int.from_bytes(b, 'little') for k, b in group_bytes.items()}
    del group_bytes
    geometry = {}
    for a, ra, ca in set(zip(map(int, widths), map(int, residuals), map(int, windows[:, 0]))):
        bits = 0
        for (b, rb), mask in groups.items():
            d = a - b
            # For the higher-width owner d>0, rb-d<=capB is automatic from
            # source feasibility rb<=capB. The remaining tests are exactly
            # the two capacity constraints and positive squared spread.
            if d > 0 and d <= rb < ra + d and ra + d <= ca:
                bits |= mask
        geometry[a, ra, ca] = bits
    call_masks = tuple(((1 << HELPERS) - 1) << (t * HELPERS) for t in range(CALLS))
    # First count all S exactly, before allocating the S/corpus arrays.
    def mask_for(i):
        a, ra, ca = int(widths[i]), int(residuals[i]), int(windows[i, 0])
        bits = geometry[a, ra, ca] & ~call_masks[i // HELPERS]
        for j in bin_rows[int(bins[i])]:
            bits &= ~(1 << j)
        return bits
    s_count = sum(mask_for(i).bit_count() for i in range(ROLES))
    need(s_count <= ROW_CAP, f'incomplete: S population {s_count} exceeds registered cap {ROW_CAP} for {pr}')
    mem = _memory()
    projected_extra = (s_count + UNIFORM_N) * 64 + 256 * 1024 ** 2
    need(mem['available_bytes'] is not None and projected_extra < mem['available_bytes'] // 2,
         'incomplete: projected parent corpus memory is unavailable')
    s_codes = np.empty(s_count, dtype='<i8')
    pos = 0
    for i in range(ROLES):
        bits = mask_for(i)
        while bits:
            bit = bits & -bits
            j = bit.bit_length() - 1
            s_codes[pos] = min(i, j) * ROLES + max(i, j)
            pos += 1
            bits ^= bit
    need(pos == s_count, 'S count/materialization equality')
    s_codes.sort()
    need(s_count < 2 or bool(np.all(s_codes[1:] > s_codes[:-1])), 'unique S pair ownership')
    del groups, geometry, call_masks
    seed_text = f'CONT12-UNIFORM-v1:{CORPUS_SEED}:{pr}'
    rng_seed = int(hashlib.sha256(seed_text.encode('ascii')).hexdigest(), 16)
    rng = random.Random(rng_seed)
    uniform_domain = np.asarray(rng.sample(range(DOMAIN), UNIFORM_N), dtype='<i8')
    q, hp = np.divmod(uniform_domain, HELPERS ** 2)
    prefixes = np.asarray([t * (2 * CALLS - t - 1) // 2 for t in range(CALLS)], dtype='<i8')
    ta = np.searchsorted(prefixes, q, side='right') - 1
    tb = ta + 1 + q - prefixes[ta]
    ha, hb = np.divmod(hp, HELPERS)
    ia, ib = HELPERS * ta + ha, HELPERS * tb + hb
    need(bool(np.all((0 <= ta) & (ta < tb) & (tb < CALLS))), 'uniform exact domain unranking')
    uniform_codes = ia * ROLES + ib
    uniform_codes.sort()
    need(bool(np.all(uniform_codes[1:] > uniform_codes[:-1])), 'distinct uniform sample')
    codes = np.union1d(s_codes, uniform_codes)
    need(len(codes) <= ROW_CAP, f'incomplete: union population {len(codes)} exceeds registered row cap for {pr}')
    in_s = np.isin(codes, s_codes, assume_unique=True)
    in_u = np.isin(codes, uniform_codes, assume_unique=True)
    need(int(in_s.sum()) == s_count and int(in_u.sum()) == UNIFORM_N, 'all S and uniform members retained')
    shards = ((codes // ROLES) // HELPERS) // 8
    shard_indices = tuple(np.flatnonzero(shards == s).astype('<i4') for s in range(SHARDS))
    need(sum(map(len, shard_indices)) == len(codes), 'complete disjoint shard partition')
    source_digest = _array_digest(dict(rows=rows, widths=widths, windows=windows,
        families=families, bins=bins, residuals=residuals))
    corpus_digest = _array_digest(dict(pair_codes=codes, inS=in_s.astype('i1'), uniform_selected=in_u.astype('i1')))
    summary = dict(pr=pr, source_roles=ROLES, calls=CALLS, helpers=HELPERS,
        domain=DOMAIN, uniform_n=UNIFORM_N, S_population=s_count, union_rows=len(codes),
        uniform_intersection_S=s_count + UNIFORM_N - len(codes),
        uniform_seed_sha256=hashlib.sha256(seed_text.encode('ascii')).hexdigest(),
        source_arrays_sha256=source_digest, corpus_pair_sha256=corpus_digest,
        shard_rows=[len(x) for x in shard_indices], source_expected_profile=model.expected_profile,
        source_expected_mass=model.expected_mass, normalized_live=66304,
        model_scope='Historical T74 base_model only; unused T370 lift is never included in corpus.',
        memory_projection=dict(before_corpus=mem, extra_bytes=projected_extra),
        sampling=dict(D=DOMAIN, n=UNIFORM_N, S=s_count, pi_S='1', pi_outside_S=f'{UNIFORM_N}/{DOMAIN}'))
    return dict(model=model, pr=pr, rows=rows, original=original, widths=widths, windows=windows,
        families=families, bins=bins, residuals=residuals, used=tuple(frozenset(x) for x in used),
        family_degree=family_degree, bin_degree=bin_degree, child_families=child_families,
        order=np.asarray(model.order, dtype='<i4'), codes=codes, in_s=in_s, in_u=in_u,
        shard_indices=shard_indices, summary=summary)


def prepare(protocol=None):
    """Parent-only registered preparation; does not launch parallel jobs."""
    global _STATE, _NEW_MODULE_NAMES
    if _STATE is not None:
        return deepcopy(_STATE['summary'])
    protocol = {} if protocol is None else deepcopy(protocol)
    need(not sys.flags.optimize, 'assertions enabled')
    if 'sources' in protocol:
        need(tuple(map(int, protocol['sources'])) == SOURCES, 'fixed registered source list')
    before_names = set(sys.modules)
    started = time.process_time()
    pins = source_manifest()
    import numpy as np
    sys.dont_write_bytecode = True
    held = _load('heldout'); held.prepare(prs=(2853,))
    latest = _load('latest'); latest.prepare(pr=2917)
    before2979 = _memory()
    newer = _load('source2979'); newer.prepare()
    after2979 = _memory()
    hrec = held.RECORDS['2853']
    need(hrec.get('prepare_error') is None, 'PR2853 trusted inert adapter prepared')
    recs = {2853: hrec['model'], 2917: latest.get_record()['model'], 2979: newer.get_state()['base_model']}
    provenance = {2853: held.provenance(2853), 2917: latest.provenance(), 2979: newer.provenance()}
    indices = {pr: _build_index(recs[pr], pr, np) for pr in SOURCES}
    output = protocol.get('_runtime_data_path', 'data/continuation-12/ml4-v1')
    output_path = (PKG / output).resolve() if not Path(output).is_absolute() else Path(output).resolve()
    need(output_path.is_relative_to((PKG / 'data/continuation-12').resolve()), 'new CONT12 output confinement')
    _NEW_MODULE_NAMES = set(sys.modules) - before_names
    summary = dict(status='PREPARED', protocol=PROTOCOL, sources=[indices[p]['summary'] for p in SOURCES],
        feature_schema=feature_schema(), trusted_sources=pins, provenance=provenance,
        sampling_is_outcome_enriched=True, weighting_required=True,
        confirmatory_seeds_are_repeated_computation=True, expected_generation_tasks=3*84*2,
        adapter_memory=dict(PR2979_before=before2979, PR2979_after=after2979,
            unused_T370_lift_roles_loaded=len(newer.get_state()['model'].rows),
            historical_T74_roles_used=len(newer.get_state()['base_model'].rows),
            note='The trusted CONT06 loader also materializes 1,358,640 unused T370 roles. They remain parent/COW cache until release_generation_state; high-water RSS includes them.'),
        preparation_cpu_seconds=time.process_time()-started, parent_memory=_memory())
    _STATE = dict(np=np, indices=indices, provenance=provenance, summary=summary,
        output=output_path / 'numeric', fill=held._modules()[0], protocol=protocol)
    return deepcopy(summary)


def _state():
    need(_STATE is not None, 'prepare once in parent before tasks')
    return _STATE


def generation_specs(seed, batch_index=0):
    _state()
    need(int(seed) in EXECUTION_SEEDS and int(batch_index) == 0, 'registered generation seed/batch')
    specs = [dict(kind='generation', pr=pr, source=pr, shard=s, seed=int(seed))
             for pr in SOURCES for s in range(SHARDS)]
    random.Random(int(seed)).shuffle(specs)
    return specs


def _labels(x, ia, ib, np):
    ta, tb = ia // HELPERS, ib // HELPERS
    a, b = x['widths'][ia], x['widths'][ib]
    ra, rb = x['residuals'][ia], x['residuals'][ib]
    ca, sa, ea = x['windows'][ia].T
    cb, sb, eb = x['windows'][ib].T
    same_bin = x['bins'][ia] == x['bins'][ib]
    d = a - b
    score = (d * (ra-rb+d)).astype('<i8')
    score[same_bin] = 0
    capacity = same_bin | ((0 <= ra+d) & (ra+d <= ca) & (0 <= rb-d) & (rb-d <= cb))
    windows = (sa < tb) & (tb <= ea) & (sb < ta) & (ta <= eb)
    fa, fb = x['families'][ia], x['families'][ib]
    family = np.fromiter((int(f) == int(g) or
        (int(g) not in x['used'][int(t)] and int(f) not in x['used'][int(u)])
        for t, u, f, g in zip(ta, tb, fa, fb)), dtype=bool, count=len(ia))
    legal = capacity & windows & family
    sign = np.sign(score).astype('i1')
    sign[~legal] = 0
    return dict(legal=legal, sign=sign, capacity=capacity, windows=windows,
        family=family, score=score, positive=score > 0, same_bin=same_bin)


def _numeric_rows(x, indices, np):
    codes = x['codes'][indices]
    ia, ib = np.divmod(codes, ROLES)
    ta, tb = ia // HELPERS, ib // HELPERS
    ca, sa, ea = x['windows'][ia].T
    cb, sb, eb = x['windows'][ib].T
    l = _labels(x, ia, ib, np)
    in_s = x['in_s'][indices]
    need(bool(np.all(in_s == (l['capacity'] & l['positive'] & ~l['same_bin']))),
         'S labels use only declared capacity/spread/bin geometry')
    features = [tb-ta, np.abs(x['order'][ta, 0]-x['order'][tb, 0]),
        np.abs(x['order'][ta, 1]-x['order'][tb, 1]),
        ea-sa, eb-sb, ta-sa, tb-sb, ea-ta, eb-tb,
        tb-sa, ta-sb, ea-tb, eb-ta,
        x['family_degree'][ia], x['family_degree'][ib], x['bin_degree'][ia], x['bin_degree'][ib],
        x['families'][ia] == x['families'][ib], l['same_bin'], x['rows'][ia, 4] == x['rows'][ib, 4],
        x['child_families'][ia] == x['child_families'][ib], ia % HELPERS == ib % HELPERS,
        np.maximum(0, np.minimum(ea, eb)-np.maximum(sa, sb))]
    arrays = dict(pairs=np.column_stack((ia, ib)).astype('<i4'),
        groups=np.column_stack((x['order'][ta, 0]*74+x['order'][ta, 1],
            x['order'][tb, 0]*74+x['order'][tb, 1],
            x['families'][ia], x['families'][ib], x['bins'][ia], x['bins'][ib])).astype('<i4'),
        labels=np.column_stack((l['legal'], l['sign'], in_s, x['in_u'][indices])).astype('i1'),
        baseline=np.column_stack((l['capacity'], l['positive'], l['windows'], l['score'])).astype('<i8'),
        core_features=np.column_stack(features).astype('<i4'),
        mechanism_features=np.column_stack((x['widths'][ia], x['widths'][ib],
            x['residuals'][ia], x['residuals'][ib], ca, cb)).astype('<i4'))
    counts = dict(rows=len(codes), S=int(in_s.sum()), uniform_selected=int(x['in_u'][indices].sum()),
        uniform_intersection_S=int((in_s & x['in_u'][indices]).sum()),
        legal_positive=int((l['legal'] & (l['sign'] == 1)).sum()),
        legal_tie=int((l['legal'] & (l['sign'] == 0)).sum()),
        legal_harm=int((l['legal'] & (l['sign'] == -1)).sum()),
        illegal_capacity=int((~l['capacity']).sum()),
        illegal_window=int((l['capacity'] & ~l['windows']).sum()),
        illegal_family=int((l['capacity'] & l['windows'] & ~l['family']).sum()),
        same_bin=int(l['same_bin'].sum()), equal_width=int((x['widths'][ia] == x['widths'][ib]).sum()))
    need(sum(counts[k] for k in ('legal_positive', 'legal_tie', 'legal_harm',
        'illegal_capacity', 'illegal_window', 'illegal_family')) == len(codes), 'complete exact label partition')
    return arrays, counts


def _write_npz(path, arrays, np):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(arrays):
            data = io.BytesIO()
            np.lib.format.write_array(data, arrays[name], allow_pickle=False)
            info = zipfile.ZipInfo(name + '.npy', date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data.getvalue(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    raw = out.getvalue()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        need(path.read_bytes() == raw, 'immutable numeric artifact collision')
    else:
        with path.open('xb') as stream:
            stream.write(raw)
    return dict(path=str(path.relative_to(PKG)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def generate(spec):
    started = time.process_time()
    state = _state(); np = state['np']
    pr = int(spec.get('pr', spec.get('source')))
    shard, seed = int(spec['shard']), int(spec['seed'])
    need(pr in SOURCES and seed in EXECUTION_SEEDS and 0 <= shard < SHARDS, 'registered generation task')
    x = state['indices'][pr]
    indices = x['shard_indices'][shard]
    # A different traversal is confirmed, but stored arrays have canonical order.
    traversal = indices.copy()
    random.Random(seed ^ (pr << 12) ^ shard).shuffle(traversal)
    order = np.argsort(x['codes'][traversal], kind='stable')
    indices = traversal[order]
    need(bool(np.array_equal(indices, x['shard_indices'][shard])), 'canonical output independent of schedule seed')
    feature_started = time.process_time()
    arrays, counts = _numeric_rows(x, indices, np)
    feature_seconds = time.process_time()-feature_started
    semantic = _array_digest(arrays)
    artifact = _write_npz(state['output'] / f'seed-{seed}' / f'pr-{pr}-shard-{shard:03d}.npz', arrays, np)
    return dict(status='PASS', pr=pr, source=pr, shard=shard, seed=seed,
        artifact=artifact, counts=counts, semantic_digest=semantic, corpus_semantic_sha256=semantic,
        source_arrays_sha256=x['summary']['source_arrays_sha256'],
        corpus_pair_sha256=x['summary']['corpus_pair_sha256'],
        feature_schema=feature_schema(), sampling=x['summary']['sampling'],
        array_schema={k: dict(dtype=a.dtype.str, shape=list(a.shape)) for k, a in arrays.items()},
        source_attribution=x['model'].attributions,
        feature_and_label_cpu_seconds=feature_seconds, cpu_seconds=time.process_time()-started,
        scope=PROTOCOL['scientific_scope'])


def _scalar_label(x, i, j):
    """Independent set-based guard calculation used only by registered controls."""
    ta, tb = i // HELPERS, j // HELPERS
    need(ta != tb, 'cross-call control domain')
    a, b, ra, rb = (int(x[k][z]) for k, z in [('widths', i), ('widths', j), ('residuals', i), ('residuals', j)])
    ca, sa, ea = map(int, x['windows'][i]); cb, sb, eb = map(int, x['windows'][j])
    same = int(x['bins'][i]) == int(x['bins'][j])
    nra, nrb = (ra, rb) if same else (ra+a-b, rb-a+b)
    fa, fb = int(x['families'][i]), int(x['families'][j])
    f1, f2 = set(x['used'][ta]), set(x['used'][tb])
    f1.remove(fa); f2.remove(fb)
    okay = (0 <= nra <= ca and 0 <= nrb <= cb and sa < tb <= ea and sb < ta <= eb
            and fb not in f1 and fa not in f2)
    score = 0 if same else (nra*nra+nrb*nrb-ra*ra-rb*rb)//2
    return okay, (1 if score > 0 else -1 if score < 0 else 0) if okay else 0


def _swapped_rows(x, i, j, fill):
    rows = [list(r) for r in x['model'].rows]
    oi, oj = int(x['original'][i]), int(x['original'][j])
    rows[oi][2:5], rows[oj][2:5] = rows[oj][2:5], rows[oi][2:5]
    return fill.compact_rows(x['model'], [row[:5] for row in rows])


def controls(seed):
    started = time.process_time()
    state = _state(); np, fill = state['np'], state['fill']
    seed = int(seed['seed'] if isinstance(seed, dict) else seed)
    need(seed in EXECUTION_SEEDS, 'registered control seed')
    checks, baselines, literal = [], {}, []
    for pr in SOURCES:
        x = state['indices'][pr]
        audit = fill.audit(x['model'])
        need(audit['profile'] == x['model'].expected_profile, 'source exact local+idle profile audit')
        baselines[str(pr)] = dict(profile=audit['profile'], rank_mass=x['model'].expected_mass,
            source_arrays_sha256=x['summary']['source_arrays_sha256'])
        # Fixed representative pairs are selected before inspecting any outcomes.
        pairs = [divmod(int(c), ROLES) for c in x['codes'][:4]]
        if pr == 2917:
            pairs.append((56, 62*HELPERS+184))
        for i, j in pairs:
            label = _labels(x, np.asarray([i]), np.asarray([j]), np)
            independent = _scalar_label(x, i, j)
            need((bool(label['legal'][0]), int(label['sign'][0])) == independent,
                 'vectorized label equals independent scalar/set predicate')
            try:
                candidate = fill.audit(x['model'], rows=_swapped_rows(x, i, j, fill), require_profile=False)
                admitted = True
            except (ValueError, AssertionError):
                admitted = False; candidate = None
            need(admitted == independent[0], 'exact swap label equals independent literal full-fill audit')
            if admitted:
                delta = Counter(candidate['profile']); delta.subtract(x['model'].expected_profile)
                delta = {int(r): int(n) for r, n in sorted(delta.items()) if n}
                need(sum(r*n for r, n in delta.items()) == 0, 'literal complete profile delta is mass neutral')
                ia, ib = int(x['bins'][i]), int(x['bins'][j])
                expected = Counter()
                if ia != ib:
                    a, b, ra, rb = (int(x[k][z]) for k, z in [('widths', i), ('widths', j), ('residuals', i), ('residuals', j)])
                    for r, n in ((ra, -1), (rb, -1), (ra+a-b, 1), (rb-a+b, 1)):
                        if r: expected[r] += n
                need(delta == {r: n for r, n in sorted(expected.items()) if n}, 'complete literal profile equals two-bin exact delta')
                if pr == 2917 and (i, j) == (56, 62*HELPERS+184):
                    need(independent == (True, 1) and delta == {5: 1, 6: -1, 7: -1, 8: 1},
                         'known admitted CONT01 witness reproduces exact delta')
            literal.append(dict(pr=pr, pair=[i, j], legal=independent[0], gain_sign=independent[1]))
        # These source tamper controls are rejected by the independent audit.
        tampered = [tuple(r) for r in x['model'].rows]
        r = list(tampered[0]); r[5] = -1; tampered[0] = tuple(r)
        rejected = False
        try: fill.audit(x['model'], rows=tampered, require_profile=False)
        except (ValueError, AssertionError): rejected = True
        need(rejected, 'negative literal offset rejected')
        checks.append(f'{pr}:source/profile/swap/negative-offset')
    # Independent tiny simultaneous-family fixtures: remove the outgoing
    # identities before insertion. Same physical family is a legal replacement.
    def family_ok(old_a, old_b, fa, fb):
        aa, bb = set(old_a), set(old_b)
        aa.remove(fa); bb.remove(fb)
        return fb not in aa and fa not in bb
    need(family_ok({3, 7}, {3, 9}, 3, 3), 'same-family simultaneous replacement positive')
    need(not family_ok({3, 7}, {5, 7}, 3, 7), 'incoming duplicate-family negative')
    need(family_ok({3, 7}, {5, 9}, 3, 5), 'different absent-family positive')
    checks.extend(['simultaneous-same-family', 'duplicate-family-rejected', 'different-family'])
    # Small fresh geometry fixtures exercise the production vectorized label
    # path, with an independent remove/insert set calculation as its oracle.
    def toy(a=9, b=8, ra=7, rb=6, same_bin=False, window_bad=False, family_bad=False):
        n = 2 * HELPERS
        xx = dict(widths=np.ones(n, dtype='<i4'), residuals=np.zeros(n, dtype='<i4'),
            windows=np.tile(np.asarray([48, -1, 1], dtype='<i4'), (n, 1)),
            families=np.zeros(n, dtype='<i4'), bins=np.zeros(n, dtype='<i4'),
            used=(frozenset({10, 20} | ({11} if family_bad else set())),
                  frozenset({10 if same_bin else 11, 30})))
        xx['widths'][0], xx['widths'][HELPERS] = a, b
        xx['residuals'][0], xx['residuals'][HELPERS] = ra, rb
        xx['families'][0], xx['families'][HELPERS] = 10, 10 if same_bin else 11
        xx['bins'][0], xx['bins'][HELPERS] = 100, 100 if same_bin else 101
        if window_bad: xx['windows'][HELPERS, 1] = 0
        return xx
    fixtures = [('strict-gain', toy(), (True, 1)),
        ('strict-harm', toy(ra=5, rb=8), (True, -1)),
        ('equal-width-legal-tie', toy(a=9, b=9), (True, 0)),
        ('same-bin-unequal-legal-tie', toy(same_bin=True, ra=7, rb=7), (True, 0)),
        ('capacity-rejection', toy(rb=0), (False, 0)),
        ('reciprocal-window-rejection', toy(window_bad=True), (False, 0)),
        ('simultaneous-family-rejection', toy(family_bad=True), (False, 0))]
    for name, xx, expected in fixtures:
        for i, j in ((0, HELPERS), (HELPERS, 0)):
            independent = _scalar_label(xx, i, j)
            actual = _labels(xx, np.asarray([i]), np.asarray([j]), np)
            need(independent == expected == (bool(actual['legal'][0]), int(actual['sign'][0])),
                 'independent exact synthetic label: ' + name)
        checks.append('synthetic-both-orientations:' + name)
    # Synthetic ties and strict changes include equal widths and one shared bin;
    # the latter must not be treated as two independent bins.
    need((9-9)*(7-6+9-9) == 0, 'equal-width profile tie')
    need((8*8+5*5-7*7-6*6)//2 == 2, 'independent squared residual gain')
    need(sum(r*n for r, n in {5: 1, 6: -1, 7: -1, 8: 1}.items()) == 0, 'mass-neutral witness')
    need({5: 1, 6: -1, 7: -1, 8: 1} != {5: -1, 6: 1, 7: 1, 8: -1}, 'wrong signed profile rejected')
    need(Fraction(UNIFORM_N, DOMAIN) < 1 and Fraction(1) != Fraction(UNIFORM_N, DOMAIN), 'nonuniform inclusion weights retained')
    checks.extend(['equal-width-tie', 'squared-gain-independent', 'mass-neutral', 'wrong-sign', 'sampling-weights'])
    return dict(status='PASS', seed=seed, checks=checks, check_count=len(checks),
        baseline_profiles=baselines, literal_pair_controls=literal,
        feature_schema=feature_schema(), trusted_sources=source_manifest(),
        cpu_seconds=time.process_time()-started,
        scope='Exact historical owner/profile label controls; no new supplier/native/outer admission.')


def _summary_from_record(record):
    return record.get('summary', record.get('result', record))


def summarize_generation(manifest_records):
    state = _state()
    bykey = {}
    for record in manifest_records:
        row = _summary_from_record(record)
        need(row.get('status') == 'PASS', 'all generation receipts passed')
        key = int(row.get('pr', row.get('source'))), int(row['shard']), int(row['seed'])
        need(key not in bykey, 'unique source/shard/seed receipt')
        bykey[key] = row
    need(set(bykey) == {(p, s, seed) for p in SOURCES for s in range(SHARDS) for seed in EXECUTION_SEEDS},
         'complete 504 generation task coverage')
    summaries = {}
    for pr in SOURCES:
        counts = Counter()
        semantic_rows = []
        for shard in range(SHARDS):
            a, b = (bykey[pr, shard, seed] for seed in EXECUTION_SEEDS)
            need(a['corpus_semantic_sha256'] == b['corpus_semantic_sha256'] and a['counts'] == b['counts'],
                 'second execution seed confirms the same exact corpus and labels')
            counts.update(a['counts'])
            semantic_rows.append([shard, a['corpus_semantic_sha256']])
        base = state['indices'][pr]['summary']
        need(counts['rows'] == base['union_rows'] and counts['S'] == base['S_population']
             and counts['uniform_selected'] == UNIFORM_N, 'generation equals full prepared stratified corpus')
        summaries[str(pr)] = dict(counts=dict(counts), sampling=base['sampling'],
            corpus_semantic_sha256=digest(semantic_rows),
            source_arrays_sha256=base['source_arrays_sha256'], confirmed_identical=True)
    return dict(status='PASS', confirmed=True, sources=summaries, completed_tasks=len(bykey),
        unique_rows=sum(v['counts']['rows'] for v in summaries.values()),
        repeated_computation_rows=2*sum(v['counts']['rows'] for v in summaries.values()),
        confirmation_is_not_additional_sample=True, feature_schema=feature_schema(),
        scope=PROTOCOL['scientific_scope'])


def release_generation_state():
    """Discard only this run's parent allocations after workers have exited."""
    global _STATE, _OWN_MODULES, _NEW_MODULE_NAMES
    _STATE = None
    owned = set(id(m) for m in _OWN_MODULES)
    # Removing cache references changes no source file or scientific result.
    # Newly loaded private r11 modules are not shared with pre-existing imports.
    removed = []
    for name in list(_NEW_MODULE_NAMES):
        module = sys.modules.get(name)
        if module is None: continue
        filename = str(getattr(module, '__file__', ''))
        if id(module) in owned or ('styles_' in name and filename.startswith(str(PKG / 'pipeline'))):
            removed.append(name); sys.modules.pop(name, None)
    _OWN_MODULES = []
    _NEW_MODULE_NAMES = set()
    gc.collect()
    return dict(status='RELEASED', private_modules_unreferenced=sorted(removed), memory=_memory())
