"""Pairs of r3 pre-moves (W0-relative edits) whose merge cancels inserted gates: same insert position and (op, target,
source) with coefficients summing to zero (or tail inserts at the same early-cleanup slot).  Also pairs where one move's
insert re-creates a gate the other deletes at the same index.  Output: out/CANCEL-PAIRS.json (merged, simplified edits)."""
import collections, json, os, sys
from fractions import Fraction as Q
sys.path.insert(0, os.path.dirname(__file__)); import common
pms = json.load(open(os.path.join(common.OUT, 'PREMOVES.json')))
def key(kind, pos, g): return (kind, pos, g[0], g[1], g[2] if g[0] == 'add' else None)
def coef(g): return Q(g[3], g[4]) if g[0] == 'add' else Q(g[2], g[3])
idx = collections.defaultdict(list)
for n, p in enumerate(pms):
    for pos, g in p['ed']['insert']: idx[key('B', pos, g)].append((n, coef(g)))
    for pos, g in p['ed']['tail']: idx[key('T', pos, g)].append((n, coef(g)))
pairs = set()
for k, lst in idx.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            (a, ca), (b, cb) = lst[i], lst[j]
            if a != b and ca + cb == 0: pairs.add((min(a, b), max(a, b)))
def merge(e1, e2):
    if set(e1['delete']) & set(e2['delete']): return None
    m = dict(delete=sorted(set(e1['delete']) | set(e2['delete'])), insert=[], tail=[], prepend=e1['prepend'] + e2['prepend'])
    acc = collections.OrderedDict()
    for kind in ('insert', 'tail'):
        for pos, g in e1[kind] + e2[kind]:
            k = key(kind, pos, g); acc.setdefault(k, [kind, pos, g, Q(0)]); acc[k][3] += coef(g)
    for kind, pos, g, c in acc.values():
        if c == 0: continue
        h = [g[0], g[1], g[2], c.numerator, c.denominator, []] if g[0] == 'add' else [g[0], g[1], c.numerator, c.denominator, []]
        m['insert' if kind == 'insert' else 'tail'].append([pos, h])
    return m
out = []
for a, b in sorted(pairs):
    m = merge(pms[a]['ed'], pms[b]['ed'])
    if m is None: continue
    n0 = len(pms[a]['ed']['insert']) + len(pms[a]['ed']['tail']) + len(pms[b]['ed']['insert']) + len(pms[b]['ed']['tail'])
    out.append(dict(id=pms[a]['id'] + ' + ' + pms[b]['id'], d1=pms[a]['delta1'], d2=pms[b]['delta1'], removed=n0 - len(m['insert']) - len(m['tail']), ed=m))
print('insert keys', len(idx), 'cancelling pairs', len(pairs), 'mergeable', len(out), collections.Counter(o['removed'] for o in out).most_common(6))
print(collections.Counter((o['id'].split(':')[0], o['id'].split(' + ')[1].split(':')[0]) for o in out).most_common(10))
json.dump(out, open(os.path.join(common.OUT, 'CANCEL-PAIRS.json'), 'w'))
