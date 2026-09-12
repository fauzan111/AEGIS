# -*- coding: utf-8 -*-
"""
AEGIS - Zero-Trust Gate dashboard (Streamlit).

A NOC/SOC-style view of the zero-trust gate: per-agent behaviour, risk scores,
PASS / STEP-UP / BLOCK decisions, a live network-topology view of which agents
are touching which 5G Network Functions, a live-replay mode that streams the
scored windows in time order like a real SOC feed, and an incident inspector
that explains WHY each window was flagged using the actual rule that fired
(not a generic guess).

Run:  .venv/Scripts/streamlit run AEGIS/src/aegis_dashboard.py
Data: reports/scored_windows.csv  (produced by aegis_detect.py)
"""

import os
import sys
import time
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SCORED = os.path.join(HERE, "..", "reports", "scored_windows.csv")
sys.path.insert(0, HERE)
from aegis_detect import REASON_TEXT  # noqa: E402
from generate_synthetic_traffic import AGENTS as AGENT_CFG, ALL_NFS  # noqa: E402

INK, LEGIT, PASS_C, STEP_C, BLOCK_C, ACC = "#1F2A37", "#3B82C4", "#0E9384", "#E0A100", "#D1495B", "#0E9384"

st.set_page_config(page_title="AEGIS - Zero-Trust Gate", page_icon="\U0001F6E1", layout="wide")


@st.cache_data
def load():
    df = pd.read_csv(SCORED, parse_dates=["win"])
    df["nfs_touched"] = df["nfs_touched"].fillna("").apply(
        lambda s: set(s.split(",")) if s else set())
    return df


def decide(risk, stepup, block):
    return np.where(risk >= block, "BLOCK", np.where(risk >= stepup, "STEP-UP", "PASS"))


def explain(row):
    """Human-readable reason(s) a window was flagged, sourced from the actual
    rule that fired (rule_reason, set by aegis_detect.py's rule_score) rather
    than re-guessing from raw feature thresholds - several different rules
    deliberately share score values, so guessing from the score alone would
    sometimes name the wrong threat."""
    reasons = []
    tag = row.get("rule_reason", "none")
    if tag and tag != "none":
        reasons.append(f"**Rule fired:** {REASON_TEXT.get(tag, tag)}")
    if row["ml"] >= 0.5 and (not reasons or row["ml"] > row["rule"]):
        reasons.append("**ML anomaly:** the Isolation Forest finds this window unlike "
                       f"the agent's known-good baseline (ML score {row['ml']:.2f})")
    if not reasons:
        reasons.append("within the agent's normal behavioural envelope")
    return reasons


def draw_topology(view, agents_shown, highlight_row=None):
    """Bipartite agent -> Network Function graph. Thin grey edges are each
    agent's authorized baseline scope; a highlighted incident's actual
    touched NFs are drawn in red, and a red-dashed edge marks a scope
    violation (an NF outside that agent's onboarded baseline)."""
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    agent_y = {a: i for i, a in enumerate(agents_shown)}
    nf_y = {nf: i * (len(agents_shown) - 1) / max(len(ALL_NFS) - 1, 1) for i, nf in enumerate(ALL_NFS)}

    for a in agents_shown:
        ax.scatter([0], [agent_y[a]], s=900, color="#E8F1F8", edgecolor=ACC, zorder=3, linewidths=1.5)
        ax.text(-0.06, agent_y[a], a, ha="right", va="center", fontsize=9, color=INK)
        for nf in AGENT_CFG.get(a, {}).get("scope", []):
            ax.plot([0, 1], [agent_y[a], nf_y[nf]], color="#C9D2DA", lw=1, zorder=1)

    for nf in ALL_NFS:
        ax.scatter([1], [nf_y[nf]], s=700, color="#DCEEEB", edgecolor="#0E9384", zorder=3, linewidths=1.5)
        ax.text(1.06, nf_y[nf], nf, ha="left", va="center", fontsize=9, color=INK)

    if highlight_row is not None:
        a = highlight_row["agent_id"]
        touched = highlight_row["nfs_touched"]
        scope = set(AGENT_CFG.get(a, {}).get("scope", []))
        dc = {"BLOCK": BLOCK_C, "STEP-UP": STEP_C}.get(highlight_row["decision"], ACC)
        if a in agent_y:
            ax.scatter([0], [agent_y[a]], s=1100, color=dc, edgecolor=INK, zorder=5, linewidths=2, alpha=0.85)
        for nf in touched:
            if nf not in nf_y:
                continue
            violation = nf not in scope
            ax.plot([0, 1], [agent_y.get(a, 0), nf_y[nf]], color=dc, lw=3.2 if violation else 2.2,
                    ls="--" if violation else "-", zorder=4)
            ax.scatter([1], [nf_y[nf]], s=850, color=dc, edgecolor=INK, zorder=5, linewidths=2, alpha=0.85)

    ax.set_xlim(-0.55, 1.35)
    ax.set_ylim(-0.8, max(len(agents_shown), 1) - 0.2)
    ax.axis("off")
    return fig


