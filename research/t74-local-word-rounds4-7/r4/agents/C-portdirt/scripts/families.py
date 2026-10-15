"""families.py: compensation-absorbed edit candidates on one word (exact rationals).
Absorbable change = a change of the A+cut+B map supported on port rows x ORDINARY helper columns (k >= 2v, not entering,
not a low end); the derived compensation then cancels it and the auditor's residual rules still hold.
Family R (absorbed re-timing): move a port read g = (t += c s) from B position i to j, crossing only gates that commute
with g OR write s with a pure-ordinary-dirt row (s += c' h, h's row supported on ordinary helpers); never crossing a gate
that reads t, scales t, scales s, or writes s with a non-ordinary row.  Moves crossing at least one ordinary-dirt write
of s are new (pure-commuting moves were #1957's).
Family P (cancelling pairs): two port reads g, h with m_g (x) N_g + lam m_h (x) N_h = 0, where N = non-ordinary part of
c*source row and m = the port-propagation vector of t after the read; deleting g and scaling h by (1+lam)... reduces to
deleting both when lam = 1 is needed exactly.
usage: families.py WORD.json.gz OUT.json"""
import gzip, json, sys, collections
from fractions import Fraction as F
w = json.load(gzip.open(sys.argv[1])); r = w['report']; V = r['v']; R = r['R']; n = 2 * V + R
entering = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
ordinary = lambda k: k >= 2 * V and k not in entering and k not in low
def coef(e): return F(e[3], e[4]) if e[0] == 'add' else F(e[2], e[3])
rows = [{k: F(1)} for k in range(n)]
def apply(e, rows):
    c = coef(e); t = e[1]
    if e[0] == 'scale': rows[t] = {k: a * c for k, a in rows[t].items()}; return
    d = rows[t]
    for k, a in rows[e[2]].items():
        y = d.get(k, 0) + c * a
        if y: d[k] = y
        else: d.pop(k, None)
for e in w['A'] + w['cut']: apply(e, rows)
B = w['B']; src_rows = []; kind = []
for i, e in enumerate(B):
    if e[0] == 'add':
        s = rows[e[2]]; nonord = any(not ordinary(k) for k in s); 
        kind.append('pure-ordinary' if not nonord else ('pure-dirt' if all(k >= 2 * V for k in s) else 'data'))
        src_rows.append({k: a for k, a in s.items()} if V <= e[1] < 2 * V else None)
    else: kind.append('scale'); src_rows.append(None)
    apply(e, rows)
# m vectors: contribution of t right after gate i to the final ports (backward pass)
contrib = [None] * n
for y in range(V, 2 * V): contrib[y] = {y: F(1)}
mvec = [None] * len(B)
for i in range(len(B) - 1, -1, -1):
    e = B[i]
    if e[0] == 'add' and V <= e[1] < 2 * V: mvec[i] = dict(contrib[e[1]])
    t = e[1]
    if e[0] == 'scale':
        if contrib[t] is not None: contrib[t] = {y: a * coef(e) for y, a in contrib[t].items()}
    else:
        s = e[2]; c = coef(e)
        if contrib[t] is not None:
            d = dict(contrib[s]) if contrib[s] is not None else {}
            for y, a in contrib[t].items():
                z = d.get(y, 0) + c * a
                if z: d[y] = z
                else: d.pop(y, None)
            contrib[s] = d or None
# Family R
def writes(e, x): return e[1] == x
def reads(e, x): return e[0] == 'add' and e[2] == x
moves = []; stats = collections.Counter()
for i, e in enumerate(B):
    if not (e[0] == 'add' and V <= e[1] < 2 * V): continue
    t, s = e[1], e[2]
    for direction in (+1, -1):
        j = i + direction; crossed_dirt = 0
        while 0 <= j < len(B):
            h = B[j]
            if reads(h, t) or (h[0] == 'scale' and h[1] in (t, s)): break       # changes m or the data read
            if writes(h, s):
                if kind[j] == 'pure-ordinary': crossed_dirt += 1
                else: break
            # placement: insert just past h (forward) or just before h (backward)
            if crossed_dirt:
                pos = j + 1 if direction > 0 else j
                moves.append(dict(B=i, t=t, s=s, to=pos, dir=direction, crossed_dirt_writes=crossed_dirt))
            j += direction
        stats['reads'] += 1
print(sys.argv[1].split('/')[-1], 'source kinds of all adds:', dict(collections.Counter(k for k in kind)))
print('family R: port reads', stats['reads'], 'absorbed re-timing placements', len(moves),
      'over', len({m['B'] for m in moves}), 'reads')
# Family P (exact rank-one cancellation of the non-ordinary parts)
def nonord(i):
    c = coef(B[i]); return {k: c * a for k, a in src_rows[i].items() if not ordinary(k)}
def norm(v):
    if not v: return None
    k0 = min(v); a0 = v[k0]; return tuple(sorted((k, a / a0) for k, a in v.items())), a0
groups = collections.defaultdict(list)
for i, e in enumerate(B):
    if src_rows[i] is None: continue
    Nv = nonord(i); mv = mvec[i]
    if not Nv or not mv: 
        if not Nv: stats['N-zero'] += 1
        continue
    nN, aN = norm(Nv); nm, am = norm(mv)
    groups[(nN, nm)].append((i, aN * am))
pairs = []
for key, lst in groups.items():
    for x in range(len(lst)):
        for y in range(x + 1, len(lst)):
            (i, ai), (j, aj) = lst[x], lst[y]
            if ai + aj == 0: pairs.append(dict(g=i, h=j, kind='cancel'))
print('family P: rank-one groups', len(groups), 'exactly cancelling pairs (delete both)', len(pairs), '| N-zero port reads', stats['N-zero'])
json.dump(dict(word=sys.argv[1].split('/')[-1], kinds=dict(collections.Counter(kind)), moves=moves, pairs=pairs,
               groups_multi=sum(1 for v in groups.values() if len(v) > 1)), open(sys.argv[2], 'w'))
