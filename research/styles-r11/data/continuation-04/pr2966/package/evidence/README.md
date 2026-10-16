# Provenance of the files in this directory

`ADMISSION-RESULT.json`, `ADMISSION-STAGES.json`, `RELEASE-RECEIPT.json`, `FULL-NATIVE-*`, `ENVIRONMENT.json`, `RUNTIME-PATCHES.json`,
`ADAPTER-DERIVATION.json`, `OVERLAY-DERIVATION.json` (PR2942's normal-45 stage, byte-identical to its own), `REWRITE-DERIVATION.json`
(the declared fourteen-rewrite stage), `FULL-REPLAY-STAGES.json` and `FULL-REPLAY-RESULT.json` come from ONE development run of
`reproduce.py` on Windows with an explicitly reused, authenticated retained-native cache (`--retained`). In that run the changed words'
native chains, the complete admission and the outer release were fresh. The run used this package without these evidence files (the
final inventory assertion of `reproduce.py` compares the package with its manifest at the start of the run).
`REWRITE-REVIEW.json` is the output of `rewrite/rewrites_review.py` on the shipped words; `run_registered.py` re-runs it and requires
equality.

The complete NO-CACHE `verify_release.py` runs (fresh retained bootstrap, fresh native chains, complete admission and outer release;
Windows and WSL Ubuntu) are separate; their pass times are listed in the PR description and their receipts are not stored here.

`evidence/pr2942/` is the inherited record of PR2942's own run (its words, allocation and cap certificate, macOS arm64), kept for
reference. `check_cap.py` and `certificates/` are updated to this package's local profile.
