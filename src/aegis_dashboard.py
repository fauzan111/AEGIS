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
import base64
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SCORED = os.path.join(HERE, "..", "reports", "scored_windows.csv")
BADGE = os.path.join(HERE, "..", "assets", "fastweb_vodafone_badge.png")
HERO_BG = os.path.join(HERE, "..", "assets", "hero_landscape.jpg")
sys.path.insert(0, HERE)
from aegis_detect import REASON_TEXT  # noqa: E402
from generate_synthetic_traffic import AGENTS as AGENT_CFG, ALL_NFS  # noqa: E402

INK, LEGIT, PASS_C, STEP_C, BLOCK_C, ACC = "#1F2A37", "#3B82C4", "#0E9384", "#E0A100", "#D1495B", "#0E9384"
BG, PANEL, CARD, HAIR, MUTE = "#060b18", "#0c1526", "#111c33", "#1c2b45", "#93a3bd"

st.set_page_config(page_title="AEGIS - Zero-Trust Gate", page_icon="\U0001F6E1", layout="wide")

# ------------------------------------------------------------------ i18n
# UI chrome (header, sidebar controls, KPI/tab labels) is translated; deep
# data content (the scored-window table, per-row incident text) stays in
# English, a common scope boundary for a first pass at i18n.
TRANSLATIONS = {
    "EN": {
        "kicker": "5G Academy 2026 &middot; Topic 2, Security &middot; Team 4",
        "hero_title": "Together, we secure the network",
        "hero_tag": "Every request window from a machine agent to a 5G Network Function is scored "
                    "against the agent's behavioural fingerprint, then gated: PASS / STEP-UP / BLOCK.",
        "hero_pitch": "“Credentials prove what you have, AEGIS verifies how you behave.”",
        "nav_dashboard": "Live Dashboard", "nav_docs": "Docs", "nav_github": "GitHub",
        "sidebar_caption": "Zero-Trust Identity for AI Agents on the Network",
        "sidebar_team": "5G Academy 2026 - Team 4",
        "sidebar_link": "Project overview & docs",
        "stepup_threshold": "STEP-UP threshold", "block_threshold": "BLOCK threshold",
        "agents": "Agents", "live_replay": "Live replay",
        "enable_live_replay": "Enable live replay",
        "enable_live_replay_help": "Stream the scored windows in time order, like watching a live "
                                   "SOC feed, instead of viewing the full historical set at once.",
        "speed": "Speed (windows/tick)", "play": "Play", "pause": "Pause", "reset": "Reset",
        "playhead": "Playhead", "now": "Now",
        "live_replay_active": "Live replay active",
        "replay_status": "showing traffic up to {t} ({shown:,} of {total:,} windows revealed so far).",
        "kpi_windows": "Windows", "kpi_pass": "PASS", "kpi_stepup": "STEP-UP", "kpi_block": "BLOCK",
        "kpi_recall": "Attack recall", "kpi_fpr": "False-positive rate",
        "tab_overview": "Live overview", "tab_topology": "Network topology",
        "tab_inspector": "Incident inspector",
        "risk_over_time": "Risk over time", "detection_per_threat": "Detection per threat",
        "no_attack_windows": "No attack windows in the current view yet.",
        "live_event_feed": "Live event feed",
        "no_incidents_yet": "No incidents yet in the current view.",
        "agents_to_nfs": "Agents -> Network Functions",
        "topology_caption": "Grey lines are each agent's authorized baseline scope. A highlighted "
                            "incident's actual traffic is drawn in colour; a dashed line marks a "
                            "scope violation, an NF outside that agent's onboarded baseline.",
        "most_recent_incident": "Most recent incident shown", "touching_nfs": "touching NF(s)",
        "no_incidents_to_highlight": "No incidents in the current view to highlight yet.",
        "incident_inspector": "Incident inspector",
        "windows_flagged": "windows flagged (STEP-UP or BLOCK). Highest-risk first.",
        "inspect_window": "Inspect a flagged window",
        "decision": "Decision", "risk_label": "risk",
        "agent_label": "Agent", "window_label": "Window", "requests_label": "Requests",
        "distinct_nfs_label": "Distinct NFs", "nfs_touched_label": "NFs touched",
        "why_flagged": "Why AEGIS flagged this window:",
        "ground_truth": "Ground truth (synthetic)",
        "actual_attack": "actual attack", "false_positive": "legitimate traffic (false positive)",
    },
    "IT": {
        "kicker": "5G Academy 2026 &middot; Topic 2, Sicurezza &middot; Team 4",
        "hero_title": "Insieme, proteggiamo la rete",
        "hero_tag": "Ogni finestra di richieste da un agente macchina verso una Network Function 5G "
                    "viene valutata rispetto all'impronta comportamentale dell'agente, poi decisa: "
                    "PASS / STEP-UP / BLOCK.",
        "hero_pitch": "“Le credenziali provano cosa hai, AEGIS verifica come ti comporti.”",
        "nav_dashboard": "Dashboard Live", "nav_docs": "Documenti", "nav_github": "GitHub",
        "sidebar_caption": "Identita Zero-Trust per Agenti AI sulla Rete",
        "sidebar_team": "5G Academy 2026 - Team 4",
        "sidebar_link": "Panoramica del progetto",
        "stepup_threshold": "Soglia STEP-UP", "block_threshold": "Soglia BLOCK",
        "agents": "Agenti", "live_replay": "Replay Live",
        "enable_live_replay": "Attiva replay live",
        "enable_live_replay_help": "Riproduce le finestre valutate in ordine cronologico, come un "
                                   "feed SOC dal vivo, invece di mostrare subito l'intero storico.",
        "speed": "Velocita (finestre/tick)", "play": "Riproduci", "pause": "Pausa",
        "reset": "Reimposta", "playhead": "Posizione", "now": "Adesso",
        "live_replay_active": "Replay live attivo",
        "replay_status": "traffico mostrato fino a {t} ({shown:,} di {total:,} finestre rivelate finora).",
        "kpi_windows": "Finestre", "kpi_pass": "PASS", "kpi_stepup": "STEP-UP", "kpi_block": "BLOCK",
        "kpi_recall": "Richiamo attacchi", "kpi_fpr": "Tasso falsi positivi",
        "tab_overview": "Panoramica live", "tab_topology": "Topologia di rete",
        "tab_inspector": "Analisi incidenti",
        "risk_over_time": "Rischio nel tempo", "detection_per_threat": "Rilevamento per minaccia",
        "no_attack_windows": "Nessuna finestra di attacco nella vista attuale.",
        "live_event_feed": "Feed eventi live",
        "no_incidents_yet": "Nessun incidente nella vista attuale.",
        "agents_to_nfs": "Agenti -> Network Function",
        "topology_caption": "Le linee grigie rappresentano l'ambito autorizzato di ciascun agente. "
                            "Il traffico reale di un incidente evidenziato e mostrato a colori; una "
                            "linea tratteggiata indica una violazione dell'ambito, una NF fuori dal "
                            "perimetro assegnato all'agente.",
        "most_recent_incident": "Incidente piu recente mostrato", "touching_nfs": "NF coinvolte",
        "no_incidents_to_highlight": "Nessun incidente da evidenziare nella vista attuale.",
        "incident_inspector": "Analisi incidenti",
        "windows_flagged": "finestre segnalate (STEP-UP o BLOCK). Rischio piu alto per primo.",
        "inspect_window": "Ispeziona una finestra segnalata",
        "decision": "Decisione", "risk_label": "rischio",
        "agent_label": "Agente", "window_label": "Finestra", "requests_label": "Richieste",
        "distinct_nfs_label": "NF distinte", "nfs_touched_label": "NF coinvolte",
        "why_flagged": "Perche AEGIS ha segnalato questa finestra:",
        "ground_truth": "Verita di base (sintetica)",
        "actual_attack": "attacco reale", "false_positive": "traffico legittimo (falso positivo)",
    },
}
LANG = "EN" if st.session_state.get("lang_toggle", True) else "IT"
T = TRANSLATIONS[LANG]


