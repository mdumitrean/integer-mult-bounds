"""pdprice.py: price compensation-absorbed edits with the #1186 rev3 harness, relaxing ONLY the compensation-equality guard.
Checks per candidate: compile_edits; static program rules (harness.program_violation); exact absorbed-change screen (the
A+cut+B map is unchanged on every non-port row and on every non-ordinary column of the port rows; ordinary = helper, not
entering, not a low end); re-derived compensation obeys the auditor's residual rules (no gate reads an entering helper,
none touches entering or cold-end helpers); cone caps recomputed from the new compensation; exact optimal frames with
interval bounds.  Negative deltas are written back and passed through the unchanged audit_local.py (toolkit audit).
usage: pdprice.py WORD.json.gz CANDS.json OUT.jsonl [--workers 3] [--limit N]"""
import argparse, json, os, sys, time
from fractions import Fraction as Fr
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))          # scratchpad/
TK = os.path.join(SCR, 'r3', 'toolkit-rev3'); sys.path.insert(0, TK)
os.environ.setdefault('IMB_ROOT', os.path.join(SCR, 'r3', 'main'))
os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from word import inline
from model import cone_caps
from compat import deadline, Timeout, peak_rss_gib, pool_context
ap = argparse.ArgumentParser(); ap.add_argument('word'); ap.add_argument('cands'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--timeout', type=int, default=120)
a = ap.parse_args()
P = None; BASE = None
def coef(e): return Fr(e[3], e[4]) if e[0] == 'add' else Fr(e[2], e[3])
def run_rows(seq, rows):
    for e in seq:
        c = coef(e); t = e[1]
        if e[0] == 'scale': rows[t] = {k: x * c for k, x in rows[t].items()}; continue
        d = dict(rows[t])
        for k, x in rows[e[2]].items():
            y = d.get(k, 0) + c * x
            if y: d[k] = y
            else: d.pop(k, None)
        rows[t] = d
    return rows
def init():
    global P, BASE
    P = H.Pricer(a.word, check_literal=True, interval=True)
    w = P.base; V = w['report']['v']; n = 2 * V + w['report']['R']
    ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
    pre = run_rows(w['A'] + w['cut'], [{k: Fr(1)} for k in range(n)])
    main = run_rows(w['B'], [dict(r) for r in pre])
    BASE = dict(V=V, n=n, ent=ent, low=low, cold=low - ent, pre=pre, main=main)
def absorbed(w1):
    V, n = BASE['V'], BASE['n']; ent, low = BASE['ent'], BASE['low']
    rows = run_rows(w1['B'], [dict(r) for r in BASE['pre']])
    nonport_changed = port_hard = port_soft = 0
    for x in range(n):
        if rows[x] == BASE['main'][x]: continue
        if not (V <= x < 2 * V): nonport_changed += 1; continue
        b = BASE['main'][x]; r = rows[x]
        for k in set(b) | set(r):
            if b.get(k, 0) != r.get(k, 0):
                if k >= 2 * V and k not in ent and k not in low: port_soft += 1
                else: port_hard += 1
    return nonport_changed, port_hard, port_soft
def price(c):
    t0 = time.time(); out = dict(c)
    try:
        ed = c['ed'] if 'ed' in c else dict(delete=[c['B']], insert=[(c['p'], ['add', c['t'], c['y'], c['c'][0], c['c'][1], []])])
        ed = dict(delete=list(ed['delete']), insert=[(int(q), list(gg)) for q, gg in ed['insert']])
        w1 = H.compile_edits(P.base, ed)
        why = H.program_violation(w1)
        if why: out['status'] = 'rule:' + why; return out
        npc, ph, ps = absorbed(w1); out['port_soft_entries'] = ps
        if npc or ph: out['status'] = 'not-absorbed'; out['nonport_rows'] = npc; out['port_hard_entries'] = ph; return out
        with deadline(a.timeout):
            caps, comp = cone_caps(w1)
            ent, cold = BASE['ent'], BASE['cold']
            if any(e[2] in ent for e in comp): out['status'] = 'comp-reads-entering'; return out
            if any(e[1] in ent | cold or e[2] in ent | cold for e in comp): out['status'] = 'comp-touches-residual'; return out
            out['comp_gates'] = len(comp); out['comp_changed'] = comp != P.compensation
            out['caps_changed'] = caps != P.caps
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), P.costs, check_literal=False, graph=g, interval=True)
        out.update(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - P.base_cost,
                   profile=dict(sorted(r['profile'].items())))
        cmp = P.compare(r['profile'], r['interval']); out['gain_certified'] = cmp.get('gain_certified')
        out['max_gain_units'] = str(cmp.get('max_gain_units')) if cmp.get('max_gain_units') is not None else None
        if out['delta'] < 0:
            from writeback import write_back, audit
            word = write_back(w1, g, r['assign']); ok, rep, sha = audit(word); out['audit'] = ok; out['word_sha256'] = sha
            if ok:
                import gzip; keep = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'gain-%d-%d-%d.json.gz' % (c['B'], c['y'], c['p']))
                open(keep, 'wb').write(gzip.compress(json.dumps(word, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
                out['word_file'] = os.path.basename(keep)
            else: out['audit_why'] = str(rep)[:200]
    except F.Infeasible: out['status'] = 'infeasible'
    except Timeout: out['status'] = 'timeout'
    except Exception as e: out['status'] = 'error:' + repr(e)[:120]
    out['sec'] = round(time.time() - t0, 2)
    rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    cands = json.load(open(a.cands))['cands']
    if a.limit: cands = cands[:a.limit]
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            if line.strip(): x = json.loads(line); done.add((x['B'], x['y'], x['p']))
    todo = [c for c in cands if (c['B'], c['y'], c['p']) not in done]
    print('candidates', len(cands), 'todo', len(todo), flush=True); t0 = time.time()
    with pool_context().Pool(a.workers, initializer=init, maxtasksperchild=40) as pool, open(a.out, 'a') as f:
        for k, r in enumerate(pool.imap_unordered(price, todo), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if r.get('delta') is not None and r['delta'] < 0: print('  NEG', r, flush=True)
            if k % 50 == 0: print(f'  {k}/{len(todo)} {time.time()-t0:.0f}s', flush=True)
    print('done', time.time() - t0, flush=True)
