"""Exact commuting exposure of fixed saved J1 packets; coordinator runs only.

Two stable gathers, full-window tariffs, no intermediate frame-feasibility
requirement.  Frozen utilities and all inherited source credits are retained.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import gzip
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys
import time

RR=Path(__file__).resolve().parents[2]
UTILITY_PATH=RR/'pipeline/continuation09/shared_carrier.py'
UTILITY_SHA256='6c8b9b40bdfabf575f5f4b687541cbd3a20f5c10d44720b95c12dfc5e1570c47'
SECTIONS=('A','B')
_J=None
_WORDS={}
_DOMAINS={}
_DOMAIN_PINS={}
_INSTALLED={}
_PLANS={}
_ENDPOINT=None


def need(ok,message):
    if not ok:raise ValueError(message)


def _canonical(value):
    """Stable across JSON round trips, including integer register/profile keys."""
    if isinstance(value,dict):
        result={}
        for key,item in value.items():
            key=str(key);need(key not in result,'canonical mapping key collision')
            result[key]=_canonical(item)
        return result
    if isinstance(value,(list,tuple)):return [_canonical(item) for item in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(_canonical(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _joint():
    global _J
    if _J is None:
        need(hashlib.sha256(UTILITY_PATH.read_bytes()).hexdigest()==UTILITY_SHA256,'frozen joint utility drift')
        need(not sys.flags.optimize,'scientific assertions enabled')
        sys.dont_write_bytecode=True
        spec=importlib.util.spec_from_file_location('styles10_frozen_joint',UTILITY_PATH)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
        spec.loader.exec_module(module);_J=module
    return _J


def _U():return _joint()._U()
def _T():return _joint()._T()
def _W():return _joint()._W()
def _profile(value):return _joint()._profile(value)
def _mass(value):return _joint()._mass(value)
def _gate(*args,**kwargs):return _joint()._gate(*args,**kwargs)
def _cid(address):return '.'.join(str(x) for x in address)


def prepare(records,endpoint,domains):
    """Once in the registered parent; no new source-domain enumeration."""
    global _ENDPOINT
    need(not _WORDS and set(domains)==set(records)=={'base','extra'},'once-only two-provider preparation')
    _ENDPOINT=Q(endpoint)
    summary=_joint().prepare(records,_ENDPOINT)
    for provider,state in _joint()._WORDS.items():
        _WORDS[provider]=state
        # The literal utility may put a self-add node twice in a register
        # chain.  Its second paid climb is zero; exterior neighbors must skip
        # repeated occurrences of that same node.
        before,after={},{}
        for register,chain in enumerate(state['fixed']['chains']):
            unique=[]
            for node in chain:
                if not unique or unique[-1]!=node:unique.append(node)
            for left,right in zip(unique,unique[1:]):
                after[left,register]=right;before[right,register]=left
        state['distinct_previous']=before;state['distinct_following']=after
        envelope=domains[provider];receipt=envelope['receipt'];pin=deepcopy(envelope['source_pin'])
        source=(RR/pin['path']).resolve()
        need(source.is_relative_to(RR) and source.suffix!='.py','confined saved J1 data')
        payload=source.read_bytes()
        need(hashlib.sha256(payload).hexdigest()==pin['sha256'],'saved domain bytes')
        if 'bytes' in pin:need(len(payload)==pin['bytes'],'saved domain byte count')
        authenticated=json.loads(gzip.decompress(payload) if source.suffix=='.gz' else payload)
        need(authenticated.get('status')=='OK' and authenticated.get('result')==receipt,
             'supplied domain is exactly the authenticated saved pool result')
        need(receipt['provider']==provider and receipt['status']=='PASS' and receipt['complete'],
             'complete saved J1 census')
        need(receipt['parent_semantic_sha256']==state['semantic_sha256'],'same source word as J1')
        need(digest(receipt['exclusions'])==receipt['exclusions_sha256'],'saved exclusion digest')
        need(not receipt['candidates'] and receipt['counts']['exposure_rejected_packets']==2878,
             'registered empty J1 source domain and fixed excluded-address count')
        rows=receipt['exclusions']
        need(all(r['predicate']=='intervening_contact' and len(r['address'])==6 for r in rows),
             'only saved exposure-excluded four-edge addresses')
        addresses=[tuple(r['address']) for r in rows]
        need(len(set(addresses))==len(addresses)==2878,'unique fixed saved packet addresses')
        _DOMAINS[provider]=tuple(sorted(addresses,key=lambda a:(SECTIONS.index(a[0]),*a[1:])))
        _DOMAIN_PINS[provider]=dict(source_pin=pin,exclusions_sha256=receipt['exclusions_sha256'],
            saved_seed=receipt['seed'],address_count=len(addresses),addresses_sha256=digest(_DOMAINS[provider]))
    return dict(status='PASS',endpoint=str(_ENDPOINT),providers=summary['providers'],
        domains=_DOMAIN_PINS,placements={'0':'gather_left','1':'gather_right'},
        utility_source=dict(path=str(UTILITY_PATH.relative_to(RR)),sha256=UTILITY_SHA256),
        scope='Saved J1 addresses only; scalar crossing certificates plus final full-window frame tariff. No fresh native or global allocation admission.')


def _address(value):
    if isinstance(value,str):
        p=value.split('.');need(len(p)==10,'J2 address arity')
        return [p[0],*(int(x) for x in p[1:5]),p[5],*(int(x) for x in p[6:])]
    if isinstance(value,dict):
        result=list(value.get('address') or _address(value['candidate_id']))
        if 'candidate_id' in value:need(_cid(result)==value['candidate_id'],'candidate ID/address')
        return result
    return list(value)


def _source_packet(state,address):
    section,*tail=address;positions=list(tail[:4]);kind=tail[4]
    need(section in SECTIONS and positions==sorted(set(positions)) and len(positions)==4,'saved packet shape')
    need(0<=positions[0]<positions[-1]<len(state['raw'][section]),'saved packet positions')
    need(_T()._same_segment(state['raw'],section,positions),'immutable section/prelude/warp barriers')
    old=[state['raw'][section][p] for p in positions]
    packet=_joint()._packet(old,kind,0,0,state['centres'])
    need(packet is not None,'saved exact rank-one four-register packet')
    return old,packet


def _matrix(gates,dual=False):return _joint()._frozen()._window_matrix(gates,dual)


def _first_difference(left,right):
    for row in sorted(set(left)|set(right)):
        for col in sorted(set(left.get(row,{}))|set(right.get(row,{}))):
            a=left.get(row,{}).get(col,Q(0));b=right.get(row,{}).get(col,Q(0))
            if a!=b:return dict(row=row,column=col,left=str(a),right=str(b))
    return None


def _commute(g,h):
    """Exact selected-add crossing certificate; frames do not enter this test."""
    need(_T()._add(g),'selected packet operation is a nonzero nonself dyadic add')
    if not isinstance(h,list) or not h or h[0] not in ('add','scale'):
        return dict(commutes=False,method='scalar_precondition',reason='unsupported_opcode',
                    opcode=h[0] if isinstance(h,list) and h else None,pair_hash=digest([g,h]))
    if h[0]=='scale':
        multiplier=Q(h[2],h[3])
    elif h[1]==h[2]:
        multiplier=1+Q(h[3],h[4])
    else:multiplier=None
    if multiplier==0:
        return dict(commutes=False,method='scalar_precondition',reason='singular_scale' if h[0]=='scale' else 'singular_self_add',
                    register=h[1],multiplier='0',pair_hash=digest([g,h]))
    if _T()._add(h):
        first=g[2]!=h[1];second=h[2]!=g[1]
        return dict(commutes=first and second,method='add_guard',
            selected_source_differs_unselected_target=first,
            unselected_source_differs_selected_target=second)
    forward_left,forward_right=_matrix([g,h]),_matrix([h,g])
    dual_left,dual_right=_matrix([g,h],True),_matrix([h,g],True)
    forward_equal=forward_left==forward_right;dual_equal=dual_left==dual_right
    need(forward_equal==dual_equal,'invertible forward/dual pair agreement')
    result=dict(commutes=forward_equal,method='pair_matrix',pair_hash=digest([g,h]),
                forward_equal=forward_equal,dual_equal=dual_equal)
    if not forward_equal:result['first_difference']=_first_difference(forward_left,forward_right)
    return result


def _gather(window,positions,start,placement):
    """Stable adjacent-crossing log; intermediate frames are deliberately ignored."""
    need(placement in (0,1),'two fixed gather placements')
    selected=tuple(positions);selected_set=set(selected)
    unselected=tuple(p for p in range(start,start+len(window)) if p not in selected_set)
    log=[]
    moving=selected if placement==0 else selected[::-1]
    for p in moving:
        crossed=tuple(q for q in unselected if q<p)[::-1] if placement==0 else tuple(q for q in unselected if q>p)
        for q in crossed:
            g,h=window[p-start],window[q-start]
            cert=_commute(g,h)
            if not cert['commutes']:
                predicate='scalar_crossing_precondition' if cert['method']=='scalar_precondition' else 'noncommuting_crossing'
                return dict(legal=False,crossings=log,failure=dict(predicate=predicate,
                    selected_index=p,unselected_index=q,selected_gate=deepcopy(g),unselected_gate=deepcopy(h),
                    commutation=cert,verified_prefix_count=len(log)))
            item=dict(selected_index=p,unselected_index=q,method=cert['method'])
            if cert['method']=='pair_matrix':
                item.update(pair_hash=cert['pair_hash'],forward_equal=True,dual_equal=True)
            log.append(item)
    order=list(selected+unselected if placement==0 else unselected+selected)
    return dict(legal=True,crossings=log,gathered_order=order)


def _plan_identity(state,address):
    return digest(dict(parent_semantic_sha256=state['semantic_sha256'],address=address))


def _enumerate(provider):
    state=_WORDS[provider];candidates=[];plans={};exclusions=[]
    counts=Counter(source_excluded_addresses=len(_DOMAINS[provider]),placements_considered=0,
        commuting_placements=0,noncommuting_placements=0,ratio_rejected_carriers=0,
        scalar_precondition_rejected_placements=0,admissible_carrier_choices=0,candidates=0,crossings_verified=0)
    for base in _DOMAINS[provider]:
        section=base[0];positions=list(base[1:5]);kind=base[5]
        old,packet=_source_packet(state,base)
        window=state['raw'][section][positions[0]:positions[-1]+1]
        for placement in (0,1):
            counts['placements_considered']+=1
            plan_address=[*base,placement]
            gather=_gather(window,positions,positions[0],placement)
            counts['crossings_verified']+=len(gather['crossings'])
            if not gather['legal']:
                counts['scalar_precondition_rejected_placements' if gather['failure']['predicate']=='scalar_crossing_precondition'
                       else 'noncommuting_placements']+=1
                exclusions.append(dict(gather['failure'],plan_address=plan_address))
                continue
            ordinal=len(plans);plan_id=_plan_identity(state,plan_address)
            plan=dict(plan_id=plan_id,plan_ordinal=ordinal,address=plan_address,
                crossings=gather['crossings'],crossings_sha256=digest(gather['crossings']),
                gathered_order_sha256=digest(gather['gathered_order']),interval_sha256=digest(window),
                parent_semantic_sha256=state['semantic_sha256'])
            plans[plan_id]=plan;counts['commuting_placements']+=1
            for carrier in (0,1):
                c=_joint()._packet(old,kind,carrier,0,state['centres'])
                need(c is not None,'gather preserves rank-one packet')
                if not c['coefficient_admissible']:
                    counts['ratio_rejected_carriers']+=1
                    ratio=Q(c['ratio'])
                    exclusions.append(dict(predicate='non_dyadic_transport_ratio',
                        address=[*base,placement,carrier],plan_id=plan_id,ratio=str(ratio),
                        reduced_numerator=ratio.numerator,reduced_denominator=ratio.denominator,
                        coefficients={n:c[n] for n in ('a1','b1','a2','b2')}))
                    continue
                counts['admissible_carrier_choices']+=1
                for order,corner in itertools.product((0,1),range(20)):
                    address=[*base,placement,carrier,order,corner]
                    candidates.append(dict(candidate_id=_cid(address),pair_key=_cid(address),address=address,
                        plan_id=plan_id,plan_ordinal=ordinal))
                    counts['candidates']+=1
    need(len(candidates)==40*counts['admissible_carrier_choices'],'complete order/corner coverage')
    need(len({c['candidate_id'] for c in candidates})==len(candidates),'unique candidate addresses')
    need(len(exclusions)==counts['noncommuting_placements']+counts['scalar_precondition_rejected_placements']+counts['ratio_rejected_carriers'],
         'every scalar exclusion has an explicit witness')
    return candidates,plans,exclusions,dict(counts)


def census_task(spec):
    begin=time.process_time();provider,seed=spec['provider'],int(spec['seed'])
    candidates,plans,exclusions,counts=_enumerate(provider);state=_WORDS[provider]
    return dict(status='PASS',provider=provider,seed=seed,complete=True,candidates=candidates,
        plans=plans,plans_sha256=digest(plans),exclusions=exclusions,exclusions_sha256=digest(exclusions),
        counts=counts,domain_sha256=digest(candidates),candidate_set_sha256=digest(candidates),
        parent_semantic_sha256=state['semantic_sha256'],source_pin=state['source_pin'],
        source_attribution=state['attribution'],saved_domain=_DOMAIN_PINS[provider],
        source_sections=list(SECTIONS),restore_search=False,pricing_cap=None,
        sharding='plan_ordinal modulo 64; each plan retains every carrier/order/corner label',
        cpu_seconds=time.process_time()-begin)


def install_census(provider,receipt):
    need(receipt['status']=='PASS' and receipt['complete'] and receipt['provider']==provider,'complete census')
    need(receipt['parent_semantic_sha256']==_WORDS[provider]['semantic_sha256'],'census parent')
    for key in ('plans','exclusions'):
        need(digest(receipt[key])==receipt[key+'_sha256'],'census '+key+' hash')
    need(digest(receipt['candidates'])==receipt['domain_sha256'],'census candidate hash')
    _INSTALLED[provider]=receipt['candidates'];_PLANS[provider]=receipt['plans']


def _window_boundaries(state,section,start,end):
    fixed=state['fixed'];contacts=defaultdict(list)
    ids=[fixed['index'][section,p] for p in range(start,end+1)]
    for node_id in ids:
        node=fixed['nodes'][node_id]
        for raw_register,virtual in dict(zip(node['raw_registers'],node['registers'])).items():
            contacts[raw_register].append((node_id,virtual))
    boundaries={}
    for register,chain in contacts.items():
        aliases={r for _,r in chain};need(len(aliases)==1,'no hidden alias change in complete window')
        virtual=chain[0][1]
        left=state['distinct_previous'][chain[0][0],virtual]
        right=state['distinct_following'][chain[-1][0],virtual]
        need(left not in ids and right not in ids,'whole-window boundaries are exterior')
        before,after=fixed['nodes'][left],fixed['nodes'][right]
        equality=(section=='A' and after['section']=='cut') or (after['section']=='end' and virtual in fixed['eq_end'])
        boundaries[register]=dict(register=register,virtual_register=virtual,entry=list(before['frame']),
            exit=list(after['frame']),equality_exit=equality,previous_node=left,next_node=right,
            previous_origin=[before['section'],before['raw_index']],next_origin=[after['section'],after['raw_index']])
    return boundaries


def _bill(gates,boundaries,positions=None,phase='window',detailed=False):
    """Complete actual-register invoice: scale touches one, self-add's second climb is zero."""
    U=_U();current={r:U._basis(v['entry']) for r,v in boundaries.items()};profile=Counter();jumps=[]
    indices=list(range(len(gates))) if positions is None else list(positions)
    need(len(indices)==len(gates),'bill origin positions')
    for index,gate in zip(indices,gates):
        frame=U._basis(gate[-1] or ())
        for register in _W().registers(gate):
            need(register in current,'every touched register has whole-window boundaries')
            before=current[register]
            if not U._leq(before,frame):
                return dict(valid=False,failures=[dict(predicate='window_frame_inclusion',phase=phase,
                    origin='gate',index=index,register=register,actual=list(before),required=list(frame),
                    excluded_vector=next(v for v in before if not U._leq((v,),frame)))])
            rank=len(frame)-len(before)
            if rank:profile[rank]+=1
            if detailed:jumps.append(dict(register=register,index=index,origin='gate',rank=rank,before=list(before),after=list(frame)))
            current[register]=frame
    for register,record in sorted(boundaries.items()):
        frame=U._basis(record['exit']);before=current[register]
        if not U._leq(before,frame):
            return dict(valid=False,failures=[dict(predicate='window_frame_inclusion',phase=phase,
                origin='outside_successor',index=record.get('next_origin'),register=register,
                actual=list(before),required=list(frame),
                excluded_vector=next(v for v in before if not U._leq((v,),frame)))])
        if record['equality_exit'] and before!=frame:
            return dict(valid=False,failures=[dict(predicate='window_exit_equality',phase=phase,
                origin='outside_successor',index=record.get('next_origin'),register=register,
                actual=list(before),required=list(frame))])
        rank=len(frame)-len(before)
        if rank:profile[rank]+=1
        if detailed:jumps.append(dict(register=register,index=record.get('next_origin'),origin='outside_successor',
                                      rank=rank,before=list(before),after=list(frame),equality_exit=record['equality_exit']))
    result=dict(valid=True,profile=dict(sorted(profile.items())),rank_mass=_mass(profile),failures=[])
    if detailed:result['jumps']=jumps
    return result