@st.cache_data
def data_uri(path, mime="image/png"):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


hero_uri = data_uri(HERO_BG, mime="image/jpeg") or ""

st.markdown(f"""
<style>
  .aegis-topbar {{ display: flex; align-items: center; justify-content: space-between;
    padding: 6px 4px 16px; flex-wrap: wrap; gap: 10px; }}
  .aegis-topbar img.badge {{ height: 46px; display: block; }}
  .aegis-topbar .tb-nav {{ display: flex; gap: 26px; }}
  .aegis-topbar .tb-nav span {{ color: #f2f6fb; font-size: 15px; font-weight: 700;
    letter-spacing: .02em; }}
  /* IT/EN labels attached directly to the toggle's own container (via its
     st-key-lang_toggle class) so they sit immediately next to the switch no
     matter the viewport width - separate st.columns stretch with the page,
     which pushed the labels away from the switch on wide screens. */
  .st-key-lang_toggle div[data-testid="stCheckbox"] {{
    display: flex; align-items: center; justify-content: center; gap: 8px;
  }}
  .st-key-lang_toggle div[data-testid="stCheckbox"]::before {{
    content: "IT"; order: -1; font-size: 14px; font-weight: 800; color: {MUTE};
  }}
  .st-key-lang_toggle div[data-testid="stCheckbox"]::after {{
    content: "EN"; font-size: 14px; font-weight: 800; color: #f2f6fb;
  }}
  .st-key-lang_toggle div[data-testid="stCheckbox"]:has(input:checked)::before {{ color: {MUTE}; }}
  .st-key-lang_toggle div[data-testid="stCheckbox"]:has(input:checked)::after {{ color: #f2f6fb; }}
  .st-key-lang_toggle div[data-testid="stCheckbox"]:has(input:not(:checked))::before {{ color: #f2f6fb; }}
  .st-key-lang_toggle div[data-testid="stCheckbox"]:has(input:not(:checked))::after {{ color: {MUTE}; }}
  .aegis-hero-banner {{
    background-image: linear-gradient(180deg, rgba(6,11,24,.35) 0%, rgba(6,11,24,.05) 30%,
      rgba(6,11,24,.15) 100%), url('{hero_uri}');
    background-size: cover; background-position: center;
    border: 1px solid {HAIR}; border-radius: 18px; padding: 110px 30px 90px;
    text-align: center; margin-bottom: 22px; position: relative;
  }}
  .aegis-hero-banner .kicker {{ color: #ffffff; font-weight: 800; letter-spacing: .12em;
    font-size: 14px; text-transform: uppercase; text-shadow: 0 2px 14px rgba(0,0,0,.85); }}
  .aegis-hero-banner h1 {{ color: #ffffff; font-size: 68px; font-weight: 900; line-height: 1.05;
    letter-spacing: -.02em; margin: 16px 0 18px; text-shadow: 0 4px 30px rgba(0,0,0,.75); }}
  .aegis-hero-banner .tag {{ color: #ffffff; font-size: 17px; max-width: 680px; margin: 0 auto 16px;
    text-shadow: 0 2px 16px rgba(0,0,0,.85); font-weight: 500; }}
  .aegis-hero-banner .pitch {{ color: #ffffff; font-style: italic; font-size: 15px;
    text-shadow: 0 2px 16px rgba(0,0,0,.85); font-weight: 600; }}
  .kpi-row {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 6px; }}
  .kpi-card {{ background: {PANEL}; border: 1px solid {HAIR}; border-left: 4px solid var(--ac);
    border-radius: 12px; padding: 14px 16px; }}
  .kpi-card .v {{ font-size: 26px; font-weight: 800; color: #f2f6fb; }}
  .kpi-card .l {{ font-size: 11px; color: {MUTE}; text-transform: uppercase; letter-spacing: .05em; margin-top: 2px; }}
  @media (max-width: 900px) {{ .kpi-row {{ grid-template-columns: repeat(3, 1fr); }} }}
</style>
""", unsafe_allow_html=True)


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
    fig, ax = plt.subplots(figsize=(5.6, 3.4), dpi=130)
    agent_y = {a: i for i, a in enumerate(agents_shown)}
    nf_y = {nf: i * (len(agents_shown) - 1) / max(len(ALL_NFS) - 1, 1) for i, nf in enumerate(ALL_NFS)}

    for a in agents_shown:
        ax.scatter([0], [agent_y[a]], s=420, color="#E8F1F8", edgecolor=ACC, zorder=3, linewidths=1.2)
        ax.text(-0.07, agent_y[a], a, ha="right", va="center", fontsize=7, color=INK)
        for nf in AGENT_CFG.get(a, {}).get("scope", []):
            ax.plot([0, 1], [agent_y[a], nf_y[nf]], color="#C9D2DA", lw=0.7, zorder=1)

    for nf in ALL_NFS:
        ax.scatter([1], [nf_y[nf]], s=320, color="#DCEEEB", edgecolor="#0E9384", zorder=3, linewidths=1.2)
        ax.text(1.07, nf_y[nf], nf, ha="left", va="center", fontsize=7, color=INK)

    if highlight_row is not None:
        a = highlight_row["agent_id"]
        touched = highlight_row["nfs_touched"]
        scope = set(AGENT_CFG.get(a, {}).get("scope", []))
        dc = {"BLOCK": BLOCK_C, "STEP-UP": STEP_C}.get(highlight_row["decision"], ACC)
        if a in agent_y:
            ax.scatter([0], [agent_y[a]], s=520, color=dc, edgecolor=INK, zorder=5, linewidths=1.5, alpha=0.85)
        for nf in touched:
            if nf not in nf_y:
                continue
            violation = nf not in scope
            ax.plot([0, 1], [agent_y.get(a, 0), nf_y[nf]], color=dc, lw=2.4 if violation else 1.6,
                    ls="--" if violation else "-", zorder=4)
            ax.scatter([1], [nf_y[nf]], s=400, color=dc, edgecolor=INK, zorder=5, linewidths=1.5, alpha=0.85)

    ax.set_xlim(-0.62, 1.4)
    ax.set_ylim(-0.8, max(len(agents_shown), 1) - 0.2)
    ax.axis("off")
    fig.tight_layout(pad=0.4)
    return fig


