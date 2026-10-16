# Saved ML4 interpretation

**The fixed learned models did not improve the exact screening baseline.** Across all36observed configurations per seed, none beats the cheap exact screen or training stratum-mean baseline on population-weighted Brier loss. None of the60learning-curve configurations beats the cheap screen on Brier. This is a protocol-specific descriptive result, not a general impossibility statement about ML.

The corpus contains3,250,295distinct sampled/censused pairs and6,500,590repeated computations across two execution seeds. The complete necessary-gain strata contain34,727pairs/11,067legal positives for PR2853,69,847/14,101 for PR2917,and0/0 for PR2979. The three sources share ancestry. Two-seed agreement reproduces the same corpus and fitted results; it is not independent data replication.

The following are whole-fill held-out metrics **within S**, where the rare-event ranking question is informative. Each observed evaluation panel has131,072rows before restricting toS. PR2853 has4,228S rows/1,415positives; PR2917 has8,089/1,602.

| Held-out source | Model | AUROC in S | AP in S | Brier in S |
|---|---|---:|---:|---:|
| 2853 | core_linear | 0.864714 | 0.769133 | 0.334672 |
| 2853 | core_quadratic | 0.947618 | 0.856313 | 0.334673 |
| 2853 | mechanism_linear | 0.680483 | 0.453745 | 0.334673 |
| 2853 | mechanism_quadratic | 0.506072 | 0.339104 | 0.334673 |
| 2853 | cheap_exact_screen | 0.988091 | 0.954791 | 0.015847 |
| 2853 | training_stratum_mean | 0.500000 | 0.334674 | 0.240214 |
| 2917 | core_linear | 0.882564 | 0.601390 | 0.198047 |
| 2917 | core_quadratic | 0.897702 | 0.608193 | 0.198040 |
| 2917 | mechanism_linear | 0.848768 | 0.545450 | 0.198046 |
| 2917 | mechanism_quadratic | 0.720085 | 0.334783 | 0.197903 |
| 2917 | cheap_exact_screen | 0.990057 | 0.925477 | 0.015948 |
| 2917 | training_stratum_mean | 0.500000 | 0.198047 | 0.172595 |

The core features carry ranking signal: linear/quadratic AP is0.769/0.856 on2853 and0.601/0.608 on2917, above constant withinS prevalence0.335/0.198. The cheap capacity/spread/window screen is substantially stronger: AP0.955/0.925 and Brier0.01585/0.01595. Optional width/residual/capacity features improve some global ranking metrics (whole-fill AUROC up to0.9966/0.9994), but their whole-population AP remains only0.0282/0.0112 at best, versus cheap-screen AP0.9548/0.9255. High AUROC against billions of obvious noncandidates is not sufficient evidence of useful screening.

Probability calibration remains poor under this fixed model/penalty/prior-correction protocol: learned withinS Brier is close to the zero-prediction loss (approximately the withinS positive prevalence), and all36observed variants lose to stratum-mean Brier. The pair-purged PR2917 quadratic core model is especially unstable in population Brier:3.82436e-6 against mean3.88334e-7. There were zero optimizer nonconvergence reports, so numerical convergence does not resolve this modeling limitation.

The joint call/family endpoint-disjoint and exact-pair-purged sensitivities preserve useful withinS core ranking, but neither reverses cheap-screen/Brier dominance. PR2979 hasS=0 and no positive label: AUROC/AP are unavailable, conditionalS evaluation is empty, and cheap/stratum Brier is exactly0. It must not be counted as a successful discrimination fold.

Learning curves use fixed training caps512,2048,8192,32768,131072. Their smallest positive training counts are4 or7 in the two positive-source holdouts. Larger samples improve some ranking curves without monotone improvement and without overtaking the cheap screen; no best cap or model was selected after seeing outcomes.

The matched8192-per-fill benchmark has two movable blocks (S of2853 and2917) and four fixed/empty one-class blocks. Both seeds completed2,000indexed shuffles. The unshuffled primary Brier-improvement statistics are negative:−3.30715e-13(linear) and−4.80240e-11(quadratic). Secondary improvements over the stratum mean are−4.94359e-8 and−4.94836e-8. These are descriptive conditional-label-shuffle comparisons, with no p-values, q-values or independent-lineage pattern claim.

The complete registered run used1759.514187750CPU seconds and111.450437wall seconds:4,702pool tasks, comprising504generation and4,198model/control tasks. The4,000permutation tasks averaged47.54CPU cores; configured worker count was61. Overall utilization averaged15.79core equivalents because parent preparation and small control phases are included.

The practical outcome is to retain the exact cheap guards and full oracle for this historical exchange task. The models provide limited descriptive ranking evidence, not a stronger replacement or a newly priced move. Only linear and per-feature-square logistic models were tested; interactions, trees, other penalties and independent lineages were not tested. No historical classification result establishes simultaneous exchange compatibility, supplier admission or any κ gain.

Source receipt references and full numerical summaries are preserved in `data/continuation-12/ml4-v1/SAVED-INTERPRETATION.json` (SHA256 7d9a4ab071464d25843afaf37cd86a6023512b5a3c1df282bf3053b2287c0a6c). No scientific functions were executed during this review.
