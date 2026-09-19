# AEGIS vs. a Naive Bayes Likelihood-Ratio Reference Classifier

## Method

The Neyman-Pearson lemma defines the only rigorously 'optimal' detector as the one that maximises detection probability subject to a cap on false-alarm probability, using the likelihood ratio of the TRUE class-conditional distributions. We don't know those distributions - not in production (no labelled attacks to estimate them from), and not exactly here either. What we CAN do, because our synthetic evaluation set is fully labelled, is approximate them: a 1-D Gaussian KDE per feature, per class, fit on a held-out split, combined into a log-likelihood-ratio score under a Naive Bayes / feature-independence assumption. This is deliberately NOT reported as a 'bound' - the independence assumption discards feature correlations and any structured, higher-order signal, so it is not guaranteed to be an upper bound on a detector that can exploit that structure.

- Features used: n, distinct_nf, err_rate, n_orphan, max_resp, distinct_ep_roll, err_count_roll, resp_roll_max
- Fit split: 5,682 windows · Eval split: 5,683 windows
- **Numerical disclosure:** 26 of 45,464 per-feature density evaluations underflowed to the 1e-300 floor (mostly n_orphan on attack-side windows far from either class's KDE mass). When that happens, that single feature's log-ratio contribution (~690 nats) dominates the summed score for that row, rather than the 8 features contributing comparably. This mainly makes the reference classifier's score MORE extreme on exactly the windows it already gets right, so it does not appear to inflate AEGIS's margin over it - but it means the reference's AUC should be read as directionally informative, not a precisely calibrated figure.

## Result

| Detector | ROC-AUC | Recall @ FPR 1.43% |
|---|---|---|
| Naive Bayes likelihood-ratio reference | 0.941 | 79.2% |
| AEGIS (rules + ML fusion) | **0.972** | **89.9%** |

AEGIS exceeds the Naive Bayes reference by **10.7 percentage points of recall** at matched false-positive rate.

This is not a contradiction of Neyman-Pearson - the reference classifier is not a true bound, precisely because its independence assumption discards information AEGIS's rules layer uses directly: session-state sequencing (an update/release referencing a session that was never opened) and scope-set membership (a Network Function outside an agent's onboarded baseline) are structured, non-marginal signals no per-feature likelihood ratio can represent. The result quantifies, concretely, what domain-informed structure buys over a textbook statistical baseline built from the same raw features - the honest version of the state-of-the-art comparison, rather than an unearned 'we beat the optimal' claim.
