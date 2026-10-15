# AEGIS vs. a Named State-of-the-Art Baseline

## What we compared against

**Statistical Process Control (SPC) / control-chart anomaly detection** - the classic, widely-deployed baseline this kind of behavioural monitoring descends from, and the direct statistical ancestor of most commercial rate-based UEBA/NIDS alerting. Per agent, we learn a mean and standard deviation for four features (request count, error rate, max response size, distinct NFs touched) from legit-only training traffic, then flag any window where at least one feature breaches a z-score control limit. We implemented and ran it ourselves on the IDENTICAL train/test split AEGIS itself is evaluated on (same seed, same 22,417-window training set, same 15,363-window test set) - a real head-to-head, not two numbers from two different papers.

## Result

| Detector | ROC-AUC | Recall @ FPR 1.44% |
|---|---|---|
| SPC z-score baseline | 0.929 | 64.0% |
| AEGIS (rules + ML fusion) | **0.979** | **91.6%** |

## Per-threat detection at matched false-positive rate

| Threat | SPC baseline | AEGIS |
|---|---|---|
| T1 | 100% | 100% |
| T2 | 34% | 84% |
| T3 | 45% | 95% |
| T4 | 100% | 100% |
| T5 | 72% | 72% |
| T6 | 31% | 76% |
| T7 | 46% | 100% |

SPC catches loud, single-feature deviations (volumetric spikes) reasonably well, since that is exactly what it is built for, but it has no notion of scope, sequence, or cross-window behaviour - so it is structurally blind to threats like scope creep or orphaned session sequences that never show up as a single feature outlier. That gap is the concrete, measured case for the fingerprinting and rules-plus-ML fusion approach over the classic baseline, not just an architectural preference.