# ------------------------------------------------------------------ load + sidebar
df = load()
all_wins = np.sort(df["win"].unique())

st.sidebar.title("\U0001F6E1 AEGIS")
st.sidebar.caption(T["sidebar_caption"])
st.sidebar.markdown(f"**{T['sidebar_team']}**")
st.sidebar.markdown(f"[{T['sidebar_link']}](https://fauzan111.github.io/AEGIS/)")
st.sidebar.divider()

stepup = st.sidebar.slider(T["stepup_threshold"], 0.1, 0.95, 0.60, 0.05)
block = st.sidebar.slider(T["block_threshold"], stepup, 1.0, max(0.85, stepup), 0.05)
agents = sorted(df["agent_id"].unique())
sel_agents = st.sidebar.multiselect(T["agents"], agents, default=agents)

st.sidebar.divider()
st.sidebar.subheader(T["live_replay"])
live_mode = st.sidebar.checkbox(T["enable_live_replay"], value=False,
                                help=T["enable_live_replay_help"])
if "play_idx" not in st.session_state:
    st.session_state.play_idx = 0
if "playing" not in st.session_state:
    st.session_state.playing = False

if live_mode:
    speed = st.sidebar.select_slider(T["speed"], options=[1, 2, 5, 10, 25, 50], value=5)
    pc1, pc2 = st.sidebar.columns(2)
    if pc1.button(T["play"] if not st.session_state.playing else T["pause"], use_container_width=True):
        st.session_state.playing = not st.session_state.playing
    if pc2.button(T["reset"], use_container_width=True):
        st.session_state.play_idx = 0
        st.session_state.playing = False
    st.session_state.play_idx = st.sidebar.slider(
        T["playhead"], 0, len(all_wins) - 1, st.session_state.play_idx)
    current_time = all_wins[st.session_state.play_idx]
    st.sidebar.caption(f"{T['now']}: {pd.Timestamp(current_time)}")
