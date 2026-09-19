# AEGIS - Concept-Drift / Stationarity Check

## Method

Two-sample Kolmogorov-Smirnov test per agent per feature, comparing LEGIT-only traffic on the first day of data (2026-08-03) against the last (2026-08-07) - the most temporally distant pair available, giving the most power to detect real drift within the week. 20 tests total (5 agents x 4 features), with a Benjamini-Hochberg FDR correction at alpha=0.05 so the result isn't just multiple-comparison noise.

## Result

**6 of 20 agent/feature combinations show statistically significant drift** after FDR correction.

| Agent | Feature | KS statistic | p-value | Significant (FDR) |
|---|---|---|---|---|
| orch-session-mgr | n | 0.305 | 0.0000 | YES |
| nrf-heartbeat-svc | n | 0.139 | 0.0000 | YES |
| closed-loop-assurance | n | 0.122 | 0.0000 | YES |
| provisioning-agent | n | 0.101 | 0.0001 | YES |
| orch-session-mgr | max_resp | 0.079 | 0.0002 | YES |
| provisioning-agent | max_resp | 0.079 | 0.0050 | YES |
| closed-loop-assurance | max_resp | 0.057 | 0.0182 | no |
| oss-inventory-job | n | 0.123 | 0.0318 | no |
| nrf-heartbeat-svc | max_resp | 0.032 | 0.4527 | no |
| oss-inventory-job | max_resp | 0.068 | 0.5399 | no |
| closed-loop-assurance | err_rate | 0.029 | 0.5943 | no |
| orch-session-mgr | err_rate | 0.025 | 0.7593 | no |
| provisioning-agent | distinct_nf | 0.028 | 0.8274 | no |
| oss-inventory-job | err_rate | 0.037 | 0.9911 | no |
| provisioning-agent | err_rate | 0.019 | 0.9943 | no |
| orch-session-mgr | distinct_nf | 0.013 | 0.9996 | no |
| oss-inventory-job | distinct_nf | 0.016 | 1.0000 | no |
| nrf-heartbeat-svc | err_rate | 0.003 | 1.0000 | no |
| nrf-heartbeat-svc | distinct_nf | 0.000 | 1.0000 | no |
| closed-loop-assurance | distinct_nf | 0.001 | 1.0000 | no |

6 combination(s) show real, statistically significant drift even within this short synthetic week - the fingerprint is not perfectly stationary even in our own controlled data, let alone in production traffic subject to real config and usage changes.

## Re-baselining recommendation
Given the fingerprint baseline is learned once from a training window and assumed valid thereafter, and given real 5G network agents will drift over weeks/months even where our 5-day synthetic traffic does not, we recommend a **periodic re-baselining cadence (e.g. weekly, re-fit on a trailing window) rather than a one-time baseline** for production deployment - stated here as an explicit Gate 3 design requirement rather than an implicit assumption.
