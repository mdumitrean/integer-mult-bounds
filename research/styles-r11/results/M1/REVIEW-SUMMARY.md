The registered L-1 grammar search returned **NULL under both seeds**. It fitted the same deterministic capped RePair algorithm separately to every one of the 84 three-word subsets of the nine pinned files. The original criterion required at most 200 shared rules, exact regeneration of all three declared A/B skeletons, and at least 90% pairwise overlap of transitively used rules. The [preregistration](PREREGISTRATION.json) fixed the triples, algorithm, cap and decision before execution.

All 168 tasks completed successfully. Every fit produced 201 rules and reached the cap, so every triple failed the rule-count condition. All 252 skeleton expansions per seed were exact. Saved decision evidence, including overlap values and axiom/rule hashes, matched across seeds. This result concerns the fixed capped RePair protocol; existence of other grammars or a parametric construction was not decided.

| Seed | Completed triples | Rule count for every fit | Exact replays | Recorded CPU seconds | Recorded wall seconds |
|---|---:|---:|---:|---:|---:|
| [11031](../L-1/v1/seed-11031/RESULT.json) | 84 | 201 | 252 | 167.493003 | 4.183466 |
| [29063](../L-1/v1/seed-29063/RESULT.json) | 84 | 201 | 252 | 166.904018 | 4.530605 |

Timings above are rounded to six decimals; the linked receipts retain the recorded values. Combined recorded CPU was 334.397021 seconds, including preparation and process overhead. Peak recorded RSS was 546,148,352 bytes. Worker CPU alone was 146.579147 and 147.414504 seconds.

Pairwise rule-use overlap ranged from 0.13930348258706468 to 1.0. Axiom lengths ranged from 5,054 to 5,451 symbols, with 5,013 to 5,435 residual literals. These axiom measurements were diagnostics and did not add a pass threshold. The exact gate used zero permutations and received no inferential p-value or q-value.

The confirmed L-2 literal-cleanup NULL immediately preceded L-1 in Lane A. Their two consecutive confirmed NULLs trigger PLAN section 6; [STOP.json](STOP.json) records the four supporting seed receipts. The 540-cell screen, L-3, L-4, L-5 and conditional N4 were not run. L-3/L-4/L-5 have explicit EXPLORATORY/not-run receipts with zero permutations and null p/q fields. No compression, periodicity, climb-prediction or alias-motif NULL is inferred from those skipped tests.

The independent review checked complete distinct-triple coverage, the original numerical pass predicate, exact-replay flags, both-seed evidence equality, executed-source hashes, PINS identities, registry confirmation and stop receipts. It read existing source and result artifacts only; it launched no experiment.

Source attribution retained from [PINS.json](../../data/words/PINS.json):

| Source PR | Word files | Retained author attribution |
|---|---:|---|
| #1094 | 1 | Jeremy Kothe (jeremykothe2) |
| #1672 | 2 | Jeremy Kothe (LeverRank); on PR #1625 words; PR #1319/#1297 lineage (Rohan Arun) |
| #2745 | 2 | Jeremy Kothe (jeremykothe2) |
| #2766 | 1 | DavidAriasC |
| #2751 | 1 | Tekalign (tekuuu) |
| #2802 | 2 | Marius-Paul Dumitrean |
