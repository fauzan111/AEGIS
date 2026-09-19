# AEGIS - Bootstrap Confidence Intervals & Significance Test

## Method

Stratified bootstrap (3,000 replicates): legit and attack windows resampled separately, with replacement, each at their original count, so every replicate keeps the real class balance. 95% CIs are the 2.5th/97.5th percentiles of the replicate distribution. The significance test against the SPC baseline is a PAIRED bootstrap - the same resampled row indices are scored by both AEGIS and SPC each replicate, since both were evaluated on the identical held-out test set - and reports the AUC-difference distribution directly, which avoids DeLong's asymptotic-normality assumption.

## AEGIS headline metrics, 95% CI

| Metric | Point estimate | 95% CI |
|---|---|---|
| ROC-AUC | 0.965 | [0.951, 0.977] |
| Recall @ STEP-UP (0.60) | 90.7% | [87.6%, 93.5%] |
| False-positive rate @ STEP-UP (0.60) | 1.43% | [1.21%, 1.64%] |

## Per-threat detection rate, 95% CI

| Threat | Point estimate | 95% CI | Windows |
|---|---|---|---|
| T1_impersonation | 96% | [90%, 100%] | 54 |
| T2_compromise | 91% | [81%, 98%] | 43 |
| T3_recon | 80% | [69%, 90%] | 60 |
| T4_volumetric | 100% | [100%, 100%] | 60 |
| T5_exfil | 76% | [62%, 88%] | 46 |
| T6_sequence | 93% | [85%, 98%] | 57 |
| T7_scope_creep | 100% | [100%, 100%] | 35 |

Note the width of these intervals tracks sample size directly: threats with fewer windows (e.g. T7 scope creep, T5 exfil) have visibly wider CIs than T3/T4/T6 - a reminder that the point estimates alone, without this spread, overstate how precisely we know the true per-threat detection rate.

## Significance test: AEGIS vs. SPC baseline (paired bootstrap on AUC)

- Observed AUC difference (AEGIS - SPC): **0.0216**
- 95% CI on the difference: **[0.0042, 0.0401]**
- Empirical two-sided p-value: **0.0147**

The CI excludes zero, so the improvement over the SPC baseline is statistically significant at the 95% level, not attributable to sampling noise.
