"""bfront.py: B gates that can commute back (within B, not past the cut) to a position where both registers are still at
frame 0 (zero start, cut level 0 for targets, and no nonzero-frame event on them in A or earlier in B).  Such a gate could run
at frame 0 there.  usage: bfront.py WORD.json.gz OUT.json"""
import json, gzip, sys, collections
V = 112
w = json.load(gzip.open(sys.argv[1])); A, B = w['A'], w['B']
def regs(e): return [e[1]] + ([e[2]] if e[0] == 'add' else [])
def commute(g1, g2):
    if g1[0] == 'scale' and g2[0] == 'scale': return True
    if g1[0] == 'scale': return g1[1] not in (g2[1], g2[2])
    if g2[0] == 'scale': return g2[1] not in (g1[1], g1[2])
    return g1[1] != g2[2] and g2[1] != g1[2]
zero_start = lambda r: (V <= r < 2 * V) or (r >= 2 * V and str(r) not in w['start_extra'])
climbed_in_A = {r for e in A if e[-1] for r in regs(e)}
centres = set(w['centers'])
first_nonzero_B = {}
for i, e in enumerate(B):
    if e[-1]:
        for r in regs(e): first_nonzero_B.setdefault(r, i)
c = collections.Counter(); cands = []
for i, e in enumerate(B):
    rs = regs(e)
    if not all(zero_start(r) and r not in climbed_in_A and r not in centres for r in rs): c['register above frame 0 at B start'] += 1; continue
    k = i
    while k > 0 and commute(e, B[k - 1]): k -= 1
    if all(first_nonzero_B.get(r, 10 ** 9) >= k for r in rs): cands.append(dict(i=i, to=k, gate=e)); c['candidate'] += 1
    else: c['blocked'] += 1
res = dict(word=sys.argv[1].split('/')[-1], counts=dict(c), candidates=cands)
json.dump(res, open(sys.argv[2], 'w'), indent=1); print(res['counts'], cands[:6])
