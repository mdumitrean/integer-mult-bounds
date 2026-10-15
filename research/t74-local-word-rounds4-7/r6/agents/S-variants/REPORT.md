# r6 / S-variants: profitable local edits on the 45 equal-cost extra-word interfaces?

Agent S-variants, round r6 (2026-10-15, 08:21–09:20Z). Words: `r3/inputs/{gauge44,extra}-word-566-554.json.gz`.
Toolkit `r3/toolkit-rev3` (#1186 rev3), b = 0.001679754956125544. Local only: nothing committed, pushed or posted.

**Outcome: scoped negative. No variant admits a profitable local edit in the searched families; κ is unchanged.**

## 1. The 45 variants
r4 D-widths found 15 equal-cost hyperplanes in each of three (5,9) helper groups. Each group has 4 width-4 members and
4 width-8 readers, and 12 early B reads (each reader reads three members before their first writes):
- G1: members 619/621/622/623, readers 616/617/618/620, reads B457–B468, first writes B1088–B1092.
- G2: members 627/629/630/631, readers 624/625/626/628, reads B397–B408, first writes B1096–B1100 (the current extra word
  uses G2 with level 390 dropped).
- G3: members 651/653/654/655, readers 648/649/650/652, reads B445–B456, first writes B1120–B1124.

All 45 were built from the base word (start frames of the 4 members reduced to the hyperplane, exact optimal frames
re-solved and written back; `scripts/build_variants.py`, `words/`). Every one prices at exactly the extra word's cost,
11,691,748,602 (base + 8,458,352), certified, inventory {4:40, 5:48, 7:38, 8:114, 9:240}, and differs from the base word
in exactly the 12 frames of its group's early reads (no tail change).

## 2. Screens and results

| Screen | Scope | Result |
|---|---|---|
| Reader-read relaxations: 12 singles, 4 reader triples, all 12 | all 45 variants + base + extra (867 solves) | one signature for all 45: singles 0, triples −11,938, all 12 −47,752 (= the extra word's; base −8,879 / −35,516) |
| Relaxation of every B add gate touching the group's 8 registers (52–56 gates) | base, extra, 5 representatives | identical to base except one G3 variant |
| Relaxation of the group-region large-gain gates (16 per group) | all 45 variants | exactly one outlier per group (below); the other 42 equal base |
| Multi-deletion projected split-key (r6 M's sk5/run5: sentinels kept, cone-aware, re-reads banned) | reader triples + all 12, on 6 words: 2 per group, incl. the current extra word and the G3 outlier | 30/30 INFEASIBLE (7,459–19,432 candidates, all shape-feasible) |
| Exact commuting relocations of the G3 outlier's 16 gates | outlier + base control | 160 priced: all Δ = 0 or frame-infeasible on both words |
| First-order kernels for the outliers' enlarged deletions (projected split-key, budget = gain − 1) | 3 outliers, 2 reps per class | first-write deletions shape-infeasible; delivery deletions: 8 exact window proposals, all priced Δ = 0 (compensation 7,208); rest INFEASIBLE |

**The outliers.** In each group exactly one hyperplane changes the relaxation of 16 gates (the group's 8 first writes
and 8 port deliveries from the group's registers):
- G3 `651-655-30-96-139-267`: B1117–B1124 −19,037 → −22,096; deliveries B1647.. −9,850 → −12,256 (certified).
- G1 `619-623-24-96-132-260`: B1085–B1088 −20,893 → −23,952; B1089–B1092 −19,037 → −20,893; deliveries B1519.. −9,850 →
  −11,053 (the last two classes uncertified).
- G2 `627-631-24-34-68-390`: the same pattern at B1093–B1100 and B1551.. (this is not the current extra word, which drops 390).

The larger deletion savings are not realisable: every exact relocation and every exact window compensation found costs
the larger saving back exactly (Δ = 0), and the first-write deletions admit no compensation shape at all.

## 3. Hosting note
A gain on a G1 or G3 variant would move the extra word's 4 width-5 upgrades to other helper indices: the provider's
widths list changes and PR1319's reconstruct.py would relabel width-4/5 roles (bins and windows do not depend on helper
indices; r6 C-hosting). No gain arose, so nothing is needed.

## Scope
Single-hyperplane variants of the three groups; relaxation screens of the group regions; multi-deletion of reader groups
on 6 representative words (not all 45, since all 45 share one reader signature); relocations of the G3 outlier only;
first-order projected kernels for the outliers' enlarged classes (2 representatives each, ≤12 inserts, quarter steps).
Not run: reader-group multi-deletion on the G1/G2 outliers, relocations on the G1/G2 outliers, two-level interface
changes, edits outside the group regions (shared with the base word and covered by r3–r6).

## Evidence
`out/EVIDENCE.json` (summary), `out/GROUPS.json`, `out/VARIANTS.json`, `out/RELAX-READERS.json`, `out/RELAX-S.json`,
`out/RELAX-CLASSES-G3.json`, `out/RELAX-CLASSES-G12.json`, `out/RELOC16.json`; `runs/RUN-*.json`, `runs/PRICED-*.json`,
`runs/*.cap.log`, `runs/SPEC-*.json`; `words/` (the 45 variants); scripts in `scripts/` (common, pool, inspect_groups,
build_variants, relax_readers, relax_S, relax_classes, reloc16, lane.sh, summarize). At most 4 processes, per-task
deadlines, RSS cap 6 GiB (capped.py and a pool watchdog); peak about 0.7 GiB per CP-SAT process.

Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).
