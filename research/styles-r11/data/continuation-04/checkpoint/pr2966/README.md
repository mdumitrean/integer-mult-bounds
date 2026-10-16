# Fourteen declared gate rewrites on PR #2942's words: conditional κ = 0.001724034272523452177412 − 10⁻⁴⁶ − 10⁻⁷⁰

**Credit first: PR #2942 (mdumitrean, Marius-Paul Dumitrean) is the base.** Its words (PR #2917's (mason-hale) words plus four
normal-45 paired extractions, on PR #2908's (jeremydiviney) construction), its normal-45 overlay stage, its literal T74
allocation (fill, order, dispatch), its cap certificate and its checkers are used unchanged except as listed below. PR #2930
(mdumitrean) is the comparator of the admission. **Ours (Jeremy Kothe (jeremykothe2), with AI assistance)**: a declared
source-bound stage (`rewrite/`, `tools/build_rewrites.py`, stage `declared-rewrite-stage` of `reproduce.py`) of fourteen
exactness-preserving gate rewrites in five classes, an independent reviewer with 16 semantic tamper controls per word, and the
re-derived paid profile and cap certificate.

```text
Status / UTC update / priority revision: DONE (conditional candidate) · 2026-10-17
Concrete question and changed premise: PR #2942's words are the leading record. Which exactness-preserving gate rewrites of
    those words lower the paid local profile without changing the width inventory or the private-buffer count?
Established result and evidence status: fourteen declared rewrites (R-retime ×4, A3779-cut-start-read ×1,
    PM-carrier-lender-entry ×2, B-carrier-retime ×2, A-commuting-swap ×5) move the local profile per call from
    {1:2434, 2:632, 3:286, 4:104, 5:26, 8:8} to {1:2430, 2:628, 3:282, 4:110, 5:26, 8:8} (same rank mass, same inventory
    {4:26, 5:2, 7:62, 8:100, 9:218}, same 86 private buffers). PR #2942's literal allocation is unchanged and stays valid; its
    complete paid profile is re-derived. The complete fresh-native admission and the modern outer release pass:
    κ = 0.001724034272523452177412 − 10⁻⁴⁶ − 10⁻⁷⁰ ≈ 1.2180e-6 above PR #2942 (head a027b0f6), ≈ 6.778e-7 above the
    nine-rewrite package on PR #2930's words and ≈ 1.5344e-6 above PR #2930. Author-checked (AI-assisted); not maintainer-reviewed.
Public artifact URL + exact commit: this package (see the PR).
Next useful task: more gate rewrites in these classes; an integral packing above the class optimum (see below).
Active claim / expiry: released.
```

## Result

| | κ (headline) | local profile per call | width inventory | buffers | complete paid profile (T74) |
|---|---|---|---|---:|---|
| PR #2930 | 0.001722499906443274564357 − 10⁻⁴⁶ − 10⁻⁷⁰ | {1:2416, 2:640, 3:280, 4:110, 5:26, 8:8} | {4:26, 5:2, 7:62, 8:96, 9:222} | 82 | {1:1626372, 2:426240, 3:192474, 4:73260, 5:24198, 8:5328, 48:27158} |
| PR #2942 | 0.001722816319863214327996 − 10⁻⁴⁶ − 10⁻⁷⁰ | {1:2434, 2:632, 3:286, 4:104, 5:26, 8:8} | {4:26, 5:2, 7:62, 8:100, 9:218} | 86 | {1:1638360, 2:420912, 3:196337, 4:69264, 5:23531, 8:5328, 14:1, 48:27291} |
| **this package** | **0.001724034272523452177412 − 10⁻⁴⁶ − 10⁻⁷⁰** | **{1:2430, 2:628, 3:282, 4:110, 5:26, 8:8}** | same as PR #2942 | 86 | **{1:1635696, 2:418248, 3:193673, 4:73260, 5:23531, 8:5328, 14:1, 48:27291}** |

The paid profile is `old − 666·old_local + 666·new_local` (666 calls); the idle children (`allocation/FILL.json.gz`,
`ORDER.json`, `DISPATCH.json`) are PR #2942's byte-for-byte, because the rewrites keep every helper width. Physical stock
66,808; 632 independent inputs; 408 live helpers; 271,728 helper roles.

## The rewrites

