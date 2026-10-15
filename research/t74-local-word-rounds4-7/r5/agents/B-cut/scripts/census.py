"""census.py: classify B gates of a word by register kinds; find B gates that read a centre into a target and could move
to the (frame-free) cut, i.e. commute back to the start of B.  usage: census.py WORD.json.gz"""
import json, gzip, sys, collections
V = 112
w = json.load(gzip.open(sys.argv[1]))
cent = set(w['centers'])
def kind(r): return 'data' if r < V else 'target' if r < 2 * V else 'helper'
B = w['B']
cls = collections.Counter()
for g in B:
    if g[0] == 'scale': cls[('scale', kind(g[1]))] += 1
    else: cls[(kind(g[1]), kind(g[2]))] += 1
print('B classes (target<-source):', dict(sorted(cls.items(), key=lambda x: -x[1])))
# A section kinds
clsA = collections.Counter((g[0], kind(g[1]), kind(g[2]) if g[0] == 'add' else '-') for g in w['A'])
print('A classes:', dict(sorted(clsA.items(), key=lambda x: -x[1])))
print('A gates with empty frame:', sum(1 for g in w['A'] if not g[-1]), 'of', len(w['A']))
# centres in B
cr = collections.Counter(); cw = collections.Counter()
for g in B:
    if g[0] == 'add' and g[2] in cent: cr[(g[2], kind(g[1]))] += 1
    if g[1] in cent: cw[(g[1], g[0])] += 1
print('B reads of centres (centre, target kind):', dict(cr))
print('B writes/scales of centres:', dict(cw))
# movable to cut: B gate t += c*x, x centre, t target; no earlier B gate writes/scales x, reads t, or scales t
cands = []
for j, g in enumerate(B):
    if g[0] != 'add' or g[2] not in cent or not (V <= g[1] < 2 * V): continue
    t, x = g[1], g[2]; ok = True; why = None
    for h in B[:j]:
        if h[0] == 'scale':
            if h[1] in (t, x): ok = False; why = ('scale', h[1]); break
        else:
            if h[1] == x: ok = False; why = ('writes x', h); break
            if h[2] == t: ok = False; why = ('reads t', h); break
    cands.append(dict(j=j, gate=g, movable=ok, why=str(why)))
print('centre->target B reads:', len(cands), 'movable to cut:', sum(c['movable'] for c in cands))
for c in cands[:12]: print('  ', c)
