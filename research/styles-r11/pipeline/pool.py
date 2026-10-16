"""Process pool with the caps required for every experiment of the r11 styles plan (PLAN.md section 7).

run_pool(fn, args_list, workers, timeout=300, rss_gib=4.0) applies fn to each argument tuple in a multiprocessing.Pool
(maxtasksperchild=50) and returns a list of dicts {"status": "OK"|"TIMEOUT"|"ERROR", "result"|"error", "seconds"}.
Each worker is started with an address-space limit where the OS enforces it (Linux) and with a watchdog thread that
polls its own peak RSS every 2 s and exits with code 3 above the cap (macOS does not enforce RLIMIT_AS). A task that
exceeds the timeout is recorded as TIMEOUT and never retried silently; the pool is terminated at the end of every run.
Project the peak RSS before launching: workers x (word 30 MB + fill 250 MB + working set) must stay under the machine's RAM.
"""
import multiprocessing as mp, os, resource, sys, threading, time, traceback

def _limits(rss_gib):
    cap = int(rss_gib * (1 << 30))
    for name in ("RLIMIT_AS", "RLIMIT_DATA"):
        lim = getattr(resource, name, None)
        if lim is not None and sys.platform.startswith("linux"):
            try:
                resource.setrlimit(lim, (cap, cap))
            except (ValueError, OSError):
                pass
    def watchdog():
        unit = 1024 if sys.platform.startswith("linux") else 1   # ru_maxrss: KiB on Linux, bytes on macOS
        while True:
            time.sleep(2.0)
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * unit > cap:
                os._exit(3)
    threading.Thread(target=watchdog, daemon=True).start()

def _call(fn, args):
    t0 = time.monotonic()
    try:
        return {"status": "OK", "result": fn(*args), "seconds": round(time.monotonic() - t0, 3)}
    except Exception:
        return {"status": "ERROR", "error": traceback.format_exc()[-2000:], "seconds": round(time.monotonic() - t0, 3)}

def run_pool(fn, args_list, workers, timeout=300, rss_gib=4.0, maxtasksperchild=50):
    out = []
    ctx = mp.get_context("fork" if sys.platform != "win32" else "spawn")
    pool = ctx.Pool(processes=workers, maxtasksperchild=maxtasksperchild, initializer=_limits, initargs=(rss_gib,))
    try:
        handles = [pool.apply_async(_call, (fn, args)) for args in args_list]
        for h in handles:
            try:
                out.append(h.get(timeout=timeout))
            except mp.TimeoutError:
                out.append({"status": "TIMEOUT", "seconds": timeout})
    finally:
        pool.terminate(); pool.join()
    return out

if __name__ == "__main__":   # smoke: 8 tasks, one of them slow -> TIMEOUT
    def work(i):
        if i == 3: time.sleep(5)
        return i * i
    res = run_pool(work, [(i,) for i in range(8)], workers=4, timeout=2)
    print([r["status"] for r in res])
