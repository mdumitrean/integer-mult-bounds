"""blocks.py (agent Q-blocks, r6): catalogue runs of consecutive large-deletion gates (A and B) on the 566+554 base word.
Classes come from r3 A-extra's single-deletion relaxations (extra word; r3 A showed both words share the program and the
same per-deletion profile changes).  usage: blocks.py OUT.json"""
import gzip, json, os, sys, collections
SCR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
R3A = os.path.join(SCR, 'r3', 'agents', 'A-extra', 'out')
W = json.load(gzip.open(os.path.join(SCR, 'r3', 'inputs', 'gauge44-word-566-554.json.gz')))
BIG = -9592
out = {}
for sec, fn in (('A', 'relaxA-extra.json'), ('B', 'relax-extra.json')):
    res = json.load(open(os.path.join(R3A, fn)))['results']
    d = {int(k): v.get('delta') for k, v in res.items() if isinstance(v, dict)}
    big = {i: x for i, x in d.items() if isinstance(x, (int, float)) and x <= BIG}
    gates = W[sec]
    # maximal runs of consecutive indices, same class
    runs_same = []; runs_any = []
    for runs, key in ((runs_same, lambda i: big[i]), (runs_any, lambda i: 'big')):
        cur = []
        for i in sorted(big):
            if cur and i == cur[-1] + 1 and key(i) == key(cur[-1]): cur.append(i)
            else:
                if cur: runs.append(cur)
                cur = [i]
        if cur: runs.append(cur)
    def desc(r):
        gs = [gates[i][:5] if gates[i][0] == 'add' else gates[i][:4] for i in r]
        regs = sorted({x for g in gs for x in (g[1:3] if g[0] == 'add' else g[1:2])})
        return dict(start=r[0], end=r[-1], n=len(r), classes=sorted({big[i] for i in r}), sum_single=sum(big[i] for i in r), gates=gs, regs=regs)
    out[sec] = dict(n_big=len(big), class_counts=dict(collections.Counter(big.values())),
                    same_class_runs=[desc(r) for r in runs_same if len(r) >= 2], linked_runs=[desc(r) for r in runs_any if len(r) >= 2])
    rs = out[sec]['same_class_runs']; ls = out[sec]['linked_runs']
    print(sec, 'big gates', len(big), '| same-class runs >= 2:', len(rs), collections.Counter(r['n'] for r in rs), '| linked runs >= 2:', len(ls), collections.Counter(r['n'] for r in ls))
json.dump(out, open(sys.argv[1], 'w'), indent=1)
