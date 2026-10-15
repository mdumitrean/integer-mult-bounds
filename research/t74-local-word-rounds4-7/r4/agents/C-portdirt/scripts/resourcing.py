"""resourcing.py: family S (compensation-absorbed re-sourcing) on one word, exact rationals.
For a B port read g = (t += c s) at B index i, delete g and insert (t += c y) before base B index p, where p lies in g's
port window (no gate between reads t or scales t) and y's value before p equals s's value before i on every
NON-ordinary column (data, ports, entering and low-end helpers).  The A+cut+B map then changes only in port rows x ordinary
helper columns, which the re-derived compensation cancels.  (p, y) = (i, s) is excluded; (p, s) with p != i is a re-timing.
usage: resourcing.py WORD.json.gz OUT.json"""
import gzip, json, sys, collections
from fractions import Fraction as F
w = json.load(gzip.open(sys.argv[1])); r = w['report']; V = r['v']; n = 2 * V + r['R']
ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
ordinary = lambda k: k >= 2 * V and k not in ent and k not in low
def coef(e): return F(e[3], e[4]) if e[0] == 'add' else F(e[2], e[3])
rows = [{k: F(1)} for k in range(n)]
def apply(e):
    c = coef(e); t = e[1]
    if e[0] == 'scale': rows[t] = {k: a * c for k, a in rows[t].items()}; return
    d = rows[t]
    for k, a in rows[e[2]].items():
        y = d.get(k, 0) + c * a
        if y: d[k] = y
        else: d.pop(k, None)
for e in w['A'] + w['cut']: apply(e)
B = w['B']; L = len(B)
key = lambda row: tuple(sorted((k, a) for k, a in row.items() if not ordinary(k)))
# windows of constant value per register over B positions: value before position p (p in [start, end))
start = [0] * n; cur_key = [key(rows[x]) for x in range(n)]; win = collections.defaultdict(list)
src_key = {}
for i, e in enumerate(B):
    if e[0] == 'add' and V <= e[1] < 2 * V: src_key[i] = cur_key[e[2]]
    t = e[1]; apply(e); nk = key(rows[t])
    if nk != cur_key[t]:
        win[cur_key[t]].append((t, start[t], i + 1)); start[t] = i + 1; cur_key[t] = nk
for x in range(n): win[cur_key[x]].append((x, start[x], L + 1))
# value windows hold "value before position p" for p in [start, end): a register written at gate i has its old value
# for p <= i and the new one for p >= i+1.
def port_window(i, t):
    lo = i
    while lo > 0 and not ((B[lo - 1][0] == 'add' and B[lo - 1][2] == t) or (B[lo - 1][0] == 'scale' and B[lo - 1][1] == t)): lo -= 1
    hi = i + 1
    while hi < L and not ((B[hi][0] == 'add' and B[hi][2] == t) or (B[hi][0] == 'scale' and B[hi][1] == t)): hi += 1
    return lo, hi           # insert positions p in [lo, hi]: before base index p (p == hi: just before the next port op)
cands = []; per = collections.Counter()
for i, kk in src_key.items():
    e = B[i]; t, s = e[1], e[2]; lo, hi = port_window(i, t)
    for (y, a, b) in win.get(kk, []):
        if y == t: continue
        if V <= y < 2 * V and False: pass
        p0, p1 = max(a, lo), min(b - 1, hi)
        for p in range(p0, p1 + 1):
            if y == s and p in (i, i + 1): continue      # same gate (before/after itself is the same read)
            if y == s and a <= i < b and a <= p < b: kind = 'commuting-retime'   # s unchanged on the way: #1957's class
            elif y == s: kind = 'absorbed-retime'
            else: kind = 'resource'
            cands.append(dict(B=i, t=t, s=s, c=[e[3], e[4]], y=y, p=p, kind=kind))
            per[kind] += 1
print(sys.argv[1].split('/')[-1], 'port reads', len(src_key), 'candidates', dict(per),
      'reads with a resource', len({c['B'] for c in cands if c['kind'] == 'resource'}))
json.dump(dict(word=sys.argv[1].split('/')[-1], counts=dict(per), cands=[c for c in cands if c['kind'] != 'commuting-retime']),
          open(sys.argv[2], 'w'))
