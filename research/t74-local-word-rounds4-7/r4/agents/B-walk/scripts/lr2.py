"""lr2: two-step local re-search on neutral pre-moves (base word).
For a pre-move N (W0-relative edit): W1 = N(W0) with its own exact optimal frames (Pricer, check_literal off), then
 (a) deletion relaxation on W1 of every kernel-sized read (W0 band -8,879..-3,000) whose registers N touches, against W0;
 (b) second moves on W1 near N: compensated single-crossing re-timings (r3 D's generator) and read fusions (toolkit
     fusion.py) touching N's registers, priced exactly by the harness on W1 (screen, static rules, unchanged compensation).
usage: lr2.py SEL.json OUT.jsonl [--max2 40]; 3 workers, pricing deadlines, 6 GiB RSS watchdog, maxtasksperchild."""
import json, os, sys, time, threading, multiprocessing as mp
sys.path.insert(0, os.path.dirname(__file__)); import common
import harness as Hm, frames as F, fusion as G
from word import inline
from compat import deadline, Timeout
sys.path.insert(0, os.path.join(common.R3, 'agents', 'D-families', 'scripts'))
import gen_cmove as GC
MAX2 = int(sys.argv[sys.argv.index('--max2') + 1]) if '--max2' in sys.argv else 40
W0 = None; C0 = None; RELAX0 = None; KB = None
def watchdog():
    import resource
    while True:
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 6 * 1024 ** 3: os._exit(3)
        time.sleep(1)
def init():
    global W0, C0, RELAX0, KB
    threading.Thread(target=watchdog, daemon=True).start()
    W0 = common.load('base'); C0 = Hm.Pricer(W0, b=os.environ['IMB_B'], check_literal=True).base_cost
    r = json.load(open(os.path.join(common.R3, 'agents', 'A-extra', 'out', 'relax-extra.json')))['results']
    RELAX0 = {int(k): v['delta'] for k, v in r.items()}; KB = {i for i, d in RELAX0.items() if -8879 <= d <= -3000}
def regs_of(e): return set(e[1:3]) if e[0] == 'add' else {e[1]}
def nregs(ed):
    s = set()
    for i in ed['delete']: s |= regs_of(W0['B'][i])
    for _, g in ed['insert'] + ed['tail']: s |= regs_of(g)
    return s
def mapidx(ed, i):
    if i in set(ed['delete']): return None
    return i - sum(1 for d in ed['delete'] if d < i) + sum(1 for p, _ in ed['insert'] if p <= i)
def relax(P1, w1, j):
    w2 = Hm.compile_edits(w1, dict(delete=[j]))
    try:
        with deadline(90):
            g = F.Graph(inline(w2, True), check_literal=False, tail_mutable=True, caps=P1.caps, cut_equality=True)
            r = F.optimal_frames(inline(w2, True), P1.costs, check_literal=False, graph=g)
        return r['cost'] - P1.base_cost
    except F.Infeasible: return 'infeasible'
    except Timeout: return 'timeout'
def run(N):
    t0 = time.time(); ed = N['ed']; out = dict(id=N['id'], src=N['src'])
    try:
        w1 = Hm.compile_edits(W0, ed)
        with deadline(300): P1 = Hm.Pricer(w1, b=os.environ['IMB_B'], check_literal=False)
    except Exception as e: out['w1'] = repr(e)[:100]; return out
    out['delta1'] = P1.base_cost - C0; R = nregs(ed); out['regs'] = sorted(R)
    # (a) relaxation of kernel-sized reads touching R
    rel = []
    for i in sorted(KB):
        if not (regs_of(W0['B'][i]) & R): continue
        j = mapidx(ed, i)
        if j is None: continue
        d1 = relax(P1, w1, j); rel.append([i, RELAX0[i], d1])
    out['relax'] = rel
    # (b) second moves near N on W1
    B1 = w1['B']; pos = sorted(set(ed['delete']) | {p for p, _ in ed['insert']}) or [0]
    cands = []
    for c in GC.gen(w1):
        g = B1[c['g']]; h = B1[c['h']]
        if (regs_of(g) | regs_of(h)) & R: cands.append(('cmove:' + c['id'], c['ed'], min(abs(c['g'] - p) for p in pos)))
    I = G.index(w1)
    for c in G.candidates(w1, I):
        if {c['t'], c['A'], c['H']} & R:
            e2 = c['ed']; cands.append((f"fusion:t{c['t']}A{c['A']}H{c['H']}p{c['p']}{c.get('rest','')}", e2, min(abs(c['iA'] - p) for p in pos)))
    cands.sort(key=lambda x: x[2]); out['n2_all'] = len(cands); res = []
    for cid, e2, _ in cands[:MAX2]:
        for k in ('delete', 'insert', 'tail', 'prepend'): e2.setdefault(k, [])
        r = P1.price(e2, timeout=90); r.pop('word', None)
        d2 = r.get('delta'); res.append([cid, r.get('status'), d2])
    out['second'] = res; out['seconds'] = round(time.time() - t0, 1)
    return out
if __name__ == '__main__':
    sel = json.load(open(sys.argv[1])); outp = sys.argv[2]; done = set()
    if os.path.exists(outp):
        for l in open(outp):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    todo = [s for s in sel if s['id'] not in done]; print(len(todo), 'pre-moves to re-search', flush=True); t0 = time.time(); n = 0
    with mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=8) as pool, open(outp, 'a') as f:
        for r in pool.imap_unordered(run, todo, chunksize=1):
            f.write(json.dumps(r) + '\n'); f.flush(); n += 1
            gains = [x for x in r.get('second', []) if x[2] is not None and r.get('delta1') is not None and r['delta1'] + x[2] < 0]
            better = [x for x in r.get('relax', []) if isinstance(x[2], int) and x[2] < x[1]]
            if gains: print('  GAIN', r['id'], r.get('delta1'), gains[:5], flush=True)
            if n % 10 == 0 or better: print(f"  {n}/{len(todo)} {time.time()-t0:.0f}s {r['id'][:50]} d1={r.get('delta1')} relax-better={better[:3]} n2={r.get('n2_all')}", flush=True)
    print(f'done {n} in {time.time()-t0:.0f}s', flush=True)
