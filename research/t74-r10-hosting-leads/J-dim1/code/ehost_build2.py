"""Entering-hostee -> cold-host hosting (J-dim1): the hostee h's anticipatory target read(s) before its first write k1
become dyadic initial corrections t += c*K_op(host) pulled back through the target-only precondition (as #2679's
prelife rule does for compensation reads); h is renamed to the cold host from k1 on, with one warp U_host -> E = hi(k1)
placed before k1; the host loses its cold end (helper_final) and buffer; h is removed (and leaves start_extra).
usage: ehost_build.py WORD.json.gz OUT.json PAIRS(h:c,h:c,...)"""
import sys, json, copy, gzip, time
from fractions import Fraction as Fr
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import borrow_price as bp
from bounds import Bounds, regs
from alias_build import make_G
src = sys.argv[1]; OUT = sys.argv[2]; pairs = [tuple(map(int, p.split(':'))) for p in sys.argv[3].split(',')]
HYPER = len(sys.argv) > 4 and sys.argv[4] == 'hyper'
w0 = bp.load(src); b = Bounds(src); ev = b.ev; v = w0['report']['v']
tB = [t for t, (sec, e) in enumerate(ev) if sec == 'B']          # time of each B gate (B index -> time)
def istarget(r): return v <= r < 2 * v
def build(w0, h, c, Esel=None):
    w = copy.deepcopy(w0); B = w['B']
    assert str(c) in w['helper_final'] and str(c) not in w['start_extra'] and str(h) in w['start_extra']
    assert not any(c in regs(e) for e in w['restore']), 'host in restore'
    assert not any(rec[1] in (c, h) for rec in w['warps']), 'host/hostee is a lender'
    pos = [i for i, e in enumerate(B) if h in regs(e)]
    j = next(i for i in pos if not (B[i][0] == 'add' and B[i][2] == h and istarget(B[i][1])))
    reads = [i for i in pos if i < j]
    lastc = max([i for i, e in enumerate(B) if c in regs(e)], default=-1); assert lastc < j, 'host not retired'
    vec = {}
    for i in reads:
        e = B[i]; vec[e[1]] = vec.get(e[1], Fr(0)) + Fr(e[3], e[4])
    for g in reversed(w['precondition']):                     # pull back through the target-only precondition
        if g[0] == 'add':
            if vec.get(g[2]): vec[g[1]] = vec.get(g[1], Fr(0)) - Fr(g[3], g[4]) * vec[g[2]]
        else:
            if g[1] in vec: vec[g[1]] = vec[g[1]] / Fr(g[2], g[3])
    Uc = tuple(bp.basis(tuple(w['helper_final'][str(c)])))
    E = b.hi[tB[j]] if Esel is None else Esel; assert len(E) == len(Uc), ('dim', len(E), len(Uc))
    for i in range(j, len(B)):
        e = B[i]
        if e[0] == 'add':
            if e[1] == h: e[1] = c
            if e[2] == h: e[2] = c
        elif e[1] == h: e[1] = c
    newB = [e for i, e in enumerate(B) if i not in set(reads)]
    shift = lambda p: p - sum(1 for i in reads if i < p)
    w['B'] = newB; w['warps'] = [[shift(rec[0])] + rec[1:] for rec in w['warps']]
    w['warps'].append([shift(j), c, make_G(Uc, E), list(Uc), list(E)]); op = len(w['warps'])
    w['initial_corrections'] = w['initial_corrections'] + [dict(target=t, source=c, operator_word=[op], coefficient=str(q)) for t, q in sorted(vec.items()) if q]
    del w['helper_final'][str(c)]; del w['start_extra'][str(h)]; w['removed'] = w['removed'] + [h]
    w['cleanup'] = bp.derive_cleanup(w, bp.word_patch.restored_of(w0) - {c})
    return w, dict(reads=reads, k1=j, E=list(E), corrections=len(w['initial_corrections']) - len(w0['initial_corrections']))
