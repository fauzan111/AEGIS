# -*- coding: utf-8 -*-
"""
AEGIS — detection pipeline (baseline).

OBSERVE  : load SBI-style request logs
FINGERPRINT : build per-agent behavioural feature vectors over time windows,
              and learn each agent's known-good baseline from LEGIT traffic only
SCORE    : rules layer (scope / rate / error / exfil / sequence)  +
           ML layer (Isolation Forest trained on legit windows)  -> risk 0..1
DECIDE   : PASS / STEP-UP / BLOCK

Then a full numerical evaluation (Gate-2 evidence): ROC-AUC, precision/recall/F1,
per-attack detection rate, and false-positive rate on legit traffic.

Run:  .venv/Scripts/python AEGIS/src/aegis_detect.py
"""

from __future__ import annotations
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "aegis_traffic.csv")
REPORTS = os.path.join(HERE, "..", "reports")
os.makedirs(REPORTS, exist_ok=True)

WINDOW = "60s"          # tumbling window per agent
STEPUP, BLOCK = 0.50, 0.80   # decision thresholds on risk
MIN_N = 5               # below this, a window is too small for an ML fingerprint;
                        # only hard rule breaches can flag it (avoids tiny-window noise)


# ------------------------------------------------------------------ 1. windowing
def flag_orphans(df: pd.DataFrame) -> np.ndarray:
    """Session-level state machine: an update/release referencing a PDU session
    that was never created (or already released) is an orphan operation (T6).
    Runs over the full chronological stream, per agent."""
    from collections import defaultdict
    open_sessions = defaultdict(set)
    orphan = np.zeros(len(df), dtype=int)
    for i, (agent, ep, sid) in enumerate(zip(df["agent_id"], df["endpoint"], df["session_id"])):
        if sid == "-" or pd.isna(sid):
            continue
        if ep == "Nsmf_PDUSession/create":
            open_sessions[agent].add(sid)
        elif ep == "Nsmf_PDUSession/release":
            if sid in open_sessions[agent]:
                open_sessions[agent].discard(sid)
            else:
                orphan[i] = 1                     # release with no open session
        elif ep == "Nsmf_PDUSession/update":
            if sid not in open_sessions[agent]:
                orphan[i] = 1                     # update with no open session
    return orphan


def build_windows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.sort_values("ts").reset_index(drop=True)
    df["win"] = df["ts"].dt.floor(WINDOW)
    df["is_err"] = (df["status"] >= 400).astype(int)
    df["is_get"] = (df["method"] == "GET").astype(int)
    df["is_write"] = df["method"].isin(["POST", "PUT", "DELETE"]).astype(int)
    df["orphan"] = flag_orphans(df)

    g = df.groupby(["agent_id", "win"])
    feat = g.agg(
        n=("endpoint", "size"),
        distinct_nf=("nf", "nunique"),
        distinct_ep=("endpoint", "nunique"),
        err_rate=("is_err", "mean"),
        get_frac=("is_get", "mean"),
        write_frac=("is_write", "mean"),
        mean_resp=("resp_size", "mean"),
        max_resp=("resp_size", "max"),
        n_orphan=("orphan", "sum"),
    ).reset_index()
    feat["hour"] = feat["win"].dt.hour

    # window label: attack if it contains any attack request
    lab = g.apply(lambda x: pd.Series({
        "label": "attack" if (x["label"] == "attack").any() else "legit",
        "attack_type": (x.loc[x["label"] == "attack", "attack_type"].mode().iat[0]
                        if (x["label"] == "attack").any() else "none"),
    }), include_groups=False).reset_index()
    feat = feat.merge(lab, on=["agent_id", "win"])

    # per-window NF set (for the scope rule)
    nfset = g["nf"].apply(lambda s: set(s)).rename("nf_set").reset_index()
    feat = feat.merge(nfset, on=["agent_id", "win"])
    return feat


# ------------------------------------------------------------------ 2. baselines
def learn_baselines(train_legit: pd.DataFrame) -> dict:
    base = {}
    for agent, gdf in train_legit.groupby("agent_id"):
        allowed = set().union(*gdf["nf_set"]) if len(gdf) else set()
        base[agent] = dict(
            allowed_nfs=allowed,
            n_p99=float(np.percentile(gdf["n"], 99)) if len(gdf) else 1.0,
            resp_p99=float(np.percentile(gdf["max_resp"], 99)) if len(gdf) else 1.0,
            err_mean=float(gdf["err_rate"].mean()) if len(gdf) else 0.0,
            hours=set(gdf["hour"].unique().tolist()),
        )
    return base


