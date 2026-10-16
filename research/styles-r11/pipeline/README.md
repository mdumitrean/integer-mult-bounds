# r11 research pipeline

Run from the repository root with the dedicated interpreter:

```sh
.venv-styles/bin/python -I -B research/styles-r11/pipeline/verify_results.py
```

The completed experiment registry and immutable receipts are under `../EXPERIMENTS.json` and `../results/`. `verify_results.py` checks receipt/provenance integrity; it does not rerun the scientific experiments or upgrade their verdicts. Historical source-byte gaps are listed separately from the required retained SHA256 manifests.

The run sequence is `run_m0.py`, `run_m1.py`, `run_m2.py`, `run_m3.py`, then `run_m4.py`. Each runner reads its frozen milestone preregistration. Run IDs are immutable; an existing receipt is not silently overwritten or retried. Binding lane stops have explicit zero-compute receipts for the remaining families. An independent reproduction requires a separate checkout, the matching archived scientific sources and a fresh output namespace; the current results directory is evidence, not scratch space.

`wordio.py` implements canonical extraction for both word formats. `nulls.py`, `word_commute_fast.py` and `word_frame_fast.py` retain the registered null semantics. `measures.py` and `string_screen.py` hold the string statistics and capped grammar screen. `fill.py`, `matching.py` and `sandpile.py` implement the scoped fill, matching and frame checks. `growth.py`, `growth_replay.py`, `growth_order.py`, `growth_m3.py` and `growth_cost.py` implement profile ledgers, guarded edits, exact rational class certificates and conditional local-cost calibration.

All experimental parallelism goes through `pool.py`. It uses the user allocation of 128 cores, leaves eight free, and sets workers to `min(120, floor(RAM_GiB/4))`: 61 on this host. Workers have task deadlines and 4 GiB RSS limits, or 6 GiB for fill work. Parent-loaded objects are inherited with `fork`; every launch projects memory. BLAS and HiGHS are restricted to one thread. The live CPU-budget guard includes parent, reaped-child and current-worker CPU. Early timeout/abort limitations are retained in the report.

`heldout_data.py` reads only pinned inert JSON/gzip data for #2833 and #2853. Its trusted loaders and Bounds implementation come from the preexisting pinned repository. No fetched module, recipe, auditor or native executable is loaded. Canonical/frame/fill validation is narrower than a replay of either PR's supplier admission or outer theorem proof. The frozen predictions and implementation hashes are retained under `../results/M4/`.

`export_language.py` is a deterministic format export of already-recorded M0 and later evidence. It emits four indexed artifacts per original pinned word and explicitly marks absent or unresolved production evidence. It performs no solver, permutation or word-extraction experiment. `records.py` preserves source attributions, source bytes, per-run metrics and second-seed decisions.

Before outward use, read `../results/HANDBACK.md`, including the scoped nulls and unresolved obligations. This round leaves proposed census targets unpriced.
