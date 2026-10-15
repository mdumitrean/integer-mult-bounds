# r5 / C-packing: the T74 hosting packing of the 566+554 supplier

Agent C-packing, round r5 (2026-10-15, 03:05–03:45Z). Inputs: PR1319's package as stacked in `wt-566`
(`research/global-mixed-t74-exact-fill`: PLAN, OWNERS, ORDER, DISPATCH, reconstruct.py, independent_core.py), the words
`r3/inputs/{gauge44,extra}-word-566-554.json.gz`, toolkit rev3 (`toolkit/`), b = 0.001679754956125544. Local only:
nothing committed, pushed or posted. The owner map is byte-identical along the #1319 → #1625 → #1672 → #2044/#2180/#2220
line (kernels do not change widths), so every statement here applies to the current top supplier.

**Outcome: scoped negative, with two structural results. κ is unchanged.**
1. The current fill is optimal over every packing of the current width inventories, even ignoring windows and families.
2. The dispatch of 417 extra calls is forced by a "9-tightness" inequality, for any replica count.
The only packing-side lever left is changing the inventories; every profitable change is either frame-infeasible or blocked
by the auditor's entrance rule. Unblocking one width-9 helper would be worth about +3.8e-7 κ (≈ 9 kernels).

## 1. Packing model (validated exactly)
From `reconstruct.py` and `independent_core.check_roles`:
- **Bins:** (owner replica, child, port). 74 replicas × 18 idle children × 112 ports = **149,184 bins** (= `parent_idle`).
  Child capacities 8/16/32/48 (6/4/4/4 children per replica). Each child has a strict time window of calls.
- **Roles:** every call hosts its 480 helpers as whole-helper widths (319,680 roles). A role sits in a bin whose window
  contains its call; a call uses each physical family at most once, family = owner·896 + (2·pair + side)·112 + port;
  no aliasing of the call's active data pair; slices stacked contiguously from offset 0 (pending prefix).
- **Cost:** each bin's leftover capacity is one idle jump of rank = remainder; global profile = idle + Σ provider paid
  profiles; rank mass = 73·live − 320·T = 4,816,512 (fixed by the geometry).
- **Validation** (`scripts/pmodel.py`, `out/VALIDATION.json`): reproduces idle {48: 22,748}, the PLAN profile, rank mass,
  dispatch 249/417, capacity 3,580,416 vs role width 2,488,512; every role passes window/family/width checks.
- **The fill is extremely regular** (`scripts/analyze.py`): cap 8: (8)×41,112, (4,4)×8,616; cap 16: (7,9)×20,948,
  (8,8)×12,204; cap 32: (5,9,9,9)×30,972, (7,7,9,9)×2,180; cap 48: empty×22,748, (4,8,9,9,9,9)×10,404. The extra
  provider's 1,668 upgraded roles (helpers 403/405/406/407, 4→5) all sit in (5,9,9,9) bins.

## 2. Exact costs at b (`scripts/costs.py`, `out/COSTS.json`)
c[1] = 2,116,454 … c[48] = 100,931,344, i.e. **2,102,736 per unit for an empty 48-bin**, against 2,114,588 per unit for
the extra word's upgrades and 2,116,454 for an H1 hole. Every remainder ≥ 2 is cheaper per unit than an upgrade.

## 3. The current fill is optimal at the pattern level (`scripts/pattern_opt.py`, `out/PATTERN-OPT.json`)
Relaxation: all multisets of widths {4,5,7,8,9} per bin capacity, **partial bins allowed** (remainder priced c[rem]),
free dispatch n_extra ∈ [0,666], exact width inventories; no windows, families or call identity (necessary conditions only).
CP-SAT proves the optimum **equals the current fill**: objective 2,299,513,346,096 = bound, same eight compositions,
n_extra = 417. Other dispatches are strictly worse (405: +89,568; 200: +1,619,688; 0: +3,112,488 units).

## 4. Why 417 extra calls are forced: 9-tightness
In 8/16/32-bins a width-9 role needs odd partners (widths ≡ 0 mod 4 or 8 cannot complete it): at most 3 nines per 5 and
1 per 7; a 48-bin holds at most 4. Hence every exact fill satisfies **n9 ≤ 3·n5 + n7 + 4·(non-empty 48-bins)**, and the
current fill meets it with equality: 159,840 = 92,916 + 25,308 + 41,616. With mass balance this gives
**n_extra ≥ (69.5·3/37)·T = 5.635·T**: at least 62.6% of calls must be extra for every replica count T. T = 74 meets the
bound with equality (417.0), which is why it is the exact fill; further replication cannot help.

