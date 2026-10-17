"""Two ordered rank-two factors with independent nested residual-read frames.

The original R2 production and all frozen scientific sources remain unchanged.
This module privately reuses its scalar domain, exact gathers, whole-window
invoice, and materialization. Forty labeled corners optimize X<=Y<=P<=Q<=Z;
forty more use the exact reverse/inverse orthogonal-complement chain. No scientific preparation
or control is performed at import time. Native/physical/outer admission remains
separate from a favorable recursive tariff.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import hashlib
import importlib.util
import itertools
from pathlib import Path
import random
import sys
import time

RR = Path(__file__).resolve().parents[2]
BASE_PATH = RR / 'pipeline/continuation12/rank2_carrier.py'
BASE_SHA256 = 'ab39e50db72b8191e5cac65388511d8ed76927c79760a894fcb404872c3a877a'
JOINT_PATH = RR / 'pipeline/continuation09/shared_carrier.py'
JOINT_SHA256 = '6c8b9b40bdfabf575f5f4b687541cbd3a20f5c10d44720b95c12dfc5e1570c47'
MAX_PACKETS = 12_500
MAX_LABELS = 8_000_000
SHARDS = 192
AMBIENT = 9
FRAME_CLASSES = ('FORWARD_MATCHED', 'FORWARD_SPLIT', 'REVERSE_MATCHED', 'REVERSE_SPLIT')
SCOPE = ('Exact rank-two 4-to-5 production in two explicit ordered chains: '
         'carrier-first u-j,v-j,v-k and reverse-chain v-k,v-j,u-j, forty '
         'fixed-exterior corner labels each. No arbitrary middle ordering, '
         'native, full-allocation or kappa claim.')
DOMINANCE = ('The old ordinary-exit argument required P=Q. Undoing at P when '
             'P<Q introduces a k contact before Q, so that matched-frame '
             'comparison is not applied to split residual reads. No global '
             'optimality or distinctness from broad covector work is claimed.')
_K = _J = _BASE_CANDIDATE = None
_WORDS = {}
_INSTALLED_HASHES = {}
_SHARD_GROUPS = {}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def _load(path, expected, name):
    need(hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'frozen utility hash: ' + str(path))
    need(name not in sys.modules, 'private utility module name already occupied')
    need(not sys.flags.optimize, 'scientific assertions enabled')
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _joint():
    global _J
    if _J is None:
        _J = _load(JOINT_PATH, JOINT_SHA256, 'styles14_split_frozen_joint')
    return _J


def _kernel():
    global _K, _BASE_CANDIDATE, _WORDS
    if _K is None:
        _K = _load(BASE_PATH, BASE_SHA256, 'styles14_split_frozen_rank2')
        # These hooks belong only to this newly loaded private instance. The
        # original matched replacement and original controls stay untouched.
        _K._joint = _joint
        _BASE_CANDIDATE = _K._candidate
        _K._candidate = _candidate
        _K._screen = _screen
        _K.MAX_PACKETS = MAX_PACKETS
        _K.MAX_LABELS = MAX_LABELS
        _K.SCOPE = SCOPE
        _K.DOMINANCE = DOMINANCE
        _WORDS = _K._WORDS
    return _K


def digest(value):
    return _kernel().digest(value)


def prepare(records, endpoint, domains=None):
    K = _kernel()
    summary = K.prepare(records, endpoint, domains)
    need(all(state['canonical'].h == AMBIENT for state in K._WORDS.values()),
         'source orthogonal-complement ambient is exactly nine')
    summary.update(matched_residual_read_frame=False, corners_per_choice=80,
                   forward_matched_control_labels=20, forward_split_labels=20,
                   reverse_matched_labels=20, reverse_split_labels=20,
                   reverse_matched_scope='New reverse order, not an inherited negative control',
                   shards_per_provider=SHARDS, scope=SCOPE,
                   ordinary_source_exit_dominance=DOMINANCE,
                   utility_source=dict(path=str(BASE_PATH.relative_to(RR)), sha256=BASE_SHA256),
                   joint_utility_source=dict(path=str(JOINT_PATH.relative_to(RR)), sha256=JOINT_SHA256))
    return summary


def _candidate(state, compact):
    K = _kernel()
    address = K._address(compact)
    need(len(address) == 10 and type(address[-1]) is int and 0 <= address[-1] < 80,
         'registered eighty-corner address')
    reduced = deepcopy(compact)
    if not isinstance(reduced, dict):
        reduced = dict(address=address)
    reduced['address'] = [*address[:-1], address[-1] % 20]
    reduced['candidate_id'] = K._cid(reduced['address'])
    candidate = _BASE_CANDIDATE(state, reduced)
    candidate.update(address=address, candidate_id=K._cid(address), pair_key=K._cid(address),
                     corner=address[-1], frame_class=FRAME_CLASSES[address[-1] // 20],
                     production_order='carrier_first' if address[-1] < 40 else 'reverse_chain')
    return candidate


def _forward_frames(boundaries, corner):
    """Complete fixed-exterior flag minimum; no equal-rank frame substitution."""
    need(type(corner) is int and 0 <= corner < 40, 'forty labels')
    J = _joint()
    U = J._U()
    E = {r: U._basis(v['entry']) for r, v in boundaries.items()}
    O = {r: U._basis(v['exit']) for r, v in boundaries.items()}
    L = U._join(E['j'], E['k'])
    A1 = U._join(L, E['i1'])
    A2 = U._join(A1, E['i2'])
    D = U._meet(O['j'], O['k'])
    U2 = U._meet(D, O['i2'])
    U1 = U._meet(U2, O['i1'])
    K, V = U._meet(A2, U1), U._join(A2, U1)
    f = dict(L=L, A1=A1, A2=A2, D=D, U1=U1, U2=U2, K=K, J=V)
    vertex, x, z = J.CORNERS[corner % 20]
    lower, upper = J.MIDDLE_VERTICES[vertex]
    f['Y1'], f['P'] = f[lower], f[upper]
    f['Y2'] = f['P']  # Legacy proof-field alias; the second v read uses Q.
    f['Q'] = f['P'] if corner < 20 else U2
    f['X'] = f[x]
    f['Z'] = f['Q'] if z == 'Y2' else D
    failed = []
    for low, high in (('A1', 'U1'), ('A2', 'U2'), ('L', 'X'), ('X', 'Y1'),
                      ('A1', 'Y1'), ('Y1', 'U1'), ('Y1', 'P'), ('A2', 'P'),
                      ('P', 'Q'), ('Q', 'U2'), ('Q', 'Z'), ('Z', 'D')):
        if not U._leq(f[low], f[high]):
            failed.append(dict(predicate='frame_inclusion', lower=low, upper=high,
                               lower_frame=list(f[low]), upper_frame=list(f[high]),
                               excluded_vector=next(v for v in f[low] if not U._leq((v,), f[high]))))
    final = dict(i1=f['Y1'], i2=f['Q'], j=f['Z'], k=f['Z'])
    for r in ('i1', 'i2', 'j', 'k'):
        if not U._leq(final[r], O[r]):
            failed.append(dict(predicate='exit_inclusion', register=r, actual=list(final[r]),
                               required=list(O[r]),
                               excluded_vector=next(v for v in final[r] if not U._leq((v,), O[r]))))
        if boundaries[r]['equality_exit'] and final[r] != O[r]:
            failed.append(dict(predicate='exit_equality', register=r,
                               actual=list(final[r]), required=list(O[r])))
    return f, failed


@lru_cache(maxsize=32768)
def _perp_cached(frame, ambient):
    """Exact GF(2) nullspace, independently annihilation/rank checked."""
    need(type(ambient) is int and 1 <= ambient <= 9, 'registered ambient dimension')
    need(all(type(v) is int and 0 <= v < (1 << ambient) for v in frame), 'ambient vector range')
    U = _joint()._U()
    rows = list(U._basis(frame))
    pivots, at = [], 0
    for col in range(ambient):
        found = next((i for i in range(at, len(rows)) if (rows[i] >> col) & 1), None)
        if found is None:
            continue
        rows[at], rows[found] = rows[found], rows[at]
        for i in range(len(rows)):
            if i != at and ((rows[i] >> col) & 1):
                rows[i] ^= rows[at]
        pivots.append(col)
        at += 1
    answer = []
    for free in range(ambient):
        if free in pivots:
            continue
        vector = 1 << free
        for row, pivot in zip(rows, pivots):
            if (row >> free) & 1:
                vector ^= 1 << pivot
        answer.append(vector)
    answer = U._basis(answer)
    need(len(answer) + len(U._basis(frame)) == ambient, 'orthogonal dimension complement')
    need(all((x & y).bit_count() % 2 == 0 for x in frame for y in answer), 'exact annihilator')
    return answer


def _perp(frame, ambient=AMBIENT):
    return _perp_cached(tuple(_joint()._U()._basis(frame)), ambient)


def _frames(boundaries, corner, ambient=AMBIENT):
    need(type(corner) is int and 0 <= corner < 80, 'eighty labeled corners')
    if corner < 40:
        return _forward_frames(boundaries, corner)
    # Reverse/invert the factor of the inverse scalar map. Original exit
    # equalities become first-touch lower faces in the transformed domain;
    # they are NOT transformed exit equalities. The actual original chain
    # below checks these exact faces after taking orthogonal complements.
    transformed = {r: dict(entry=list(_perp(v['exit'], ambient)),
                           exit=list(_perp(v['entry'], ambient)), equality_exit=False)
                   for r, v in boundaries.items()}
    prime, failures = _forward_frames(transformed, corner - 40)
    f = {'prime_' + key: value for key, value in prime.items()}
    f.update(X=_perp(prime['Z'], ambient), Q=_perp(prime['Q'], ambient),
             P=_perp(prime['P'], ambient), Y1=_perp(prime['Y1'], ambient),
             Z=_perp(prime['X'], ambient))
    f['Y2'] = f['P']
    if failures:
        return f, [dict(item, transformed_inverse_domain=True) for item in failures]
    U = _joint()._U()
    first = dict(i1=f['Y1'], i2=f['Q'], j=f['X'], k=f['X'])
    final = dict(i1=f['Y1'], i2=f['P'], j=f['Z'], k=f['Z'])
    for low, high in (('X', 'Q'), ('Q', 'P'), ('P', 'Y1'), ('Y1', 'Z')):
        if not U._leq(f[low], f[high]):
            failures.append(dict(predicate='reverse_frame_inclusion', lower=low, upper=high,
                                 lower_frame=list(f[low]), upper_frame=list(f[high])))
    for r, boundary in boundaries.items():
        E, O = U._basis(boundary['entry']), U._basis(boundary['exit'])
        if not U._leq(E, first[r]):
            failures.append(dict(predicate='entry_inclusion', register=r, actual=list(first[r]), required=list(E)))
        if not U._leq(final[r], O):
            failures.append(dict(predicate='exit_inclusion', register=r, actual=list(final[r]), required=list(O)))
        if boundary['equality_exit'] and final[r] != O:
            failures.append(dict(predicate='exit_equality', register=r, actual=list(final[r]), required=list(O),
                                 transformed_constraint='first_touch_lower_face'))
    return f, failures


def _replacement(candidate, frames):
    K = _kernel()
    c = candidate['chain']
    u, v, j, k = (c[n] for n in ('i1', 'i2', 'j', 'k'))
    q, a, b, e = (Q(c[n]) for n in ('ratio', 'a1', 'a2', 'residual'))
    if candidate.get('corner', 0) < 40:
        middle = [K._gate(u, j, a, frames['Y1']), K._gate(v, j, b, frames['P']),
                  K._gate(v, k, e, frames['Q'])]
    else:
        middle = [K._gate(v, k, e, frames['Q']), K._gate(v, j, b, frames['P']),
                  K._gate(u, j, a, frames['Y1'])]
    return [K._gate(j, k, q, frames['X']), *middle, K._gate(j, k, -q, frames['Z'])]


def _screen(context, candidate, detailed=False):
    K = _kernel()
    result = dict(candidate_id=candidate['candidate_id'], status='REJECTED_GUARD')
    if not context['fixed_bill']['valid']:
        result['guard_failures'] = context['fixed_bill']['failures']
        return result
    boundaries = {n: context['block_boundaries'][candidate['chain'][n]] for n in ('i1', 'i2', 'j', 'k')}
    frames, failures = _frames(boundaries, candidate['corner'])
    if failures:
        result['guard_failures'] = failures
        return result
    new = _replacement(candidate, frames)
    block = K._bill(new, {r: context['block_boundaries'][r] for r in context['support']},
                    phase='split_factor_block', detailed=detailed)
    need(block['valid'], 'ordered-chain guards imply five-frame factor feasibility')
    total = Counter(context['fixed_bill']['profile'])
    total.update(block['profile'])
    total = K._profile(total)
    need(K._mass(total) == context['original_bill']['rank_mass'], 'complete window rank mass')
    delta = Counter(total)
    delta.subtract(context['original_bill']['profile'])
    delta = K._profile(delta)
    moment = _joint()._moment(delta)
    status = ('PASS_CANDIDATE' if Q(moment['upper']) < 0 else
              'NO_GAIN' if not delta or Q(moment['lower']) >= 0 else 'EXPLORATORY')
    result.update(status=status, profile_delta=delta, moment_delta=moment)
    if detailed:
        result['proof'] = dict(block_boundaries=boundaries, whole_window_boundaries=context['outer'],
                              frames={k: list(v) for k, v in frames.items()}, new_gates=new,
                              original_window_bill=context['original_bill'], fixed_contact_bill=context['fixed_bill'],
                              factor_block_bill=block, complete_new_window_profile=total,
                              complete_rank_mass=K._mass(total), centre_payments_unchanged=True,
                              includes_all_unchanged_interveners_and_outside_successors=True,
                              intermediate_frame_feasibility_required=False,
                              crossings_sha256=context['plan']['crossings_sha256'],
                              frame_class=candidate['frame_class'], production_order=candidate['production_order'])
    return result


def census_task(spec):
    begin = time.process_time()
    K = _kernel()
    provider, seed = spec['provider'], int(spec['seed'])
    base, plans, exclusions, counts = K._enumerate(provider)
    need(len(base) % 20 == 0, 'complete inherited matched label blocks')
    candidates = []
    for first in range(0, len(base), 20):
        group = base[first:first + 20]
        need([x['address'][-1] for x in group] == list(range(20)), 'canonical inherited corner order')
        need(len({tuple(x['address'][:-1]) for x in group}) == 1, 'one carrier/anchor choice per block')
        need(len(candidates) + 80 <= MAX_LABELS, 'INCOMPLETE_DOMAIN_CAP: no truncated null')
        for offset, label in zip((0, 20, 40, 60), FRAME_CLASSES):
            for item in group:
                new = deepcopy(item)
                new['address'][-1] += offset
                new['candidate_id'] = new['pair_key'] = K._cid(new['address'])
                new['frame_class'] = label
                new['production_order'] = 'carrier_first' if offset < 40 else 'reverse_chain'
                candidates.append(new)
    for label in FRAME_CLASSES:
        counts[label] = len(base)
    counts['candidates'] = len(candidates)
    need(len(candidates) == 80 * counts['admissible_carrier_anchor_choices'], 'all eighty labels')
    need(len({c['candidate_id'] for c in candidates}) == len(candidates), 'unique split addresses')
    state = K._WORDS[provider]
    return dict(status='PASS', provider=provider, seed=seed, complete=True, candidates=candidates,
                plans=plans, plans_sha256=digest(plans), exclusions=exclusions,
                exclusions_sha256=digest(exclusions), counts=counts,
                domain_sha256=digest(candidates), candidate_set_sha256=digest(candidates),
                parent_semantic_sha256=state['semantic_sha256'], source_pin=state['source_pin'],
                source_attribution=state['attribution'], saved_domain=K._DOMAIN_PINS[provider],
                source_sections=list(K.SECTIONS), restore_search=False, pricing_cap=None,
                sharding='plan_ordinal modulo 192; every choice retains all80 labeled corners',
                scope=SCOPE, cpu_seconds=time.process_time() - begin)


def install_census(provider, receipt):
    need(receipt['counts']['candidates'] == 80 * receipt['counts']['admissible_carrier_anchor_choices'],
         'fresh eighty-label census required')
    need(provider not in _INSTALLED_HASHES, 'once-parent census installation')
    K = _kernel()
    K.install_census(provider, receipt)  # Validates full candidate/plan hashes once.
    _INSTALLED_HASHES[provider] = dict(domain=receipt['domain_sha256'], plans=receipt['plans_sha256'])
    groups = [defaultdict(list) for _ in range(SHARDS)]
    for ordinal, compact in enumerate(K._INSTALLED[provider]):
        groups[compact['plan_ordinal'] % SHARDS][compact['plan_id']].append((ordinal, compact))
    _SHARD_GROUPS[provider] = groups


def shard_task(spec):
    begin = time.process_time()
    K = _kernel()
    provider, seed = spec['provider'], int(spec['seed'])
    shard, shards = int(spec['shard']), int(spec.get('shards', SHARDS))
    need(shards == SHARDS and 0 <= shard < shards, '192 registered plan shards')
    need(provider in K._INSTALLED, 'install seed-agreed census in parent first')
    grouped = _SHARD_GROUPS[provider][shard]
    plans = sorted(grouped, key=lambda p: K._PLANS[provider][p]['plan_ordinal'])
    random.Random(seed).shuffle(plans)
    rows, favorable, tariffs, guards, windows = [], [], {}, {}, {}
    counts = Counter(candidates=sum(map(len, grouped.values())), plans=len(plans),
                     PASS_CANDIDATE=0, NO_GAIN=0, REJECTED_GUARD=0, EXPLORATORY=0,
                     **{name: 0 for name in FRAME_CLASSES})
    state = K._WORDS[provider]
    for plan_id in plans:
        plan = K._PLANS[provider][plan_id]
        context = K._context(state, plan)
        windows[plan_id] = dict(original_window_bill=context['original_bill'], fixed_contact_bill=context['fixed_bill'],
                               block_boundaries=context['block_boundaries'], whole_window_boundaries=context['outer'],
                               whole_window_boundaries_sha256=digest(context['outer']),
                               interval_sha256=plan['interval_sha256'], crossings_sha256=plan['crossings_sha256'])
        for ordinal, compact in grouped[plan_id]:
            candidate = _candidate(state, compact)
            result = _screen(context, candidate)
            row = dict(ordinal=ordinal, candidate_id=candidate['candidate_id'], status=result['status'],
                       plan_id=plan_id, plan_ordinal=plan['plan_ordinal'], frame_class=candidate['frame_class'])
            if result['status'] == 'REJECTED_GUARD':
                failures = result['guard_failures']
                ident = digest(failures)
                guards[ident] = failures
                row['failure_id'] = ident
            else:
                certificate = {k: result[k] for k in ('profile_delta', 'moment_delta')}
                ident = digest(certificate)
                tariffs[ident] = certificate
                row['tariff_id'] = ident
            rows.append(row)
            counts[row['status']] += 1
            counts[candidate['frame_class']] += 1
            if row['status'] == 'PASS_CANDIDATE':
                favorable.append(dict(row, address=candidate['address'], pair_key=candidate['pair_key'],
                                      profile_delta=result['profile_delta'], moment_delta=result['moment_delta']))
    rows.sort(key=lambda r: r['ordinal'])
    favorable.sort(key=lambda r: r['ordinal'])
    counts['unresolved'] = counts['EXPLORATORY']
    return dict(status='PASS', provider=provider, seed=seed, shard=shard, shards=shards, complete=True,
                counts=dict(counts), rows=rows, favorable=favorable, tariff_certificates=tariffs,
                guard_certificates=guards, window_certificates=windows,
                tariff_certificates_sha256=digest(tariffs), guard_certificates_sha256=digest(guards),
                window_certificates_sha256=digest(windows), shard_rows_sha256=digest(rows),
                domain_sha256=_INSTALLED_HASHES[provider]['domain'], plans_sha256=_INSTALLED_HASHES[provider]['plans'],
                parent_semantic_sha256=state['semantic_sha256'], source_attribution=state['attribution'],
                source_pin=state['source_pin'], saved_domain=K._DOMAIN_PINS[provider],
                primitive_cost_included=False, canonical_full_words_built=0,
                scope=SCOPE, ordinary_source_exit_dominance=DOMINANCE,
                cpu_seconds=time.process_time() - begin)


def build_candidate(provider, candidate_id):
    return _kernel().build_candidate(provider, candidate_id)


def validate_selected(spec):
    begin = time.process_time()
    K = _kernel()
    provider, seed = spec['provider'], int(spec['seed'])
    candidate_id = spec.get('candidate_id') or spec['candidate']['candidate_id']
    raw, result = build_candidate(provider, candidate_id)
    state = K._WORDS[provider]
    result.update(provider=provider, seed=seed, word=None, source_pin=state['source_pin'],
                  source_attribution=state['attribution'], saved_domain=K._DOMAIN_PINS[provider],
                  private_buffers=state['private_buffers'], word_source_physical_families=state['physical_families'],
                  native_admission=False, scalar_instruction_delta=2,
                  fresh_all_column_audit='Required separately; inherited native evidence does not admit changed words')
    if raw is not None and result['status'] == 'PASS_CANDIDATE':
        directory = Path(spec['output_dir'])
        directory = directory if directory.is_absolute() else RR / directory
        directory = directory.resolve()
        need(directory.is_relative_to((RR / 'data/continuation-14/candidates').resolve()), 'new retained subtree only')
        result['word'] = K._T()._write_word(raw, directory / provider, candidate_id)
    result['cpu_seconds'] = time.process_time() - begin
    return result


def _corner_oracle():
    """Independent actual-subspace enumeration of each five-flag chain in 3D."""
    spans = {frozenset({0})}
    for v in range(1, 8):
        spans |= {frozenset(set(s) | {x ^ v for x in s}) for s in list(spans)}
    spaces = sorted(spans, key=lambda x: (len(x), sorted(x)))
    need(len(spaces) == 16, 'full independent GF2^3 subspaces')

    def span(basis):
        values = {0}
        for v in basis:
            values |= {x ^ v for x in list(values)}
        return frozenset(values)

    def rank(space):
        return len(space).bit_length() - 1

    below = {s: [t for t in spaces if t <= s] for s in spaces}
    flags = [(X, Y, P, Q2, Z) for Z in spaces for Q2 in below[Z]
             for P in below[Q2] for Y in below[P] for X in below[Y]]
    fixtures = [dict(i1=((), (1, 2)), i2=((2, 4), (1, 2, 4)), j=((), (1, 2, 4)), k=((), (1, 2, 4))),
                dict(i1=((), (1,)), i2=((2,), (1, 2, 4)), j=((), (1, 2, 4)), k=((), (1, 2, 4))),
                dict(i1=((1,), (1,)), i2=((1, 2), (1, 2)), j=((), (1, 2)), k=((), (1, 2))),
                {r: ((), (1, 2, 4)) for r in ('i1', 'i2', 'j', 'k')}]
    names = ('i1', 'i2', 'j', 'k')
    tariffs = ((0, 6, 10, 12), (0, 10, 17, 23))
    records = []
    for space in spaces:
        b = _joint()._U()._basis(space)
        p = _perp(b, 3)
        need(span(p) == frozenset(v for v in range(8) if all((u & v).bit_count() % 2 == 0 for u in space)),
             'orthogonal complement agrees with independent full-vector oracle')
        need(_perp(p, 3) == b and len(p) + rank(space) == 3, 'same-ambient involution and rank')
    for fi, pairs in enumerate(fixtures):
        E = {r: span(e) for r, (e, o) in pairs.items()}
        O = {r: span(o) for r, (e, o) in pairs.items()}
        e, o = {r: rank(v) for r, v in E.items()}, {r: rank(v) for r, v in O.items()}
        for reverse in (False, True):
            if not reverse:
                feasible_base = [f for f in flags if (E['j'] | E['k']) <= f[0]
                                 and E['i1'] <= f[1] <= O['i1'] and E['i2'] <= f[2]
                                 and f[3] <= O['i2'] and f[4] <= O['j'] and f[4] <= O['k']]
            else:
                # Actual reverse-order frames (encode, v-k, v-j, u-j, undo).
                feasible_base = [f for f in flags if (E['j'] | E['k']) <= f[0]
                                 and E['i2'] <= f[1] and f[2] <= O['i2']
                                 and E['i1'] <= f[3] <= O['i1']
                                 and f[4] <= O['j'] and f[4] <= O['k']]

            def cost(f, h):
                x, second, third, fourth, z = map(rank, f)
                if not reverse:
                    y, p, q = second, third, fourth
                    jumps = (x - e['j'], y - x, p - y, z - p, o['j'] - z,
                             x - e['k'], q - x, z - q, o['k'] - z,
                             y - e['i1'], o['i1'] - y, p - e['i2'], q - p, o['i2'] - q)
                else:
                    q, p, y = second, third, fourth
                    jumps = (x - e['j'], p - x, y - p, z - y, o['j'] - z,
                             x - e['k'], q - x, z - q, o['k'] - z,
                             y - e['i1'], o['i1'] - y, q - e['i2'], p - q, o['i2'] - p)
                need(len(jumps) == 14 and min(jumps) >= 0, 'independent fourteen nonnegative jump terms')
                return sum(h[d] for d in jumps)

            for mask in range(16):
                def equality_ok(f):
                    final = (f[3], f[2], f[4], f[4]) if reverse else (f[1], f[3], f[4], f[4])
                    return all(not (mask & (1 << i)) or final[i] == O[r] for i, r in enumerate(names))

                feasible = [f for f in feasible_base if equality_ok(f)]
                boundaries = {r: dict(entry=list(pairs[r][0]), exit=list(pairs[r][1]),
                                     equality_exit=bool(mask & (1 << i))) for i, r in enumerate(names)}
                corners = []
                offset = 40 if reverse else 0
                for label in range(offset, offset + 40):
                    frames, failures = _frames(boundaries, label, ambient=3)
                    if not failures:
                        order = ('X', 'Q', 'P', 'Y1', 'Z') if reverse else ('X', 'Y1', 'P', 'Q', 'Z')
                        f = tuple(span(frames[r]) for r in order)
                        need(f in feasible, 'corner meets independent full flag/equality constraints')
                        corners.append(f)
                need(bool(feasible) == bool(corners), 'full five-frame feasibility parity')
                for h in tariffs:
                    actual = min((cost(f, h) for f in feasible), default=None)
                    proposed = min((cost(f, h) for f in corners), default=None)
                    need(actual == proposed, 'forty corners attain independent ordered full flag minimum')
                    records.append(dict(fixture=fi, reverse_chain=reverse, equality_mask=mask, tariff=list(h),
                                        feasible_flags=len(feasible), valid_labels=len(corners), minimum=actual))
    return dict(passed=True, ambient_dimension=3, subspaces=16, nested_flags=len(flags),
                records=records, scope='Each of the two explicit five-frame chains separately; all16 source/target equality masks')


def controls_task(spec):
    begin = time.process_time()
    K = _kernel()
    seed = int(spec['seed'] if isinstance(spec, dict) else spec)
    inherited = K.controls_task(dict(seed=seed))
    need(inherited['status'] == 'PASS', 'unchanged matched/control utility suite')
    checks = Counter()

    def check(name, condition):
        need(condition, 'split residual control: ' + name)
        checks[name] += 1

    S, T, U5 = (1, 2), (1, 2, 4, 8), (1, 2, 4, 8, 16)
    old = [K._gate(0, 2, 1, S), K._gate(1, 2, 1, S), K._gate(0, 3, 1, S), K._gate(1, 3, -1, S)]
    boundary = {0: dict(entry=list(S), exit=list(S), equality_exit=False),
                1: dict(entry=list(S), exit=list(T), equality_exit=False),
                2: dict(entry=[], exit=list(U5), equality_exit=False),
                3: dict(entry=[], exit=list(U5), equality_exit=False)}
    before = K._bill(old, boundary)
    check('positive_fixture_original_profile', before['valid'] and before['profile'] == {2: 3, 3: 2})
    matched, split, strictly_split = [], [], []
    for carrier, anchor in itertools.product((0, 1), repeat=2):
        chain = K._packet(old, 'in', carrier, anchor, ())
        b = {n: boundary[chain[n]] for n in ('i1', 'i2', 'j', 'k')}
        for label in range(40):
            frames, failures = _frames(b, label)
            if failures:
                continue
            candidate = dict(chain=chain, corner=label)
            new = _replacement(candidate, frames)
            after = K._bill(new, boundary)
            check('fixture_frame_feasibility', after['valid'])
            check('fixture_complete_rank_mass', after['rank_mass'] == before['rank_mass'] == 12)
            for dual in (False, True):
                check('split_forward_dual_identity', K._matrix(old, dual) == K._matrix(new, dual))
            delta = Counter(after['profile'])
            delta.subtract(before['profile'])
            delta = K._profile(delta)
            moment = _joint()._moment(delta)
            entry = dict(carrier=carrier, anchor=anchor, label=label, profile=after['profile'],
                         profile_delta=delta, moment=moment)
            (matched if label < 20 else split).append(entry)
            if label < 20:
                check('all_old_matched_corners_nonimproving', not delta or Q(moment['lower']) >= 0)
                oldframes, oldfailures = _joint()._frames(b, label)
                check('matched_label_subspaces_identical', not oldfailures and frames['X'] == oldframes['X']
                      and frames['Y1'] == oldframes['Y1'] and frames['P'] == frames['Q'] == oldframes['Y2']
                      and frames['Z'] == oldframes['Z'])
            elif Q(moment['upper']) < 0:
                strictly_split.append(entry)
    check('matched_family_has_exact_tie', any(not x['profile_delta'] for x in matched))
    check('split_strictly_improves_beyond_matched_minimum', bool(strictly_split))
    wanted = {1: 1, 2: -1, 3: -1, 4: 1}
    check('strict_fixture_expected_complete_delta', any(x['profile_delta'] == wanted for x in strictly_split))
    manual = dict(X=(), Y1=S, P=S, Q=T, Z=U5)
    chain = K._packet(old, 'in', 0, 0, ())
    new = _replacement(dict(chain=chain), manual)
    after = K._bill(new, boundary)
    check('independent_positive_profile', after['profile'] == {1: 1, 2: 2, 3: 1, 4: 1})
    bad = deepcopy(new)
    bad[2][-1] = [1, 4]
    check('equal_rank_wrong_orientation_rejected', not K._bill(bad, boundary)['valid'])
    bad = deepcopy(new)
    bad[3][3] = -bad[3][3]
    for dual in (False, True):
        check('residual_sign_mutant_rejected', K._matrix(old, dual) != K._matrix(bad, dual))
    # The Q-P jump on v is a real paid child; removing just its invoice term
    # destroys mass even though the scalar production has not changed.
    omitted = Counter(after['profile'])
    omitted[len(T) - len(S)] -= 1
    check('omitted_split_target_climb_breaks_mass', K._mass(omitted) == 10 != after['rank_mass'])
    # The second order is new even at its matched-read labels. In particular,
    # it must not inherit the old forward order's no-improvement assertion.
    line, plane = (1,), (1, 2)
    reverse_old = [K._gate(0, 2, 1, line), K._gate(1, 2, 1, line),
                   K._gate(0, 3, 1, line), K._gate(1, 3, -1, line)]
    reverse_boundary = {0: dict(entry=list(line), exit=list(line), equality_exit=False),
                        1: dict(entry=[], exit=list(line), equality_exit=False),
                        2: dict(entry=[], exit=list(plane), equality_exit=False),
                        3: dict(entry=[], exit=list(plane), equality_exit=False)}
    reverse_before = K._bill(reverse_old, reverse_boundary)
    check('reverse_fixture_original_profile', reverse_before['valid'] and reverse_before['profile'] == {1: 5})
    reverse_strict, reverse_labels = [], 0
    for carrier, anchor in itertools.product((0, 1), repeat=2):
        chain = K._packet(reverse_old, 'in', carrier, anchor, ())
        b = {n: reverse_boundary[chain[n]] for n in ('i1', 'i2', 'j', 'k')}
        for label in range(40, 80):
            frames, failures = _frames(b, label, ambient=2)
            if failures:
                continue
            reverse_labels += 1
            new_reverse = _replacement(dict(chain=chain, corner=label), frames)
            reverse_after = K._bill(new_reverse, reverse_boundary)
            check('reverse_fixture_feasibility_and_mass', reverse_after['valid'] and reverse_after['rank_mass'] == 5)
            for dual in (False, True):
                check('reverse_exact_forward_dual_identity', K._matrix(reverse_old, dual) == K._matrix(new_reverse, dual))
            delta = Counter(reverse_after['profile'])
            delta.subtract(reverse_before['profile'])
            delta = K._profile(delta)
            interval = _joint()._moment(delta)
            if Q(interval['upper']) < 0:
                reverse_strict.append(dict(carrier=carrier, anchor=anchor, label=label,
                                           profile=reverse_after['profile'], delta=delta))
    check('reverse_order_has_strict_gain', bool(reverse_strict))
    check('reverse_fixture_expected_delta', any(x['delta'] == {1: -2, 2: 1} for x in reverse_strict))
    reverse_manual = dict(X=(), Q=(), P=line, Y1=line, Z=plane)
    reverse_chain = K._packet(reverse_old, 'in', 0, 0, ())
    reverse_new = _replacement(dict(chain=reverse_chain, corner=60), reverse_manual)
    reverse_bill = K._bill(reverse_new, reverse_boundary)
    check('reverse_independent_complete_bill', reverse_bill['valid'] and reverse_bill['profile'] == {1: 3, 2: 1})
    bad = deepcopy(reverse_new)
    bad[1][3] = -bad[1][3]
    for dual in (False, True):
        check('reverse_residual_sign_mutant', K._matrix(reverse_old, dual) != K._matrix(bad, dual))
    equality = deepcopy(reverse_boundary)
    equality[2]['equality_exit'] = True
    too_early = deepcopy(reverse_new)
    too_early[-1][-1] = list(line)
    check('reverse_original_exit_equality_not_successor_repaired', not K._bill(too_early, equality)['valid'])
    wrong_ambient = _perp(line, 3)
    check('ambient_is_explicit_not_maximum_bit', len(wrong_ambient) == 2 and _perp(line, 2) != wrong_ambient)
    # Both scalar orderings receive a fresh signed non-unit coefficient check;
    # inherited controls independently cover the original matched order.
    signed = (Q(-2), Q(-1, 2), Q(1, 2), Q(2))
    extra_signed = 0
    for a, b, c, d in itertools.product(signed, repeat=4):
        if a * d == b * c:
            continue
        original = [K._gate(0, 2, a), K._gate(1, 2, c), K._gate(0, 3, b), K._gate(1, 3, d)]
        for carrier, anchor in itertools.product((0, 1), repeat=2):
            chain = K._packet(original, 'in', carrier, anchor, ())
            if not chain['coefficient_admissible']:
                continue
            for order_label in (0, 40):
                frames = dict(X=(), Y1=(), P=(), Q=(), Z=())
                rewritten = _replacement(dict(chain=chain, corner=order_label), frames)
                for dual in (False, True):
                    check('both_orders_signed_dirty_map', K._matrix(original, dual) == K._matrix(rewritten, dual))
                    extra_signed += 1
    oracle = _corner_oracle()
    check('independent_full_five_frame_oracle', oracle['passed'])
    combined = {'inherited_' + k: v for k, v in inherited['checks_by_family'].items()}
    combined.update(checks)
    return dict(status='PASS', seed=seed, checks=sum(combined.values()), checks_by_family=combined,
                inherited_matched_checks=inherited['checks'], inherited_controls=inherited,
                all_interleavings=inherited['all_interleavings'], exact_signed_identities=inherited['exact_signed_identities'] + extra_signed,
                corner_oracle=oracle, positive_profile_delta=wanted,
                positive_fixture=dict(original=before['profile'], new=after['profile'], rank_mass=12,
                                      matched_labels=len(matched), split_labels=len(split),
                                      matched_all_nonimproving=True, strict_split_labels=len(strictly_split),
                                      tariff_scope='The old matched minimum uses the registered power tariff; corner completeness uses concavity.'),
                reverse_positive_fixture=dict(original=reverse_before['profile'], new=reverse_bill['profile'],
                                              profile_delta={1: -2, 2: 1}, rank_mass=5,
                                              valid_labels=reverse_labels, strict_labels=len(reverse_strict),
                                              matched_labels_are_new_order=True),
                matched_residual_read_frame=False, scope=SCOPE,
                source_attribution={p: s['attribution'] for p, s in K._WORDS.items()},
                cpu_seconds=time.process_time() - begin)
