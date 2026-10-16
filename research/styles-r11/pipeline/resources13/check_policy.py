"""Registered safety checks for measured_pool; no real workers are launched.

Run only after registration/source freeze, with isolated Python and the frozen
adapter hash. All resource snapshots and pool execution are mocked. The real
pool source is read for provenance only; it is never imported by these tests.
"""
from contextlib import ExitStack
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
POOL_SHA256 = '59714d0b8501a4d2a0b041bbf18be089fa6a4881943a8c4db7c7605e6c5d86d8'
GIB = 1 << 30
M = None
SNAPSHOT_IMPL = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(total=247, available=239):
    return dict(total_bytes=int(total * GIB), available_bytes=int(available * GIB),
                host_available_bytes=int(available * GIB), cgroup_limits=[])


class FakePool:
    """Exercise the adapter hooks without importing multiprocessing/pool.py."""
    def __init__(self, body=None):
        self.worker_count = lambda: 61
        self.project_memory = lambda *a, **kw: {'original_projection': True}
        self._live_worker_cpu = lambda processes: 0.125
        self.original_hooks = (self.worker_count, self.project_memory, self._live_worker_cpu)
        self.calls = []
        self.body = body

    def run_pool(self, fn, args_list, **kwargs):
        args = list(args_list)
        self.calls.append(dict(args=args, kwargs=kwargs))
        projected = self.project_memory(kwargs['workers'], kwargs['rss_gib'], 99)
        if self.body is not None:
            return self.body(self, fn, args, kwargs)
        observed_cpu = self._live_worker_cpu([])
        return dict(workers=kwargs['workers'], projection=projected, cpu=observed_cpu)


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.assertFalse(M._ACTIVE, 'prior test leaked the active-policy latch')
        self.stack = ExitStack()
        self.memory = snapshot()
        self.stack.enter_context(patch.object(M, 'memory_snapshot', side_effect=lambda: deepcopy(self.memory)))
        self.stack.enter_context(patch.object(M, '_rss', return_value=(GIB // 2, 'R')))
        self.stack.enter_context(patch.object(M.os, 'sched_getaffinity', return_value=set(range(256))))
        self.stack.enter_context(patch.object(M, '_cgroups', return_value=[]))

    def tearDown(self):
        try:
            self.assertFalse(M._ACTIVE, 'policy latch must be restored after every path')
        finally:
            self.stack.close()

    def assert_restored(self, module):
        self.assertEqual((module.worker_count, module.project_memory, module._live_worker_cpu),
                         module.original_hooks)
        self.assertFalse(M._ACTIVE)

    def call_fake(self, module, args=None, **overrides):
        options = dict(estimated_worker_rss_gib=1.5, workers=120, rss_gib=4,
                       cpu_budget_seconds=10, timeout=30)
        options.update(overrides)
        with patch.object(M, '_pool_module', return_value=module):
            return M.run_pool(lambda value: value, [(i,) for i in range(256)] if args is None else args,
                              **options)

    def test_120_workers_are_admitted_from_measured_memory(self):
        report = M.projection(1.5)
        self.assertEqual(report['workers'], 120)
        self.assertEqual(report['maximum_admitted_workers'], 120)
        self.assertAlmostEqual(report['reserved_per_worker_gib'], 1.8)
        self.assertAlmostEqual(report['projected_increment_gib'], 216)
        self.assertEqual(report['worker_rss_cap_gib'], 4)
        self.assertLess(report['projected_increment_gib'] + report['headroom_gib'], 239)

    def test_low_available_memory_downsizes_and_rejects_oversubscription(self):
        self.memory = snapshot(247, 50)
        report = M.projection(1.5)
        self.assertEqual(report['workers'], 18)
        with self.assertRaises(ValueError):
            M.projection(1.5, workers=19)
        self.memory = snapshot(247, 16)
        with self.assertRaises(MemoryError):
            M.projection(1.5)

    def test_explicit_worker_request_is_bounded(self):
        for workers in (0, -1, 121, 120.0, True, float('nan'), float('inf')):
            with self.subTest(workers=repr(workers)), self.assertRaises((ValueError, TypeError)):
                M.projection(1.5, workers=workers)

    def test_estimates_and_process_caps_must_be_finite_positive(self):
        for estimate in (0, -1, float('nan'), float('inf'), -float('inf'), True):
            with self.subTest(estimate=repr(estimate)), self.assertRaises((ValueError, TypeError)):
                M.projection(estimate)
        for cap in (0, -1, 6.01, float('nan'), float('inf'), -float('inf'), True):
            with self.subTest(cap=repr(cap)), self.assertRaises((ValueError, TypeError)):
                M.projection(0.25, rss_gib=cap)

    def test_finite_positive_cpu_budget_is_mandatory_for_live_guard(self):
        module = FakePool()
        for budget in (0, -1, None, float('nan'), float('inf'), -float('inf'), True):
            with self.subTest(budget=repr(budget)), self.assertRaises((ValueError, TypeError)):
                self.call_fake(module, cpu_budget_seconds=budget)
        self.assertEqual(module.calls, [])
        self.assert_restored(module)

    def test_parent_rss_and_worker_cap_are_independent_reservation_inputs(self):
        with patch.object(M, '_rss', return_value=(2 * GIB, 'R')):
            report = M.projection(1.5)
            self.assertAlmostEqual(report['reserved_per_worker_gib'], 2.4)
            self.assertEqual(report['workers'], 92)
        with patch.object(M, '_rss', return_value=(int(3.4 * GIB), 'R')):
            with self.assertRaises(MemoryError):
                M.projection(0.25, rss_gib=4)

    def test_cgroup_remaining_memory_limits_host_available(self):
        groups = [Path('/sys/fs/cgroup'), Path('/sys/fs/cgroup/parent'),
                  Path('/sys/fs/cgroup/parent/job')]
        contents = {
            '/proc/meminfo': f'MemTotal: {300 * GIB // 1024} kB\nMemAvailable: {239 * GIB // 1024} kB\n',
            str(groups[0] / 'memory.max'): 'max',
            str(groups[1] / 'memory.max'): str(247 * GIB),
            str(groups[1] / 'memory.current'): str(40 * GIB),
            str(groups[2] / 'memory.max'): str(200 * GIB),
            str(groups[2] / 'memory.current'): str(80 * GIB),
        }

        def read_text(path, *args, **kwargs):
            if str(path) not in contents:
                raise FileNotFoundError(str(path))
            return contents[str(path)]

        with patch.object(M, '_cgroups', return_value=groups), patch.object(Path, 'read_text', read_text):
            observed = SNAPSHOT_IMPL()
            self.assertEqual(observed['total_bytes'], 200 * GIB)
            self.assertEqual(observed['available_bytes'], 120 * GIB)
            self.assertEqual(observed['host_available_bytes'], 239 * GIB)
            self.assertEqual(len(observed['cgroup_limits']), 2)
            contents[str(groups[2] / 'memory.current')] = str(201 * GIB)
            self.assertEqual(SNAPSHOT_IMPL()['available_bytes'], 0)

    def test_cpu_affinity_and_quota_bound_workers(self):
        with patch.object(M.os, 'sched_getaffinity', return_value=set(range(48))):
            self.assertLessEqual(M.projection(1.5)['workers'], 40)
        group = Path('/sys/fs/cgroup/mock-quota')

        def read_text(path, *args, **kwargs):
            if path == group / 'cpu.max':
                return '3200000 100000'
            raise FileNotFoundError(str(path))

        with patch.object(M, '_cgroups', return_value=[group]), patch.object(Path, 'read_text', read_text):
            self.assertEqual(M.projection(1.5)['workers'], 24)

    def test_private_pool_source_hash_rejected_before_import(self):
        with patch.object(Path, 'read_bytes', return_value=b'changed frozen source'), \
                patch.object(M.importlib.util, 'spec_from_file_location', side_effect=AssertionError('must not import')):
            with self.assertRaisesRegex(ValueError, 'source hash'):
                M._pool_module()

    def test_private_pool_name_and_cached_identity_are_bound(self):
        name = 'styles_r11_frozen_pool'
        with patch.object(M, '_POOL', None), patch.dict(sys.modules, {name: object()}), \
                patch.object(M.importlib.util, 'spec_from_file_location', side_effect=AssertionError('must not import')):
            with self.assertRaisesRegex(ValueError, 'already occupied'):
                M._pool_module()
        cached = SimpleNamespace(__file__=str(HERE.parent / 'pool.py'))
        with patch.object(M, '_POOL', cached), patch.dict(sys.modules, {name: cached}):
            self.assertIs(M._pool_module(), cached)
            with patch.dict(sys.modules, {name: object()}):
                with self.assertRaisesRegex(ValueError, 'identity changed'):
                    M._pool_module()
            with patch.object(cached, '__file__', str(HERE / 'wrong.py')):
                with self.assertRaisesRegex(ValueError, 'identity changed'):
                    M._pool_module()

    def test_success_uses_original_entrypoint_and_restores_hooks(self):
        module = FakePool()
        result = self.call_fake(module)
        self.assertEqual(result['workers'], 120)
        self.assertEqual(result['projection']['workers'], 120)
        self.assertEqual(result['cpu'], 0.125)
        self.assertEqual(len(module.calls), 1)
        self.assertEqual(module.calls[0]['kwargs']['timeout'], 30)
        self.assertEqual(module.calls[0]['kwargs']['rss_gib'], 4)
        self.assertEqual(module.calls[0]['kwargs']['cpu_budget_seconds'], 10)
        self.assert_restored(module)

    def test_task_count_caps_processes_and_does_not_hide_invalid_worker_request(self):
        module = FakePool()
        result = self.call_fake(module, args=[(1,), (2,), (3,)])
        self.assertEqual(result['workers'], 3)
        self.assert_restored(module)
        invalid = FakePool()
        with self.assertRaises(ValueError):
            self.call_fake(invalid, args=[(1,)], workers=121)
        self.assertEqual(invalid.calls, [])
        self.assert_restored(invalid)
        empty = FakePool()
        self.assertEqual(self.call_fake(empty, args=[]), [])
        self.assertEqual(empty.calls, [])
        self.assert_restored(empty)

    def test_low_memory_aborts_without_retries_and_restores_hooks(self):
        checkpoints = []

        def body(module, fn, args, options):
            options['on_result'](0, {'status': 'OK', 'result': 'already-completed'})
            self.memory = snapshot(247, 15)
            return module._live_worker_cpu([])

        module = FakePool(body)
        with self.assertRaisesRegex(MemoryError, 'headroom'):
            self.call_fake(module, on_result=lambda i, result: checkpoints.append((i, result)))
        self.assertEqual(len(module.calls), 1)
        self.assertEqual(checkpoints, [(0, {'status': 'OK', 'result': 'already-completed'})])
        self.assert_restored(module)

    def test_live_worker_rss_cap_aborts_and_restores_hooks(self):
        fake_pid = os.getpid() + 1000000

        def body(module, fn, args, options):
            return module._live_worker_cpu([SimpleNamespace(pid=fake_pid, exitcode=None)])

        module = FakePool(body)
        with patch.object(M, '_rss', side_effect=lambda pid: (int(4.1 * GIB), 'R') if pid == fake_pid else (GIB // 2, 'R')):
            with self.assertRaisesRegex(MemoryError, 'RSS cap'):
                self.call_fake(module)
        self.assertEqual(len(module.calls), 1)
        self.assert_restored(module)

    def test_worker_exception_restores_hooks(self):
        def body(module, fn, args, options):
            raise RuntimeError('synthetic execution failure')

        module = FakePool(body)
        with self.assertRaisesRegex(RuntimeError, 'synthetic execution failure'):
            self.call_fake(module)
        self.assert_restored(module)

    def test_telemetry_open_failure_restores_active_latch(self):
        module = FakePool()
        with patch.object(Path, 'mkdir'), patch.object(Path, 'open', side_effect=OSError('synthetic exclusive-open failure')):
            with self.assertRaisesRegex(OSError, 'exclusive-open'):
                self.call_fake(module, telemetry_path=HERE / 'never-created.jsonl')
        self.assertEqual(module.calls, [])
        self.assert_restored(module)

    def test_nested_policy_and_non_main_thread_are_rejected(self):
        module = FakePool()
        with M._policy(module, 1.5, 120, 4, None):
            with self.assertRaises(RuntimeError):
                with M._policy(module, 1.5, 120, 4, None):
                    self.fail('nested policy admitted')
        self.assert_restored(module)
        with patch.object(M.threading, 'current_thread', return_value=object()):
            with self.assertRaises(RuntimeError):
                with M._policy(module, 1.5, 120, 4, None):
                    self.fail('non-main-thread policy admitted')
        self.assert_restored(module)


class RecordedResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.test_names = []
        self.subtests = 0

    def startTest(self, test):
        self.test_names.append(test.id())
        super().startTest(test)

    def addSubTest(self, test, subtest, err):
        self.subtests += 1
        super().addSubTest(test, subtest, err)


def main():
    global M, SNAPSHOT_IMPL
    parser = argparse.ArgumentParser()
    parser.add_argument('--adapter-sha256', required=True)
    options = parser.parse_args()
    if not sys.flags.isolated or sys.flags.optimize:
        raise SystemExit('isolated Python with assertions is required')
    adapter = HERE / 'measured_pool.py'
    pool_path = HERE.parent / 'pool.py'
    if sha(adapter) != options.adapter_sha256 or sha(pool_path) != POOL_SHA256:
        raise SystemExit('frozen adapter or original pool hash mismatch')
    spec = importlib.util.spec_from_file_location('resource_policy_under_test', adapter)
    M = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = M
    spec.loader.exec_module(M)
    SNAPSHOT_IMPL = M.memory_snapshot
    result = RecordedResult()
    started = time.monotonic()
    unittest.defaultTestLoader.loadTestsFromTestCase(SafetyTests).run(result)
    report = dict(status='PASS' if result.wasSuccessful() else 'FAIL',
                  tests=result.testsRun, subtests=result.subtests, skipped=len(result.skipped),
                  failures=[dict(test=str(test), traceback=detail) for test, detail in result.failures],
                  errors=[dict(test=str(test), traceback=detail) for test, detail in result.errors],
                  test_names=result.test_names, seconds=time.monotonic() - started,
                  adapter_sha256=sha(adapter), checks_sha256=sha(Path(__file__)),
                  original_pool_sha256=POOL_SHA256, actual_pool_imports=0, worker_launches=0,
                  resource_snapshots='All synthetic; no scientific workload is imported or run.')
    print(json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
