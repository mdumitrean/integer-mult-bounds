"""Exploratory structure/gain analysis of authenticated improving releases.

Source-only until the coordinator freezes a preregistration. No import-time I/O
or numerical work. One release, rather than each provider, is one observation.
All reported labels are source-bound conditional claims, not fresh admission.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import json
import math
import re
import time

ALPHA = 1.0
PERMUTATIONS = 199
PROVIDERS = ('base', 'extra')
RELEASE_TIER = 'SOURCE_REPORTED_CONDITIONAL_COMPLETE_FINITE_RELEASE'
FORBIDDEN = re.compile(r'(^|_)(paid|profile|price|cost|moment|phi|kappa|gain|root|outcome|author|label|pr|id)(_|$)', re.I)
_STATE = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def _numpy():
    # Trusted installed dependency, never code acquired from a PR.
    import numpy as np
    return np


def _feature_contract(names):
    need(isinstance(names, (list, tuple)) and names, 'explicit structural delta feature whitelist')
    need(all(isinstance(name, str) and name for name in names), 'named structural features')
    need(len(set(names)) == len(names), 'unique feature whitelist')
    for name in names:
        need(FORBIDDEN.search(name) is None, 'forbidden outcome/identity/cost predictor: '+name)
    return tuple(sorted(names))


def _target(labels, parent_pr):
    """Missing/ambiguous comparator => censored, never CLAIM.gain substitution."""
    absent = ('kappa_before', 'kappa_after', 'matched_parent_gain')
    if parent_pr is None or any(labels.get(key) is None for key in absent):
        return None, 'missing exact structural-parent endpoint or matched-parent difference'
    if labels.get('structural_parent_match') is False or labels.get('comparator_ambiguous') is True:
        return None, 'explicit structural-parent/comparator ambiguity'
    if labels.get('matched_parent_pr') is not None and str(labels['matched_parent_pr']) != str(parent_pr):
        return None, 'label parent differs from structural feature parent'
    try:
        before, after, gain = (Q(str(labels[key])) for key in absent)
    except (ValueError, ZeroDivisionError, TypeError):
        return None, 'exact rational endpoint format unavailable'
    if after-before != gain:
        return None, 'matched-parent difference disagrees with exact endpoints'
    if gain <= 0:
        return None, 'not a strictly improving matched-parent release'
    if labels.get('tier') != RELEASE_TIER or labels.get('source_reported_only') is not True:
        return None, 'not the registered source-reported complete conditional release tier'
    if labels.get('structural_regression_eligible') is False:
        return None, 'source-declared mechanism is outside structural regression (for example certificate precision)'
    return dict(before=str(before), after=str(after), gain=str(gain),
        log10_gain=math.log10(gain.numerator)-math.log10(gain.denominator)), None


def _aggregate(rows, names):
    need(isinstance(rows, list) and rows, 'nonempty provider feature rows')
    grouped = {}
    for row in rows:
        release = row.get('release_id', row.get('pr'))
        need(release is not None, 'release identity is metadata, required for provider grouping')
        provider = row.get('provider')
        need(provider in PROVIDERS, 'registered base/extra provider')
        key = str(release)
        slot = grouped.setdefault(key, {})
        need(provider not in slot, 'one feature row per release/provider; seed duplicates removed upstream')
        slot[provider] = row
    releases = []
    for release in sorted(grouped):
        providers = grouped[release]
        missing = [provider for provider in PROVIDERS if provider not in providers]
        items = [providers[p] for p in PROVIDERS if p in providers]
        first = items[0]
        parent = first.get('parent_pr')
        parents = {str(row.get('parent_pr')) for row in items}
        need(len(parents) == 1, 'both providers have the same structural parent')
        mechanisms = {str(row.get('mechanism_group', 'UNSPECIFIED')) for row in items}
        need(len(mechanisms) == 1, 'provider-independent declared mechanism grouping')
        label_keys = ('kappa_before', 'kappa_after', 'matched_parent_gain', 'matched_parent_pr',
                      'structural_parent_match', 'comparator_ambiguous', 'tier',
                      'source_reported_only', 'structural_regression_eligible')
        labels = {key:first.get('labels', {}).get(key) for key in label_keys}
        for row in items[1:]:
            other = {key:row.get('labels', {}).get(key) for key in label_keys}
            need(labels == other, 'provider twins share one exact release label')
        reason = 'missing provider: '+','.join(missing) if missing else None
        feature_maps = [row.get('structural_features') for row in items]
        if any(features is None for features in feature_maps):
            reason = reason or 'missing complete structural feature vector'
        vector, asymmetry = None, None
        if reason is None:
            for features in feature_maps:
                need(set(features) == set(names), 'feature map matches explicit whitelist exactly')
                need(all(type(features[name]) in (int,float) and math.isfinite(features[name])
                         for name in names), 'finite numeric structural deltas')
            vector = [sum(float(features[name]) for features in feature_maps)/len(PROVIDERS)
                      for name in names]
            asymmetry = {name:float(feature_maps[0][name])-float(feature_maps[1][name])
                         for name in names if feature_maps[0][name] != feature_maps[1][name]}
        target, target_reason = _target(labels, parent)
        coverage = [deepcopy(row.get('predictor_coverage', {})) for row in items]
        mechanism_observed = all(item.get('regression_supported') is True and
                                 item.get('mechanism_complete') is True for item in coverage)
        if not mechanism_observed:
            target_reason = target_reason or 'structural covariates do not cover the declared improvement mechanism'
        if reason is not None:
            target_reason = reason
        releases.append(dict(release_id=release, parent_pr=parent,
            source_group=str(parent) if parent is not None else 'MISSING_PARENT',
            mechanism_group=next(iter(mechanisms)),
            lineage_groups=sorted({str(row.get('lineage_group', 'UNSPECIFIED')) for row in items}),
            features=vector, provider_feature_difference=asymmetry,
            structural_censor_reason=reason,
            predictor_coverage=coverage,
            provider_missingness=[deepcopy(row.get('missingness', [])) for row in items],
            target=target if target_reason is None else None,
            regression_censor_reason=target_reason,
            labels=deepcopy(first.get('labels', {})),
            provider_row_ids=[row.get('row_id') for row in items],
            source_attribution=[deepcopy(row.get('source_attribution', row.get('provenance', {})))
                                for row in items],
            feature_scope='Equal-weight mean of base/extra structural deltas; no provider pseudo-replication.'))
    return releases


def prepare(payload):
    """Once-parent preparation after registration; provider features are precomputed."""
    global _STATE
    need(_STATE is None, 'one release-model parent preparation')
    started = time.process_time()
    need(isinstance(payload, dict), 'prepare expects rows and explicit feature_names')
    names = _feature_contract(payload['feature_names'])
    rows = _aggregate(payload['rows'], names)
    np = _numpy()
    complete = [row for row in rows if row['features'] is not None]
    eligible = [row for row in complete if row['target'] is not None]
    X = np.asarray([row['features'] for row in eligible], dtype=float)
    if not eligible:
        X = np.empty((0, len(names)), dtype=float)
    y = np.asarray([row['target']['log10_gain'] for row in eligible], dtype=float)
    allX = np.asarray([row['features'] for row in complete], dtype=float)
    if not complete:
        allX = np.empty((0, len(names)), dtype=float)
    summary = dict(status='PASS_PREPARED_EXPLORATORY_RELEASE_COHORT',
        provider_rows=len(payload['rows']), release_rows=len(rows),
        complete_structural_releases=len(complete), regression_eligible_releases=len(eligible),
        censored=[dict(release_id=row['release_id'], reason=row['regression_censor_reason'])
                  for row in rows if row['regression_censor_reason'] is not None],
        feature_names=list(names), rows_sha256=digest(rows),
        source_groups=sorted({row['source_group'] for row in eligible}),
        mechanism_groups=sorted({row['mechanism_group'] for row in eligible}),
        source_attribution=payload.get('source_attribution'),
        cpu_seconds=time.process_time()-started,
        scope='Published improving releases only; cumulatively related ancestry. Continuous gain-size exploration, not an improvement classifier or causal estimate.')
    _STATE = dict(names=names, rows=rows, eligible=eligible, complete=complete,
                  X=X, y=y, allX=allX, summary=summary)
    return deepcopy(summary)


def _state():
    need(_STATE is not None, 'registered once-parent prepare required')
    return _STATE


def _fit(X, y):
    np = _numpy()
    need(X.ndim == 2 and len(X) == len(y) and len(y)>0, 'nonempty ridge training fold')
    mean = X.mean(axis=0)
    scale = X.std(axis=0, ddof=0)
    active = X.max(axis=0)>X.min(axis=0)
    scale[~active] = 0.0
    ymean = float(y.mean())
    beta = np.zeros(X.shape[1], dtype=float)
    if active.any():
        Z = (X[:, active]-mean[active])/scale[active]
        # Equivalent dual form avoids a large feature-by-feature solve at small n.
        beta[active] = Z.T@np.linalg.solve(Z@Z.T+ALPHA*np.eye(len(y)), y-ymean)
    return dict(mean=mean, scale=scale, active=active, beta=beta, intercept=ymean)


def _predict(model, X):
    np = _numpy()
    out = np.full(len(X), model['intercept'], dtype=float)
    active = model['active']
    if active.any():
        out += ((X[:,active]-model['mean'][active])/model['scale'][active])@model['beta'][active]
    return out


def _ranks(values):
    np = _numpy()
    values = np.asarray(values)
    order = np.argsort(values, kind='stable')
    ranks = np.empty(len(values), dtype=float)
    lo = 0
    while lo < len(order):
        hi = lo+1
        while hi<len(order) and values[order[hi]] == values[order[lo]]:
            hi += 1
        ranks[order[lo:hi]] = (lo+hi-1)/2
        lo = hi
    return ranks


def _rank_correlation(y, predictions):
    np = _numpy()
    a,b = _ranks(y), _ranks(predictions)
    a,b = a-a.mean(), b-b.mean()
    norm = float(np.linalg.norm(a)*np.linalg.norm(b))
    return None if norm == 0 else float(a@b/norm)


def _cv(X, y, groups, row_ids, with_details=True):
    np = _numpy()
    group_names = sorted(set(groups))
    if len(group_names)<2 or len(y)<3:
        return dict(status='UNIDENTIFIABLE_GROUPING', reason='Fewer than two groups or three eligible releases.',
                    groups=group_names, n=len(y))
    predictions = np.empty(len(y), dtype=float)
    baseline = np.empty(len(y), dtype=float)
    seen = np.zeros(len(y), dtype=int)
    folds = []
    betas = []
    for group in group_names:
        test = np.asarray([i for i,g in enumerate(groups) if g==group], dtype=int)
        train = np.asarray([i for i,g in enumerate(groups) if g!=group], dtype=int)
        need(len(train)>0 and len(test)>0, 'nonempty disjoint grouped train/test folds')
        model = _fit(X[train], y[train])
        predictions[test] = _predict(model, X[test])
        baseline[test] = model['intercept']
        seen[test] += 1
        betas.append(model['beta'].tolist())
        if with_details:
            folds.append(dict(group=group, train_ids=[row_ids[i] for i in train],
                test_ids=[row_ids[i] for i in test], train_n=len(train), test_n=len(test),
                train_mean=model['mean'].tolist(), train_scale=model['scale'].tolist(),
                train_constant_features=[int(i) for i in np.flatnonzero(~model['active'])],
                standardized_coefficients=model['beta'].tolist(), train_y_mean=model['intercept']))
    need(bool(np.all(seen==1)), 'every release held out exactly once')
    ridge_mse = float(np.mean((y-predictions)**2))
    baseline_mse = float(np.mean((y-baseline)**2))
    result = dict(status='PASS_GROUPED_OOF', n=len(y), groups=group_names,
        baseline_mse=baseline_mse, ridge_mse=ridge_mse,
        primary_statistic=baseline_mse-ridge_mse,
        primary_statistic_definition='Mean training-mean baseline squared log10-gain error minus ridge squared log10-gain error; positive favors ridge.',
        spearman_gain_order=_rank_correlation(y,predictions),
        oof_coverage_exact=True)
    if with_details:
        result.update(folds=folds,
            predictions=[dict(release_id=row_ids[i], observed_log10_gain=float(y[i]),
                predicted_log10_gain=float(predictions[i]), baseline_log10_gain=float(baseline[i]))
                for i in range(len(y))],
            fold_coefficients=betas)
    return result


def _unsupervised(X, row_ids, names):
    np = _numpy()
    if len(X)<2:
        return dict(status='UNIDENTIFIABLE_STRUCTURE', reason='Fewer than two complete releases.')
    mean, scale = X.mean(axis=0), X.std(axis=0,ddof=0)
    active = X.max(axis=0)>X.min(axis=0)
    scale[~active] = 0.0
    if not active.any():
        return dict(status='NO_STRUCTURAL_VARIATION', n=len(X), constant_features=list(names))
    Z = (X[:,active]-mean[active])/scale[active]
    U, singular, Vt = np.linalg.svd(Z, full_matrices=False)
    axes = min(2,len(singular))
    scores = U[:,:axes]*singular[:axes]
    loadings = Vt[:axes].copy()
    for j in range(axes):
        pivot = int(np.argmax(np.abs(loadings[j])))
        if loadings[j,pivot]<0:
            loadings[j] *= -1; scores[:,j] *= -1
    total = float(np.sum(singular**2))
    # Deterministic Ward agglomeration on all standardized structural dimensions.
    clusters = {i:[i] for i in range(len(X))}
    centers = {i:Z[i].copy() for i in range(len(X))}
    sizes = {i:1 for i in range(len(X))}
    wanted = min(3,len(X))
    merges, next_id = [], len(X)
    while len(clusters)>wanted:
        best = None
        keys = sorted(clusters)
        for pos,a in enumerate(keys):
            for b in keys[pos+1:]:
                distance = float(sizes[a]*sizes[b]/(sizes[a]+sizes[b])*np.sum((centers[a]-centers[b])**2))
                key = (distance,tuple(clusters[a]),tuple(clusters[b]),a,b)
                if best is None or key<best:
                    best=key
        distance,_ca,_cb,a,b = best
        members = sorted(clusters[a]+clusters[b])
        centers[next_id]=(sizes[a]*centers[a]+sizes[b]*centers[b])/(sizes[a]+sizes[b])
        sizes[next_id]=sizes[a]+sizes[b]
        clusters[next_id]=members
        merges.append(dict(left=[row_ids[i] for i in clusters[a]],
                           right=[row_ids[i] for i in clusters[b]], ward_increase=distance))
        for key in (a,b):
            del clusters[key]; del centers[key]; del sizes[key]
        next_id += 1
    active_names = [name for name,on in zip(names,active) if on]
    return dict(status='PASS_DESCRIPTIVE_PCA_WARD', n=len(X),
        standardization_scope='All complete structural release observations; descriptive only, never reused for CV.',
        means=mean.tolist(), scales=scale.tolist(),
        active_features=active_names, constant_features=[name for name,on in zip(names,active) if not on],
        principal_components=[dict(axis=j+1, explained_variance_fraction=float(singular[j]**2/total),
            loadings=dict(zip(active_names,map(float,loadings[j])))) for j in range(axes)],
        scores=[dict(release_id=row_ids[i],coordinates=scores[i].tolist()) for i in range(len(X))],
        clusters=[dict(cluster=j+1,releases=[row_ids[i] for i in members])
                  for j,members in enumerate(sorted(clusters.values()))],
        ward_merges=merges, fixed_clusters=wanted,
        interpretation='A graph of structural similarities, not discovered physical toppling classes or proof of causal mechanisms.')


def run_task(spec):
    """One observed or indexed-permutation pool task; no internal task loop."""
    started = time.process_time()
    s = _state(); np = _numpy()
    need(isinstance(spec,dict), 'small registered pool task specification')
    seed = int(spec['seed'])
    index = spec.get('permutation')
    need(index is None or (type(index) is int and 0<=index<PERMUTATIONS),
         'observed task or registered permutation index0..198')
    X,y = s['X'],s['y']
    row_ids = [row['release_id'] for row in s['eligible']]
    if index is not None:
        generator = np.random.default_rng(np.random.SeedSequence([seed,index]))
        order = generator.permutation(len(y))
        permuted = y[order]
        reports = {}
        for scheme,key in (('immediate_source','source_group'),('declared_mechanism','mechanism_group')):
            groups = [row[key] for row in s['eligible']]
            reports[scheme] = _cv(X,permuted,groups,row_ids,False)
        return dict(status='PASS_EXPLORATORY_PERMUTATION', seed=seed, permutation=index,
            row_ids=row_ids, rows_sha256=s['summary']['rows_sha256'],
            label_permutation=order.tolist(), grouped_validation=reports,
            full_training_pipeline_refitted=True, label_only=True,
            cpu_seconds=time.process_time()-started,
            scope='Descriptive calibration only; related selected releases do not establish label exchangeability. No hypothesis promotion from a permutation fraction.')
    reports = {}
    for scheme,key in (('immediate_source','source_group'),('declared_mechanism','mechanism_group')):
        groups = [row[key] for row in s['eligible']]
        report = _cv(X,y,groups,row_ids)
        if report['status']=='PASS_GROUPED_OOF':
            coefficients = np.asarray(report['fold_coefficients'])
            report['coefficient_instability'] = [dict(feature=name,
                fold_min=float(coefficients[:,j].min()),fold_max=float(coefficients[:,j].max()),
                positive_folds=int(np.sum(coefficients[:,j]>0)),negative_folds=int(np.sum(coefficients[:,j]<0)),
                zero_folds=int(np.sum(coefficients[:,j]==0))) for j,name in enumerate(s['names'])]
        reports[scheme] = report
    full = None
    if len(y):
        model = _fit(X,y)
        full=dict(intercept=model['intercept'],
            standardized_coefficients=dict(zip(s['names'],map(float,model['beta']))),
            scope='Descriptive all-row fit; never evaluated on its own training predictions as evidence.')
    return dict(status='PASS_EXPLORATORY_RELEASE_ANALYSIS',seed=seed,permutation=None,
        method=dict(alpha=ALPHA,target='log10 exact positive matched-parent conditional kappa difference',
            permutations=PERMUTATIONS,adaptive_tuning=False,provider_aggregation='one release; mean of base and extra structural deltas'),
        prepared_summary=deepcopy(s['summary']), release_rows=deepcopy(s['rows']),
        grouped_validation=reports, descriptive_full_fit=full,
        descriptive_structure=_unsupervised(s['allX'],[row['release_id'] for row in s['complete']],s['names']),
        gain_classifier=None, matched_failed_release_controls_used=False,
        failed_controls_scope='Existing scalar frame proposals are not commensurable release observations and are not attached as negative gain labels.',
        no_causal_or_generalization_claim=True, hypothesis_promotion_allowed=False,
        cpu_seconds=time.process_time()-started,
        scope='Exploratory positive-gain magnitude and structural-similarity analysis of the fixed acquired corpus. No construction, native replay, admission or kappa improvement follows from model output.')


def controls_task(seed):
    started = time.process_time(); _state(); np = _numpy()
    analytic=_fit(np.asarray([[-1.],[1.]]),np.asarray([-1.,1.]))
    need(abs(float(analytic['beta'][0])-2/3)<1e-12 and analytic['intercept']==0.0,
         'two-point exact ridge alpha1 normalization: beta=2/3')
    X=np.asarray([[0.,2.,5.],[2.,2.,5.],[4.,2.,5.]])
    y=np.asarray([0.,1.,2.])
    model=_fit(X,y)
    need(model['mean'].tolist()==[2.,2.,5.] and model['active'].tolist()==[True,False,False],
         'training-only standardization and constant-column removal')
    a=_predict(model,np.asarray([[100.,999.,5.]]))
    b=_predict(model,np.asarray([[100.,-999.,5.]]))
    need(a.tolist()==b.tolist(), 'held-out values cannot activate a training-constant feature')
    constant=_fit(np.full((4,2),0.1),np.asarray([1.,2.,3.,4.]))
    need(not bool(constant['active'].any()) and
         _predict(constant,np.ones((2,2))).tolist()==[2.5,2.5], 'nonbinary-float constant-feature intercept baseline')
    tx=np.asarray([[0.,0.],[1.,0.],[2.,1.],[3.,1.],[4.,2.],[5.,2.]])
    ty=np.asarray([0.,1.,1.,2.,2.,3.]); before=ty.copy()
    cv=_cv(tx,ty,['a','a','b','b','c','c'],list('abcdef'))
    need(cv['oof_coverage_exact'] and bool(np.array_equal(ty,before)), 'grouped coverage and label immutability')
    need(all(set(fold['train_ids']).isdisjoint(fold['test_ids']) for fold in cv['folds']), 'no group train/test overlap')
    need(_cv(tx,ty,['same']*6,list('abcdef'))['status']=='UNIDENTIFIABLE_GROUPING', 'no silent row-CV fallback')
    labels=dict(kappa_before='1/1000',kappa_after='11/10000',matched_parent_gain='1/10000',
                tier=RELEASE_TIER,source_reported_only=True)
    target,reason=_target(labels,1)
    need(target is not None and reason is None, 'matched-parent exact label positive fixture')
    censored={}
    for name,change in (
        ('wrong_parent',{'matched_parent_pr':2}),
        ('wrong_gain',{'matched_parent_gain':'1/1000'}),
        ('ambiguous_comparator',{'comparator_ambiguous':True}),
        ('local_only',{'tier':'LOCAL_ONLY'}),
        ('missing_endpoint',{'kappa_before':None}),
        ('precision_only',{'structural_regression_eligible':False})):
        changed=dict(labels,**change)
        t,r=_target(changed,1)
        need(t is None and r is not None, 'censor invalid target: '+name)
        censored[name]=r
    rejected=[]
    for name in ('paid_profile_h1','exact_cost','gain','root_value','author_id'):
        try:
            _feature_contract([name])
        except ValueError:
            rejected.append(name)
    need(len(rejected)==5,'forbidden predictor rejection')
    providers=[dict(pr=10,parent_pr=1,provider=p,row_id=p,mechanism_group='fixture',
        structural_features={'delta_contacts':v},labels=labels,
        predictor_coverage={'regression_supported':True,'mechanism_complete':True}) for p,v in (('base',1),('extra',3))]
    aggregated=_aggregate(providers,('delta_contacts',))
    need(len(aggregated)==1 and aggregated[0]['features']==[2.] and aggregated[0]['target'] is not None,
         'provider twins collapse to one equally weighted release')
    unsupported=deepcopy(providers)
    for row in unsupported:
        row['predictor_coverage']['regression_supported']=False
    censored_release=_aggregate(unsupported,('delta_contacts',))[0]
    need(censored_release['features']==[2.] and censored_release['target'] is None,
         'unobserved mechanism retained descriptively but censored from regression')
    duplicate=False
    try:
        _aggregate(providers+[deepcopy(providers[0])],('delta_contacts',))
    except ValueError:
        duplicate=True
    need(duplicate,'duplicate provider cannot increase sample size')
    return dict(status='PASS',seed=int(seed),
        analytic_ridge_normalization='beta=2/3, intercept=0',
        train_only_scaling=True, constant_feature_control=True,grouped_coverage=True,
        target_censor_controls=censored,forbidden_predictors_rejected=rejected,
        provider_pseudoreplication_rejected=True,synthetic_only=True,
        cpu_seconds=time.process_time()-started,
        scope='Synthetic ML/accounting safeguards, not new candidate or release observations.')
