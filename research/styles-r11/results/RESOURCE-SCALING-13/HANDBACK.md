The 120-worker measured-memory policy and two-seed scaling check passed. See RESULTS.md for the four-cell table and the workload-specific scope. All 1,920 tasks and 17 policy tests passed. No scientific null, pattern, new kappa improvement or census target was produced. Prior handbacks remain in force.

New queues should use pipeline/resources13/measured_pool.py with a measured workload-specific RSS estimate, a finite CPU budget, task timeouts and coarse batches. It delegates execution to the original pool. Keep inputs parent-loaded and BLAS threads at one. Historical frozen replays retain their original resource policy.

Compute used: 9,570.841 CPU seconds, 122.204 seconds benchmark wall; code preparation/review time is separate. All work stopped after the registered four cells.

Open next questions: apply the policy to the next justified, preregistered scientific family; separately parallelize or reduce the historical-ML serial preparation phase; measure scaling for memory-heavier and less cache-friendly workloads. More CPU allocation does not reopen prior scientific stop rules.

The canonical-main refresh is recorded in data/resources13/UPSTREAM-CHECKPOINT.json. Push only to the authorized fork results branch; coordinator review precedes external posting. Substantial OpenAI Codex assistance was used.
