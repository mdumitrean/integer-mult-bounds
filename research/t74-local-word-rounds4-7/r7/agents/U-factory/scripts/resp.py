"""resp.py: exact target-response (dirt) analysis of a FULL-WORD.
For every helper k >= 2V, its target response is the column k of the target rows y in [V, 2V) of the A+cut+B map,
transformed by the precondition (the derived compensation reads exactly the helpers with a nonzero response).
usage: resp.py WORD.json.gz [OUT.json]"""
import gzip, json, sys
from fractions import Fraction as Q
V = 112
def gate(e):
    if e[0] == 'add': return ('add', e[1], e[2], Q(e[3], e[4]))
    if e[0] == 'scale': return ('scale', e[1], None, Q(e[2], e[3]))
    raise ValueError(e[0])
def apply(g, rows):
    op, t, s, q = g
    if op == 'scale':
        rows[t] = {k: q * x for k, x in rows[t].items()}; return
    rt = rows[t]
    for k, x in rows[s].items():
        z = rt.get(k, 0) + q * x
        if z: rt[k] = z
        else: rt.pop(k, None)
def analyse(w):
    R = w['report']['R']; n = 2 * V + R
    rows = [{k: Q(1)} for k in range(n)]
    for sec in ('A', 'cut', 'B'):
        for e in w[sec]: apply(gate(e), rows)
    dirt = [{} for _ in range(n)]
    for y in range(V, 2 * V): dirt[y] = {k: a for k, a in rows[y].items() if k >= 2 * V}
    for e in w['precondition']: apply(gate(e), dirt)
    resp = {}
    for y in range(V, 2 * V):
        for k, a in dirt[y].items():
            if a: resp.setdefault(k, {})[y] = a
    entering = sorted(int(q) for q in w.get('start_extra', {}))
    ended = sorted(int(q) for q in w.get('helper_final', {}))
    read = sorted(resp)
    return dict(R=R, n_read=len(read), read=read, entering=entering, ended=ended,
                entering_with_response=sorted(set(entering) & set(read)), ended_with_response=sorted(set(ended) & set(read)),
                rows_per_helper={str(k): len(v) for k, v in sorted(resp.items())},
                resp={str(k): {str(y): str(a) for y, a in sorted(v.items())} for k, v in sorted(resp.items())})
if __name__ == '__main__':
    w = json.load(gzip.open(sys.argv[1])); r = analyse(w)
    print('R', r['R'], 'read', r['n_read'], 'entering', len(r['entering']), 'ended', len(r['ended']),
          'entering_with_response', len(r['entering_with_response']), 'ended_with_response', len(r['ended_with_response']))
    if len(sys.argv) > 2: json.dump(r, open(sys.argv[2], 'w'))
