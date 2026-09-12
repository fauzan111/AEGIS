# AEGIS - Baseline Detection Results

- Windows evaluated: **11,365** (legit 11,010 · attack 355)
- Window size: 60s · decision thresholds: STEP-UP ≥ 0.6, BLOCK ≥ 0.85

## Headline metrics (rules + ML fused)

| Metric | Value |
|---|---|
| ROC-AUC | **0.965** |
| Precision | 0.672 |
| Recall (detection) | **0.907** |
| F1 | 0.772 |
| False-positive rate (legit flagged) | **0.0143** |
| ROC-AUC - ML only (no rules) | 0.721 |

_All seven threats T1–T7 have a working detector. Detection rate is deliberately not uniform: thresholds are tuned for a realistic ~1.5% false-positive budget rather than maximum sensitivity, so threats with a loud, unambiguous signal (volumetric spikes, scope-policy violations) sit near 100%, while statistically subtle threats (slow reconnaissance, low-and-slow exfiltration) are genuinely harder to catch - consistent with published NIDS/UEBA benchmarks. T6 uses a session-level state machine (orphan update/release detection). T3/T5 use rolling 5-minute cross-window accumulators (breadth, error count, peak payload) since both attacks are too sparse per-window to be caught by a single 60s snapshot._

## Detection rate per threat

| Threat | Windows | Detected |
|---|---|---|
| T1_impersonation | 54 | 96% |
| T2_compromise | 43 | 91% |
| T3_recon | 60 | 80% |
| T4_volumetric | 60 | 100% |
| T5_exfil | 46 | 76% |
| T6_sequence | 57 | 93% |
| T7_scope_creep | 35 | 100% |

## Gate decisions on the test set

| Decision | Windows |
|---|---|
| PASS | 10,886 |
| STEP-UP | 148 |
| BLOCK | 331 |
