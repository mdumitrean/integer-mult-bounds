"""Aggregate the walk evidence into out/SUMMARY.json."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(__file__)); import common
O = common.OUT; S = {}
def jl(name): p = os.path.join(O, name); return [json.loads(l) for l in open(p)] if os.path.exists(p) else []
pms = json.load(open(os.path.join(O, 'PREMOVES.json')))
S['premoves'] = dict(unique=len(pms), by_source_delta={f'{k[0]}:{k[1]}': v for k, v in collections.Counter((p['src'], p['delta1']) for p in pms).items()})
st = json.load(open(os.path.join(O, 'STRUCT.json')))
sh = jl('SHARED2.jsonl')
S['shared_fusion_unblocking'] = dict(premoves_scanned=st['n'], base_shared_candidates=st['base_shared'], premoves_opening_shared=len(st['hits']),
    composites_priced=sum(len(r['results']) for r in sh), status={f'{k[0]}:{k[1]}': v for k, v in collections.Counter((x['status'], x['total']) for r in sh for x in r['results']).items()})
st2p = os.path.join(O, 'STRUCT2.json'); sh3 = jl('SHARED3.jsonl')
if os.path.exists(st2p):
    st2 = json.load(open(st2p))
    S['shared_fusion_two_premoves'] = dict(pairs_clearing_both_blockers=st2['pairs'], pairs_opening_shared=len(st2['hits']),
        composites_priced=sum(len(r['results']) for r in sh3), status={f'{k[0]}:{k[1]}': v for k, v in collections.Counter((x['status'], x['total']) for r in sh3 for x in r['results']).items()},
        delta1=sorted({str(r.get('delta1')) for r in sh3}))
cp = jl('CANCEL-PAIRS-base.jsonl')
S['cancelling_pairs'] = dict(mergeable=len(cp), status={f'{k[0]}:{k[1]}': v for k, v in collections.Counter((r.get('status'), r.get('delta')) for r in cp).items()})
for tag, name in (('local_research_neutral', 'LR2.jsonl'), ('local_research_positive', 'LR2-pos.jsonl'), ('local_research_neutral_batch2', 'LR2b.jsonl')):
    rs = jl(name)
    if not rs: continue
    sec = collections.Counter(); rel = collections.Counter(); tot = collections.Counter(); gains = []; n2 = 0; n2all = 0
    for r in rs:
        n2all += r.get('n2_all', 0)
        for cid, s, d in r.get('second', []):
            n2 += 1; sec[f'{s}:{d}'] += 1
            if d is not None and r.get('delta1') is not None and r['delta1'] + d < 0: gains.append([r['id'], cid, r['delta1'], d])
        for i, d0, d1 in r.get('relax', []):
            rel['same' if d1 == d0 else ('infeasible' if not isinstance(d1, int) else ('better' if d1 < d0 else 'worse'))] += 1
            if isinstance(d1, int) and r.get('delta1') is not None: tot[('walk-better' if r['delta1'] + d1 < d0 else ('walk-same' if r['delta1'] + d1 == d0 else 'walk-worse'))] += 1
    S[tag] = dict(premoves=len(rs), delta1=dict(collections.Counter(str(r.get('delta1')) for r in rs)), second_moves_generated=n2all,
                  second_moves_priced=n2, second_status=dict(sec.most_common()), relaxations=dict(rel), relaxation_walk_totals=dict(tot), gains=gains,
                  seconds=round(sum(r.get('seconds', 0) for r in rs), 1))
json.dump(S, open(os.path.join(O, 'SUMMARY.json'), 'w'), indent=1); print(json.dumps(S, indent=1)[:3000])
