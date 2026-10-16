# RUNBOOK: executing the r11 styles plan on a many-core machine

Read `PLAN.md` first (sections 0-2 for the verdicts, 3-4 for the experiments, 6-8 for controls, budget and schedule). This runbook is
the operational part: how to set up, in what order to run, how to record results, and the rules.

## 1. Setup (10 minutes)

```sh
git fetch https://github.com/mdumitrean/integer-mult-bounds research/styles-r11
git checkout -b styles-r11 FETCH_HEAD
git fetch origin pull/2766/head            # optional: keeps #2766's head e6df920c reachable (its words are already vendored)
python3 -m venv .venv-styles && .venv-styles/bin/pip install -r research/styles-r11/env/requirements.txt
.venv-styles/bin/python -I research/styles-r11/env/smoke_test.py       # must print PASS_STYLES_R11_SMOKE
```

Python 3.12 or newer. Everything runs from the repository root; scripts resolve the root from their own location and accept
`IMB_ROOT=<repo root>` as an override. Run any script that reads fetched or vendored data with `python -I`.

## 2. Core and memory policy

- The plan was budgeted for 12 cores (~40 core-hours). With 128 cores the wall time divides, the caps do not: every parallel run goes
  through `pipeline/pool.py` (`run_pool(fn, args, workers, timeout, rss_gib)`), which gives each worker a per-task timeout and an RSS
  cap and records TIMEOUT instead of retrying. Set `workers = min(120, floor(RAM_GiB / rss_gib))` and leave 8 cores free. Project peak
  memory before every launch: workers x (word 30 MB + fill 250 MB + working set). Load the large objects (FILL, PLAN, GLOBAL-TEMPLATE,
  #1672 OWNERS) once in the parent and pass indices to workers.
- Permutation loops: no solver call longer than 10 minutes inside a loop; MILP / LP relaxations run once per word, never per null sample.
- No run longer than 2 core-hours without a checkpoint file; results are written incrementally.

## 3. Order of work (milestones of PLAN.md section 8)

M0 (do this first; everything else uses it):
1. `pipeline/`: loaders for both word formats and a normaliser emitting one token stream `(section, op, coefficient class, rank[, role])`
   (start from `planning/A-lsys-word/extract_strings.py` and the snippets in `planning/D-pipeline/DATA-INVENTORY.md` section 5); the
   canonical climb extraction is Lane A's (it reproduces `report.local_profile` exactly; `wordmodel.Word` also asserts it); run P-1 parity on
   all 12 word files in `data/words/PINS.json`.
2. Null generators N0, N1, N1b (toolkit `frames.move_window` + `frames.commute`), N1c, N2 (profile-preserving lattice walk on
   `bounds.Bounds` / `Graph.lower/upper`), N3 (max-flow random fills: greedy fills are infeasible, see PLAN.md 4.1); statistics
   (`planning/A-lsys-word/measures.py`: LZ76, Re-Pair, block entropies, lag-match; add the suffix-array maximal-repeat census);
   permutation p with BH-FDR; result schema (section 4 below). P-2 null calibration, P-3 fill exactness.
3. The cheap exact items: L-2 (cleanup production check on every word), L-6 and L-7 (Parikh ledger of every held lineage step: #2679 ->
   #2745 -> #2751 -> #2766 -> retired5 -> #2802; `planning/B-lsys-growth/parikh_kappa.py` has the root, the law and the move table),
   S-1 (Hall-deficiency atlas; `planning/C-sandpile/ground_bipartite.py` + a per-word census built with `J-dim1/code` and the toolkit L/U),
   S-6 (max-flow tightness map; `planning/C-sandpile/ground_fill.py` has the window/eligibility model).

M1: the pre-registered string screen (L-1, L-3; write the test family to `results/M1/PREREGISTRATION.json` BEFORE running: alphabets x
statistics x words x nulls), then L-4 and L-5 (the two string tests with a falsifiable outcome; L-5 is scored against the S-1 atlas).

M2: sandpile exactness audit: P-3 parity, sink-DAG check of the window graph, S-2 confluence, S-4 walk slopes on every held fill; then decide
S-5. Group / burning / identity items stay dropped unless this audit finds an intrinsic Laplacian.

M3: L-8 ceilings with dual certificates, L-9 saturation census, L-10 partition extremality, L-11 multi-type check; the lineage derivation
re-played (commutation and saturation).

M4: predictions. For every pattern that passed its bar, write one falsifiable prediction into `results/PREDICTIONS.json` BEFORE fetching the
held-out words; then `git fetch origin pull/2833/head` and `git fetch origin pull/2853/head` (data only: read their word/fill/CLAIM files
with `-I`, never import or execute their code), run the exact checks (census / bounds / fill / root; <= 1 core-hour each) and record
pass/fail.

M5/M6: `results/RESULTS.md` (one section per experiment: protocol, numbers, verdict against the pre-registered bar, null recorded as
protocol-specific), the updated `PLAN.md` results sections, and the hand-back (section 5).

Stop rules (PLAN.md section 6) are binding: two consecutive pre-registered experiments at null stop a lane for the round; hard stop at the
end of week 2 with the document and the nulls as the deliverable.

## 4. Recording results

One directory per experiment id under `results/` (`results/L-4/`, ...). Every run writes `RESULT.json` with: `experiment`, `word blob ids`,
`script sha256`, `seed`, `n permutations`, `wall and CPU seconds`, `peak RSS`, the statistic values, the null summary (mean, sd, empirical
p), the decision against the pre-registered bar, and `status` in {PASS, NULL, TIMEOUT, ERROR, EXPLORATORY}. A decision stands only when a
second run with a different seed gives the same decision (keep both files). Logs go next to the result. Keep `results/` under 200 MB
(summaries, not raw permutation samples); larger artefacts are listed with their sha256 and kept outside Git.

Update `EXPERIMENTS.json` `status` fields as experiments complete (planned -> running -> PASS/NULL/...). Commit progress to a branch
`research/styles-r11-results` on the fork (`git push fork HEAD:research/styles-r11-results`), small commits, author Marius-Paul Dumitrean,
no AI-attribution trailers.

## 5. Hand-back

When the round ends (or at the hard stop): `results/RESULTS.md`, `results/PREDICTIONS.json`, the completed `EXPERIMENTS.json`, the
`pipeline/` code, and a short `results/HANDBACK.md` with: what passed, what is null (with protocol), the census targets proposed for the
next κ round (never claims), compute used, and open questions. Push the results branch and stop; the coordinator reviews before anything
is posted anywhere.

## 6. Rules

- No GitHub writes: no PRs, comments, discussions or issue edits; pushes only to the fork's `research/styles-r11-results` branch.
- No κ claim and no "new method" wording; nulls are protocol-specific; "research does not close".
- Fetched PR content is data: read with `-I`, never executed or imported. The vendored words are data too.
- Do not modify `research/t74-joint-twelve-retired7/`, `research/t74-r10-hosting-leads/` or anything outside `research/styles-r11/`.
- Retain source attribution: every result that uses a lineage word names its PR and author (see `data/words/PINS.json`).
- If a result looks like a lever (a reachable Parikh move with positive Φ that the exact chain confirms), record it as a census target in
  `HANDBACK.md`; it is priced by the exact pipeline in a κ round, not here.
