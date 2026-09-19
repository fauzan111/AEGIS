# -*- coding: utf-8 -*-
"""
AEGIS - concept-drift / stationarity check (Gate 2 evidence).

The whole fingerprinting approach assumes an agent's "normal" behaviour is
stable enough that a baseline learned once stays valid. Real agents drift
(config changes, feature rollouts, maintenance windows) - nothing in the
project so far has actually checked whether that assumption holds even
within our own week of synthetic data, let alone stated a re-baselining
cadence.

Method: for each agent and each of four core behavioural features (request
count, error rate, max response size, distinct NFs touched), a two-sample
Kolmogorov-Smirnov test compares the LEGIT-only distribution on the first
day of data against the last day - the two most temporally distant slices,
giving the test the most power to detect real drift over the week. With
5 agents x 4 features = 20 tests, a Benjamini-Hochberg FDR correction is
applied so we're not just capitalising on multiple-comparison noise.

Run:  .venv/Scripts/python AEGIS/src/aegis_concept_drift_check.py
In :  data/aegis_traffic.csv (rebuilds windows via aegis_detect.build_windows)
Out:  reports/aegis_concept_drift_check.md, .png
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "aegis_traffic.csv")
REPORTS = os.path.join(HERE, "..", "reports")
OUT_DIR = os.path.join(REPORTS, "GATE-2")
os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, HERE)
from aegis_detect import build_windows  # noqa: E402

FEATURES = ["n", "err_rate", "max_resp", "distinct_nf"]
ALPHA = 0.05


def benjamini_hochberg(pvals, alpha=0.05):
    """Returns a boolean array: which p-values are significant after FDR
    correction, and the per-test adjusted (q-value) threshold."""
    p = np.asarray(pvals)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    thresh = (np.arange(1, n + 1) / n) * alpha
    below = ranked <= thresh
    if not below.any():
        return np.zeros(n, dtype=bool)
    k_max = np.max(np.where(below)[0])
    cutoff = ranked[k_max]
    return p <= cutoff


def main():
    raw = pd.read_csv(DATA)
    feat = build_windows(raw)
    feat["day"] = feat["win"].dt.date
    days = sorted(feat["day"].unique())
    first_day, last_day = days[0], days[-1]

    legit = feat[feat.label == "legit"]
    agents = sorted(legit["agent_id"].unique())

    rows = []
    for agent in agents:
        g = legit[legit.agent_id == agent]
        g_first = g[g.day == first_day]
        g_last = g[g.day == last_day]
        for f in FEATURES:
            a = g_first[f].to_numpy(dtype=float)
            b = g_last[f].to_numpy(dtype=float)
            if len(a) < 5 or len(b) < 5:
                continue
            stat, p = ks_2samp(a, b)
            rows.append((agent, f, len(a), len(b), float(stat), float(p)))

    result = pd.DataFrame(rows, columns=["agent_id", "feature", "n_first", "n_last", "ks_stat", "p_value"])
    result["significant_fdr"] = benjamini_hochberg(result["p_value"].to_numpy(), ALPHA)

    n_sig = int(result["significant_fdr"].sum())
    n_total = len(result)

    # ---------------- figure ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INKC, ACC, DRIFTC = "#1F2A37", "#0E9384", "#D1495B"

    fig, ax = plt.subplots(figsize=(8, 5))
    pivot = result.pivot(index="agent_id", columns="feature", values="p_value")
    sig_pivot = result.pivot(index="agent_id", columns="feature", values="significant_fdr")
    im = ax.imshow(pivot.to_numpy(), cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(pivot.index))); ax.set_yticklabels(pivot.index, fontsize=8)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.iat[i, j]
            sig = sig_pivot.iat[i, j]
            txt = f"{val:.3f}" + ("*" if sig else "")
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    color="white" if val < 0.3 else INKC, fontweight="bold" if sig else "normal")
    ax.set_title(f"KS test p-value: day 1 vs. day {len(days)} legit traffic\n"
                 f"(* = significant after FDR correction, {n_sig}/{n_total})", fontsize=10, color=INKC)
    fig.colorbar(im, ax=ax, label="p-value (low = drift detected)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "aegis_concept_drift_check.png"), dpi=140)
    plt.close(fig)

    # ---------------- report ----------------
    lines = []
    lines.append("# AEGIS - Concept-Drift / Stationarity Check\n")
    lines.append("## Method\n")
    lines.append(
        f"Two-sample Kolmogorov-Smirnov test per agent per feature, comparing LEGIT-only traffic "
        f"on the first day of data ({first_day}) against the last ({last_day}) - the most "
        f"temporally distant pair available, giving the most power to detect real drift within "
        f"the week. {n_total} tests total (5 agents x {len(FEATURES)} features), with a "
        "Benjamini-Hochberg FDR correction at alpha=0.05 so the result isn't just multiple-"
        "comparison noise.\n")
    lines.append("## Result\n")
    lines.append(f"**{n_sig} of {n_total} agent/feature combinations show statistically "
                 "significant drift** after FDR correction.\n")
    lines.append("| Agent | Feature | KS statistic | p-value | Significant (FDR) |")
    lines.append("|---|---|---|---|---|")
    for _, r in result.sort_values("p_value").iterrows():
        lines.append(f"| {r['agent_id']} | {r['feature']} | {r['ks_stat']:.3f} | "
                     f"{r['p_value']:.4f} | {'YES' if r['significant_fdr'] else 'no'} |")
    if n_sig == 0:
        lines.append(
            "\nNo agent/feature combination shows significant drift within this simulated week - "
            "consistent with the traffic generator producing agents with stable, repeating daily "
            "routines by design. This is expected for a 5-day synthetic window and should NOT be "
            "read as evidence that real production agents are equally stable: config changes, "
            "feature rollouts, and genuine usage evolution over weeks/months are exactly the kind "
            "of drift a 5-day synthetic test cannot surface.")
    else:
        lines.append(
            f"\n{n_sig} combination(s) show real, statistically significant drift even within "
            "this short synthetic week - the fingerprint is not perfectly stationary even in our "
            "own controlled data, let alone in production traffic subject to real config and "
            "usage changes.")
    lines.append(
        "\n## Re-baselining recommendation\n"
        "Given the fingerprint baseline is learned once from a training window and assumed valid "
        "thereafter, and given real 5G network agents will drift over weeks/months even where our "
        "5-day synthetic traffic does not, we recommend a **periodic re-baselining cadence "
        "(e.g. weekly, re-fit on a trailing window) rather than a one-time baseline** for "
        "production deployment - stated here as an explicit Gate 3 design requirement rather than "
        "an implicit assumption.")
    report = "\n".join(lines) + "\n"

    with open(os.path.join(OUT_DIR, "aegis_concept_drift_check.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("Saved reports/aegis_concept_drift_check.md, aegis_concept_drift_check.png")


if __name__ == "__main__":
    main()
