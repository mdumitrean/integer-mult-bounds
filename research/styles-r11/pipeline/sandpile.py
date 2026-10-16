"""M2 exactness/confluence and rule-preserving owner-fill diagnostics.

These are lattice, capacity and concave-moment protocols. No intrinsic graph
Laplacian or sandpile group is supplied by the word or fill. Every parallel
entry is intended for pipeline/pool.py, after the coordinator preregisters it.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
import random
import statistics
import time

import fill

_SAMPLERS=[]
_OPTIMA={}
_COSTS=None
_REPAIRS=[]
_REPAIR_MODELS=[]
_REPAIR_BASE=None
_REPAIR_REFERENCES={}


def prepare_s2(paths,endpoint="0.001717794984118634663827"):
    """Parent-load exact graph objects; solving is a separate pool task."""
    import nulls
    import wordio
    global _SAMPLERS,_COSTS
    _SAMPLERS=[nulls.FrameSampler(wordio.load(path)) for path in paths]
    F,_=wordio.toolkit();_COSTS=F.Costs(endpoint)
    _OPTIMA.clear()
    _delta_interval.cache_clear()
    return [dict(index=i,word=s.word.attribution,variables=len(s.variables)) for i,s in enumerate(_SAMPLERS)]


def _json_metadata(value):
    if isinstance(value,Fraction):
        return str(value)
    if isinstance(value,dict):
        if any(not isinstance(k,(str,int,float,bool,type(None))) for k in value):
            return {"entries":[{"key":_json_metadata(k),"value":_json_metadata(v)} for k,v in value.items()]}
        return {k:_json_metadata(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [_json_metadata(x) for x in value]
    return value


def optimum_task(arg):
    """One reference solve with true-cost interval, outside all order loops."""
    import nulls
    import wordio
    sampler=_SAMPLERS[arg["index"]]
    endpoint=arg.get("endpoint","0.001717794984118634663827")
    F,_=wordio.toolkit()
    start=time.monotonic()
    try:
        with nulls.solver_timeout(min(600,arg.get("timeout",600))):
            costs=F.Costs(endpoint)
            result=F.optimal_frames(sampler.graph.w,costs,graph=sampler.graph,
                                    check_literal=True,interval=True)
    except TimeoutError as exc:
        return dict(status="TIMEOUT",certified=False,endpoint=endpoint,reason=str(exc),
                    seconds=time.monotonic()-start)
    profile=Counter(result["profile"]);profile.update(sampler.word.centre_paid)
    literal=Counter(result["literal_profile"]);literal.update(sampler.word.centre_paid)
    interval=result.get("interval")
    valid_interval=bool(interval is not None and interval["lower"]<=interval["upper"])
    return dict(status="PASS" if result["certified"] and valid_interval else "EXPLORATORY",
                certified=bool(result["certified"]),integer_surrogate_certified=bool(result["certified"]),
                certification="Exact integer-surrogate optimum; rational interval bounds the true toolkit cost minimum. It does not establish uniqueness of a true-moment optimum profile.",
                endpoint=endpoint,cost=str(result["cost"]),literal_cost=str(result["literal_cost"]),
                profile=dict(profile),literal_profile=dict(literal),
                true_moment_interval=_json_metadata(interval),true_moment_interval_valid=valid_interval,
                exact_true_optimum_profile_proved=False,
                surrogate_not_true_minimal=bool(interval and interval.get("surrogate_not_minimal")),
                true_cost_scope="Pinned toolkit T_r includes its per-child fallback overhead; this is not the global kappa-root equation. Interval excludes the unchanged centre descents.",
                centre_paid=dict(sampler.word.centre_paid),parts=_json_metadata(result["parts"]),
                seconds=time.monotonic()-start)


@lru_cache(maxsize=4096)
def _delta_interval(delta_key):
    lower=sum(n*(_COSTS.exact[r] if n>0 else _COSTS.upper[r]) for r,n in delta_key)
    upper=sum(n*(_COSTS.upper[r] if n>0 else _COSTS.exact[r]) for r,n in delta_key)
    return lower,upper


def install_optimum(index,metadata):
    """Install the already checked one-per-word reference in the parent."""
    _OPTIMA[index]=metadata


def _local_delta(sampler,assignment,k,new):
    import wordio
    g=sampler.graph
    current=lambda j:assignment.get(j,tuple(g.nodes[j][1]))
    delta=Counter()
    for left,right,reg in sampler.edges[k]:
        oldl,oldr=current(left),current(right)
        newl=new if left==k else oldl
        newr=new if right==k else oldr
        if not wordio.contained(newl,newr):return None
        oldd,newd=len(oldr)-len(oldl),len(newr)-len(newl)
        if oldd:delta[oldd]-=1
        if newd:delta[newd]+=1
    return {r:n for r,n in delta.items() if n}


def _order_seed(experiment, seed, identity, order):
    """Order streams are independent of batch boundaries and worker scheduling."""
    data=json.dumps([experiment,int(seed),identity,int(order)],sort_keys=True,separators=(",",":"))
    return int.from_bytes(hashlib.sha256(data.encode()).digest()[:16],"big")


def _word_identity(sampler):
    attribution=sampler.word.attribution
    return {k:attribution[k] for k in ("pin_key","git_blob","blob","sha256") if k in attribution} or attribution


def _reference_comparison(sampler,optimum):
    reference={int(r):n for r,n in optimum["profile"].items()}
    lower=sum(n*_COSTS.exact[r] for r,n in reference.items())
    upper=sum(n*_COSTS.upper[r] for r,n in reference.items())
    comparison_upper=upper
    interval=optimum.get("true_moment_interval")
    if interval and interval.get("fine_upper") is not None:
        centre_upper=sum(n*_COSTS.upper[r] for r,n in sampler.word.centre_paid.items())
        comparison_upper=min(upper,Fraction(interval["fine_upper"])+centre_upper)
    return reference,lower,upper,comparison_upper


def _one_confluence_order(index,seed,order):
    import wordio
    sampler=_SAMPLERS[index];g=sampler.graph
    rng_seed=_order_seed("S-2",seed,_word_identity(sampler),order)
    rng=random.Random(rng_seed)
    assignment={k:tuple(g.upper[k]) for k in sampler.variables}
    initial_potential=sum(len(x) for x in assignment.values())
    minimum_potential=sum(len(g.lower[k]) for k in sampler.variables)
    moves=0;sweep=0;unresolved=0;examples=[]
    while True:
        sweep+=1;changed=False;sweep_unresolved=0
        variables=list(sampler.variables);rng.shuffle(variables)
        for k in variables:
            old=assignment[k];candidates=[]
            for new in sampler.domains[k]:
                if len(new)>=len(old) or not wordio.contained(new,old):continue
                delta=_local_delta(sampler,assignment,k,new)
                if not delta:continue
                lower,upper=_delta_interval(tuple(sorted(delta.items())))
                if upper<0:
                    candidates.append(new)
                elif lower<0:
                    unresolved+=1;sweep_unresolved+=1
                    if len(examples)<20:
                        examples.append(dict(order=order,sweep=sweep,gate=_json_metadata(k),
                            delta=delta,lower=str(lower),upper=str(upper)))
            if candidates:
                assignment[k]=rng.choice(candidates);moves+=1;changed=True
        if not changed:
            break
    final_potential=sum(len(x) for x in assignment.values())
    if not minimum_potential<=final_potential<=initial_potential or moves>initial_potential-final_potential:
        raise AssertionError("Strict dimension potential failed")
    profile=Counter(g.profile(assignment));profile.update(sampler.word.centre_paid)
    profile=dict(sorted(profile.items()))
    state=[[_json_metadata(k),list(assignment[k])] for k in sampler.variables]
    state_sha=hashlib.sha256(json.dumps(state,separators=(",",":")).encode()).hexdigest()
    return dict(order=order,order_seed=str(rng_seed),profile=profile,
        assignment_sha256=state_sha,accepted_lowerings=moves,sweeps=sweep,
        unresolved_legal_deltas=unresolved,unresolved_terminal_deltas=sweep_unresolved,
        unresolved_examples=examples,dimension_potential_initial=initial_potential,
        dimension_potential_final=final_potential,dimension_potential_lower_bound=minimum_potential,
        terminal_maximality_verified=sweep_unresolved==0)


def confluence_batch_task(arg):
    """Small pool checkpoint; no solver call occurs inside an order loop."""
    index,seed=arg["index"],arg["seed"]
    sampler=_SAMPLERS[index];optimum=_OPTIMA.get(index)
    first=arg.get("start_order",0);count=arg.get("order_count",1)
    if not 0<=first<100 or not 1<=count<=100-first:
        raise ValueError("S-2 batch must be contained in orders 0..99")
    if not optimum or not optimum.get("certified"):
        return dict(status="EXPLORATORY",index=index,seed=seed,word=sampler.word.attribution,
            start_order=first,order_count=count,orders=[],decision="Certified reference missing.")
    if Fraction(optimum["endpoint"])!=_COSTS.b:
        raise ValueError("Reference and dynamics endpoints differ")
    orders=[_one_confluence_order(index,seed,order) for order in range(first,first+count)]
    return dict(status="PASS",index=index,seed=seed,word=sampler.word.attribution,
        start_order=first,order_count=count,orders=orders,
        decision="Batch computed; scientific decision requires all 100 prescribed orders.")


def _unwrap_batches(outputs):
    values=[];failures=[]
    for i,out in enumerate(outputs):
        if out.get("status")=="OK":
            values.append(out["result"])
        elif "result" in out or out.get("status") in ("ERROR","TIMEOUT"):
            failures.append(dict(batch=i,status=out.get("status"),error=out.get("error")))
        else:
            values.append(out)
    return values,failures


def summarize_confluence(outputs,index,seed):
    """Preserve the >=95/100 bar; partial/missing batches cannot decide it."""
    sampler=_SAMPLERS[index];optimum=_OPTIMA.get(index)
    values,failures=_unwrap_batches(outputs)
    orders=[];identities_valid=True
    for value in values:
        identities_valid &= value.get("index")==index and value.get("seed")==seed
        orders.extend(value.get("orders",[]))
    order_ids=[o["order"] for o in orders]
    complete=identities_valid and sorted(order_ids)==list(range(100))
    technical=next((x["status"] for x in failures if x["status"]=="ERROR"),None)
    technical=technical or ("TIMEOUT" if failures else None)
    if not complete or not optimum or not optimum.get("certified"):
        return dict(status=technical or "EXPLORATORY",n_permutations=len(orders),
            statistics=dict(index=index,seed=seed,word=sampler.word.attribution,
                prescribed_orders=100,completed_orders=len(orders),order_ids=order_ids,
                identities_valid=identities_valid,failures=failures,certified_reference=optimum),
            decision="All 100 unique prescribed orders and a certified reference are required.")
    orders.sort(key=lambda x:x["order"])
    reference,ref_lower,ref_upper,comparison_upper=_reference_comparison(sampler,optimum)
    terminal_counts=Counter(tuple(sorted((int(r),n) for r,n in o["profile"].items())) for o in orders)
    maximal_counts=Counter(tuple(sorted((int(r),n) for r,n in o["profile"].items()))
                           for o in orders if o["terminal_maximality_verified"])
    hits=sum({int(r):n for r,n in o["profile"].items()}==reference for o in orders)
    unresolved=sum(o["unresolved_legal_deltas"] for o in orders)
    terminal_unresolved=sum(o["unresolved_terminal_deltas"] for o in orders)
    terminals=[];proved_worse=0;proved_worse_maximal=0
    for profile_key,count in sorted(terminal_counts.items()):
        p=dict(profile_key)
        lower=sum(n*_COSTS.exact[r] for r,n in p.items())
        upper=sum(n*_COSTS.upper[r] for r,n in p.items())
        worse=lower>comparison_upper
        if worse:
            proved_worse+=count
            proved_worse_maximal+=maximal_counts[profile_key]
        terminals.append(dict(profile=p,count=count,cost_lower=str(lower),cost_upper=str(upper),
            terminal_maximality_verified_count=maximal_counts[profile_key],
            rigorously_worse_and_maximal_count=maximal_counts[profile_key] if worse else 0,
            strictly_worse_than_reference_certified=worse))
    interval_valid=optimum.get("true_moment_interval_valid",False)
    reference_agreement="PASS" if hits>=95 else "NULL"
    exact_reference=optimum.get("exact_true_optimum_profile_proved",False)
    if hits>=95 and unresolved==0 and interval_valid and exact_reference and not optimum.get("surrogate_not_true_minimal",False):
        status="PASS"
        decision=f"{hits}/100 profiles equal an independently certified true-cost optimum profile; all local sign and maximality checks resolved. This is finite-sample agreement only."
    elif proved_worse_maximal>5 and interval_valid:
        status="NULL"
        decision=f"{proved_worse_maximal}/100 individually certified maximal terminals are rigorously worse than a feasible reference, failing the >=95/100 bar; other orders retain their reported uncertainties."
    else:
        status="EXPLORATORY"
        decision=f"Integer-surrogate reference agreement {reference_agreement} ({hits}/100; bar 95/100), but true-optimum, sign, or terminal comparison uncertainty prevents the full scientific verdict."
    value=dict(word=sampler.word.attribution,index=index,seed=seed,orders=100,
        order_stream="SHA256(experiment, seed, immutable word identifiers, order index), independent of batching",
        certified_reference=optimum,hits=hits,hit_rate=hits/100,
        original_profile_agreement_bar=95,reference_agreement_subtest_status=reference_agreement,
        distinct_terminal_profiles=len(terminal_counts),terminals=terminals,
        distinct_terminal_assignments=len({o["assignment_sha256"] for o in orders}),
        order_results=orders,strict_true_cost_decreases_verified=sum(o["accepted_lowerings"] for o in orders),
        unresolved_legal_deltas=unresolved,unresolved_terminal_deltas=terminal_unresolved,
        proved_worse_terminals=proved_worse,reference_true_cost_lower=str(ref_lower),
        proved_worse_maximal_terminals=proved_worse_maximal,
        reference_true_cost_upper=str(ref_upper),best_feasible_comparison_cost_upper=str(comparison_upper),
        terminal_maximality_verified=terminal_unresolved==0,
        terminal_maximality="Final full sweep tests every legal proper-subspace single-gate lowering using rational cost intervals.",
        potential_proof="Sum of mutable frame dimensions is a nonnegative integer and strictly decreases at every accepted lowering; this proves termination only.",
        exact_true_optimum_profile_proved=bool(exact_reference),
        scope="Profile agreement to a certified integer-surrogate reference at one endpoint. A true-minimum interval does not prove a unique exact-moment optimum profile; no state-confluence or abelianity theorem.")
    return dict(status=status,statistics=value,n_permutations=100,decision=decision)


def confluence_task(arg):
    """Compatibility wrapper; the coordinator should checkpoint small batches."""
    if arg.get("orders",100)!=100:
        raise ValueError("S-2 registration requires exactly 100 orders per seed")
    return summarize_confluence([confluence_batch_task(dict(arg,start_order=0,order_count=100))],
                                 arg["index"],arg["seed"])


def window_dag_audit(model):
    """All eligibility arcs go call(t,0) -> window(stop,1), a sink DAG."""
    count=0;zero=0
    for cap,start,stop in model.win.values():
        if stop<=start:zero+=1
        for t in range(max(0,start+1),min(model.calls-1,stop)+1):
            if not (t,0)<(stop,1):raise ValueError("non-DAG eligibility arc")
            count+=1
    return dict(vertices=model.calls+len(model.win),arcs=count,
                sink_windows=len(model.win),empty_eligibility_windows=zero,
                acyclic=True,topological_order="lexicographic (call-time,0), (window-stop,1)",
                intrinsic_laplacian=False,group_identity_burning="DROPPED: no intrinsic Laplacian or toppling rule")


def _walk_state(model):
    rem={(o,c,p):cap for (o,c),(cap,_,_) in model.win.items() for p in range(model.ports)}
    families=[set() for _ in range(model.calls)]
    rows=[tuple(r[:5]) for r in model.rows]
    for t,h,o,c,p in rows:
        rem[o,c,p]-=model.widths[t][h];families[t].add(model.family_id(o,c,p))
    eligible=[[] for _ in range(model.calls)]
    for (o,c),(cap,start,stop) in model.win.items():
        for t in range(max(0,start+1),min(model.calls-1,stop)+1):eligible[t].append((o,c))
    return rows,rem,families,eligible


def _proposal(model,rows,rem,families,eligible,rng,mutate):
    i=rng.randrange(len(rows));t,h,o,c,p=rows[i];old=o,c,p;width=model.widths[t][h]
    oldfam=model.family_id(o,c,p);rem[old]+=width;families[t].remove(oldfam)
    dest=old
    for _ in range(60):
        o2,c2=rng.choice(eligible[t]);p2=rng.randrange(model.ports);candidate=o2,c2,p2
        if rem[candidate]>=width and model.family_id(o2,c2,p2) not in families[t]:
            dest=candidate;break
    changed=dest!=old
    if changed:
        # Remainder changes: x->x+w at source, y->y-w at destination.
        before=(rem[old]-width,rem[dest]);after=(rem[old],rem[dest]-width)
    else:
        before=after=(rem[old]-width,)
    if mutate:
        rem[dest]-=width;families[t].add(model.family_id(*dest));rows[i]=(t,h)+dest
    else:
        rem[old]-=width;families[t].add(oldfam)
    return before,after,changed


def walk_slope(model,seed,moves=300000,pilot=10000,initial_checkpoint=1000):
    """Independent literal-state pilot predicts initial per-attempt root decay.

    Every move preserves exact family/time/capacity constraints. Prefix offsets
    are rebuilt deterministically for the final independent literal audit.
    The chain is local and starts at the shipped fill; no uniformity claim.
    """
    if pilot<=0 or initial_checkpoint<=0 or moves<initial_checkpoint:
        raise ValueError("Positive pilot/checkpoint and moves>=checkpoint are required")
    baseline=fill.audit(model)
    local=model.overlay_local_profiles or model.local_profiles
    idle0=baseline["idle"]
    profile0=fill._profile(local,idle0);k0=fill.kappa_float(profile0)
    derivative=math.fsum(c*(r/73)**(1-k0)*math.log(73/r) for r,c in profile0.items())
    weights={r:(r/73)**(1-k0) if r else 0.0 for r in range(1+max(c for c,_,_ in model.win.values()))}
    rows,rem,families,eligible=_walk_state(model)
    pilot_rng=random.Random(seed^0x534C4F50);pilot_deltas=[];pilot_changes=0
    for _ in range(pilot):
        before,after,changed=_proposal(model,rows,rem,families,eligible,pilot_rng,False)
        delta=math.fsum(weights[r] for r in after)-math.fsum(weights[r] for r in before)
        pilot_deltas.append(-delta/derivative);pilot_changes+=changed
    predicted=statistics.fmean(pilot_deltas)
    rng=random.Random(seed)
    checkpoints=sorted(set([initial_checkpoint,3000,10000,30000,100000,moves]))
    checkpoints=[x for x in checkpoints if x<=moves]
    log=[];accepted=0;cumulative_delta=0.0
    for step in range(1,moves+1):
        before,after,changed=_proposal(model,rows,rem,families,eligible,rng,True)
        accepted+=changed
        cumulative_delta+=math.fsum(weights[r] for r in after)-math.fsum(weights[r] for r in before)
        if step in checkpoints:
            idle=Counter(r for r in rem.values() if r)
            profile=fill._profile(local,idle);k=fill.kappa_float(profile)
            clump=sum(rem[b] in (0,model.win[b[:2]][0]) for b in rem)/len(rem)
            log.append(dict(attempts=step,changed_moves=accepted,kappa=k,kappa_delta=k-k0,
                            linearized_path_delta=-cumulative_delta/derivative,
                            clumping=clump,idle=dict(sorted(idle.items()))))
    measured=log[0]["kappa_delta"]/initial_checkpoint
    relerr=abs(measured-predicted)/abs(predicted) if predicted else None
    final_rows=fill.compact_rows(model,rows)
    final=fill.audit(model,final_rows,require_profile=False)
    status="EXPLORATORY" if relerr is None else "PASS" if relerr<=.1 and baseline["clumping"]>=.75 else "NULL"
    return dict(status=status,statistics=dict(fill=model.name,seed=seed,pilot_attempts=pilot,
                 pilot_changed_moves=pilot_changes,pilot_slope_sd=statistics.pstdev(pilot_deltas),
                 predicted_initial_slope=predicted,measured_initial_slope=measured,
                 initial_checkpoint_attempts=initial_checkpoint,relative_error=relerr,
                 original_clumping=baseline["clumping"],clumping_bar=.75,trace=log,
                 final_literal_rules_verified=final["all_literal_rules_verified"],
                 final_profile=fill._profile(local,final["idle"]),window_dag=window_dag_audit(model),
                 attribution=model.attributions,sources=model.sources,
                 profile_basis="held-word overlay" if model.overlay_local_profiles else "literal provider metadata",
                 scope="Independent one-state pilot vs finite early local-walk slope; not a uniform feasible-fill null."),
                n_permutations=0,
                decision=f"Initial slope relative error {relerr} (bar 0.1; None means a zero pilot prediction); initial clumping {baseline['clumping']:.6g} (bar 0.75).")


def fill_task(arg):
    model=fill._MODELS[arg.get("index",0)]
    if arg["experiment"]=="S-4":
        return walk_slope(model,arg["seed"],arg.get("moves",300000),arg.get("pilot",10000),arg.get("initial_checkpoint",1000))
    if arg["experiment"]=="M2-AUDIT":
        return dict(status="PASS",statistics=dict(literal=fill.audit(model),dag=window_dag_audit(model)),
                    decision="Literal conservation and sink DAG exact; intrinsic Laplacian absent.",n_permutations=0)
    raise ValueError(arg["experiment"])


def prepare_s5(model=None,perturbations=10):
    """Parent-load the original ten fixed helper-width perturbations.

    An altered local word is not available. The explicit rank-1 closure below
    balances mass for conditional diagnostics only; it is not a valid word
    construction and cannot certify the original width-edit utility claim.
    """
    global _REPAIRS,_REPAIR_MODELS,_REPAIR_BASE
    if perturbations!=10:
        raise ValueError("S5 registers five 8->9 and five 9->8 helper perturbations")
    if model is None:
        model=next(m for m in fill._MODELS if m.name=="2802")
    if model.name!="2802":
        raise ValueError("S5 primary perturbations are on the #2802 fill")
    literal=fill.audit(model)
    rows,remaining,families,eligible=_walk_state(model)
    bin_roles=defaultdict(list);helper_rows=defaultdict(list)
    for i,row in enumerate(rows):
        bin_roles[row[2:]].append(i);helper_rows[row[1]].append(i)
    common=set.intersection(*(set(range(len(ws))) for ws in model.widths))
    chosen=[];models=[]
    for before,after in ((8,9),(9,8)):
        helpers=[h for h in sorted(common) if all(ws[h]==before for ws in model.widths)]
        if len(helpers)<5:
            raise ValueError(f"Need five helper labels of width {before} in every call")
        for helper in helpers[:5]:
            delta=after-before
            changed_widths=[list(ws) for ws in model.widths]
            changed_local=[dict(profile) for profile in model.local_profiles]
            for t in range(model.calls):
                changed_widths[t][helper]=after
                changed_local[t][1]=changed_local[t].get(1,0)+delta
                if changed_local[t][1]<0:
                    raise ValueError("Rank-1 counterfactual closure would have a negative count")
                if not changed_local[t][1]:del changed_local[t][1]
            local_before=sum(r*n for p in model.local_profiles for r,n in p.items())
            local_after=sum(r*n for p in changed_local for r,n in p.items())
            width_before=sum(map(sum,model.widths));width_after=sum(map(sum,changed_widths))
            if local_after-local_before!=width_after-width_before or width_after-width_before!=model.calls*delta:
                raise AssertionError("Counterfactual signed mass ledger failed")
            record=dict(index=len(chosen),kind="width-perturbation",helper=helper,
                old_width=before,new_width=after,affected_calls=model.calls,
                reference_key=f"width:{before}->{after}",
                changed_width_mass=model.calls*delta,closure_rank1_count_delta=model.calls*delta,
                authentic_changed_word_available=False,
                counterfactual_local_profile="Add one rank-1 local child per affected call for +1 width; remove one for -1 width. Diagnostic mass closure only.",
                ledger=dict(delta_width_mass=width_after-width_before,
                    delta_local_paid_rank_mass=local_after-local_before,
                    delta_idle_rank_mass=-(width_after-width_before),delta_global_rank_mass=0))
            notes=dict(model.source_notes or {})
            notes["S5_counterfactual"]=record
            changed=replace(model,name=f"2802:helper{helper}:{before}->{after}",
                widths=changed_widths,local_profiles=changed_local,overlay_local_profiles=None,
                source_notes=notes)
            chosen.append(record);models.append(changed)
    _REPAIR_BASE=dict(model=model,rows=tuple(rows),remaining=remaining,
        families=tuple(frozenset(x) for x in families),eligible=tuple(tuple(x) for x in eligible),
        bin_roles={b:tuple(v) for b,v in bin_roles.items()},
        helper_rows={h:tuple(v) for h,v in helper_rows.items()},literal_audit=literal)
    _REPAIRS=chosen;_REPAIR_MODELS=models;_REPAIR_REFERENCES.clear()
    seen=set();references=[]
    for start in chosen:
        if start["reference_key"] not in seen:
            references.append(dict(index=start["index"],reference_key=start["reference_key"]))
            seen.add(start["reference_key"])
    return dict(fill=model.name,starts=chosen,once_per_relaxed_inventory_references=references,
        attribution=model.attributions,sources=model.sources,fixed_global_rank_mass=model.expected_mass,
        selection="Five lowest helper labels of width 8 in every call, then five lowest labels of width 9; modify that label in every call.",
        primary_scope="Exact assignment order-independence on the modified role-width problem.",
        utility_scope="Original valid-word utility is unresolved without authentic changed local words; rank-1 closure roots are explicitly counterfactual diagnostics.")


def prepare_placement_control(model=None,perturbations=10):
    """Parent-load one fill and preselect lexicographic overflow relocations.

    This registered control preserves widths and the pinned local profile.
    Its perturbation is a misplaced existing role, not PLAN 4.2's width edit;
    it cannot by itself settle the width-edit hosting-oracle claim.
    """
    global _REPAIRS,_REPAIR_BASE,_REPAIR_MODELS
    if perturbations!=10:
        raise ValueError("The S5 placement-control family contains exactly ten starts")
    if model is None:
        model=next(m for m in fill._MODELS if m.name=="2802")
    if model.name!="2802":
        raise ValueError("S5 starts are registered on the #2802 fill")
    literal=fill.audit(model)
    rows,remaining,families,eligible=_walk_state(model)
    bin_roles=defaultdict(list)
    for i,row in enumerate(rows):
        bin_roles[row[2:]].append(i)
    chosen=[]
    for i in sorted(range(len(rows)),key=lambda j:rows[j][:2]):
        t,h,o,c,p=rows[i];source=(o,c,p);width=model.widths[t][h]
        source_family=model.family_id(*source)
        occupied=families[t]-{source_family}
        for o2,c2 in sorted(eligible[t]):
            cap,_,_=model.win[o2,c2]
            if cap<width:
                continue
            for p2 in range(model.ports):
                dest=(o2,c2,p2)
                if dest==source or model.family_id(*dest) in occupied:
                    continue
                if remaining[dest]>=width:
                    continue
                chosen.append(dict(index=len(chosen),kind="placement-control",reference_key="placement-control",row_index=i,time=t,helper=h,
                    width=width,source=list(source),destination=list(dest),
                    initial_overflow=width-remaining[dest]))
                if len(chosen)==perturbations:break
            if len(chosen)==perturbations:break
        if len(chosen)==perturbations:break
    if len(chosen)!=perturbations:
        raise ValueError("Fewer than ten admissible deterministic overflow relocations")
    _REPAIR_BASE=dict(model=model,rows=tuple(rows),remaining=remaining,
        families=tuple(frozenset(x) for x in families),eligible=tuple(tuple(x) for x in eligible),
        bin_roles={b:tuple(v) for b,v in bin_roles.items()},literal_audit=literal)
    _REPAIRS=chosen
    _REPAIR_MODELS=[model]*len(chosen)
    _REPAIR_REFERENCES.clear()
    return dict(fill=model.name,starts=chosen,attribution=model.attributions,sources=model.sources,
        fixed_role_width_counts=dict(Counter(w for row in model.widths for w in row)),
        fixed_rank_mass=model.expected_mass,
        selection="First ten lexicographic (time,helper,owner,child,port) relocations with legal time/family, role width <= bin capacity, and resulting positive overflow.",
        scope="Fixed-inventory placement control; not the original width-perturbation utility experiment.")


def repair_reference_task(arg):
    """One common relaxation solve outside all S5 repair-order loops."""
    import growth_m3
    import nulls
    index=arg.get("index",0)
    model=_REPAIR_MODELS[index]
    timeout=min(600,int(arg.get("timeout",300)))
    try:
        with nulls.solver_timeout(timeout):
            value=growth_m3.pattern_ceiling(model,time_limit=timeout)
    except TimeoutError as exc:
        return dict(status="TIMEOUT",reason=str(exc),certified=False,
            attribution=model.attributions,sources=model.sources)
    value=dict(value)
    value["certified"]=bool(value.get("dual",{}).get("exact_rational_verification")
        and value.get("dual",{}).get("root_rejected")
        and not value.get("dual",{}).get("inequality_violations"))
    value["reference_key"]=_REPAIRS[index]["reference_key"]
    value["reference_shared_across_starts_with_same_relaxed_inventory"]=True
    value["primal_exact_rehost_solved"]=False
    return value


def install_repair_reference(metadata,index=0):
    """Install a once-per-inventory reference before forking order workers."""
    _REPAIR_REFERENCES[_REPAIRS[index]["reference_key"]]=metadata


@lru_cache(maxsize=4096)
def _profile_root_bracket(profile_key):
    import growth_m3
    import growth
    profile=dict(profile_key)
    proposal=growth.root(profile)
    bracket=growth_m3._rational_root_bracket(profile,proposal)
    return dict(bracket,diagnostic_decimal=str(proposal))


def _assignment_digest(model,rows):
    """Offsets are canonicalized by (time,helper), so physical labels count."""
    canonical=sorted(rows,key=lambda x:x[:2])
    canonical=fill.compact_rows(model,canonical)
    digest=hashlib.sha256()
    for row in canonical:
        digest.update((",".join(map(str,row))+"\n").encode())
    return digest.hexdigest(),canonical


def _repair_order(index,seed,order):
    base=_REPAIR_BASE;model=_REPAIR_MODELS[index];start=_REPAIRS[index]
    identity=dict(fill=model.name,start=start,sources=model.sources)
    rng_seed=_order_seed("S-5-"+start["kind"],seed,identity,order)
    rng=random.Random(rng_seed)
    rows=list(base["rows"]);rem=dict(base["remaining"])
    families=[set(x) for x in base["families"]]
    modified_bins={}
    def occupants(b):
        if b not in modified_bins:
            modified_bins[b]=set(base["bin_roles"].get(b,()))
        return modified_bins[b]
    if start["kind"]=="placement-control":
        i=start["row_index"];t,h,o,c,p=rows[i];source=(o,c,p)
        dest=tuple(start["destination"]);width=model.widths[t][h]
        rem[source]+=width;rem[dest]-=width
        families[t].remove(model.family_id(*source));families[t].add(model.family_id(*dest))
        occupants(source).remove(i);occupants(dest).add(i);rows[i]=(t,h)+dest
    else:
        delta=start["new_width"]-start["old_width"]
        for i in base["helper_rows"][start["helper"]]:
            rem[rows[i][2:]]-=delta
    overflow={b for b,n in rem.items() if n<0}
    initial_potential=sum(-rem[b] for b in overflow)
    moves=0;examples=[];stuck_details=[];previous_potential=initial_potential
    while overflow:
        sources=sorted(overflow);rng.shuffle(sources)
        moved=False
        for source in sources:
            candidate_roles=sorted(occupants(source));rng.shuffle(candidate_roles)
            for i in candidate_roles:
                t,h,o,c,p=rows[i];width=model.widths[t][h]
                oldfam=model.family_id(*source)
                rem[source]+=width;families[t].remove(oldfam)
                dest=None
                # Rejection plus a uniform exact fallback is uniform over all
                # currently feasible eligible bins, conditional on this role.
                for _ in range(64):
                    oo,cc=rng.choice(base["eligible"][t]);pp=rng.randrange(model.ports)
                    trial=(oo,cc,pp)
                    if rem[trial]>=width and model.family_id(*trial) not in families[t]:
                        dest=trial;break
                if dest is None:
                    n=0
                    for oo,cc in base["eligible"][t]:
                        for pp in range(model.ports):
                            trial=(oo,cc,pp)
                            if rem[trial]<width or model.family_id(*trial) in families[t]:
                                continue
                            n+=1
                            if rng.randrange(n)==0:dest=trial
                if dest is None:
                    rem[source]-=width;families[t].add(oldfam)
                    continue
                if dest==source:
                    raise AssertionError("Overflow source cannot accept its released role")
                rem[dest]-=width;families[t].add(model.family_id(*dest))
                occupants(source).remove(i);occupants(dest).add(i);rows[i]=(t,h)+dest
                moves+=1;moved=True
                if len(examples)<64:
                    examples.append(dict(time=t,helper=h,width=width,
                        source=list(source),destination=list(dest)))
                if rem[source]>=0:overflow.remove(source)
                break
            if moved:break
        if not moved:
            stuck_details=[dict(bin=list(b),overflow=-rem[b],
                roles=[[rows[i][0],rows[i][1],model.widths[rows[i][0]][rows[i][1]]]
                       for i in sorted(occupants(b))]) for b in sorted(overflow)]
            break
        potential=sum(-rem[b] for b in overflow)
        if potential>=previous_potential or moves>initial_potential:
            raise AssertionError("Overflow potential did not provide the finite move bound")
        previous_potential=potential
    final_potential=sum(-rem[b] for b in overflow)
    state_sha,canonical=_assignment_digest(model,rows)
    result=dict(start=index,order=order,order_seed=str(rng_seed),
        assignment_sha256=state_sha,moves=moves,initial_overflow=initial_potential,
        final_overflow=final_potential,repair_feasible=not overflow,
        move_examples=examples,stuck_bins=stuck_details,
        termination_proof="Total positive integer overflow strictly decreases at each move into a capacity-feasible destination; an exhaustive failed round certifies local rule blockage only.")
    if overflow:
        result["status"]="REPAIR_STUCK"
        return result
    audited=fill.audit(model,canonical,require_profile=False)
    profile_key=tuple(sorted(audited["profile"].items()))
    bracket=_profile_root_bracket(profile_key)
    reference=_REPAIR_REFERENCES.get(start["reference_key"],{})
    upper=reference.get("certified_ceiling")
    certified=bool(reference.get("certified") and bracket.get("lower_certified")
                   and bracket.get("upper_certified") and upper is not None)
    gap=Fraction(upper)-Fraction(bracket["lo"]) if certified else None
    if gap is not None and gap<0:
        raise AssertionError("Feasible terminal exceeds a claimed relaxation ceiling")
    result.update(status="PASS",profile=audited["profile"],idle=audited["idle"],
        root_interval=bracket,all_literal_rules_verified=audited["all_literal_rules_verified"],
        rank_mass=audited["rank_mass"],utility_gap_upper=str(gap) if gap is not None else None,
        within_1e8_certified=bool(gap is not None and gap<=Fraction(1,10**8)),
        used_cells=audited["used_cells"],idle_cells=audited["idle_cells"])
    return result


def repair_batch_task(arg):
    """Checkpoint one or a few repair orders; no solver is called here."""
    index,seed=arg["index"],arg["seed"]
    first=arg.get("start_order",0);count=arg.get("order_count",1)
    if not 0<=index<len(_REPAIRS) or not 0<=first<100 or not 1<=count<=100-first:
        raise ValueError("S5 needs a registered start and a batch contained in orders 0..99")
    return dict(status="PASS",index=index,seed=seed,start_order=first,order_count=count,
        orders=[_repair_order(index,seed,order) for order in range(first,first+count)],
        decision="Order batch computed; all 100 orders of all ten starts are required for the family verdict.")


def summarize_repair(outputs,seed):
    """Preserve exact-assignment and >=90%-of-perturbations scientific bars."""
    values,failures=_unwrap_batches(outputs)
    rows=[];identities=True
    for value in values:
        identities &= value.get("seed")==seed
        rows.extend(value.get("orders",[]))
    indices=[(r["start"],r["order"]) for r in rows]
    expected=[(i,j) for i in range(10) for j in range(100)]
    complete=identities and sorted(indices)==expected
    technical="ERROR" if any(x["status"]=="ERROR" for x in failures) else "TIMEOUT" if failures else None
    model=_REPAIR_BASE["model"]
    kind=_REPAIRS[0]["kind"]
    if not complete:
        return dict(status=technical or "EXPLORATORY",n_permutations=len(rows),
            statistics=dict(seed=seed,protocol=kind,prescribed_orders=1000,completed_orders=len(rows),
                identities_valid=identities,failures=failures,attribution=model.attributions,
                sources=model.sources),
            decision="Incomplete S5 family; neither scientific bar is decided.")
    per_start=[]
    for index in range(10):
        group=sorted((r for r in rows if r["start"]==index),key=lambda r:r["order"])
        assignments=Counter(r["assignment_sha256"] for r in group if r["repair_feasible"])
        profiles=Counter(tuple(sorted((int(k),n) for k,n in r["profile"].items()))
                         for r in group if r["repair_feasible"])
        identical=max(assignments.values(),default=0)
        close=sum(r.get("within_1e8_certified",False) for r in group)
        lower_values=[Fraction(r["root_interval"]["lo"]) for r in group
                      if r.get("root_interval",{}).get("lower_certified")]
        best_lower=max(lower_values) if lower_values else None
        disproved=0
        for r in group:
            if not r["repair_feasible"]:
                r["conditional_utility_failure_certified"]=True
            else:
                bracket=r["root_interval"]
                r["conditional_utility_failure_certified"]=bool(best_lower is not None and bracket.get("upper_certified")
                    and best_lower-Fraction(bracket["hi"])>Fraction(1,10**8))
            disproved+=r["conditional_utility_failure_certified"]
            if r.get("within_1e8_certified") and r["conditional_utility_failure_certified"]:
                raise AssertionError("Mutually inconsistent utility certificates")
        per_start.append(dict(start=_REPAIRS[index],identical_terminal_assignments=identical,
            identical_terminal_fraction=identical/100,primary_status="PASS" if identical>=95 else "NULL",
            distinct_terminal_assignments=len(assignments),distinct_terminal_profiles=len(profiles),
            feasible_orders=sum(r["repair_feasible"] for r in group),
            conditional_utility_close_certified=close,conditional_utility_failure_certified=disproved,
            conditional_utility_unresolved=100-close-disproved,
            conditional_utility_sufficient_bar_met=close>=90,
            best_feasible_root_lower=str(best_lower) if best_lower is not None else None,
            terminal_assignment_counts=dict(sorted(assignments.items())),
            terminal_profile_counts=[dict(profile=dict(p),count=n) for p,n in profiles.items()],
            order_results=group))
    primary="PASS" if all(p["primary_status"]=="PASS" for p in per_start) else "NULL"
    sufficient=sum(p["conditional_utility_sufficient_bar_met"] for p in per_start)
    conditional_utility="PASS" if sufficient>=9 else "EXPLORATORY"
    if kind=="width-perturbation":
        utility="EXPLORATORY"
        utility_reason="No authentic changed local word/profile. Rank-1 closure and its exact root bounds describe a counterfactual objective only."
    else:
        utility=conditional_utility
        utility_reason="A rational relaxation ceiling plus feasible terminal bounds can prove closeness without an exact primal rehost; loose bounds leave utility unresolved."
    status="NULL" if primary=="NULL" else "PASS" if utility=="PASS" else "EXPLORATORY"
    return dict(status=status,n_permutations=1000,statistics=dict(seed=seed,
        protocol="S5 "+kind,primary_status=primary,utility_status=utility,
        utility_reason=utility_reason,per_start=per_start,
        conditional_utility_status=conditional_utility,
        perturbations_with_sufficient_closeness_certificate=sufficient,
        utility_perturbation_bar=9,orders_per_perturbation=100,
        conservative_sufficient_order_bar=90,
        utility_bar_interpretation="At least 9/10 perturbations; >=90/100 rigorously close orders is a preregistered sufficient condition for each. Failure of this stronger certificate is not a utility NULL.",
        references=_REPAIR_REFERENCES,
        assignment_identity="Canonical (time,helper,owner,child,port,offset) records; offsets rebuilt in sorted (time,helper) order. Profiles are secondary.",
        source_attribution=model.attributions,sources=model.sources,
        source_rank_mass=model.expected_mass,
        counterfactual_diagnostic=kind=="width-perturbation",
        original_width_utility_answered=False,
        scope="Finite exact-assignment order-independence for the prescribed overflow dynamics. No abelianity theorem or kappa construction claim."),
        decision=f"Exact-assignment primary {primary}; original utility {utility}; {sufficient}/10 perturbations satisfy the conditional sufficient closeness certificate.")
