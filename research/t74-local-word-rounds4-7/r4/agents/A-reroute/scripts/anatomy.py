"""anatomy: structure of the 13 never-written copy-window pivots in the base word (A/cut writes and reads, B reads,
tail/cleanup gates, q's value at the cut, q's B+tail column)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
w = load(sys.argv[1] if len(sys.argv) > 1 else 'base')
A, C, B, CL = w['A'], w['cut'], w['B'], w['cleanup']
tail = [CL[i] for i, U in w['early_cleanup']]; early_idx = {i for i, U in w['early_cleanup']}
print('sections', {k: len(w[k]) for k in ('precondition', 'A', 'cut', 'B', 'cleanup')}, 'early', len(w['early_cleanup']), 'R', w['report']['R'])
rowsAC = apply_rows(A + C)
out = {}
for q in PIVOTS:
    aw = [(i, g[:5]) for i, g in enumerate(A) if g[1] == q]; ar = [(i, g[:5]) for i, g in enumerate(A) if g[0] == 'add' and g[2] == q]
    cw = [(i, g[:5]) for i, g in enumerate(C) if g[1] == q]; cr = [(i, g[:5]) for i, g in enumerate(C) if g[0] == 'add' and g[2] == q]
    bw = [(i, g[:5]) for i, g in enumerate(B) if g[1] == q]; br = [(i, g[:5]) for i, g in enumerate(B) if g[0] == 'add' and g[2] == q]
    tq = [(j, g[:5]) for j, g in enumerate(tail) if q in regs(g)]
    clq = [(i, g[:5], i in early_idx) for i, g in enumerate(CL) if q in regs(g)]
    pre = [(i, g[:5]) for i, g in enumerate(w['precondition']) if q in regs(g)]
    val = rowsAC.get(q, {q: Q(1)})
    out[q] = dict(A_writes=aw, A_reads=ar, cut_writes=cw, cut_reads=cr, B_writes=bw, B_reads=br, tail=tq, cleanup=clq, pre=pre,
                  value_at_cut={str(k): str(v) for k, v in sorted(val.items())}, start_extra=w['start_extra'].get(str(q)), helper_final=w['helper_final'].get(str(q)))
    print(f"q={q}: A writes {len(aw)} {aw[:3]}{'...' if len(aw)>3 else ''} | A reads {len(ar)} | cut w/r {len(cw)}/{len(cr)} | B writes {len(bw)} | B reads {len(br)} -> targets {[g[1] for i,g in br]} at {[i for i,g in br]} coefs {[str(coef(g)) for i,g in br]}")
    print(f"     value at cut: {out[q]['value_at_cut']} | tail {tq} | cleanup {[(i, g, e) for i, g, e in clq][:4]} | pre {pre[:2]} | start_extra {out[q]['start_extra']} helper_final {out[q]['helper_final']}")
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'ANATOMY-' + (sys.argv[1] if len(sys.argv) > 1 else 'base') + '.json'), 'w'), indent=1, default=str)
