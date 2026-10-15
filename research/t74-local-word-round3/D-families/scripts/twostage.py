"""twostage: family 1 (two-column) for never-written copy-window pivots.
Stage 1 (pre-edit): an exact compensated non-commuting re-timing (gen_cmove) of a B gate that WRITES a register in the
non-FULL-end support of q's deletion vector (the ports q delivers into, directly or via its copy), frame-feasible alone
(status ok in the CMOVE sweep).  Stage 2: round-2 PFS on the pre-edited word: delete the q-reads D (all reads, and each
single read), compensate with <= K inserted q-reads (exact dyadic solve, joint frame screen) + free cleanup prepends.
Output: composed candidate edits relative to the base word (priced by runner.py).
usage: twostage.py WORD CMOVE-cands.json CMOVE-results.jsonl OUT.json q1,q2,... [K] [maxpre]"""
import sys, os, json, time, itertools, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r2h'))
from common import *
from pfslib import PFS
import sx
WN, CANDS, RES, OUT, QS = sys.argv[1:6]; K = int(sys.argv[6]) if len(sys.argv) > 6 else 4; MAXPRE = int(sys.argv[7]) if len(sys.argv) > 7 else 60
P = H.Pricer(WORDS[WN], b=os.environ['IMB_B'], check_literal=True); w = P.base; B = w['B']; nB = len(B)
cands = {c['id']: c for c in json.load(open(CANDS))}
okpre = [json.loads(l) for l in open(RES)]; okpre = [r['id'] for r in okpre if r['status'] == 'ok' and r.get('delta') == 0]
seq = list(B) + [w['cleanup'][i] for i, U in w['early_cleanup']]; N = sx.nregs(w); Sfx = sx.Suffix(seq, N)
fe = lambda r: (r < 112 or r >= 224) and str(r) not in w['helper_final']
allc = []; summ = {}
for q in map(int, QS.split(',')):
    reads = [i for i, g in enumerate(B) if g[0] == 'add' and g[2] == q]
    d = {}
    for i in reads: d = sx.addv(d, Sfx.at(B[i][1], i + 1), sx.coef(B[i]))
    supp = sorted(k for k in d if not fe(k))
    pres = [None]
    for pid in okpre:
        ed = cands[pid]['ed']; i = ed['delete'][0]; g = B[i]; comp = ed['insert'][1][1]
        if i in reads: continue
        if g[1] in supp or comp[1] in supp: pres.append(pid)
    pres = pres[:MAXPRE + 1]
    print(f'q {q}: reads {reads} supp(non-FULL d) {supp} pre-edits {len(pres) - 1}', flush=True)
    Ds = [tuple(reads)] + [(r,) for r in reads]
    for pid in pres:
        pre = None if pid is None else dict(delete=cands[pid]['ed']['delete'], insert=cands[pid]['ed']['insert'])
        S_ = PFS(P, q, pre)
        for Dsub in Ds:
            t0 = time.time()
            try: r = S_.run(list(Dsub), K, maxsets=8)
            except AssertionError as e: r = dict(status='assert', cands=[])
            n = len(r['cands']); summ[f'{q}|{pid}|{Dsub}'] = dict(status=r['status'], natoms=r.get('natoms'), nsols=r.get('nsols'), ncands=n, s=round(time.time() - t0, 1))
            for j, c in enumerate(r['cands']):
                c['id'] = f"TS-{q}-{pid or 'nopre'}-D{'_'.join(map(str, Dsub))}-{j:02d}"; c['pivot'] = q; c['pre'] = pid; c['D'] = list(Dsub); allc.append(c)
        print(f'  pre {pid}: ' + ' '.join(f"{len(k.split('|')[2])}:{v['status'][:3]}/{v['ncands']}" for k, v in summ.items() if k.startswith(f'{q}|{pid}|')), flush=True)
json.dump(allc, open(OUT, 'w')); json.dump(summ, open(OUT.replace('.json', '-summary.json'), 'w'), indent=0)
print('total cands', len(allc), collections.Counter(c['pivot'] for c in allc))
