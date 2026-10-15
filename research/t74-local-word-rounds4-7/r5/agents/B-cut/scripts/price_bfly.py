"""price_bfly.py: move each simple butterfly (y'+=y; y+=-1/2 y'; y*=-2, i.e. (y,y') -> (y'-y, y+y')) of B to the start of B,
where both targets are still at frame 0, and replace every earlier delivery into y or y' by its conjugate
(into y: y-=a s, y'+=a s; into y': y+=a s, y'+=a s).  The main map is unchanged by construction; the harness re-checks it
(static rules, exact B+tail map, unchanged compensation, recomputed caps) and prices exact optimal frames.
usage: price_bfly.py TOOLKIT WORD BFLY.json OUT.jsonl [--workers 3]"""
import json, gzip, sys, os, time
TK, WORD, BF, OUT = sys.argv[1:5]; WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3
sys.path.insert(0, TK)
import harness as H, compat
V = 112
w = json.load(gzip.open(WORD)); B = w['B']
groups = [g for g in json.load(open(BF))['groups_detail'] if g['candidate'] and len(g['targets']) == 2 and len(g['gates']) == 3]
def edit(g):
    y0, y1 = g['targets']; js = g['gates']
    gates = [B[j] for j in js]
    # identify roles: the scaled register is y, the other is y'
    y = next(e[1] for e in gates if e[0] == 'scale'); yp = y1 if y == y0 else y0
    ins = [(0, list(e[:-1]) + [[]]) for e in gates]; dele = list(js)
    for i in range(g['first']):
        e = B[i]
        if e[0] == 'add' and e[1] in (y, yp):
            t, s, num, den = e[1], e[2], e[3], e[4]
            dele.append(i)
            if t == y: ins += [(i, ['add', y, s, -num, den, []]), (i, ['add', yp, s, num, den, []])]
            else: ins += [(i, ['add', y, s, num, den, []]), (i, ['add', yp, s, num, den, []])]
    return dict(delete=sorted(dele), insert=ins), dict(y=y, yp=yp, crossed=len(dele) - 3)
P = None
def init():
    global P; P = H.Pricer(WORD, b='0.001679754956125544', check_literal=True, interval=True)
def run(g):
    ed, meta = edit(g); t0 = time.time()
    r = P.price(ed, timeout=120)
    r.pop('word', None)
    return dict(group=g['targets'], gates=g['gates'], **meta, seconds=round(time.time() - t0, 2), price={k: v for k, v in r.items() if k not in ('why',)}, why=str(r.get('why', ''))[:200])
if __name__ == '__main__':
    t0 = time.time(); init(); print('base cost', P.base_cost, P.base_profile, flush=True)
    with compat.pool_context().Pool(WORKERS, initializer=init, maxtasksperchild=8) as pool, open(OUT, 'w') as f:
        for k, r in enumerate(pool.imap_unordered(run, groups), 1):
            f.write(json.dumps(r) + '\n'); f.flush()
            print(k, r['group'], 'crossed', r['crossed'], r['price'].get('status'), r['price'].get('delta'), r['seconds'], 's', flush=True)
            if r['price'].get('rss_exit'): print('RSS above 6 GiB in a worker', flush=True)
    print('done', round(time.time() - t0, 1), 's', flush=True)
