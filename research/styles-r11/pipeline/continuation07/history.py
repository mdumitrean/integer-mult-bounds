"""Descriptive, source-reported PR2979 lowering-price cohort.

No import-time I/O or science, no acquired-code execution, no statistical fit.
The coordinator calls prepare only after preregistration and launches the two
task functions through the shared pool. Features use requested endpoints and
the original parent restore graph; optimized frames/prices are not features.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from fractions import Fraction as Q
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time

RR = Path(__file__).resolve().parents[2]
PACKAGE = RR/'data/continuation-05/pr2979/package'
HEAD = 'be191346391661f4d35fc0d1508d0a6029572576'
TIER = 'SOURCE_REPORTED_INTEGER_SURROGATE_PRICE'
PINS = {
    'construction/STAGE-PRICES.json': 'dfb7d06724bf95367f3fdb398f4828fc70f803d23030bc0eee0b00541457f546',
    'data/PARENT-base.json.gz': '54ca34c749e3228d7e2df3d8dbf7aa1568c2872490166997c5962f12fd03da35',
    'data/PARENT-extra.json.gz': 'eded756dfe8f411c3d1f80a3ac16516f0ea5dd6f9866728b2179b157630fa7b6',
    'construction/records/make_prices.py.txt': '5fcf593b5672b4f66cabd9d2bd5b4e843453248186d95794386331d801280b78',
    'CLAIM.json': '436e0d297cbdf195445d3697d496ac675e95210b79e70ce602a6a6667a4c6ce9',
    'CREDITS.md': 'bf85777bd2d9b8e537dae2e70614759ba1a265101dd903a72fbd2cfc2869c406',
    'NOTICE': 'b767e40e8c7e16058d1ebb8c08eef9b9bffae31cfa30512b843ae1fcbfc6f5cd',
    'SOURCES.json': 'd5f3f498d4d34125bcaed14dafaceaff342223d511d1099993d5b217a147019c',
    'PINS.json': '978b20708cabb86cc379e42ca04f45b9251d60a5241c3d70092288f42051cc68',
}
ORIGINAL_PINS_SHA = '4d62f7caf94a102ebb83feb3beca6ebeb1ab9637901ff51cc84e5beeb15d2a65'
_STATE = None


def need(test, message):
    if not test:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _read(name):
    raw = (PACKAGE/name).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PINS[name], 'pinned historical source: '+name)
    if name.endswith('.gz'):
        return json.loads(gzip.decompress(raw))
    if name.endswith('.json'):
        return json.loads(raw)
    return raw.decode()


def _basis(vectors):
    """Canonical GF(2) reduced basis on the fixed nine-dimensional ambient."""
    rows = {}
    for raw in vectors:
        need(type(raw) is int and 0 < raw < 512, 'nonzero nine-bit frame vector')
        value = raw
        for pivot in sorted(rows, reverse=True):
            if value & (1 << pivot):
                value ^= rows[pivot]
        if not value:
            continue
        pivot = value.bit_length()-1
        for old in tuple(rows):
            if rows[old] & (1 << pivot):
                rows[old] ^= value
        rows[pivot] = value
    return tuple(rows[p] for p in sorted(rows, reverse=True))


def _requested(assignment):
    return tuple(sorted((int(h), _basis(frame)) for h,frame in assignment.items()))


def _regs(gate):
    need(gate[0] in ('add', 'scale'), 'parent restore contains only framed scalar gates')
    return tuple(gate[1:3]) if gate[0] == 'add' else (gate[1],)


def _geometry(word, request):
    selected = {h for h,_ in request}
    ends = []
    for helper, target in request:
        need(str(helper) in word['helper_final'], 'requested restored parent endpoint')
        old = _basis(word['helper_final'][str(helper)])
        need(len(_basis(old+target)) == len(old), 'requested endpoint is a parent subspace')
        ends.append([helper, list(old), list(target)])
    contacts = []
    for index,gate in enumerate(word['restore']):
        regs = _regs(gate)
        if selected.intersection(regs):
            need(isinstance(gate[-1], list), 'literal parent restore frame')
            contacts.append(dict(index=index, gate=gate[:-1], regs=list(regs),
                                 frame=list(_basis(gate[-1]))))
    return dict(endpoints=ends, contacts=contacts)


def _features(geometry):
    targets = {h:tuple(target) for h,_old,target in geometry['endpoints']}
    selected = set(targets)
    neighbors = defaultdict(set)
    graph = {h:set() for h in selected}
    contacts, ranks, losses = geometry['contacts'], [], []
    internal = boundary = scales = touches = 0
    for item in contacts:
        regs, frame = set(item['regs']), tuple(item['frame'])
        involved = regs & selected
        touches += len(involved)
        ranks.append(len(frame))
        for h in involved:
            # dim(F)-dim(F intersect W) = dim(F+W)-dim(W).
            losses.append(len(_basis(frame+targets[h]))-len(targets[h]))
        if item['gate'][0] == 'scale':
            scales += 1
        elif len(involved) == 2:
            internal += 1
            a,b = sorted(involved)
            graph[a].add(b); graph[b].add(a)
        else:
            boundary += 1
            for other in regs-selected:
                neighbors[other].update(involved)
    for seen in neighbors.values():
        for h in seen:
            graph[h].update(seen-{h})
    remaining, components = set(selected), 0
    while remaining:
        todo = [min(remaining)]
        remaining.remove(todo[0])
        components += 1
        while todo:
            for other in graph[todo.pop()] & remaining:
                remaining.remove(other); todo.append(other)
    endpoint_before = sum(len(old) for _h,old,_target in geometry['endpoints'])
    endpoint_after = sum(len(target) for target in targets.values())
    return dict(n_helpers=len(selected), n_target_frames=len(set(targets.values())),
        endpoint_rank_before=endpoint_before, endpoint_rank_drop=endpoint_before-endpoint_after,
        target_rank_min=min(map(len,targets.values())), target_rank_max=max(map(len,targets.values())),
        restore_contact_gates=len(contacts), restore_selected_touches=touches,
        restore_internal_adds=internal, restore_boundary_adds=boundary,
        restore_selected_scales=scales, restore_external_neighbors=len(neighbors),
        restore_shared_carriers=sum(len(seen)>=2 for seen in neighbors.values()),
        restore_overlap_excess=sum(max(0,len(seen)-1) for seen in neighbors.values()),
        restore_selected_components=components,
        restore_contact_rank_sum=sum(ranks), restore_contact_rank_min=min(ranks,default=0),
        restore_contact_rank_max=max(ranks,default=0),
        restore_requested_rank_loss_sum=sum(losses),
        restore_requested_rank_loss_nonzero=sum(x>0 for x in losses),
        restore_support_span=(contacts[-1]['index']-contacts[0]['index']+1 if contacts else 0))


def _check_label(row, break_even):
    label = row['labels']
    need(label['tier'] == TIER and label['admitted_kappa'] is None,
         'individual search price is not an admitted kappa label')
    need(type(label['delta_units']) is int and type(label['margin_units']) is int,
         'exact integer surrogate labels')
    need(label['margin_units'] == -label['delta_units']-len(row['requested'])*break_even,
         'source margin equals minus delta minus endpoint break-even charge')
    need(label['guide_positive'] == (label['margin_units']>0), 'guide-margin sign label')


def _insert(table, assignment, margin, delta, break_even, origin, provider, groups):
    request = _requested(assignment)
    key = digest([[h,list(frame)] for h,frame in request])
    need(type(margin) is int, 'stored source integer margin')
    inferred = delta is None
    if inferred:
        delta = -margin-len(request)*break_even
    row = dict(row_id=key, episode_id='PR2942-parent/PR2979-stage1-lowerings',
        requested=[[h,list(frame)] for h,frame in request],
        labels=dict(tier=TIER, delta_units=delta, margin_units=margin,
                    guide_positive=margin>0, admitted_kappa=None),
        origins=[origin], source_provider_reports=[provider],
        group_names=sorted(groups), delta_reconstructed_from_margin=inferred)
    _check_label(row,break_even)
    if key in table:
        old = table[key]
        need(old['requested'] == row['requested'] and old['labels'] == row['labels'],
             'duplicate requested assignment has identical exact source labels')
        old['origins'].append(origin)
        old['source_provider_reports'] = sorted(set(old['source_provider_reports']+[provider]))
        old['group_names'] = sorted(set(old['group_names'])|set(groups))
        old['delta_reconstructed_from_margin'] &= inferred
    else:
        table[key] = row
    return key


def _build_rows(prices, words):
    stage, break_even = prices['stage1'], prices['weights']['break_even']
    table, group_defs, group_rows, singles, v45_rows = {}, {}, {}, {}, []
    raw_occurrences = 0

    def insert(assignment, margin, delta, origin, provider='source-unspecified', groups=()):
        nonlocal raw_occurrences
        raw_occurrences += 1
        return _insert(table,assignment,margin,delta,break_even,origin,provider,groups)

    for group in stage['groups']:
        name, target, helpers = group['group'], group['W'], group['helpers']
        key = _basis(target)
        need(key not in group_defs, 'distinct same-W source groups')
        group_defs[key] = dict(name=name, helpers=set(helpers), target=target)
        provider = 'base' if name == 'V45' else 'source-unspecified'
        for helper in helpers:
            rid = insert({helper:target},group['singles_margin'][str(helper)],None,
                         'stage1/groups/'+name+'/singles/'+str(helper),provider,(name,))
            singles[helper] = rid
        group_rows[name] = insert(dict.fromkeys(helpers,target),group['joint_margin'],
            group['joint_delta'],'stage1/groups/'+name+'/joint',provider,(name,))
        for index,item in enumerate(group.get('subsets',[])):
            need(name == 'V45', 'only documented V45 full subset lattice')
            rid = insert(dict.fromkeys(item['helpers'],target),item['margin'],item['delta'],
                         'stage1/groups/V45/subsets/'+str(index),'base',('V45',))
            v45_rows.append(rid)
    for index,item in enumerate(stage['unused_single_W_groups']):
        need(len(item['helpers']) == 1, 'reported unused singleton group')
        helper, target = item['helpers'][0], item['W']
        name = 'unused-'+str(helper)
        group_defs[_basis(target)] = dict(name=name,helpers={helper},target=target)
        rid = insert({helper:target},item['margin'],None,
                     'stage1/unused_single_W_groups/'+str(index),groups=(name,))
        group_rows[name] = rid
        singles[helper] = rid
    unions = []
    for index,item in enumerate(stage['pairwise_unions']):
        defs = [group_defs[_basis(frame)] for frame in item['Ws']]
        need(len(defs) == 2 and defs[0]['helpers'].isdisjoint(defs[1]['helpers']),
             'source cross-W union has disjoint helper sets')
        assignment = {h:g['target'] for g in defs for h in g['helpers']}
        need(set(assignment) == set(item['helpers']), 'literal union helper coverage')
        names = tuple(g['name'] for g in defs)
        rid = insert(assignment,item['joint_margin'],item['joint_delta'],
                     'stage1/pairwise_unions/'+str(index),groups=names)
        unions.append(dict(row_id=rid, component_row_ids=[group_rows[n] for n in names]))

    need(raw_occurrences == 59 and len(table) == 54 and len(singles) == 24,
         'fixed source occurrence and deduplicated inventory')
    for row in table.values():
        request = _requested(dict(row['requested']))
        base = _geometry(words['base'],request)
        extra = _geometry(words['extra'],request)
        same = base == extra
        explicit_base = 'base' in row['source_provider_reports']
        row['provider_scope'] = ('base-source-explicit' if explicit_base else
            'source-unspecified/identical-parent-restore-geometry' if same else
            'source-unspecified/structural-features-censored')
        row['parent_restore_geometry_equal'] = same
        row['parent_geometry_sha256'] = dict(base=digest(base),extra=digest(extra))
        row['features'] = _features(base) if explicit_base or same else None
        row['feature_scope'] = 'Requested endpoint assignment and original restore contacts only; no optimized frame edits, output profile, price, group name or helper identifier is a predictor.'
        row['origins'].sort()
        _check_label(row,break_even)
    rows = [table[key] for key in sorted(table)]
    return dict(rows=rows, table=table, group_rows=group_rows, singles=singles,
                v45_rows=v45_rows, unions=unions, raw_occurrences=raw_occurrences)


def _state():
    need(_STATE is not None, 'registered parent prepare required')
    return _STATE


def prepare():
    """Once-parent extraction, after registration, with no fresh pricing/model."""
    global _STATE
    started = time.process_time()
    need(_STATE is None, 'one historical source preparation')
    data = {name:_read(name) for name in PINS}
    raw_pins = (RR/'data/words/PINS.json').read_bytes()
    need(hashlib.sha256(raw_pins).hexdigest() == ORIGINAL_PINS_SHA, 'original word attribution pin')
    prices = data['construction/STAGE-PRICES.json']
    need(prices['weights']['break_even'] == 2091300 and
         Q(prices['weights']['b']) == Q('0.001703676387993676'), 'source cost convention')
    words = {name:data['data/PARENT-'+name+'.json.gz'] for name in ('base','extra')}
    cohort = _build_rows(prices,words)
    attribution = dict(pr=2979, head=HEAD, author='Marius-Paul Dumitrean (mdumitrean)',
        parent='PR2942 words, both source-pinned providers',
        original_words_PINS=json.loads(raw_pins),
        credits={name:data[name] for name in ('CREDITS.md','NOTICE','SOURCES.json','PINS.json')},
        construction_price_source='construction/STAGE-PRICES.json',
        producer_text_only='construction/records/make_prices.py.txt; never imported or executed')
    names = sorted({key for row in cohort['rows'] if row['features'] is not None
                    for key in row['features']})
    summary = dict(status='PASS_PREPARED_DESCRIPTIVE_SOURCE', parent_loaded_once=True,
        source_occurrences=cohort['raw_occurrences'], distinct_assignments=len(cohort['rows']),
        singleton_assignments=len(cohort['singles']), same_W_joint_groups=5,
        V45_lattice_assignments=len(cohort['v45_rows']), cross_W_union_rows=len(cohort['unions']),
        feature_names=names,
        structural_features_censored=sum(row['features'] is None for row in cohort['rows']),
        rows_sha256=digest(cohort['rows']), source_pins=PINS,
        source_attribution=attribution, cpu_seconds=time.process_time()-started,
        scope='One parent lineage; source-reported surrogate prices only. No fit, generalization or fresh operator/native/admission claim.')
    _STATE = dict(prices=prices, words=words, cohort=cohort, attribution=attribution,
                  summary=summary, claim=data['CLAIM.json'])
    return deepcopy(summary)


def get_rows():
    return deepcopy(_state()['cohort']['rows'])


def _interaction(joint, singles, break_even):
    for row in [joint]+singles:
        _check_label(row,break_even)
    need({h for row in singles for h,_ in row['requested']} ==
         {h for h,_ in joint['requested']} and all(len(r['requested'])==1 for r in singles),
         'complete unique singleton comparison')
    need(len(singles) == len(joint['requested']), 'one singleton per requested helper')
    jm = joint['labels']['margin_units']
    sm = sum(row['labels']['margin_units'] for row in singles)
    delta_form = sum(row['labels']['delta_units'] for row in singles)-joint['labels']['delta_units']
    need(jm-sm == delta_form, 'break-even cancellation in joint interaction')
    return dict(joint_margin_units=jm, sum_single_margin_units=sm,
        interaction_units=jm-sm, independent_delta_form=delta_form,
        break_even_cancels_exactly=True,
        interpretation='Positive means reported joint savings exceed the sum of reported single savings; this is a same-parent surrogate-cost contrast, not admitted kappa.')


def analysis_task(seed):
    started = time.process_time()
    s = _state(); c = s['cohort']; be = s['prices']['weights']['break_even']
    rows = get_rows()
    for row in rows:
        _check_label(row,be)
    interactions = []
    for group in s['prices']['stage1']['groups']:
        joint = c['table'][c['group_rows'][group['group']]]
        singles = [c['table'][c['singles'][h]] for h in group['helpers']]
        interactions.append(dict(group=group['group'], row_id=joint['row_id'],
            single_row_ids=[r['row_id'] for r in singles],
            **_interaction(joint,singles,be)))
    lattice = [c['table'][rid] for rid in c['v45_rows']]
    helpers = sorted(next(g['helpers'] for g in s['prices']['stage1']['groups'] if g['group']=='V45'))
    expected = {tuple(combo) for k in range(1,len(helpers)+1)
                for combo in itertools.combinations(helpers,k)}
    need({tuple(h for h,_ in row['requested']) for row in lattice} == expected,
         'all15 nonempty V45 subsets represented exactly once')
    lattice = sorted(lattice,key=lambda row:(len(row['requested']),row['requested']))
    additive = []
    for item in c['unions']:
        joint = c['table'][item['row_id']]
        parts = [c['table'][rid] for rid in item['component_row_ids']]
        d = joint['labels']['delta_units']-sum(x['labels']['delta_units'] for x in parts)
        m = joint['labels']['margin_units']-sum(x['labels']['margin_units'] for x in parts)
        need(d == -m, 'cross-group complete linear break-even cancellation')
        additive.append(dict(**item, delta_additivity_residual=d,
            margin_additivity_residual=m, additive=(d==0)))
    claim = s['claim']
    composed = dict(tier='AUTHENTICATED_SOURCE_REPORTED_COMPOSED_CONDITIONAL_RELEASE',
        pr=2979, source_status=claim['status'], complex_lower=claim['complex_lower'],
        kappa=claim['kappa'], native_receipt_sha256=claim['native_receipt_sha256'],
        release_receipt_sha256=claim['release_receipt_sha256'],
        label_scope='Only the final composed words plus actual allocation and supplier/outer release have this source-reported conditional claim; it is not assigned to individual Stage1 rows.',
        fresh_native_or_outer_replay=False)
    return dict(status='PASS_DESCRIPTIVE_SOURCE_ANALYSIS', seed=int(seed), rows=rows,
        rows_sha256=digest(rows), source_occurrences=c['raw_occurrences'],
        deduplicated_assignments=len(rows), duplicate_occurrences_collapsed=c['raw_occurrences']-len(rows),
        same_W_interactions=interactions,
        V45_subset_lattice=[dict(row_id=r['row_id'],helpers=[h for h,_ in r['requested']],
            **r['labels']) for r in lattice], V45_subset_lattice_complete=True,
        cross_W_additivity_controls=additive,
        all_cross_W_unions_additive=all(x['additive'] for x in additive),
        cost_convention=deepcopy(s['prices']['weights']),
        other_stage_prices=dict(stage2=dict(tier=TIER,source_report=deepcopy(s['prices']['stage2'])),
            stage3=dict(tier=TIER,source_report=deepcopy(s['prices']['stage3'])),
            total=dict(tier=TIER,source_report=deepcopy(s['prices']['total']))),
        separate_admission_tier=composed, source_pins=PINS, source_attribution=s['attribution'],
        statistical_inference=False, independent_parent_lineages=1,
        source_notes=dict(price_evidence=s['prices']['note'],
            missing_individual_frame_certificates='Per-single optimized frame assignments are not supplied by this price table; exact causal attribution to a particular restore gate is not established.',
            leave_one_out='Reported range only; no synthetic per-helper rows are invented.',
            synthetic_admission_controls='Validator mutants are not natural unsuccessful candidates and are excluded from this historical cohort.'),
        cpu_seconds=time.process_time()-started,
        scope='Read-only arithmetic over pinned source-reported prices and pre-price parent-restore geometry. No rerun, optimizer, significance test, statistical fit, cross-lineage validation or admitted kappa prediction.')


def controls_task(seed):
    started = time.process_time()
    _state()
    # Synthetic exact prices exercise the accounting independently of source labels.
    be, table = 13, {}
    first = _insert(table,{1:[1]},-10,-3,be,'first','base',())
    again = _insert(table,{1:[1]},-10,None,be,'duplicate','base',())
    second = _insert(table,{2:[1]},-20,7,be,'second','base',())
    joint = _insert(table,{1:[1],2:[1]},5,-31,be,'joint','base',())
    need(first==again and len(table)==3 and len(table[first]['origins'])==2,
         'duplicate collapse preserves one assignment and both evidence origins')
    interaction = _interaction(table[joint],[table[first],table[second]],be)
    need(interaction['interaction_units']==35, 'synthetic shared-price positive control')
    shifted = deepcopy(table)
    for row in shifted.values():
        row['labels']['margin_units'] = -row['labels']['delta_units']-len(row['requested'])*17
        row['labels']['guide_positive'] = row['labels']['margin_units']>0
    need(_interaction(shifted[joint],[shifted[first],shifted[second]],17)['interaction_units']==35,
         'changing break-even changes margins but not interaction')
    checks = {}
    bad = deepcopy(table[first]);bad['labels']['margin_units']+=1
    tests = {'wrong_margin':lambda:_check_label(bad,be)}
    tier = deepcopy(table[first]);tier['labels']['tier']='ADMITTED_KAPPA'
    tests['wrong_admission_tier']=lambda:_check_label(tier,be)
    gain = deepcopy(table[first]);gain['labels']['admitted_kappa']='1/1000'
    tests['invented_kappa_label']=lambda:_check_label(gain,be)
    tests['conflicting_duplicate']=lambda:_insert(deepcopy(table),{1:[1]},-9,-4,be,'bad','base',())
    for name,call in tests.items():
        try:
            call()
        except ValueError as error:
            checks[name]=dict(rejected=True,reason=str(error))
        else:
            checks[name]=dict(rejected=False)
    need(all(item['rejected'] for item in checks.values()), 'historical accounting mutants reject')
    need(_basis([3,2])==_basis([1,2]) and len(_basis([1,2,3]))==2,
         'GF2 basis orientation/redundancy controls')
    return dict(status='PASS',seed=int(seed),controls=checks,
        duplicate_collapse=True, break_even_invariant_interaction=35,
        source_pins=PINS,source_attribution=_state()['attribution'],
        cpu_seconds=time.process_time()-started,
        scope='Synthetic accounting and label-tier controls only; no fresh candidate or model result.')