def _prepare_context(window,positions,start,support,placement,outer):
    selected=set(positions)
    unchanged=[(start+n,g) for n,g in enumerate(window) if start+n not in selected]
    before=_bill(window,outer,range(start,start+len(window)),phase='original')
    need(before['valid'],'unchanged source full-window invoice must be feasible')
    block={};constant=deepcopy(outer)
    for register in support:
        contacts=[(p,g) for p,g in unchanged if register in _W().registers(g)]
        record=deepcopy(outer[register])
        if placement==0:
            record['exit']=list(contacts[0][1][-1] or ()) if contacts else list(record['exit'])
            record['equality_exit']=False if contacts else record['equality_exit']
            if contacts:record['next_origin']=['unchanged_window',contacts[0][0]]
            constant[register]['entry']=list(record['exit'])
        else:
            record['entry']=list(contacts[-1][1][-1] or ()) if contacts else list(record['entry'])
            if contacts:record['previous_origin']=['unchanged_window',contacts[-1][0]]
            constant[register]['exit']=list(record['entry']);constant[register]['equality_exit']=False
        block[register]=record
    fixed=_bill([g for _,g in unchanged],constant,[p for p,_ in unchanged],phase='fixed_contacts')
    return dict(window=window,positions=positions,start=start,placement=placement,outer=outer,
        unchanged=unchanged,block_boundaries=block,constant_boundaries=constant,
        original_bill=before,fixed_bill=fixed,support=sorted(support))


