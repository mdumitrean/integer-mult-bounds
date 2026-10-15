"""Run a command in its own session; kill the whole session if any process in its tree exceeds --cap-gib RSS or the run
exceeds --wall seconds.  usage: capped.py --cap-gib 6 --wall 3000 --log LOG -- cmd ..."""
import argparse, os, signal, subprocess, sys, time
ap = argparse.ArgumentParser(); ap.add_argument('--cap-gib', type=float, default=6); ap.add_argument('--wall', type=int, default=3000)
ap.add_argument('--log', required=True); ap.add_argument('cmd', nargs=argparse.REMAINDER); a = ap.parse_args()
cmd = a.cmd[1:] if a.cmd and a.cmd[0] == '--' else a.cmd
cap_kib = int(a.cap_gib * 1024 * 1024); t0 = time.time(); peak = 0
with open(a.log, 'w') as log:
    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    def tree():
        out = subprocess.run(['ps', '-A', '-o', 'pid=,ppid=,rss='], capture_output=True, text=True).stdout.split('\n')
        kids = {}; rss = {}
        for line in out:
            f = line.split()
            if len(f) == 3: pid, ppid, r = map(int, f); kids.setdefault(ppid, []).append(pid); rss[pid] = r
        todo = [p.pid]; seen = []
        while todo:
            x = todo.pop(); seen.append(x); todo += kids.get(x, [])
        return [(x, rss.get(x, 0)) for x in seen]
    why = None
    while p.poll() is None:
        time.sleep(3)
        procs = tree(); m = max((r for _, r in procs), default=0); peak = max(peak, m)
        if m > cap_kib: why = f'RSS cap: a process reached {m / 1048576:.2f} GiB'
        elif time.time() - t0 > a.wall: why = f'wall cap {a.wall}s'
        if why:
            os.killpg(p.pid, signal.SIGKILL); p.wait(); break
    rc = p.returncode
with open(a.log, 'a') as log:
    log.write(f'\n[capped] exit {rc} after {time.time() - t0:.0f}s, peak process RSS {peak / 1048576:.2f} GiB' + (f', KILLED: {why}' if why else '') + '\n')
sys.exit(0 if rc == 0 and not why else 1)
