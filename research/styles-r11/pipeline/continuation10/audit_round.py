"""Administrative saved-byte audit for continuation10; no scientific imports.

Run after the coordinator closes all receipts, reports and registry. --write
creates AUDIT.json once; repeat verification checks its stable payload without
rewriting immutable bytes. Detailed evidence lives under data from the outset.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

PKG=Path(__file__).resolve().parents[2]
ROOT=PKG.parents[1]
ROUND=PKG/'results/CONTINUATION-10'
DATA=PKG/'data/continuation-10'
BASE='bf3c12018d6988d611895d60c3afb40691e18096'
FAMILY='J2-COMMUTING-EXPOSURE'
SEEDS={53017,106013}
PROVIDERS={'base','extra'}
IGNORE={'seed','cpu_seconds','wall_seconds','elapsed_seconds','seconds','recorded_utc','output_dir','schedule'}
CHECKED_REFS=set()
_SPANS={}
_RAW={}


def read(path):
    path=Path(path)
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def local_path(name):
    p=Path(name)
    p=(ROOT/p if str(p).startswith('research/styles-r11/') else PKG/p).resolve()
    need(p.is_relative_to(PKG), 'artifact path confined to r11: '+str(name))
    return p


def need(ok, message):
    if not ok:
        raise ValueError(message)



def digest(raw):
    return hashlib.sha256(raw).hexdigest()



def normalized(value):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key = str(key)
            need(key not in out, 'canonical mapping key collision')
            out[key] = normalized(item)
        return out
    if isinstance(value, (list, tuple)):
        return [normalized(v) for v in value]
    return value


def canonical(value):
    return json.dumps(normalized(value), sort_keys=True, separators=(',', ':'), allow_nan=False)



def clean(value):
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        out = {k: clean(v) for k, v in value.items() if k not in IGNORE}
        if 'path' in out and 'sha256' in out:
            out['path'] = '<separate-path-identical-bytes>'
        return out
    return value



def reference(ref):
    p = local_path(ref['path'])
    raw = p.read_bytes()
    need(digest(raw) == ref['sha256'], 'artifact SHA256: ' + str(p))
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'artifact byte count')
    if 'payload_sha256' in ref:
        payload = gzip.decompress(raw) if p.suffix == '.gz' else raw
        need(digest(payload) == ref['payload_sha256'], 'artifact payload SHA256')
    if 'git_blob' in ref:
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
             == ref['git_blob'], 'artifact Git blob')
    CHECKED_REFS.add(str(p.relative_to(PKG)))
    return p



def references(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            if value['path'].startswith(('data/', 'results/', 'pipeline/', 'research/styles-r11/')):
                reference(value)
        for v in value.values():
            references(v)
    elif isinstance(value, list):
        for v in value:
            references(v)



def credits(result, original):
    rows = result['source_attribution']
    by_path = {x['path']: x for x in rows}
    need(len(by_path) == len(rows), 'unique attribution identities')
    for name, pin in original.items():
        need(name in by_path and all(by_path[name].get(k) == v for k, v in pin.items()),
             'all21 original PINS source credits')
    return len(rows)



def acquisition(ref):
    path = reference(ref)
    value = read(path)
    files = value['files']
    need(isinstance(files, list), 'acquisition list schema')
    total = 0
    for row in files:
        name = row.get('local_path', row.get('path'))
        pin = {k: row[k] for k in ('sha256', 'bytes', 'git_blob') if k in row}
        pin['path'] = name
        p = reference(pin)
        need(p.suffix != '.py', 'fetched programs stored only as inert text')
        total += p.stat().st_size
    return dict(path=str(path.relative_to(PKG)), sha256=digest(path.read_bytes()),
                files=len(files), payload_bytes=total, author=value.get('author', value.get('author_login')))



def archives(pins, implementation):
    mapping = pins['source_archives']
    need(implementation['source_archives'] == mapping, 'implementation/archive-reference agreement')
    need(set(mapping) == set(pins['sha256'].values()), 'all frozen source payloads archived')
    historical = []
    for name, expected in pins['sha256'].items():
        archive = reference(mapping[expected])
        need(digest(gzip.decompress(archive.read_bytes())) == expected, 'exact frozen source preimage')
        p = (ROOT / name).resolve()
        need(p.is_relative_to(ROOT), 'trusted frozen source is repository-confined')
        if not p.exists() or digest(p.read_bytes()) != expected:
            need(name.endswith(('/audit_round.py', '/final_checkpoint.py', '/checkpoint_sources.py')),
                 'scientific source changed after freeze: ' + name)
            historical.append(name)
    return dict(unique_source_payloads=len(mapping), historical_administrative_preimages=historical,
                reused_earlier_archives=sum(not local_path(x['path']).is_relative_to(ROUND)
                                          for x in mapping.values()))



def address_key(row):
    address = row['address']
    return (('A', 'B').index(address[0]), *address[1:])



def span(frame):
    key = tuple(frame)
    if key not in _SPANS:
        need(all(type(x) is int and 0 <= x < 512 for x in key), 'saved GF2 frame coordinates')
        values = {0}
        for x in key:
            values |= {y ^ x for y in values}
        _SPANS[key] = frozenset(values)
    return _SPANS[key]



def guard_certificate(value):
    predicate = value['predicate']
    if predicate == 'window_frame_inclusion':
        lower,upper = span(value['actual']),span(value['required'])
        need(value['excluded_vector'] in lower and value['excluded_vector'] not in upper, 'literal full-window inclusion witness')
        return
    if predicate == 'frame_inclusion':
        lower, upper = span(value['lower_frame']), span(value['upper_frame'])
    elif predicate == 'exit_inclusion':
        lower, upper = span(value['actual']), span(value['required'])
    else:
        need(predicate in {'exit_equality', 'window_exit_equality'} and span(value['actual']) != span(value['required']),
             'saved exit equality is a genuine subspace inequality')
        return
    witness = value['excluded_vector']
    need(witness in lower and witness not in upper, 'saved exclusion vector certifies failed inclusion')



def raw_source(provider):
    """Read a source-bound JSON word as data; never load a scientific module."""
    if provider not in _RAW:
        bindings = read(DATA/'pr3030/SOURCE-BINDINGS.json')
        path = reference(bindings['words'][provider]['existing_artifact'])
        _RAW[provider] = read(path)
    return _RAW[provider]


def operands(gate):
    if gate[0] == 'add':
        return [int(gate[1]), int(gate[2])]
    if gate[0] == 'scale':
        return [int(gate[1])]
    raise ValueError('nonordinary gate in registered commuting window')


def pair_operator(first, second, dual=False):
    """Independent exact tiny-matrix arithmetic on saved literal gate pairs."""
    regs = sorted(set(operands(first)+operands(second)))
    ix = {r:i for i,r in enumerate(regs)}
    matrix = [[Fraction(i == j) for j in range(len(regs))] for i in range(len(regs))]
    for gate in (first, second):
        t = ix[gate[1]]
        if gate[0] == 'add':
            a = Fraction(gate[3], gate[4]); u = ix[gate[2]]
            if t == u:
                factor = 1+a
                need(factor != 0, 'invertible self-addition in saved crossing')
                if dual: factor = 1/factor
                matrix[t] = [factor*x for x in matrix[t]]
            else:
                if dual: t,u,a = u,t,-a
                matrix[t] = [x+a*y for x,y in zip(matrix[t], matrix[u])]
        else:
            factor = Fraction(gate[2], gate[3])
            need(factor != 0, 'invertible scale in saved crossing')
            if dual: factor = 1/factor
            matrix[t] = [factor*x for x in matrix[t]]
    return matrix


def pair_commutes(first, second):
    forward = pair_operator(first, second) == pair_operator(second, first)
    dual = pair_operator(first, second, True) == pair_operator(second, first, True)
    need(forward == dual, 'independent forward/dual crossing agreement')
    return forward


def crossing_certificate(item, gates, selected):
    i,j = item['selected_index'],item['unselected_index']
    need(i in selected and j not in selected and min(selected) <= j <= max(selected),
         'crossing exact selected/unselected indices')
    first,second = gates[i],gates[j]
    if item['method'] == 'add_guard':
        need(first[0] == second[0] == 'add' and first[1] != first[2] and second[1] != second[2],
             'ordinary nonself-add guard scope')
        need(Fraction(first[3],first[4]) and Fraction(second[3],second[4]) and
             first[2] != second[1] and second[2] != first[1], 'exact add commutation guard')
    else:
        need(item['method'] == 'pair_matrix' and
             item['pair_hash'] == digest(canonical([first,second]).encode()) and
             item['forward_equal'] is True and item['dual_equal'] is True,
             'saved fallback binds both exact literal gates and orientations')
        need(pair_commutes(first,second), 'independent exact dirty-input crossing identity')


def crossing_pairs(address):
    selected = tuple(address[1:5]); unselected = tuple(i for i in range(selected[0],selected[-1]+1) if i not in selected)
    placement = address[6]
    need(placement in (0,1), 'registered left/right placement')
    for i in (selected if placement == 0 else selected[::-1]):
        crossed = tuple(j for j in unselected if j < i)[::-1] if placement == 0 else tuple(j for j in unselected if j > i)
        for j in crossed:
            yield i,j


def scalar_precondition(second):
    if not isinstance(second, list) or not second or second[0] not in ('add', 'scale'):
        return 'unsupported_opcode'
    if second[0] == 'scale' and Fraction(second[2], second[3]) == 0:
        return 'singular_scale'
    if second[0] == 'add' and second[1] == second[2] and 1+Fraction(second[3], second[4]) == 0:
        return 'singular_self_add'
    return None


def scalar_pair_commutes(first,second):
    if scalar_precondition(second) is not None:
        return False
    ordinary = all(g[0] == 'add' and g[1] != g[2] and Fraction(g[3],g[4]) != 0 for g in (first,second))
    if ordinary:
        return first[2] != second[1] and second[2] != first[1]
    return pair_commutes(first,second)


def plan_certificates(census,provider,protocol):
    raw = raw_source(provider); parent = digest(canonical(raw).encode())
    need(census['parent_semantic_sha256'] == parent, 'saved plan parent is the exact pinned source word')
    previous = read(reference(protocol['inputs']['saved_source_census_'+provider]))
    need(previous['status'] == 'OK', 'source census pool receipt succeeded')
    previous = previous['result']
    need(previous['parent_semantic_sha256'] == parent and
         digest(canonical(previous['exclusions']).encode()) == previous['exclusions_sha256'],
         'inherited source exclusions and exact parent binding')
    bases = {tuple(v['address']) for v in previous['exclusions']}
    need(len(bases) == 2878, 'fixed inherited2878-address domain')
    expected = {(*a,placement) for a in bases for placement in (0,1)}
    plans = census['plans']; exclusions = census['exclusions']; counts = census['counts']
    need(digest(canonical(plans).encode()) == census['plans_sha256'] and
         digest(canonical(exclusions).encode()) == census['exclusions_sha256'], 'exact plan and exclusion inventories')
    legal = {}; failed = {}; ratio = {}; verified = 0; methods = Counter(); failure_kinds = Counter()
    ordered = sorted(plans.values(), key=lambda v:v['plan_ordinal'])
    need([v['plan_ordinal'] for v in ordered] == list(range(len(ordered))), 'consecutive unique plan ordinals')
    need(ordered == sorted(ordered,key=address_key), 'canonical numeric plan order')
    for plan in ordered:
        address = plan['address']; key = tuple(address)
        need(len(address) == 7 and key in expected and key not in legal, 'unique legal registered plan address')
        ident = digest(canonical(dict(parent_semantic_sha256=parent,address=address)).encode())
        need(plan['plan_id'] == ident and plans[ident] == plan and plan['parent_semantic_sha256'] == parent,
             'plan ID binds parent and exact address')
        section = address[0]; gates = raw[section]; selected = tuple(address[1:5]); start,end = selected[0],selected[-1]
        window = gates[start:end+1]
        need(digest(canonical(window).encode()) == plan['interval_sha256'], 'literal source window hash')
        log = plan['crossings']
        need(digest(canonical(log).encode()) == plan['crossings_sha256'], 'complete crossing log hash')
        pairs = list(crossing_pairs(address))
        need([(v['selected_index'],v['unselected_index']) for v in log] == pairs,
             'all and only deterministic adjacent crossings')
        current = list(range(start,end+1)); locations = {r:i for i,r in enumerate(current)}
        for item in log:
            crossing_certificate(item,gates,selected); methods[item['method']] += 1
            i,j = item['selected_index'],item['unselected_index'];a,b = locations[i],locations[j]
            need(abs(a-b) == 1 and ((b<a) == (address[6] == 0)), 'literal adjacent swap in stated gather direction')
            current[a],current[b] = current[b],current[a];locations[i],locations[j] = b,a
        remainder = [i for i in range(start,end+1) if i not in selected]
        target = list(selected)+remainder if address[6] == 0 else remainder+list(selected)
        need(current == target and digest(canonical(current).encode()) == plan['gathered_order_sha256'],
             'stable complete gathered order, unchanged interveners and selected order')
        legal[key] = plan; verified += len(log)
    for exclusion in exclusions:
        predicate = exclusion['predicate']
        if predicate in {'noncommuting_crossing', 'scalar_crossing_precondition'}:
            address = exclusion['plan_address']; key = tuple(address)
            need(key in expected and key not in failed and key not in legal, 'unique excluded registered placement')
            gates = raw[address[0]]; i,j = exclusion['selected_index'],exclusion['unselected_index']
            prefix = exclusion['verified_prefix_count']; pairs = crossing_pairs(address)
            need(type(prefix) is int and prefix >= 0, 'nonnegative verified crossing prefix')
            for n in range(prefix+1):
                pair = next(pairs,None);need(pair is not None, 'failure prefix is within the exact crossing sequence')
                if n < prefix:need(scalar_pair_commutes(gates[pair[0]],gates[pair[1]]), 'claimed verified prefix actually commutes')
            need(pair == (i,j) and exclusion['selected_gate'] == gates[i] and exclusion['unselected_gate'] == gates[j],
                 'first failing crossing binds actual source instructions')
            need(not scalar_pair_commutes(gates[i],gates[j]), 'independent exact noncommutation witness')
            cert = exclusion['commutation']
            need(cert['commutes'] is False, 'recorded failed crossing disposition')
            if predicate == 'scalar_crossing_precondition':
                reason = scalar_precondition(gates[j])
                need(reason is not None and cert['method'] == 'scalar_precondition' and cert['reason'] == reason and
                     cert['pair_hash'] == digest(canonical([gates[i], gates[j]]).encode()),
                     'literal singular or unsupported scalar exclusion')
                if reason == 'unsupported_opcode':
                    need(cert['opcode'] == (gates[j][0] if isinstance(gates[j], list) and gates[j] else None), 'unsupported opcode binding')
                else:
                    need(cert['register'] == gates[j][1] and cert['multiplier'] == '0', 'singular scalar multiplier and register')
            elif cert['method'] == 'add_guard':
                need(cert['selected_source_differs_unselected_target'] == (gates[i][2] != gates[j][1]) and
                     cert['unselected_source_differs_selected_target'] == (gates[j][2] != gates[i][1]),
                     'literal dependency witness booleans')
            else:
                need(cert['method'] == 'pair_matrix' and cert['pair_hash'] == digest(canonical([gates[i],gates[j]]).encode()) and
                     cert['forward_equal'] is False and cert['dual_equal'] is False, 'exact noncommuting fallback witness')
            failed[key] = exclusion;verified += prefix;failure_kinds[predicate] += 1
        elif predicate == 'non_dyadic_transport_ratio':
            address = exclusion['address']; key = tuple(address)
            need(len(address) == 8 and tuple(address[:7]) in legal and key not in ratio,
                 'unique carrier exclusion belongs to legal plan')
            need(exclusion['plan_id'] == legal[tuple(address[:7])]['plan_id'], 'ratio exclusion plan binding')
            q = Fraction(exclusion['ratio']);coeff = {k:Fraction(v) for k,v in exclusion['coefficients'].items()}
            need(q.numerator == exclusion['reduced_numerator'] and q.denominator == exclusion['reduced_denominator'] and
                 q != 0 and q.denominator & (q.denominator-1) != 0 and
                 q == coeff['b1']/coeff['a1'] == coeff['b2']/coeff['a2'], 'exact non-dyadic common transport ratio')
            ratio[key] = exclusion
        else:raise ValueError('unexpected scalar exclusion predicate: '+predicate)
    need(set(legal)|set(failed) == expected and not(set(legal)&set(failed)), 'every source packet gets both gather dispositions')
    need(counts['source_excluded_addresses'] == 2878 and counts['placements_considered'] == 5756 and
         counts['commuting_placements'] == len(legal) and counts['noncommuting_placements'] == failure_kinds['noncommuting_crossing'] and
         counts['scalar_precondition_rejected_placements'] == failure_kinds['scalar_crossing_precondition'] and
         counts['ratio_rejected_carriers'] == len(ratio) and counts['crossings_verified'] == verified,
         'saved scalar-domain accounting from exact certificates')
    expected_labels = set()
    for address,plan in legal.items():
        for carrier in (0,1):
            if (*address,carrier) in ratio:continue
            for order in (0,1):
                for corner in range(20):expected_labels.add((*address,carrier,order,corner))
    need({tuple(c['address']) for c in census['candidates']} == expected_labels and
         len(census['candidates']) == len(expected_labels), 'every allowed carrier/order/corner label exactly once')
    for candidate in census['candidates']:
        plan = legal[tuple(candidate['address'][:7])]
        need(candidate['plan_id'] == plan['plan_id'] and candidate['plan_ordinal'] == plan['plan_ordinal'] and
             candidate['candidate_id'] == candidate['pair_key'] == '.'.join(map(str,candidate['address'])),
             'candidate ID and plan address binding')
    return dict(source_addresses=2878, placements=5756, legal_plans=len(legal),
                noncommuting_placements=failure_kinds['noncommuting_crossing'],
                scalar_precondition_rejected_placements=failure_kinds['scalar_crossing_precondition'], ratio_exclusions=len(ratio),
                verified_prefix_and_legal_crossings=verified, successful_crossing_methods=dict(methods))


def expanded_rows(shard,candidates,plans,protocol):
    tariffs,guards,windows = (shard[k] for k in ('tariff_certificates','guard_certificates','window_certificates'))
    for name,mapping in (('tariff_certificates',tariffs),('guard_certificates',guards),('window_certificates',windows)):
        need(digest(canonical(mapping).encode()) == shard[name+'_sha256'], 'complete compact certificate map hash')
    for mapping in (tariffs,guards):
        need(all(ident == digest(canonical(value).encode()) for ident,value in mapping.items()), 'exact compact certificate IDs')
    rows=[];used_t=set();used_g=set();used_p=set()
    for saved in shard['rows']:
        ordinal = saved['ordinal'];need(0 <= ordinal < len(candidates), 'canonical candidate ordinal')
        src = candidates[ordinal];pid = src['plan_id']
        need(saved['candidate_id'] == src['candidate_id'] and saved['plan_id'] == pid and
             saved['plan_ordinal'] == src['plan_ordinal'] and src['plan_ordinal']%64 == shard['shard'],
             'plan-based shard and exact candidate membership')
        need(saved.get('address',src['address']) == src['address'], 'optional compact address consistency')
        row = dict(src,**{k:v for k,v in saved.items() if k not in src})
        used_p.add(pid)
        if saved['status'] == 'REJECTED_GUARD':
            ident=saved['failure_id'];need(ident in guards and guards[ident], 'explicit saved guard witness')
            row.update(guard_failures=guards[ident],profile_delta=None,moment_delta=None);used_g.add(ident)
        else:
            ident=saved['tariff_id'];need(ident in tariffs, 'saved exact tariff certificate')
            row.update(tariffs[ident]);used_t.add(ident)
        rows.append(row)
    need(used_t == set(tariffs) and used_g == set(guards) and used_p == set(windows), 'all and only referenced compact certificates')
    for pid,window in windows.items():
        plan=plans[pid]
        need(window['interval_sha256'] == plan['interval_sha256'] and window['crossings_sha256'] == plan['crossings_sha256'],
             'window invoice binds exact source interval and crossings')
        old=window['original_window_bill'];need(old['valid'] and not old['failures'] and
             sum(int(r)*n for r,n in old['profile'].items()) == old['rank_mass'], 'complete saved original window mass')
        fixed=window['fixed_contact_bill']
        if fixed['valid']:need(not fixed['failures'] and sum(int(r)*n for r,n in fixed['profile'].items()) == fixed['rank_mass'],
                              'saved fixed-contact mass')
        else:
            need(fixed['failures'], 'invalid fixed contact has exact obstruction')
            for failure in fixed['failures']:guard_certificate(failure)
    positives=[r for r in rows if r['status']=='PASS_CANDIDATE']
    need(len(positives) == len(shard['favorable']), 'all favorable rows expanded')
    for row,saved in zip(positives,shard['favorable']):
        need(all(row[k] == saved[k] for k in ('candidate_id','ordinal','plan_id','plan_ordinal','address','pair_key','profile_delta','moment_delta')),
             'expanded favorable row agrees with source and compact tariff')
    return rows


def saved_domain(tasks, seed_results, protocol, meta, run, reconcile=False):
    census = {(s['seed'], s['provider']): v for phase, s, v, _ in tasks if phase == 'census'}
    price = {(s['seed'], s['provider'], s['shard']): v
             for phase, s, v, _ in tasks if phase == 'prices'}
    need(set(census) == {(s, p) for s in SEEDS for p in PROVIDERS}, 'both complete source censuses')
    need(set(price) == {(s, p, i) for s in SEEDS for p in PROVIDERS for i in range(64)},
         'all64 shards for each seed/provider')
    summaries = {}
    favorable = {}
    for provider in sorted(PROVIDERS):
        twins = [census[s, provider] for s in sorted(SEEDS)]
        need(clean(twins[0]) == clean(twins[1]), 'two-seed exact census equality')
        c = twins[0]
        candidates = c['candidates']
        excluded = plan_certificates(c,provider,protocol)
        need(c['complete'] and c['status'] == 'PASS' and not c['restore_search'], 'fixed A/B domain only')
        need(len(candidates) == c['counts']['candidates'] and
             len({x['candidate_id'] for x in candidates}) == len(candidates), 'unique exhaustive candidate inventory')
        need(candidates == sorted(candidates, key=address_key), 'canonical numeric domain order')
        need(digest(canonical(candidates).encode()) == c['domain_sha256'], 'exact census domain digest')
        need(len(candidates) == 40*c['counts']['admissible_carrier_choices'], 'both orders and twenty labels per allowed carrier')
        per_seed = {}
        for seed in sorted(SEEDS):
            rows = []
            totals = Counter()
            for shard in range(64):
                v = price[seed, provider, shard]
                need(v['status'] == 'PASS' and v['complete'] and v['shard'] == shard and v['shards'] == 64,
                     'complete disjoint shard specification')
                need(v['domain_sha256'] == c['domain_sha256'], 'shard binds the registered canonical census')
                need(digest(canonical(v['rows']).encode()) == v['shard_rows_sha256'], 'exact saved shard row hash')
                expected = [i for i,x in enumerate(candidates) if x['plan_ordinal']%64 == shard]
                need([x['ordinal'] for x in v['rows']] == expected, 'all and only assigned canonical ordinals')
                need(v['plans_sha256'] == c['plans_sha256'], 'shard binds exact crossing plans')
                resolved = expanded_rows(v,candidates,c['plans'],protocol)
                for row in resolved:
                    src = candidates[row['ordinal']]
                    need(all(row[k] == src[k] for k in ('candidate_id', 'pair_key', 'address')),
                         'price row binds exact candidate address')
                    moment = row.get('moment_delta')
                    if row['status'] == 'REJECTED_GUARD':
                        need(row.get('guard_failures') and row.get('profile_delta') is None,
                             'guard rejection has explicit witness')
                        for failure in row['guard_failures']:
                            guard_certificate(failure)
                    else:
                        need(moment is not None, 'resolved price has saved interval')
                        lo, hi = Fraction(moment['lower']), Fraction(moment['upper'])
                        need(lo <= hi and moment['endpoint'] == protocol['comparison']['complex_endpoint'],
                             'saved exact interval and fixed comparator')
                        need(sum(int(r)*n for r, n in row['profile_delta'].items()) == 0,
                             'saved signed profile has exact zero mass')
                        if row['status'] == 'PASS_CANDIDATE':
                            need(hi < 0, 'favorable row certified strictly negative')
                        elif row['status'] == 'NO_GAIN':
                            need(lo >= 0, 'nonnegative row actually resolved')
                            need(bool(row['profile_delta']) != moment['exact_profile_identity'],
                                 'exact identity flag agrees with signed profile')
                            if not row['profile_delta']:
                                need(lo == hi == 0, 'identical profile has exact zero moment interval')
                        else:
                            need(row['status'] == 'EXPLORATORY' and lo < 0 <= hi,
                                 'unresolved sign remains exploratory')
                counts = Counter(x['status'] for x in v['rows'])
                need(v['counts']['candidates'] == len(v['rows']), 'saved shard candidate total')
                need(v['counts'].get('unresolved', v['counts'].get('EXPLORATORY', 0)) == counts['EXPLORATORY'],
                     'unresolved counter matches actual saved rows')
                for name in ('PASS_CANDIDATE', 'NO_GAIN', 'REJECTED_GUARD', 'EXPLORATORY'):
                    if name in v['counts']:
                        need(v['counts'][name] == counts[name], 'saved per-status shard count')
                rows.extend(resolved)
                totals.update(v['counts'])
            rows.sort(key=lambda row: row['ordinal'])
            need([x['ordinal'] for x in rows] == list(range(len(candidates))), 'no domain omission or duplication')
            per_seed[seed] = rows
            if not reconcile:
                need(dict(totals) == seed_results[seed]['statistics']['counts_by_provider'][provider],
                     'RESULT aggregate equals every saved shard')
        need(per_seed[min(SEEDS)] == per_seed[max(SEEDS)], 'all price rows agree across seeds')
        favorable[provider] = {x['candidate_id']: x for x in per_seed[min(SEEDS)]
                               if x['status'] == 'PASS_CANDIDATE'}
        summaries[provider] = dict(candidates=len(candidates), shards_per_seed=64,
                                  commutation_certificate_summary=excluded,
                                  status_counts=dict(Counter(x['status'] for x in per_seed[min(SEEDS)])),
                                  identical_profile_rows=sum(x['status'] == 'NO_GAIN' and not x['profile_delta']
                                                             for x in per_seed[min(SEEDS)]),
                                  strictly_costlier_rows=sum(x['status'] == 'NO_GAIN' and bool(x['profile_delta']) and
                                                            Fraction(x['moment_delta']['lower']) > 0
                                                            for x in per_seed[min(SEEDS)]),
                                  guard_predicate_counts=dict(Counter(g['predicate']
                                      for x in per_seed[min(SEEDS)] for g in x.get('guard_failures', []))))
    selection_path = run / 'SELECTION.json'
    selection = read(selection_path) if selection_path.exists() else None
    common = sorted(set(favorable['base']) & set(favorable['extra']),
                    key=lambda cid: address_key(favorable['base'][cid]))
    selected = common[:protocol['retained_pair_limit']]
    if selection is None:
        need(False,
             'missing selection reconciles only with zero favorable rows')
        selection = dict(paired_favorable=0, selected_pair_keys=[], unretained_paired_favorable=0)
    need(selection['paired_favorable'] == len(common) and
         selection['selected_pair_keys'] == [favorable['base'][x]['pair_key'] for x in selected] and
         selection['unretained_paired_favorable'] == len(common)-len(selected),
         'first8 canonical matched candidates without post-hoc ranking')
    retained = {(s['seed'], s['provider'], s['candidate_id']): v
                for phase, s, v, _ in tasks if phase == 'retention'}
    need(set(retained) == {(s, p, cid) for s in SEEDS for p in PROVIDERS for cid in selected},
         'all retained candidates validated with both providers and seeds')
    for cid in selected:
        for provider in sorted(PROVIDERS):
            twins = [retained[s, provider, cid] for s in sorted(SEEDS)]
            need(clean(twins[0]) == clean(twins[1]), 'two-seed retained-word validation agreement')
            for v in twins:
                need(v['status'] == 'PASS_CANDIDATE', 'retained canonical construction passes')
                audit = v['independent_local_admission']
                need(audit['status'] == 'PASS' and audit['audit']['checked_columns'] == 632 and
                     audit['audit']['orientations'] == {'forward': 'PASS', 'dual': 'PASS'},
                     'all632 independent retained-word columns in both orientations')
                need(v['independent_rejecting_controls'] ==
                     dict(wrong_scalar=True, omitted_paid_child=True, omitted_cleanup=True),
                     'all three scientific mutation controls reject')
                need(not v['kappa_claim'] and v['fresh_native_admission'] == 'UNRUN_REQUIRED' and
                     v['complete_supplier_outer_admission'] == 'UNRUN_REQUIRED', 'finite scope preserved')
                reference(v['word'])
    unresolved = sum(s['status_counts'].get('EXPLORATORY', 0) for s in summaries.values())
    total = sum(s['candidates'] for s in summaries.values())
    expected = ('EXPLORATORY' if unresolved else 'PASS' if selected else 'EXPLORATORY'
                if any(favorable.values()) or total == 0 else 'NULL')
    if not reconcile:
        need(meta['status'] == expected, 'registered scientific disposition from saved coverage and exact signs')
    return dict(providers=summaries, selected_pairs=len(selected), unvalidated_paired=len(common)-len(selected),
                unresolved_rows=unresolved, decision_from_saved_records=expected)



def preserved_base():
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', BASE, '--', 'research/styles-r11/'], cwd=ROOT)
    count = 0
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        info, name = entry.split(b'\t', 1)
        _, kind, blob = info.split()
        need(kind == b'blob', 'ordinary pre-round evidence file')
        raw = (ROOT / name.decode()).read_bytes()
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode() == blob,
             'immutable prior evidence: ' + name.decode())
        count += 1
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    allowed = ('research/styles-r11/data/continuation-10/', 'research/styles-r11/pipeline/continuation10/',
               'research/styles-r11/results/CONTINUATION-10/')
    need(all(p.startswith(allowed) for p in changed+untracked), 'new continuation10 paths only; every prior file immutable')
    return count


def control_receipt(value, protocol):
    counts = value['checks_by_family']
    need(value['status'] == 'PASS' and value['inherited_control_checks'] == 3212 and
         value['checks'] == 3212 + sum(counts.values()) and
         all(type(n) is int and n > 0 for n in counts.values()), 'all saved inherited and new control counters passed')
    inherited = value['inherited_control_result_sha256']
    need(len(inherited) == 64 and all(c in '0123456789abcdef' for c in inherited), 'immutable inherited control digest')
    expected = dict(inherited_exact_twenty_corner_and_joint_controls=1,
                    shared_contact_positive=32, positive_old_full_invoice=32,
                    all24_interleavings_full_gather_and_invoice=384,
                    noncommuting_intervener_rejected=2, noncommuting_witness_oracle=2,
                    commutation_does_not_imply_frame_feasibility=1,
                    omitted_intervener_same_mass_detected=1, scale_self_add_exact_crossing=10,
                    invalid_scalar_typed_exclusion=3, invalid_scalar_gather_witness=6,
                    scale_touches_one_register=1, self_add_second_climb_zero=1,
                    outside_equality_rejected=1, equal_rank_wrong_frame_rejected=1,
                    outside_successors_remove_false_gain=1, gate_only_false_two_unit_saving=1,
                    stable_gather_legal=2, synthetic_source_positive=1,
                    integer_register_certificate_roundtrip=1, canonical_key_collision_rejected=1)
    need(all(counts.get(k) == n for k,n in expected.items()), 'fixed J2 signed/gather/invoice control coverage')
    for name in ('fixture_scalar_gather', 'fixture_full_operator', 'fixture_full_window_tariff',
                 'crossing_is_actual_adjacent_swap', 'stable_gather_exact_final_order',
                 'stable_unselected_order_and_frames'):
        need(counts.get(name, 0) > 0, 'registered direct gather/operator/invoice oracle: '+name)
    for name in ('missing_source_gate_rejected', 'duplicated_source_gate_rejected', 'stale_source_rejected',
                 'stale_interval_rejected', 'stale_plan_rejected', 'changed_source_coefficient_rejected',
                 'prelude_crossing_rejected', 'warp_crossing_rejected', 'section_crossing_rejected',
                 'hidden_virtual_alias_rejected'):
        need(counts.get(name) == 1, 'registered immutable preimage and barrier mutation: '+name)
    need(value['endpoint'] == protocol['comparison']['complex_endpoint'], 'fixed comparison endpoint in controls')
    return dict(total_checks=value['checks'], inherited_checks=3212, new_control_families=len(counts),
                inherited_control_result_sha256=inherited, all24_gather_control_cases=384,
                direct_window_operator_checks=counts['fixture_full_operator'],
                direct_window_tariff_checks=counts['fixture_full_window_tariff'])


def audit_attempt(row, attempt, original):
    version = attempt['attempt']
    run = ROUND / FAMILY / version
    detail = DATA / ('j2-' + version)
    meta = read(run / 'RUN.json')
    preg_path = ROUND / 'J2/PREREGISTRATION.json'
    protocol = read(preg_path)
    pins_path = ROUND / 'J2' / ('IMPLEMENTATION-PINS-' + version + '.json')
    pins = read(pins_path)
    implementation = read(run / 'IMPLEMENTATION.json')
    need(protocol['state'] == 'FROZEN' and set(protocol['seeds']) == SEEDS,
         'frozen family and both seeds')
    need(implementation['script_sha256'] == pins['sha256'] and
         implementation['preregistration_sha256'] == digest(preg_path.read_bytes()) and
         implementation['implementation_pins_sha256'] == digest(pins_path.read_bytes()), 'source/protocol freeze bindings')
    source_report = archives(pins, implementation)
    frozen_time = pins.get('registered_utc', pins.get('recorded_utc'))
    need(frozen_time is not None and pins.get('freeze_before_import_or_preparation') is True,
         'implementation frozen before preparation')
    need(datetime.fromisoformat(protocol['registered_utc']) <= datetime.fromisoformat(frozen_time),
         'registration precedes source freeze')
    need(implementation['parent_load_once'] is True and set(implementation['prepared']) == {'constructor'},
         'source and large objects prepared once in parent')
    references(protocol['inputs'])
    references(implementation['provenance'])
    comparison = implementation['provenance']['comparison']
    need(comparison['pr'] == 3030 and comparison['replicas'] == 740 and
         comparison['physical_families'] == 663549 and comparison['source_reported_only'] and
         comparison['fresh_native_physical_outer'] is False, 'source-reported comparator scope')
    need(meta['detailed_evidence_directory'] == str(detail.relative_to(PKG)), 'declared separate detailed-data namespace')
    indexed = set()
    for ref in meta['detailed_evidence']:
        path = reference(ref)
        need(path.is_relative_to(detail) and path not in indexed, 'unique confined detailed artifact')
        indexed.add(path)
    need(indexed == {p for p in detail.rglob('*') if p.is_file()}, 'all detailed artifact bytes authenticated')
    phases = {phase: read(detail / (phase.upper() + '-TASKS.json.gz')) for phase in meta['completed_by_phase']}
    visits = {phase: set() for phase in phases}
    results, tasks, statuses, rss, seconds = {}, [], Counter(), [], []
    task_cpu = 0.0
    for ref in meta['results']:
        result = read(reference(ref))
        seed = result['seed']
        need(seed in SEEDS and seed not in results, 'distinct registered seed result')
        results[seed] = result
        need(datetime.fromisoformat(result['recorded_utc']) >= datetime.fromisoformat(frozen_time),
             'result follows implementation freeze')
        need(result['status'] == meta['status'] == attempt['status'], 'attempt dispositions agree')
        need(result['script_sha256'] == pins['sha256'] and
             result['preregistration_sha256'] == digest(preg_path.read_bytes()) and
             result['implementation_pins_sha256'] == digest(pins_path.read_bytes()), 'RESULT exact scientific bindings')
        need(result['source_attribution'] == implementation['source_attribution'], 'complete source credits in each RESULT')
        credits(result, original)
        need(any(x.get('pr') == 3030 and x.get('author_login') == 'petalas' for x in result['source_attribution']),
             'Petalas comparison attribution')
        need(not result['decision']['pattern_claim'] and not result['decision']['kappa_claim'] and
             result['n_permutations'] == 0, 'finite census does not claim pattern or kappa admission')
        references(result.get('inputs', {}))
        for task_ref in result['task_receipts']:
            path = reference(task_ref)
            need(path in indexed, 'every RESULT task belongs to complete detailed inventory')
            phase = path.parent.name
            need(phase in phases, 'task belongs to launched phase')
            ordinal = int(path.name.split('.')[0].split('-')[-1])
            need(ordinal not in visits[phase] and 0 <= ordinal < len(phases[phase]), 'unique task address')
            visits[phase].add(ordinal)
            spec = phases[phase][ordinal]
            need(spec['seed'] == seed and spec['kind'] == phase, 'task phase and seed binding')
            receipt = read(path)
            statuses[receipt['status']] += 1
            rss.append(receipt.get('peak_rss_bytes') or 0)
            seconds.append(receipt.get('seconds') or 0)
            task_cpu += receipt.get('cpu_seconds') or 0
            if receipt['status'] == 'OK':
                value = receipt['result']
                need(value['seed'] == seed, 'task output seed')
                references(value)
                tasks.append((phase, spec, value, receipt))
            else:
                need(meta['failure'] is not None, 'infrastructure exception is not a scientific loss')
    need(set(results) == SEEDS, 'both distinct seed RESULTs')
    cpu = sum(x['cpu_seconds'] for x in results.values())
    need(abs(cpu - meta['total_cpu_seconds']) < 1e-5 and abs(cpu - attempt['cpu_seconds']) < 1e-5 and
         task_cpu <= cpu + 1e-5, 'scientific task and parent CPU accounted once')
    need(abs(meta['total_wall_seconds'] - attempt['wall_seconds']) < 1e-8, 'wall accounting')
    need(meta['workers'] == 61, 'central61-worker pool')
    for phase, seen in visits.items():
        need(len(seen) == meta['completed_by_phase'][phase], 'every completed task included once')
    projections = []
    for path in sorted(detail.glob('*MEMORY-PROJECTION.json')):
        value = read(path)
        need(value['workers'] == min(120, int(value['ram_gib']//4)) == 61 and
             value['reserved_cores'] >= 8 and value['worker_rss_cap_gib'] == 4 and
             value['working_set_gib'] == protocol['resources']['working_set_gib'] == 1.25 and
             value['projected_peak_gib'] < value['ram_gib'], 'worker, reserved-core and memory projection rules')
        projections.append(dict(path=str(path.relative_to(PKG)), sha256=digest(path.read_bytes()),
                                projected_peak_gib=value['projected_peak_gib']))
    need(len(projections) == len(phases) + 1, 'parent and every pool launch were projected')
    need(max(rss, default=0) <= 4*1024**3 and max(seconds, default=0) <= 301,
         'recorded4GiB RSS and300second task bounds')
    summary = dict(attempt=version, status=meta['status'], pool_tasks=sum(map(len, visits.values())),
                   completed_by_phase=meta['completed_by_phase'], pool_status_counts=dict(statuses),
                   cpu_seconds=cpu, worker_cpu_seconds=task_cpu, wall_seconds=meta['total_wall_seconds'],
                   max_worker_rss_bytes=max(rss, default=0), max_task_seconds=max(seconds, default=0),
                   source_archives=source_report, memory_projections=projections,
                   detailed_artifacts=len(indexed), detailed_bytes=sum(p.stat().st_size for p in indexed),
                   source_credits_per_result={str(s): len(v['source_attribution']) for s, v in results.items()})
    if meta['failure'] is not None:
        need(meta['status'] in {'ERROR', 'TIMEOUT'} and not meta['confirmed'], 'failed attempt preserved')
        summary['failure'] = meta['failure']
        return summary
    need(all(v['confirmed'] and v['scientific_decision_agreement'] and v['failure'] is None
             for v in results.values()) and meta['confirmed'], 'two-seed scientific decision agreement')
    expected = dict(controls=2, baseline=4, census=4, prices=256)
    if 'retention' in phases:
        expected['retention'] = len(phases['retention'])
        need(0 < expected['retention'] <= 32 and expected['retention'] % 4 == 0, 'bounded paired retention')
    need(meta['completed_by_phase'] == expected, 'complete registered phase coverage')
    controls = {}
    for phase, spec, value, _ in tasks:
        if phase in {'controls', 'baseline', 'census', 'prices'}:
            need(value['status'] == 'PASS', 'all primary controls and shards completed')
        if phase == 'controls':
            controls[str(spec['seed'])] = control_receipt(value, protocol)
        if phase == 'baseline':
            finite = value['local_admission']['audit']
            need(finite['checked_columns'] == finite['independent_inputs'] == 632 and
                 finite['orientations'] == {'forward': 'PASS', 'dual': 'PASS'} and
                 finite['restored_cold'] == finite['zero_buffers'] == 91,
                 'all632 baseline columns and91 restored buffers')
            need(value['word_source_declared_physical_families'] == 66813 and
                 value['comparison_source_declared_physical_families'] == 663549 and
                 value['comparison_replicas'] == 740 and value['fresh_native_physical_outer'] is False,
                 'baseline distinguishes word-source and comparison stock')
    for phase, seen in visits.items():
        need(seen == set(range(len(phases[phase]))), 'no omitted task in completed phase')
    for seed, result in results.items():
        need(result['statistics'] == meta['statistics'][str(seed)], 'RUN/RESULT statistics equality')
    need(clean(results[min(SEEDS)]['statistics']) == clean(results[max(SEEDS)]['statistics']),
         'two-seed aggregate statistics equality')
    for phase in ('controls', 'baseline'):
        groups = {}
        for actual_phase, spec, value, _ in tasks:
            if actual_phase == phase:
                groups.setdefault(spec.get('provider', 'all'), []).append(value)
        need(all(len(v) == 2 and clean(v[0]) == clean(v[1]) for v in groups.values()),
             'saved controls and baseline checks agree across seeds')
    summary['controls'] = controls
    summary['domain'] = saved_domain(tasks, results, protocol, meta, run)
    return summary


def build_audit():
    CHECKED_REFS.clear()
    registry = read(ROUND / 'EXPERIMENTS.json')
    task = read(ROUND / 'TASK.json')
    need(task['base_work_commit'] == BASE and registry['no_active_experiments'], 'closed pools and exact base')
    need('RUNNING' not in registry['status'].upper(), 'closed registry before final audit')
    original = read(PKG / 'data/words/PINS.json')['files']
    need(len(original) == 21, 'all original source credits')
    row = next(x for x in registry['experiments'] if x['id'] == FAMILY)
    need(row['execution'] in {'COMPLETED', 'INCOMPLETE'} and
         row['status'] in {'PASS', 'NULL', 'EXPLORATORY', 'ERROR', 'TIMEOUT'}, 'final scoped disposition')
    preg = ROUND / 'J2/PREREGISTRATION.json'
    need(row['preregistration_sha256'] == digest(preg.read_bytes()), 'registry preregistration pin')
    reports = [audit_attempt(row, attempt, original) for attempt in row['attempts']]
    need(abs(sum(x['cpu_seconds'] for x in reports) - row['cpu_seconds']) < 1e-5,
         'scientific attempts counted once')
    need(row['status'] == reports[-1]['status'] and row['cpu_seconds'] < task['round_cpu_budget_seconds'],
         'final attempt and round CPU budget')
    protocol = read(preg)
    acquisitions = [acquisition(ref) for name, ref in protocol['inputs'].items() if name.endswith('_acquisition')]
    preserved = preserved_base()
    documents = {name: digest((ROUND/name).read_bytes()) for name in
                 ('RESULTS.md', 'HANDBACK.md', 'PREDICTIONS.json', 'EXPERIMENTS.json', 'TASK.json')}
    checkpoints = {}
    for label in ('checkpoint', 'final_checkpoint', 'final-checkpoint'):
        path = DATA / label / 'RECEIPT.json'
        if not path.exists():
            need(label != 'checkpoint', 'initial checkpoint exists')
            continue
        receipt = read(path)
        need(not receipt['errors'], 'source checkpoint reports no suppressed errors')
        for relative, pin in receipt['files'].items():
            need(digest((path.parent/relative).read_bytes()) == pin['sha256'], 'checkpoint exact saved bytes')
        checkpoints[label] = dict(sha256=digest(path.read_bytes()), canonical_main=receipt['canonical_main'],
                                  priority_revision=receipt['priority_revision'], files=len(receipt['files']))
    destination = ROUND / 'AUDIT.json'
    sizes = {name: sum(p.stat().st_size for p in path.rglob('*') if p.is_file() and p != destination)
             for name, path in (('global_results', PKG/'results'), ('round_results', ROUND),
                                ('new_data', DATA), ('new_pipeline', Path(__file__).parent))}
    need(sizes['global_results'] < 200000000 and sizes['round_results'] < 1500000 and
         sizes['round_results'] + sizes['new_data'] + sizes['new_pipeline'] < 256000000,
         'global200MB, round1.5MB and all-new-evidence256MB caps')
    return dict(schema_version=1, status='PASS', kind='Administrative saved-byte audit; no scientific reruns',
                script_sha256=digest(Path(__file__).read_bytes()), base_work_commit=BASE,
                preserved_pre_round_files=preserved, experiments={FAMILY: reports},
                total_pool_tasks=sum(x['pool_tasks'] for x in reports),
                total_experimental_cpu_seconds=sum(x['cpu_seconds'] for x in reports),
                acquisitions=acquisitions, source_checkpoints=checkpoints, final_documents=documents,
                local_artifact_references_checked=len(CHECKED_REFS), storage_bytes_excluding_audit=sizes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    started = time.process_time()
    stable = build_audit()
    path = ROUND / 'AUDIT.json'
    if path.exists():
        need(read(path)['stable'] == stable, 'immutable administrative audit still agrees')
        print(json.dumps(dict(status='PASS', sha256=digest(path.read_bytes()), overwritten=False)))
        return
    value = dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
                 administrative_cpu_seconds=time.process_time()-started, stable=stable)
    raw = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
    sizes = stable['storage_bytes_excluding_audit']
    need(sizes['global_results']+len(raw) < 200000000 and sizes['round_results']+len(raw) < 1500000 and
         sizes['round_results']+sizes['new_data']+sizes['new_pipeline']+len(raw) < 256000000,
         'all storage caps include final audit bytes')
    if args.write:
        with path.open('xb') as stream:
            stream.write(raw)
    print(json.dumps(value, sort_keys=True))


if __name__ == '__main__':
    main()

