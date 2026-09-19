# AEGIS - Cross-Validated Threshold Stability

## Method & scope

The reported STEP-UP threshold (0.60) was chosen against the same held-out test set used to report final numbers - worth checking honestly rather than ignoring. This is a 5-fold stratified cross-validation OF THE TEST SET ITSELF: in each fold, we pick the threshold hitting our target 1.43% FPR budget using the other 4 folds' scores, then evaluate that threshold on the held-out fold. This checks whether the threshold-selection process is stable and generalises across different slices of the data, not whether the underlying Isolation Forest/rules model itself generalises (that would need refitting the whole detector per fold - out of scope here, flagged for Gate 3).

## Result

| Fold | Threshold picked | Held-out recall | Held-out FPR | Attack windows | Legit windows |
|---|---|---|---|---|---|
| 1 | 0.565 | 85.9% | 2.00% | 71 | 2202 |
| 2 | 0.634 | 95.8% | 0.73% | 71 | 2202 |
| 3 | 0.565 | 88.7% | 1.91% | 71 | 2202 |
| 4 | 0.615 | 95.8% | 1.41% | 71 | 2202 |
| 5 | 0.621 | 85.9% | 1.00% | 71 | 2202 |

- Threshold across folds: **0.600 +/- 0.033** (reported value: 0.60)
- Held-out recall across folds: **90.4% +/- 5.0%** (reported value: 90.7%)
- Held-out FPR across folds: **1.41% +/- 0.55%** (reported value: 1.43%)

The fold-to-fold threshold and out-of-fold recall/FPR stay close to the originally reported values, with modest spread consistent with the ~350-window attack sample size. This does not prove the underlying detector would generalise to genuinely new traffic distributions (that needs real or temporally-held-out data, see the temporal-split check) - it shows the threshold itself was not cherry-picked to this particular test set.
