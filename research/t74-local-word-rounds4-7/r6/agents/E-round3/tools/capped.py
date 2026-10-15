"""capped.py: run one command with a wall-clock timeout and an RSS cap on its whole process tree (polled every 2 s).
usage: capped.py TIMEOUT_S RSS_GIB LOG -- cmd ...   exit code: child's, or 124 (timeout) / 137 (RSS cap)."""
import os, signal, subprocess, sys, time
t_lim = float(sys.argv[1]); rss_lim = float(sys.argv[2]) * 1024 ** 3; log = sys.argv[3]
cmd = sys.argv[sys.argv.index('--') + 1:]
def tree_rss(pid):
    out = subprocess.run(['ps', '-A', '-o', 'pid=,ppid=,rss='], capture_output=True, text=True).stdout.split('\n')
    kids = {}; rss = {}
    for line in out:
        f = line.split()
        if len(f) == 3: p, pp, r = map(int, f); kids.setdefault(pp, []).append(p); rss[p] = r * 1024
    tot, st = 0, [pid]
    while st:
        p = st.pop(); tot += rss.get(p, 0); st.extend(kids.get(p, []))
    return tot
with open(log, 'w') as f:
    pr = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time(); peak = 0; code = None
    while code is None:
        try: code = pr.wait(timeout=2)
        except subprocess.TimeoutExpired:
            r = tree_rss(pr.pid); peak = max(peak, r)
            if r > rss_lim or time.time() - t0 > t_lim:
                os.killpg(pr.pid, signal.SIGKILL); pr.wait(); code = 137 if r > rss_lim else 124
    f.write(f'\n[capped] exit {code} wall {time.time() - t0:.1f}s peak_rss_gib {peak / 1024 ** 3:.2f}\n')
sys.exit(code)
