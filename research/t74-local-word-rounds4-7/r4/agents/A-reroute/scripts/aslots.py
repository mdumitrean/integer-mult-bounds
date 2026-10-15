"""aslots: per pivot, why A-window delivery fails: q's frame at its last A vertex in the deleted word (lower/upper),
each dp port's cut target level, and the feasibility of a direct q-meet at every A-window slot of each dp coordinate."""
import sys, os, json, bisect
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from awin import *
wname = sys.argv[1]; qs = list(map(int, sys.argv[2:])); out = {}
for q in qs:
    aw = AWin(wname, q); w = aw.w; nA = aw.nA
    w1 = H.compile_edits(w, dict(delete=aw.Breads)); caps1, comp1 = cone_caps(w1)
    res = lu(inline(w1, True), caps1); nodes, chains, lower, upper = res['nodes'], res['chains'], res['lower'], res['upper']
    seq0B = list(w['B']) + aw.tail; seq1B = list(w1['B']) + [w1['cleanup'][i] for i, U in w1['early_cleanup']]
    d = sx.addv(sx.col(seq0B, q), sx.col(seq1B, q), -1); dp = sorted(k for k in d if not aw.full_end(k))
    qA = [k for k in chains[q] if nodes[k][2] == 'A']; qlast = qA[-1]
    sp = lambda X: set(F.span(tuple(X)))
    rec = dict(q=q, q_last_A=nodes[qlast][3], q_lower=list(lower[qlast]), q_upper=list(upper[qlast]), ports={})
    for y in dp:
        ch = chains[y]; cutn = [k for k in ch if nodes[k][2] == 'cut']
        tl = list(nodes[cutn[0]][1]) if cutn else None
        # A-window slots: positions after q's last A write where y has an A vertex boundary
        Aks = [k for k in ch if nodes[k][2] == 'A' and nodes[k][3] > aw.lastW]
        feas = 0; tried = 0
        for p in sorted(set([aw.lastW + 1] + [nodes[k][3] + 1 for k in Aks] + [nA])):
            r = None
            ts = []
            for k in ch:
                sec, idx = nodes[k][2], nodes[k][3]
                ts.append(-1 if sec == 'start' else idx if sec == 'A' else nA + 0.5 if sec == 'cut' else 10 ** 7)
            j = bisect.bisect_left(ts, p); a, b = ch[j - 1], ch[j]
            Lnew = F.basis(tuple(lower[a]) + tuple(lower[qlast]))
            if nodes[b][2] == 'cut': Lnew = F.basis(tuple(Lnew) + tuple(nodes[b][1]))
            ok = sp(Lnew) <= sp(upper[b]); tried += 1; feas += ok
        q_in_tl = (sp(lower[qlast]) <= sp(tl)) if tl is not None else None
        rec['ports'][y] = dict(cut_target_level=tl, q_lower_inside_target_level=q_in_tl, A_window_vertices=len(Aks), slots_tried=tried, slots_feasible=feas)
        print(q, 'dp', y, 'cut level', tl, '| q lower inside it:', q_in_tl, '| A-window vertices', len(Aks), '| direct-meet slots feasible', feas, '/', tried, flush=True)
    out[q] = rec
json.dump(out, open(os.path.join(HERE, '..', 'out', f'ASLOTS-{wname}.json'), 'w'), indent=1, default=str)
