"""Greedy joint narrowing: apply feasible single start-side narrowings one at a time (best first), keeping each one that
keeps the word frame-feasible with certified frames and lowers the cost; record the cumulative word and its exact cost.
usage: joint_narrow.py TOOLKIT WORD SINGLES.jsonl OUT_PREFIX [max_seconds]"""
import copy, gzip, json, os, sys, time
TK = sys.argv[1]; sys.path.insert(0, TK); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
WORD, SINGLES, OUTP = sys.argv[2], sys.argv[3], sys.argv[4]; TMAX = float(sys.argv[5]) if len(sys.argv) > 5 else 1500
base = K.load(WORD); C = F.Costs(K.B); r0 = K.solve(base, C)[0]; cost0 = r0['cost']
singles = [json.loads(l) for l in open(SINGLES) if l.strip()]
cand = sorted([s for s in singles if s['status'] == 'ok' and s['delta'] < 0], key=lambda s: (s['delta'], s['q']))
seen = set(); order = []
for s in cand:
    if s['q'] in seen: continue
    seen.add(s['q']); order.append(s)
cur = copy.deepcopy(base); cost = cost0; kept = []; log = []; t0 = time.time()
for s in order:
    if time.time() - t0 > TMAX: log.append(dict(stop='time')); break
    w = copy.deepcopy(cur); w['start_extra'][str(s['q'])] = s['basis']
    try:
        with deadline(90):
            r, g, nc = K.solve(w, C)
        if r['certified'] and r['cost'] < cost:
            kept.append(dict(q=s['q'], width=s['width'], basis=s['basis'], step_delta=r['cost'] - cost, single_delta=s['delta']))
            cur, cost, prof = w, r['cost'], r['profile']; cur['_last'] = None
            log.append(dict(q=s['q'], ok=True, step=r['cost'] - kept[-1]['step_delta'] - cost if False else kept[-1]['step_delta']))
        else: log.append(dict(q=s['q'], ok=False, why='cost' if r['certified'] else 'uncertified'))
    except F.Infeasible: log.append(dict(q=s['q'], ok=False, why='infeasible'))
    except Timeout: log.append(dict(q=s['q'], ok=False, why='timeout'))
    rss = peak_rss_gib()
    if rss is not None and rss > 6: log.append(dict(stop='rss')); break
    if len(log) % 10 == 0: print(f'  tried {len(log)} kept {len(kept)} total {cost - cost0} {time.time()-t0:.0f}s', flush=True)
cur.pop('_last', None)
res = dict(word=WORD.split('/')[-1], base_cost=cost0, final_cost=cost, total_delta=cost - cost0, kept=len(kept), tried=len(log),
           kept_list=kept, log=log, final_profile=dict(sorted(prof.items())) if kept else None, seconds=round(time.time() - t0, 1))
json.dump(res, open(OUTP + '.json', 'w'), indent=1)
w = cur; json.dump(w, gzip.open(OUTP + '-start_extra-only.json.gz', 'wt'))
print('kept', len(kept), 'total delta', cost - cost0, 'per narrowing', (cost - cost0) / max(1, len(kept)))
