"""reloc16: exact commuting relocations of the outlier gates of variant 651-655-30-96-139-267 (B1117-B1124, B1647..B1660
class members), priced with the rev3 harness (static rules, exact map screen, unchanged derived compensation, exact optimal
frames, interval certificate); the same moves priced on the base word as a control.  usage: reloc16.py OUT.json"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import harness as H
WORDS = os.path.join(os.path.dirname(__file__), '..', 'words'); OUT = os.path.join(os.path.dirname(__file__), '..', 'out')
GATES = [1117, 1118, 1119, 1120, 1121, 1122, 1123, 1124, 1647, 1648, 1651, 1652, 1655, 1656, 1659, 1660]
def commutes(g, h):
    t, s = g[1], g[2]
    if h[0] == 'add': return h[2] != t and h[1] != s
    return h[1] not in (t, s)
def window(B, i):
    g = B[i]; lo = i
    while lo - 1 >= 0 and commutes(g, B[lo - 1]): lo -= 1
    hi = i
    while hi + 1 < len(B) and commutes(g, B[hi + 1]): hi += 1
    return lo, hi   # g may sit anywhere in [lo, hi+1) as an insert-before index in the deleted word coordinates
def moves(B, i):
    lo, hi = window(B, i); ps = sorted({lo, (lo + i) // 2, max(lo, i - 1), min(hi + 1, i + 2), (i + hi + 1) // 2, hi + 1} - {i, i + 1})
    return lo, hi, ps
if __name__ == '__main__':
    words = [('V30', os.path.join(WORDS, '651-655-30-96-139-267.json.gz')), ('base', os.path.join(C.INP, 'gauge44-word-566-554.json.gz'))]
    res = []; t0 = time.time()
    for nm, p in words:
        P = H.Pricer(p, b=C.B, check_literal=True, interval=True); B = P.base['B']
        for i in GATES:
            lo, hi, ps = moves(B, i)
            for q in ps:
                ed = dict(delete=[i], insert=[[q, list(B[i][:-1]) + [[]]]])
                r = P.price(ed, timeout=300)
                keep = {k: r[k] for k in ('status', 'delta', 'profile', 'gain_certified', 'max_gain_units', 'audit', 'why') if k in r}
                res.append(dict(word=nm, gate=i, gate_op=B[i][:5], window=[lo, hi], to=q, ed=ed, **keep))
                print(nm, i, B[i][:4], 'win', lo, hi, '->', q, keep.get('status'), keep.get('delta'), keep.get('gain_certified'), keep.get('audit'), f'{time.time()-t0:.0f}s', flush=True)
                json.dump(res, open(os.path.join(OUT, sys.argv[1]), 'w'))
    print('done', len(res), f'{time.time()-t0:.0f}s')
