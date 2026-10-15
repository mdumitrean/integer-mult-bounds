"""summarize: machine-readable SUMMARY.json of all r3/D-families runs."""
import json, collections, os
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def tally(path):
    if not os.path.exists(path): return None
    rs = [json.loads(l) for l in open(path)]
    return dict(n=len(rs), status=dict(collections.Counter(r['status'] for r in rs)),
                deltas={str(k): v for k, v in sorted(collections.Counter(r.get('delta') for r in rs if r.get('delta') is not None).items())},
                gains=[r['id'] for r in rs if r.get('delta') is not None and r['delta'] < 0])
o = lambda p: os.path.join(D, 'out', p)
cs = json.load(open(o('CAPSCREEN-base.json')))
S = dict(agent='r3/D-families', words=dict(base='76c01583 (gauge44-word-566-554)', extra='e86142b3 (extra-word-566-554)'),
         b='0.001679754956125544', base_cost=11683290250,
         runs={'1a single-crossing compensated moves (BASE, all 4824)': tally(o('CMOVE-base.jsonl')),
               '1a base-feasible moves on EXTRA (1020)': tally(o('CMOVE-extra-ok.jsonl')),
               '1b multi-crossing moves on target ports (BASE, 1736)': tally(o('CMULTI-base.jsonl')),
               '1b two-stage PFS: no-pre + novel single-crossing pre-edits (BASE, 969)': tally(o('TS-base.jsonl')),
               '1b two-stage PFS: novel multi-crossing pre-edits (BASE, 39)': tally(o('TSM-base.jsonl')),
               'EXTRA batch: 969 + 39 two-stage + 109 base-infeasible moves near 627/629/630/631': tally(o('EXTRA-batch.jsonl'))},
         capscreen={q: dict(ports=v['ports'], dimK=v['dimK'], screen=v['screen'].get('delta'), capped=v['capped'].get('delta'),
                            base_capped=v['base_capped'].get('delta'), unrealizable=v['unrealizable']) for q, v in cs.items()},
         relocation=dict(candidates=0, mergeable_pairs=0, repeated_ts_pairs=165))
json.dump(S, open(os.path.join(D, 'SUMMARY.json'), 'w'), indent=1); print(json.dumps(S['runs'], indent=0)[:3000])
