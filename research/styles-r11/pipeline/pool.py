"""Bounded r11 process pool; task execution deadlines, RSS caps, no retries.

Large objects are loaded once in the parent. Tasks carry indices and inherit data
with fork. All research parallelism goes through this module.
"""
import fcntl
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import resource
import signal
import sys
import threading
import time
import traceback

GIB = 1 << 30
PKG = Path(__file__).resolve().parents[1]


def memory_gib():
    total = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    paths = [Path('/sys/fs/cgroup/memory.max')]
    try:
        group = Path('/proc/self/cgroup').read_text().strip().split('::')[-1]
        here = Path('/sys/fs/cgroup') / group.lstrip('/')
        paths += [p / 'memory.max' for p in (here, *here.parents)
                  if str(p).startswith('/sys/fs/cgroup')]
    except OSError:
        pass
    for path in paths:
        try:
            value = path.read_text().strip()
            if value != 'max':
                total = min(total, int(value))
        except (OSError, ValueError):
            pass
    return total / GIB


def worker_count():
    return max(1, min(120, math.floor(memory_gib() / 4)))


def project_memory(workers, rss_gib=4.0, working_set_gib=1.0,
                   fill_gib=250 / 1024, word_gib=30 / 1024):
    parent = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    parent *= 1024 if sys.platform.startswith('linux') else 1
    # Count inherited parent pages for each worker, although fork shares them.
    per_worker = parent / GIB + fill_gib + word_gib + working_set_gib
    projected = parent / GIB + workers * per_worker
    report = dict(workers=workers, allocated_cores=128, reserved_cores=8,
                  ram_gib=memory_gib(), parent_peak_rss_gib=parent / GIB,
                  worker_rss_cap_gib=rss_gib,
                  projected_per_worker_gib=per_worker,
                  projected_peak_gib=projected,
                  working_set_gib=working_set_gib,
                  formula='parent + workers*(parent + word + fill + working set)')
    if workers > worker_count():
        raise ValueError('worker count exceeds user allocation')
    if projected >= report['ram_gib']:
        raise MemoryError('projected peak exceeds RAM: ' + repr(report))
    if per_worker >= rss_gib:
        raise MemoryError('projected worker exceeds RSS cap: ' + repr(report))
    return report


def _limits(rss_gib):
    sys.dont_write_bytecode = True
    cap = int(rss_gib * GIB)
    for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
                 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[name] = '1'
    for name in ('RLIMIT_AS', 'RLIMIT_DATA'):
        lim = getattr(resource, name, None)
        if lim is not None and sys.platform.startswith('linux'):
            resource.setrlimit(lim, (cap, cap))

    def watchdog():
        unit = 1024 if sys.platform.startswith('linux') else 1
        while True:
            time.sleep(2)
            if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * unit > cap:
                os._exit(3)
    threading.Thread(target=watchdog, daemon=True).start()


class TaskTimeout(BaseException):
    pass


class PoolCpuBudgetExceeded(TimeoutError):
    pass


def _live_worker_cpu(workers):
    ticks = os.sysconf('SC_CLK_TCK')
    total = 0.0
    for worker in workers:
        if worker.exitcode is not None:
            continue
        try:
            # Fields after the process-name closing parenthesis start at field 3.
            fields = Path('/proc/%d/stat' % worker.pid).read_text().rsplit(')', 1)[1].split()
            total += (int(fields[11]) + int(fields[12])) / ticks
        except (OSError, ValueError, IndexError):
            pass
    return total


def _alarm(signum, frame):
    raise TaskTimeout()


def _call(fn, args, timeout):
    t0, c0 = time.monotonic(), time.process_time()
    child0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        out = {'status': 'OK', 'result': fn(*args)}
    except TaskTimeout:
        out = {'status': 'TIMEOUT', 'error': 'worker execution deadline exceeded'}
    except BaseException:
        out = {'status': 'ERROR', 'error': traceback.format_exc()[-6000:]}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    child1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    out.update(seconds=time.monotonic() - t0,
               cpu_seconds=time.process_time() - c0 + child1.ru_utime
               + child1.ru_stime - child0.ru_utime - child0.ru_stime,
               peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
               * (1024 if sys.platform.startswith('linux') else 1))
    return out


def run_pool(fn, args_list, workers=None, timeout=300, rss_gib=4.0,
             maxtasksperchild=50, *, working_set_gib=1.0,
             projection_path=None, on_result=None, cpu_budget_seconds=None):
    """Return ordered results; on_result(index,result) checkpoints in parent.

    The old helper timed only the parent's wait. SIGALRM now bounds execution;
    a second get deadline detects lost workers. Neither case retries the task.
    """
    workers = worker_count() if workers is None else int(workers)
    if cpu_budget_seconds is not None and cpu_budget_seconds <= 0:
        raise ValueError('positive pool CPU budget required')
    if timeout <= 0:
        raise ValueError('positive task timeout required')
    report = project_memory(workers, rss_gib, working_set_gib)
    if projection_path:
        p = Path(projection_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2) + '\n')
    args_list = list(args_list)
    if not args_list:
        return []
    lock_path = PKG / 'results' / '.pool.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        cpu_start = time.process_time()
        child_start = resource.getrusage(resource.RUSAGE_CHILDREN)
        reserve = min(cpu_budget_seconds or float('inf'), workers * 0.10)
        pool = mp.get_context('fork').Pool(
            processes=workers, maxtasksperchild=maxtasksperchild,
            initializer=_limits, initargs=(rss_gib,))
        out = [None] * len(args_list)
        try:
            handles = {}
            submitted = 0
            completed = 0
            observed_workers = set(pool._pool)
            while completed < len(args_list):
                observed_workers.update(pool._pool)
                if cpu_budget_seconds is not None:
                    child_now = resource.getrusage(resource.RUSAGE_CHILDREN)
                    used = (time.process_time() - cpu_start + child_now.ru_utime + child_now.ru_stime
                            - child_start.ru_utime - child_start.ru_stime + _live_worker_cpu(observed_workers))
                    if used >= max(0.0, cpu_budget_seconds - reserve):
                        raise PoolCpuBudgetExceeded('live pool CPU budget reached: %.6f of %.6f seconds; %.6f reserved for collection/termination; no retry' % (used, cpu_budget_seconds, reserve))
                lost = [w for w in observed_workers if w.exitcode not in (None, 0)]
                if lost:
                    detail = [(w.pid, w.exitcode) for w in lost]
                    raise RuntimeError('worker process exited abnormally; no retry: ' + repr(detail))
                while submitted < len(args_list) and len(handles) < workers:
                    handles[submitted] = (time.monotonic(), pool.apply_async(
                        _call, (fn, args_list[submitted], timeout)))
                    submitted += 1
                ready = [i for i, (start, h) in handles.items()
                         if h.ready() or time.monotonic() - start > timeout + 15]
                if not ready:
                    time.sleep(0.05)
                    continue
                for i in ready:
                    start, handle = handles.pop(i)
                    try:
                        item = handle.get(timeout=0.01)
                    except mp.TimeoutError:
                        item = {'status': 'ERROR',
                                'error': 'worker lost after execution deadline; no retry',
                                'seconds': time.monotonic() - start, 'cpu_seconds': None,
                                'peak_rss_bytes': None}
                    out[i] = item
                    completed += 1
                    if on_result:
                        on_result(i, item)
        finally:
            pool.terminate()
            pool.join()
    return out


if __name__ == '__main__':
    def work(i):
        if i == 3:
            time.sleep(5)
        return i * i
    res = run_pool(work, [(i,) for i in range(8)], workers=4, timeout=2)
    print([r['status'] for r in res])
