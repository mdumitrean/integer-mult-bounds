"""precond.py: (1) the precondition acts only on targets and equals the inverse of the target-only mixing of B + early tail;
(2) which A/B gates act only on registers still at frame 0 at that point of the literal frame chains (already free in place);
(3) frame-0 registers at the start: targets and ordinary helpers; data and entering helpers start above 0.
usage: precond.py WORD.json.gz OUT.json"""
import json, gzip, sys, collections
from fractions import Fraction as Q
V = 112
w = json.load(gzip.open(sys.argv[1])); R = w['report']['R']; n = 2 * V + R
def coef(e): return Q(e[3], e[4]) if e[0] == 'add' else Q(e[2], e[3])
def apply(e, rows):
    if e[0] == 'add':
        t, s, q = e[1], e[2], coef(e); d = rows[t]
        for k, x in rows[s].items():
            y = d.get(k, 0) + q * x
            if y: d[k] = y
            else: d.pop(k, None)
    else:
        t, q = e[1], coef(e); rows[t] = {k: q * x for k, x in rows[t].items()}
isT = lambda r: V <= r < 2 * V
pre_regs = collections.Counter('target' if isT(r) else 'other' for e in w['precondition'] for r in ([e[1], e[2]] if e[0] == 'add' else [e[1]]))
tail = [w['cleanup'][i][:-1] + [U] for i, U in w['early_cleanup']]
mixB = [e for e in w['B'] if isT(e[1]) and (e[0] == 'scale' or isT(e[2]))]
mixT = [e for e in tail if isT(e[1]) and (e[0] == 'scale' or isT(e[2]))]
rows = [{k: Q(1)} for k in range(n)]
for e in w['precondition'] + mixB + mixT: apply(e, rows)
identity = all(rows[t] == {t: Q(1)} for t in range(V, 2 * V))
# literal frames: gates whose frame is empty (frame-0 gates, free in place)
emptyA = sum(1 for e in w['A'] if not e[-1]); emptyB = sum(1 for e in w['B'] if not e[-1])
start0 = dict(targets=V, ordinary_or_cold_helpers=sum(1 for q in range(2 * V, n) if str(q) not in w['start_extra']), entering_helpers=len(w['start_extra']), data_at_dim1=V)
res = dict(word=sys.argv[1].split('/')[-1], precondition_gates=len(w['precondition']), precondition_register_kinds=dict(pre_regs),
           b_target_mixing_gates=len(mixB), tail_target_mixing_gates=len(mixT), precondition_is_inverse_of_target_mixing=identity,
           a_gates_frame0=emptyA, b_gates_frame0=emptyB, frame0_registers_at_start=start0)
json.dump(res, open(sys.argv[2], 'w'), indent=1); print(res)
