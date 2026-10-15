"""End-side one-level narrowings of low-end helpers (types (w,0,w)): helper_final -> each hyperplane of the end frame."""
import collections, json, os, sys
TK = sys.argv[1]; sys.path.insert(0, TK); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word as Wd, wcore as K
w = K.load(sys.argv[2]); paid, centre, widths, starts, ends, endB = Wd.recount(w); v, R = w['report']['v'], w['report']['R']
T = []; stat = collections.Counter()
for q in range(2 * v, 2 * v + R):
    wd = widths[q - 2 * v]; sd = Wd.dimension(starts[q]); ed = Wd.dimension(ends[q])
    if sd == 0 and ed < 9:
        ev = list(w['helper_final'].get(str(q), []))
        for h in K.hyperplanes(ev): T.append((q, wd, h, 'end', 0))
        stat[(wd, sd, ed)] += 1
print('tasks', len(T), dict(stat)); json.dump(T, open(sys.argv[3], 'w'))
