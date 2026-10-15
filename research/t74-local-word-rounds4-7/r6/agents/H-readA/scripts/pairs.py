"""pairs.py: the full-c1 (8,1,9) narrowings of r5 C (NARROW-base.jsonl) whose helper q is read in A; for each, q's reads and
writes in main (A, cut, B), whether each A read happens while q is pure (before q's first write), and the raw target leak L_q.
usage: pairs.py WORD NARROW-base.jsonl OUT.json"""
import gzip, json, sys
from fractions import Fraction as F
W, NARROW, OUT = sys.argv[1:4]
w = json.load(gzip.open(W)); v = w['report']['v']; R = w['report']['R']
main = [('A', i, g) for i, g in enumerate(w['A'])] + [('cut', i, g) for i, g in enumerate(w['cut'])] + [('B', i, g) for i, g in enumerate(w['B'])]
coef = lambda g: F(g[3], g[4]) if g[0] == 'add' else F(g[2], g[3])
def transfer(c, start):
    col = {c: F(1)}
    for k in range(start, len(main)):
        s, i, g = main[k]
        if g[0] == 'add':
            t, src = g[1], g[2]; x = col.get(src)
            if x:
                a = col.get(t, F(0)) + coef(g) * x
                if a: col[t] = a
                else: col.pop(t)
        elif g[1] in col: col[g[1]] = col[g[1]] * coef(g)
    return {y: a for y, a in col.items() if v <= y < 2 * v}
pairs = []
seen = set()
for l in open(NARROW):
    r = json.loads(l)
    if r.get('status') == 'ok' and r.get('width') == 9 and len(r.get('basis', [])) == 1 and r.get('delta') == -2116454:
        key = (r['q'], r['basis'][0])
        if key not in seen: seen.add(key); pairs.append(key)
NA = len(w['A'])
out = []
for q, u in pairs:
    writes = [k for k, (s, i, g) in enumerate(main) if g[1] == q]
    reads = [k for k, (s, i, g) in enumerate(main) if g[0] == 'add' and g[2] == q]
    readsA = [k for k in reads if k < NA]
    if not readsA: continue
    t0 = writes[0] if writes else None
    pure = [k for k in readsA if t0 is None or k < t0]
    L = transfer(q, 0)
    out.append(dict(q=q, u=u, first_write=t0, first_write_sec=(main[t0][0], main[t0][1]) if t0 is not None else None,
                    writes_A=[k for k in writes if k < NA], reads_A=readsA, pure_reads_A=pure,
                    pure_readers=[main[k][2][1] for k in pure], leak={str(y): str(a) for y, a in sorted(L.items())}))
json.dump(dict(word=W.split('/')[-1], full_c1_pairs=len(pairs), read_in_A=len(out), pairs=out), open(OUT, 'w'), indent=0)
print('full-c1 pairs', len(pairs), '| read in A', len(out), '| helpers', len({p['q'] for p in out}))
import collections
print('pure-read counts:', collections.Counter(len(p['pure_reads_A']) for p in out))
print('first write sections:', collections.Counter(p['first_write_sec'][0] if p['first_write_sec'] else None for p in out))