`rewrite/REWRITES.json` lists 14 rewrites (61 literal hunks), each a set of edits addressed by index in PR #2942's word and
checked against the exact old gates (`rewrite/declared_rewrites.py`, pure, applied by the source's own `rebuild_borrow.py`
after PR #2942's `normal45-paired-extractions` stage; the step name is `declared-fourteen-rewrites`). Compensation, helper
endpoints, buffers and widths are unchanged; the paid profile, inventory, warp positions and cleanup are re-derived by the
inherited frame rules.

* **R-retime** (4): the carrier entry of a restored helper is moved earlier and its later duplicate deleted.
* **A3779-cut-start-read** (1): one read is moved to the start of the cut.
* **PM-carrier-lender-entry** (2): PreloadMove carrier entries are taken from lender registers.
* **B-carrier-retime** (2): a PreloadMove carrier raise in phase B is replaced by the same lender gate at its unraised frame in
  phase A; the B-position of every phase warp is shifted by the number of deleted B gates before it.
* **A-commuting-swap** (5): five consecutive adds on distinct registers are swapped and the moved gate's frame is re-solved.

`rewrite/rewrites_review.py` does not import the producer. It requires each shipped word to differ from PR #2942's word only
in the declared hunks (plus the derived report/cleanup) and then runs the inherited exact auditor (PR #2833's, forward and dual
over all 632 inputs) on the candidate and on 16 tampered copies per word (at least two per class: dropped or sign-flipped
gates, wrong lender, kept B gate, unresolved frame, wrong swap pair, dropped moved gate, restore kept, stale cleanup); every
tampered copy is rejected (`evidence/REWRITE-REVIEW.json`). The review runs in `run_registered.py`, in the admitted source's
own `verify.py` (stage `declared-rewrite-review`, inside the release), and the reproduction audits both final words again.

## Packing check

PR #2942's cap certificate is for its own local profile and a *fractional* optimum at T74. `certificates/RELAX-CAP.json` is
updated to this package's local profile (same nine-pattern basis, same inventory: the exact basis verifies,
`tools/relax_exact.py`): cap ∈ [0.0017240352247481048785505, 0.0017240352247481048785506], and the literal root of the
re-derived profile is 9.5222e-10 below it (`check_cap.py`, three controls). Independently of the shipped fill we solved the
class-level integer program over all 1,163 patterns (bins 672/448/448/448 per replica at T74, every width placed, cost =
the idle child's contribution at the headline κ, HiGHS MILP to proven optimality): its idle profile
{1:17316, 3:5861, 5:6215, 14:1, 48:27291} equals PR #2942's shipped one exactly, hence the re-derived profile and the root
are the integral optimum of that class model and no repack of this inventory with one idle child per bin can improve it.
(Not a claim about allocations outside the model.)

## Verification

**Registered, bounded** (`run_registered.py`): package pins; PR #2942's `verify.py` (producer rebuild of the unrewritten words,
structure certificate, 40 semantic controls); the rewrite review above; `check_allocation.py` on the rewritten words (owner
geometry with five controls, exact moment with PR #2930's headline); `check_cap.py`; binding of the stored overlay, rewrite,
native, admission and release receipts in `evidence/` to the exact words, allocation and claim.

**Complete replay** (`reproduce.py`, run by `verify_release.py` after the exact gates against PR2827 … PR2942 and the
nine-rewrite package): exact Git exports of PR2908, PR2917, PR2930 and through them PR2894 and PR2833; fresh retained bootstrap;
PR2857's four-kernel stage, PR2894's preload stage, PR2908's paired stage, PR2917's extension stage; PR #2942's
`normal45-paired-extractions` overlay (manifest 79956f19, 637 files, byte-identical to PR #2942's); the declared rewrite
stage (manifest f18779d9, 642 files); closed adapters for 86 buffers; fresh native chains for both providers; complete
admission and the modern outer release. `reproduce.py` runs its stages with a text-write LF adapter on the process, so the
derived manifests are the same on Windows and POSIX.

`evidence/` holds one development run of `reproduce.py` on Windows, CPython 3.12 with an explicitly reused authenticated
retained cache (`--retained`; every changed-word native chain, the admission and the release fresh): native chains 84.5 s,
admission 487.3 s, 595 s wall, ending `PASS_NORMAL45_COMPLETE_REPLAY`. It ran on this package before the evidence files were
added (the final inventory assertion compares the package with its manifest at the start of the run). The complete
no-cache `verify_release.py` runs (Windows and WSL Ubuntu) are separate; their times are in the PR description.
PR #2942's own evidence is kept in `evidence/pr2942/` (its macOS arm64 run).

```sh
python3.12 -B research/paired-extension-normal45-rewrites/verify_release.py --main . --work /tmp/n45rw --python python3.12
```

`--main` is a checkout with the predecessor commits present (no network during the replay). Needs Python 3.12 with numpy,
scipy, sympy, mpmath, gmpy2 and psutil (`evidence/ENVIRONMENT.json`).

## Scope

Conditional finite supplier and modern outer certificate, exactly as inherited by PR #2942, #2930 and #2917; all inherited
all-size, compiler, hosting, precision and analytic hypotheses remain. No selected-frontier change, no unconditional
multiplication theorem and no independent human review is claimed.

## Credit

Marius-Paul Dumitrean (PR #2942, #2930): the base words, overlay, literal allocation, cap certificate and checkers;
Mason Hale (PR #2917); Jeremy Diviney (PR #2908); Jeremy Kothe (PR #2894/#2833: supplier, frame accounting and cleanup,
`vendor/preload_move.py`, source tools); Yiyang Lu (PR #2857/#2848); Dugongue (PR #2863/#2839); Tekalign; icekylinx
(`vendor/audit_local.py`). New here: Jeremy Kothe (jeremykothe2), with AI assistance. See `CREDITS.md` and `NOTICE`. Apache-2.0.