## 5. Inventory changes: what would pay (`scripts/conv_breakeven*.py`, `out/CONV-BREAKEVEN*.json`)
Allowing K conversions w → w' at a local saving s per level:
- **5→4 never pays** (each 5 carries three 9s): K = 0 at every s up to 2,111,000.
- **9→8, 8→7, 9→7, 9→5, 4→3, 8→6** each gain **19.77M units at exactly s = 2,102,736** (the H48 per-unit cost): the relaxed
  9-tightness lets the extra word disappear (417 × 47,407 = extra premium over consolidated idle). 7→6 gains 10.9M.
  Every unit of saving above 2,102,736 adds K·(s − 2,102,736).

## 6. Local feasibility of those changes (base word; exact optimal frames, cone caps recomputed)
| Change | Candidates | Feasible | Saving per level | Verdict |
|---|---:|---:|---|---|
| (9,0,9) → (8,1,9), start frame += a vector of the helper's first frame | 288 | 153 (117 helpers) | 2,116,454 (= c1, the rank-1 first jump vanishes) or 2,109,673 | frame-feasible but **all blocked**: see below |
| (8,·,·) and (7,·,·) start side, first-frame vectors | 711 | 0 | — | infeasible |
| (4,0,4) and (4,5,9) start side, every extension inside the end frame | 660 | 0 | — | infeasible |
| Low-end (4,0,4)/(7,0,7)/(8,0,8) end side, every hyperplane | 3,536 | 8 (all (8,0,8)) | 2,094,255 ×4, 2,072,056 ×4 | below break-even; mix optimum unchanged (`out/MIX-E*.json`) |

**The entrance rule.** `audit_local.py` requires that no compensation gate reads an entering helper ("nonzero entrance
response") and that the precondition/compensation touch no entering or cold-end helper. The derived compensation (7,208
gates) reads **exactly the 240 (9,0,9) helpers and no other type** (`out/ENTRANCE-FILTER.json`). So every frame-feasible
width-9 start-side narrowing is auditor-invalid as the program stands; an end-side one would make the helper a cold end,
which the compensation may not touch either.

## 7. Value of unblocking width-9 helpers (`scripts/mix_opt.py`, `out/MIX-J*.json`)
If J width-9 helpers per word could be narrowed to (8,1,9) at saving c1 (entrance response zeroed at no cost):
| J | Optimal dispatch | Gain (units) | κ estimate |
|---:|---|---:|---:|
| 1 | 299 narrowed-base / 367 narrowed-extra | 11,478,864 | +3.8e-7 |
| 3 | 398 / 268 | 34,444,056 | +1.15e-6 |
| 12 | 666 / 0 (extra word gone) | 129,341,346 | +4.3e-6 |
(κ per unit ≈ 4.1e-8 / (1,850·666), calibrated on the helper-donor kernel; pattern-level, so realizability by an owner map
is a further obligation.) Each helper's dirt reaches 4–72 port rows (`out/LEAKS.json`); among the 117 frame-feasible ones,
7 leak into only 4 rows: 478, 479, 490, 491, 502, 503, 515.

## 8. Admission path for any future inventory change
New provider word(s) with changed `start_extra`/`helper_final` → native provider admission (adapters regenerate) →
PLAN provider registry (widths, entrance rank) → a **new owner map**: PR1319's `reconstruct.py` only moves width-4/5 roles
along alternating paths, so a general exact-fill constructor over all widths is needed (windows, families, active-pair rule,
prefix stacking) → SPEC (idle profile, 73-axis chart count) → PR1319's strict T74 replay → outer assembly (#2044 line).

## Best next step
Zero the entrance response of one of the seven 4-leak width-9 helpers (e.g. cancel its four port-row leaks with exact
`y −= a·q` reads where q holds its initial value), then narrow it to (8,1,9). Success test: the edited word passes
`audit_local.py --main` with that helper entering and costs less than about 17k units per call above the base word on
both words (its value in §7). This is a local-word edit (compensation/port-dirt lanes), not a packing change.

## Evidence
`EVIDENCE.json` (summary of all results); `out/`: VALIDATION, COSTS, PATTERN-OPT, CONV-BREAKEVEN(2), NARROW-TASKS +
NARROW-base.jsonl, NARROW4-*, ENDNARROW-*, ENTRANCE-FILTER, LEAKS, MIX-J1/J3/J12, MIX-E1/E4, words-*.json.
Scripts: `pmodel.py`, `analyze.py`, `costs.py`, `pcore.py`, `patterns.py`, `pattern_opt.py`, `conv_breakeven.py`,
`conv_breakeven2.py`, `mix_opt.py`, `narrow_tasks.py`, `narrow4_tasks.py`, `endnarrow_tasks.py`, `narrow_sweep.py`,
`narrow_sweep2.py`, `joint_narrow.py` (stopped: moot after the entrance filter), `wcore.py` (r4 D's). At most 3 workers,
per-task deadlines, RSS flag at 6 GiB; CP-SAT single-threaded.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
