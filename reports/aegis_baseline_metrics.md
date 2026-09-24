# AEGIS - Baseline Detection Results

- Windows evaluated: **15,363** (legit 14,946 · attack 417)
- Window size: 60s - decision thresholds: STEP-UP >= 0.6, BLOCK >= 0.85

## Headline metrics (rules + ML fused)

| Metric | Value |
|---|---|
| ROC-AUC | **0.979** |
| Precision | 0.640 |
| Recall (detection) | **0.916** |
| F1 | 0.753 |
| False-positive rate (legit flagged) | **0.0144** |
| ROC-AUC - ML only (no rules) | 0.717 |

_All seven threats T1-T7 have a working detector. Detection rate is deliberately not uniform: thresholds are tuned for a realistic ~1.5% false-positive budget rather than maximum sensitivity, so threats with a loud, unambiguous signal (volumetric spikes, scope-policy violations) sit near 100%, while statistically subtle threats (slow reconnaissance, low-and-slow exfiltration) are genuinely harder to catch - consistent with published NIDS/UEBA benchmarks. T6 uses a session-level state machine (orphan update/release detection). T3/T5 use rolling 5-minute cross-window accumulators (breadth, error count, peak payload) since both attacks are too sparse per-window to be caught by a single 60s snapshot._

## Detection rate per threat

| Threat | Windows | Detected |
|---|---|---|
| T1_impersonation | 54 | 100% |
| T1_impersonation_v2 | 4 | 100% |
| T2_compromise | 44 | 84% |
| T3_recon | 58 | 95% |
| T4_volumetric | 60 | 100% |
| T4_volumetric_slow_ramp | 30 | 100% |
| T5_exfil | 39 | 72% |
| T6_sequence | 58 | 76% |
| T7_scope_creep | 38 | 100% |
| T7_scope_creep_v2 | 32 | 100% |

## Gate decisions on the test set

| Decision | Windows |
|---|---|
| PASS | 14,766 |
| STEP-UP | 166 |
| BLOCK | 431 |
