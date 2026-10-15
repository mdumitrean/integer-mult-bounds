"""holders.py: candidate copy holders c for helper q (copy c += q in A before q's first write; subtract q -= c after t1).
Reports, per helper c: frame at t0 (just before q's first write), frame at t1 (just after q's write at B-index t1),
reads of c in [t0, end of program), writes of c in (t1, end of B], and the dim of c's next vertex frames."""
import json, sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import traj as TJ
w = TJ.load(sys.argv[1]); q = int(sys.argv[2]); T1B = int(sys.argv[3]); OUT = sys.argv[4]
v = w['report']['v']; R = w['report']['R']
seq, T = TJ.trajectories(w)
posA0 = next(p for p, s, i, role, o, fr in T[q] if role == 'write')       # q's first write
posB = {(s, i): p for p, (s, i, g, fr) in enumerate(seq)}
t1 = posB[('B', T1B)]
endB = max(p for p, (s, i, g, fr) in enumerate(seq) if s == 'B')
def frame_before(r, pos):
    f = []
    for p, s, i, role, o, fr in T.get(r, []):
        if p >= pos: break
        if fr is not None: f = fr
    return f
def nxt(r, pos):
    for p, s, i, role, o, fr in T.get(r, []):
        if p > pos and fr is not None: return (p, s, i, fr)
    return None
start_extra = set(map(int, w['start_extra'])); lowends = set(map(int, w['helper_final']))
res = []
for c in range(2 * v, 2 * v + R):
    if c == q or c in start_extra or c in lowends: continue
    tr = T.get(c, [])
    reads_after = [(p, s, i, o) for p, s, i, role, o, fr in tr if role == 'read' and p >= posA0]
    writes_t1_endB = [(p, s, i, o) for p, s, i, role, o, fr in tr if role == 'write' and t1 < p <= endB]
    f0 = frame_before(c, posA0); f1 = frame_before(c, t1 + 1)
    res.append(dict(c=c, f0=f0, f1=f1, next0=nxt(c, posA0 - 1), next1=nxt(c, t1), n_reads_after=len(reads_after),
                    first_reads_after=reads_after[:3], n_writes_t1_endB=len(writes_t1_endB)))
json.dump(dict(q=q, posA0=posA0, t1=t1, qframe_t0=frame_before(q, posA0), qframe_t1=frame_before(q, t1 + 1), holders=res), open(OUT, 'w'), indent=0)
ok = [r for r in res if r['n_reads_after'] == 0]
print('q', q, 'first write pos', posA0, 't1 pos', t1, '| helpers with no reads after t0:', len(ok))
for r in ok[:20]: print('  ', r['c'], 'f0', r['f0'], 'f1', r['f1'], 'next0', r['next0'], 'writes(t1,endB]', r['n_writes_t1_endB'])
