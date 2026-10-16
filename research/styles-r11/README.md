# styles-r11: evaluation package for two research styles on the integer-mult-bounds words

A research hand-off, not a PR and not a κ claim. It carries the evaluation plan `PLAN.md` ("L-system descriptions and sandpile /
chip-firing analysis of the local words, the owner fill and the κ equation"), the data the plan's experiments read, the planning
round's reports and scripts, and a runbook for a large machine. The branch `research/styles-r11` is stacked on
`research/t74-r10-hosting-leads` (our r10 hosting leads, with the #1186 exact frame toolkit and #2745's helper modules), which is
stacked on PR #2802's head `17b2ee6e` (the `research/t74-joint-twelve-retired7/` package: words, owner fill, plan, template, exact
moment, literal owner check, pinned PR2679 auditor, evidence). One fetch brings everything.

## Contents

| path | what |
|---|---|
| `PLAN.md` | the evaluation plan (copy of `new_research_styles.md`, 2026-10-16): verdicts, mappings, 17 pre-registered experiments L-1..L-11 and S-1..S-6, null models, pattern criteria, stop rules, compute plan, schedule, feedback into the κ work |
| `RUNBOOK.md` | how to run it on a many-core machine: setup, smoke test, core and memory policy, milestone order, per-experiment entry points, result schema, what to report back, rules |
| `EXPERIMENTS.json` | machine-readable registry of the experiments (inputs, method, null, pass bar, budget, milestone, starting script, status) |
| `data/words/` | the frozen word set W and intermediates as data (15 files, 1 MB) with `PINS.json` (SHA-256, Git blob, source PR/head/path, author, κ); the #2802 / #2751 / #2462 words are referenced in the #2802 package, not copied |
| `data/fills/` | #1672's OWNERS / GLOBAL-TEMPLATE / PLAN / PROFILE / CLAIM (the FULL-WORD family's fill objects); retired5's and #1625's CLAIM.json |
| `data/PROFILES.json` | local and complete profiles, width inventories and recorded κ per construction (derived from the words and the pinned CLAIM files; quoted entries are marked) |
| `planning/` | the planning round: `BRIEF.md` and the four lane directories (`A-lsys-word`, `B-lsys-growth`, `C-sandpile`, `D-pipeline`), each with `REPORT.md`, the grounding scripts and their outputs. Paths were relocated to the repository layout (`IMB_ROOT` overrides the root); `$S` in the prose means the planning scratchpad, whose files are now here |
| `pipeline/` | `root.py` (90-digit moment root by bisection), `pool.py` (process pool with per-task timeout and per-worker RSS cap, required by PLAN.md section 7); the M0 pipeline of the plan is built here |
| `env/` | `requirements.txt`, `smoke_test.py` |
| `results/` | empty; one directory per experiment id, see RUNBOOK.md |

## Quick start

```sh
git fetch https://github.com/mdumitrean/integer-mult-bounds research/styles-r11
git checkout -b styles-r11 FETCH_HEAD
python3 -m venv .venv-styles && .venv-styles/bin/pip install -r research/styles-r11/env/requirements.txt
.venv-styles/bin/python -I research/styles-r11/env/smoke_test.py      # PASS_STYLES_R11_SMOKE in about 10 s
```

Then follow `RUNBOOK.md`. The grounding scripts run from the repository root, for example
`python3 -I research/styles-r11/planning/D-pipeline/word_timing.py` or
`python3 -I research/styles-r11/planning/C-sandpile/ground_fill.py research/t74-joint-twelve-retired7/inputs /tmp/fill.json`.

## Provenance and attribution

All vendored words are Apache-2.0 research artefacts of the integer-mult-bounds community with their lineage notices retained in their
source packages: #1094 and #2745 (Jeremy Kothe, jeremykothe2), #1672 (Jeremy Kothe / LeverRank, on our #1625 words, PR #1319/#1297
lineage of Rohan Arun), #2679 (Philippe Van Velzen, philippeVV), #2766 (DavidAriasC), #2751 (Tekalign, tekuuu; referenced in tree),
#2462 (jeremykothe2; referenced in tree), our #1195, #1625, retired5 and #2802. `data/words/PINS.json` records the exact source of
every file. The helper modules in `research/t74-r10-hosting-leads/J-dim1/code/` are byte-identical to #2745's handoff; the toolkit in
`deps/toolkit-rev3/` is our PR #1186. The pinned auditor is PR #2679's. The local L-system and sandpile work this plan builds on is in
the author's `prime/` research directory (not part of the repository); its verdicts are summarised in `planning/BRIEF.md`.

No new κ; nothing here is a verification of the full multiplication theorem; the sandpile vocabulary is a reading aid and the plan's
own exactness audit ranks the mappings ("never call it a new method").

Prepared by Marius-Paul Dumitrean with substantial AI assistance (Anthropic Claude, via Claude Code). Apache-2.0.