def _context(state,plan):
    section,*tail=plan['address'];positions=tail[:4];kind=tail[4];placement=tail[5]
    old,packet=_source_packet(state,[section,*positions,kind])
    start,end=positions[0],positions[-1];window=state['raw'][section][start:end+1]
    need(digest(window)==plan['interval_sha256'],'immutable source interval')
    support={packet[k] for k in ('i1','i2','j','k')}
    outer=_window_boundaries(state,section,start,end)
    context=_prepare_context(window,positions,start,support,placement,outer)
    context.update(section=section,plan_id=plan['plan_id'],plan=plan,original_gates=old)
    return context


def _candidate(state,compact):
    address=_address(compact)
    section,p0,p1,p2,p3,kind,placement,carrier,order,corner=address
    base=(section,p0,p1,p2,p3,kind)
    if 'parent_semantic_sha256' in compact:
        need(compact['parent_semantic_sha256']==state['semantic_sha256'],'stale source binding')
    need(base in _DOMAINS[compact['provider']] if 'provider' in compact else True,'fixed saved address membership')
    need(placement in (0,1) and carrier in (0,1) and order in (0,1) and corner in range(20),'registered label')
    old,packet=_source_packet(state,base)
    if 'interval_sha256' in compact:
        need(compact['interval_sha256']==digest(state['raw'][section][p0:p3+1]),'stale interval preimage')
    need(compact['plan_id']==_plan_identity(state,address[:7]),'candidate plan/address binding')
    packet=_joint()._packet(old,kind,carrier,order,state['centres'])
    need(packet is not None and packet['coefficient_admissible'],'admissible exact carrier ratio')
    return dict(candidate_id=_cid(address),pair_key=_cid(address),address=address,
        chain=packet,corner=corner,placement=placement,section=section,positions=[p0,p1,p2,p3],
        plan_id=compact['plan_id'],plan_ordinal=compact['plan_ordinal'],original_gates=old,
        parent_semantic_sha256=state['semantic_sha256'])


