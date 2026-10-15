"""Price two-step walks: W1 = N(W0) with its own optimal frames, then second-step candidates on W1 (W1-relative edits).
Reports delta1 = cost(W1) - cost(W0) and delta2 = cost(W1 + M) - cost(W1), total = delta1 + delta2.
usage: price2.py JOBS.json OUT.jsonl   (JOBS: [{id, ed1, cands: [{cid, ed}]}]); 3 workers, timeout + RSS cap."""
import json, os, sys, time, threading, multiprocessing as mp
sys.path.insert(0, os.path.dirname(__file__)); import common
import harness as Hm
from compat import deadline, Timeout
B0 = None; W0 = None
def watchdog():
    import resource
    while True:
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 6 * 1024 ** 3: os._exit(3)
        time.sleep(1)
def init():
    global B0, W0
    threading.Thread(target=watchdog, daemon=True).start()
    W0 = common.load('base'); B0 = Hm.Pricer(W0, b=os.environ['IMB_B'], check_literal=True).base_cost
def run(job):
    t0 = time.time(); out = dict(id=job['id'], results=[])
    try:
        w1 = Hm.compile_edits(W0, job['ed1'])
        with deadline(300): P1 = Hm.Pricer(w1, b=os.environ['IMB_B'], check_literal=False)
    except Timeout: out['w1'] = 'timeout'; return out
    except Exception as e: out['w1'] = 'error:' + repr(e)[:100]; return out
    out['delta1'] = P1.base_cost - B0; out['w1_certified'] = P1.base_certified; out['w1_profile'] = P1.base_profile
    for c in job['cands']:
        r = P1.price(c['ed'], timeout=120); r.pop('word', None)
        d2 = r.get('delta')
        out['results'].append(dict(cid=c['cid'], status=r.get('status'), delta2=d2, total=(out['delta1'] + d2) if d2 is not None else None,
                                   profile=r.get('profile'), why=str(r.get('why', ''))[:80]))
    out['seconds'] = round(time.time() - t0, 1); return out
if __name__ == '__main__':
    jobs = json.load(open(sys.argv[1])); outp = sys.argv[2]; t0 = time.time(); n = 0
    with mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=20) as pool, open(outp, 'w') as f:
        for r in pool.imap_unordered(run, jobs, chunksize=1):
            f.write(json.dumps(r) + '\n'); f.flush(); n += 1
            best = min([x['total'] for x in r['results'] if x['total'] is not None], default=None)
            print(f"  {n}/{len(jobs)} {r['id'][:60]} d1={r.get('delta1')} best_total={best} {[(x['status'], x['delta2']) for x in r['results']][:8]}", flush=True)
            for x in r['results']:
                if x['total'] is not None and x['total'] < 0: print('  GAIN', r['id'], json.dumps(x), flush=True)
    print(f'done {n} jobs in {time.time()-t0:.0f}s')
