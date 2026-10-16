"""Rank-two matched-frame five-gate audit; coordinator runs only.

Fresh finite packet census and exact gathers, with the complete-window tariff.
All changed-word native/global admission remains separate. Fetched code is data.
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
        spec=importlib.util.spec_from_file_location('styles12_rank2_frozen_joint',UTILITY_PATH)
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




def _address(value):
    if isinstance(value,str):
        p=value.split('.');need(len(p)==10,'J2 address arity')
        return [p[0],*(int(x) for x in p[1:5]),p[5],*(int(x) for x in p[6:])]
    if isinstance(value,dict):
        result=list(value.get('address') or _address(value['candidate_id']))
        if 'candidate_id' in value:need(_cid(result)==value['candidate_id'],'candidate ID/address')
        return result
    return list(value)




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
    packet=_packet(old,kind,carrier,order,state['centres'])
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
    new=_replacement(candidate,frames)
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
        scope=SCOPE,ordinary_source_exit_dominance=DOMINANCE,
        cpu_seconds=time.process_time()-begin)




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
        word_source_physical_families=state['physical_families'],native_admission=False,scalar_instruction_delta=2,
        fresh_all_column_audit='Required separately; inherited native evidence does not admit changed words')
    if raw is not None and result['status']=='PASS_CANDIDATE':
        directory=Path(spec['output_dir']);directory=directory if directory.is_absolute() else RR/directory
        directory=directory.resolve()
        need(directory.is_relative_to((RR/'data/continuation-12/candidates').resolve()),'new retained data subtree only')
        result['word']=_T()._write_word(raw,directory/provider,candidate_id)
    result['cpu_seconds']=time.process_time()-begin
    return result




MAX_PACKETS=12_500
MAX_LABELS=2_000_000
SCOPE='Exact rank-two 4-to-5 audit with both residual-target reads at identical Y2; no all-five-frame optimum, native, full-allocation or kappa claim.'
DOMINANCE='For ordinary source exits the matched-Y2 factor is weakly dominated by a broader exact-commutation single-row exposure, undo atY2 before the other original reads, and merged final source climbs. That broader exposure was not the frozen F1 domain. Equality exits can block this comparison.'


def prepare(records,endpoint,domains=None):
    """Source-generic parent preparation; no fresh packet enumeration here."""
    global _ENDPOINT
    need(not _WORDS and set(records)=={'base','extra'},'once-only two-provider preparation')
    _ENDPOINT=Q(endpoint);summary=_joint().prepare(records,_ENDPOINT)
    for provider,state in _joint()._WORDS.items():
        _WORDS[provider]=state;before,after={},{}
        for register,chain in enumerate(state['fixed']['chains']):
            unique=[]
            for node in chain:
                if not unique or unique[-1]!=node:unique.append(node)
            for left,right in zip(unique,unique[1:]):
                after[left,register]=right;before[right,register]=left
        state['distinct_previous']=before;state['distinct_following']=after
        _DOMAIN_PINS[provider]=dict(source_pin=state['source_pin'],parent_semantic_sha256=state['semantic_sha256'],
            domain='fresh rank-two consecutive-target-contact packets')
    return dict(status='PASS',endpoint=str(_ENDPOINT),providers=summary['providers'],
        sections=list(SECTIONS),restore_search=False,matched_residual_read_frame=True,
        max_packets_per_provider=MAX_PACKETS,max_labels_per_provider=MAX_LABELS,
        placements={'0':'gather_left','1':'gather_right'},
        utility_source=dict(path=str(UTILITY_PATH.relative_to(RR)),sha256=UTILITY_SHA256),
        scope=SCOPE,ordinary_source_exit_dominance=DOMINANCE)


def _packet(gates,kind='in',carrier=0,order=0,centres=()):
    if len(gates)!=4 or kind!='in' or carrier not in (0,1) or order not in (0,1):return None
    if not all(_T()._add(g) for g in gates):return None
    targets=sorted({g[1] for g in gates});sources=sorted({g[2] for g in gates})
    if len(targets)!=2 or len(sources)!=2 or len(set(targets+sources))!=4:return None
    if set(targets+sources)&set(centres):return None
    table={(g[1],g[2]):Q(g[3],g[4]) for g in gates}
    if len(table)!=4 or set(table)!=set(itertools.product(targets,sources)):return None
    if carrier:sources.reverse()
    if order:targets.reverse()
    i1,i2=targets;j,k=sources
    a,b,c,d=table[i1,j],table[i1,k],table[i2,j],table[i2,k]
    det=a*d-b*c
    if not det:return None
    ratio=b/a;residual=d-ratio*c
    need(residual!=0,'rank-two residual is nonzero')
    return dict(kind='in',i1=i1,i2=i2,j=j,k=k,a1=str(a),b1=str(b),a2=str(c),b2=str(d),
        determinant=str(det),ratio=str(ratio),residual=str(residual),carrier=carrier,order=order,
        coefficient_admissible=_joint()._dyadic(ratio) and _joint()._dyadic(residual))


def _source_packet(state,address):
    section,*tail=address;positions=list(tail[:4]);kind=tail[4]
    need(section in SECTIONS and kind=='in' and positions==sorted(set(positions)) and len(positions)==4,'rank-two packet shape')
    need(0<=positions[0]<positions[-1]<len(state['raw'][section]),'packet positions')
    need(_T()._same_segment(state['raw'],section,positions),'section/prelude/warp barriers')
    old=[state['raw'][section][p] for p in positions]
    packet=_packet(old,kind,0,0,state['centres'])
    need(packet is not None,'complete rank-two four-register coefficient block')
    return old,packet


def _domain_addresses(state):
    packets=set();counts=Counter(segments=0,inner_contact_pair_records=0,grouped_pair_combinations=0,
        preliminary_same_inner_combinations=0,preliminary_duplicate_position_combinations=0,
        rank_one_outside_domain=0,preliminary_overlapping_support_combinations=0)
    for section in SECTIONS:
        gates=state['raw'][section]
        for first,last in _T()._segments(state['raw'],section):
            counts['segments']+=1;previous={};groups=defaultdict(list)
            for p in range(first,last):
                gate=gates[p]
                if _T()._add(gate):
                    target=gate[1];before=previous.get(target)
                    if before is not None and _T()._add(gates[before]) and gates[before][1]==target:
                        old=gates[before];sources=tuple(sorted((old[2],gate[2])))
                        if len(set((target,*sources)))==3 and not set((target,*sources))&state['centres']:
                            groups[sources].append((target,before,p));counts['inner_contact_pair_records']+=1
                for register in _W().registers(gate):previous[register]=p
            for sources,records in sorted(groups.items()):
                for left,right in itertools.combinations(records,2):
                    counts['grouped_pair_combinations']+=1
                    if left[0]==right[0]:counts['preliminary_same_inner_combinations']+=1;continue
                    positions=tuple(sorted(left[1:]+right[1:]))
                    if len(set(positions))!=4:counts['preliminary_duplicate_position_combinations']+=1;continue
                    if len(set((left[0],right[0],*sources)))!=4:
                        counts['preliminary_overlapping_support_combinations']+=1;continue
                    old=[gates[p] for p in positions]
                    packet=_packet(old,'in',0,0,state['centres'])
                    if packet is None:counts['rank_one_outside_domain']+=1;continue
                    key=(section,*positions,'in')
                    if key not in packets:
                        need(len(packets)<MAX_PACKETS,'INCOMPLETE_DOMAIN_CAP: structural packet count exceeds registered cap')
                        packets.add(key)
    return sorted(packets,key=lambda a:(SECTIONS.index(a[0]),*a[1:])),dict(counts)


def _enumerate(provider):
    state=_WORDS[provider];candidates=[];plans={};exclusions=[]
    addresses,preliminary=_domain_addresses(state);_DOMAINS[provider]=tuple(addresses)
    counts=Counter(preliminary)
    counts.update(dict(source_packets=len(addresses),source_packet_addresses=len(addresses),placements_considered=0,
        commuting_placements=0,noncommuting_placements=0,ratio_rejected_carriers=0,
        ratio_rejected_carrier_anchor_choices=0,scalar_precondition_rejected_placements=0,
        admissible_carrier_choices=0,admissible_carrier_anchor_choices=0,candidates=0,crossings_verified=0))
    for base in addresses:
        section=base[0];positions=list(base[1:5]);kind=base[5]
        old,packet=_source_packet(state,base);window=state['raw'][section][positions[0]:positions[-1]+1]
        for placement in (0,1):
            counts['placements_considered']+=1;plan_address=[*base,placement]
            gather=_gather(window,positions,positions[0],placement)
            counts['crossings_verified']+=len(gather['crossings'])
            if not gather['legal']:
                counts['scalar_precondition_rejected_placements' if gather['failure']['predicate']=='scalar_crossing_precondition'
                       else 'noncommuting_placements']+=1
                exclusions.append(dict(gather['failure'],plan_address=plan_address));continue
            ordinal=len(plans);plan_id=_plan_identity(state,plan_address)
            plans[plan_id]=dict(plan_id=plan_id,plan_ordinal=ordinal,address=plan_address,
                crossings=gather['crossings'],crossings_sha256=digest(gather['crossings']),
                gathered_order_sha256=digest(gather['gathered_order']),interval_sha256=digest(window),
                parent_semantic_sha256=state['semantic_sha256'])
            counts['commuting_placements']+=1
            for carrier,anchor in itertools.product((0,1),repeat=2):
                c=_packet(old,kind,carrier,anchor,state['centres'])
                need(c is not None,'gather preserves rank-two coefficients')
                if not c['coefficient_admissible']:
                    counts['ratio_rejected_carriers']+=1;counts['ratio_rejected_carrier_anchor_choices']+=1
                    ratio=Q(c['ratio'])
                    exclusions.append(dict(predicate='non_dyadic_transport_ratio',address=[*base,placement,carrier,anchor],
                        plan_id=plan_id,ratio=str(ratio),reduced_numerator=ratio.numerator,
                        reduced_denominator=ratio.denominator,coefficients={n:c[n] for n in ('a1','b1','a2','b2')},residual=c['residual']))
                    continue
                counts['admissible_carrier_anchor_choices']+=1;counts['admissible_carrier_choices']+=1
                need(len(candidates)+20<=MAX_LABELS,'INCOMPLETE_DOMAIN_CAP: no truncated scientific null')
                for corner in range(20):
                    address=[*base,placement,carrier,anchor,corner]
                    candidates.append(dict(candidate_id=_cid(address),pair_key=_cid(address),address=address,
                        plan_id=plan_id,plan_ordinal=ordinal));counts['candidates']+=1
    need(len(candidates)==20*counts['admissible_carrier_anchor_choices'],'complete anchor/carrier twenty-label coverage')
    need(len({c['candidate_id'] for c in candidates})==len(candidates),'unique candidate addresses')
    need(len(exclusions)==counts['noncommuting_placements']+counts['scalar_precondition_rejected_placements']+counts['ratio_rejected_carriers'],
         'every scalar exclusion has an exact witness')
    return candidates,plans,exclusions,dict(counts)


def install_census(provider,receipt):
    need(receipt['status']=='PASS' and receipt['complete'] and receipt['provider']==provider,'complete census')
    need(receipt['parent_semantic_sha256']==_WORDS[provider]['semantic_sha256'],'census parent')
    for key in ('plans','exclusions'):need(digest(receipt[key])==receipt[key+'_sha256'],'census '+key+' hash')
    need(digest(receipt['candidates'])==receipt['domain_sha256'],'census candidate hash')
    _INSTALLED[provider]=receipt['candidates'];_PLANS[provider]=receipt['plans']
    _DOMAINS[provider]=tuple(sorted({tuple(p['address'][:6]) for p in receipt['plans'].values()},
        key=lambda a:(SECTIONS.index(a[0]),*a[1:])))


def _replacement(candidate,frames):
    c=candidate['chain'];i1,i2,j,k=(c[n] for n in ('i1','i2','j','k'))
    q,a,c2,e=Q(c['ratio']),Q(c['a1']),Q(c['a2']),Q(c['residual'])
    result=[_gate(j,k,q,frames['X']),_gate(i1,j,a,frames['Y1']),
        _gate(i2,j,c2,frames['Y2']),_gate(i2,k,e,frames['Y2']),_gate(j,k,-q,frames['Z'])]
    need(result[2][-1]==result[3][-1],'identical residual-read frames, not merely equal ranks')
    return result


def _materialize(state,context,candidate,result):
    need(result['status']!='REJECTED_GUARD','feasible final factor required')
    raw=state['raw'];section=candidate['section'];p,q=candidate['positions'][0],candidate['positions'][-1]
    replay=_gather(context['window'],candidate['positions'],p,candidate['placement']);plan=context['plan']
    need(replay['legal'] and replay['crossings']==plan['crossings'],'retained exact crossing replay')
    need(digest(replay['crossings'])==plan['crossings_sha256'] and digest(replay['gathered_order'])==plan['gathered_order_sha256']
         and digest(context['window'])==plan['interval_sha256'],'retained source and gather hashes')
    new_gates=result['proof']['new_gates'];unchanged=[deepcopy(g) for _,g in context['unchanged']]
    new_window=deepcopy(new_gates)+unchanged if candidate['placement']==0 else unchanged+deepcopy(new_gates)
    need(len(new_window)==len(context['window'])+1,'four-to-five exact window length')
    for dual in (False,True):need(_matrix(context['window'],dual)==_matrix(new_window,dual),'complete forward and dual map')
    bill=_bill(new_window,context['outer'],range(p,p+len(new_window)),phase='final',detailed=True)
    need(bill['valid'],'fresh complete-window chain feasibility')
    need(bill['profile']==result['proof']['complete_new_window_profile'],'direct versus decomposed full-window invoice')
    edited=deepcopy(raw);edited[section]=deepcopy(raw[section][:p])+new_window+deepcopy(raw[section][q+1:])
    need(edited[section][:p]==raw[section][:p] and edited[section][q+2:]==raw[section][q+1:],'fixed scalar exterior')
    if section=='B':
        edited['warps']=_shift_warps(raw['warps'],p,q)
        need([w[1:] for w in edited['warps']]==[w[1:] for w in raw['warps']],
             'all nonpositional warp data unchanged')
        need([w[0] for w in edited['warps']]==[w[0]+int(w[0]>q) for w in raw['warps']],
             'exact later B warp index translation')
    else:need(edited['warps']==raw['warps'],'A rewrite leaves every B warp unchanged')
    for other in ('A','B','restore'):
        if other!=section:need(edited[other]==raw[other],'other scalar sections fixed')
    need(_T()._boundary_signature(edited)==state['boundaries'],'fixed interfaces and compensation')
    npre=int(raw.get('prelude_events',0));need(edited['A'][:npre]==raw['A'][:npre],'literal prelude fixed')
    W=_W();canonical=W.WordData(edited,state['attribution'],assert_profile=False);old=state['canonical']
    need(canonical.helpers==old.helpers and canonical.start==old.start and canonical.end==old.end,'exact ordered helper endpoints')
    need(_T()._widths(canonical)==state['widths'],'ordered helper widths')
    expected=Counter(old.paid);expected.update(result['profile_delta'])
    need(all(v>=0 for v in expected.values()) and _profile(expected)==canonical.paid,'full canonical versus complete-window delta')
    need(_mass(canonical.paid)==_mass(old.paid),'complete local rank mass')
    edited['report']['local_profile']={str(r):n for r,n in sorted(canonical.paid.items())}
    edited['cleanup']=W.derived_borrow_cleanup(canonical);checked=W.WordData(edited,state['attribution'])
    need(checked.paid==canonical.paid,'fresh cleanup and canonical profile')
    result['proof']['direct_final_window_bill']=bill;result['proof']['retained_crossing_plan_replayed']=True
    return edited,checked


def _corner_oracle():
    spans={frozenset({0})}
    for v in range(1,8):spans|={frozenset(set(s)|{x^v for x in s}) for s in list(spans)}
    spaces=sorted(spans,key=lambda x:(len(x),sorted(x)));need(len(spaces)==16,'independent full3D subspace universe')
    def span(b):
        s={0}
        for v in b:s|={x^v for x in list(s)}
        return frozenset(s)
    def rank(s):return len(s).bit_length()-1
    fixtures=[dict(i1=((),(1,2)),i2=((2,4),(1,2,4)),j=((),(1,2,4)),k=((),(1,2,4))),
        dict(i1=((),(1,)),i2=((2,),(1,2,4)),j=((),(1,2,4)),k=((),(1,2,4))),
        dict(i1=((1,),(1,)),i2=((1,2),(1,2)),j=((),(1,2)),k=((),(1,2)))]
    tariffs=((0,6,10,12),(0,10,17,23));records=[]
    for fi,pairs in enumerate(fixtures):
        for equal_sources in (False,True):
            boundary={k:dict(entry=list(e),exit=list(o),equality_exit=equal_sources and k in ('j','k')) for k,(e,o) in pairs.items()}
            E={k:span(e) for k,(e,o) in pairs.items()};O={k:span(o) for k,(e,o) in pairs.items()}
            def allowed(X,Y1,Y2,Z):
                return (E['j']|E['k'])<=X<=Y1<=Y2<=Z<=O['j'] and Z<=O['k'] and E['i1']<=Y1<=O['i1'] and E['i2']<=Y2<=O['i2'] and (not equal_sources or Z==O['j']==O['k'])
            def cost(X,Y1,Y2,Z,h):
                x,a,b,z=map(rank,(X,Y1,Y2,Z));e={k:rank(v) for k,v in E.items()};o={k:rank(v) for k,v in O.items()}
                jumps=(x-e['j'],a-x,b-a,z-b,o['j']-z,x-e['k'],b-x,z-b,o['k']-z,a-e['i1'],o['i1']-a,b-e['i2'],0,o['i2']-b)
                need(min(jumps)>=0,'oracle nonnegative jumps');return sum(h[r] for r in jumps)
            feasible=[]
            for X in spaces:
                for Y1 in spaces:
                    if not X<=Y1:continue
                    for Y2 in spaces:
                        if not Y1<=Y2:continue
                        for Z in spaces:
                            if allowed(X,Y1,Y2,Z):feasible.append((X,Y1,Y2,Z))
            corners=[]
            for ci in range(20):
                f,errors=_joint()._frames(boundary,ci)
                if not errors:
                    flags=tuple(span(f[k]) for k in ('X','Y1','Y2','Z'))
                    need(allowed(*flags),'corner meets independent constraints');corners.append(flags)
            need(bool(feasible)==bool(corners),'oracle feasibility parity')
            for h in tariffs:
                actual=min((cost(*f,h) for f in feasible),default=None);proposed=min((cost(*f,h) for f in corners),default=None)
                need(actual==proposed,'twenty corners attain exhaustive matched-frame optimum')
                records.append(dict(fixture=fi,source_equality=equal_sources,tariff=list(h),feasible_flags=len(feasible),valid_labels=len(corners),minimum=actual))
    return dict(passed=True,ambient_dimension=3,subspaces=16,records=records,
        scope='Complete finite matched-Y2 flag oracle; not all five independent frames')


def controls_task(spec):
    begin=time.process_time();seed=int(spec['seed'] if isinstance(spec,dict) else spec);checks=Counter()
    def check(name,good):need(good,'rank2 control: '+name);checks[name]+=1
    def rejects(name,fn):
        failed=False
        try:fn()
        except (ValueError,AssertionError):failed=True
        check(name,failed)
    signed=(Q(-2),Q(-1),Q(-1,2),Q(1,2),Q(1),Q(2));identity_count=0
    for a,b,c,d in itertools.product(signed,repeat=4):
        if a*d==b*c:continue
        old=[_gate(0,2,a),_gate(1,2,c),_gate(0,3,b),_gate(1,3,d)]
        for carrier,anchor in itertools.product((0,1),repeat=2):
            chain=_packet(old,'in',carrier,anchor,())
            if not chain['coefficient_admissible']:continue
            new=_replacement(dict(chain=chain),dict(X=(),Y1=(1,),Y2=(1,2),Z=(1,2)))
            for dual in (False,True):check('signed_forward_dual',_matrix(old,dual)==_matrix(new,dual));identity_count+=1
    check('rank_one_outside_domain',_packet([_gate(0,2,1),_gate(1,2,2),_gate(0,3,1),_gate(1,3,2)],'in',0,0,()) is None)
    nd=_packet([_gate(0,2,Q(3,2)),_gate(1,2,1),_gate(0,3,1),_gate(1,3,2)],'in',0,0,())
    check('nondyadic_ratio',nd is not None and not nd['coefficient_admissible'])
    S=(1,);T=(1,2)
    old=[_gate(0,2,1,S),_gate(1,2,1,T),_gate(0,3,1,S),_gate(1,3,-1,T)]
    boundary={0:dict(entry=list(S),exit=list(S),equality_exit=False),1:dict(entry=list(T),exit=list(T),equality_exit=False),
        2:dict(entry=[],exit=list(T),equality_exit=False),3:dict(entry=[],exit=list(T),equality_exit=False)}
    before=_bill(old,boundary);check('positive_original_full_bill',before['valid'] and before['profile']=={1:4})
    new=_replacement(dict(chain=_packet(old,'in',0,0,())),dict(X=(),Y1=S,Y2=T,Z=T));after=_bill(new,boundary)
    check('positive_complete_bill',after['valid'] and after['profile']=={1:2,2:1})
    check('positive_exact_registered_tariff',Q(_joint()._moment({1:-2,2:1})['upper'])<0)
    bad=deepcopy(new);bad[3][3]=-bad[3][3]
    for dual in (False,True):
        check('wrong_residual_rejected',_matrix(old,dual)!=_matrix(bad,dual))
        check('missing_undo_rejected',_matrix(old,dual)!=_matrix(new[:-1],dual))
    bad=deepcopy(new);bad[3][-1]=[1,4];check('equal_rank_wrong_frame',not _bill(bad,boundary)['valid'])
    permutation_count=0
    for gates in itertools.permutations(old):
        raw=dict(A=[deepcopy(g) for g in gates],B=[],warps=[],prelude_events=0,centers=[])
        addresses,_=_domain_addresses(dict(raw=raw,centres=set()))
        check('all24_complete_packet_enumeration',addresses==[('A',0,1,2,3,'in')])
        for placement in (0,1):check('both_gathers_without_interveners',_gather(list(gates),[0,1,2,3],0,placement)['legal'])
        permutation_count+=1
    blocked=old[:2]+[_gate(2,1,1,T)]+old[2:]
    for placement in (0,1):check('noncommuting_crossing_rejected',not _gather(blocked,[0,1,3,4],0,placement)['legal'])
    check('barrier_rejected',not _T()._same_segment(dict(A=[],B=old,warps=[[2]],prelude_events=0),'B',[0,1,2,3]))
    check('prelude_rejected',not _T()._same_segment(dict(A=old,B=[],warps=[],prelude_events=1),'A',[0,1,2,3]))
    rejects('stale_parent_rejected',lambda:_candidate(dict(semantic_sha256='current'),
        dict(address=['A',0,1,2,3,'in',0,0,0,0],parent_semantic_sha256='stale')))
    preimage_state=dict(raw=dict(A=deepcopy(old),B=[],warps=[],prelude_events=0),
        centres=set(),semantic_sha256='current')
    preimage_address=['A',0,1,2,3,'in',0,0,0,0]
    preimage_compact=dict(address=preimage_address,parent_semantic_sha256='current',
        plan_id=_plan_identity(preimage_state,preimage_address[:7]),plan_ordinal=0,
        interval_sha256=digest(old))
    check('current_literal_preimage_accepted',
        _candidate(preimage_state,preimage_compact)['original_gates']==old)
    stale_interval=deepcopy(preimage_compact);stale_interval['interval_sha256']='stale'
    rejects('stale_literal_preimage_rejected',lambda:_candidate(preimage_state,stale_interval))
    # With Y2<Z, omitting the independent surviving-k read changes the tariff
    # even though both invoices conserve rank mass. The positive fixture alone
    # has Y2=Z and would not detect this billing error.
    V=(1,2,4);higher=deepcopy(boundary)
    higher[2]['exit']=list(V);higher[3]['exit']=list(V)
    five=_replacement(dict(chain=_packet(old,'in',0,0,())),dict(X=(),Y1=S,Y2=T,Z=V))
    full=_bill(five,higher);omitted=_bill(five[:3]+five[4:],higher)
    check('surviving_k_contact_full_bill',full['valid'] and full['profile']=={1:4,2:1})
    check('missing_surviving_k_detected',omitted['valid'] and omitted['profile']=={1:3,3:1}
        and omitted['rank_mass']==full['rank_mass'] and omitted['profile']!=full['profile'])
    earlier=_replacement(dict(chain=_packet(old,'in',0,0,())),dict(X=(),Y1=S,Y2=T,Z=T))
    with_successor=_bill(earlier,higher);without_successor=_bill(earlier,boundary)
    check('missing_successor_detected',with_successor['valid'] and without_successor['valid']
        and with_successor['rank_mass']==without_successor['rank_mass']+2)
    equality=deepcopy(higher);equality[2]['equality_exit']=True
    check('source_equality_guard',not _bill(earlier,equality)['valid'])
    # Whole-window decomposition with an unchanged shared-register intervener.
    intervened=old[:1]+[_gate(0,4,1,S)]+old[1:]
    outer=deepcopy(boundary);outer[4]=dict(entry=list(S),exit=list(S),equality_exit=False)
    positions=[10,12,13,14]
    for placement in (0,1):
        gather=_gather(intervened,positions,10,placement)
        check('shared_register_commuting_exposure',gather['legal'])
        context=_prepare_context(intervened,positions,10,{0,1,2,3},placement,outer)
        check('fixed_contact_bill_feasible',context['fixed_bill']['valid'])
        block=_bill(new,context['block_boundaries']);check('block_bill_feasible',block['valid'])
        total=Counter(context['fixed_bill']['profile']);total.update(block['profile'])
        untouched=[g for _,g in context['unchanged']]
        final=new+untouched if placement==0 else untouched+new
        direct=_bill(final,outer)
        check('direct_decomposed_invoice_parity',direct['valid'] and _profile(total)==direct['profile'])
        for dual in (False,True):check('complete_intervened_window_map',_matrix(intervened,dual)==_matrix(final,dual))
    warps=[[0,'left'],[4,'right'],[9,'later']]
    shifted=_shift_warps(warps,0,3)
    check('warp_index_translation',shifted==[[0,'left'],[5,'right'],[10,'later']] and warps==[[0,'left'],[4,'right'],[9,'later']])
    rejects('hidden_warp_translation_rejected',lambda:_shift_warps([[2,'hidden']],0,3))
    check('warp_payload_mutant_detected',[w[1:] for w in shifted]!=[['left'],['wrong'],['later']])
    oracle=_corner_oracle();check('independent_matched_frame_corner_oracle',oracle['passed'])
    return dict(status='PASS',seed=seed,checks=sum(checks.values()),checks_by_family=dict(checks),
        exact_signed_identities=identity_count,all_interleavings=permutation_count,corner_oracle=oracle,
        positive_profile_delta={1:-2,2:1},matched_residual_read_frame=True,ordinary_source_exit_dominance=DOMINANCE,
        source_attribution={p:s['attribution'] for p,s in _WORDS.items()},scope=SCOPE,cpu_seconds=time.process_time()-begin)


def _shift_warps(warps,start,end):
    result=deepcopy(warps)
    for warp in result:
        need(isinstance(warp,list) and warp and type(warp[0]) is int,'literal B warp record')
        need(not(start<warp[0]<=end),'no hidden internal B warp')
        if warp[0]>end:warp[0]+=1
    need([w[1:] for w in result]==[w[1:] for w in warps],'exact warp payload preservation')
    return result