def _screen(context,candidate,detailed=False):
    result=dict(candidate_id=candidate['candidate_id'],status='REJECTED_GUARD')
    if not context['fixed_bill']['valid']:
        result['guard_failures']=context['fixed_bill']['failures'];return result
    boundaries={name:context['block_boundaries'][candidate['chain'][name]] for name in ('i1','i2','j','k')}
    frames,failures=_joint()._frames(boundaries,candidate['corner'])
    if failures:
        result['guard_failures']=failures;return result
    new=_joint()._replacement(candidate,frames)
    block_bill=_bill(new,{r:context['block_boundaries'][r] for r in context['support']},phase='factor_block',detailed=detailed)
    need(block_bill['valid'],'twenty-corner guards imply factor-block feasibility')
    total=Counter(context['fixed_bill']['profile']);total.update(block_bill['profile']);total=_profile(total)
    need(_mass(total)==context['original_bill']['rank_mass'],'complete window including all successors conserves rank mass')
    delta=Counter(total);delta.subtract(context['original_bill']['profile']);delta=_profile(delta)
    moment=_joint()._moment(delta)
    status=('PASS_CANDIDATE' if Q(moment['upper'])<0 else
            'NO_GAIN' if not delta or Q(moment['lower'])>=0 else 'EXPLORATORY')
    result.update(status=status,profile_delta=delta,moment_delta=moment)
    if detailed:
        result['proof']=dict(block_boundaries=boundaries,whole_window_boundaries=context['outer'],
            frames={k:list(v) for k,v in frames.items()},new_gates=new,
            original_window_bill=context['original_bill'],fixed_contact_bill=context['fixed_bill'],
            factor_block_bill=block_bill,complete_new_window_profile=total,
            complete_rank_mass=_mass(total),centre_payments_unchanged=True,
            includes_all_unchanged_interveners_and_outside_successors=True,
            intermediate_frame_feasibility_required=False,
            crossings_sha256=context['plan']['crossings_sha256'])
    return result


