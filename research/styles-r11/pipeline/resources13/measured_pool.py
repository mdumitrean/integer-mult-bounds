"""Measured reservation policy for the unchanged r11 process pool.

This explicit adapter replaces allocation/projection hooks for one invocation;
execution, locks, deadlines, CPU budgets and per-process limits remain in
pipeline/pool.py. Historical files and their pinned hashes remain unchanged.
The user revised the conservative worker reservation on 2026-10-16.
"""
from contextlib import contextmanager
import importlib.util
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import threading
import time

GIB = 1 << 30
MAX_WORKERS = 120
RESERVED_CORES = 8
HEADROOM_GIB = 16.0
RESERVATION_FACTOR = 1.20
_ACTIVE = False
_POOL = None
POOL_SHA256 = '59714d0b8501a4d2a0b041bbf18be089fa6a4881943a8c4db7c7605e6c5d86d8'


def _cgroups():
    root = Path('/sys/fs/cgroup')
    paths = [root]
    for line in Path('/proc/self/cgroup').read_text().splitlines():
        if line.startswith('0::'):
            here = root / line.split('::', 1)[1].lstrip('/')
            paths += [p for p in (here, *here.parents) if p.is_relative_to(root)]
    return list(dict.fromkeys(paths))


def memory_snapshot():
    fields = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        name, value = line.split(':', 1)
        if name in ('MemTotal', 'MemAvailable'):
            fields[name] = int(value.split()[0]) * 1024
    available = fields['MemAvailable']
    total = fields['MemTotal']
    limits = []
    for group in _cgroups():
        try:
            raw = (group / 'memory.max').read_text().strip()
            if raw != 'max':
                cap = int(raw)
                current = int((group / 'memory.current').read_text())
                total = min(total, cap)
                available = min(available, max(0, cap - current))
                limits.append(dict(path=str(group), limit_bytes=cap, current_bytes=current))
        except FileNotFoundError:
            continue
    return dict(total_bytes=total, available_bytes=available,
                host_available_bytes=fields['MemAvailable'], cgroup_limits=limits)


