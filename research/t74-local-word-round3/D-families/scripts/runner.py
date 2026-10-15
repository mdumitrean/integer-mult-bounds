"""runner: price candidate edits with the toolkit harness. 3 workers max, per-task deadline (harness timeout), per-worker
RSS watchdog (exit above 6 GiB, set in the initializer before any work), maxtasksperchild recycling, results streamed to
JSONL (resumable: ids already in OUT are skipped).
usage: runner.py WORD(base|extra) CANDS.json OUT.jsonl [--workers 3] [--interval 0|1] [--ids FILE] [--limit N] [--timeout S]"""
import argparse, json, os, sys, threading, time, multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
ap = argparse.ArgumentParser(); ap.add_argument('word'); ap.add_argument('cands'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--interval', type=int, default=0)
ap.add_argument('--ids'); ap.add_argument('--limit', type=int); ap.add_argument('--timeout', type=int, default=120)
a = ap.parse_args()
CAP = 6 * 1024 ** 3
P = None
def watchdog():
    import resource
    while True:
        r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform != 'darwin': r *= 1024
        if r > CAP: os._exit(3)
        time.sleep(1)
def init():
    global P
    threading.Thread(target=watchdog, daemon=True).start()
    import harness as H
    P = H.Pricer(common.WORDS[a.word], b=os.environ['IMB_B'], check_literal=True, interval=bool(a.interval))
def run(c):
    t0 = time.time(); r = P.price(c['ed'], timeout=a.timeout)
    r.pop('word', None); r.pop('why', None) if r.get('status') != 'audit-rejected' else None
    return dict(id=c['id'], word=a.word, seconds=round(time.time() - t0, 2), **{k: v for k, v in r.items()})
if __name__ == '__main__':
    cands = json.load(open(a.cands))
    if a.ids: keep = set(json.load(open(a.ids))); cands = [c for c in cands if c['id'] in keep]
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try: done.add(json.loads(line)['id'])
            except Exception: pass
    todo = [c for c in cands if c['id'] not in done]
    if a.limit: todo = todo[:a.limit]
    print(f'{len(todo)} to price ({len(done)} done) on {a.word}', flush=True)
    t0 = time.time(); n = 0
    ctx = mp.get_context('fork')
    while todo:
        with ctx.Pool(a.workers, initializer=init, maxtasksperchild=40) as pool, open(a.out, 'a') as f:
            it = pool.imap_unordered(run, todo, chunksize=1); got = set()
            try:
                while True:
                    r = it.next(timeout=a.timeout + 120)
                    f.write(json.dumps(r) + '\n'); f.flush(); got.add(r['id']); n += 1
                    if r.get('delta') is not None and r['delta'] < 0: print('  GAIN', json.dumps(r), flush=True)
                    if n % 200 == 0: print(f'  {n} priced {time.time()-t0:.0f}s', flush=True)
            except StopIteration: pass
            except mp.TimeoutError: print('  stalled worker: restarting pool', flush=True)
        todo = [c for c in todo if c['id'] not in got]
    print(f'done {n} in {time.time()-t0:.0f}s', flush=True)
