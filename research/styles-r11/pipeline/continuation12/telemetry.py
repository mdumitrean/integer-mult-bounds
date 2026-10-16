"""Observed resource use for the parent and its pool children; no science."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import threading
import time

GIB = 1 << 30


def memory():
    fields = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key, value = line.split(':', 1)
        if key in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree'):
            fields[key + '_bytes'] = int(value.split()[0]) * 1024
    return fields


def _process(pid, pss=False):
    try:
        path = Path('/proc') / str(pid)
        fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
        out = dict(pid=pid, state=fields[0],
                   cpu_seconds=(int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK'),
                   rss_bytes=int(fields[21]) * os.sysconf('SC_PAGE_SIZE'))
        if pss:
            try:
                for line in (path / 'smaps_rollup').read_text().splitlines():
                    if line.startswith('Pss:'):
                        out['pss_bytes'] = int(line.split()[1]) * 1024
                        break
            except (OSError, ValueError, IndexError) as error:
                out['pss_error'] = repr(error)
        return out
    except (OSError, ValueError, IndexError):
        return None


class Monitor:
    """One lightweight sampling thread inside the pool-owning parent.

    CPU accounting includes reaped children and currently live children. RSS
    totals count shared pages repeatedly; PSS is also sampled every 10 seconds.
    Samples with a reaping race can have a negative CPU delta and are flagged,
    rather than being used to claim utilization. Final process accounting from
    the experiment runner remains authoritative for total CPU consumed.
    """

    def __init__(self, path, workers, interval=2.0):
        self.path = Path(path)
        self.workers = workers
        self.interval = interval
        self.phase = 'initialization'
        self.completed = 0
        self.queued = 0
        self.stop_event = threading.Event()
        self.samples = []
        self.thread = None

    def set_phase(self, phase, queued):
        self.phase, self.queued, self.completed = phase, queued, 0

    def progress(self, completed):
        self.completed = completed

    def sample(self, pss=False):
        reaped_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        pid = os.getpid()
        task_path = Path('/proc') / str(pid) / 'task'
        try:
            children = set()
            # Pool replacements are forked by its worker-handler thread, so
            # the main thread's children file alone misses recycled workers.
            for child_path in task_path.glob('*/children'):
                try:
                    children.update(int(s) for s in child_path.read_text().split())
                except OSError:
                    pass
            children = sorted(children)
        except OSError:
            children = []
        processes = [v for p in [pid, *children] if (v := _process(p, pss)) is not None]
        reaped = resource.getrusage(resource.RUSAGE_CHILDREN)
        reap_race = (reaped.ru_utime != reaped_before.ru_utime or
                     reaped.ru_stime != reaped_before.ru_stime)
        live_child_cpu = sum(v['cpu_seconds'] for v in processes if v['pid'] != pid)
        accounted_cpu = time.process_time() + reaped.ru_utime + reaped.ru_stime + live_child_cpu
        row = dict(utc=datetime.now(timezone.utc).isoformat(), monotonic=time.monotonic(),
                   phase=self.phase, queued=self.queued, completed=self.completed,
                   configured_workers=self.workers, live_children=len(processes) - 1,
                   running_children=sum(v['state'] == 'R' for v in processes if v['pid'] != pid),
                   accounted_cpu_seconds=accounted_cpu,
                   summed_rss_bytes_including_shared_pages=sum(v['rss_bytes'] for v in processes),
                   max_process_rss_bytes=max((v['rss_bytes'] for v in processes), default=0),
                   memory=memory(), load_average=os.getloadavg(),
                   affinity_cores=len(os.sched_getaffinity(0)), allocated_cores=128,
                   pss_sampled=pss, cpu_accounting_race=reap_race)
        if pss:
            row['summed_pss_bytes'] = sum(v.get('pss_bytes', 0) for v in processes)
            row['pss_coverage_processes'] = sum('pss_bytes' in v for v in processes)
        if self.samples:
            previous = self.samples[-1]
            delta = accounted_cpu - previous['accounted_cpu_seconds']
            elapsed = row['monotonic'] - previous['monotonic']
            row['cpu_accounting_race'] |= delta < 0
            if not row['cpu_accounting_race'] and not previous['cpu_accounting_race'] and elapsed > 0:
                row['observed_busy_cores'] = delta / elapsed
                row['parent_and_children_core_equivalents_per_configured_worker'] = delta / elapsed / self.workers
        self.samples.append(row)
        with self.path.open('a') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n')
        return row

    def _run(self):
        count = 0
        while not self.stop_event.wait(self.interval):
            count += 1
            try:
                self.sample(pss=count % 5 == 0)
            except Exception as error:
                with self.path.open('a') as stream:
                    stream.write(json.dumps(dict(telemetry_error=repr(error))) + '\n')

    def start(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raise FileExistsError(self.path)
        self.sample(pss=True)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return self

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.sample(pss=True)
        values = self.samples
        return dict(samples=len(values), interval_seconds=self.interval,
                    maximum_live_children=max(v['live_children'] for v in values),
                    maximum_running_children=max(v['running_children'] for v in values),
                    maximum_process_rss_bytes=max(v['max_process_rss_bytes'] for v in values),
                    maximum_summed_pss_bytes=max(v.get('summed_pss_bytes', 0) for v in values),
                    minimum_available_memory_bytes=min(v['memory']['MemAvailable_bytes'] for v in values),
                    maximum_observed_busy_cores=max(v.get('observed_busy_cores', 0) for v in values),
                    cpu_accounting_race_samples=sum(v.get('cpu_accounting_race', False) for v in values),
                    note='Sampled live use; summed RSS repeats shared pages. Use full-run CPU/wall for average cores.')
