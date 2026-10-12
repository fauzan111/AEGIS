# AEGIS - Cross-Validated Threshold Stability

## Method & scope

The reported STEP-UP threshold (0.60) was chosen against the same held-out test set used to report final numbers - worth checking honestly rather than ignoring. This is a 5-fold stratified cross-validation OF THE TEST SET ITSELF: in each fold, we pick the threshold hitting our target 1.44% FPR budget using the other 4 folds' scores, then evaluate that threshold on the held-out fold. This checks whether the threshold-selection process is stable and generalises across different slices of the data, not whether the underlying Isolation Forest/rules model itself generalises (that would need refitting the whole detector per fold - out of scope here, flagged as future work).

## Result

| Fold | Threshold picked | Held-out recall | Held-out FPR | Attack windows | Legit windows |
|---|---|---|---|---|---|
| 1 | 0.600 | 86.7% | 1.57% | 83 | 2990 |
| 2 | 0.610 | 94.0% | 1.17% | 84 | 2989 |
| 3 | 0.610 | 90.5% | 1.41% | 84 | 2989 |
| 4 | 0.600 | 91.6% | 1.47% | 83 | 2989 |
| 5 | 0.600 | 95.2% | 1.54% | 83 | 2989 |

- Threshold across folds: **0.604 +/- 0.005** (reported value: 0.60)
- Held-out recall across folds: **91.6% +/- 3.3%** (reported value: 91.6%)
- Held-out FPR across folds: **1.43% +/- 0.16%** (reported value: 1.44%)

The fold-to-fold threshold and out-of-fold recall/FPR stay close to the originally reported values, with modest spread consistent with the ~420-window attack sample size. This does not prove the underlying detector would generalise to genuinely new traffic distributions (that needs real or temporally-held-out data, see the temporal-split check) - it shows the threshold itself was not cherry-picked to this particular test set.
