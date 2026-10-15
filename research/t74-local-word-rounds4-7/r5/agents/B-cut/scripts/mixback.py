"""mixback.py: target-only B gates (mixes/scales) that commute back to the start of B, where targets are still at frame 0
(their cut level is empty), and how far back each one commutes.  usage: mixback.py WORD.json.gz OUT.json"""
import json, gzip, sys, collections
V = 112
w = json.load(gzip.open(sys.argv[1])); B = w['B']
isT = lambda r: V <= r < 2 * V
def commute(g1, g2):
    if g1[0] == 'scale' and g2[0] == 'scale': return True
    if g1[0] == 'scale': return g1[1] not in (g2[1], g2[2])
    if g2[0] == 'scale': return g2[1] not in (g1[1], g1[2])
    return g1[1] != g2[2] and g2[1] != g1[2]
out = []; dist = collections.Counter()
for j, e in enumerate(B):
    if not (isT(e[1]) and (e[0] == 'scale' or isT(e[2]))): continue
    k = j
    while k > 0 and commute(e, B[k - 1]): k -= 1
    # first earlier gate it fails to commute with, and whether that gate is a delivery (non-target source) or a mix
    blocker = B[k - 1] if k > 0 else None
    kind = None if blocker is None else ('mix' if isT(blocker[1]) and (blocker[0] == 'scale' or isT(blocker[2])) else 'delivery' if isT(blocker[1]) else 'other')
    out.append(dict(j=j, gate=e, back_to=k, blocker_kind=kind)); dist['to_B0' if k == 0 else kind] += 1
res = dict(word=sys.argv[1].split('/')[-1], target_only_gates=len(out), stops=dict(dist), to_start=[o for o in out if o['back_to'] == 0])
json.dump(res, open(sys.argv[2], 'w'), indent=1); print({k: v for k, v in res.items() if k != 'to_start'}, 'to_start:', len(res['to_start']))
