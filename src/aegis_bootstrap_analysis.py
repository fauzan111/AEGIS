# -*- coding: utf-8 -*-
"""
AEGIS - bootstrap confidence intervals + paired significance test (Gate 2 evidence).

Two things every headline number in this project has been missing:

1. Uncertainty. "90.7% recall" on a few hundred attack windows (some threat
   types as few as 35-60 windows) is a point estimate, not a fact - a couple
   of windows going the other way moves the percentage noticeably. We
   stratified-bootstrap (resample legit and attack windows separately, with
   replacement, preserving class sizes) to get 95% confidence intervals on
   ROC-AUC, recall, false-positive rate, and each per-threat detection rate.

2. Significance. "AEGIS beats the SPC baseline" was reported as two point
   AUC values with no test of whether the gap is real or sampling noise. We
   run a PAIRED bootstrap (same resampled row indices scored by both
   detectors, since both were evaluated on the identical test set) on the
   AUC difference, and report its 95% CI and an empirical two-sided p-value -
   this is the non-parametric analogue of a DeLong test, and avoids DeLong's
   asymptotic-normality assumption, which is a more comfortable fit for our
   modest attack sample size.

Run:  .venv/Scripts/python AEGIS/src/aegis_bootstrap_analysis.py
In :  reports/scored_windows.csv (AEGIS) + rebuilt SPC scores (aegis_baseline_comparison)
Out:  reports/aegis_bootstrap_analysis.md, reports/aegis_bootstrap_analysis.png
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "..", "reports")
OUT_DIR = os.path.join(REPORTS, "GATE-2")
os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, HERE)
from aegis_baseline_comparison import build_spc_test_frame  # noqa: E402

N_BOOT = 3000
STEPUP = 0.60
RNG_SEED = 7


def stratified_boot_indices(y, rng):
    """Resample legit and attack rows separately, with replacement, each at
    their own original size - keeps every bootstrap replicate's class balance
    identical to the real data (plain unstratified resampling can occasionally
    under/over-represent the already-small attack class)."""
    idx_legit = np.where(y == 0)[0]
    idx_attack = np.where(y == 1)[0]
    b_legit = rng.choice(idx_legit, size=len(idx_legit), replace=True)
    b_attack = rng.choice(idx_attack, size=len(idx_attack), replace=True)
    return np.concatenate([b_legit, b_attack])


def main():
    scored = pd.read_csv(os.path.join(REPORTS, "scored_windows.csv"), parse_dates=["win"])
    spc_test, _, _ = build_spc_test_frame()

    # pair AEGIS and SPC scores row-for-row by (agent_id, win) - safer than
    # assuming positional alignment between two independently rebuilt frames
    paired = scored[["agent_id", "win", "label", "attack_type", "risk"]].merge(
        spc_test[["agent_id", "win", "spc_z"]], on=["agent_id", "win"], how="inner")
    assert len(paired) == len(scored), (
        f"merge dropped rows: {len(scored)} scored vs {len(paired)} paired - "
        "SPC test frame is not the same window set as scored_windows.csv")

    y = (paired["label"] == "attack").astype(int).to_numpy()
    risk = paired["risk"].to_numpy()
    spc = paired["spc_z"].to_numpy()
    threats = sorted(paired.loc[y == 1, "attack_type"].unique())

    rng = np.random.default_rng(RNG_SEED)

    # ---------------- 1. bootstrap CIs on AEGIS's own headline metrics ----------------
    aucs, recalls, fprs = [], [], []
    per_threat = {t: [] for t in threats}
    for _ in range(N_BOOT):
        idx = stratified_boot_indices(y, rng)
        yb, rb = y[idx], risk[idx]
        aucs.append(roc_auc_score(yb, rb))
        pred = (rb >= STEPUP).astype(int)
        recalls.append(float(((pred == 1) & (yb == 1)).sum() / max((yb == 1).sum(), 1)))
        fprs.append(float(((pred == 1) & (yb == 0)).sum() / max((yb == 0).sum(), 1)))
        pt = paired.iloc[idx]
        rb_series = pd.Series(rb, index=pt.index)
        for t in threats:
            mask = pt["attack_type"] == t
            if mask.sum() > 0:
                per_threat[t].append(float((rb_series[mask] >= STEPUP).mean()))

    def ci(arr):
        a = np.array(arr)
        return float(np.mean(a)), float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))

    auc_m, auc_lo, auc_hi = ci(aucs)
    rec_m, rec_lo, rec_hi = ci(recalls)
    fpr_m, fpr_lo, fpr_hi = ci(fprs)
    per_ci = {t: ci(v) for t, v in per_threat.items() if v}

    # ---------------- 2. paired bootstrap significance test vs SPC ----------------
    auc_diffs = []
    rng2 = np.random.default_rng(RNG_SEED + 1)
    for _ in range(N_BOOT):
        idx = stratified_boot_indices(y, rng2)
        yb = y[idx]
        auc_diffs.append(roc_auc_score(yb, risk[idx]) - roc_auc_score(yb, spc[idx]))
    auc_diffs = np.array(auc_diffs)
    diff_m, diff_lo, diff_hi = float(np.mean(auc_diffs)), float(np.percentile(auc_diffs, 2.5)), \
        float(np.percentile(auc_diffs, 97.5))
    # empirical two-sided p-value: how often does the bootstrap distribution of
    # the difference cross 0 (i.e. SPC matching or beating AEGIS)?
    p_value = float(2 * min((auc_diffs <= 0).mean(), (auc_diffs >= 0).mean()))
    p_value = min(p_value, 1.0)

    # ---------------- figure ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INKC, ACC, SPCC = "#1F2A37", "#0E9384", "#D1495B"

    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.4))

    a = ax[0]
    labels = ["ROC-AUC", "Recall @ 0.60", "FPR @ 0.60"]
    means = [auc_m, rec_m, fpr_m]
    los = [auc_m - auc_lo, rec_m - rec_lo, fpr_m - fpr_lo]
    his = [auc_hi - auc_m, rec_hi - rec_m, fpr_hi - fpr_m]
    a.errorbar(range(3), means, yerr=[los, his], fmt="o", color=ACC, capsize=5, markersize=8)
    a.set_xticks(range(3)); a.set_xticklabels(labels)
    a.set_ylim(0, 1.05)
    a.set_title("AEGIS headline metrics, 95% bootstrap CI", fontsize=11, color=INKC)
    for sp in ["top", "right"]:
        a.spines[sp].set_visible(False)

    b = ax[1]
    b.hist(auc_diffs, bins=40, color=SPCC, alpha=0.85)
    b.axvline(0, color=INKC, ls="--", lw=1.2, label="no difference")
    b.axvline(diff_m, color=ACC, ls="-", lw=1.5, label=f"observed diff ({diff_m:.3f})")
    b.set_xlabel("AUC(AEGIS) - AUC(SPC), bootstrap replicates")
    b.set_ylabel("count")
    b.set_title(f"Paired bootstrap: AEGIS vs SPC (p={p_value:.4f})", fontsize=11, color=INKC)
    b.legend(frameon=False, fontsize=8)
    for sp in ["top", "right"]:
        b.spines[sp].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "aegis_bootstrap_analysis.png"), dpi=140)
    plt.close(fig)

    # ---------------- report ----------------
    lines = []
    lines.append("# AEGIS - Bootstrap Confidence Intervals & Significance Test\n")
    lines.append("## Method\n")
    lines.append(
        f"Stratified bootstrap ({N_BOOT:,} replicates): legit and attack windows resampled "
        "separately, with replacement, each at their original count, so every replicate keeps the "
        "real class balance. 95% CIs are the 2.5th/97.5th percentiles of the replicate distribution. "
        "The significance test against the SPC baseline is a PAIRED bootstrap - the same resampled "
        "row indices are scored by both AEGIS and SPC each replicate, since both were evaluated on "
        "the identical held-out test set - and reports the AUC-difference distribution directly, "
        "which avoids DeLong's asymptotic-normality assumption.\n")
    lines.append("## AEGIS headline metrics, 95% CI\n")
    lines.append("| Metric | Point estimate | 95% CI |\n|---|---|---|")
    lines.append(f"| ROC-AUC | {auc_m:.3f} | [{auc_lo:.3f}, {auc_hi:.3f}] |")
    lines.append(f"| Recall @ STEP-UP (0.60) | {rec_m*100:.1f}% | [{rec_lo*100:.1f}%, {rec_hi*100:.1f}%] |")
    lines.append(f"| False-positive rate @ STEP-UP (0.60) | {fpr_m*100:.2f}% | [{fpr_lo*100:.2f}%, {fpr_hi*100:.2f}%] |")
    lines.append("\n## Per-threat detection rate, 95% CI\n")
    lines.append("| Threat | Point estimate | 95% CI | Windows |\n|---|---|---|---|")
    for t in threats:
        n_t = int((paired.attack_type == t).sum())
        m, lo, hi = per_ci[t]
        lines.append(f"| {t} | {m*100:.0f}% | [{lo*100:.0f}%, {hi*100:.0f}%] | {n_t} |")
    lines.append(
        "\nNote the width of these intervals tracks sample size directly: threats with fewer "
        "windows (e.g. T7 scope creep, T5 exfil) have visibly wider CIs than T3/T4/T6 - a reminder "
        "that the point estimates alone, without this spread, overstate how precisely we know the "
        "true per-threat detection rate.\n")
    lines.append("## Significance test: AEGIS vs. SPC baseline (paired bootstrap on AUC)\n")
    lines.append(f"- Observed AUC difference (AEGIS - SPC): **{diff_m:.4f}**")
    lines.append(f"- 95% CI on the difference: **[{diff_lo:.4f}, {diff_hi:.4f}]**")
    lines.append(f"- Empirical two-sided p-value: **{p_value:.4f}**")
    verdict = ("The CI excludes zero, so the improvement over the SPC baseline is statistically "
               "significant at the 95% level, not attributable to sampling noise."
               if diff_lo > 0 else
               "The CI includes zero - with this sample size we cannot rule out that some of the "
               "observed gap is sampling noise, though the point estimate still favours AEGIS.")
    lines.append(f"\n{verdict}")
    report = "\n".join(lines) + "\n"

    with open(os.path.join(OUT_DIR, "aegis_bootstrap_analysis.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("Saved reports/aegis_bootstrap_analysis.md, aegis_bootstrap_analysis.png")


if __name__ == "__main__":
    main()