def shard_task(spec):
    begin=time.process_time();provider,seed=spec['provider'],int(spec['seed'])
    shard,shards=int(spec['shard']),int(spec.get('shards',64))
    need(shards==64 and 0<=shard<shards,'64 fixed plan shards')
    need(provider in _INSTALLED,'parent must install two-seed-agreed census')
    grouped=defaultdict(list)
    for ordinal,compact in enumerate(_INSTALLED[provider]):
        if compact['plan_ordinal']%shards==shard:grouped[compact['plan_id']].append((ordinal,compact))
    plan_ids=sorted(grouped,key=lambda p:_PLANS[provider][p]['plan_ordinal']);random.Random(seed).shuffle(plan_ids)
    rows=[];favorable=[];tariffs={};guards={};window_certificates={}
    counts=Counter(candidates=sum(map(len,grouped.values())),plans=len(plan_ids),PASS_CANDIDATE=0,
                   NO_GAIN=0,REJECTED_GUARD=0,EXPLORATORY=0)
    state=_WORDS[provider]
    for plan_id in plan_ids:
        plan=_PLANS[provider][plan_id];context=_context(state,plan)
        window_certificates[plan_id]=dict(original_window_bill=context['original_bill'],
            fixed_contact_bill=context['fixed_bill'],block_boundaries=context['block_boundaries'],
            whole_window_boundaries=context['outer'],
            whole_window_boundaries_sha256=digest(context['outer']),
            interval_sha256=plan['interval_sha256'],crossings_sha256=plan['crossings_sha256'])
        for ordinal,compact in grouped[plan_id]:
            candidate=_candidate(state,compact);result=_screen(context,candidate)
            row=dict(ordinal=ordinal,candidate_id=candidate['candidate_id'],status=result['status'],
                     plan_id=plan_id,plan_ordinal=plan['plan_ordinal'])
            if result['status']=='REJECTED_GUARD':
                failures=result['guard_failures'];ref=digest(failures);guards[ref]=failures;row['failure_id']=ref
            else:
                certificate={k:result[k] for k in ('profile_delta','moment_delta')}
                ref=digest(certificate);tariffs[ref]=certificate;row['tariff_id']=ref
            rows.append(row);counts[row['status']]+=1
            if row['status']=='PASS_CANDIDATE':
                favorable.append(dict(row,address=candidate['address'],pair_key=candidate['pair_key'],
                    profile_delta=result['profile_delta'],moment_delta=result['moment_delta']))
        # No plan-sized cache survives this loop iteration.
    rows.sort(key=lambda r:r['ordinal']);favorable.sort(key=lambda r:r['ordinal'])
    counts['unresolved']=counts['EXPLORATORY']
    return dict(status='PASS',provider=provider,seed=seed,shard=shard,shards=shards,complete=True,
        counts=dict(counts),rows=rows,favorable=favorable,tariff_certificates=tariffs,
        guard_certificates=guards,window_certificates=window_certificates,
        tariff_certificates_sha256=digest(tariffs),guard_certificates_sha256=digest(guards),
        window_certificates_sha256=digest(window_certificates),shard_rows_sha256=digest(rows),
        domain_sha256=digest(_INSTALLED[provider]),plans_sha256=digest(_PLANS[provider]),
        parent_semantic_sha256=state['semantic_sha256'],
        source_attribution=state['attribution'],source_pin=state['source_pin'],saved_domain=_DOMAIN_PINS[provider],
        primitive_cost_included=False,canonical_full_words_built=0,
        scope='Final complete-window recursive tariff; no intermediate frame guard and no native/global admission.',
        cpu_seconds=time.process_time()-begin)


def _materialize(state,context,candidate,result):
    need(result['status']!='REJECTED_GUARD','feasible final factor required')
    raw=state['raw'];section=candidate['section'];p,q=candidate['positions'][0],candidate['positions'][-1]
    replay=_gather(context['window'],candidate['positions'],p,candidate['placement']);plan=context['plan']
    need(replay['legal'] and replay['crossings']==plan['crossings'],'retained fresh exact crossing replay')
    need(digest(replay['crossings'])==plan['crossings_sha256'] and
         digest(replay['gathered_order'])==plan['gathered_order_sha256'] and
         digest(context['window'])==plan['interval_sha256'],'retained source and gather hashes')
    new_gates=result['proof']['new_gates'];unchanged=[deepcopy(g) for _,g in context['unchanged']]
    new_window=deepcopy(new_gates)+unchanged if candidate['placement']==0 else unchanged+deepcopy(new_gates)
    need(len(new_window)==len(context['window']),'four-to-four window length')
    for dual in (False,True):
        need(_matrix(context['window'],dual)==_matrix(new_window,dual),'complete original/new window forward and dual operator')
    bill=_bill(new_window,context['outer'],range(p,q+1),phase='final',detailed=True)
    need(bill['valid'],'fresh final whole-window chain feasibility')
    need(bill['profile']==result['proof']['complete_new_window_profile'],'direct full-window versus constant/block ledger')
    edited=deepcopy(raw);edited[section]=deepcopy(raw[section][:p])+new_window+deepcopy(raw[section][q+1:])
    need(edited[section][:p]==raw[section][:p] and edited[section][q+1:]==raw[section][q+1:],'fixed scalar exterior')
    need(edited['warps']==raw['warps'],'all warp positions remain unchanged')
    for other in ('A','B','restore'):
        if other!=section:need(edited[other]==raw[other],'other scalar sections fixed')
    need(_T()._boundary_signature(edited)==state['boundaries'],'fixed interfaces and compensation')
    npre=int(raw.get('prelude_events',0));need(edited['A'][:npre]==raw['A'][:npre],'literal prelude fixed')
    W=_W();canonical=W.WordData(edited,state['attribution'],assert_profile=False);old=state['canonical']
    need(canonical.helpers==old.helpers and canonical.start==old.start and canonical.end==old.end,'ordered exact helper endpoints')
    need(_T()._widths(canonical)==state['widths'],'ordered helper widths')
    expected=Counter(old.paid);expected.update(result['profile_delta'])
    need(all(v>=0 for v in expected.values()) and _profile(expected)==canonical.paid,'canonical full-word versus complete-window profile parity')
    need(_mass(canonical.paid)==_mass(old.paid),'complete local rank mass')
    edited['report']['local_profile']={str(r):n for r,n in sorted(canonical.paid.items())}
    edited['cleanup']=W.derived_borrow_cleanup(canonical);checked=W.WordData(edited,state['attribution'])
    need(checked.paid==canonical.paid,'fresh cleanup and full canonical profile')
    result['proof']['direct_final_window_bill']=bill
    result['proof']['retained_crossing_plan_replayed']=True
    return edited,checked


