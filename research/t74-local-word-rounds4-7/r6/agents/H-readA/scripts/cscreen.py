"""cscreen.py: sound screen of the pure-copy family for read-in-A full-c1 narrowings (q, u).
For q narrowed to (8,1,9) (start_extra[q] = [u]) the only registers holding pure q_init are q itself before its first write
t0 (all 78 pairs have no A read before t0).  A copy `c += k*q` before position p <= t0 is admissible iff the single-insert
cone test (r3 B tools/cone.py: L_a v L_c <= U_b ^ U_d ^ caps, exact for one insert into the feasible narrowed word) passes
with FRAMES RE-SOLVED, a superset of r6 A's "existing frames already contain u" holders.  Necessary condition for any exact
copy construction: -L_q in span{transfer(c, p) : (c, p) admissible}.  Also reports the same span with ALL copies (no frame
test), the algebraic ceiling of the family.  usage: cscreen.py TOOLKIT WORD PAIRS.json OUT.json [WORKERS]"""
import copy, gzip, json, os, resource, signal, sys, time, multiprocessing as mp
from fractions import Fraction as F
from types import SimpleNamespace
TOOLKIT, WORD, PAIRS, OUT = sys.argv[1:5]; WORKERS = int(sys.argv[5]) if len(sys.argv) > 5 else 2
sys.path.insert(0, TOOLKIT); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as MD, cone as CN
# CSCREEN_PREV=<earlier CSCREEN json>: restrict holders to cold ends + that run's admissible holders (cold-end completion)
PREV = {r['q']: sorted({int(a.split('@')[0]) for a in r.get('admissible', [])}) for r in json.load(open(os.environ['CSCREEN_PREV']))['results']} if os.environ.get('CSCREEN_PREV') else {}
w0 = json.load(gzip.open(WORD)); v = w0['report']['v']; R = w0['report']['R']; n = 2 * v + R
main = [g for g in w0['A']] + [g for g in w0['cut']] + [g for g in w0['B']]
NA = len(w0['A'])
low = set(map(int, w0['helper_final']))
coef = lambda g: F(g[3], g[4]) if g[0] == 'add' else F(g[2], g[3])
def transfer(c, start):
    col = {c: F(1)}
    for k in range(start, len(main)):
        g = main[k]
        if g[0] == 'add':
            t, src = g[1], g[2]; x = col.get(src)
            if x:
                a = col.get(t, F(0)) + coef(g) * x
                if a: col[t] = a
                else: col.pop(t)
        elif g[1] in col: col[g[1]] = col[g[1]] * coef(g)
    return {y: a for y, a in col.items() if v <= y < 2 * v}
def rank_solve(cols, target):
    names = list(cols); rows = sorted({y for c in names for y in cols[c]} | set(target))
    A = [[cols[c].get(y, F(0)) for c in names] + [target.get(y, F(0))] for y in rows]
    r = 0; piv = []
    for j in range(len(names)):
        p = next((i for i in range(r, len(A)) if A[i][j] != 0), None)
        if p is None: continue
        A[r], A[p] = A[p], A[r]; inv = 1 / A[r][j]; A[r] = [x * inv for x in A[r]]
        for i in range(len(A)):
            if i != r and A[i][j] != 0:
                f = A[i][j]; A[i] = [a - f * b for a, b in zip(A[i], A[r])]
        piv.append(j); r += 1
        if r == len(A): break
    ok = not any(all(x == 0 for x in A[i][:-1]) and A[i][-1] != 0 for i in range(len(A)))
    sol = {names[j]: A[i][-1] for i, j in enumerate(piv) if A[i][-1] != 0} if ok else None
    return ok, r, sol
