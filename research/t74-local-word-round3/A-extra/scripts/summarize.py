"""Assemble RESULTS.json for agent A-extra from the evidence files in out/.  usage: summarize.py AGENT_DIR ROUND_DIR"""
import json, sys, glob, os, collections, hashlib
A, R = sys.argv[1:3]; O = A + '/out'
rd = lambda p: json.load(open(p))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
out = dict(agent='A-extra', round='r3', status=None,
           words=dict(extra=dict(path='inputs/extra-word-566-554.json.gz', sha256=sha(R + '/inputs/extra-word-566-554.json.gz')),
                      base=dict(path='inputs/gauge44-word-566-554.json.gz', sha256=sha(R + '/inputs/gauge44-word-566-554.json.gz'))),
           word_diff='identical gates in A, cut, B, early_cleanup and cleanup; 12 B gates (B397-B408) differ only in frames; start_extra of 627/629/630/631 lacks the 390 level in the extra word (rank 4 vs 5); local rank mass 5594 vs 5590')
out['b_relaxation'] = rd(O + '/RELAX-COMPARISON.json')
dc = rd(O + '/diffcheck108.json')
out['pr2142_strict_models_on_extra'] = dict(jobs=len(dc), identical=sum(1 for r in dc if r.get('identical')), ddel_equal=sum(1 for r in dc if r.get('ddel_base') == r.get('ddel_extra')),
    S_sets=sorted({tuple(r['S']) for r in dc}), s_candidate_costs_checked=sum(r.get('checked', 0) for r in dc), b='#1094 DEFAULT_B (as #2142)',
    meaning='same budget and same filtered candidate list (keys, positions, columns, oracle costs): the CP-SAT model is identical, so #2142\'s 104 infeasibility proofs and 4 shape-infeasibilities apply to the extra word')
sp = rd(O + '/spivot-relax.json')
out['width_interface_reader_groups'] = dict(relaxation={k: {w: dict(dels=v[w]['dels'], delta=v[w].get('delta'), status=v[w].get('status'), profile=v[w].get('prof')) for w in v} for k, v in sp.items()})
jm = rd(O + '/jointmove-extra.json')['results']
out['width_interface_reader_groups']['exact_relocations_extra'] = dict(jobs=len(jm), outcomes=dict(collections.Counter('%s/%s' % (r['status'], 'neg' if (r.get('delta') or 0) < 0 else ('pos' if (r.get('delta') or 0) > 0 else '0')) for r in jm)),
    gains=[r for r in jm if r.get('delta') is not None and r['delta'] < 0])
skm = []
for p in sorted(glob.glob(O + '/skm-extra/skm-*.json')):
    r = rd(p); skm.append(dict(name=r['name'], dels=r['dels'], ddel=r['ddel'], keys=r['keys'], candidates=r['ncand'], shape=r['shape'], cp_status=r['cp_status'], solutions=len(r['res']), sec=r['sec']))
out['width_interface_reader_groups']['multi_deletion_split_key_strict'] = dict(settings='<=12 inserts, |lambda|<=4 in half steps, budget |gain|-1, per-insert cap = budget, CP-SAT 300 s, #1094 DEFAULT_B', runs=skm)
dg = []
for p in sorted(glob.glob(O + '/skm-diag/diag-*.json')):
    r = rd(p); dg.append(dict(name=r['name'], candidates=r['ncand'], cp_status_after_exclusions=r['cp_status'], solutions=[dict(status=x['status'], delta=x['delta'], terms=x['terms']) for x in r['res']], sec=r['sec']))
out['width_interface_reader_groups']['diagnostic_no_budget_cap3'] = dg
if os.path.exists(O + '/relaxA-extra.json'):
    ra = rd(O + '/relaxA-extra.json'); res = ra['results']
    refA = {}
    refA.update(rd(R + '/vendor/pr2142/research/t74-split-key-kernel-search/data/relaxation-A-rest.json'))
    refA.update(rd(R + '/vendor/pr1957/research/t74-k554-local-exhaustion/data/relaxation-A-sample.json'))
    bp = {1: 2348, 2: 500, 3: 416, 4: 130, 5: 82}; ep = {int(k): v for k, v in ra['base_profile'].items()}
    def dprof(p, base):
        p = {int(k): v for k, v in p.items()}; return {k: p.get(k, 0) - base.get(k, 0) for k in set(p) | set(base) if p.get(k, 0) != base.get(k, 0)}
    same = sum(1 for i, r in res.items() if 'prof' in r and i in refA and 'prof' in refA[i] and dprof(r['prof'], ep) == dprof(refA[i]['prof'], bp))
    out['a_relaxation'] = dict(gates=len(res), statuses=dict(collections.Counter(r.get('status', 'ok') for r in res.values())), with_gain=sum(1 for r in res.values() if r.get('delta', 0) < 0),
        reference_base_gates=len(refA), profile_change_identical_to_base_reference=same,
        gain_histogram=dict(sorted(collections.Counter(r['delta'] for r in res.values() if r.get('delta', 0) < 0).items())))
out['kernel_found'] = False
out['status'] = 'NO_EXTRA_WORD_KERNEL_IN_SEARCHED_FAMILIES'
json.dump(out, open(A + '/RESULTS.json', 'w'), indent=1, default=str)
print(json.dumps({k: (v if not isinstance(v, dict) else {kk: (vv if not isinstance(vv, (list, dict)) else '...') for kk, vv in v.items()}) for k, v in out.items()}, indent=1, default=str)[:4000])
