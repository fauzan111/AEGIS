# AEGIS - Temporal Split Robustness Check

## Method & an honest data constraint

The main pipeline splits legit windows randomly across the week. Real deployment fits a baseline on past traffic and scores future traffic - this check reruns the identical rules+ML pipeline (same functions, unmodified) with a strictly chronological split instead.

Constraint discovered in the data, not assumed: each of the 7 attack types was injected on exactly one specific day. A temporal split must keep every attack-bearing day in the test period to evaluate all seven threats, which leaves only **2026-08-03** (5,579 legit windows, the traffic's first day) as training data - much less than the original random split's ~40% (about 4 days). This is reported as a limitation of the check itself, not smoothed over: a fairer temporal evaluation would need attack injections spread across every day, which is Gate 3 scope for the traffic generator.

## Result

| Metric | Original (random split) | Temporal split |
|---|---|---|
| ROC-AUC | 0.965 | 0.969 |
| Recall | 90.7% | 90.1% |
| Precision | - | 0.540 |
| False-positive rate | 1.43% | 1.24% |

## Per-threat detection, temporal split

| Threat | Windows | Detected |
|---|---|---|
| T1_impersonation | 54 | 96% |
| T2_compromise | 43 | 86% |
| T3_recon | 60 | 80% |
| T4_volumetric | 60 | 100% |
| T5_exfil | 46 | 76% |
| T6_sequence | 57 | 93% |
| T7_scope_creep | 35 | 100% |

Performance holds up closely despite a much smaller, single-day training period - evidence the fingerprinting approach doesn't depend on the random split's easier access to a full week of variation.
