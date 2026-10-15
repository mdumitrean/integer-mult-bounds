"""aenum.py: enumerate exact A-window equivalents. args: k Lmax max_n out.jsonl [first last]
One JSON line per alternative: i (A start), k, alt (gate tuples), perm flag, nz (window has a nonzero-frame gate),
big (window contains a gate of a large A deletion class, delta <= -6781 in r3 A-extra's relaxA-extra.json).
4 workers; per-window deadline 60 s; maxtasksperchild=300; the run stops if a worker's peak RSS passes 5.5 GiB."""
import os, sys, json, gzip, time, resource, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit'))
import apeep
from compat import deadline, Timeout, peak_rss_gib
k, Lmax, max_n, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
A = json.load(gzip.open(os.path.join(SCR, 'r3/inputs/gauge44-word-566-554.json.gz')))['A']
lo = int(sys.argv[5]) if len(sys.argv) > 5 else 0; hi = int(sys.argv[6]) if len(sys.argv) > 6 else len(A) - k + 1
rel = json.load(open(os.path.join(SCR, 'r3/agents/A-extra/out/relaxA-extra.json')))['results']
big = {int(i) for i, e in rel.items() if isinstance(e.get('delta'), (int, float)) and e['delta'] <= -6781}
def job(i):
    W = [apeep.gt(A[j]) for j in range(i, i + k)]
    nz = any(A[j][-1] for j in range(i, i + k))
    try:
        with deadline(60): alts = apeep.equivalents(W, Lmax, max_n)
    except Timeout: return i, 'timeout', [], nz, peak_rss_gib()
    except MemoryError: return i, 'mem', [], nz, peak_rss_gib()
    if alts is None: return i, 'skip', [], nz, peak_rss_gib()
    return i, 'ok', [([[str(x) if isinstance(x, apeep.Q) else x for x in t] for t in s], p) for s, p in alts], nz, peak_rss_gib()
if __name__ == '__main__':
    t0 = time.time(); n_alt = 0; st = {}
    with mp.get_context('fork').Pool(4, maxtasksperchild=300) as pool, open(out, 'w') as f:
        for i, s, alts, nz, rss in pool.imap(job, range(lo, hi), chunksize=8):
            st[s] = st.get(s, 0) + 1
            if rss is not None and rss > 5.5:
                print('RSS cap exceeded in a worker:', rss, 'GiB at window', i, flush=True); pool.terminate(); break
            pr = any(j in big for j in range(i, i + k))
            for a, p in alts:
                f.write(json.dumps(dict(i=i, k=k, alt=a, perm=p, nz=nz, big=pr)) + '\n'); n_alt += 1
    print(f'k={k} Lmax={Lmax} max_n={max_n} windows {hi - lo} {st} alternatives {n_alt} {time.time() - t0:.0f}s', flush=True)
