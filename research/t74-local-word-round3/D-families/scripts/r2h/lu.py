"""lu: L/U bounds along chains of chosen registers in a (possibly uncompensated) edited word, base caps.
usage: lu.py WORD 'edit json' q regs"""
import sys, os, json
S = os.environ['S']; TK = S + '/latest/eft/research/exact-frame-toolkit'; sys.path.insert(0, TK)
import harness as H, frames as F
from word import inline
P = H.Pricer(sys.argv[1], check_literal=True)
ed = json.loads(sys.argv[2]); q = int(sys.argv[3]); regs = [int(x) for x in sys.argv[4].split(',')]
w1 = H.compile_edits(P.base, ed)
g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
sp = lambda X: F.span(tuple(X))
def join(a, b): return F.basis(tuple(a) + tuple(b))
def meet(a, b):
    sa = sp(a); return F.basis(tuple(x for x in sp(b) if x in sa))
def leq(a, b): return sp(a) <= sp(b)
def name(k):
    n = g.nodes[k]; sec, idx = n[2], n[3]
    if sec == 'B': return f'B{idx}:{w1["B"][idx][:5]}'
    if sec == 'tail': return f'T{idx}:{w1["cleanup"][w1["early_cleanup"][idx][0]][:5]}'
    return f'{sec}{idx if idx is not None else ""}'
# q chain: lower/upper along it
print('q chain', q)
for k in g.chains[q]: print('   ', name(k), 'L', len(g.lower[k]), list(g.lower[k]), 'U', len(g.upper[k]), list(g.upper[k]))
for x in regs:
    ch = g.chains[x]; print('== reg', x, 'cap', P.caps.get(x))
    for a, b in zip(ch, ch[1:]):
        # q's bounds at this time: find q vertices around time of a/b (approx: use B index)
        print('   gap after', name(a), '| L', len(g.lower[a]), list(g.lower[a]), '| U(next)', len(g.upper[b]), list(g.upper[b]), '| next', name(b))
