"""Exact fixed-inventory cap for the complete saved G2 rank-seven census.

Independent rational linear algebra and full pattern enumeration. PR2930's
nine basis patterns are inert data, never executable code. Cost enclosures use
the hash-pinned, preexisting Douglas Colkitt packing-ceiling implementation.
No solver, internal pool, subprocess, or experiment at import. The coordinator
must preregister prepare(PIN, ledger_data) followed by pool-launched task(seed).
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
from functools import lru_cache
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
RR = HERE.parents[1]
ROOT = RR.parents[1]
CEILING = ('research/t74-joint-twelve-retired7/vendor/ceiling.py',
           '86a1432870b3b21d8454106ec9162fddc0471472d9214c590a1420f2426cedfc')
CAPS = (8,16,32,48)
WIDTHS = (4,5,7,8,9)
CAPACITY_COUNTS = (672,448,448,448)
OLD_INVENTORY = {4:26,5:2,7:62,8:96,9:222}
NEW_INVENTORY = {4:26,5:2,7:63,8:96,9:221}
GRID = Q(1,10**20)
_STATE = None
_C = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    if isinstance(value,Q):
        return str(value)
    if isinstance(value,dict):
        return {str(k):encode(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [encode(v) for v in value]
    return value


def digest(value):
    # Match the frozen G2 runner's canonical JSON, including its final newline.
    return hashlib.sha256((json.dumps(encode(value),sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()


def decimal(value):
    with localcontext() as context:
        context.prec=60
        return str(Decimal(value.numerator)/Decimal(value.denominator))


def _read(reference):
    path=Path(reference['path'])
    if not path.is_absolute():
        path=RR/path
    path=path.resolve()
    need(path.is_relative_to(RR.resolve()),'inert source confinement')
    need(path.name.endswith(('.json','.json.gz')),'only inert JSON inputs')
    raw=path.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==reference['sha256'],'source artifact hash')
    return json.loads(gzip.decompress(raw) if path.name.endswith('.gz') else raw)


def _ceiling():
    global _C
    path=ROOT/CEILING[0]
    need(sha(path)==CEILING[1],'trusted interval engine pin')
    if _C is None:
        need(not sys.flags.optimize,'enabled assertions required')
        sys.dont_write_bytecode=True
        spec=importlib.util.spec_from_file_location('styles_c02_inventory_intervals',path)
        _C=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=_C
        spec.loader.exec_module(_C)
    return _C


def _histogram(value):
    result={}
    for r,n in value.items():
        rank=int(r)
        need(str(rank)==str(r) and 0<rank<73 and type(n) is int and n>=0,'integer histogram')
        if n:
            result[rank]=n
    return dict(sorted(result.items()))


def _local_mass(local,inventory):
    need(sum(inventory.values())==408,'fixed408 helper roles')
    mass=sum(r*n for r,n in local.items())
    need(mass==sum(w*n for w,n in inventory.items())+1856,'complete local paid/width mass identity')
    return mass


def prepare(PIN,ledger_data):
    """Hash-bind small immutable data once in parent, without evaluating costs.

    PIN keys: target,basis,template,ledger_source,matched_ledgers,g2_results (list),
    source_attribution (list). Artifact references are {path,sha256}.
    ledger_data is the already loaded CAP-TASKS.json.gz list.
    """
    global _STATE
    need(_STATE is None,'prepare exactly once')
    target,basis,ledgers,matched=(_read(PIN[k]) for k in
                                 ('target','basis','ledger_source','matched_ledgers'))
    template=_read(PIN['template'])
    children=template['idle_children']
    by_child={}
    seen=set()
    for child in children:
        key=child['child'],child['port']
        need(key not in seen and 0<=child['port']<112,'unique source idle-child/port')
        seen.add(key)
        metadata=(child['rank'],child['replicas'])
        need(metadata[1]==37 and metadata[0] in CAPS,'literal half-template capacity and replicas')
        if key[0] in by_child:
            need(by_child[key[0]]==metadata,'one capacity per source child')
        by_child[key[0]]=metadata
    need(len(by_child)==18 and len(seen)==2016 and
         seen=={(c,p) for c in by_child for p in range(112)},'all18source children at all112ports')
    supplies=Counter(rank for rank,replicas in by_child.values())
    need(tuple(supplies[c]*112 for c in CAPS)==CAPACITY_COUNTS,'source-bound capacity supplies per replica')
    need((target['replicas'],target['calls'],target['live_families'])==(74,666,66304),
         'literal two-copy74replica/666call target geometry')
    need(ledgers==ledger_data,'parent-loaded complete ledger equality')
    results=[_read(r) for r in PIN['g2_results']]
    need(len(results)==2 and len({r['seed'] for r in results})==2,'two distinct saved G2 seeds')
    for r in results:
        stats=r['statistics']
        need(stats['complete'] and stats['matched_unique_cost_ledgers']==16 and
             stats['counts']['matched_addresses']==48,'saved complete G2 census')
    need(Q(target['complex_lower'])==Q(basis['cap_lower']),'target/source-cap lower endpoint binding')
    _ceiling()
    _STATE=dict(pins=deepcopy(PIN),target=target,basis=basis,ledgers=ledgers,matched=matched,
                g2_seed_ids=sorted(r['seed'] for r in results),
                template_binding=dict(children=len(by_child),ports=112,template_replicas=37,
                    actual_replicas=74,capacity_counts_per_replica=dict(zip(CAPS,CAPACITY_COUNTS))))
    return dict(parent_loaded_once=True,scientific_evaluation=False,ledger_rows=len(ledgers),
                expected_ledger_classes=16,expected_matched_addresses=48,
                target_complex_lower=target['complex_lower'],grid=str(GRID),
                trusted_interval_source=dict(path=CEILING[0],sha256=CEILING[1]),
                template_binding=deepcopy(_STATE['template_binding']))


def _state():
    need(_STATE is not None,'parent preparation required')
    return _STATE


def _patterns():
    result=[]
    def enumerate_counts(position,remaining,prefix):
        if position==len(WIDTHS):
            yield tuple(prefix),remaining
            return
        width=WIDTHS[position]
        for count in range(remaining//width+1):
            yield from enumerate_counts(position+1,remaining-width*count,prefix+[count])
    for cap in CAPS:
        for counts,remainder in enumerate_counts(0,cap,[]):
            column=tuple(int(c==cap) for c in CAPS)+counts
            result.append((cap,counts,remainder,column))
    return result


def _coverage(patterns):
    need(len(patterns)==1163 and len({(c,p) for c,p,r,a in patterns})==1163,
         'complete1163 distinct count-vector patterns')
    need(all(any(c==cap and not any(counts) and r==cap for c,counts,r,a in patterns)
             for cap in CAPS),'empty pattern for each capacity')
    need(all(sum(w*n for w,n in zip(WIDTHS,counts))+r==cap and
             all(n>=0 for n in counts) and r>=0 for cap,counts,r,a in patterns),
         'exact pattern capacity equations')


def _inverse(matrix):
    n=len(matrix)
    augmented=[[Q(x) for x in row]+[Q(i==j) for j in range(n)] for i,row in enumerate(matrix)]
    need(all(len(row)==2*n for row in augmented),'square exact basis')
    for col in range(n):
        pivot=next((r for r in range(col,n) if augmented[r][col]),None)
        need(pivot is not None,'nonsingular9-pattern basis')
        augmented[col],augmented[pivot]=augmented[pivot],augmented[col]
        scale=augmented[col][col]
        augmented[col]=[x/scale for x in augmented[col]]
        for row in range(n):
            if row!=col and augmented[row][col]:
                q=augmented[row][col]
                augmented[row]=[x-q*y for x,y in zip(augmented[row],augmented[col])]
    need(all(augmented[i][j]==(i==j) for i in range(n) for j in range(n)),'inverse identity')
    return [row[n:] for row in augmented]


def _rhs(inventory):
    return list(map(Q,CAPACITY_COUNTS))+[Q(9*inventory[w]) for w in WIDTHS]


def _matvec(matrix,vector):
    return [sum((a*b for a,b in zip(row,vector)),Q(0)) for row in matrix]


def _check_primal(matrix,counts,rhs):
    need(all(x>=0 for x in counts) and _matvec(matrix,counts)==rhs,'exact nonnegative basis/RHS equality')


def _basis(patterns):
    source=_state()['basis']['basis_patterns']
    need(len(source)==9,'nine frozen basis patterns')
    columns,remainder,declared=[],[],[]
    available={(cap,counts):column for cap,counts,r,column in patterns}
    for item in source:
        cap=item['capacity']; widths=Counter(item['widths'])
        need(set(widths)<=set(WIDTHS),'basis width alphabet')
        counts=tuple(widths[w] for w in WIDTHS)
        need((cap,counts) in available,'basis is a legal enumerated column')
        columns.append(available[cap,counts])
        remainder.append(cap-sum(item['widths']))
        declared.append(Q(item['count_per_replica']))
    matrix=[list(row) for row in zip(*columns)]
    inverse=_inverse(matrix)
    old_counts=_matvec(inverse,_rhs(OLD_INVENTORY))
    new_counts=_matvec(inverse,_rhs(NEW_INVENTORY))
    need(old_counts==declared,'source primal counts reproduced independently')
    _check_primal(matrix,old_counts,_rhs(OLD_INVENTORY))
    _check_primal(matrix,new_counts,_rhs(NEW_INVENTORY))
    # B^T y = c_B, so y_i = sum_j (B^-1)_{j,i} phi_{residual_j}.
    dual=[]
    for i in range(9):
        poly={}
        for j,r in enumerate(remainder):
            if r:
                poly[r]=poly.get(r,Q(0))+inverse[j][i]
        dual.append({r:q for r,q in poly.items() if q})
    return matrix,inverse,remainder,old_counts,new_counts,dual


def _reduced(patterns,dual):
    result=[]
    for cap,counts,remainder,column in patterns:
        poly={remainder:Q(1)} if remainder else {}
        for coefficient,y in zip(column,dual):
            for rank,q in y.items():
                poly[rank]=poly.get(rank,Q(0))-coefficient*q
        result.append({r:q for r,q in poly.items() if q})
    return result


@lru_cache(maxsize=65536)
def _cost(rank,exponent):
    if rank==0:
        return Q(0),Q(0)
    if rank==73: # exact constant1, used only by the rejecting dual mutant.
        return Q(1),Q(1)
    need(0<rank<73,'cost rank range')
    return _ceiling().child_cost(rank,73,Q(exponent))


def _poly_bounds(poly,exponent):
    lower=upper=Q(0)
    for rank,q in poly.items():
        lo,hi=_cost(rank,str(exponent))
        lower+=q*(lo if q>=0 else hi)
        upper+=q*(hi if q>=0 else lo)
    return lower,upper


def _dual_check(patterns,reduced,exponent):
    _coverage(patterns)
    need(len(reduced)==len(patterns),'complete reduced-cost census')
    zero,strict,negative,unresolved=[],[],[],[]
    minimum=None
    for i,poly in enumerate(reduced):
        if not poly:
            zero.append(i)
            continue
        lo,hi=_poly_bounds(poly,exponent)
        if lo>0:
            strict.append(i)
            if minimum is None or lo<minimum[0]:
                minimum=(lo,i)
        elif hi<0:
            negative.append(dict(index=i,lower=str(lo),upper=str(hi)))
        else:
            unresolved.append(dict(index=i,lower=str(lo),upper=str(hi)))
    passed=not negative and not unresolved and len(zero)+len(strict)==1163
    return dict(status='PASS' if passed else 'EXPLORATORY',exponent=str(exponent),patterns=1163,
        child_cost_intervals={str(rank):[str(q) for q in _cost(rank,str(exponent))]
                              for rank in sorted({r for poly in reduced for r in poly})},
        exact_zero_polynomial_indices=zero,exact_zero_count=len(zero),strict_positive_count=len(strict),
        minimum_strict_margin=str(minimum[0]) if minimum else None,
        minimum_strict_pattern=minimum[1] if minimum else None,
        negative_patterns=negative,unresolved_patterns=unresolved,
        zero_policy='Only a coefficientwise-zero reduced-cost polynomial counts as exact equality; every nonzero polynomial requires a strictly positive rational lower enclosure.')


def _idle(remainders,counts):
    out={}
    for rank,count in zip(remainders,counts):
        if rank:
            out[rank]=out.get(rank,Q(0))+count
    return out


def _full(local,idle):
    out={r:Q(9*n) for r,n in local.items()}
    for r,n in idle.items():
        out[r]=out.get(r,Q(0))+n
    need(sum(r*n for r,n in out.items())==65088,'exact per-replica coverage mass')
    return out


def _moment(profile,endpoint):
    return _poly_bounds(profile,endpoint)


def _bracket(profile):
    low,high=Q(0),Q(1,20)
    need(_moment(profile,low)[1]<896<_moment(profile,high)[0],'positive complete-profile bracket')
    while high-low>GRID:
        mid=Q(((low+high)/(2*GRID)).__floor__())*GRID
        if mid<=low:
            mid=low+GRID
        lo,hi=_moment(profile,mid)
        if hi<896:
            low=mid
        elif lo>896:
            high=mid
        else:
            return None
    return low,high


def _ledgers():
    state=_state(); groups=state['matched']['ledger_groups']
    need(len(groups)==16 and state['matched']['counts']['matched_addresses']==48,
         'complete16ledger/48address source partition')
    cap_records={}
    for row in state['ledgers']:
        key=row['ledger_id'],row['seed']
        need(key not in cap_records,'unique ledger/seed row')
        cap_records[key]=row
    need(len(cap_records)==32,'complete32two-seed cap records')
    members=[];profiles={};mapping=[]
    for lid,group in sorted(groups.items()):
        ledger=group['ledger']
        need(digest(ledger)==lid,'exact original ledger hash')
        need(set(ledger)=={'extra','gauge44'},'both provider invoices')
        for seed in state['g2_seed_ids']:
            row=cap_records[lid,seed]
            need(row['addresses']==group['addresses'] and row['identity']==group['members'][0],
                 'cap record binds full saved ledger group')
        paid=[_histogram(ledger[p]['local_profile']) for p in ('extra','gauge44')]
        need(paid[0]==paid[1],'both-provider homogeneous invoice in this bounded family')
        for pid in ledger:
            need(_histogram(ledger[pid]['width_inventory'])==NEW_INVENTORY and
                 ledger[pid]['private_buffers']==83,'exact newinventory and83buffer bill')
            _local_mass(paid[0],NEW_INVENTORY)
        profile_id=digest(paid[0]);profiles[profile_id]=paid[0]
        mapping.append(dict(ledger_id=lid,profile_id=profile_id,members=deepcopy(group['members'])))
        members.extend(group['members'])
    need(len(members)==len({digest(m) for m in members})==48 and len(profiles)==6,
         'all48distinct matched addresses in six paid profiles')
    return profiles,mapping


def _controls(patterns,matrix,reduced,dual,old_counts,remainder):
    source=_state()['basis'];local=_histogram(source['local_per_call'])
    need(_histogram(source['inventory_per_call'])==OLD_INVENTORY,'source old inventory')
    _local_mass(local,OLD_INVENTORY)
    full=_full(local,_idle(remainder,old_counts))
    global_profile={r:n*74 for r,n in full.items()}
    need(all(n.denominator==1 for n in global_profile.values()) and
         {r:int(n) for r,n in global_profile.items()}==_histogram(_state()['target']['profile']),
         'source basis complete profile equals pinned PR2930 literal-profile claim')
    low,high=Q(source['cap_lower']),Q(source['cap_upper'])
    low_m,high_m=_moment(full,low),_moment(full,high)
    need(low_m[1]<896<high_m[0],'source exact root bracket reproduced')
    source_dual=_dual_check(patterns,reduced,high)
    need(source_dual['status']=='PASS','original source basis dual must certify')
    wrong_rhs=_rhs(OLD_INVENTORY);wrong_rhs[-1]+=1
    bad_local=dict(local);bad_local[1]+=1
    rejected={}
    for label,check in {
        'wrong_basis_rhs':lambda:_check_primal(matrix,old_counts,wrong_rhs),
        'omitted_pattern_coverage':lambda:_coverage(patterns[:-1]),
        'wrong_local_mass':lambda:_local_mass(bad_local,OLD_INVENTORY),
    }.items():
        try:
            check()
        except (ValueError,AssertionError) as error:
            rejected[label]=dict(rejected=True,reason=str(error))
        else:
            rejected[label]=dict(rejected=False)
    mutant=deepcopy(dual);mutant[CAPS.index(48)][73]=Q(1)
    mutant_check=_dual_check(patterns,_reduced(patterns,mutant),high)
    empty=next(i for i,(cap,counts,r,a) in enumerate(patterns) if cap==48 and not any(counts))
    rejected['increased_capacity_dual_fools_empty_pattern']=dict(
        rejected=mutant_check['status']!='PASS' and empty in {x['index'] for x in mutant_check['negative_patterns']},
        empty_pattern_index=empty,negative_patterns=len(mutant_check['negative_patterns']))
    need(all(v['rejected'] for v in rejected.values()),'every registered rejection control')
    return encode(dict(status='PASS',source_primal_counts=old_counts,source_idle_per_replica=_idle(remainder,old_counts),
        source_root_bracket=[low,high],source_lower_moment=low_m,source_upper_moment=high_m,
        source_dual=source_dual,negative_controls=rejected))


def task(seed):
    """One registered pool worker; all six profiles and all16/48source classes."""
    started=time.process_time();state=_state()
    profiles,mapping=_ledgers();patterns=_patterns();_coverage(patterns)
    matrix,inverse,remainder,old_counts,new_counts,dual=_basis(patterns)
    reduced=_reduced(patterns,dual)
    controls=_controls(patterns,matrix,reduced,dual,old_counts,remainder)
    target=Q(state['target']['complex_lower'])
    target_dual=_dual_check(patterns,reduced,target)
    new_idle=_idle(remainder,new_counts)
    order=sorted(profiles);random.Random(int(seed)).shuffle(order)
    caps=[]
    for profile_id in order:
        local=profiles[profile_id];full=_full(local,new_idle)
        target_moment=_moment(full,target)
        bracket=_bracket(full)
        entry=dict(profile_id=profile_id,local_per_call=local,complete_fractional_profile_per_replica=full,
            target_moment_lower=target_moment[0],target_moment_upper=target_moment[1],
            target_rejection_margin=target_moment[0]-896,
            target_bound_certified=target_dual['status']=='PASS',
            target_root_rejected=target_dual['status']=='PASS' and target_moment[0]>896)
        if bracket is None:
            entry.update(status='EXPLORATORY',reason='root grid interval unresolved')
        else:
            low,high=bracket;dual_upper=_dual_check(patterns,reduced,high)
            lo_m,hi_m=_moment(full,low),_moment(full,high)
            proved=(dual_upper['status']=='PASS' and lo_m[1]<896<hi_m[0])
            entry.update(status='PASS_EXACT_FIXED_INVENTORY_CAP' if proved else 'EXPLORATORY',
                cap_lower=low,cap_upper=high,cap_decimal_interval=[decimal(low),decimal(high)],grid=GRID,
                lower_endpoint_moment=lo_m,upper_endpoint_moment=hi_m,dual_at_upper=dual_upper,
                gap_below_target=target-high,strictly_below_target=proved and high<target,
                admitted_target_fraction_of_cap_interval=[target/high,target/low])
        caps.append(entry)
    caps.sort(key=lambda row:row['profile_id'])
    all_below=all(row.get('strictly_below_target',False) and row['target_root_rejected'] for row in caps)
    complete=len(caps)==6 and len(mapping)==16 and sum(len(g['members']) for g in mapping)==48
    status='NULL' if complete and all_below else 'EXPLORATORY'
    return encode(dict(status=status,seed=int(seed),complete_coverage=complete,
        all_six_profiles_certified_below_target=all_below,target=state['target']['complex_lower'],
        controls=controls,target_dual=target_dual,profile_caps=caps,ledger_mapping=mapping,
        capacity_counts_per_replica=dict(zip(CAPS,CAPACITY_COUNTS)),widths=list(WIDTHS),
        old_inventory_per_call=OLD_INVENTORY,new_inventory_per_call=NEW_INVENTORY,
        new_basis_counts_per_replica=new_counts,new_idle_per_replica=new_idle,
        basis_matrix=matrix,basis_inverse=inverse,dual_coefficient_rows=dual,
        pattern_count=len(patterns),pattern_census_sha256=digest(patterns),
        reduced_cost_coefficient_sha256=digest(reduced),coefficient_zero_reduced_costs=sum(not p for p in reduced),
        source_pins=deepcopy(state['pins']),source_attribution=deepcopy(state['pins']['source_attribution']),
        template_binding=deepcopy(state['template_binding']),
        trusted_interval_source=dict(path=CEILING[0],sha256=CEILING[1],attribution='Douglas Colkitt, Apache-2.0; original assistance attribution retained in source.'),
        solver_calls=0,n_permutations=0,cpu_seconds=time.process_time()-started,
        proof='Exact nonnegative basis counts prove fractional primal feasibility. B inverse derives a symbolic dual with c_B=B^T y. Every one of1163reduced-cost polynomials is either coefficientwise zero or has a strictly positive rational lower bound at the tested exponent. Weak duality plus increasing complete moments gives the upper cap; the feasible primal gives its lower endpoint.',
        native_and_physical_scope='Only conditional fixed-template packing bounds.83buffers are explicitly retained in G2 ledgers; no actual changed-word native/physical/supplier release is claimed.',
        integrality_caveat='The new basis has rational counts and need not be realizable as an integerT74allocation. This strengthens validity as an optimistic upper bound, never an existence claim.',
        null_scope='Only all48matched G2 addresses represented by16immutable ledger classes/sixpaid profiles, with fixed666call dispatch, PR2917 controller capacities,408helper roles and one9-to7extraction percall. No claim about other endpoint sets, joint extractions, templates or production families.',
        outer_relation='Direct complex endpoint comparison under the retained modern24-place ledger. No historicala/(1+a)conversion is applied.'))
