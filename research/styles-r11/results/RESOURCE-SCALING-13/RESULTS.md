The measured-memory policy passed, and 120 workers improved throughput by 42% and 47% in the two registered comparisons. This is a resource benchmark, with no new kappa result or scientific pattern claim.

The original 61-worker limit reserved 4 GiB per worker regardless of observed use. The user requested measured sizing. New queues use `pipeline/resources13/measured_pool.py`, which invokes the original `pipeline/pool.py` with a temporary allocation/projection policy and live memory guard. Historical sources and replays remain byte-identical.

Admission reserves 1.20 times the larger of estimated worker RSS and current parent RSS, leaves 16 GiB available, checks cgroup limits and caps workers at 120 with eight cores reserved. A 1.5-GiB estimate reserves 1.8 GiB per worker: 216 GiB at 120. The separate per-worker ceilings remain 4 GiB (6 GiB for fill work). Shared pages are conservatively counted again in every worker reservation. New workload sizes need a comparable measurement or bounded pilot.

| Seed | Workers | Wall seconds | CPU seconds | Average busy cores |
|---|---:|---:|---:|---:|
| 73001 | 61 | 33.57 | 1929.60 | 57.49 |
| 73001 | 120 | 23.65 | 2550.46 | 107.82 |
| 146003 | 120 | 26.23 | 2848.87 | 108.62 |
| 146003 | 61 | 38.60 | 2241.76 | 58.08 |

All 1,920 tasks completed. Total compute, including benchmark setup and recording: 9570.841 CPU seconds (2.659 core-hours), 122.204 wall seconds. At 120 workers, CPU time per fixed workload rose 32.2% and 27.1%; elapsed time fell 29.5% and 32.1%. Faster completion therefore costs additional CPU time.

The frozen workload uses one parent-loaded 32768×32 float64 synthetic feature matrix, single-thread numerical libraries, and 10000 fixed squared-loss gradient steps per task. Each seed runs exactly 480 tasks at each worker count, in reversed order for the second seed. Every corresponding numerical output and checksum matched exactly. The independent tiny scalar reference passed. All 17 policy safety tests, including 27 subtests, passed before launch. These controls cover admission, cgroup and CPU limits, low-memory/RSS aborts, provenance and restoration after failure.

Both 120-worker runs observed 120 live/running worker processes. Joined CPU/wall accounting, rather than instantaneous samples, gives 107.82 and 108.62 average busy cores. Maximum worker RSS across all cells was 50.16 MiB; minimum sampled available memory was237.79 GiB. This small synthetic workload validates dispatch and throughput, not the peak memory of a future large historical-ML run. Numerical/native library threads were set to one before import; the input receipt records whether threadpoolctl was available.

The four cells spent 0.30–0.37 seconds each in checkpoint callbacks. The prior historical-ML run separately spent about 49 seconds preparing data without active workers and used quarter-second permutation jobs. This benchmark uses coarse tasks to reduce scheduling gaps. It does not isolate every scheduling/startup effect or demonstrate a speedup for serial data preparation. The 120-worker preference is confirmed for this fixed cached dense workload; other kernels may scale differently.

No stopped scientific lane was reopened. Prior kappa findings, source attribution and their limitations are unchanged. This work received substantial OpenAI Codex assistance in implementation and review.

Reproduce with the existing environment after source verification:

```sh
.venv-styles/bin/python -I -B research/styles-r11/pipeline/resources13/check_policy.py --adapter-sha256 24f7e2df124307c263ee711ef7006bcaf350ba9a48ce057b3a9e72761fe134cb
.venv-styles/bin/python -I -B research/styles-r11/pipeline/resources13/run_scaling.py --registration-sha256 6ab17d58406505a500adfada36b041257290ff33c30cafe26023f3c7e14e9f73 --implementation-sha256 f18f41d69772213260bbd938caf745f79520cc187e8f558dc17d0f95c7850263 --attempt replay-1
```

Use an unused attempt name. A reproduction is a new execution, not additional scientific evidence. See PREREGISTRATION.json, IMPLEMENTATION-PINS.json, EXPERIMENTS.json, v1/RUN.json, per-cell RESULT.json files and data/resources13 for exact evidence.