# ------------------------------------------------------------------ 3. rules layer
def rule_score(row, base) -> float:
    b = base.get(row["agent_id"])
    if b is None:
        return 0.0
    s = 0.0
    n = row["n"]

    # --- HARD rules: fire on any window, small or large (unambiguous evidence) ---
    # T1/T7 — touching an NF outside the agent's onboarded scope
    if row["nf_set"] - b["allowed_nfs"]:
        s = max(s, 0.95)
    # T6 — orphan session ops: update/release of a PDU session never created
    # (proper session-level state machine, so it does not false-fire on normal traffic)
    if row["n_orphan"] >= 1:
        s = max(s, 0.9)

    # --- STATISTICAL rules: need a minimum denominator to be meaningful ---
    if n >= 10:
        # T4 — request-rate spike vs baseline envelope
        if n > 3 * b["n_p99"]:
            s = max(s, 1.0)
        elif n > 1.5 * b["n_p99"]:
            s = max(s, 0.8)
        # T3 — error/enumeration (also require an absolute error count)
        if row["err_rate"] > max(0.25, 3 * b["err_mean"]) and row["err_rate"] * n >= 4:
            s = max(s, 0.75)
        # T5 — large off-baseline responses (exfiltration)
        if row["max_resp"] > 3 * b["resp_p99"] and row["hour"] not in b["hours"]:
            s = max(s, 0.85)
    return s


# ------------------------------------------------------------------ 4. ML layer
ML_FEATURES = ["n", "distinct_nf", "distinct_ep", "err_rate", "get_frac",
               "write_frac", "mean_resp", "max_resp", "hour"]


def ml_scores(fit_legit, calib_legit, test, agents):
    """Isolation Forest on legit windows; agent identity one-hot so the model
    learns each agent's *own* normal (impersonation = unlike-itself).

    The 0..1 calibration uses a HELD-OUT legit split (calib), never the fit set —
    otherwise in-sample scores understate the tail and the operating-point FPR
    blows up out of sample.
    """
    def X(dfr):
        base = dfr[ML_FEATURES].to_numpy(dtype=float)
        oh = np.stack([(dfr["agent_id"] == a).to_numpy(dtype=float) for a in agents], axis=1)
        return np.hstack([base, oh])

    clf = IsolationForest(n_estimators=300, contamination=0.02, random_state=42)
    clf.fit(X(fit_legit))
    s_calib = -clf.score_samples(X(calib_legit))      # out-of-sample legit tail
    s_test = -clf.score_samples(X(test))
    # Map the held-out-legit CDF band [lo, hi] -> [0, 1]. With STEP-UP=0.5 the flag
    # sits near the legit ~97th percentile — an honest ~2-3% ML false-positive budget.
    order = np.sort(s_calib)
    cdf = np.searchsorted(order, s_test, side="right") / len(order)
    lo, hi = 0.95, 0.999
    return np.clip((cdf - lo) / (hi - lo), 0, 1)


# ------------------------------------------------------------------ 5. run + evaluate
def decision(risk):
    return np.where(risk >= BLOCK, "BLOCK", np.where(risk >= STEPUP, "STEP-UP", "PASS"))


