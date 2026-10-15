import sys, json, gzip
from collections import Counter
w = json.load(gzip.open(sys.argv[1])); R = json.load(open(sys.argv[2]))['rows']
v = w['report']['v']
def tgt_of(h):
    for e in w['B']:
        if e[0] == 'add' and e[2] == h and v <= e[1] < 2 * v: return e[1]
secs = ('precondition', 'compensation', 'A', 'cut')
bad = Counter(); detail = {}
for r in R:
    h = r['h']; t = tgt_of(h); hits = []
    for sec in secs:
        for e in w[sec]:
            if e[0] == 'add' and e[2] == t: hits.append((sec, 'read', e[1]))
            if e[0] == 'scale' and e[1] == t: hits.append((sec, 'scale', e[2:4]))
    # B before the read
    for i, e in enumerate(w['B']):
        if e[0] == 'add' and e[2] == h and e[1] == t: break
        if e[0] == 'add' and e[2] == t: hits.append(('B', 'read', e[1]))
        if e[0] == 'scale' and e[1] == t: hits.append(('B', 'scale', e[2:4]))
    detail[h] = dict(target=t, hits=hits[:6], nhits=len(hits))
    bad[len(hits) > 0] += 1
print('hostees with target transformed before the read:', dict(bad))
print({h: d for h, d in list(detail.items())[:5]})
print('sections sizes', {s: len(w[s]) for s in secs}, 'scale gates in B', sum(1 for e in w['B'] if e[0] == 'scale'))