def inventory(w):
    vv, R = w['report']['v'], w['report']['R']; n = 2 * vv + R; rm = set(w['removed']); full = 9; out = {}
    for q in range(2 * vv, n):
        if q in rm: continue
        e = len(w['helper_final'][str(q)]) if str(q) in w['helper_final'] else full
        s = len(w['start_extra'][str(q)]) if str(q) in w['start_extra'] else 0
        out[str(e - s)] = out.get(str(e - s), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: int(kv[0])))
res = json.loads(Path(OUT).read_text()) if Path(OUT).exists() else {}
pf0 = bp.frame_profile(w0); print('base', pf0['profile'], pf0['certified'], flush=True)
for h, c in pairs:
    t0 = time.monotonic(); key = f'{h}:{c}'
    Es = [None]
    if HYPER:
        B_ = w0['B']; pos_ = [i for i, e in enumerate(B_) if h in regs(e)]
        j_ = next(i for i in pos_ if not (B_[i][0] == 'add' and B_[i][2] == h and istarget(B_[i][1])))
        Hk = b.hi[tB[j_]]; import itertools
        from wordmodel import basis as wb
        Es = sorted({wb([x for x in range(1, 512) if all(((x & y).bit_count() % 2 == 0) for y in [z]) and wb(list(Hk) + [x]) == Hk]) for z in range(1, 512) if wb(list(Hk) + [z]) != Hk or True} - {Hk}) if False else []
        # hyperplanes of Hk: kernels of nonzero functionals on Hk's coordinates
        vecs = [x for x in range(1, 512) if wb(list(Hk) + [x]) == Hk]
        dimk = len(Hk); seen = set()
        for f in range(1, 1 << dimk):
            hp = wb([x for x in vecs if (sum(((f >> i) & 1) * ((x >> 0) & 0) for i in range(dimk)) == 0)])
        coords = {}
        Hl = list(Hk)
        for m in range(1, 1 << dimk):
            x = 0
            for i in range(dimk):
                if m >> i & 1: x ^= Hl[i]
            coords[x] = m
        for f in range(1, 1 << dimk):
            hp = wb([x for x, m in coords.items() if (bin(m & f).count('1') % 2 == 0)])
            if len(hp) == dimk - 1 and hp not in seen: seen.add(hp); Es.append(hp)
    for Ei, Esel in enumerate(Es):
      key = f'{h}:{c}' + (f':E{Ei}' if HYPER else '')
      try: w1, info = build(w0, h, c, Esel)
      except AssertionError as ex: res[key] = dict(status='build:' + str(ex)[:80]); print(key, res[key], flush=True); continue
      w1['report'] = dict(w1['report']); w1['report']['width_inventory'] = inventory(w1)
      try: pf = bp.frame_profile(w1)
      except bp.Infeasible as ex: res[key] = dict(status='infeasible', why=str(ex)[:160], **info); print(key, 'infeasible', flush=True); Path(OUT).write_text(json.dumps(res, indent=1)); continue
      wf = bp.write_frames(w1, pf); wf['report']['width_inventory'] = inventory(w1)
      out = Path(OUT).parent / f'w-{Path(src).name.split("-")[0]}-{h}_{c}.json.gz'; bp.dump(wf, out)
      a = bp.audit(wf, timeout=600)
      d = {k: pf['profile'].get(k, 0) - pf0['profile'].get(k, 0) for k in set(pf['profile']) | set(pf0['profile'])}
      res[key] = dict(status='ok' if pf['certified'] else 'uncertified', profile=pf['profile'], delta_local={str(k): x for k, x in sorted(d.items()) if x},
                      cost_delta=str(pf['cost'] - pf0['cost']), inventory=w1['report']['width_inventory'], audit=a['status'], audit_err=a.get('error'),
                      word=str(out), seconds=round(time.monotonic() - t0, 1), **info)
      Path(OUT).write_text(json.dumps(res, indent=1))
      print(key, res[key]['status'], 'dlocal', res[key]['delta_local'], 'audit', a['status'], a.get('error') or '', res[key]['seconds'], flush=True)