def build_candidate(provider,candidate_id):
    address=_address(candidate_id);state=_WORDS[provider]
    need(tuple(address[:6]) in _DOMAINS[provider],'retained address belongs to fixed saved domain')
    plan_id=_plan_identity(state,address[:7]);need(plan_id in _PLANS[provider],'retained scalar-legal plan')
    plan=_PLANS[provider][plan_id]
    compact=dict(candidate_id=candidate_id,address=address,plan_id=plan_id,plan_ordinal=plan['plan_ordinal'])
    candidate=_candidate(state,compact);context=_context(state,plan);result=_screen(context,candidate,detailed=True)
    result.update(pair_key=candidate['pair_key'],address=address,plan_id=plan_id,plan_ordinal=plan['plan_ordinal'])
    if result['status']=='REJECTED_GUARD':return None,result
    raw,canonical=_materialize(state,context,candidate,result)
    result.update(local_profile=canonical.paid,width_inventory=dict(Counter(state['widths'])),ordered_widths=state['widths'],
        canonical_profile_and_boundary_delta_agree=True,complete_window_invoice_verified=True,
        semantic_sha256=digest(raw),cleanup_sha256=digest(raw['cleanup']))
    return raw,result


def validate_selected(spec):
    begin=time.process_time();provider,seed=spec['provider'],int(spec['seed'])
    candidate_id=spec.get('candidate_id') or spec['candidate']['candidate_id']
    raw,result=build_candidate(provider,candidate_id);state=_WORDS[provider]
    result.update(provider=provider,seed=seed,word=None,source_pin=state['source_pin'],source_attribution=state['attribution'],
        saved_domain=_DOMAIN_PINS[provider],private_buffers=state['private_buffers'],
        word_source_physical_families=state['physical_families'],native_admission=False,scalar_instruction_delta=0,
        fresh_all_column_audit='Required separately; inherited native evidence does not admit changed words')
    if raw is not None and result['status']=='PASS_CANDIDATE':
        directory=Path(spec['output_dir']);directory=directory if directory.is_absolute() else RR/directory
        directory=directory.resolve()
        need(directory.is_relative_to((RR/'data/continuation-10/candidates').resolve()),'new retained data subtree only')
        result['word']=_T()._write_word(raw,directory/provider,candidate_id)
    result['cpu_seconds']=time.process_time()-begin
    return result