else:
    current_time = all_wins[-1]

view = df[df["agent_id"].isin(sel_agents)].copy()
view["decision"] = decide(view["risk"].to_numpy(), stepup, block)
if live_mode:
    view = view[view["win"] <= current_time]

# ------------------------------------------------------------------ header + KPIs
badge_uri = data_uri(BADGE)
badge_html = f'<img class="badge" src="{badge_uri}" alt="Fastweb + Vodafone">' if badge_uri else \
    '<span style="color:#f2f6fb;font-weight:800;font-size:22px">AEGIS</span>'

tb_logo, tb_nav, tb_lang = st.columns([2.2, 3, 1.6])
with tb_logo:
    st.markdown(f'<div class="aegis-topbar"><div class="tb-left">{badge_html}</div></div>',
               unsafe_allow_html=True)
with tb_nav:
    st.markdown(f'<div class="aegis-topbar"><div class="tb-nav">'
               f'<span>{T["nav_dashboard"]}</span><span>{T["nav_docs"]}</span>'
               f'<span>{T["nav_github"]}</span></div></div>', unsafe_allow_html=True)
with tb_lang:
    # IT/EN labels are attached to this toggle via CSS (::before/::after on its
    # own container, see the st-key-lang_toggle rules above) so they always sit
    # immediately next to the switch, instead of drifting apart in separate
    # st.columns that stretch with the page width.
    is_en = st.toggle("lang", value=st.session_state.get("lang_toggle", True),
                      key="lang_toggle", label_visibility="collapsed")