def _rss(pid):
    fields = (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()
    return int(fields[21]) * os.sysconf('SC_PAGE_SIZE'), fields[0]


def projection(estimated_worker_rss_gib, workers=None, rss_gib=4.0):
    if isinstance(estimated_worker_rss_gib, bool) or not math.isfinite(estimated_worker_rss_gib) or estimated_worker_rss_gib <= 0:
        raise ValueError('positive finite measured worker RSS estimate required')
    if isinstance(rss_gib, bool) or not math.isfinite(rss_gib) or not 0 < rss_gib <= 6:
        raise ValueError('per-worker cap must be positive and at most 6 GiB')
    mem = memory_snapshot()
    parent_rss = _rss(os.getpid())[0] / GIB
    # Conservatively reserve the entire worker RSS, even shared inherited pages.
    reservation = max(estimated_worker_rss_gib, parent_rss) * RESERVATION_FACTOR
    if reservation >= rss_gib:
        raise MemoryError('worker reservation reaches its hard process cap')
    cpu_limit = min(MAX_WORKERS, len(os.sched_getaffinity(0)) - RESERVED_CORES)
    for group in _cgroups():
        try:
            quota, period = (group / 'cpu.max').read_text().split()
            if quota != 'max':
                cpu_limit = min(cpu_limit, math.floor(int(quota) / int(period)) - RESERVED_CORES)
        except FileNotFoundError:
            continue
    memory_limit = math.floor((mem['available_bytes'] / GIB - HEADROOM_GIB) / reservation)
    admitted = min(cpu_limit, memory_limit)
    if admitted < 1:
        raise MemoryError('insufficient available memory or CPU allocation')
    if workers is None:
        workers = admitted
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= admitted:
        raise ValueError(f'worker count {workers!r} exceeds measured admission {admitted}')
    return dict(policy='measured-rss-v1', workers=workers, maximum_admitted_workers=admitted,
                allocated_cores=128, reserved_cores=8, estimated_worker_rss_gib=estimated_worker_rss_gib,
                reservation_factor=RESERVATION_FACTOR, reserved_per_worker_gib=reservation,
                worker_rss_cap_gib=rss_gib, headroom_gib=HEADROOM_GIB,
                parent_current_rss_gib=parent_rss, memory=mem,
                projected_increment_gib=workers * reservation,
                projected_process_rss_sum_gib=parent_rss + workers * reservation,
                formula='new workers * 1.20 * max(measured worker RSS, parent RSS) <= available memory - 16 GiB',
                shared_pages='Full worker RSS is reserved; fork sharing is not required for admission.',
                authority='User requested use of measured memory headroom on 2026-10-16; 120-worker and per-worker caps retained.')


def _pool_module():
    global _POOL
    name = 'styles_r11_frozen_pool'
    path = Path(__file__).resolve().parents[1] / 'pool.py'
    if hashlib.sha256(path.read_bytes()).hexdigest() != POOL_SHA256:
        raise ValueError('frozen pool source hash changed')
    if _POOL is None:
        if name in sys.modules:
            raise ValueError('private pool module name already occupied')
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _POOL = module
    if sys.modules.get(name) is not _POOL or Path(_POOL.__file__).resolve() != path:
        raise ValueError('private pool module identity changed')
    return _POOL


@contextmanager
def _policy(module, estimate, workers, cap, telemetry_path):
    global _ACTIVE
    if _ACTIVE or threading.current_thread() is not threading.main_thread():
        raise RuntimeError('one pool policy on the main thread at a time')
    originals = module.worker_count, module.project_memory, module._live_worker_cpu
    _ACTIVE = True
    last_sample = -float('inf')
    stream = None
    try:
        if telemetry_path:
            path = Path(telemetry_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            stream = path.open('x')

        def project(count, rss_gib=cap, working_set_gib=0, **unused):
            return projection(estimate, count, rss_gib)

        def live_cpu(processes):
            nonlocal last_sample
            cpu = originals[2](processes)
            now = time.monotonic()
            if now - last_sample >= 0.5:
                last_sample = now
                mem = memory_snapshot()
                rss_values, states = [], []
                for process in processes:
                    if process.exitcode is None:
                        try:
                            rss, state = _rss(process.pid)
                            rss_values.append(rss)
                            states.append(state)
                        except FileNotFoundError:
                            pass
                row = dict(monotonic=now, live_workers=len(states), running_workers=states.count('R'),
                           maximum_worker_rss_bytes=max(rss_values, default=0),
                           summed_worker_rss_bytes=sum(rss_values), memory=mem,
                           note='Sequential samples; shared pages counted repeatedly; no instantaneous CPU claim.')
                if stream:
                    stream.write(json.dumps(row, sort_keys=True) + '\n')
                    stream.flush()
                if mem['available_bytes'] < HEADROOM_GIB * GIB:
                    raise MemoryError('global memory headroom crossed; pool terminated, no retry')
                if max(rss_values, default=0) > cap * GIB:
                    raise MemoryError('worker RSS cap crossed; pool terminated, no retry')
            return cpu

        module.worker_count = lambda: projection(estimate, None, cap)['workers']
        module.project_memory = project
        module._live_worker_cpu = live_cpu
        yield
    finally:
        module.worker_count, module.project_memory, module._live_worker_cpu = originals
        _ACTIVE = False
        if stream:
            stream.close()


def run_pool(fn, args_list, *, estimated_worker_rss_gib, workers=None,
             timeout=300, rss_gib=4.0, maxtasksperchild=50,
             projection_path=None, on_result=None, cpu_budget_seconds,
             telemetry_path=None):
    """Run the original pool with measured admission and a live memory guard.

    Estimate must cover the same workload and loaded parent objects; a distinct
    workload needs a bounded pilot. The 4/6-GiB cap is a ceiling, not a reservation.
    Keep callbacks small and combine short logical trials into coarse tasks.
    """
    if isinstance(cpu_budget_seconds, bool) or not math.isfinite(cpu_budget_seconds) or cpu_budget_seconds <= 0:
        raise ValueError('finite positive CPU budget required for live guards')
    args_list = list(args_list)
    if not args_list:
        return []
    report = projection(estimated_worker_rss_gib, workers, rss_gib)
    workers = min(report['workers'], len(args_list))
    module = _pool_module()
    with _policy(module, estimated_worker_rss_gib, workers, rss_gib, telemetry_path):
        return module.run_pool(fn, args_list, workers=workers, timeout=timeout,
                               rss_gib=rss_gib, maxtasksperchild=maxtasksperchild,
                               projection_path=projection_path, on_result=on_result,
                               cpu_budget_seconds=cpu_budget_seconds)