def main():
    df = pd.read_csv(DATA)
    feat = build_windows(df)
    agents = sorted(feat["agent_id"].unique())

    legit = feat[feat.label == "legit"].copy()
    attack = feat[feat.label == "attack"].copy()

    # split legit windows: 40% fit IF, 20% held-out calibration, 40% test.
    legit = legit.sample(frac=1.0, random_state=42).reset_index(drop=True)
    c1, c2 = int(0.4 * len(legit)), int(0.6 * len(legit))
    fit_legit, calib_legit, test_legit = legit.iloc[:c1], legit.iloc[c1:c2], legit.iloc[c2:]
    test = pd.concat([test_legit, attack], ignore_index=True)

    base = learn_baselines(pd.concat([fit_legit, calib_legit]))  # baselines from all training legit
    test["rule"] = test.apply(lambda r: rule_score(r, base), axis=1)
    test["ml"] = ml_scores(fit_legit, calib_legit, test, agents)
    # fuse: for small windows trust only hard rules (ML fingerprint not meaningful)
    small = test["n"] < MIN_N
    test["risk"] = np.where(small, test["rule"],
                            test[["rule", "ml"]].max(axis=1))
    test["decision"] = decision(test["risk"].to_numpy())

    y = (test.label == "attack").astype(int).to_numpy()
    risk = test["risk"].to_numpy()
    pred = (risk >= STEPUP).astype(int)          # STEP-UP or BLOCK = flagged

    auc = roc_auc_score(y, risk)
    prec = precision_score(y, pred)
    rec = recall_score(y, pred)
    f1 = f1_score(y, pred)
    fpr = float(((pred == 1) & (y == 0)).sum() / max((y == 0).sum(), 1))

    # per-attack detection rate
    per = {}
    for t, gdf in test[test.label == "attack"].groupby("attack_type"):
        det = float((gdf["risk"] >= STEPUP).mean())
        per[t] = (len(gdf), det)

    # recall on the threats we actually implement a detector for (T6 needs a
    # session-level detector, documented as future work — reported separately)
    covered = test[(test.label == "attack") & (test.attack_type != "T6_sequence")]
    rec_cov = float((covered["risk"] >= STEPUP).mean())

    # ML-only baseline (no rules) for comparison
    auc_ml = roc_auc_score(y, test["ml"].to_numpy())

    # ---- report ----
    lines = []
    lines.append("# AEGIS — Baseline Detection Results\n")
    lines.append(f"- Windows evaluated: **{len(test):,}** "
                 f"(legit {int((y==0).sum()):,} · attack {int((y==1).sum()):,})")
    lines.append(f"- Window size: {WINDOW} · decision thresholds: STEP-UP ≥ {STEPUP}, BLOCK ≥ {BLOCK}\n")
    lines.append("## Headline metrics (rules + ML fused)\n")
    lines.append(f"| Metric | Value |\n|---|---|")
    lines.append(f"| ROC-AUC | **{auc:.3f}** |")
    lines.append(f"| Precision | {prec:.3f} |")
    lines.append(f"| Recall (detection) | **{rec:.3f}** |")
    lines.append(f"| F1 | {f1:.3f} |")
    lines.append(f"| False-positive rate (legit flagged) | **{fpr:.4f}** |")
    lines.append(f"| ROC-AUC — ML only (no rules) | {auc_ml:.3f} |\n")
    lines.append("_All seven threats T1–T7 now have a working detector. T6 uses a "
                 "session-level state machine (orphan update/release detection), which "
                 "replaced the earlier window-count heuristic that false-fired on legit traffic._\n")
    lines.append("## Detection rate per threat\n")
    lines.append("| Threat | Windows | Detected |\n|---|---|---|")
    for t in sorted(per):
        nwin, det = per[t]
        lines.append(f"| {t} | {nwin} | {det*100:.0f}% |")
    dec_counts = test["decision"].value_counts().to_dict()
    lines.append("\n## Gate decisions on the test set\n")
    lines.append("| Decision | Windows |\n|---|---|")
    for d in ["PASS", "STEP-UP", "BLOCK"]:
        lines.append(f"| {d} | {dec_counts.get(d,0):,} |")
    report = "\n".join(lines) + "\n"

    with open(os.path.join(REPORTS, "aegis_baseline_metrics.md"), "w", encoding="utf-8") as f:
        f.write(report)

    # save scored windows for the dashboard later
    test.drop(columns=["nf_set"]).to_csv(os.path.join(REPORTS, "scored_windows.csv"), index=False)

    make_figure(test, per)
    print(report)
    print("Saved reports/aegis_baseline_metrics.md, scored_windows.csv, aegis_eval.png")


def make_figure(test, per):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    INKC, LEGITC, ATKC, ACC = "#1F2A37", "#3B82C4", "#D1495B", "#0E9384"
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    fig.suptitle("AEGIS — zero-trust gate: detection on synthetic 5G SBA traffic",
                 fontsize=13, fontweight="bold", color=INKC, x=0.5, y=0.99)

    # (1) risk distribution: legit vs attack
    a = ax[0]
    bins = np.linspace(0, 1, 26)
    a.hist(test.loc[test.label == "legit", "risk"], bins=bins, color=LEGITC,
           alpha=0.85, label="legit", log=True)
    a.hist(test.loc[test.label == "attack", "risk"], bins=bins, color=ATKC,
           alpha=0.85, label="attack", log=True)
    a.axvline(STEPUP, color="#6B7280", ls="--", lw=1); a.axvline(BLOCK, color=INKC, ls="--", lw=1)
    a.text(STEPUP, 1.5, " STEP-UP", fontsize=8, color="#6B7280")
    a.text(BLOCK, 1.5, " BLOCK", fontsize=8, color=INKC)
    a.set_title("Risk score — legit vs attack", fontsize=11, color=INKC)
    a.set_xlabel("risk"); a.set_ylabel("windows (log)"); a.legend(frameon=False, fontsize=9)
    for sp in ["top", "right"]:
        a.spines[sp].set_visible(False)

    # (2) per-threat detection
    b = ax[1]
    names = sorted(per)
    vals = [per[t][1]*100 for t in names]
    cols = [ACC if v >= 90 else ATKC for v in vals]
    b.barh(range(len(names)), vals, color=cols)
    b.set_yticks(range(len(names))); b.set_yticklabels([t.replace("_", " ") for t in names], fontsize=9)
    b.invert_yaxis(); b.set_xlim(0, 100)
    for i, v in enumerate(vals):
        b.text(min(v+2, 96), i, f"{v:.0f}%", va="center", fontsize=8.5, color=INKC)
    b.set_title("Detection rate per threat", fontsize=11, color=INKC)
    b.set_xlabel("% detected")
    for sp in ["top", "right"]:
        b.spines[sp].set_visible(False)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(REPORTS, "aegis_eval.png"), dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
