"""Calibration 1: r4 C's demo insert 112 += 482 before B0 on the base word (expect 7,208 -> 7,209 gates, delta 0, audit PASS),
plus the unchanged base word (delta 0) and a control that must be rejected (a data-carrying port read deleted: inexact)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from absorb import AbsorbPricer, AGENT, SCR
word = os.path.join(SCR, 'r3', 'inputs', 'gauge44-word-566-554.json.gz'); t0 = time.time()
P = AbsorbPricer(word, check_literal=True, interval=True); out = dict(base_cost=P.base_cost, base_comp=len(P.compensation))
out['demo'] = P.price_absorb(dict(delete=[], insert=[(0, ['add', 112, 482, 1, 1, []])]), always_audit=True,
                             audit_dir=os.path.join(AGENT, 'out', 'calib', 'demo'))
out['identity'] = P.price_absorb(dict(delete=[], insert=[]))
B = P.base['B']; V = 112
j = next(i for i, e in enumerate(B) if e[0] == 'add' and V <= e[1] < 2 * V and e[2] < V)   # a port read of a data register
out['control_delete_data_read'] = dict(B=j, gate=B[j][:5], price=P.price_absorb(dict(delete=[j])))
out['seconds'] = round(time.time() - t0, 1)
os.makedirs(os.path.join(AGENT, 'out', 'calib'), exist_ok=True)
json.dump(out, open(os.path.join(AGENT, 'out', 'calib', 'CALIB-ABSORB.json'), 'w'), indent=1, default=str); print(json.dumps(out, indent=1, default=str))
