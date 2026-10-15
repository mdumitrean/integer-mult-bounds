"""run_pfs: PFS over pivots x all nonempty subsets of their B reads (no pre-edit).  usage: run_pfs.py WORD K OUT.json q1,q2,.."""
import sys, os, json, itertools, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from pfslib import PFS
P = H.Pricer(WORDS[sys.argv[1]], check_literal=True); K = int(sys.argv[2]); OUT = sys.argv[3]
qs = [int(x) for x in sys.argv[4].split(',')]
allc = []; summ = {}
for q in qs:
    S_ = PFS(P, q); reads = [P.base['B'][0] and x[1] for x in S_.prov0 if x[0] == 'b' and P.base['B'][x[1]][0] == 'add' and P.base['B'][x[1]][2] == q]
    for k in range(1, len(reads) + 1):
        for Dsub in itertools.combinations(reads, k):
            t0 = time.time(); r = S_.run(list(Dsub), K)
            n = len(r['cands']); summ[f'{q}:{Dsub}'] = dict(status=r['status'], natoms=r.get('natoms'), nsols=r.get('nsols'), ncands=n)
            for j, c in enumerate(r['cands']):
                c['id'] = f"PFS-{q}-D{'_'.join(map(str, Dsub))}-{j:03d}"; c['pivot'] = q; c['D'] = list(Dsub); allc.append(c)
            print(q, Dsub, r['status'], 'atoms', r.get('natoms'), 'sols', r.get('nsols'), 'cands', n, 'with prepends', sum(1 for c in r['cands'] if c['nprepend']), f'{time.time()-t0:.1f}s', flush=True)
json.dump(allc, open(OUT, 'w')); json.dump(summ, open(OUT.replace('.json', '-summary.json'), 'w'), indent=0)
print('total cands', len(allc))
