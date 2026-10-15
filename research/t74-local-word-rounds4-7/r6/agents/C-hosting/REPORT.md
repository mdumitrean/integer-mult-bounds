# r6 / C-hosting: hosting-side admission path for a narrowed width-9 helper

Agent C-hosting, round r6 (2026-10-15, 03:35–04:15Z). Task: prepare the T74 hosting side so that a local word with one
width-9 helper narrowed to width 8 (constructed in parallel by A-zero478 / B-zero502) can become a full κ claim. Local only:
nothing committed, pushed or posted. Paths below are relative to `scratchpad/`.

**Outcome.** A valid narrowed-inventory owner map exists and passes PR1319's own independent checker:
`r6/agents/C-hosting/out/R1-final-478/OWNERS.json.gz`. If the narrowed words save exactly c1 per call (H1 −1, the class
of helpers 478/479/490/491), it raises the certified complex endpoint by **+8.358e-8** (native and conservative), i.e.
κ ≈ +8.36e-8 on the #2220 line (κ = C − 1/F − B). It tolerates at most **≈3,728 units/call** of extra local cost from the
edit that zeroes the helper's entrance response. r5 C's pattern-level optimum (11,478,864 units, +3.8e-7) is **not**
reachable by local edits of the current owner map; it needs a re-solved owner assignment (details in §3).

## 1. What an owner map and PLAN must pass in the strict T74 replay
From PR1319's `verify.py`, `replay.py`, `audit_mixed.py`, `independent_core.py`, `lift_parent.py`, `freeze_spec.py`,
`geometry_controls.py` (vendored in `wt-566/research/global-mixed-t74-exact-fill`):
- **Package (`verify.py`):** MANIFEST pins; retained predecessor admission; the owner constructor must reproduce
  OWNERS/ORDER/DISPATCH/PROFILE byte for byte; the parent lift must reproduce GLOBAL-TEMPLATE, PLAN, CONSTRUCTION and the
  SPEC geometry.
- **bind:** provider natives bound to PLAN `provider_registry` (widths, `actual_paid_profile`, artifact and program hashes)
  and SPEC `providers.*` (inventory, expected_profile, entering, entrance, width_digest, program_hashes, artifacts,
  complete_contract, wrappers, native_negative_controls, phase_edges, semantic_phase_sha256, expected_local).
- **emit / audit (`audit_allcold.py --mutation-controls`):** emitted controller; 15 mutations rejected; hosted residuals
  (319,680), complete invocations, orthogonal 73-column maps (= SPEC `actual_73column_sigmas`), cross-replica helper roles.
- **invoice:** global prefix bits < charged bits (1,441 < 2,048); physical row coefficient < 20,161; strict finite checks.
- **assembly:** both exact moment engines → complex_lower / conservative; 47 strict outer inequalities; κ.
- **admission controls** (114 = 32 + Σ_providers(17 + |inv|(|inv|−1) + |width_spot_helpers|)) and **bit controls** (12).
- **independent (`audit_mixed.py` → `independent_core`):** native status and word binding; common ports and ordered centre
  frames; ordered provider widths = PLAN widths; local paid-profile and width recount; dispatch = PLAN `provider_calls`;
  disjoint pending child axes per family; and in `check_roles`: role coordinates and invocation time; whole-helper width =
  the call's provider width; private namespace; physical family identity (copy and family formula); strict bridge-aware
  idle window; no aliasing of the call's active data pair; distinct helper and family per call; slice inside capacity, no
  overlap; pending-axis chart binding; complete per-call helper inventory; contiguous prefix (no gaps); idle profile =
  CONSTRUCTION idle; rank deficit 73·live − mass = 320·T; 9T bridges; prefix reserve; row < 20,161 and M² > 2·max(profile)²;
  8 rejected controls (7 + wrong provider). Also: independent profile = assembly complex profile = PLAN profile.
- **geometry controls:** 6 understated-charge mutations rejected by the assembly.

## 2. The narrowed owner map (R1-final)
**Construction (`scripts/greedy_r1.py`, `scripts/build_owners.py`).** No role leaves its bin. In every call, one of its
240 width-9 slots becomes width 8 and is relabelled helper 254 (= register 478) by swapping helper ids with the slot that
held 254 (660 swaps). Offsets are re-stacked in each affected bin, keeping the original slice order. The greedy (400
seeded trials) concentrates the freed cells: it repeatedly takes the bin with the most still-unnarrowed width-9 calls.
Every bin hosts exactly the same calls as before; cross-replica helper roles stay 296,300. Dispatch is unchanged (249/417).

**Verification (`scripts/ctx.py`, `scripts/sanity.py`).** PR1319's unchanged `check_roles` and `controls` run on a context
built from the retained fresh T74 replay (`r2/full566b`), with the narrowed provider widths and paid profiles:
- Sanity: the current owner map passes with the 566+554 provider profiles and reproduces #1672's PLAN profile exactly.
- R1-final: `PASS_INDEPENDENT_VARIABLE_T_LITERAL_WINDOWS_CHARTS_PREFIX_ROW`; all 8 controls rejected (incl. wrong provider);
  idle {1:59, 2:41, 3:99, 4:57, 48:22,748}; profile H1 1,559,825, H2 336,377, H3 278,823, H4 84,969, H5 54,612,
  H8 5,328, H48 22,748; rank mass 4,816,512 (unchanged); 11,605 charts (was 11,142); prefix 1,441 < 2,048; row 19,545.