def task(pr):
    signal.alarm(900); t_start = time.time()
    q, u, t0 = pr['q'], pr['u'], pr['first_write']
    W = copy.deepcopy(w0); W['start_extra'] = dict(W['start_extra']); W['start_extra'][str(q)] = [u]
    caps, _ = MD.cone_caps(W)
    if os.environ.get('CSCREEN_NOCAPS') == '1': caps = {}          # loosest upper frames: sound whatever the final caps are
    lu = CN.LU(SimpleNamespace(caps=caps), W)
    Lq = {int(y): F(a) for y, a in pr['leak'].items()}; tgt = {y: -a for y, a in Lq.items()}
    adm = {}; allc = {}; tested = 0
    prev = PREV.get(q)
    holders = (sorted(low | set(prev)) if prev is not None else range(n))
    for c in holders:
        if c == q or v <= c < 2 * v or (c in low and os.environ.get('CSCREEN_INCLUDE_COLD') != '1'): continue
        cps = [p for p in lu.cpos[c] if 0 <= p < t0]          # c's A vertices before q's first write
        cand = sorted({0} | {p + 1 for p in cps})
        cand = [p for p in cand if p <= t0]
        seen_ok = set(); seen_all = set()
        for p in cand:
            tested += 1
            col = None
            okp = lu.ok(c, q, p)
            key_seg = p
            if len(allc) < 4000:
                col = transfer(c, p); kc = tuple(sorted(col.items()))
                if col and kc not in seen_all: seen_all.add(kc); allc[f'{c}@{p}'] = col
            if okp:
                if col is None: col = transfer(c, p)
                kc = tuple(sorted(col.items()))
                if col and kc not in seen_ok: seen_ok.add(kc); adm[f'{c}@{p}'] = col
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3 > 6: raise MemoryError('rss cap')
    ok_adm, r_adm, sol_adm = rank_solve(adm, tgt) if adm else (False, 0, None)
    ok_all, r_all, _ = rank_solve(allc, tgt) if allc else (False, 0, None)
    signal.alarm(0)
    return dict(q=q, u=u, t0=t0, leak_targets=len(Lq), copy_tests=tested, admissible_columns=len(adm), all_columns=len(allc),
                rank_admissible=r_adm, rank_all=r_all, pass_admissible=ok_adm, pass_all_copies=ok_all,
                solution={k: str(x) for k, x in sol_adm.items()} if sol_adm else None,
                admissible=sorted(adm)[:60], seconds=round(time.time() - t_start, 1))
if __name__ == '__main__':
    pairs = json.load(open(PAIRS))['pairs']
    out = dict(word=os.path.basename(WORD), toolkit=os.path.basename(TOOLKIT.rstrip('/')), pairs=len(pairs), results=[])
    def save():
        tmp = OUT + '.tmp'; json.dump(out, open(tmp, 'w'), indent=0); os.replace(tmp, OUT)
    def init():
        def on_alarm(sig, frm): raise TimeoutError('task timeout')
        signal.signal(signal.SIGALRM, on_alarm)
    def safe(pr):
        try: return task(pr)
        except Exception as e: return dict(q=pr['q'], u=pr['u'], error=repr(e)[:200])
    with mp.get_context('fork').Pool(WORKERS, initializer=init, maxtasksperchild=10) as pool:
        for k, res in enumerate(pool.imap_unordered(safe, pairs), 1):
            out['results'].append(res)
            out['pass_admissible'] = sorted(r['q'] for r in out['results'] if r.get('pass_admissible'))
            out['pass_all_copies'] = sorted(r['q'] for r in out['results'] if r.get('pass_all_copies'))
            out['errors'] = sorted(r['q'] for r in out['results'] if 'error' in r)
            save()
            print(k, '/', len(pairs), 'q', res['q'], 'adm', res.get('admissible_columns'), 'pass_adm', res.get('pass_admissible'),
                  'pass_all', res.get('pass_all_copies'), res.get('error', ''), res.get('seconds'), flush=True)
    out['complete'] = True; save()
    print('DONE pass_admissible', out['pass_admissible'], 'pass_all_copies', out['pass_all_copies'], 'errors', out['errors'], flush=True)
