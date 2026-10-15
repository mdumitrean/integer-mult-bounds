"""traj.py: per-register vertex trajectories of a word in program order (A, cut, B, tail, cleanup), auditor semantics.
Each vertex: (pos, sec, idx, role, other, frame) with frame = the gate's stored frame (cut/cleanup: None)."""
import gzip, json
def load(p): return json.load(gzip.open(p))
def program(w):
    early = w.get('early_cleanup', []); eids = {i for i, U in early}
    seq = [('A', i, g, g[-1]) for i, g in enumerate(w['A'])] + [('cut', i, g, None) for i, g in enumerate(w['cut'])] \
        + [('B', i, g, g[-1]) for i, g in enumerate(w['B'])] + [('tail', j, w['cleanup'][i], U) for j, (i, U) in enumerate(early)] \
        + [('clean', i, g, None) for i, g in enumerate(w['cleanup']) if i not in eids]
    return seq
def regs(g): return g[1:3] if g[0] == 'add' else g[1:2]
def trajectories(w):
    seq = program(w); T = {}
    for pos, (sec, i, g, fr) in enumerate(seq):
        rs = regs(g)
        for k, r in enumerate(rs):
            role = 'write' if k == 0 else 'read'
            other = rs[1 - k] if len(rs) == 2 else None
            T.setdefault(r, []).append((pos, sec, i, role, other, fr))
    return seq, T
