"""Start-side one-level narrowings of width-4 helpers (types (4,0,4) and (4,5,9)): start frame -> every superspace inside the end frame."""
import collections, json, os, sys
TK = sys.argv[1]; sys.path.insert(0, TK); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word as Wd, wcore as K
w = K.load(sys.argv[2]); paid, centre, widths, starts, ends, endB = Wd.recount(w); v, R = w['report']['v'], w['report']['R']
T = []; stat = collections.Counter()
for q in range(2 * v, 2 * v + R):
    if widths[q - 2 * v] != 4: continue
    sv = list(w['start_extra'].get(str(q), [])); ev = list(w['helper_final'].get(str(q), [])) or [1 << i for i in range(9)]
    base = K.echelon(sv); endspan = [0]
    for b in K.echelon(ev).values(): endspan += [x ^ b for x in endspan]
    seen = set()
    for x in endspan:
        if not K.reduce_vec(x, base): continue
        key = tuple(sorted(K.echelon(sv + [x]).values()))
        if key in seen: continue
        seen.add(key); T.append((q, 4, sorted(sv + [x]), 'start', 0))
    stat[(Wd.dimension(starts[q]), Wd.dimension(ends[q]))] += 1
print('tasks', len(T), dict(stat)); json.dump(T, open(sys.argv[3], 'w'))