# ------------------------------------------------------------------ load + sidebar
df = load()
all_wins = np.sort(df["win"].unique())

st.sidebar.title("\U0001F6E1 AEGIS")
st.sidebar.caption("Zero-Trust Identity for AI Agents on the Network")
st.sidebar.markdown("**5G Academy 2026 - Team 4**")
st.sidebar.markdown("[Project overview & docs](https://fauzan111.github.io/AEGIS/)")
st.sidebar.divider()

stepup = st.sidebar.slider("STEP-UP threshold", 0.1, 0.95, 0.60, 0.05)
block = st.sidebar.slider("BLOCK threshold", stepup, 1.0, max(0.85, stepup), 0.05)
agents = sorted(df["agent_id"].unique())
sel_agents = st.sidebar.multiselect("Agents", agents, default=agents)

st.sidebar.divider()
st.sidebar.subheader("Live replay")
live_mode = st.sidebar.checkbox("Enable live replay", value=False,
                                help="Stream the scored windows in time order, like watching a live SOC feed, "
                                     "instead of viewing the full historical set at once.")
if "play_idx" not in st.session_state:
    st.session_state.play_idx = 0
if "playing" not in st.session_state:
    st.session_state.playing = False

if live_mode:
    speed = st.sidebar.select_slider("Speed (windows/tick)", options=[1, 2, 5, 10, 25, 50], value=5)
    pc1, pc2 = st.sidebar.columns(2)
    if pc1.button("Play" if not st.session_state.playing else "Pause", use_container_width=True):
        st.session_state.playing = not st.session_state.playing
    if pc2.button("Reset", use_container_width=True):
        st.session_state.play_idx = 0
        st.session_state.playing = False
    st.session_state.play_idx = st.sidebar.slider(
        "Playhead", 0, len(all_wins) - 1, st.session_state.play_idx)
    current_time = all_wins[st.session_state.play_idx]
    st.sidebar.caption(f"Now: {pd.Timestamp(current_time)}")
else:
    current_time = all_wins[-1]

view = df[df["agent_id"].isin(sel_agents)].copy()
view["decision"] = decide(view["risk"].to_numpy(), stepup, block)
if live_mode:
    view = view[view["win"] <= current_time]

# ------------------------------------------------------------------ header + KPIs
st.title("Zero-Trust Gate - live view")
st.caption("Every request window from a machine agent to a 5G Network Function is scored against "
           "the agent's behavioural fingerprint, then gated: PASS / STEP-UP / BLOCK.")
if live_mode:
    st.info(f"**Live replay active** - showing traffic up to {pd.Timestamp(current_time)} "
           f"({len(view):,} of {len(df[df['agent_id'].isin(sel_agents)]):,} windows revealed so far).",
           icon="\U0001F534")

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

tab_overview, tab_topology, tab_inspector = st.tabs(
    ["Live overview", "Network topology", "Incident inspector"])

# ------------------------------------------------------------------ tab 1: overview
with tab_overview:
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Risk over time")
        fig, ax = plt.subplots(figsize=(7.6, 3.5))
        leg = view[view.label == "legit"]
        atk = view[view.label == "attack"]
        ax.scatter(leg["win"], leg["risk"], s=6, c=LEGIT, alpha=0.35, label="legit", linewidths=0)
        ax.scatter(atk["win"], atk["risk"], s=22, c=BLOCK_C, alpha=0.9, label="attack",
                   marker="x", linewidths=1.2)
        ax.axhline(stepup, color=STEP_C, ls="--", lw=1); ax.axhline(block, color=BLOCK_C, ls="--", lw=1)
        if live_mode:
            ax.axvline(pd.Timestamp(current_time), color=INK, ls="-", lw=1.5, alpha=0.6)
        ax.set_ylabel("risk"); ax.set_ylim(-0.02, 1.02); ax.legend(frameon=False, fontsize=8, loc="center left")
        for sp in ["top", "right"]:
            ax.spines[sp].set_visible(False)
        fig.autofmt_xdate(); fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

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
            st.info("No attack windows in the current view yet.")

    st.subheader("Live event feed")
    feed = view[view.decision != "PASS"].sort_values("win", ascending=False).head(12)
    if len(feed):
        for _, r in feed.iterrows():
            badge = {"BLOCK": ":red[BLOCK]", "STEP-UP": ":orange[STEP-UP]"}.get(r["decision"], r["decision"])
            reason = REASON_TEXT.get(r["rule_reason"], "behavioural anomaly (ML)") if r["rule_reason"] != "none" \
                else "behavioural anomaly (ML)"
            st.markdown(f"`{r['win']}` **{r['agent_id']}** {badge} (risk {r['risk']:.2f}): {reason}")
    else:
        st.caption("No incidents yet in the current view.")

