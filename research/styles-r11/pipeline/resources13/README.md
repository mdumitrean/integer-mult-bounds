Use `measured_pool.run_pool` for newly registered research queues. It invokes the
unchanged `pipeline/pool.py` with an explicit, temporary resource policy. Frozen
historical runners retain their original 61-worker policy and source hashes.

The user requested this allocation change after comparing measured worker RSS
with available RAM. The 4-GiB per-worker ceiling (6 GiB for fill work) is separate
from the amount reserved for admission. The new policy reserves 1.20 times the
larger of the supplied worker-RSS estimate and current parent RSS, conservatively
counting all inherited pages again for each worker. It leaves 16 GiB available,
observes cgroup limits/current usage, caps execution at 120 workers, and leaves
eight CPUs outside the allocation. A queue with fewer tasks starts fewer workers.

Every launch projects memory again. During execution a parent polling hook checks
available memory and worker RSS at approximately half-second intervals. Memory
pressure aborts the pool and retains completed checkpoints; it is an incomplete
resource outcome, never a scientific null. This is measured admission with live
protection, not a claim that 120 workers can simultaneously use their 4-GiB caps.

Supply `estimated_worker_rss_gib` from a comparable measured workload or a bounded
pilot. New data sizes, large parent objects, and different algorithms require a
new estimate. Keep a finite CPU budget, task timeout and small checkpoint callback.
Load shared inputs once in the parent; combine short logical trials into coarse
tasks with deterministic indices and individual outcomes. Set numerical library
thread counts to one before importing them. Scientific registration, provenance,
confirmation and stopping rules remain applicable.

The resource benchmark compares identical fixed numerical tasks at 61 and 120
workers, reversing order for a second seed. Its synthetic data and timing outcomes
do not reopen any closed scientific search or imply a kappa improvement. Prefer
120 for this workload only if both seeds show at least a 15% throughput increase
with identical numerical outputs. Performance of other workloads remains open.

See `results/RESOURCE-SCALING-13/PREREGISTRATION.json`, the per-run results and
`RESULTS.md` for exact commands, measurements and scope. Source hashes and archives
bind both this adapter and the original pool. Substantial OpenAI Codex assistance
was used for implementation and review.
