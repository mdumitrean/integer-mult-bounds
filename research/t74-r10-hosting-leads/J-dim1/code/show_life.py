import sys, json
sys.path.insert(0, sys.argv[1])
from bounds import Bounds, regs
b = Bounds(sys.argv[2]); Wd = b.Wd; w = Wd.w; v = Wd.v; ev = b.ev
def cls(q): return 'S' if q < v else 'T' if q < 2 * v else 'H'
for h in map(int, sys.argv[3].split(',')):
    print('helper', h, 'start', Wd.start[h], 'end dim', len(Wd.end[h]))
    for x in b.byreg[h][:12]:
        t = x[0]; sec, e = ev[t]
        if x[1] == 'warp': print('  ', t, sec, 'WARP', e); continue
        ops = [(q, cls(q)) for q in regs(e)]
        print('  ', t, sec, e[0], ops, 'coef', e[3] if e[0] == 'add' else e[2], 'frame', len(Wd.gateframe[t]), 'lo', len(b.lo[t]), 'hi', len(b.hi[t]))
    print('   total events', len(b.byreg[h]))
