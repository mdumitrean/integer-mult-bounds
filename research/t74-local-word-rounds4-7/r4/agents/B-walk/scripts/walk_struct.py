"""Structural pass: for every pre-move N, build W1 = N(W0) and run C-repair's shared-fusion generator on W1.
Pre-moves whose W1 admits a shared (multi-target) fusion are written to out/STRUCT.json with the candidates (W1-relative)."""
import json, os, sys, time, threading, multiprocessing as mp
sys.path.insert(0, os.path.dirname(__file__)); import common
sys.path.insert(0, os.path.join(common.R3, 'agents', 'C-repair'))
import harness as Hm, fusion as G, shared_fusion as SF
W0 = None
def watchdog():
    import resource
    while True:
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 6 * 1024 ** 3: os._exit(3)
        time.sleep(1)
def init():
    global W0
    threading.Thread(target=watchdog, daemon=True).start(); W0 = common.load('base')
def run(pm):
    try:
        w1 = Hm.compile_edits(W0, pm['ed'])
        cs, groups = SF.gen(w1, G)
    except Exception as e:
        return dict(id=pm['id'], err=repr(e)[:120])
    return dict(id=pm['id'], n_shared=len(cs), groups=groups, cands=cs[:200])
if __name__ == '__main__':
    pms = json.load(open(os.path.join(common.OUT, 'PREMOVES.json')))
    base_cs, base_groups = SF.gen(common.load('base'), G); print('W0 shared candidates', len(base_cs), base_groups, flush=True)
    t0 = time.time(); res = []
    with mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=300) as pool:
        for n, r in enumerate(pool.imap_unordered(run, pms, chunksize=8), 1):
            res.append(r)
            if n % 500 == 0: print(f'  {n}/{len(pms)} {time.time()-t0:.0f}s with-shared {sum(1 for x in res if x.get("n_shared"))}', flush=True)
    hit = [r for r in res if r.get('n_shared')]; err = [r for r in res if 'err' in r]
    print(f'done {len(res)} in {time.time()-t0:.0f}s | pre-moves opening shared fusions: {len(hit)} | errors {len(err)}', flush=True)
    json.dump(dict(base_shared=len(base_cs), hits=hit, errors=err[:20], n=len(res)), open(os.path.join(common.OUT, 'STRUCT.json'), 'w'))