st.markdown(f"""
<div class="aegis-hero-banner">
  <div class="kicker">{T['kicker']}</div>
  <h1>{T['hero_title']}</h1>
  <div class="tag">{T['hero_tag']}</div>
  <div class="pitch">{T['hero_pitch']}</div>
</div>
""", unsafe_allow_html=True)

if live_mode:
    status = T["replay_status"].format(t=pd.Timestamp(current_time), shown=len(view),
                                        total=len(df[df["agent_id"].isin(sel_agents)]))
    st.info(f"**{T['live_replay_active']}** - {status}", icon="\U0001F534")

npass = int((view.decision == "PASS").sum())
nstep = int((view.decision == "STEP-UP").sum())
nblock = int((view.decision == "BLOCK").sum())
y = (view.label == "attack").astype(int).to_numpy()
flagged = (view.decision != "PASS").to_numpy().astype(int)
rec = float((flagged[y == 1]).mean()) if (y == 1).any() else 0.0
fpr = float((flagged[y == 0]).mean()) if (y == 0).any() else 0.0

kpis = [
    (T["kpi_windows"], f"{len(view):,}", MUTE),
    (T["kpi_pass"], f"{npass:,}", PASS_C),
    (T["kpi_stepup"], f"{nstep:,}", STEP_C),
    (T["kpi_block"], f"{nblock:,}", BLOCK_C),
    (T["kpi_recall"], f"{rec*100:.0f}%", ACC),
    (T["kpi_fpr"], f"{fpr*100:.1f}%", BLOCK_C if fpr > 0.05 else ACC),
]
kpi_html = "".join(
    f'<div class="kpi-card" style="--ac:{color}"><div class="v">{val}</div><div class="l">{label}</div></div>'
    for label, val, color in kpis
)
st.markdown(f'<div class="kpi-row">{kpi_html}</div>', unsafe_allow_html=True)

st.divider()

tab_overview, tab_topology, tab_inspector = st.tabs(
    [T["tab_overview"], T["tab_topology"], T["tab_inspector"]])

# ------------------------------------------------------------------ tab 1: overview
with tab_overview:
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader(T["risk_over_time"])
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
        st.subheader(T["detection_per_threat"])
        atk = view[view.label == "attack"]
        if len(atk):
            rows = []
            for t, g in atk.groupby("attack_type"):
                rows.append((t.replace("_", " "), len(g), float((g.decision != "PASS").mean()) * 100))
            pt = pd.DataFrame(rows, columns=["threat", "windows", "detected_%"]).set_index("threat")
            st.bar_chart(pt["detected_%"], color=ACC, height=280)
        else:
            st.info(T["no_attack_windows"])

    st.subheader(T["live_event_feed"])
    feed = view[view.decision != "PASS"].sort_values("win", ascending=False).head(12)
    if len(feed):
        for _, r in feed.iterrows():
            badge = {"BLOCK": ":red[BLOCK]", "STEP-UP": ":orange[STEP-UP]"}.get(r["decision"], r["decision"])
            reason = REASON_TEXT.get(r["rule_reason"], "behavioural anomaly (ML)") if r["rule_reason"] != "none" \
                else "behavioural anomaly (ML)"
            st.markdown(f"`{r['win']}` **{r['agent_id']}** {badge} (risk {r['risk']:.2f}): {reason}")
    else:
        st.caption(T["no_incidents_yet"])

