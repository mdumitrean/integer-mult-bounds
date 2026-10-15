"""calib_aid.py: A-insert identity calibration for the compensation-aware pricer (agent G-ainsert r6).
An A gate's (t, s) pair is inserted as +1 then -1 right before that gate (net identity, frame-compatible): must price ok,
delta 0, compensation unchanged, and pass the unchanged audit_local.py --main.  Control: the +1 insert alone is inexact.
usage: calib_aid.py WORD OUT.json AUDITDIR"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from absorb import AbsorbPricer
word, outp, adir = sys.argv[1:4]
P = AbsorbPricer(word, check_literal=True, interval=True); A = P.base['A']; V = 112; res = []
picks = [k for k, e in enumerate(A) if e[0] == 'add' and not (V <= e[1] < 2 * V) and not (V <= e[2] < 2 * V)]
for k in (picks[len(picks) // 3], picks[2 * len(picks) // 3], picks[-1]):
    e = A[k]; g1 = ['add', e[1], e[2], 1, 1, []]; g2 = ['add', e[1], e[2], -1, 1, []]
    pr = P.price_ab(dict(insert=[('A', k, g1), ('A', k, g2)]), always_audit=True, audit_dir=os.path.join(adir, f'id-A{k}'))
    pr.pop('word', None); res.append(dict(kind='identity', A=k, gate=e[:5], price=pr)); print('identity A', k, e[:5], pr.get('status'), pr.get('delta'), pr.get('comp_gates'), pr.get('audit', {}).get('status'), flush=True)
    pc = P.price_ab(dict(insert=[('A', k, g1)])); pc.pop('word', None)
    res.append(dict(kind='control-single', A=k, price=pc)); print('control A', k, pc.get('status'), flush=True)
json.dump(res, open(outp, 'w'), indent=1, default=str)
