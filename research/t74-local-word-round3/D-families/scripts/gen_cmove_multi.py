"""gen_cmove_multi: compensated re-timing of g = (y += c*s) across up to M non-commuting gates (one compensating gate per
crossing).  Invariant (forward): between g's old and new positions every register equals its original value except
y_trans = y_orig - c*s_current; each crossing h restores it with one gate placed adjacent to h:
  W (s += c'u): y += -c c' u after h;  S (s *= l): y += -c(l-1) s before h;  R (z += c'' y): z += c'' c s after h;
  Y (y *= l): y += (l-1) c s after h.   Backward (y_trans = y_orig + c*s_current):
  W: y += c c' u after h;  S: y += c(l-1) s before h;  R: z += -c'' c s after h;  Y: y += -(l-1) c s after h.
Blocking pairs (s += c' y) stop the move.  Only gates writing a register in TARGETS are moved.
usage: gen_cmove_multi.py OUT.json M y1,y2,..."""
import json, sys, collections
from fractions import Fraction as Q
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import common
from gen_cmove import interacts, coef, gate
def comp_for(direction, kind, d, y, s, c, k):
    if kind == 'W':
        u, c1 = d; return (gate(y, u, -c * c1), k + 1) if direction == 'F' else (gate(y, u, c * c1), k + 1)
    if kind == 'S': return (gate(y, s, -c * (d - 1)), k) if direction == 'F' else (gate(y, s, c * (d - 1)), k)
    if kind == 'R':
        z, c2 = d; return (gate(z, s, c2 * c), k + 1) if direction == 'F' else (gate(z, s, -c2 * c), k + 1)
    return (gate(y, s, (d - 1) * c), k + 1) if direction == 'F' else (gate(y, s, -(d - 1) * c), k + 1)
def gen(w, M, targets):
    B = w['B']; n = len(B); out = []
    for i, g in enumerate(B):
        if g[0] != 'add' or g[1] not in targets: continue
        y, s, c = g[1], g[2], coef(g)
        for direction in 'FB':
            rng = range(i + 1, n) if direction == 'F' else range(i - 1, -1, -1)
            hits = []
            for k in rng:
                it = interacts(g, B[k])
                if it is None: continue
                if it[0] == 'block': break
                hits.append((k, it))
                if len(hits) > M: break
            for m in range(2, min(M, len(hits)) + 1):          # m = 1 is the single-crossing sweep (gen_cmove)
                comps = []; ok = True
                for k, (kind, d) in hits[:m]:
                    cg, cp = comp_for(direction, kind, d, y, s, c, k)
                    if cg[3] == 0 or cg[1] == cg[2]: ok = False; break
                    comps.append([cp, cg])
                if not ok: continue
                km = hits[m - 1][0]; nxt = hits[m][0] if len(hits) > m else (n if direction == 'F' else -1)
                poss = sorted({km + 1, nxt}) if direction == 'F' else sorted({km, nxt + 1})
                for p in poss:
                    ins = [[p, list(g[:5]) + [[]]]] + comps
                    out.append(dict(id=f'M{direction}{m}-{i}-to{p}', g=i, dir=direction, m=m, crossed=[k for k, _ in hits[:m]], ed=dict(delete=[i], insert=ins)))
    return out
if __name__ == '__main__':
    OUT, M, T = sys.argv[1], int(sys.argv[2]), set(map(int, sys.argv[3].split(',')))
    w = common.load('base'); c = gen(w, M, T)
    print(len(c), collections.Counter((x['dir'], x['m']) for x in c))
    ex = [x for x in c if x['g'] == 518]; print('B518 examples:', [(x['id'], x['ed']['insert']) for x in ex][:4])
    json.dump(c, open(OUT, 'w'))
