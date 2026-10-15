"""Enumerate exact equivalents for all B windows of size k (args: k Lmax max_n out.jsonl). Writes one JSON line per
alternative: window start i, k, the alternative gates, plus a priority flag (window touches a large-deletion gate)."""
import os, sys, json, gzip, time, multiprocessing as mp
S = os.environ['SCR']; sys.path.insert(0, S + '/r6/agents/P-peephole/scripts')
import peep
k, Lmax, max_n, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
B = json.load(gzip.open(S + '/r3/inputs/gauge44-word-566-554.json.gz'))['B']
rel = json.load(open(S + '/r3/agents/A-extra/out/relax-extra.json'))['results']
big = {int(i) for i, e in rel.items() if isinstance(e.get('delta'), (int, float)) and e['delta'] <= -3059}
def job(i):
    W = [peep.gt(B[j]) for j in range(i, i + k)]
    try: alts = peep.equivalents(W, Lmax, max_n)
    except MemoryError: return i, 'mem', []
    if alts is None: return i, 'skip', []
    return i, 'ok', [[list(map(lambda x: str(x) if isinstance(x, peep.Q) else x, t)) for t in s] for s in alts]
if __name__ == '__main__':
    t0 = time.time(); n_alt = n_skip = 0
    with mp.get_context('fork').Pool(4, maxtasksperchild=200) as pool, open(out, 'w') as f:
        for i, st, alts in pool.imap(job, range(len(B) - k + 1), chunksize=8):
            if st != 'ok': n_skip += 1; continue
            pr = any(j in big for j in range(i, i + k))
            for a in alts:
                f.write(json.dumps(dict(i=i, k=k, alt=a, big=pr)) + '\n'); n_alt += 1
    print(f'k={k} Lmax={Lmax}: windows {len(B) - k + 1}, skipped {n_skip}, alternatives {n_alt}, {time.time() - t0:.0f}s', flush=True)
