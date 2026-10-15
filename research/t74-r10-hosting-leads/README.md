# Hosting leads on #2802's words (research notes and code, no κ claim)

Notes and code from one research round on the words of PR #2802 (conditional κ 0.001717794984118634663827: #2751's
joint twelve-source words + #2766's frame refit + seven retired-lender aliases with two hostee moves). This branch is
based on #2802's head, so the package `research/t74-joint-twelve-retired7/` (words, fill, pinned auditor) is present.
Nothing here changes or claims κ; it records what was tried, the obstructions found, and one open lead.

## Contents

| path | what |
|---|---|
| `J-dim1/REPORT.md` | low-floor lenders for the 48 width-8 followers: obstruction map, a new exact hosting mechanism, the open lead |
| `J-dim1/code/` | screens, builders, frame-bound tools, relaxations (`*.py`); see provenance below |
| `J-dim1/out/` | census, cap chains, gap map, screens, relaxations, and certified hosted words `out/eh/w-*.json.gz` |
| `J-dim1/base-words/` | the two certified double-move words the lane started from (the #2802 construction; #2802's rebuilt package words differ only in how `cleanup`, `warps` and `removed` are serialised) |
| `deps/toolkit-rev3/` | our #1186 exact frame toolkit, revision 3 (certified `frames.optimal_frames`) |
| `context/` | the round's other lanes: F (the #2802 construction), G (unlock rewrites), H (width cuts), I (restorable helpers): all others null |

## Requirements and smoke test

Python 3.12+; `numpy`, `scipy` and `mpmath` for the relaxations, the standard library otherwise. Run from the repository root.

```sh
J=research/t74-r10-hosting-leads/J-dim1
# certified optimal frames (#1186 toolkit) + the pinned PR2679 auditor on a stored hosted word (about 1 s)
python3 -B $J/code/price_words.py /tmp/PRICE.json $J/out/eh/w-b-473_277.json.gz
# owner-fill pattern relaxations (upper bounds); the second reproduces out/RELAX-host7.json byte for byte
python3 -B $J/code/relax_host.py /tmp/RELAX-host.json      # merged width 9: about -1.96e-7 per hosting
python3 -B $J/code/relax_host7.py /tmp/RELAX-host7.json    # host kept cold (4,8)->7: +8.70e-7 per hosting
# screen, build and undo check on the base word (extra word: e-30_564_667-31_565_669.cert.json.gz)
W=$J/base-words/b-30_564_667-31_565_669.cert.json.gz
python3 -B $J/code/ehost_screen.py $J/code $W /tmp/EHOST-b.json
python3 -B $J/code/ehost_build2.py $W /tmp/eh 473:277          # hostee:host pairs, comma-separated; optional 4th arg 'hyper'
python3 -B $J/code/undo_check.py $W /tmp/EHOST-b.json
```

`J-dim1/code/borrow_price.py` resolves its dependencies from the repository root. Overrides: `IMB_TOOLKIT` (toolkit
directory), `IMB_AUDITOR` (default `research/t74-joint-twelve-retired7/vendor/audit_local_pr2679.py`), `IMB_ROOT`, and
`IMB_PR2745_PKG` for `borrow_price.native()`, which needs #2745's package
(`git fetch origin pull/2745/head && git archive 4f485de0 research/gmx-t74-borrow43-handoff | tar -x`).

## The open lead

The new mechanism (all of `J-dim1/REPORT.md`, 40 hostees x 26 width-4 cold hosts screened, every built word passes the
pinned auditor): an entering width-8 hostee's anticipatory target reads become dyadic initial corrections pulled back
through the precondition, and the hostee is renamed into a cold width-4 host from its first write, with one warp
`U_host -> E <= hi(first write)`. The best local change is one rank-3 piece fewer per call, but the merged register ends
at full width, so the inventory moves (4,8) -> 9 and the relaxation is negative.

If the host could stay cold (restored at its own end frame, (4,8) -> 7), the same relaxation gives **+8.70e-7 per
hosting** (an upper bound). That needs an exact undo of the hostee's writes before the host's end; `undo_check.py` shows
every first-write source is rewritten twice before the final read, so a direct `host -= c*q` is not available. A
backward replay that rebuilds the old value from current registers (2-3 gates; see `context/I-restore-REPORT.md`, where
it is auditor-verified for restored helpers at a full end frame) is the natural next attempt; price any hit with
certified frames plus the relaxation, then a literal owner fill and the exact root against 0.001717794984118634663827.

## Provenance and credits

- `J-dim1/code/{word_patch,alias_build,refit,bounds,audit_local,wordmodel}.py` are byte-identical copies from PR #2745
  (jeremykothe2), `research/gmx-t74-borrow43-handoff` at `4f485de0` (lineage #2474 and #2679/#2559, philippeVV); its
  notice is retained as `J-dim1/code/NOTICE-PR2745`.
- The pinned auditor is #2802's `vendor/audit_local_pr2679.py` (byte-identical to #2679's).
- `deps/toolkit-rev3/` is our #1186 toolkit; `borrow_price.py` and the remaining scripts were written in this program.
- Words and lineage: tekuuu (#2751), DavidAriasC (#2766), mason-hale (#2696), 1337isnot1337 (#2226), philippeVV
  (#2679), jeremykothe2 (#2673/#2745), Vlado-V (#2322); see #2802's `SOURCE-NOTICE`.

Prepared by Marius-Paul Dumitrean with substantial AI assistance (Anthropic Claude, via Claude Code). Apache-2.0.
