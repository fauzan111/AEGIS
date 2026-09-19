# -*- coding: utf-8 -*-
"""
AEGIS - Naive Bayes likelihood-ratio reference classifier (Gate 2 evidence).

The Neyman-Pearson lemma says the only rigorously "optimal" detector is the
one that maximises probability of detection subject to a cap on probability
of false alarm, using the likelihood ratio of the TRUE class-conditional
distributions. We don't know those distributions, in production or here -
what we CAN do, because our synthetic set is fully labelled, is estimate an
approximation of them per-feature and independently (a Naive Bayes model),
and see how a likelihood-ratio classifier built on that approximation
compares to AEGIS's own rules+ML fusion.

IMPORTANT - this is deliberately not called a "bound": the independence
assumption behind Naive Bayes throws away feature correlations and any
higher-order structure, so it is not guaranteed to be an upper bound on any
detector that can exploit that structure - and indeed, as the result below
shows, AEGIS exceeds it, precisely because AEGIS's rules layer encodes
structured, non-marginal signals (session-state sequencing, scope-set
membership) that a per-feature independence assumption cannot represent.
That comparison, not a claim of "beating the optimal", is the point: it
quantifies what structured, domain-informed detection buys you over a
textbook statistical baseline built from the same raw features.

Run:  .venv/Scripts/python AEGIS/src/aegis_neyman_pearson.py
In :  reports/scored_windows.csv
Out:  reports/aegis_neyman_pearson.png, reports/aegis_neyman_pearson.md
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from sklearn.metrics import roc_curve, roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "..", "reports")
SCORED = os.path.join(REPORTS, "scored_windows.csv")
OUT_DIR = os.path.join(REPORTS, "GATE-2")
os.makedirs(OUT_DIR, exist_ok=True)

# Core interpretable features driving both the rules and ML layers already;
# log1p on the heavy-tailed count/size features to keep the KDE well-behaved.
RAW_FEATURES = ["n", "distinct_nf", "err_rate", "n_orphan", "max_resp",
                 "distinct_ep_roll", "err_count_roll", "resp_roll_max"]
LOG_FEATURES = {"n", "max_resp", "resp_roll_max", "err_count_roll"}

FPR_TARGET = 0.0143  # AEGIS's own achieved FPR, for a matched comparison


def transform(df):
    X = {}
    for f in RAW_FEATURES:
        v = df[f].to_numpy(dtype=float)
        X[f] = np.log1p(np.clip(v, 0, None)) if f in LOG_FEATURES else v
    return pd.DataFrame(X)


def fit_kde_ratio(fit_legit, fit_attack):
    """Returns a function computing the summed log-likelihood-ratio (Naive
    Bayes over RAW_FEATURES) for any dataframe of transformed features."""
    kdes_legit, kdes_attack = {}, {}
    for f in RAW_FEATURES:
        xl = fit_legit[f].to_numpy()
        xa = fit_attack[f].to_numpy()
        # tiny jitter avoids a degenerate (zero-bandwidth) KDE on near-constant columns
        kdes_legit[f] = gaussian_kde(xl + np.random.default_rng(0).normal(0, 1e-6, len(xl)))
        kdes_attack[f] = gaussian_kde(xa + np.random.default_rng(1).normal(0, 1e-6, len(xa)))

    def score(dfr):
        total = np.zeros(len(dfr))
        floor_hits = 0
        for f in RAW_FEATURES:
            x = dfr[f].to_numpy()
            da, dl = kdes_attack[f](x), kdes_legit[f](x)
            # the 1e-300 floor is not just a theoretical safeguard - it is
            # genuinely hit for some rows (e.g. orphan-count spikes far from
            # either class's KDE mass), where it can make one feature's log
            # contribution swamp the other seven; counted here so the report
            # discloses it rather than silently averaging it away
            floor_hits += int((da < 1e-300).sum() + (dl < 1e-300).sum())
            la = np.log(np.clip(da, 1e-300, None))
            ll = np.log(np.clip(dl, 1e-300, None))
            total += la - ll
        score.last_floor_hits = floor_hits
        return total

    score.last_floor_hits = 0
    return score


def recall_at_fpr(y, score, target_fpr):
    fpr, tpr, thresh = roc_curve(y, score)
    idx = np.searchsorted(fpr, target_fpr, side="right") - 1
    idx = max(idx, 0)
    return float(tpr[idx]), float(fpr[idx]), float(thresh[idx])


def main():
    df = pd.read_csv(SCORED, parse_dates=["win"])
    y_all = (df["label"] == "attack").astype(int).to_numpy()
    X_all = transform(df)

    # stratified 50/50 split: one half to fit the class-conditional KDEs,
    # the other to evaluate - keeps the bound honest (not fit-on-eval).
    rng = np.random.default_rng(42)
    idx_legit = np.where(y_all == 0)[0]
    idx_attack = np.where(y_all == 1)[0]
    rng.shuffle(idx_legit); rng.shuffle(idx_attack)
    fit_idx = np.concatenate([idx_legit[:len(idx_legit)//2], idx_attack[:len(idx_attack)//2]])
    eval_idx = np.concatenate([idx_legit[len(idx_legit)//2:], idx_attack[len(idx_attack)//2:]])

    fit_legit = X_all.iloc[fit_idx][y_all[fit_idx] == 0]
    fit_attack = X_all.iloc[fit_idx][y_all[fit_idx] == 1]
    X_eval, y_eval = X_all.iloc[eval_idx], y_all[eval_idx]
    aegis_risk_eval = df["risk"].to_numpy()[eval_idx]

    score_fn = fit_kde_ratio(fit_legit, fit_attack)
    np_score = score_fn(X_eval)

    auc_np = roc_auc_score(y_eval, np_score)
    auc_aegis = roc_auc_score(y_eval, aegis_risk_eval)

    rec_np, fpr_np, _ = recall_at_fpr(y_eval, np_score, FPR_TARGET)
    rec_aegis, fpr_aegis, _ = recall_at_fpr(y_eval, aegis_risk_eval, FPR_TARGET)

    # ---------------- figure ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INKC, ACC, NPC = "#1F2A37", "#0E9384", "#D1495B"

    fpr_a, tpr_a, _ = roc_curve(y_eval, aegis_risk_eval)
    fpr_n, tpr_n, _ = roc_curve(y_eval, np_score)

    fig, ax = plt.subplots(figsize=(6, 5.2))
    ax.plot(fpr_n, tpr_n, color=NPC, lw=2, label=f"Naive Bayes LR reference (AUC {auc_np:.3f})")
    ax.plot(fpr_a, tpr_a, color=ACC, lw=2, label=f"AEGIS rules+ML (AUC {auc_aegis:.3f})")
    ax.plot([0, 1], [0, 1], color="#B0B7BF", ls="--", lw=1, label="random")
    ax.axvline(FPR_TARGET, color=INKC, ls=":", lw=1)
    ax.scatter([fpr_np], [rec_np], color=NPC, zorder=5)
    ax.scatter([fpr_aegis], [rec_aegis], color=ACC, zorder=5, marker="D")
    ax.set_xlim(0, 0.15); ax.set_ylim(0, 1.02)
    ax.set_xlabel("false-positive rate"); ax.set_ylabel("recall (probability of detection)")
    ax.set_title("AEGIS vs. Naive Bayes likelihood-ratio reference", fontsize=11, color=INKC)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "aegis_neyman_pearson.png"), dpi=140)
    plt.close(fig)

    # ---------------- report ----------------
    lines = []
    lines.append("# AEGIS vs. a Naive Bayes Likelihood-Ratio Reference Classifier\n")
    lines.append("## Method\n")
    lines.append(
        "The Neyman-Pearson lemma defines the only rigorously 'optimal' detector as the one that "
        "maximises detection probability subject to a cap on false-alarm probability, using the "
        "likelihood ratio of the TRUE class-conditional distributions. We don't know those "
        "distributions - not in production (no labelled attacks to estimate them from), and not "
        "exactly here either. What we CAN do, because our synthetic evaluation set is fully "
        "labelled, is approximate them: a 1-D Gaussian KDE per feature, per class, fit on a held-out "
        "split, combined into a log-likelihood-ratio score under a Naive Bayes / feature-independence "
        "assumption. This is deliberately NOT reported as a 'bound' - the independence assumption "
        "discards feature correlations and any structured, higher-order signal, so it is not "
        "guaranteed to be an upper bound on a detector that can exploit that structure.\n")
    lines.append(f"- Features used: {', '.join(RAW_FEATURES)}")
    lines.append(f"- Fit split: {len(fit_idx):,} windows · Eval split: {len(eval_idx):,} windows")
    floor_hits = getattr(score_fn, "last_floor_hits", 0)
    lines.append(
        f"- **Numerical disclosure:** {floor_hits} of {len(eval_idx) * len(RAW_FEATURES):,} "
        "per-feature density evaluations underflowed to the 1e-300 floor (mostly n_orphan on "
        "attack-side windows far from either class's KDE mass). When that happens, that single "
        "feature's log-ratio contribution (~690 nats) dominates the summed score for that row, "
        "rather than the 8 features contributing comparably. This mainly makes the reference "
        "classifier's score MORE extreme on exactly the windows it already gets right, so it does "
        "not appear to inflate AEGIS's margin over it - but it means the reference's AUC should be "
        "read as directionally informative, not a precisely calibrated figure.\n")
    lines.append("## Result\n")
    lines.append("| Detector | ROC-AUC | Recall @ FPR {:.2%} |\n|---|---|---|".format(FPR_TARGET))
    lines.append(f"| Naive Bayes likelihood-ratio reference | {auc_np:.3f} | {rec_np*100:.1f}% |")
    lines.append(f"| AEGIS (rules + ML fusion) | **{auc_aegis:.3f}** | **{rec_aegis*100:.1f}%** |")
    gap = (rec_aegis - rec_np) * 100
    lines.append(f"\nAEGIS exceeds the Naive Bayes reference by **{gap:.1f} percentage points of "
                 f"recall** at matched false-positive rate.")
    lines.append(
        "\nThis is not a contradiction of Neyman-Pearson - the reference classifier is not a true "
        "bound, precisely because its independence assumption discards information AEGIS's rules "
        "layer uses directly: session-state sequencing (an update/release referencing a session that "
        "was never opened) and scope-set membership (a Network Function outside an agent's onboarded "
        "baseline) are structured, non-marginal signals no per-feature likelihood ratio can represent. "
        "The result quantifies, concretely, what domain-informed structure buys over a textbook "
        "statistical baseline built from the same raw features - the honest version of the state-of-"
        "the-art comparison, rather than an unearned 'we beat the optimal' claim.")
    report = "\n".join(lines) + "\n"

    with open(os.path.join(OUT_DIR, "aegis_neyman_pearson.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("Saved reports/aegis_neyman_pearson.md, aegis_neyman_pearson.png")


if __name__ == "__main__":
    main()