# ------------------------------------------------------------------ tab 2: topology
with tab_topology:
    st.subheader(T["agents_to_nfs"])
    st.caption(T["topology_caption"])
    incidents = view[view.decision != "PASS"].sort_values("win", ascending=False)
    hl_row = incidents.iloc[0] if len(incidents) else None
    fig = draw_topology(view, sel_agents, highlight_row=hl_row)
    topo_l, topo_c, topo_r = st.columns([1, 2, 1])
    with topo_c:
        st.pyplot(fig, use_container_width=False)
    if hl_row is not None:
        dc = {"BLOCK": "red", "STEP-UP": "orange"}.get(hl_row["decision"], "grey")
        st.markdown(f"{T['most_recent_incident']}: **{hl_row['agent_id']}** at `{hl_row['win']}`, "
                   f"{T['decision'].lower()} :{dc}[{hl_row['decision']}], {T['touching_nfs']}: "
                   f"{', '.join(sorted(hl_row['nfs_touched'])) or 'none recorded'}.")
    else:
        st.caption(T["no_incidents_to_highlight"])

# ------------------------------------------------------------------ tab 3: incident inspector
with tab_inspector:
    st.subheader(T["incident_inspector"])
    flagged_df = view[view.decision != "PASS"].sort_values("risk", ascending=False)
    st.caption(f"{len(flagged_df):,} {T['windows_flagged']}")

    show = flagged_df[["win", "agent_id", "decision", "risk", "rule", "rule_reason", "ml", "n",
                       "distinct_nf", "err_rate", "n_orphan", "max_resp", "label", "attack_type"]].copy()
    show["risk"] = show["risk"].round(2); show["rule"] = show["rule"].round(2); show["ml"] = show["ml"].round(2)
    show["err_rate"] = (show["err_rate"] * 100).round(0)
    st.dataframe(show.head(200), use_container_width=True, height=280,
                column_config={"err_rate": st.column_config.NumberColumn("err %"),
                               "risk": st.column_config.ProgressColumn("risk", min_value=0, max_value=1)})

    if len(flagged_df):
        idx = st.selectbox(T["inspect_window"],
                           options=list(flagged_df.index)[:200],
                           format_func=lambda i: f"{flagged_df.loc[i,'agent_id']} - "
                                                 f"{flagged_df.loc[i,'win']} - {flagged_df.loc[i,'decision']} "
                                                 f"(risk {flagged_df.loc[i,'risk']:.2f})")
        row = flagged_df.loc[idx]
        dc = {"BLOCK": BLOCK_C, "STEP-UP": STEP_C}.get(row["decision"], PASS_C)
        st.markdown(f"### {T['decision']}: <span style='color:{dc}'>**{row['decision']}**</span> "
                    f"- {T['risk_label']} **{row['risk']:.2f}**  (rule {row['rule']:.2f} - ml {row['ml']:.2f})",
                    unsafe_allow_html=True)
        st.markdown(f"**{T['agent_label']}:** `{row['agent_id']}`  -  **{T['window_label']}:** {row['win']}  -  "
                    f"**{T['requests_label']}:** {int(row['n'])}  -  **{T['distinct_nfs_label']}:** {int(row['distinct_nf'])}  -  "
                    f"**{T['nfs_touched_label']}:** {', '.join(sorted(row['nfs_touched'])) or 'n/a'}")
        st.markdown(f"**{T['why_flagged']}**")
        for r in explain(row):
            st.markdown(f"- {r}")
        truth = T["actual_attack"] if row["label"] == "attack" else T["false_positive"]
        st.caption(f"{T['ground_truth']}: **{truth}**"
                  + (f" - {row['attack_type']}" if row["label"] == "attack" else ""))

# ------------------------------------------------------------------ live replay tick
if live_mode and st.session_state.playing:
    if st.session_state.play_idx < len(all_wins) - 1:
        time.sleep(0.35)
        st.session_state.play_idx = min(st.session_state.play_idx + speed, len(all_wins) - 1)
        st.rerun()
    else:
        st.session_state.playing = False
