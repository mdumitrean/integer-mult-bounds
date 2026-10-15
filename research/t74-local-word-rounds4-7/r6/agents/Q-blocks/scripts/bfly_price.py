"""bfly_price.py (agent Q-blocks, r6): price the butterfly-to-cleanup rewrite.  For a B butterfly (a += c1 b; b += c2 a)
whose outputs are only delivered into ports afterwards (bfly_scan.py), delete the butterfly and its deliveries, re-deliver
each port from the pre-butterfly values (P += d a' -> P += d a, P += d c1 b; P += d b' -> P += d c2 a, P += d (1+c1 c2) b),
and prepend the butterfly to the frame-free cleanup so the cleanup sees the same state.  Exact by construction; the rev3
harness re-checks static rules, the exact B+tail+prepend map, the derived compensation and prices certified frames with
true-moment intervals.  usage: bfly_price.py WORD SCAN.json OUT.json [POS ...]"""
import gzip, json, os, sys, time
from fractions import Fraction as Fr
SCR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r3', 'toolkit-rev3'))
import harness as H
word, scan_p, out_p = sys.argv[1:4]; only = set(map(int, sys.argv[4:]))
W = json.load(gzip.open(word)); scan = [s for s in json.load(open(scan_p)) if s['ok'] and (not only or s['pos'] in only)]
P = H.Pricer(word, b='0.001679754956125544', check_literal=True, interval=True); res = []
print('base', P.base_cost, flush=True)
def gate(t, s, c): c = Fr(c); return ['add', t, s, c.numerator, c.denominator, []]
for s in scan:
    t0 = time.time(); i = s['pos']; a, b = s['a'], s['b']
    c1 = Fr(s['g1'][3], s['g1'][4]); c2 = Fr(s['g2'][3], s['g2'][4])
    ed = dict(delete=[i, i + 1], insert=[], prepend=[list(s['g1'][:5]) + [[]], list(s['g2'][:5]) + [[]]])
    for j, g in s['deliveries']:
        P_, src, d = g[1], g[2], Fr(g[3], g[4]); ed['delete'].append(j)
        if src == a: terms = [(a, d), (b, d * c1)]
        else: terms = [(a, d * c2), (b, d * (1 + c1 * c2))]
        for r, c in terms:
            if c: ed['insert'].append((j, gate(P_, r, c)))
    try: pr = P.price(ed, timeout=300)
    except Exception as e: pr = dict(status='error:' + repr(e)[:120])
    pr = {k: v for k, v in pr.items() if k != 'word'}; pr['seconds'] = round(time.time() - t0, 1)
    res.append(dict(pos=i, a=a, b=b, edit=ed, price=pr)); json.dump(res, open(out_p, 'w'), default=str)
    print(i, a, b, pr.get('status'), pr.get('delta'), pr.get('profile'), pr['seconds'], flush=True)
print('done', len(res), flush=True)
