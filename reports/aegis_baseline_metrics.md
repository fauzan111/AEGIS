# AEGIS - Baseline Detection Results

- Windows evaluated: **11,343** (legit 10,994 · attack 349)
- Window size: 60s · decision thresholds: STEP-UP ≥ 0.5, BLOCK ≥ 0.8

## Headline metrics (rules + ML fused)

| Metric | Value |
|---|---|
| ROC-AUC | **0.992** |
| Precision | 0.790 |
| Recall (detection) | **0.983** |
| F1 | 0.876 |
| False-positive rate (legit flagged) | **0.0083** |
| ROC-AUC - ML only (no rules) | 0.726 |

_All seven threats T1–T7 now have a working detector. T6 uses a session-level state machine (orphan update/release detection), which replaced the earlier window-count heuristic that false-fired on legit traffic._

## Detection rate per threat

| Threat | Windows | Detected |
|---|---|---|
| T1_impersonation | 48 | 100% |
| T2_compromise | 47 | 100% |
| T3_recon | 56 | 89% |
| T4_volumetric | 60 | 100% |
| T5_exfil | 42 | 100% |
| T6_sequence | 57 | 100% |
| T7_scope_creep | 39 | 100% |

## Gate decisions on the test set

| Decision | Windows |
|---|---|
| PASS | 10,909 |
| STEP-UP | 55 |
| BLOCK | 379 |
