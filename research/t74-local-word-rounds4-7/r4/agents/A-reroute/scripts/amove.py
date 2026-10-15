"""amove: exact commuting re-timings of A-section gates around the copy-window pivots (r4 A-reroute).
A gate g moves past gates it commutes with (add t+=cs commutes with add u+=c'v iff t!=v and u!=s; with scale u iff
u not in {t,s}).  Only crossings of gates that share a register with g change any chain order, so the candidate
positions are 'just past each commuting gate on g's registers' inside g's commutation window.  The A map, hence the
derived compensation and the whole call map, are unchanged (checked anyway); frames are re-solved exactly.
usage: amove.py WORD LO HI [LO HI ...]   (A index ranges of gates to move)"""
import sys, os, json, time, collections, resource
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from awin import *
wname = sys.argv[1]; rngs = [(int(a), int(b)) for a, b in zip(sys.argv[2::2], sys.argv[3::2])]
P = H.Pricer(WORDS[wname], b=os.environ['IMB_B'], check_literal=True); w = P.base; A = w['A']; nA = len(A)
caps0, comp0 = cone_caps(w); map0 = apply_rows(prog(w, comp0))
def commute(g, h):
    if g[0] == 'add' and h[0] == 'add': return g[1] != h[2] and h[1] != g[2]
    if g[0] == 'add' and h[0] == 'scale': return h[1] not in (g[1], g[2])
    if g[0] == 'scale' and h[0] == 'add': return g[1] not in (h[1], h[2])
    return True   # two scales (same register: scalars commute; different: independent)
def shares(g, h): return bool(set(regs(g)) & set(regs(h)))
def move(i, j):
    """move A gate i to sit just before position j (j in [0, nA], j != i, i+1)."""
    A1 = [list(e[:-1]) + [list(e[-1]) if e[-1] is not None else []] for e in A]
    g = A1.pop(i); g = g[:-1] + [[]]
    jj = j if j < i else j - 1
    A1.insert(jj, g); w1 = dict(w); w1['A'] = A1; return w1
recs = []; t0 = time.time()
for lo, hi in rngs:
    for i in range(lo, min(hi, nA)):
        g = A[i]
        # window forward
        pos = []
        k = i + 1
        while k < nA and commute(g, A[k]):
            if shares(g, A[k]): pos.append(k + 1)
            k += 1
        k = i - 1
        while k >= 0 and commute(g, A[k]):
            if shares(g, A[k]): pos.append(k)
            k -= 1
        for j in sorted(set(pos)):
            w1 = move(i, j)
            m1 = apply_rows(prog(w1, cone_caps(w1)[1]))
            exact = all(map0.get(r, {r: Q(1)}) == m1.get(r, {r: Q(1)}) for r in set(map0) | set(m1))
            pr = price(w1, P.costs, P.base_cost, timeout=120) if exact else dict(status='inexact')
            recs.append(dict(gate=i, g=g[:5], to=j, exact=exact, price=pr))
            if (pr.get('delta') or 0) < 0: print('  GAIN', i, g[:5], '->', j, pr, flush=True)
    print(f'range {lo}-{hi}: {len(recs)} candidates so far, {time.time()-t0:.0f}s', flush=True)
st = collections.Counter((r['price'].get('status'), (r['price'].get('delta') or 0) > 0, (r['price'].get('delta') or 0) < 0) for r in recs)
print('done', len(recs), dict(st), 'rss %.2fGiB' % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3), flush=True)
json.dump(recs, open(os.path.join(HERE, '..', 'out', f'AMOVE-{wname}-' + '_'.join(f'{a}-{b}' for a, b in rngs) + '.json'), 'w'), default=str)
