"""pool: fork pool with a per-task deadline (compat.deadline in the task), maxtasksperchild, and a parent-side RSS
watchdog that kills any worker above the cap (set before forking)."""
import multiprocessing as mp, os, signal, subprocess, threading, time
RSS_CAP_GIB = 6.0
def _rss_gib(pid):
    try: return int(subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True).stdout.strip() or 0) / 1024 ** 2
    except Exception: return 0.0
def run_pool(fn, tasks, workers=4, init=None, maxtasks=20, chunksize=1, on_result=None):
    ctx = mp.get_context('fork'); stop = threading.Event(); killed = []
    with ctx.Pool(workers, initializer=init, maxtasksperchild=maxtasks) as pool:
        def watch():
            while not stop.is_set():
                for p in list(getattr(pool, '_pool', [])):
                    if p.pid and _rss_gib(p.pid) > RSS_CAP_GIB:
                        killed.append(p.pid)
                        try: os.kill(p.pid, signal.SIGKILL)
                        except OSError: pass
                time.sleep(2)
        t = threading.Thread(target=watch, daemon=True); t.start()
        try:
            for r in pool.imap_unordered(fn, tasks, chunksize=chunksize):
                if on_result: on_result(r)
        finally:
            stop.set()
    return killed
