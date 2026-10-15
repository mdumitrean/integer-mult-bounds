"""summarize: collect SINGLES/RSINGLES/BNB/RBNB outputs into out/EVIDENCE.json."""
import json, glob, os
JDIR = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(JDIR, '..', 'out')
ev = dict(agent='J-carrier', round='r6', b='0.001679754956125544', words={'base': 'r3/inputs/gauge44-word-566-554.json.gz'}, pivots={})
for f in sorted(glob.glob(f'{D}/RBNB-*.json')):
    r = json.load(open(f)); ev['pivots'][f"{r['word']}:{r['q']}"] = {k: r[k] for k in ('dp', 'deleted_delta', 'n_cand', 'n_feasible', 'single_hist', 'uncoverable', 'nodes', 'limit_hit', 'best', 'status', 'seconds')}
for f in sorted(glob.glob(f'{D}/BNB-*.json')):
    r = json.load(open(f)); ev.setdefault('relaxations', {})[f"{r['word']}:{r['q']}"] = {k: r.get(k) for k in ('n_cand', 'best_rfree', 'best_qfree', 'status', 'nodes')}
for f in sorted(glob.glob(f'{D}/SINGLES-*.json')):
    r = json.load(open(f)); ok = [s for s in r['singles'] if s['status'] == 'ok']
    ev.setdefault('qfree_singles', {})[f"{r['word']}:{r['q']}"] = dict(n=r['n'], ok=len(ok), all_free=all(s['delta'] == r['deleted_delta'] for s in ok), deleted_delta=r['deleted_delta'])
for f in sorted(glob.glob(f'{D}/RSINGLES-*.json')):
    r = json.load(open(f)); ok = [s for s in r['singles'] if s['status'] == 'ok']
    import collections
    ev.setdefault('rfree_singles', {})[f"{r['word']}:{r['q']}"] = dict(n=r['n'], ok=len(ok), hist=collections.Counter(s['delta'] for s in ok).most_common(6))
extra = os.path.join(D, 'EXTRA-CHECKS.json')
if os.path.exists(extra): ev['extra_checks'] = json.load(open(extra))
json.dump(ev, open(f'{D}/EVIDENCE.json', 'w'), indent=1, default=str); print(json.dumps({k: (v if k != 'pivots' else {p: x['status'] for p, x in v.items()}) for k, v in ev.items()}, default=str)[:3000])
