"""bfly.py: group B's target-only gates into pair groups (butterflies); for each group, the B gates before it that touch its
two targets.  A group is a conjugation candidate if every earlier gate touching its targets is a delivery from a non-target
(no earlier mix involves them); crossing it to the start of B (frame 0, free) replaces each such delivery by its conjugate.
usage: bfly.py WORD.json.gz OUT.json"""
import json, gzip, sys, collections
V = 112
w = json.load(gzip.open(sys.argv[1])); B = w['B']
isT = lambda r: V <= r < 2 * V
mix = [(j, e) for j, e in enumerate(B) if isT(e[1]) and (e[0] == 'scale' or isT(e[2]))]
# union pairs into groups by shared targets among mix gates
parent = {}
def find(x):
    while parent.setdefault(x, x) != x: x = parent[x]
    return x
for j, e in mix:
    a = e[1]; b = e[2] if e[0] == 'add' else e[1]; parent[find(a)] = find(b)
groups = collections.defaultdict(list)
for j, e in mix: groups[find(e[1])].append(j)
res = []; hist = collections.Counter()
for root, js in groups.items():
    regs = {B[j][1] for j in js} | {B[j][2] for j in js if B[j][0] == 'add'}
    first = min(js)
    before = [(i, B[i]) for i in range(first) if B[i][1] in regs or (B[i][0] == 'add' and B[i][2] in regs)]
    kinds = collections.Counter('delivery' if (isT(g[1]) and g[0] == 'add' and not isT(g[2])) else 'mix' if isT(g[1]) else 'other' for i, g in before)
    interleaved = [i for i in range(first, max(js)) if i not in js and (B[i][1] in regs or (B[i][0] == 'add' and B[i][2] in regs))]
    cand = kinds.get('mix', 0) == 0 and kinds.get('other', 0) == 0
    res.append(dict(targets=sorted(regs), gates=js, first=first, earlier=dict(kinds), interleaved=len(interleaved), candidate=cand))
    hist[(len(regs), len(js), cand)] += 1
res.sort(key=lambda r: (not r['candidate'], r['earlier'].get('delivery', 0) + r['interleaved']))
out = dict(word=sys.argv[1].split('/')[-1], groups=len(res), hist={str(k): v for k, v in hist.items()}, groups_detail=res)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print('groups', len(res), 'by (targets, gates, candidate):', dict(hist))
c = [r for r in res if r['candidate']]
print('candidates', len(c), 'crossed deliveries (min/median/max):', (min(r['earlier'].get('delivery', 0) for r in c), sorted(r['earlier'].get('delivery', 0) for r in c)[len(c)//2], max(r['earlier'].get('delivery', 0) for r in c)) if c else None)
for r in c[:6]: print('  ', r)
