# AEGIS - Baseline Detection Results

- Windows evaluated: **15,418** (legit 14,986 · attack 432)
- Window size: 60s - decision thresholds: STEP-UP >= 0.6, BLOCK >= 0.85

## Headline metrics (rules + ML fused)

| Metric | Value |
|---|---|
| ROC-AUC | **0.979** |
| Precision | 0.701 |
| Recall (detection) | **0.905** |
| F1 | 0.790 |
| False-positive rate (legit flagged) | **0.0111** |
| ROC-AUC - ML only (no rules) | 0.715 |

_All seven threats T1-T7 have a working detector. Detection rate is deliberately not uniform: thresholds are tuned for a realistic ~1.5% false-positive budget rather than maximum sensitivity, so threats with a loud, unambiguous signal (volumetric spikes, scope-policy violations) sit near 100%, while statistically subtle threats (slow reconnaissance, low-and-slow exfiltration) are genuinely harder to catch - consistent with published NIDS/UEBA benchmarks. T6 uses a session-level state machine (orphan update/release detection). T3/T5 use rolling 5-minute cross-window accumulators (breadth, error count, peak payload) since both attacks are too sparse per-window to be caught by a single 60s snapshot._

## Detection rate per threat

| Threat | Windows | Detected |
|---|---|---|
| T1_impersonation | 53 | 100% |
| T1_impersonation_v2 | 4 | 100% |
| T2_compromise | 52 | 73% |
| T3_recon | 56 | 93% |
| T4_volumetric | 60 | 100% |
| T4_volumetric_slow_ramp | 30 | 100% |
| T5_exfil | 42 | 79% |
| T6_sequence | 56 | 75% |
| T7_scope_creep | 41 | 100% |
| T7_scope_creep_v2 | 38 | 100% |

## Gate decisions on the test set

| Decision | Windows |
|---|---|
| PASS | 14,860 |
| STEP-UP | 161 |
| BLOCK | 397 |
