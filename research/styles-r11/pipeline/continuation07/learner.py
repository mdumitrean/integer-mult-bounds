"""Small preregistered retrospective models; no imported or import-time science.

Only prospective numeric features are accepted. Historical labels are stored
separately. All fitting and permutation tasks are dispatched by pool.py.
"""
from collections import defaultdict
import hashlib
import json
import math
import random
import time

_STATE = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def _key(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def prepare(rows, metadata):
    global _STATE
    need(_STATE is None,'parent prepares model data exactly once')
    import numpy as np
    from scipy.optimize import minimize
    need(rows and isinstance(rows,list),'nonempty historical transition table')
    names=sorted(rows[0]['features'])
    need(all(sorted(r['features'])==names for r in rows),'fixed complete numeric feature schema')
    x=np.asarray([[r['features'][n] for n in names] for r in rows],dtype=float)
    need(np.isfinite(x).all(),'finite prospective features')
    proposal=[i for i,n in enumerate(names) if n.startswith('proposal_')]
    context=[i for i,n in enumerate(names) if n.startswith('context_')]
    need(proposal and context and len(proposal)+len(context)==len(names), 'explicit proposal/context whitelist')
    groups=[str(r['pair_group']) for r in rows]
    ids=[str(r.get('row_id',r.get('candidate_id',i))) for i,r in enumerate(rows)]
    need(len(ids)==len(set(ids)),'unique proposal/provider rows')
    labels={target:np.asarray([r['labels'].get(target) if r['labels'].get(target) is not None else -1
                              for r in rows],dtype=int) for target in ('frame_legal','worse')}
    need(set(labels['frame_legal'])=={0,1},'both feasibility classes')
    need(all(v in (-1,0,1) for v in labels['worse']),'nullable downstream cost-harm labels')
    need(np.array_equal(labels['worse']>=0,labels['frame_legal']==1),'cost-harm labels only on legal candidates')
    by_group=defaultdict(list)
    for i,g in enumerate(groups):by_group[g].append(i)
    strata={}
    slots={}
    for g,indices in by_group.items():
        values={_key(rows[i]['permutation_stratum']) for i in indices}
        need(len(values)==1,'one proposal stratum per original contact pair')
        strata[g]=next(iter(values))
        slots[g]={_key(rows[i]['permutation_slot']):i for i in indices}
        need(len(slots[g])==len(indices),'unique paired provider/placement/corner slot')
    strata_groups=defaultdict(list)
    for g in sorted(by_group):strata_groups[strata[g]].append(g)
    for gs in strata_groups.values():
        need(all(set(slots[g])==set(slots[gs[0]]) for g in gs),'whole-group permutation slot alignment')
        for slot in slots[gs[0]]:
            first=x[slots[gs[0]][slot],proposal]
            need(all(np.array_equal(first,x[slots[g][slot],proposal]) for g in gs),
                 'all proposal-only features fixed slotwise within permutation strata')
    _STATE=dict(np=np,minimize=minimize,rows=rows,metadata=metadata,x=x,names=names,
        proposal=proposal,context=context,groups=groups,ids=ids,labels=labels,
        by_group=dict(by_group),strata_groups=dict(strata_groups),slots=slots)
    return dict(rows=len(rows),original_contact_pair_groups=len(by_group),features=len(names),
        proposal_features=[names[i] for i in proposal],context_features=[names[i] for i in context],
        group_size_counts={str(n):sum(len(v)==n for v in by_group.values()) for n in sorted({len(v) for v in by_group.values()})},
        permutation_strata={k:len(v) for k,v in strata_groups.items()},
        movable_permutation_groups=sum(len(v) for v in strata_groups.values() if len(v)>1),
        singleton_permutation_strata=sum(len(v)==1 for v in strata_groups.values()),
        targets={t:dict(positive=int((v==1).sum()),negative=int((v==0).sum()),censored=int((v<0).sum())) for t,v in labels.items()},
        full_kappa_success_training='UNAVAILABLE: no positive complete-kappa transitions in this flat proposal cohort',
        source_scope='Within one PR2966 source lineage; pair-blocked retrospective evaluation only.')


def _state():
    need(_STATE is not None,'registered parent preparation required')
    return _STATE


def _weights(groups, y, balanced=False):
    np=_state()['np']
    counts=defaultdict(int)
    for g in groups:counts[g]+=1
    w=np.asarray([1/counts[g] for g in groups],dtype=float)
    w/=w.sum()
    if balanced:
        for value in (0,1):
            mask=y==value
            need(mask.any(),'both target classes in training/evaluation')
            w[mask]*=0.5/w[mask].sum()
    return w


def _fit(x,y,groups,alpha=0.1):
    s=_state();np=s['np']
    w=_weights(groups,y,balanced=True)
    mean=(w[:,None]*x).sum(axis=0)
    scale=np.sqrt((w[:,None]*(x-mean)**2).sum(axis=0))
    scale[scale<1e-12]=1.0
    z=(x-mean)/scale
    z=np.column_stack([np.ones(len(z)),z])
    penalty=np.ones(z.shape[1]);penalty[0]=0
    def fun(beta):
        score=z@beta
        prob=np.exp(-np.logaddexp(0,-score))
        loss=float((w*(np.logaddexp(0,score)-y*score)).sum()+alpha/2*(penalty*beta*beta).sum())
        grad=z.T@(w*(prob-y))+alpha*penalty*beta
        return loss,grad
    result=s['minimize'](fun,np.zeros(z.shape[1]),method='L-BFGS-B',jac=True,
        options={'maxiter':300,'ftol':1e-12,'gtol':1e-8,'maxls':40})
    need(result.success and np.isfinite(result.x).all(),'fixed logistic optimizer converged: '+str(result.message))
    return dict(beta=result.x,mean=mean,scale=scale,iterations=int(result.nit),objective=float(result.fun))


def _predict(model,x):
    np=_state()['np']
    score=model['beta'][0]+((x-model['mean'])/model['scale'])@model['beta'][1:]
    return np.exp(-np.logaddexp(0,-score))


def _metrics(y,p,groups):
    np=_state()['np']
    w=_weights(groups,y)
    pos=float(w[y==1].sum());neg=float(w[y==0].sum())
    need(pos>0 and neg>0,'both out-of-fold target classes')
    order=np.argsort(p,kind='stable')
    negative_before=auc=0.0;i=0
    while i<len(order):
        j=i+1
        while j<len(order) and p[order[j]]==p[order[i]]:j+=1
        inds=order[i:j]
        a=float(w[inds][y[inds]==1].sum());b=float(w[inds][y[inds]==0].sum())
        auc+=a*(negative_before+b/2);negative_before+=b;i=j
    tpr=float(w[(y==1)&(p>=0.5)].sum())/pos
    tnr=float(w[(y==0)&(p<0.5)].sum())/neg
    clipped=np.clip(p,1e-15,1-1e-15)
    losses=-y*np.log(clipped)-(1-y)*np.log(1-clipped)
    bw=_weights(groups,y,balanced=True)
    return dict(auroc=auc/(pos*neg),balanced_accuracy=(tpr+tnr)/2,
        sensitivity=tpr,specificity=tnr,balanced_log_loss=float((bw*losses).sum()),
        brier=float((bw*(p-y)**2).sum()),rows=len(y),groups=len(set(groups)),
        positive_rows=int((y==1).sum()),negative_rows=int((y==0).sum()))


def _permuted_labels(seed,index):
    s=_state();y=s['labels']['frame_legal'].copy()
    rng=random.Random(int(seed)*1000003+int(index)*9176+7717)
    for groups in s['strata_groups'].values():
        shuffled=list(groups);rng.shuffle(shuffled)
        for target,source in zip(groups,shuffled):
            for slot,i in s['slots'][target].items():y[i]=s['labels']['frame_legal'][s['slots'][source][slot]]
    return y


def evaluate_task(spec):
    start=time.process_time();s=_state();np=s['np']
    seed=int(spec['seed']);target=spec.get('target','frame_legal');permutation=spec.get('permutation')
    need(target in ('frame_legal','worse'),'registered target')
    need(permutation is None or target=='frame_legal','permutations only for primary feasibility contrast')
    yall=s['labels'][target] if permutation is None else _permuted_labels(seed,permutation)
    eligible=np.flatnonzero(yall>=0); y=yall[eligible];x=s['x'][eligible]
    groups=[s['groups'][i] for i in eligible]
    unique=sorted(set(groups));random.Random(seed).shuffle(unique)
    group_fold={g:i%5 for i,g in enumerate(unique)}
    folds=np.asarray([group_fold[g] for g in groups])
    predictions={name:np.empty(len(y)) for name in ('proposal','full')}
    fold_reports=[]
    for fold in range(5):
        train=np.flatnonzero(folds!=fold);test=np.flatnonzero(folds==fold)
        need(len(train)>0 and len(test)>0,'nonempty fivefold partition')
        train_groups=[groups[i] for i in train]
        need(set(train_groups).isdisjoint(groups[i] for i in test),'no original contact pair crosses train/test')
        if len(set(y[train]))<2:
            return dict(status='UNASSESSABLE',seed=seed,target=target,permutation=permutation,
                reason='A grouped training fold lacks both classes; no fold repair or random-row fallback.',fold=fold,
                cpu_seconds=time.process_time()-start)
        details={}
        for name,columns in [('proposal',s['proposal']),('full',list(range(len(s['names']))))]:
            model=_fit(x[train][:,columns],y[train],train_groups)
            predictions[name][test]=_predict(model,x[test][:,columns])
            details[name]=dict(iterations=model['iterations'],objective=model['objective'])
        fold_reports.append(dict(fold=fold,train_groups=len(set(train_groups)),test_groups=len(set(groups[i] for i in test)),
            train_rows=len(train),test_rows=len(test),models=details))
    scores={name:_metrics(y,p,groups) for name,p in predictions.items()}
    result=dict(status='PASS_RETROSPECTIVE_MODEL',seed=seed,target=target,permutation=permutation,
        metrics=scores,delta_auroc=scores['full']['auroc']-scores['proposal']['auroc'],
        delta_balanced_log_loss=scores['proposal']['balanced_log_loss']-scores['full']['balanced_log_loss'],
        fold_reports=fold_reports,cpu_seconds=time.process_time()-start,
        scope='Pair-blocked same-source retrospective model; no independent-lineage, prospective, causal or kappa claim.')
    if permutation is None:
        final=_fit(x,y,groups)
        result['standardized_coefficients']={name:float(final['beta'][i+1]) for i,name in enumerate(s['names'])}
        result['intercept']=float(final['beta'][0])
        result['out_of_fold']=[dict(row_id=s['ids'][int(i)],pair_group=groups[j],fold=int(folds[j]),
            label=int(y[j]),proposal_probability=float(predictions['proposal'][j]),full_probability=float(predictions['full'][j]))
            for j,i in enumerate(eligible)]
    return result


def controls_task(seed):
    start=time.process_time();s=_state();np=s['np']
    y=np.asarray([0,0,1,1]);p=np.asarray([0.1,0.2,0.8,0.9]);groups=['a','b','c','d']
    metrics=_metrics(y,p,groups)
    need(metrics['auroc']==1 and metrics['balanced_accuracy']==1,'known exact ranking control')
    tied=_metrics(y,np.asarray([0.5]*4),groups)
    need(tied['auroc']==0.5 and tied['balanced_accuracy']==0.5,'tie and constant baseline control')
    toy_y=np.asarray([i%2 for i in range(100)]);toy_x=np.asarray([[2*(i%2)-1,(i//2)%3] for i in range(100)],dtype=float)
    toy_groups=['toy-'+str(i//2) for i in range(100)]
    model=_fit(toy_x,toy_y,toy_groups)
    need(_metrics(toy_y,_predict(model,toy_x),toy_groups)['auroc']==1,'learnable synthetic linear control')
    shuffled=_permuted_labels(seed,0)
    for gs in s['strata_groups'].values():
        for slot in s['slots'][gs[0]]:
            before=sorted(int(s['labels']['frame_legal'][s['slots'][g][slot]]) for g in gs)
            after=sorted(int(shuffled[s['slots'][g][slot]]) for g in gs)
            need(before==after,'permutation preserves template/provider slot marginals within stratum')
    forbidden=('moment','profile','status','failure','runtime','provider','seed','candidate_id','register_id','price','kappa')
    need(not any(any(token in name.lower() for token in forbidden) for name in s['names']),
         'feature-name leakage denylist')
    return dict(status='PASS',seed=int(seed),checks=['known_perfect_ranking','tied_auc_half','learnable_linear_fixture',
        'whole_group_template_marginals_preserved','no_forbidden_feature_names'],
        feature_count=len(s['names']),cpu_seconds=time.process_time()-start)
