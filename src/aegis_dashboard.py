# -*- coding: utf-8 -*-
"""
AEGIS — Zero-Trust Gate dashboard (Streamlit).

A NOC/SOC-style view of the zero-trust gate: per-agent behaviour, risk scores,
PASS / STEP-UP / BLOCK decisions, per-threat detection, and an incident inspector
that explains WHY each window was flagged.

Run:  .venv/Scripts/streamlit run AEGIS/src/aegis_dashboard.py
Data: reports/scored_windows.csv  (produced by aegis_detect.py)
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SCORED = os.path.join(HERE, "..", "reports", "scored_windows.csv")

INK, LEGIT, PASS_C, STEP_C, BLOCK_C, ACC = "#1F2A37", "#3B82C4", "#0E9384", "#E0A100", "#D1495B", "#0E9384"

st.set_page_config(page_title="AEGIS — Zero-Trust Gate", page_icon="🛡️", layout="wide")


@st.cache_data
def load():
    df = pd.read_csv(SCORED, parse_dates=["win"])
    return df


def decide(risk, stepup, block):
    return np.where(risk >= block, "BLOCK", np.where(risk >= stepup, "STEP-UP", "PASS"))


def explain(row):
    reasons = []
    if row["n_orphan"] >= 1:
        reasons.append(f"**{int(row['n_orphan'])} orphan session op(s)** — update/release of a PDU "
                       "session that was never created (T6 bad sequence)")
    if row["rule"] >= 0.95 and row["n_orphan"] == 0:
        reasons.append("**out-of-scope access** — called a Network Function outside this "
                       "agent's onboarded scope (T1 impersonation / T7 scope-creep)")
    if row["err_rate"] > 0.25 and row["n"] >= 10:
        reasons.append(f"**high error rate** ({row['err_rate']*100:.0f}%) — endpoint/target "
                       "enumeration (T3 recon)")
    if row["max_resp"] > 3500:
        reasons.append(f"**large response payload** ({int(row['max_resp'])} bytes) — possible "
                       "data exfiltration (T5)")
    if row["n"] > 80:
        reasons.append(f"**request-rate spike** ({int(row['n'])} in the window) — volumetric abuse (T4)")
    if not reasons and row["ml"] >= 0.5:
        reasons.append("**behavioural anomaly** — the ML model finds this window unlike the "
                       "agent's known-good baseline")
    if not reasons:
        reasons.append("within the agent's normal behavioural envelope")
    return reasons


# ------------------------------------------------------------------ load + sidebar
df = load()

st.sidebar.title("🛡️ AEGIS")
st.sidebar.caption("Zero-Trust Identity for AI Agents on the Network")
st.sidebar.markdown("**5G Academy 2026 · Team 4**")
st.sidebar.markdown("[← Project overview & docs](https://fauzan111.github.io/AEGIS/)")
st.sidebar.divider()

stepup = st.sidebar.slider("STEP-UP threshold", 0.1, 0.95, 0.50, 0.05)
block = st.sidebar.slider("BLOCK threshold", stepup, 1.0, max(0.80, stepup), 0.05)
agents = sorted(df["agent_id"].unique())
sel_agents = st.sidebar.multiselect("Agents", agents, default=agents)

view = df[df["agent_id"].isin(sel_agents)].copy()
view["decision"] = decide(view["risk"].to_numpy(), stepup, block)

# ------------------------------------------------------------------ header + KPIs
st.title("Zero-Trust Gate — live view")
st.caption("Every request window from a machine agent to a 5G Network Function is scored against "
           "the agent's behavioural fingerprint, then gated: PASS · STEP-UP · BLOCK.")

npass = int((view.decision == "PASS").sum())
nstep = int((view.decision == "STEP-UP").sum())
nblock = int((view.decision == "BLOCK").sum())
y = (view.label == "attack").astype(int).to_numpy()
flagged = (view.decision != "PASS").to_numpy().astype(int)
rec = float((flagged[y == 1]).mean()) if (y == 1).any() else 0.0
fpr = float((flagged[y == 0]).mean()) if (y == 0).any() else 0.0

c = st.columns(6)
c[0].metric("Windows", f"{len(view):,}")
c[1].metric("PASS", f"{npass:,}")
c[2].metric("STEP-UP", f"{nstep:,}")
c[3].metric("BLOCK", f"{nblock:,}")
c[4].metric("Attack recall", f"{rec*100:.0f}%")
c[5].metric("False-positive rate", f"{fpr*100:.1f}%")

st.divider()
left, right = st.columns([1.35, 1])

# ------------------------------------------------------------------ risk timeline
with left:
    st.subheader("Risk over time")
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    leg = view[view.label == "legit"]
    atk = view[view.label == "attack"]
    ax.scatter(leg["win"], leg["risk"], s=6, c=LEGIT, alpha=0.35, label="legit", linewidths=0)
    ax.scatter(atk["win"], atk["risk"], s=22, c=BLOCK_C, alpha=0.9, label="attack",
               marker="x", linewidths=1.2)
    ax.axhline(stepup, color=STEP_C, ls="--", lw=1); ax.axhline(block, color=BLOCK_C, ls="--", lw=1)
    ax.set_ylabel("risk"); ax.set_ylim(-0.02, 1.02); ax.legend(frameon=False, fontsize=8, loc="center left")
    for sp in ["top", "right"]:
        ax.spines[sp].set_visible(False)
    fig.autofmt_xdate(); fig.tight_layout()
    st.pyplot(fig, use_container_width=True)

# ------------------------------------------------------------------ per-threat detection
with right:
    st.subheader("Detection per threat")
    atk = view[view.label == "attack"]
    if len(atk):
        rows = []
        for t, g in atk.groupby("attack_type"):
            rows.append((t.replace("_", " "), len(g), float((g.decision != "PASS").mean()) * 100))
        pt = pd.DataFrame(rows, columns=["threat", "windows", "detected_%"]).set_index("threat")
        st.bar_chart(pt["detected_%"], color=ACC, height=280)
    else:
        st.info("No attack windows in the current filter.")

st.divider()

# ------------------------------------------------------------------ incident inspector
st.subheader("🔎 Incident inspector")
flagged_df = view[view.decision != "PASS"].sort_values("risk", ascending=False)
st.caption(f"{len(flagged_df):,} windows flagged (STEP-UP or BLOCK). Highest-risk first.")

show = flagged_df[["win", "agent_id", "decision", "risk", "rule", "ml", "n",
                   "distinct_nf", "err_rate", "n_orphan", "max_resp", "label", "attack_type"]].copy()
show["risk"] = show["risk"].round(2); show["rule"] = show["rule"].round(2); show["ml"] = show["ml"].round(2)
show["err_rate"] = (show["err_rate"] * 100).round(0)
st.dataframe(show.head(200), use_container_width=True, height=280,
             column_config={"err_rate": st.column_config.NumberColumn("err %"),
                            "risk": st.column_config.ProgressColumn("risk", min_value=0, max_value=1)})

if len(flagged_df):
    idx = st.selectbox("Inspect a flagged window",
                       options=list(flagged_df.index)[:200],
                       format_func=lambda i: f"{flagged_df.loc[i,'agent_id']} · "
                                             f"{flagged_df.loc[i,'win']} · {flagged_df.loc[i,'decision']} "
                                             f"(risk {flagged_df.loc[i,'risk']:.2f})")
    row = flagged_df.loc[idx]
    dc = {"BLOCK": BLOCK_C, "STEP-UP": STEP_C}.get(row["decision"], PASS_C)
    st.markdown(f"### Decision: <span style='color:{dc}'>**{row['decision']}**</span> "
                f"· risk **{row['risk']:.2f}**  (rule {row['rule']:.2f} · ml {row['ml']:.2f})",
                unsafe_allow_html=True)
    st.markdown(f"**Agent:** `{row['agent_id']}`  ·  **Window:** {row['win']}  ·  "
                f"**Requests:** {int(row['n'])}  ·  **Distinct NFs:** {int(row['distinct_nf'])}")
    st.markdown("**Why AEGIS flagged this window:**")
    for r in explain(row):
        st.markdown(f"- {r}")
    truth = "actual attack" if row["label"] == "attack" else "legitimate traffic (false positive)"
    st.caption(f"Ground truth (synthetic): **{truth}**"
               + (f" — {row['attack_type']}" if row["label"] == "attack" else ""))
