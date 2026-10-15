"""lucore: non-raising copy of frames.Graph's L/U propagation (same semantics: tail_mutable=True, caps, cut_equality),
returning nodes, chains, prev/nxt, lower, upper and the list of violated vertices."""
import sys, os
from common import *
def lu(w_inline, caps):
    w = w_inline; R = F.R_of(w); N = 2 * F.V + R
    nodes = []; chains = [[] for _ in range(N)]; mutable = set()
    start_frames = w.get("_start_frames"); final_frames = w.get("_final_frames"); tail = w.get("_tail", [])
    def node(regs, Fr, sec, index=None):
        k = len(nodes); nodes.append((tuple(regs), F.basis(tuple(Fr)), sec, index))
        for r in regs: chains[r].append(k)
        if sec in ("A", "B", "tail"): mutable.add(k)
    for r in range(N): node([r], start_frames[r], "start")
    for sec in ("A", "B"):
        if sec == "B":
            for r, Fr in zip(w["centers"], w["center_frames"]): node([r], Fr, "cut")
            for t in range(F.V): node([F.V + t], w.get("target_levels", {}).get(str(t), []), "cut")
        for i, e in enumerate(w[sec]): node(F.regs_of(e), e[-1], sec, i)
    for i, e in enumerate(tail): node(F.regs_of(e), e[-1], "tail", i)
    for r in range(N): node([r], final_frames[r], "end")
    prev = {}; nxt = {}
    for r, ch in enumerate(chains):
        for p, q in zip(ch, ch[1:]): prev[q, r] = p; nxt[p, r] = q
    lower = {}; upper = {}
    for k, (regs, F0, sec, idx) in enumerate(nodes):
        lower[k] = F.basis(tuple(x for r in regs for x in lower[prev[k, r]])) if k in mutable else F0
        if k in mutable and sec == "A":
            for r in regs:
                j = nxt.get((k, r))
                if j is not None and nodes[j][2] == "cut": lower[k] = F.basis(tuple(lower[k]) + tuple(nodes[j][1]))
    bad = []
    for k in reversed(range(len(nodes))):
        regs, F0, sec, idx = nodes[k]
        if k in mutable:
            U = set(F.span(F.FULL))
            for r in regs: U.intersection_update(F.span(upper[nxt[k, r]]))
            for r in regs:
                if r in caps and nodes[nxt[k, r]][2] in ("tail", "end"): U.intersection_update(F.span(caps[r]))
            upper[k] = F.basis(tuple(U))
            if not F.leq(lower[k], upper[k]): bad.append(k)
        else:
            upper[k] = F0
            if not F.leq(lower[k], F0): bad.append(k)
    return dict(nodes=nodes, chains=chains, prev=prev, nxt=nxt, lower=lower, upper=upper, bad=bad)
def describe(w1, res, k):
    n = res['nodes'][k]; sec, idx = n[2], n[3]
    if sec == 'B': g = w1['B'][idx][:5]
    elif sec == 'tail': g = w1['cleanup'][w1['early_cleanup'][idx][0]][:5]
    elif sec == 'A': g = w1['A'][idx][:5]
    else: g = n[0]
    return f'{sec}{idx} {g}'
def excess(L, U):
    """vectors of a basis of L not in span(U)."""
    su = F.span(tuple(U)); return [x for x in L if x not in su]
