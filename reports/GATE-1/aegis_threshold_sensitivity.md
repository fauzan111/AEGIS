# AEGIS - ROC Operating-Point and Threshold-Sensitivity Analysis

Overall ROC-AUC: **0.965**

## Youden's J optimum vs the chosen operating point

| Point | Threshold | Recall | False-positive rate |
|---|---|---|---|
| Youden's J optimum | 0.013 | 94.1% | 3.21% |
| Chosen STEP-UP | 0.6 | 90.7% | 1.43% |
| Chosen BLOCK | 0.85 | 75.5% | 0.57% |

Youden's J (recall minus false-positive rate, maximised) is the threshold that best separates attack from legitimate traffic with no assumption about which error costs more. AEGIS's chosen STEP-UP threshold sits deliberately more conservative than this statistically optimal point, trading a small amount of recall for a materially lower false-positive rate, consistent with the realistic false-positive budget described in docs/GATE-2.md 2.4.

## Full threshold sweep

| Threshold | Recall | False-positive rate | Precision |
|---|---|---|---|
| 0.01 (Youden's J optimum) | 94.1% | 3.21% | 48.6% |
| 0.05 | 93.8% | 3.08% | 49.6% |
| 0.10 | 93.5% | 2.94% | 50.6% |
| 0.15 | 93.2% | 2.79% | 51.9% |
| 0.20 | 93.0% | 2.68% | 52.8% |
| 0.25 | 93.0% | 2.54% | 54.1% |
| 0.30 | 92.7% | 2.38% | 55.7% |
| 0.35 | 92.4% | 2.13% | 58.4% |
| 0.40 | 92.4% | 1.98% | 60.1% |
| 0.45 | 91.8% | 1.80% | 62.2% |
| 0.50 | 91.8% | 1.65% | 64.2% |
| 0.55 | 90.7% | 1.56% | 65.2% |
| 0.60 (chosen STEP-UP) | 90.7% | 1.43% | 67.2% |
| 0.65 | 90.1% | 1.21% | 70.6% |
| 0.70 | 78.3% | 1.06% | 70.4% |
| 0.75 | 78.0% | 0.99% | 71.8% |
| 0.80 | 76.3% | 0.77% | 76.1% |
| 0.85 (chosen BLOCK) | 75.5% | 0.57% | 81.0% |
| 0.90 | 73.8% | 0.37% | 86.5% |
| 0.95 | 56.6% | 0.20% | 90.1% |