def controls_task(spec):
    seed=int(spec['seed']) if isinstance(spec,dict) else int(spec);begin=time.process_time();checks=Counter()
    def check(name,value):need(value,'J2 control: '+name);checks[name]+=1
    def rejects(name,call):
        try:call()
        except (AssertionError,ValueError):check(name,True)
        else:check(name,False)
    inherited=_joint().controls_task(seed)
    check('inherited_exact_twenty_corner_and_joint_controls',inherited['status']=='PASS')
    def outer(entries,exits,equalities=()):
        return {r:dict(register=r,entry=list(entries[r]),exit=list(exits[r]),equality_exit=r in equalities)
                for r in entries}
    def replay_gather(old,selected,placement,gather):
        origins=list(range(len(old)))
        for crossing in gather['crossings']:
            a=origins.index(crossing['selected_index']);b=origins.index(crossing['unselected_index'])
            check('crossing_is_actual_adjacent_swap',abs(a-b)==1)
            origins[a],origins[b]=origins[b],origins[a]
        check('stable_gather_exact_final_order',origins==gather['gathered_order'])
        unselected=[p for p in range(len(old)) if p not in selected]
        check('stable_unselected_order_and_frames',[old[p] for p in origins if p not in selected]==[old[p] for p in unselected])
    def evaluate(old,selected,bounds,kind,placement,carrier=0,order=0,corners=range(20)):
        gather=_gather(old,selected,0,placement)
        check('fixture_scalar_gather',gather['legal'])
        replay_gather(old,selected,placement,gather)
        packet=_joint()._packet([old[p] for p in selected],kind,carrier,order)
        support={packet[k] for k in ('i1','i2','j','k')}
        context=_prepare_context(old,selected,0,support,placement,bounds)
        context['plan']=dict(crossings_sha256=digest(gather['crossings']))
        outcomes=[]
        for corner in corners:
            candidate=dict(chain=packet,corner=corner,candidate_id='synthetic',original_gates=[old[p] for p in selected])
            result=_screen(context,candidate,detailed=True)
            if result['status']!='REJECTED_GUARD':
                new=result['proof']['new_gates'];rest=[g for p,g in enumerate(old) if p not in selected]
                full=new+rest if placement==0 else rest+new
                for dual in (False,True):check('fixture_full_operator',_matrix(old,dual)==_matrix(full,dual))
                full_bill=_bill(full,bounds,phase='control')
                check('fixture_full_window_tariff',full_bill['valid'] and full_bill['profile']==result['proof']['complete_new_window_profile'])
                outcomes.append(result)
        return context,outcomes
    # Same-target/shared-source contacts commute but violated J1 disjointness.
    for kind,carrier,order,placement in itertools.product(('in','out'),(0,1),(0,1),(0,1)):
        for sign in (-1,1):
            a1=Q(sign,2);a2=-Q(sign);ratio=Q(-2)
            pair1=[_gate(3,4,a1,[1]),_gate(3,5,a1*ratio,[1])] if kind=='in' else [_gate(4,3,a1,[1]),_gate(5,3,a1*ratio,[1])]
            pair2=[_gate(6,4,a2,[1]),_gate(6,5,a2*ratio,[1])] if kind=='in' else [_gate(4,6,a2,[1]),_gate(5,6,a2*ratio,[1])]
            h=_gate(3,7,1,[1]) if kind=='in' else _gate(7,3,1,[1])
            old=pair1+[h]+pair2;selected=[0,1,3,4]
            bounds=outer({3:[1],6:[1],4:[],5:[],7:[1]}, {3:[1],6:[1],4:[1,2],5:[1,2],7:[1]})
            context,outcomes=evaluate(old,selected,bounds,kind,placement,carrier,order)
            check('shared_contact_positive',any(r.get('profile_delta')=={1:-2,2:1} and r['status']=='PASS_CANDIDATE' for r in outcomes))
            check('positive_old_full_invoice',context['original_bill']['profile']=={1:4})
    # Exercise the actual stable gather on every four-edge interleaving, not
    # merely the order-insensitive rank-one recognizer.  The independent J1
    # oracle covers all twenty flags; here corner1 is the strict gain fixture.
    for kind in ('in','out'):
        edges=[_gate(i,j,1,[1]) if kind=='in' else _gate(j,i,1,[1])
               for i in (3,6) for j in (4,5)]
        h=_gate(3,7,1,[1]) if kind=='in' else _gate(7,3,1,[1])
        bounds=outer({3:[1],6:[1],4:[],5:[],7:[1]},
                     {3:[1],6:[1],4:[1,2],5:[1,2],7:[1]})
        for permutation in itertools.permutations(range(4)):
            arranged=[edges[p] for p in permutation];old=arranged[:2]+[h]+arranged[2:]
            for placement,carrier,order in itertools.product((0,1),(0,1),(0,1)):
                _,outcomes=evaluate(old,[0,1,3,4],bounds,kind,placement,carrier,order,corners=(1,))
                check('all24_interleavings_full_gather_and_invoice',len(outcomes)==1 and
                      outcomes[0]['profile_delta']=={1:-2,2:1} and outcomes[0]['status']=='PASS_CANDIDATE')
    old=[_gate(3,4,1,[1]),_gate(3,5,1,[1]),_gate(4,6,1,[1]),_gate(6,4,1,[1]),_gate(6,5,1,[1])]
    for placement in (0,1):
        rejected=_gather(old,[0,1,3,4],0,placement)
        check('noncommuting_intervener_rejected',not rejected['legal'])
        cert=rejected['failure'];g,h=cert['selected_gate'],cert['unselected_gate']
        check('noncommuting_witness_oracle',_matrix([g,h])!=_matrix([h,g]))
    # Algebra legal, but new fixed block interface forbids a required direction.
    old=[_gate(3,4,1,[1]),_gate(3,5,1,[1]),_gate(7,4,1,[1]),_gate(6,4,1,[1,2]),_gate(6,5,1,[1,2])]
    bounds=outer({3:[1],6:[2],4:[],5:[],7:[1]}, {3:[1],6:[1,2],4:[1,2],5:[1,2],7:[1]})
    context,outcomes=evaluate(old,[0,1,3,4],bounds,'in',0)
    check('commutation_does_not_imply_frame_feasibility',not outcomes)
    # Removing a shared contact can change the tariff without changing mass.
    old=[_gate(3,4,1,[1]),_gate(3,5,1,[1]),_gate(7,4,1,[1,2]),_gate(6,4,1,[1,2,4]),_gate(6,5,1,[1,2,4])]
    bounds=outer({3:[1],6:[1,2,4],4:[],5:[],7:[1,2]}, {3:[1],6:[1,2,4],4:[1,2,4],5:[1,2,4],7:[1,2]})
    whole=_bill(old,bounds);omitted=_bill([old[p] for p in (0,1,3,4)],{r:v for r,v in bounds.items() if r!=7})
    check('omitted_intervener_same_mass_detected',whole['profile']=={1:4,2:1} and omitted['profile']=={1:2,2:2}
          and whole['rank_mass']==omitted['rank_mass']==6)
    # Generic scalar crossing oracle, including one-register scales/self-adds.
    g=_gate(3,4,Q(1,2),[1])
    for scalar in (['scale',8,2,1,[1]],['scale',3,1,1,[1]],['scale',3,2,1,[1]],
                   ['add',8,8,1,1,[1]],['add',3,3,1,1,[1]]):
        cert=_commute(g,scalar)
        for dual in (False,True):check('scale_self_add_exact_crossing',cert['commutes']==(_matrix([g,scalar],dual)==_matrix([scalar,g],dual)))
    for scalar,reason in ((['scale',8,0,1,[1]],'singular_scale'),
                          (['add',8,8,-1,1,[1]],'singular_self_add'),
                          (['unsupported',8,[1]],'unsupported_opcode')):
        cert=_commute(g,scalar)
        check('invalid_scalar_typed_exclusion',not cert['commutes'] and cert['method']=='scalar_precondition' and cert['reason']==reason)
        # Force this scalar to be crossed in both stable gather directions.
        packet=[_gate(3,4,1),_gate(3,5,1),_gate(6,4,1),_gate(6,5,1)]
        window=packet[:2]+[scalar]+packet[2:]
        for placement in (0,1):
            failed=_gather(window,[0,1,3,4],0,placement)
            check('invalid_scalar_gather_witness',not failed['legal'] and
                  failed['failure']['predicate']=='scalar_crossing_precondition' and
                  failed['failure']['commutation']['pair_hash']==digest([
                      failed['failure']['selected_gate'],failed['failure']['unselected_gate']]))
    scale_bounds=outer({3:[],4:[],8:[]},{3:[1],4:[1],8:[1]})
    bill=_bill([_gate(3,4,1,[1]),['scale',8,3,2,[1]]],scale_bounds)
    check('scale_touches_one_register',bill['valid'] and bill['profile']=={1:3})
    bill=_bill([['add',8,8,1,1,[1]]],outer({8:[]},{8:[1]}))
    check('self_add_second_climb_zero',bill['valid'] and bill['profile']=={1:1})
    mismatch=_bill([_gate(3,4,1,[1])],outer({3:[],4:[]},{3:[1,2],4:[1]},(3,)))
    check('outside_equality_rejected',not mismatch['valid'] and mismatch['failures'][0]['predicate']=='window_exit_equality')
    mismatch=_bill([_gate(3,4,1,[1])],outer({3:[],4:[]},{3:[2],4:[1]},(3,)))
    check('equal_rank_wrong_frame_rejected',not mismatch['valid'] and
          mismatch['failures'][0]['predicate']=='window_frame_inclusion' and
          len(mismatch['failures'][0]['actual'])==len(mismatch['failures'][0]['required']))
    # Z=S has a gate-only 2H1 invoice, but its two remaining outside climbs
    # restore the old 4H1 invoice.  Omitting successors would invent a gain.
    old=[_gate(3,4,1,[1]),_gate(3,5,1,[1]),_gate(3,7,1,[1]),
         _gate(6,4,1,[1]),_gate(6,5,1,[1])]
    bounds=outer({3:[1],6:[1],4:[],5:[],7:[1]},
                 {3:[1],6:[1],4:[1,2],5:[1,2],7:[1]})
    context,outcomes=evaluate(old,[0,1,3,4],bounds,'in',0,corners=(0,))
    check('outside_successors_remove_false_gain',len(outcomes)==1 and outcomes[0]['profile_delta']=={}
          and outcomes[0]['proof']['complete_new_window_profile']=={1:4})
    truncated=deepcopy(bounds)
    for register in (4,5):truncated[register]['exit']=[1]
    new=outcomes[0]['proof']['new_gates']+[old[2]]
    without_successors=_bill(new,truncated)
    check('gate_only_false_two_unit_saving',without_successors['valid'] and without_successors['profile']=={1:2}
          and context['original_bill']['profile']=={1:4})
    # Complete stable gather order checked independently by actual adjacent swaps.
    old=[_gate(3,4,1),_gate(8,4,1),_gate(3,5,1),_gate(9,5,-1),_gate(6,4,1),_gate(6,5,1)]
    selected=[0,2,4,5]
    for placement in (0,1):
        gathered=_gather(old,selected,0,placement);check('stable_gather_legal',gathered['legal'])
        replay_gather(old,selected,placement,gathered)
    # Guard mutations use only synthetic words and exact immutable preimages.
    edges=[_gate(i,j,1,[1]) for i in (3,6) for j in (4,5)]
    state=dict(raw={'A':deepcopy(edges),'B':deepcopy(edges),'restore':[],
                    'warps':[],'prelude_events':0},centres=set(),semantic_sha256='synthetic')
    base=['A',0,1,2,3,'in'];address=[*base,0,0,0,0]
    compact=dict(address=address,candidate_id=_cid(address),plan_id=_plan_identity(state,address[:7]),plan_ordinal=0)
    check('synthetic_source_positive',_candidate(state,compact)['original_gates']==edges)
    bad=deepcopy(state);bad['raw']['A'].pop()
    rejects('missing_source_gate_rejected',lambda:_source_packet(bad,base))
    bad=deepcopy(state);bad['raw']['A'][3]=deepcopy(bad['raw']['A'][2])
    rejects('duplicated_source_gate_rejected',lambda:_source_packet(bad,base))
    rejects('stale_source_rejected',lambda:_candidate(state,dict(compact,parent_semantic_sha256='wrong')))
    rejects('stale_interval_rejected',lambda:_candidate(state,dict(compact,interval_sha256='wrong')))
    rejects('stale_plan_rejected',lambda:_candidate(state,dict(compact,plan_id='wrong')))
    bad=deepcopy(state);bad['raw']['A'][0][3]=2
    rejects('changed_source_coefficient_rejected',lambda:_candidate(bad,dict(compact,interval_sha256=digest(edges))))
    bad=deepcopy(state);bad['raw']['prelude_events']=1
    rejects('prelude_crossing_rejected',lambda:_source_packet(bad,base))
    bad=deepcopy(state);bad['raw']['warps']=[[2,3,[],[]]]
    rejects('warp_crossing_rejected',lambda:_source_packet(bad,['B',0,1,2,3,'in']))
    rejects('section_crossing_rejected',lambda:_source_packet(state,['restore',0,1,2,3,'in']))
    aliases=dict(fixed=dict(index={('A',0):0,('A',1):1},nodes=[
        dict(raw_registers=[3],registers=[3]),dict(raw_registers=[3],registers=[99])],eq_end=set()),
        distinct_previous={},distinct_following={})
    rejects('hidden_virtual_alias_rejected',lambda:_window_boundaries(aliases,'A',0,1))
    certificate={10:{2:[1,2],99:'boundary'},2:{100:[],8:'outside'}}
    check('integer_register_certificate_roundtrip',digest(certificate)==digest(json.loads(json.dumps(certificate))))
    rejects('canonical_key_collision_rejected',lambda:digest({1:'integer','1':'string'}))
    return dict(status='PASS',seed=seed,checks=inherited['checks']+sum(checks.values()),
        inherited_control_checks=inherited['checks'],inherited_control_result_sha256=digest({k:v for k,v in inherited.items() if k not in ('seed','cpu_seconds')}),
        checks_by_family=dict(sorted(checks.items())),endpoint=str(_ENDPOINT),
        source_attribution={p:s['attribution'] for p,s in _WORDS.items()},
        scope='Synthetic exact crossing and complete-window invoice controls; no independent source census.',
        cpu_seconds=time.process_time()-begin)
