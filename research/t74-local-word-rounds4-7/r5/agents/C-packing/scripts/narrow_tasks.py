"""Candidate one-level start-side narrowings of width-7/8/9 helpers: start frame += a vector of the helper's first stored frame."""
import collections, json, os, sys
TK = sys.argv[1]; sys.path.insert(0, TK); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word as Wd, wcore as K
w = K.load(sys.argv[2]); paid, centre, widths, starts, ends, endB = Wd.recount(w)
v, R = w['report']['v'], w['report']['R']
first = {}
for sec in ('A', 'cut', 'B'):
    for i, g in enumerate(w[sec]):
        t = g[1]
        if t not in first and g[-1]: first[t] = (sec, i, list(g[-1]))
T = []; stat = collections.Counter()
for q in range(2 * v, 2 * v + R):
    wd = widths[q - 2 * v]
    if wd not in (7, 8, 9): continue
    sv = list(w['start_extra'].get(str(q), []))
    if q not in first: stat['no-first-frame', wd] += 1; continue
    sec, i, F1 = first[q]; base = K.echelon(sv); seen = set()
    span = [0]
    for b in K.echelon(F1).values(): span += [x ^ b for x in span]
    for x in span:
        r = K.reduce_vec(x, base)
        if not r: continue
        key = tuple(sorted(K.echelon(sv + [x]).values()))
        if key in seen: continue
        seen.add(key); T.append((q, wd, sorted(sv + [x]), sec, i))
    stat['helpers', wd] += 1; stat['first-dim', wd, len(K.echelon(F1)) - len(base)] += 1
print('tasks', len(T), dict(stat))
json.dump(T, open(sys.argv[3], 'w'))
