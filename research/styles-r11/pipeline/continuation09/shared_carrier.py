"""Two-target common-ratio carrier packets; coordinator execution only.

The source pair is injected.  Frozen continuation08 code supplies trusted
canonical frames/word parsing, never its source-specific prepare or census.
The twenty exact frame labels price one jointly restored carrier.  No result
from this local screen is a native, supplier, outer, or kappa admission.
"""
from __future__ import annotations

from collections import Counter, defaultdict
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
UTILITY_PATH = RR / 'pipeline/continuation08/carrier_factors.py'
UTILITY_SHA256 = '220532f217d78cd2cf77067372c5a80ac76c6e622bf2a2275f7e610149175f69'
SECTIONS = ('A', 'B')
MIDDLE_VERTICES = (('A1', 'A2'), ('K', 'A2'), ('U1', 'J'), ('U1', 'U2'), ('A1', 'U2'))
CORNERS = tuple((v, x, z) for v in range(5) for x in ('L', 'Y1') for z in ('Y2', 'D'))
_F = None
_WORDS = {}
_INSTALLED = {}
_ENDPOINT = None
_COSTS = {}


def need(test, message):
    if not test:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def _frozen():
    global _F
    if _F is None:
        need(hashlib.sha256(UTILITY_PATH.read_bytes()).hexdigest() == UTILITY_SHA256,
             'frozen carrier utility drift')
        need(not sys.flags.optimize, 'scientific assertions enabled')
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('styles09_frozen_carrier', UTILITY_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _F = module
    return _F


def _U():
    return _frozen()._util()


def _T():
    return _frozen()._T()


def _W():
    return _frozen()._W()


def _profile(value):
    return {int(k): int(v) for k, v in sorted(value.items(), key=lambda p: int(p[0])) if v}


def _mass(value):
    return sum(int(k)*int(v) for k, v in value.items())


def _dyadic(value):
    value = Q(value)
    return value != 0 and value.denominator & (value.denominator-1) == 0


def prepare(records, endpoint):
    """Coordinator parent loads each immutable word and nine costs once."""
    global _ENDPOINT, _COSTS
    need(not _WORDS, 'once-only joint carrier preparation')
    need(set(records) == {'base', 'extra'}, 'both source providers')
    _ENDPOINT = Q(endpoint)
    need(0 < _ENDPOINT < 1, 'strictly concave registered tariff')
    ceiling = _T()._module('ceiling')
    _COSTS = {r: ceiling.child_cost(r, 73, _ENDPOINT) for r in range(1, 10)}
    summary = {}
    for provider, record in sorted(records.items()):
        state = _frozen()._load_record(record)
        _WORDS[provider] = state
        summary[provider] = dict(parent_semantic_sha256=state['semantic_sha256'],
            local_profile=state['canonical'].paid, width_inventory=dict(Counter(state['widths'])),
            private_buffers=state['private_buffers'], physical_families=state['physical_families'],
            fixed_nodes=len(state['fixed']['nodes']), source_pin=state['source_pin'],
            source_attribution=state['attribution'])
    return dict(status='PASS', endpoint=str(_ENDPOINT), providers=summary,
        sections=list(SECTIONS), middle_vertices=[list(v) for v in MIDDLE_VERTICES],
        corners=[list(v) for v in CORNERS], target_orders=2, carriers=2,
        utility_source=dict(path=str(UTILITY_PATH.relative_to(RR)), sha256=UTILITY_SHA256),
        scope='Exact two-by-two common-ratio packets, four-register exposure, fixed exterior frames. No restore search or changed-word admission.')


def _packet(gates, kind, carrier=0, order=0, centres=()):
    """Recognize the complete rank-one 2x2 scalar block, independent of order."""
    if len(gates) != 4 or kind not in ('in', 'out') or carrier not in (0, 1) or order not in (0, 1):
        return None
    if not all(_T()._add(g) for g in gates):
        return None
    inners = sorted({g[1] if kind == 'in' else g[2] for g in gates})
    outers = sorted({g[2] if kind == 'in' else g[1] for g in gates})
    if len(inners) != 2 or len(outers) != 2 or len(set(inners+outers)) != 4:
        return None
    if set(inners+outers).intersection(centres):
        return None
    table = {}
    for g in gates:
        key = (g[1], g[2]) if kind == 'in' else (g[2], g[1])
        if key in table:
            return None
        table[key] = Q(g[3], g[4])
    if set(table) != set(itertools.product(inners, outers)):
        return None
    if carrier:
        outers.reverse()
    if order:
        inners.reverse()
    i1, i2 = inners
    j, k = outers
    a1, b1 = table[i1, j], table[i1, k]
    a2, b2 = table[i2, j], table[i2, k]
    if b1/a1 != b2/a2:
        return None
    ratio = b1/a1
    return dict(kind=kind, i1=i1, i2=i2, j=j, k=k,
                a1=str(a1), b1=str(b1), a2=str(a2), b2=str(b2),
                ratio=str(ratio), carrier=carrier, order=order,
                coefficient_admissible=_dyadic(ratio))


def _cid(address):
    return '.'.join(str(x) for x in address)


def _address(value):
    if isinstance(value, str):
        parts = value.split('.')
        need(len(parts) == 9, 'joint candidate address arity')
        return [parts[0], *(int(x) for x in parts[1:5]), parts[5],
                *(int(x) for x in parts[6:])]
    if isinstance(value, dict):
        result = list(value.get('address') or _address(value['candidate_id']))
        if 'candidate_id' in value:
            need(_cid(result) == value['candidate_id'], 'candidate ID/address binding')
        return result
    return list(value)


def _candidate(state, provider, address, allow_nondyadic=False):
    address = _address(address)
    if len(address) != 9:
        return None
    section, p0, p1, p2, p3, kind, carrier, order, corner = address
    positions = [p0, p1, p2, p3]
    raw = state['raw']
    if section not in SECTIONS or not all(type(p) is int for p in positions):
        return None
    if positions != sorted(set(positions)) or not (0 <= p0 < p3 < len(raw[section])):
        return None
    if carrier not in (0, 1) or order not in (0, 1) or corner not in range(20):
        return None
    if not _T()._same_segment(raw, section, positions):
        return None
    old = [raw[section][p] for p in positions]
    packet = _packet(old, kind, carrier, order, state.get('centres', set(raw.get('centers', []))))
    if packet is None or (not allow_nondyadic and not packet['coefficient_admissible']):
        return None
    support = {packet[k] for k in ('i1', 'i2', 'j', 'k')}
    selected = set(positions)
    if any(g[0] not in ('add', 'scale') or support.intersection(_W().registers(g))
           for p, g in enumerate(raw[section][p0:p3+1], p0) if p not in selected):
        return None
    compact = dict(candidate_id=_cid(address), pair_key=_cid(address), address=list(address))
    return dict(**compact, provider=provider, section=section, positions=positions, chain=packet,
        corner=corner, variant=list(CORNERS[corner]), original_gates=deepcopy(old),
        parent_semantic_sha256=state['semantic_sha256'], interval_sha256=digest(raw[section][p0:p3+1]),
        disjoint_intervening_count=p3-p0-3)


def _resolve(state, provider, value):
    if isinstance(value, dict) and 'parent_semantic_sha256' in value:
        need(value['parent_semantic_sha256'] == state['semantic_sha256'], 'stale source binding')
    candidate = _candidate(state, provider, _address(value))
    need(candidate is not None, 'invalid or excluded joint packet address')
    if isinstance(value, dict) and 'interval_sha256' in value:
        need(value['interval_sha256'] == candidate['interval_sha256'], 'stale interval preimage')
    return candidate


def _enumerate(provider, state=None, rejections=None):
    """Complete packets from consecutive contacts of each inner register.

    Every admissible packet gives two such pairs because all other contacts
    inside its window are forbidden.  Pair grouping is purely algebraic;
    the complete four-register exposure guard is then checked independently.
    """
    state = _WORDS[provider] if state is None else state
    T, W = _T(), _W()
    counts = Counter(segments=0, inner_contact_pair_records=0, grouped_pair_combinations=0,
        exposure_rejected_packets=0, eligible_packets=0, literal_four_gate_packets=0,
        exposed_packets=0, ratio_rejected_carriers=0, admissible_carrier_choices=0,
        candidates=0, preliminary_same_inner_combinations=0, preliminary_duplicate_position_combinations=0)
    packets = set()
    for section in SECTIONS:
        gates = state['raw'][section]
        for first, last in T._segments(state['raw'], section):
            counts['segments'] += 1
            groups = defaultdict(list)
            previous = {}
            for p in range(first, last):
                gate = gates[p]
                if T._add(gate):
                    for kind, at in (('in', 1), ('out', 2)):
                        inner = gate[at]
                        before = previous.get(inner)
                        if before is None or not T._add(gates[before]) or gates[before][at] != inner:
                            continue
                        old = gates[before]
                        outer_at = 3-at
                        outers = sorted((old[outer_at], gate[outer_at]))
                        if len(set([inner]+outers)) != 3 or set([inner]+outers) & state['centres']:
                            continue
                        coeff = {old[outer_at]: Q(old[3],old[4]), gate[outer_at]: Q(gate[3],gate[4])}
                        ratio = coeff[outers[1]]/coeff[outers[0]]
                        groups[(kind, *outers, ratio)].append((inner, before, p))
                        counts['inner_contact_pair_records'] += 1
                for register in W.registers(gate):
                    previous[register] = p
            for group, records in sorted(groups.items(), key=lambda v:tuple(str(x) for x in v[0])):
                kind = group[0]
                for left, right in itertools.combinations(records, 2):
                    counts['grouped_pair_combinations'] += 1
                    if left[0] == right[0]:
                        counts['preliminary_same_inner_combinations'] += 1
                        continue
                    positions = tuple(sorted(left[1:]+right[1:]))
                    if len(set(positions)) != 4:
                        counts['preliminary_duplicate_position_combinations'] += 1
                        continue
                    # Structural packets remain counted even if neither
                    # orientation has an admitted dyadic ratio.
                    found = _candidate(state, provider, [section,*positions,kind,0,0,0],
                                       allow_nondyadic=True) is not None
                    if not found:
                        counts['exposure_rejected_packets'] += 1
                        if rejections is not None:
                            old=[state['raw'][section][p] for p in positions]
                            packet=_packet(old,kind,0,0,state['centres'])
                            need(packet is not None,'exposure rejection has an algebraically valid packet')
                            support={packet[n] for n in ('i1','i2','j','k')}
                            selected=set(positions)
                            offending=next(((p,g) for p,g in enumerate(
                                state['raw'][section][positions[0]:positions[-1]+1],positions[0])
                                if p not in selected and (g[0] not in ('add','scale')
                                    or support.intersection(W.registers(g)))),None)
                            need(offending is not None,'every counted exposure rejection has a literal witness')
                            index,gate=offending
                            rejections.append(dict(predicate=('intervening_opcode' if gate[0] not in ('add','scale')
                                else 'intervening_contact'),address=[section,*positions,kind],
                                selected_support=sorted(support),offending_index=index,offending_gate=deepcopy(gate),
                                touched_packet_registers=sorted(support.intersection(W.registers(gate)))))
                        continue
                    packets.add((section,*positions,kind))
    candidates=[]
    for packet in sorted(packets, key=lambda v:(SECTIONS.index(v[0]),*v[1:])):
        section, *rest = packet
        positions, kind = rest[:4], rest[4]
        counts['eligible_packets'] += 1
        counts['kind_'+kind] += 1
        counts['section_'+section] += 1
        gap=positions[-1]-positions[0]-3
        counts['literal_four_gate_packets' if gap == 0 else 'exposed_packets'] += 1
        counts['max_disjoint_gap'] = max(counts['max_disjoint_gap'],gap)
        old=[state['raw'][section][p] for p in positions]
        for carrier in (0,1):
            selected=_packet(old,kind,carrier,0,state['centres'])
            need(selected is not None,'grouped packet must retain its common ratio')
            if not selected['coefficient_admissible']:
                counts['ratio_rejected_carriers'] += 1
                if rejections is not None:
                    ratio=Q(selected['ratio'])
                    need(ratio!=0 and ratio.denominator & (ratio.denominator-1)!=0,
                         'inadmissible carrier ratio has a non-power-of-two reduced denominator')
                    rejections.append(dict(predicate='non_dyadic_transport_ratio',
                        address=[section,*positions,kind,carrier],ratio=str(ratio),
                        reduced_numerator=ratio.numerator,reduced_denominator=ratio.denominator,
                        coefficients={name:selected[name] for name in ('a1','b1','a2','b2')},
                        carrier_registers=[selected['j'],selected['k']],
                        inner_registers=[selected['i1'],selected['i2']]))
                continue
            counts['admissible_carrier_choices'] += 1
            for order in (0,1):
                for corner in range(20):
                    address=[section,*positions,kind,carrier,order,corner]
                    candidates.append(dict(candidate_id=_cid(address),pair_key=_cid(address),address=address))
                    counts['candidates'] += 1
    candidates.sort(key=lambda c:(SECTIONS.index(c['address'][0]),*c['address'][1:]))
    need(len({c['candidate_id'] for c in candidates}) == len(candidates),'unique packet addresses')
    need(len(candidates) == 40*counts['admissible_carrier_choices'],'complete two-order twenty-label coverage')
    return candidates,dict(counts)


def census_task(spec):
    begin=time.process_time()
    provider,seed=spec['provider'],int(spec['seed'])
    exclusions=[]
    candidates,counts=_enumerate(provider,rejections=exclusions)
    exclusions.sort(key=lambda r:(SECTIONS.index(r['address'][0]),*r['address'][1:6],
                                  r['address'][6] if len(r['address'])>6 else -1,r['predicate']))
    need(len(exclusions)==counts['exposure_rejected_packets']+counts['ratio_rejected_carriers'],
         'every counted structural or ratio exclusion has one witness')
    state=_WORDS[provider]
    return dict(status='PASS',provider=provider,seed=seed,complete=True,candidates=candidates,
        exclusions=exclusions,exclusions_sha256=digest(exclusions),
        preliminary_combinations_scope='Same-inner and duplicate-position combinations are not four-register complete packets; counts are distinguished from certified exclusions',
        counts=counts,domain_sha256=digest(candidates),candidate_set_sha256=digest(candidates),
        parent_semantic_sha256=state['semantic_sha256'],source_pin=state['source_pin'],
        source_attribution=state['attribution'],source_sections=list(SECTIONS),
        restore_search=False,pricing_cap=None,cpu_seconds=time.process_time()-begin)


def install_census(provider,receipt):
    need(receipt['provider']==provider and receipt['status']=='PASS' and receipt['complete'],
         'complete source-bound census')
    need(receipt['parent_semantic_sha256']==_WORDS[provider]['semantic_sha256'],'census parent binding')
    need(digest(receipt['candidates'])==receipt['domain_sha256'],'census domain hash')
    need(digest(receipt['exclusions'])==receipt['exclusions_sha256'],'census exclusion-certificate hash')
    _INSTALLED[provider]=deepcopy(receipt['candidates'])


def _boundaries(state,candidate):
    fixed,section=state['fixed'],candidate['section']
    ids=[fixed['index'][section,p] for p in candidate['positions']]
    result={}
    for name in ('i1','i2','j','k'):
        raw_register=candidate['chain'][name]
        contacts=[]
        for node_id in ids:
            node=fixed['nodes'][node_id]
            mapping=dict(zip(node['raw_registers'],node['registers']))
            if raw_register in mapping:
                contacts.append((node_id,mapping[raw_register]))
        need(len(contacts)==2,'every packet register has exactly two selected contacts')
        aliases={r for _,r in contacts}
        need(len(aliases)==1,'packet cannot cross a hidden warp alias')
        virtual=contacts[0][1]
        before=fixed['previous'][contacts[0][0],virtual]
        after=fixed['following'][contacts[-1][0],virtual]
        need(before not in ids and after not in ids,'actual exterior contacts')
        prev_node,next_node=fixed['nodes'][before],fixed['nodes'][after]
        equality=((section=='A' and next_node['section']=='cut') or
                  (next_node['section']=='end' and virtual in fixed['eq_end']))
        result[name]=dict(register=raw_register,virtual_register=virtual,
            entry=list(prev_node['frame']),exit=list(next_node['frame']),equality_exit=equality,
            previous_node=before,next_node=after,
            previous_origin=[prev_node['section'],prev_node['raw_index']],
            next_origin=[next_node['section'],next_node['raw_index']])
    return result


def _frames(boundaries,corner):
    U=_U()
    E={k:U._basis(v['entry']) for k,v in boundaries.items()}
    O={k:U._basis(v['exit']) for k,v in boundaries.items()}
    L=U._join(E['j'],E['k'])
    A1=U._join(L,E['i1']); A2=U._join(A1,E['i2'])
    D=U._meet(O['j'],O['k']); U2=U._meet(D,O['i2']); U1=U._meet(U2,O['i1'])
    K=U._meet(A2,U1); J=U._join(A2,U1)
    f=dict(L=L,A1=A1,A2=A2,D=D,U1=U1,U2=U2,K=K,J=J)
    vertex,x,z=CORNERS[corner]
    y1,y2=MIDDLE_VERTICES[vertex]
    f['Y1'],f['Y2']=f[y1],f[y2]
    f['X'],f['Z']=f[x],f[z]
    failed=[]
    for low,high in (('A1','U1'),('A2','U2'),('L','X'),('X','Y1'),('A1','Y1'),
                     ('Y1','U1'),('Y1','Y2'),('A2','Y2'),('Y2','U2'),('Y2','Z'),('Z','D')):
        if not U._leq(f[low],f[high]):
            failed.append(dict(predicate='frame_inclusion',lower=low,upper=high,
                lower_frame=list(f[low]),upper_frame=list(f[high]),
                excluded_vector=next(v for v in f[low] if not U._leq((v,),f[high]))))
    final=dict(i1=f['Y1'],i2=f['Y2'],j=f['Z'],k=f['Z'])
    for name in ('i1','i2','j','k'):
        if not U._leq(final[name],O[name]):
            failed.append(dict(predicate='exit_inclusion',register=name,actual=list(final[name]),
                required=list(O[name]),excluded_vector=next(v for v in final[name] if not U._leq((v,),O[name]))))
        if boundaries[name]['equality_exit'] and final[name]!=O[name]:
            failed.append(dict(predicate='exit_equality',register=name,
                               actual=list(final[name]),required=list(O[name])))
    return f,failed


def _gate(target,source,coefficient,frame=()):
    q=Q(coefficient)
    return ['add',target,source,q.numerator,q.denominator,list(frame)]


def _replacement(candidate,frames):
    c=candidate['chain']; i1,i2,j,k=(c[n] for n in ('i1','i2','j','k'))
    a1,a2,q=Q(c['a1']),Q(c['a2']),Q(c['ratio'])
    if c['kind']=='in':
        return [_gate(j,k,q,frames['X']),_gate(i1,j,a1,frames['Y1']),
                _gate(i2,j,a2,frames['Y2']),_gate(j,k,-q,frames['Z'])]
    return [_gate(k,j,-q,frames['X']),_gate(j,i1,a1,frames['Y1']),
            _gate(j,i2,a2,frames['Y2']),_gate(k,j,q,frames['Z'])]


def _moment(delta):
    lo=hi=Q(0)
    for rank,count in delta.items():
        lower,upper=_COSTS[rank]
        lo+=count*(lower if count>=0 else upper)
        hi+=count*(upper if count>=0 else lower)
    return dict(lower=str(lo),upper=str(hi),endpoint=str(_ENDPOINT),exact_profile_identity=not delta)


def _screen(state,candidate,detailed=False):
    boundary=_boundaries(state,candidate)
    frames,failures=_frames(boundary,candidate['corner'])
    result={k:deepcopy(candidate[k]) for k in ('candidate_id','pair_key','address')}
    result.update(status='REJECTED_GUARD',profile_delta=None,moment_delta=None)
    if failures:
        result['guard_failures']=failures
        if detailed:
            result['proof']=dict(boundaries=boundary,frames={k:list(v) for k,v in frames.items()},failures=failures)
        return result
    old=candidate['original_gates']; new=_replacement(candidate,frames)
    T,U=_T(),_U()
    need(T._sequential_matrix(old)==T._sequential_matrix(new),'joint forward scalar identity')
    need(T._sequential_matrix(old,True)==T._sequential_matrix(new,True),'joint inverse-transpose identity')
    before,after=U._local_bill(old,boundary),U._local_bill(new,boundary)
    need(before['rank_mass']==after['rank_mass'],'complete twelve-term boundary mass')
    delta=Counter(after['profile']); delta.subtract(before['profile']); delta=_profile(delta)
    need(_mass(delta)==0,'signed boundary mass neutrality')
    moment=_moment(delta)
    if Q(moment['upper'])<0:
        status='PASS_CANDIDATE'
    elif not delta or Q(moment['lower'])>=0:
        status='NO_GAIN'
    else:
        status='EXPLORATORY'
    result.update(status=status,profile_delta=delta,moment_delta=moment,
                  boundary_mass=before['rank_mass'],forward_dual_identity=True)
    if detailed:
        result['proof']=dict(boundaries=boundary,frames={k:list(v) for k,v in frames.items()},
            original_window_bill=before,factored_window_bill=after,new_gates=new,failures=[],
            equality_exits=[k for k,v in boundary.items() if v['equality_exit']],
            interval_sha256=candidate['interval_sha256'],
            disjoint_intervening_count=candidate['disjoint_intervening_count'],
            literal_exterior_frames_frozen=True,corner=list(CORNERS[candidate['corner']]),
            middle_vertex=list(MIDDLE_VERTICES[CORNERS[candidate['corner']][0]]))
    return result


def shard_task(spec):
    begin=time.process_time()
    provider,seed=spec['provider'],int(spec['seed'])
    shard,shards=int(spec['shard']),int(spec.get('shards',64))
    need(shards==64 and 0<=shard<shards,'registered 64-shard partition')
    candidates=_INSTALLED.get(provider)
    if candidates is None:
        candidates,_=_enumerate(provider)
    indexed=[(i,c) for i,c in enumerate(candidates) if i%shards==shard]
    random.Random(seed).shuffle(indexed)
    rows,favorable=[],[]
    counts=Counter(candidates=len(indexed),PASS_CANDIDATE=0,NO_GAIN=0,REJECTED_GUARD=0,EXPLORATORY=0)
    for ordinal,compact in indexed:
        candidate=_resolve(_WORDS[provider],provider,compact)
        row=_screen(_WORDS[provider],candidate)
        row['ordinal']=ordinal
        rows.append(row); counts[row['status']]+=1
        if row['status']=='PASS_CANDIDATE':
            favorable.append(deepcopy(row))
    rows.sort(key=lambda r:r['ordinal']); favorable.sort(key=lambda r:r['ordinal'])
    counts['unresolved']=counts['EXPLORATORY']; state=_WORDS[provider]
    return dict(status='PASS',provider=provider,seed=seed,shard=shard,shards=shards,
        complete=True,counts=dict(counts),rows=rows,favorable=favorable,
        domain_sha256=digest(candidates),shard_rows_sha256=digest(rows),
        parent_semantic_sha256=state['semantic_sha256'],source_attribution=state['attribution'],
        source_pin=state['source_pin'],canonical_full_words_built=0,primitive_cost_included=False,
        scope='Complete exact joint boundary screen; no native, full allocation, supplier, or outer admission.',
        cpu_seconds=time.process_time()-begin)


def _materialize(state,candidate,screening):
    need(screening['profile_delta'] is not None,'materialize only feasible label')
    need(digest(state['raw'])==state['semantic_sha256'],'unchanged parent in memory')
    T,U,W=_T(),_U(),_W()
    section=candidate['section']; positions=candidate['positions']; p,q=positions[0],positions[-1]
    raw=state['raw']; selected=set(positions)
    middle=[deepcopy(g) for index,g in enumerate(raw[section][p:q+1],p) if index not in selected]
    new_gates=screening['proof']['new_gates']
    old_window=raw[section][p:q+1]; new_window=deepcopy(new_gates)+middle
    need(len(new_window)==len(old_window),'joint two-target scalar count preserved')
    for dual in (False,True):
        need(_frozen()._window_matrix(old_window,dual)==_frozen()._window_matrix(new_window,dual),
             'complete exposed-window forward/dual identity')
    edited=deepcopy(raw)
    edited[section]=deepcopy(raw[section][:p])+new_window+deepcopy(raw[section][q+1:])
    need(edited[section][:p]==raw[section][:p] and edited[section][q+1:]==raw[section][q+1:],
         'exact exterior scalar prefix and suffix')
    need(edited[section][p+4:q+1]==middle,'all disjoint intervening gates retain order and frames')
    need(edited['warps']==raw['warps'],'no positional warp shift for equal-count replacement')
    if section=='B':
        need(not any(p<rec[0]<=q for rec in raw['warps']),'no hidden B barrier')
    for other in ('A','B','restore'):
        if other!=section:
            need(edited[other]==raw[other],'other scalar sections unchanged')
    need(T._boundary_signature(edited)==state['boundaries'],'fixed interfaces and compensation')
    npre=int(raw.get('prelude_events',0))
    need(edited['A'][:npre]==raw['A'][:npre],'literal prelude preserved')
    word=W.WordData(edited,state['attribution'],assert_profile=False); old=state['canonical']
    need(word.helpers==old.helpers and word.start==old.start and word.end==old.end,
         'ordered helpers and exact endpoints')
    need(T._widths(word)==state['widths'],'ordered helper widths')
    expected=Counter(old.paid); expected.update(screening['profile_delta'])
    need(all(n>=0 for n in expected.values()),'nonnegative canonical counts')
    need(_profile(expected)==word.paid,'independent canonical and boundary ledger parity')
    need(_mass(word.paid)==_mass(old.paid),'complete canonical rank mass')
    edited['report']['local_profile']={str(r):n for r,n in sorted(word.paid.items())}
    edited['cleanup']=W.derived_borrow_cleanup(word)
    checked=W.WordData(edited,state['attribution'])
    need(checked.paid==word.paid,'regenerated cleanup preserves paid ledger')
    return edited,checked


def build_candidate(provider,candidate_id):
    state=_WORDS[provider]; candidate=_resolve(state,provider,candidate_id)
    screening=_screen(state,candidate,detailed=True)
    if screening['profile_delta'] is None:
        return None,screening
    raw,canonical=_materialize(state,candidate,screening)
    screening.update(local_profile=canonical.paid,width_inventory=dict(Counter(state['widths'])),
        ordered_widths=state['widths'],canonical_profile_and_boundary_delta_agree=True,
        semantic_sha256=digest(raw),cleanup_sha256=digest(raw['cleanup']))
    return raw,screening


def validate_selected(spec):
    begin=time.process_time(); provider,seed=spec['provider'],int(spec['seed'])
    candidate_id=spec.get('candidate_id') or spec['candidate']['candidate_id']
    raw,result=build_candidate(provider,candidate_id); state=_WORDS[provider]
    result.update(provider=provider,seed=seed,word=None,source_pin=state['source_pin'],
        source_attribution=state['attribution'],private_buffers=state['private_buffers'],
        physical_families=state['physical_families'],physical_families_scope='Inherited word-source metadata; not the current comparator allocation or a candidate global invoice',
        native_admission=False,scalar_instruction_delta=0,
        fresh_all_column_audit='Required separate coordinator phase; unchanged net operator is not fresh native admission')
    if raw is not None and result['status']=='PASS_CANDIDATE':
        directory=Path(spec['output_dir'])
        if not directory.is_absolute():
            directory=RR/directory
        directory=directory.resolve()
        need(directory.is_relative_to((RR/'data/continuation-09/candidates').resolve()),
             'retained words restricted to continuation09 candidate data')
        result['word']=_T()._write_word(raw,directory/provider,candidate_id)
    result['cpu_seconds']=time.process_time()-begin
    return result


def _small_flag_controls(check):
    """Independent exact set oracle, with nontrivial intersection/join vertices."""
    def span(vectors):
        result={0}
        for vector in vectors:
            result|={x^vector for x in tuple(result)}
        return frozenset(result)
    def spaces(ambient):
        return sorted({span(v) for n in range(ambient+1)
                       for v in itertools.combinations(range(1,1<<ambient),n)},
                      key=lambda s:(len(s),tuple(sorted(s))))
    def dim(space):
        return len(space).bit_length()-1
    fixtures=[
        ('joint_positive',3,[[1],[1],[],[]],[[1],[1],[1,2],[1,2]],()),
        ('intersection_join',3,[[],[2,4],[],[]],[[1,2],[1,2,4],[1,2,4],[1,2,4]],()),
        ('all_five_vertices',4,[[],[1,2],[],[]],[[1,4],[1,2,4,8],[1,2,4,8],[1,2,4,8]],()),
        ('target1_equality',3,[[],[],[],[]],[[3],[1,2],[1,2,4],[1,2,4]],('i1',)),
        ('target2_equality',3,[[],[],[],[]],[[1,2],[1,2],[1,2,4],[1,2,4]],('i2',)),
        ('outer_equality',3,[[],[],[],[]],[[1],[1,2],[1,2],[1,2]],('j',)),
        ('all_equalities',3,[[1],[1],[],[]],[[1],[1],[1,2],[1,2]],('i1','i2','j','k')),
        ('infeasible_bound',3,[[4],[],[],[]],[[1],[1,2],[1,2],[1,2]],()),
    ]
    names=('i1','i2','j','k'); reports=[]; cache={}
    tariffs=[tuple(map(Q,(0,6,10,13,15))),tuple(map(Q,(0,1,2,3,4))),
             (Q(0),Q(1),Q(3,2),Q(7,4),Q(15,8))]
    for fixture,ambient,entry,exit_frames,equalities in fixtures:
        if ambient not in cache:
            cache[ambient]=spaces(ambient)
        universe=cache[ambient]
        check('oracle_subspace_count',len(universe)==(16 if ambient==3 else 67))
        E={k:span(v) for k,v in zip(names,entry)}; O={k:span(v) for k,v in zip(names,exit_frames)}
        boundary={k:dict(register=r,entry=entry[n],exit=exit_frames[n],equality_exit=k in equalities)
                  for n,(k,r) in enumerate(zip(names,(3,6,4,5)))}
        def feasible(X,Y1,Y2,Z):
            final=dict(i1=Y1,i2=Y2,j=Z,k=Z)
            return (E['j']<=X and E['k']<=X and E['i1']<=Y1 and E['i2']<=Y2
                and X<=Y1<=Y2<=Z and all(final[k]<=O[k] for k in names)
                and all(final[k]==O[k] for k in equalities))
        # Enumerate all actual subspaces, pruning only necessary inclusions.
        flags=[]
        for Y1 in universe:
            if not E['i1']<=Y1<=O['i1']:
                continue
            for Y2 in universe:
                if not Y1<=Y2 or not E['i2']<=Y2<=O['i2']:
                    continue
                for X in universe:
                    if not E['j']<=X<=Y1 or not E['k']<=X:
                        continue
                    for Z in universe:
                        if feasible(X,Y1,Y2,Z):
                            flags.append((X,Y1,Y2,Z))
        def bill(flag,tariff):
            X,Y1,Y2,Z=flag
            # Independent direct contact-chain invoice, not the polygon formula.
            current=dict(E); result=Q(0)
            for support,frame in ((('j','k'),X),(('i1','j'),Y1),(('i2','j'),Y2),(('j','k'),Z)):
                for name in support:
                    result+=tariff[dim(frame)-dim(current[name])]; current[name]=frame
            return result+sum(tariff[dim(O[k])-dim(current[k])] for k in names)
        corners=[]
        if fixture=='all_five_vertices':
            f,_=_frames(boundary,0)
            check('oracle_explicit_intersection_vertex',span(f['K'])==span([1]))
            check('oracle_explicit_join_vertex',span(f['J'])==span([1,2,4]))
            check('oracle_five_distinct_middle_vertices',len({(span(f[a]),span(f[b])) for a,b in MIDDLE_VERTICES})==5)
        for index in range(20):
            f,failures=_frames(boundary,index)
            flag=tuple(span(f[k]) for k in ('X','Y1','Y2','Z'))
            check('oracle_corner_guard',feasible(*flag)==(not failures))
            if not failures:
                corners.append(flag)
        check('oracle_feasibility',bool(flags)==bool(corners))
        minima=[]
        for tariff in tariffs:
            best=min((bill(flag,tariff) for flag in flags),default=None)
            corner_best=min((bill(flag,tariff) for flag in corners),default=None)
            check('oracle_twenty_corner_minimum',best==corner_best)
            minima.append(None if best is None else str(best))
        reports.append(dict(fixture=fixture,ambient=ambient,subspaces=len(universe),
            complete_cartesian_flag_domain=len(universe)**4,feasible_flags=len(flags),
            feasible_corner_labels=len(corners),exact_minima=minima,
            independent_set_arithmetic=True,all_successor_charges=True))
    return reports


def controls_task(spec):
    seed=int(spec['seed']) if isinstance(spec,dict) else int(spec)
    begin=time.process_time(); checks=Counter()
    def check(name,test):
        need(test,'joint carrier control: '+name); checks[name]+=1
    def rejects(name,fn):
        try:
            fn()
        except (ValueError,AssertionError):
            check(name,True)
        else:
            check(name,False)
    T,U=_T(),_U()
    positive_boundary={k:dict(register=r,entry=([1] if k.startswith('i') else []),
        exit=([1] if k.startswith('i') else [1,2]),equality_exit=False)
        for k,r in zip(('i1','i2','j','k'),(3,6,4,5))}
    positive_frames=dict(X=(),Y1=(1,),Y2=(1,),Z=(1,2))
    grid=(-2,-1,Q(-1,2),Q(1,2),1,2)
    for a,q in itertools.product(grid,repeat=2):
        aa=(Q(a),-Q(a)/2)
        for kind in ('in','out'):
            old=[]
            for inner,coefficient in zip((3,6),aa):
                old.extend([_gate(inner,4,coefficient),_gate(inner,5,coefficient*q)] if kind=='in'
                    else [_gate(4,inner,coefficient),_gate(5,inner,coefficient*q)])
            for carrier,order in itertools.product((0,1),repeat=2):
                packet=_packet(old,kind,carrier,order)
                check('recognizer_signed_dyadic',packet is not None and packet['coefficient_admissible'])
                new=_replacement(dict(chain=packet),dict(X=(),Y1=(),Y2=(),Z=()))
                framed_old=[g[:-1]+[[1]] for g in old]
                framed_new=_replacement(dict(chain=packet),positive_frames)
                old_invoice=U._local_bill(framed_old,positive_boundary)
                new_invoice=U._local_bill(framed_new,positive_boundary)
                joint_delta=Counter(new_invoice['profile']);joint_delta.subtract(old_invoice['profile'])
                check('joint_signed_both_kinds_carriers_orders',_profile(joint_delta)=={1:-2,2:1} and old_invoice['rank_mass']==new_invoice['rank_mass'])
                for dual in (False,True):
                    expected=T._sequential_matrix(old,dual)
                    check('signed_forward_dual_identity',expected==T._sequential_matrix(new,dual))
                    wrong=deepcopy(new); wrong[-1][3]*=-1
                    check('wrong_undo_sign',expected!=T._sequential_matrix(wrong,dual))
                    check('missing_undo',expected!=T._sequential_matrix(new[:-1],dual))
                    wrong=deepcopy(new); wrong[2][3]*=2
                    check('wrong_second_target_coefficient',expected!=T._sequential_matrix(wrong,dual))
    old=[_gate(3,4,1,[1]),_gate(3,5,1,[1]),_gate(6,4,1,[1]),_gate(6,5,1,[1])]
    for permutation in itertools.permutations(range(4)):
        permuted=[old[i] for i in permutation]
        check('all_four_edge_interleavings',_packet(permuted,'in') is not None)
        synthetic_raw=dict(A=deepcopy(permuted),B=[],warps=[],prelude_events=0,centers=[])
        synthetic_state=dict(raw=synthetic_raw,centres=set(),semantic_sha256=digest(synthetic_raw))
        synthetic_candidates,synthetic_counts=_enumerate('synthetic_control',synthetic_state)
        check('all_interleavings_complete_census',len(synthetic_candidates)==160
              and synthetic_counts['eligible_packets']==2
              and synthetic_counts['admissible_carrier_choices']==4
              and {c['address'][5] for c in synthetic_candidates}=={'in','out'})
    wrong=deepcopy(old); wrong[-1][3]=2
    check('unequal_target_ratios',_packet(wrong,'in') is None)
    wrong=deepcopy(old); wrong[-1]=deepcopy(wrong[-2])
    check('duplicate_edge',_packet(wrong,'in') is None)
    check('centre_exclusion',_packet(old,'in',centres={4}) is None)
    check('missing_edge',_packet(old[:-1],'in') is None)
    wrong=deepcopy(old);wrong[0][3]=0
    check('zero_original_coefficient',_packet(wrong,'in') is None)
    wrong=deepcopy(old);wrong[0][4]=3
    check('nondyadic_original_coefficient',_packet(wrong,'in') is None)
    wrong=deepcopy(old);wrong[0][2]=wrong[0][1]
    check('repeated_register_alias',_packet(wrong,'in') is None)
    wrong=[_gate(3,4,Q(3,2)),_gate(3,5,1),_gate(6,4,3),_gate(6,5,2)]
    check('non_dyadic_orientation',not _packet(wrong,'in')['coefficient_admissible'])
    check('admitted_reverse_orientation',_packet(wrong,'in',carrier=1)['coefficient_admissible'])
    ratio_raw=dict(A=deepcopy(wrong),B=[],warps=[],prelude_events=0,centers=[])
    ratio_state=dict(raw=ratio_raw,centres=set(),semantic_sha256=digest(ratio_raw))
    ratio_exclusions=[]
    _,ratio_counts=_enumerate('ratio_control',ratio_state,rejections=ratio_exclusions)
    check('ratio_exclusion_recorded',ratio_counts['ratio_rejected_carriers']==1 and len(ratio_exclusions)==1)
    witness=ratio_exclusions[0]
    check('ratio_exclusion_exact_certificate',witness['predicate']=='non_dyadic_transport_ratio'
          and Q(witness['ratio'])==Q(witness['coefficients']['b1'])/Q(witness['coefficients']['a1'])
          and Q(witness['ratio'])==Q(witness['coefficients']['b2'])/Q(witness['coefficients']['a2'])
          and witness['reduced_denominator']==3)
    boundary={k:dict(register=r,entry=([1] if k.startswith('i') else []),
              exit=([1] if k.startswith('i') else [1,2]),equality_exit=False)
              for k,r in zip(('i1','i2','j','k'),(3,6,4,5))}
    old_bill=U._local_bill(old,boundary)
    deltas=[]
    for corner in range(20):
        frames,failed=_frames(boundary,corner)
        if failed:
            continue
        new=_replacement(dict(chain=_packet(old,'in')),frames)
        bill=U._local_bill(new,boundary)
        delta=Counter(bill['profile']);delta.subtract(old_bill['profile']);delta=_profile(delta)
        check('joint_fixture_mass',_mass(delta)==0)
        if delta=={1:-2,2:1}:
            deltas.append(delta)
            check('joint_fixture_strict_exact_tariff',Q(_moment(delta)['upper'])<0)
    check('joint_fixture_has_strict_gain',bool(deltas))
    for inner,first in ((3,True),(6,False)):
        single_boundary=dict(i=dict(register=inner,entry=[1],exit=[1],equality_exit=False),
            j=dict(register=4,entry=[] if first else [1],exit=[1] if first else [1,2],equality_exit=False),
            k=dict(register=5,entry=[] if first else [1],exit=[1] if first else [1,2],equality_exit=False))
        pair=[g for g in old if g[1]==inner]; before=U._local_bill(pair,single_boundary)
        for carrier in (0,1):
            fan=_frozen()._fan(pair,(),carrier)
            for index in range(8):
                f,failed=_frozen()._frames(single_boundary,index)
                if failed:
                    continue
                after=U._local_bill(_frozen()._replacement(dict(chain=fan),f),single_boundary)
                check('each_single_factor_neutral',before['profile']==after['profile'])
    # Guard fixtures use literal metadata only, never a source-word search.
    raw=dict(A=deepcopy(old),B=deepcopy(old),warps=[],prelude_events=0,centers=[])
    state=dict(raw=raw,centres=set(),semantic_sha256=digest(raw))
    address=['A',0,1,2,3,'in',0,0,0]
    check('literal_packet_guard',_candidate(state,'fixture',address) is not None)
    excluded=deepcopy(state);excluded['raw']['restore']=deepcopy(old)
    check('restore_section_excluded',_candidate(excluded,'fixture',['restore',0,1,2,3,'in',0,0,0]) is None)
    altered=deepcopy(state); altered['raw']['A'].insert(2,_gate(3,9,1))
    check('extra_involved_contact_rejected',_candidate(altered,'fixture',['A',0,1,3,4,'in',0,0,0]) is None)
    exposure_raw=dict(A=deepcopy(old),B=[],warps=[],prelude_events=0,centers=[])
    exposure_raw['A'].insert(2,_gate(9,4,1))
    exposure_state=dict(raw=exposure_raw,centres=set(),semantic_sha256=digest(exposure_raw))
    exposure_exclusions=[]
    _,exposure_counts=_enumerate('exposure_control',exposure_state,rejections=exposure_exclusions)
    check('exposure_exclusion_recorded',exposure_counts['exposure_rejected_packets']==1 and len(exposure_exclusions)==1)
    witness=exposure_exclusions[0]
    check('exposure_exclusion_exact_certificate',witness['predicate']=='intervening_contact'
          and witness['offending_index']==2 and witness['offending_gate']==exposure_raw['A'][2]
          and witness['touched_packet_registers']==[4])
    exposed=deepcopy(state); exposed['raw']['A'].insert(2,_gate(8,9,Q(1,2)))
    check('disjoint_intervener_admitted',_candidate(exposed,'fixture',['A',0,1,3,4,'in',0,0,0]) is not None)
    warped=deepcopy(state); warped['raw']['warps']=[[2,4,[],[]]]
    check('hidden_warp_barrier_rejected',_candidate(warped,'fixture',['B',0,1,2,3,'in',0,0,0]) is None)
    prelude=deepcopy(state);prelude['raw']['prelude_events']=1
    check('prelude_barrier_rejected',_candidate(prelude,'fixture',address) is None)
    stale=dict(candidate_id=_cid(address),parent_semantic_sha256='0'*64)
    rejects('stale_source_rejected',lambda:_resolve(state,'fixture',stale))
    stale=dict(candidate_id=_cid(address),interval_sha256='0'*64)
    rejects('stale_preimage_rejected',lambda:_resolve(state,'fixture',stale))
    # Full successor bill must differ from an invoice silently ending at last gates.
    positive=next((_frames(boundary,c)[0] for c in range(20)
                   if not _frames(boundary,c)[1] and _frames(boundary,c)[0]['Z']==_U()._basis([1])),None)
    check('successor_fixture_exists',positive is not None)
    gates=_replacement(dict(chain=_packet(old,'in')),positive)
    complete=U._local_bill(gates,boundary)
    omitted=Counter(j['rank'] for j in complete['jumps'] if j['origin']=='gate' and j['rank'])
    check('omitted_successor_charge_detected',_profile(omitted)!=complete['profile'] and _mass(omitted)<complete['rank_mass'])
    oracle=_small_flag_controls(check)
    return dict(status='PASS',seed=seed,checks=sum(checks.values()),checks_by_family=dict(sorted(checks.items())),
        independent_flag_oracle=oracle,endpoint=str(_ENDPOINT),
        joint_fixture=dict(old_profile=old_bill['profile'],strict_delta={1:-2,2:1},
            every_single_factor_exactly_neutral=True,scalar_count_before=4,scalar_count_after=4),
        source_attribution={p:s['attribution'] for p,s in _WORDS.items()},
        scope='Synthetic registered controls only; no source candidate census or native admission.',
        cpu_seconds=time.process_time()-begin)
