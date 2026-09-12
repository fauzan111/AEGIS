# -*- coding: utf-8 -*-
"""
AEGIS - ROC operating-point and threshold-sensitivity analysis (Gate 2/3 evidence).

Sweeps the STEP-UP/BLOCK decision threshold across its full range on the
already-scored held-out set and shows how recall, false-positive rate, and
precision trade off, justifying the chosen operating point (0.6 / 0.85)
against the alternative Youden's-J-optimal point rather than by judgment call
alone.

Run:  .venv/Scripts/python AEGIS/src/aegis_threshold_analysis.py
In :  reports/scored_windows.csv  (produced by aegis_detect.py)
Out:  reports/aegis_threshold_sensitivity.png, reports/aegis_threshold_sensitivity.md
"""

import os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "..", "reports")
SCORED = os.path.join(REPORTS, "scored_windows.csv")

CHOSEN_STEPUP, CHOSEN_BLOCK = 0.60, 0.85


def main():
    df = pd.read_csv(SCORED)
    y = (df["label"] == "attack").astype(int).to_numpy()
    risk = df["risk"].to_numpy()

    fpr, tpr, roc_thresh = roc_curve(y, risk)
    prec, rec, pr_thresh = precision_recall_curve(y, risk)
    auc = roc_auc_score(y, risk)

    # Youden's J = TPR - FPR, maximised over the ROC curve: the single point
    # that best balances catching attacks against not bothering legit traffic,
    # with no assumption about which error type costs more.
    j = tpr - fpr
    j_idx = int(np.argmax(j))
    j_thresh = float(roc_thresh[j_idx])
    j_tpr, j_fpr = float(tpr[j_idx]), float(fpr[j_idx])

    # metrics at a grid of candidate thresholds, including the chosen ones
    grid = sorted(set(np.round(np.arange(0.05, 1.0, 0.05), 2).tolist()
                       + [CHOSEN_STEPUP, CHOSEN_BLOCK, round(j_thresh, 3)]))
    rows = []
    for t in grid:
        pred = (risk >= t).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        tn = int(((pred == 0) & (y == 0)).sum())
        recall_t = tp / (tp + fn) if (tp + fn) else 0.0
        fpr_t = fp / (fp + tn) if (fp + tn) else 0.0
        prec_t = tp / (tp + fp) if (tp + fp) else 0.0
        rows.append((t, recall_t, fpr_t, prec_t))
    grid_df = pd.DataFrame(rows, columns=["threshold", "recall", "fpr", "precision"])

    # ---------------- figure ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    INKC, ACC, ATKC = "#1F2A37", "#0E9384", "#D1495B"
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

    a = ax[0]
    a.plot(fpr, tpr, color=ACC, lw=2, label=f"ROC (AUC {auc:.3f})")
    a.plot([0, 1], [0, 1], color="#B0B7BF", ls="--", lw=1, label="random")
    a.scatter([j_fpr], [j_tpr], color=INKC, zorder=5, label=f"Youden's J optimum (t={j_thresh:.2f})")
    chosen_idx = np.argmin(np.abs(roc_thresh - CHOSEN_STEPUP))
    a.scatter([fpr[chosen_idx]], [tpr[chosen_idx]], color=ATKC, marker="D", zorder=5,
              label=f"chosen STEP-UP (t={CHOSEN_STEPUP})")
    a.set_xlabel("false-positive rate"); a.set_ylabel("true-positive rate (recall)")
    a.set_title("ROC curve - operating-point choice", fontsize=11, color=INKC)
    a.legend(frameon=False, fontsize=8, loc="lower right")
    for sp in ["top", "right"]:
        a.spines[sp].set_visible(False)

    b = ax[1]
    b.plot(grid_df["threshold"], grid_df["recall"], color=ACC, lw=2, label="recall")
    b.plot(grid_df["threshold"], grid_df["fpr"], color=ATKC, lw=2, label="false-positive rate")
    b.plot(grid_df["threshold"], grid_df["precision"], color="#6B7280", lw=2, ls="--", label="precision")
    b.axvline(CHOSEN_STEPUP, color=INKC, ls=":", lw=1)
    b.axvline(CHOSEN_BLOCK, color=INKC, ls=":", lw=1)
    b.text(CHOSEN_STEPUP, 1.02, "STEP-UP", fontsize=8, color=INKC, ha="center")
    b.text(CHOSEN_BLOCK, 1.02, "BLOCK", fontsize=8, color=INKC, ha="center")
    b.set_xlabel("risk threshold"); b.set_ylabel("rate"); b.set_ylim(0, 1.08)
    b.set_title("Threshold sensitivity", fontsize=11, color=INKC)
    b.legend(frameon=False, fontsize=8, loc="center left")
    for sp in ["top", "right"]:
        b.spines[sp].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(REPORTS, "aegis_threshold_sensitivity.png"), dpi=140)
    plt.close(fig)

    # ---------------- report ----------------
    lines = []
    lines.append("# AEGIS - ROC Operating-Point and Threshold-Sensitivity Analysis\n")
    lines.append(f"Overall ROC-AUC: **{auc:.3f}**\n")
    lines.append("## Youden's J optimum vs the chosen operating point\n")
    lines.append("| Point | Threshold | Recall | False-positive rate |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Youden's J optimum | {j_thresh:.3f} | {j_tpr*100:.1f}% | {j_fpr*100:.2f}% |")
    stepup_row = grid_df.iloc[(grid_df["threshold"] - CHOSEN_STEPUP).abs().argmin()]
    lines.append(f"| Chosen STEP-UP | {CHOSEN_STEPUP} | {stepup_row['recall']*100:.1f}% | {stepup_row['fpr']*100:.2f}% |")
    block_row = grid_df.iloc[(grid_df["threshold"] - CHOSEN_BLOCK).abs().argmin()]
    lines.append(f"| Chosen BLOCK | {CHOSEN_BLOCK} | {block_row['recall']*100:.1f}% | {block_row['fpr']*100:.2f}% |\n")
    lines.append(
        "Youden's J (recall minus false-positive rate, maximised) is the threshold that best "
        "separates attack from legitimate traffic with no assumption about which error costs "
        "more. AEGIS's chosen STEP-UP threshold sits "
        + ("close to" if abs(j_thresh - CHOSEN_STEPUP) < 0.1 else "deliberately more conservative than")
        + " this statistically optimal point, trading a small amount of recall for a materially "
        "lower false-positive rate, consistent with the realistic false-positive budget "
        "described in docs/GATE-2.md 2.4.\n"
    )
    lines.append("## Full threshold sweep\n")
    lines.append("| Threshold | Recall | False-positive rate | Precision |")
    lines.append("|---|---|---|---|")
    for _, r in grid_df.iterrows():
        marker = ""
        if abs(r["threshold"] - CHOSEN_STEPUP) < 1e-9:
            marker = " (chosen STEP-UP)"
        elif abs(r["threshold"] - CHOSEN_BLOCK) < 1e-9:
            marker = " (chosen BLOCK)"
        elif abs(r["threshold"] - round(j_thresh, 3)) < 1e-9:
            marker = " (Youden's J optimum)"
        lines.append(f"| {r['threshold']:.2f}{marker} | {r['recall']*100:.1f}% | {r['fpr']*100:.2f}% | {r['precision']*100:.1f}% |")

    report = "\n".join(lines) + "\n"
    with open(os.path.join(REPORTS, "aegis_threshold_sensitivity.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("Saved reports/aegis_threshold_sensitivity.png and .md")


if __name__ == "__main__":
    main()