# ------------------------------------------------------------------ tab 2: topology
with tab_topology:
    st.subheader("Agents -> Network Functions")
    st.caption("Grey lines are each agent's authorized baseline scope. A highlighted incident's actual "
              "traffic is drawn in colour; a dashed line marks a scope violation, an NF outside that "
              "agent's onboarded baseline.")
    incidents = view[view.decision != "PASS"].sort_values("win", ascending=False)
    hl_row = incidents.iloc[0] if len(incidents) else None
    fig = draw_topology(view, sel_agents, highlight_row=hl_row)
    st.pyplot(fig, use_container_width=True)
    if hl_row is not None:
        dc = {"BLOCK": "red", "STEP-UP": "orange"}.get(hl_row["decision"], "grey")
        st.markdown(f"Most recent incident shown: **{hl_row['agent_id']}** at `{hl_row['win']}`, "
                   f"decision :{dc}[{hl_row['decision']}], touching NF(s): "
                   f"{', '.join(sorted(hl_row['nfs_touched'])) or 'none recorded'}.")
    else:
        st.caption("No incidents in the current view to highlight yet.")

# ------------------------------------------------------------------ tab 3: incident inspector
with tab_inspector:
    st.subheader("Incident inspector")
    flagged_df = view[view.decision != "PASS"].sort_values("risk", ascending=False)
    st.caption(f"{len(flagged_df):,} windows flagged (STEP-UP or BLOCK). Highest-risk first.")

    show = flagged_df[["win", "agent_id", "decision", "risk", "rule", "rule_reason", "ml", "n",
                       "distinct_nf", "err_rate", "n_orphan", "max_resp", "label", "attack_type"]].copy()
    show["risk"] = show["risk"].round(2); show["rule"] = show["rule"].round(2); show["ml"] = show["ml"].round(2)
    show["err_rate"] = (show["err_rate"] * 100).round(0)
    st.dataframe(show.head(200), use_container_width=True, height=280,
                column_config={"err_rate": st.column_config.NumberColumn("err %"),
                               "risk": st.column_config.ProgressColumn("risk", min_value=0, max_value=1)})

    if len(flagged_df):
        idx = st.selectbox("Inspect a flagged window",
                           options=list(flagged_df.index)[:200],
                           format_func=lambda i: f"{flagged_df.loc[i,'agent_id']} - "
                                                 f"{flagged_df.loc[i,'win']} - {flagged_df.loc[i,'decision']} "
                                                 f"(risk {flagged_df.loc[i,'risk']:.2f})")
        row = flagged_df.loc[idx]
        dc = {"BLOCK": BLOCK_C, "STEP-UP": STEP_C}.get(row["decision"], PASS_C)
        st.markdown(f"### Decision: <span style='color:{dc}'>**{row['decision']}**</span> "
                    f"- risk **{row['risk']:.2f}**  (rule {row['rule']:.2f} - ml {row['ml']:.2f})",
                    unsafe_allow_html=True)
        st.markdown(f"**Agent:** `{row['agent_id']}`  -  **Window:** {row['win']}  -  "
                    f"**Requests:** {int(row['n'])}  -  **Distinct NFs:** {int(row['distinct_nf'])}  -  "
                    f"**NFs touched:** {', '.join(sorted(row['nfs_touched'])) or 'n/a'}")
        st.markdown("**Why AEGIS flagged this window:**")
        for r in explain(row):
            st.markdown(f"- {r}")
        truth = "actual attack" if row["label"] == "attack" else "legitimate traffic (false positive)"
        st.caption(f"Ground truth (synthetic): **{truth}**"
                  + (f" - {row['attack_type']}" if row["label"] == "attack" else ""))

# ------------------------------------------------------------------ live replay tick
if live_mode and st.session_state.playing:
    if st.session_state.play_idx < len(all_wins) - 1:
        time.sleep(0.35)
        st.session_state.play_idx = min(st.session_state.play_idx + speed, len(all_wins) - 1)
        st.rerun()
    else:
        st.session_state.playing = False