- The same pick also passes for helpers 479, 490 and 491. Helpers 502/503/515 save only 2,109,673, so this fill would lose
  2,032,997 units with them.

**Value (`scripts/endpoint.py`, retained moment engines).** Current certified complex lower 0.00167975495612554452…
(the supplier's C); R1-final 0.00167983853566806388…: **+8.3580e-8** native, **+8.3580e-8** conservative. In units:
local saving 666·c1 = 1,409,558,364 against idle cost 1,407,075,215 → net 2,483,149 (≈3,728 per call). The edit that
zeroes the entrance response must therefore cost less than ≈3,728 units/call on average (r5 C's 17k break-even applies
only to its pattern optimum).

**Candidate files:** `out/R1-final-478/OWNERS.json.gz` (content sha256 cd850982…), `PLAN-CANDIDATE.json` (#1672's PLAN with
narrowed widths, per-call widths, profile, owner hashes; fields that must come from the new native words are listed under
`pending_from_new_native_words`), `SPEC-DELTA.json` (expected idle, global profile, chart count; provider
entering/entrance +1; everything else from discovery + `freeze_spec.py`), `PROVIDER-WIDTHS.json`, `CHECK.json`.

## 3. Why r5 C's optimum is not reached here
- **Pattern level (`scripts/minchange.py`):** the 11,478,864 optimum (dispatch 299/367) needs at least **218** bins to
  change composition: 200 (5,9,9,9) → 144 (8,8,8,8) + 54 (4,4,4,4,8,8) + 2 (4,9,9,9)+1, and 18 (4,8,9,9,9,9) → empty.
  Gains of ~5–8M need at least 167 changed bins.
- **Role level, the owner map is clustered (`out/CLUSTERING.json`):** each region of cap-48 bins sharing a window holds
  width-9 roles of only 4–15 distinct calls (median 6), and an extra call's 48 (5,9,9,9) bins share the same three width-9
  calls (only 1 of 417 extra calls has four disjoint ones). Since each call narrows exactly one slot:
  - R2 (empty a 48-bin by repacking 12 bins of one region): 0 feasible moves.
  - R3 (switch extra calls to the base word with in-place shrinks): 1 feasible switch.
- **The general move needed:** relocate whole roles across children and owners (windows overlap, e.g. owner 0's cap-48
  children 12/13 cover calls 53–852 and cap-32 children 14/15 cover 215–852), re-clustering which calls share bins. That
  is a re-solve of the owner assignment for the narrowed inventories (a pattern-flow/LNS constructor over all widths with
  windows, families, active pairs and prefix stacking), not an alternating-path edit; PR1319's `reconstruct.py` only moves
  width-4/5 roles.

## 4. What remains for a full claim
1. New provider words (A-zero478 / B-zero502): helper narrowed to (8,1,9), entrance response zeroed, `audit_local.py --main`
   PASS, extra local cost ≤ ≈3,728 units/call on average (for R1-final).
2. Native admission of both words (fresh natives; adapters regenerate) → PLAN `provider_registry` artifact/program hashes
   and `actual_paid_profile`, `provider_calls[*].local_program_sha256` (rebind as in the #1625 `rebind.py`).
3. Owner constructor in the package (this greedy, seeded) reproducing `OWNERS.json.gz`; PLAN and CONSTRUCTION (idle
   above); parent and windows unchanged (no lift needed: same T, order and bins).
4. SPEC via `replay.py --discover` + `freeze_spec.py` (idle profile, 11,605 charts, provider entering/entrance, κ).
5. PR1319's strict T74 replay with all controls (114/12/15/8/6), then the outer assembly on the #2044/#2220 line.
6. For more value: a re-solved owner map toward the 218-bin optimum (+3.8e-7 at zero extra local cost).

## Evidence
`EVIDENCE.json` (summary); `out/`: SANITY-current, R1-final-478/{OWNERS.json.gz, CHECK, PLAN-CANDIDATE, SPEC-DELTA,
PROVIDER-WIDTHS}, GREEDY-R1-478(-s2) (picks), R1-478/FILL.json (CP-SAT attempt, 1.59M), R1g-478/CHECK.json (60-trial
greedy), ENDPOINT-R1-final / ENDPOINT-R1g, MINCHANGE, CLUSTERING, PROFILE-current. Scripts: `ctx.py`, `sanity.py`,
`fill_r1.py`, `greedy_r1.py`, `build_owners.py`, `endpoint.py`, `minchange.py`, `fill_r2.py`, `fill_r3.py`,
`plan_candidate.py`. At most 1 worker per run; CP-SAT single-threaded; peak memory well under 2 GiB.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
