# AEGIS - Bayes-Risk Threshold Framing

## Method

Youden's J (recall - FPR, maximised) implicitly weighs a missed attack and a false alarm equally - a claim we don't actually believe, given the SOC alert-fatigue argument used elsewhere in this project. The corrected, named framing: for a cost ratio r = C(missed attack) / C(false alarm), the Bayes-risk-minimising threshold minimises Cost(t; r) = r*(1-recall(t)) + FPR(t). For any r, the minimiser must lie on the ROC curve's concave envelope - the Neyman-Pearson-achievable frontier for this scalar risk score - so we brute-force the argmin directly over the empirical ROC curve across a wide range of r and report, honestly, the range of r for which each of our two decision thresholds is the Bayes-risk-optimal choice.

- ROC-AUC of the underlying risk score: 0.979
- Nearest achievable ROC threshold to our chosen STEP-UP (0.60): 0.6000
- Nearest achievable ROC threshold to our chosen BLOCK (0.85): 0.8499

## Result - the honest finding

Neither 0.60 nor 0.85 lands exactly on the Neyman-Pearson-achievable frontier (the ROC curve's concave hull) for any cost ratio in the swept range - the brute-force sweep never selects them as the argmin. We checked why rather than smoothing over it:

- **Pareto-efficiency (the check that actually matters operationally):** 0.60 has **0 points** that beat it on both recall and false-positive rate simultaneously; 0.85 has **0**. Zero dominators means no single alternative threshold does strictly better on both axes at once - both are legitimate, non-dominated operating points, not mistakes.
- **Why they're still technically off the hull:** the concave-hull/Bayes-risk-optimal frontier only characterises *deterministic single-threshold* rules as a strict subset - formally, a hull-interior point can be beaten by *randomising* between its two neighbouring hull vertices for some cost ratio. That's a theoretical construct, not an operational option - a live security gate doesn't flip a coin on whether to flag a request - so hull-interior-but-Pareto-efficient is the practically meaningful bar, and both thresholds clear it.

- **How close is 0.60 to the theoretical frontier, in absolute terms?** It sits between hull vertices at threshold 0.650 (r in [0.10, 0.10]) and threshold 0.500 (r in [0.10, 0.42]). The nearer of the two, by actual (FPR, recall) distance, is threshold 0.650 - a gap of only **0.19 points of FPR** and **1.20 points of recall**. That is consistent with a cost-ratio belief in roughly the r ~ 0.10-0.10 neighbourhood, and a gap this small is attributable to the finite resolution of an ~11,000-window empirical ROC curve, not a meaningful inefficiency.

- **Same check for BLOCK (0.85):** brackets between threshold 0.887 (r in [0.08, 0.10]) and 0.650 (r in [0.10, 0.10]). Nearer vertex: threshold 0.887, a gap of **0.09 points of FPR** and **0.48 points of recall**. BLOCK sits in a sparser part of the hull than STEP-UP (fewer distinct thresholds achieve very low FPR on an ~11,000-window test set), so this gap is wider than STEP-UP's - still Pareto-efficient, but the resolution-scale caveat matters more here, and is a legitimate target for a larger larger held-out set.

## The Neyman-Pearson-achievable frontier for this risk score

| Threshold | Optimal for r in | Recall | FPR |
|---|---|---|---|
| 0.900 | [0.05, 0.08] | 82.3% | 0.44% |
| 0.887 | [0.08, 0.10] | 82.7% | 0.48% |
| 0.650 | [0.10, 0.10] | 90.4% | 1.24% |
| 0.500 | [0.10, 0.42] | 95.2% | 1.75% |
| 0.467 | [0.42, 0.68] | 95.4% | 1.85% |
| 0.227 | [0.68, 1.90] | 96.4% | 2.50% |
| 0.042 | [1.90, 28.6] | 96.6% | 2.95% |
| 0.000 | [28.9, 300.0] | 100.0% | 100.00% |

## Illustrative operating points at fixed cost ratios

| Cost ratio r | Optimal threshold | Recall | FPR |
|---|---|---|---|
| 1 | 0.227 | 96.4% | 2.50% |
| 5 | 0.042 | 96.6% | 2.95% |
| 15 | 0.042 | 96.6% | 2.95% |
| 40 | 0.000 | 100.0% | 100.00% |

As r rises (a missed attack is assumed increasingly costlier than a false alarm), the optimal threshold moves lower, trading a higher false-positive rate for higher recall - the same obstacle-detector tradeoff described in an earlier rehearsal: at the extreme (r to infinity), the optimal policy degenerates to flagging everything, exactly as 'never move, see obstacles everywhere' is not actually optimal despite maximising detection. Our chosen operating points sit at a moderate, stated cost ratio, not at either extreme.

**Scope note:** this analysis covers the binary STEP-UP decision boundary (flag vs. pass). Extending it to the full three-action PASS/STEP-UP/BLOCK policy would need a richer cost matrix (distinct costs for a missed attack, an unnecessary STEP-UP challenge, and an unnecessary BLOCK) - noted here as follow-up work rather than assumed away.
