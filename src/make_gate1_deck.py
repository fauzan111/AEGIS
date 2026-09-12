# -*- coding: utf-8 -*-
"""
AEGIS - Gate 1 proposal deck (+ Gantt chart) for the 5G Academy 2026.
Covers what Gate 1 grades: problem/threat model, architecture, technology,
working PoC results, project schedule (Gantt), feasibility and business case.

Run:  .venv/Scripts/python AEGIS/src/make_gate1_deck.py
Out:  AEGIS/slides/AEGIS_Gate1.pptx  +  AEGIS/reports/aegis_gantt.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.dates as mdates
from datetime import datetime

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
SLIDES = os.path.join(HERE, "..", "slides"); os.makedirs(SLIDES, exist_ok=True)
REPORTS = os.path.join(HERE, "..", "reports")
EVAL_PNG = os.path.join(REPORTS, "aegis_eval.png")
GANTT_PNG = os.path.join(REPORTS, "aegis_gantt.png")

# ---------------- palette (clean light, security identity) ----------------
PAGE  = RGBColor(0xF6, 0xF8, 0xFC)
CARD  = RGBColor(0xFF, 0xFF, 0xFF)
INK   = RGBColor(0x0F, 0x17, 0x2A)
BODY  = RGBColor(0x33, 0x41, 0x55)
MUTE  = RGBColor(0x6B, 0x76, 0x88)
HAIR  = RGBColor(0xE2, 0xE8, 0xF0)
INDIGO = RGBColor(0x36, 0x39, 0xCD)   # primary
RED    = RGBColor(0xD1, 0x49, 0x5B)   # attack / block
GREEN  = RGBColor(0x0E, 0x93, 0x84)   # good / pass
AMBER  = RGBColor(0xE0, 0xA1, 0x00)   # step-up
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
FONT   = "Segoe UI"
FONT_L = "Segoe UI Light"
HEX_INDIGO, HEX_RED, HEX_GREEN, HEX_AMBER, HEX_INK, HEX_MUTE = "#3639CD", "#D1495B", "#0E9384", "#E0A100", "#0F172A", "#6B7688"


def tint(c, f):
    return RGBColor(*[round(v + (0xFF - v) * f) for v in (c[0], c[1], c[2])])


# ============================================================ Gantt chart
def build_gantt():
    tasks = [
        ("Data foundation & threat model", "2026-07-24", "2026-08-01", GREEN, "done"),
        ("Synthetic SBA traffic generator", "2026-07-26", "2026-08-05", GREEN, "done"),
        ("Baseline detector (rules + ML)", "2026-07-27", "2026-08-10", GREEN, "done"),
        ("Gate 1 proposal & business case", "2026-08-05", "2026-09-07", INDIGO, ""),
        ("Detector hardening (recon, temporal)", "2026-08-15", "2026-09-20", INDIGO, ""),
        ("Real-data integration (if granted)", "2026-09-02", "2026-09-25", AMBER, "opt"),
        ("Gate 2 - numerical performance analysis", "2026-09-08", "2026-09-22", INDIGO, ""),
        ("Zero-trust gate dashboard & demo", "2026-09-10", "2026-10-12", INDIGO, ""),
        ("PoC integration & evaluation", "2026-09-22", "2026-10-15", INDIGO, ""),
        ("Storyboard & video", "2026-09-24", "2026-11-01", MUTE, "par"),
    ]
    gates = [("Fastweb meeting", "2026-09-02"), ("Gate 1", "2026-09-07"),
             ("Gate 2", "2026-09-22"), ("Gate 3 · PoC", "2026-10-15")]

    fig, ax = plt.subplots(figsize=(11.2, 4.9))
    for i, (name, s, e, col, tag) in enumerate(tasks):
        y = len(tasks) - i - 1
        sd, ed = datetime.fromisoformat(s), datetime.fromisoformat(e)
        c = (col[0] / 255, col[1] / 255, col[2] / 255)
        ax.barh(y, ed - sd, left=sd, height=0.55, color=c, alpha=0.9,
                edgecolor="white", linewidth=0.8)
        label = name + (" ✓" if tag == "done" else "  (optional)" if tag == "opt"
                        else "  (parallel)" if tag == "par" else "")
        ax.text(sd, y + 0.42, label, fontsize=9, color=HEX_INK, va="bottom")
    ax.set_ylim(-0.6, len(tasks) - 0.1)
    ax.set_yticks([])
    for gname, gd in gates:
        d = datetime.fromisoformat(gd)
        ax.axvline(d, color=HEX_RED, ls="--", lw=1.1, alpha=0.8)
        ax.text(d, len(tasks) - 0.35, " " + gname, rotation=90, fontsize=8.5,
                color=HEX_RED, va="top", ha="left", fontweight="bold")
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_xlim(datetime(2026, 7, 21), datetime(2026, 11, 3))
    plt.setp(ax.get_xticklabels(), fontsize=8, rotation=0)
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.set_title("AEGIS - project schedule (27 Jul → 15 Oct 2026)", fontsize=13,
                 fontweight="bold", color=HEX_INK, loc="left")
    ax.grid(axis="x", color="#EEF1F6", lw=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(GANTT_PNG, dpi=140)
    plt.close(fig)


# ============================================================ pptx helpers
def bg(s, color=PAGE):
    s.background.fill.solid(); s.background.fill.fore_color.rgb = color


def rect(s, x, y, w, h, fill=None, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE,
         shadow=False, radius=None):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    if shadow:
        el = sp._element.spPr
        ef = el.makeelement(qn('a:effectLst'), {})
        sh = ef.makeelement(qn('a:outerShdw'),
                            {'blurRad': '110000', 'dist': '38000', 'dir': '5400000', 'rotWithShape': '0'})
        clr = sh.makeelement(qn('a:srgbClr'), {'val': '0F172A'})
        al = clr.makeelement(qn('a:alpha'), {'val': '15000'})
        clr.append(al); sh.append(clr); ef.append(sh); el.append(ef)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    return sp


def text(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         space_after=2, line_spacing=1.0):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space_after); p.space_before = Pt(0)
        p.line_spacing = line_spacing
        for (t, sz, col, b, it, *rest) in para:
            r = p.add_run(); r.text = t
            r.font.size = Pt(sz); r.font.name = rest[0] if rest else FONT
            r.font.color.rgb = col; r.font.bold = b; r.font.italic = it
    return tb


def head(s, kicker, title, sub=None):
    rect(s, 0, 0, 0.22, 7.5, fill=INDIGO)
    text(s, 0.62, 0.4, 12.0, 0.3, [[(kicker, 11, INDIGO, True, False)]])
    text(s, 0.62, 0.72, 12.1, 0.6, [[(title, 26, INK, True, False)]])
    if sub:
        text(s, 0.62, 1.3, 12.1, 0.35, [[(sub, 12.5, MUTE, False, True, FONT_L)]])


def foot(s, n):
    text(s, 0.62, 7.12, 9.0, 0.3, [[("AEGIS · Zero-Trust Identity for AI Agents · Team 4", 8.5, MUTE, False, False)]])
    text(s, 12.4, 7.12, 0.5, 0.3, [[(str(n), 9, MUTE, False, False)]], align=PP_ALIGN.RIGHT)


def bullets(s, x, y, w, h, items, accent, size=11.5, gap=6):
    runs = [[("-  ", size, accent, True, False), (it, size, BODY, False, False)] for it in items]
    text(s, x, y, w, h, runs, line_spacing=1.14, space_after=gap)


# ============================================================ build deck
build_gantt()
prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BL = prs.slide_layouts[6]
N = [0]


def nxt():
    N[0] += 1
    s = prs.slides.add_slide(BL); bg(s); return s


# ---- 1 cover
s = nxt()
rect(s, 0, 0, 13.333, 7.5, fill=INK)
rect(s, 0, 0, 13.333, 0.16, fill=INDIGO)
text(s, 0.9, 1.5, 11.5, 0.4, [[("5G ACADEMY 2026  ·  FASTWEB + VODAFONE  ·  TOPIC 2 - SECURITY", 12, tint(INDIGO, 0.4), True, False)]])
text(s, 0.9, 2.15, 11.5, 1.0, [[("AEGIS", 66, WHITE, True, False)]])
text(s, 0.92, 3.35, 11.5, 0.5, [[("Zero-Trust Identity for AI Agents on the Network", 22, tint(INDIGO, 0.55), False, False)]])
text(s, 0.92, 4.15, 11.5, 0.4, [[("Credentials prove what you have - AEGIS verifies how you behave.", 14, RGBColor(0xC7,0xCE,0xDB), False, True, FONT_L)]])
rect(s, 0.94, 4.95, 0.8, 0.04, fill=RED)
text(s, 0.92, 5.2, 11.5, 0.35, [[("Gate 1 - Project Proposal  ·  prepared for the 2 September dev meeting", 13, WHITE, True, False)]])
text(s, 0.92, 5.75, 11.5, 0.6,
     [[("Team 4 - ", 12, tint(INDIGO,0.5), True, False),
       ("Fauzan Ejaz (Captain) · Adithya Zacharia Valavi · Ghazanfar Anees Siddiqui · Llagami Tedi", 12, RGBColor(0xC7,0xCE,0xDB), False, False)]])

# ---- 2 plain-english glossary (5 terms you'll hear today)
s = nxt()
head(s, "BEFORE WE START", "Five terms you'll hear today, in plain English",
     "No prior 5G or AI knowledge assumed. Everything below is all you need to follow the rest of this talk.")
glossary = [
    ("Network Function", "One specialised system inside the 5G network, "
     "like one department in a company (example: the system that tracks "
     "device sessions)."),
    ("Agent", "An automated piece of software, a bot or script, that logs "
     "in and calls the network on its own, with no human clicking "
     "anything, the way an employee would use an internal tool."),
    ("Behavioural fingerprint", "The normal working pattern we learn for "
     "each agent, what it usually does, when, and how often, so we can "
     "tell if it starts acting differently."),
    ("Risk score", "A single number from 0 to 1 that says how unusual an "
     "agent's recent activity looks compared to its own normal pattern."),
    ("PASS / STEP-UP / BLOCK", "The three outcomes: let it through, "
     "challenge it for extra verification, or stop it and alert a human."),
]
gy = 1.95
for i, (t, d) in enumerate(glossary):
    y = gy + i * 0.98
    rect(s, 0.62, y, 12.11, 0.86, fill=CARD, line=HAIR, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    rect(s, 0.62, y, 0.09, 0.86, fill=INDIGO)
    text(s, 0.95, y + 0.14, 3.0, 0.6, [[(t, 13, INDIGO, True, False)]], anchor=MSO_ANCHOR.MIDDLE)
    text(s, 4.1, y + 0.1, 8.4, 0.66, [[(d, 11.5, BODY, False, False)]], anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
foot(s, 2)

# ---- 3 problem / why now
s = nxt()
head(s, "THE PROBLEM · WHY NOW", "Machine agents now command the network",
     "As networks become AI-native, automations - not humans - call the control plane.")
col_w = 3.94
prob = [
    ("The shift", INDIGO, ["Orchestration, closed-loop automation, OSS jobs and LLM copilots",
                           "call 5G Network Functions over the Service-Based Interface (SBI)",
                           "- the same control APIs a human operator's tooling uses."]),
    ("The gap", RED, ["A stolen token or a compromised automation account passes AAA -",
                      "the credential is valid, but the actor behind it is not.",
                      "Authentication asks “is the credential valid?”, never “is this really"
                      " our agent, behaving as it always does?”"]),
    ("The answer", GREEN, ["Zero-trust for machine identities (NIST SP 800-207):",
                           "learn each agent's behavioural fingerprint and verify every",
                           "request against it - continuously. Never trust, always verify."]),
]
for i, (t, c, items) in enumerate(prob):
    x = 0.62 + i * (col_w + 0.22)
    rect(s, x, 1.9, col_w, 3.5, fill=CARD, line=HAIR, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05, shadow=True)
    rect(s, x, 1.9, col_w, 0.09, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    text(s, x + 0.28, 2.15, col_w - 0.5, 0.35, [[(t, 15, c, True, False)]])
    text(s, x + 0.28, 2.65, col_w - 0.55, 2.6, [[(" ".join(items), 12, BODY, False, False)]], line_spacing=1.22)
rect(s, 0.62, 5.65, 12.11, 0.95, fill=tint(INDIGO, 0.9), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
rect(s, 0.62, 5.65, 0.09, 0.95, fill=INDIGO)
text(s, 0.95, 5.86, 11.6, 0.5,
     [[("In scope: ", 12.5, INDIGO, True, False),
       ("orchestration / API agents on network control services - a control-plane security "
        "problem that exists today, not a general “AI safety” concept.", 12.5, INK, False, False)]], line_spacing=1.1)
foot(s, 3)

# ---- 3 threat model
s = nxt()
head(s, "THREAT MODEL", "Seven threats - all built and detected",
     "We assume the attacker already holds a valid credential. AEGIS catches them by behaviour.")
threats = [
    ("T1", "Impersonation", "valid token, wrong role", "endpoint mix / timing mismatch"),
    ("T2", "Compromised agent", "legit agent starts new actions", "drift from its own baseline"),
    ("T3", "Recon / enumeration", "scanning endpoints & IDs", "high error rate, broad surface"),
    ("T4", "Volumetric abuse", "flooding a Network Function", "request-rate spike vs envelope"),
    ("T5", "Exfiltration", "quiet, large data pulls", "payload size + off-hours"),
    ("T6", "Bad call sequence", "release before create", "orphan session state machine"),
    ("T7", "Scope creep", "touching NFs outside role", "out-of-scope access"),
]
cw, ch, gx, gy = 3.94, 1.28, 0.22, 0.2
for i, (tid, name, what, sig) in enumerate(threats):
    r, c = divmod(i, 3)
    x = 0.62 + c * (cw + gx); y = 1.85 + r * (ch + gy)
    rect(s, x, y, cw, ch, fill=CARD, line=HAIR, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    rect(s, x, y, 0.5, ch, fill=tint(RED, 0.85), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    text(s, x, y, 0.5, ch, [[(tid, 15, RED, True, False)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.62, y + 0.14, cw - 0.7, 0.3, [[(name, 12.5, INK, True, False)]])
    text(s, x + 0.62, y + 0.46, cw - 0.72, 0.3, [[(what, 10, MUTE, False, True)]])
    text(s, x + 0.62, y + 0.76, cw - 0.72, 0.4, [[("↳ ", 10, GREEN, True, False), (sig, 10, BODY, False, False)]], line_spacing=1.0)
# 8th cell - coverage note
x = 0.62 + 2 * (cw + gx); y = 1.85 + 2 * (ch + gy)
rect(s, x, y, cw, ch, fill=tint(GREEN, 0.88), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
text(s, x + 0.25, y + 0.2, cw - 0.5, 0.9, [[("All 7 detected", 14, GREEN, True, False)],
     [("in the working baseline - see results.", 11, BODY, False, False)]], line_spacing=1.1)
foot(s, 4)

# ---- 4 architecture
s = nxt()
head(s, "ARCHITECTURE", "OBSERVE → FINGERPRINT → SCORE → DECIDE",
     "A zero-trust gate on every agent→NF request. Production: an inline policy check at the edge (FASTedge).")
steps = [
    ("OBSERVE", "Parse each request: agent id, method, NF, endpoint, timing, payload, status."),
    ("FINGERPRINT", "Windowed behavioural vector vs the agent's known-good baseline (scope, rate, sequence, errors)."),
    ("SCORE", "Rules (hard limits) + ML anomaly (Isolation Forest, trained on legit only) → risk 0-1."),
    ("DECIDE", "Thresholds → PASS / STEP-UP / BLOCK, with a plain-language reason."),
]
cw = 2.9
for i, (t, d) in enumerate(steps):
    x = 0.62 + i * (cw + 0.19)
    rect(s, x, 2.1, cw, 2.0, fill=CARD, line=HAIR, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.07, shadow=True)
    rect(s, x, 2.1, cw, 0.08, fill=INDIGO, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    rect(s, x + 0.25, 2.34, 0.44, 0.44, fill=tint(INDIGO, 0.86), shape=MSO_SHAPE.OVAL)
    text(s, x + 0.25, 2.34, 0.44, 0.44, [[(f"0{i+1}", 13, INDIGO, True, False)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.8, 2.4, cw - 0.9, 0.35, [[(t, 13.5, INK, True, False)]], anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.26, 3.0, cw - 0.5, 1.0, [[(d, 10.5, BODY, False, False)]], line_spacing=1.12)
    if i < 3:
        text(s, x + cw - 0.02, 2.95, 0.24, 0.4, [[("→", 17, MUTE, True, False)]], align=PP_ALIGN.CENTER)
# decision legend
dy = 4.5
for i, (lab, c, desc) in enumerate([("PASS", GREEN, "behaves like its known-good self"),
                                    ("STEP-UP", AMBER, "challenge - re-auth / approval / throttle"),
                                    ("BLOCK", RED, "quarantine the identity, alert the SOC")]):
    x = 0.62 + i * (3.98 + 0.19)
    rect(s, x, dy, 3.98, 1.0, fill=tint(c, 0.9), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    rect(s, x, dy, 0.09, 1.0, fill=c)
    text(s, x + 0.28, dy + 0.18, 3.6, 0.35, [[(lab, 14, c, True, False)]])
    text(s, x + 0.28, dy + 0.56, 3.6, 0.35, [[(desc, 11, BODY, False, False)]])
text(s, 0.62, 5.85, 12.1, 0.5,
     [[("Fingerprint features: ", 11.5, INDIGO, True, False),
       ("request rate & inter-arrival · distinct NFs/endpoints · method mix · call-sequence "
        "(session state machine) · error rate · payload size · time-of-day.", 11.5, BODY, False, False)]],
     line_spacing=1.1)
foot(s, 5)

# ---- 5 technology
s = nxt()
head(s, "TECHNOLOGY STACK", "Open-source, reproducible, edge-deployable",
     "Everything the PoC needs runs on open-source; internal platforms are an upgrade, not a dependency.")
cols = [
    ("DATA", GREEN, ["Synthetic 5G SBA traffic generator (5 agents, threats T1-T7)",
                     "208k labelled requests over the Service-Based Interface",
                     "Real M2M / API-gateway logs pluggable if offered"]),
    ("DETECTION", INDIGO, ["Isolation Forest (scikit-learn), trained on legit only",
                           "Deterministic rules + session state machine",
                           "Held-out calibration → honest operating point"]),
    ("GATE & DEMO", AMBER, ["Streamlit zero-trust gate dashboard (PASS/STEP-UP/BLOCK)",
                            "Per-agent risk, incident inspector, plain-language ‘why’",
                            "Production vision: inline policy check at FASTedge"]),
]
for i, (t, c, items) in enumerate(cols):
    x = 0.62 + i * (3.94 + 0.22)
    rect(s, x, 1.95, 3.94, 3.2, fill=CARD, line=HAIR, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05, shadow=True)
    rect(s, x, 1.95, 3.94, 0.09, fill=c, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    text(s, x + 0.28, 2.2, 3.4, 0.35, [[(t, 14, c, True, False)]])
    bullets(s, x + 0.3, 2.68, 3.4, 2.3, items, c, size=11)
rect(s, 0.62, 5.45, 12.11, 1.05, fill=tint(INDIGO, 0.92), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
text(s, 0.9, 5.62, 11.6, 0.35, [[("STANDARDS & FRAMEWORKS", 11, INDIGO, True, False)]])
text(s, 0.9, 5.96, 11.6, 0.4,
     [[("NIST SP 800-207 Zero-Trust  ·  3GPP Service-Based Architecture (SBI)  ·  "
        "TM Forum closed-loop / OODA  ·  aligns to NIS2 · GDPR · EU AI Act auditability", 12, BODY, False, False)]])
foot(s, 6)

# ---- 6 results (embed eval figure)
s = nxt()
head(s, "PROOF IT WORKS · WORKING PoC", "Results on synthetic 5G SBA traffic",
     "A working prototype already at proposal stage - validated on 11,343 held-out request windows.")
metrics = [("ROC-AUC", "0.99", GREEN), ("Recall", "98%", GREEN),
           ("False positives", "0.8%", GREEN), ("Threats covered", "7 / 7", INDIGO)]
for i, (lab, val, c) in enumerate(metrics):
    x = 0.62 + i * (2.02 + 0.16)
    rect(s, x, 1.85, 2.02, 1.0, fill=tint(c, 0.9), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    text(s, x, 1.98, 2.02, 0.5, [[(val, 24, c, True, False)]], align=PP_ALIGN.CENTER)
    text(s, x, 2.52, 2.02, 0.28, [[(lab.upper(), 9.5, MUTE, True, False)]], align=PP_ALIGN.CENTER)
if os.path.exists(EVAL_PNG):
    s.shapes.add_picture(EVAL_PNG, Inches(0.62), Inches(3.05), width=Inches(9.4))
text(s, 10.25, 3.15, 2.7, 3.6,
     [[("Reading it", 12.5, INK, True, False)],
      [("Left: legit traffic sits near risk 0; attacks separate cleanly above the "
        "STEP-UP/BLOCK lines.", 10.5, BODY, False, False)],
      [("", 6, BODY, False, False)],
      [("Right: every threat T1-T7 detected (recon 89%, the rest ~100%).", 10.5, BODY, False, False)],
      [("", 6, BODY, False, False)],
      [("STEP-UP is a soft challenge; only ~0.8% of legit traffic is ever flagged.", 10.5, MUTE, False, True)]],
     line_spacing=1.14, space_after=4)
foot(s, 7)

# ---- 7 gantt
s = nxt()
head(s, "PROJECT SCHEDULE", "From proposal to a working PoC by 15 October")
if os.path.exists(GANTT_PNG):
    s.shapes.add_picture(GANTT_PNG, Inches(0.62), Inches(1.6), width=Inches(12.1))
text(s, 0.62, 6.75, 12.1, 0.3,
     [[("Green = already done. ", 10.5, GREEN, True, False),
       ("Data foundation, synthetic generator and the baseline detector are complete; the "
        "path to Gate 2/3 is hardening, dashboard and evaluation.", 10.5, MUTE, False, True)]])
foot(s, 8)

# ---- 8 business case + feasibility
s = nxt()
head(s, "BUSINESS CASE & FEASIBILITY", "Why it matters - and why it’s deliverable",
     "Illustrative value model, to be validated with Fastweb + Vodafone.")
levers = [
    ("Risk avoided", "Detects a compromised / spoofed automation before it acts on the control "
                     "plane - cutting mean-time-to-detect from hours to seconds and containing blast-radius."),
    ("Enables safe automation", "Zero-trust on machine identities is the guardrail that lets the "
                                "network move up the autonomy curve (closed-loop / self-healing) without new risk."),
    ("Compliance & audit", "Supports a NIS2 zero-trust posture; every decision is logged and "
                           "explainable - direct evidence for GDPR / EU AI Act accountability."),
    ("Low OPEX", "Automates machine-identity monitoring that no SOC can do by hand at API scale."),
]
for i, (t, d) in enumerate(levers):
    r, c = divmod(i, 2)
    x = 0.62 + c * (6.05 + 0.22); y = 1.95 + r * (1.5 + 0.18)
    rect(s, x, y, 6.05, 1.5, fill=CARD, line=HAIR, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    rect(s, x, y, 0.08, 1.5, fill=INDIGO)
    text(s, x + 0.3, y + 0.18, 5.6, 0.35, [[(t, 13.5, INDIGO, True, False)]])
    text(s, x + 0.3, y + 0.58, 5.6, 0.8, [[(d, 11, BODY, False, False)]], line_spacing=1.12)
rect(s, 0.62, 5.5, 12.11, 1.05, fill=INK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
rect(s, 0.62, 5.5, 0.09, 1.05, fill=GREEN)
text(s, 0.92, 5.68, 11.6, 0.3, [[("FEASIBILITY", 11, tint(GREEN, 0.4), True, False)]])
text(s, 0.92, 5.99, 11.6, 0.5,
     [[("Synthetic-first, so no data approvals block us - and the baseline already works "
        "(ROC-AUC 0.99). Real data upgrades it from credible to proven.", 12.5, WHITE, False, False)]], line_spacing=1.08)
foot(s, 9)

# ---- 9 asks + next steps
s = nxt()
head(s, "ASKS & NEXT STEPS", "What we need - and where we go next")
rect(s, 0.62, 1.95, 6.05, 4.2, fill=tint(AMBER, 0.92), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
rect(s, 0.62, 1.95, 0.09, 4.2, fill=AMBER)
text(s, 0.92, 2.2, 5.6, 0.35, [[("STILL OPEN, FOLLOWING UP AFTER 2 SEP", 12.5, AMBER, True, False)]])
bullets(s, 0.94, 2.7, 5.5, 3.3, [
    "Real (or anonymised) network traffic to validate against, even a small sample or field distributions.",
    "Whether FASTedge exposes a hook to run our check inline, so a BLOCK can actually stop a request, not just flag it.",
    "Which agent or automation types (orchestration, OSS jobs, closed-loop, external access) matter most to you, so we prioritise correctly for Gate 2.",
], AMBER, size=11.5, gap=9)
rect(s, 6.9, 1.95, 5.83, 4.2, fill=tint(INDIGO, 0.93), shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
rect(s, 6.9, 1.95, 0.09, 4.2, fill=INDIGO)
text(s, 7.2, 2.2, 5.4, 0.35, [[("ROADMAP TO GATE 2 & 3", 12.5, INDIGO, True, False)]])
bullets(s, 7.22, 2.7, 5.3, 3.3, [
    "Gate 2 (22 Sep): full numerical performance analysis + hardened detector (recon, temporal, ROC operating points).",
    "Integrate real logs if granted; add more agent profiles & attack variants.",
    "Gate 3 (15 Oct): live zero-trust gate dashboard demoing PASS / STEP-UP / BLOCK end-to-end.",
    "Parallel: storyboard (24 Sep) → shooting (Oct) → final video (1 Nov).",
], INDIGO, size=11.5, gap=8)
text(s, 0.62, 6.4, 12.1, 0.4,
     [[("Credentials prove what you have - AEGIS verifies how you behave.", 13, INK, True, True)]],
     align=PP_ALIGN.CENTER)
foot(s, 10)

# ============================================================ presenter notes (30-min talk, 4 speakers)
NOTES = [
# 1. cover
"FAUZAN · 0:00-1:00 · Intro\n"
"Good morning. We're Team 4 and we're presenting AEGIS, a zero-trust identity check "
"for the AI agents and automations that now operate the 5G network. One line to "
"remember us by: credentials prove what you have, AEGIS verifies how you behave. "
"I'm Fauzan, team captain, and with me are Adithya, Ghazanfar and Llagami, we'll "
"each walk through a part of this.",

# 2. glossary
"FAUZAN · 1:00-2:00 · Plain-English primer\n"
"Before we go further, five quick terms so nothing after this sounds like jargon. "
"A Network Function is one specialised system inside the 5G network, think of it "
"like one department in a company. An agent is a piece of automated software that "
"logs in and acts on its own, no human clicking anything. A behavioural fingerprint "
"is the normal working pattern we learn for each agent. A risk score is one number "
"from 0 to 1 saying how unusual an agent's recent activity looks. And PASS, STEP-UP, "
"BLOCK are the three outcomes: let it through, challenge it, or stop it and alert a "
"human. Keep these five in your head and the rest of this talk will make full sense.",

# 3. problem / why now
"ADITHYA · 2:00-5:00 · The problem\n"
"As networks become AI-native, it's increasingly automations, not humans, calling "
"the network's control systems directly, orchestration tools, closed-loop "
"automation, AI copilots. Here's the gap: today, the only check on these agents is "
"a login check, does the credential work. But a stolen or misused credential still "
"passes that check every time, the password is valid, but the actor behind it isn't "
"who it should be. Authentication can only ever answer 'is this credential valid', "
"never 'is this really our agent, behaving the way it always does'. That second "
"question is what AEGIS answers, continuously, in line with the zero-trust "
"principle of never trust, always verify. And to be clear on scope: this is about "
"machine agents on the network's control systems, not end users, and not general "
"AI safety, a concrete security gap that exists today.",

# 4. threat model
"ADITHYA · 5:00-8:00 · Threat model\n"
"We assume the attacker already has a valid credential, the realistic, hard case. "
"We modelled seven ways that credential could be misused: impersonation, where an "
"identity suddenly behaves like a completely different one; a compromised agent "
"drifting into new behaviour; reconnaissance, broad scanning across systems it "
"wouldn't normally touch; a volumetric flood; slow, quiet data exfiltration; a "
"broken call sequence, like closing something that was never opened; and scope "
"creep, touching a system outside its role entirely. All seven are built into our "
"working prototype and, as we'll show, all seven are currently detected.",

# 5. architecture
"GHAZANFAR · 8:00-11:00 · Architecture\n"
"Here's how the gate actually works, four steps. First, Observe: every request an "
"agent makes gets logged, who, what, when, how big, what came back. Second, "
"Fingerprint: we build a short-term behavioural profile for that agent and compare "
"it against its own normal pattern. Third, Score: two independent checks run "
"together, a set of hard, clear-cut rules, and a machine-learning model trained "
"only on normal behaviour, that spots anything statistically unlike that agent's "
"usual self. Those combine into one risk number. Fourth, Decide: fixed thresholds "
"turn that number into pass, step-up, or block, always with a plain-language "
"reason attached, never a black box. In production, this would run inline at the "
"network edge; today it runs on replayed traffic.",

# 6. tech stack
"GHAZANFAR · 11:00-13:30 · Technology\n"
"Everything here is open-source and runs on an ordinary laptop, no special "
"hardware or licensing. On the data side, we built our own synthetic traffic "
"generator producing labelled 5G-style requests, real logs are pluggable later if "
"offered. On detection, it's a standard machine-learning library, plus "
"deterministic rules and a session state machine, calibrated honestly on data the "
"model never trained on. And for the gate itself, we built a live interactive "
"dashboard showing every decision with its reasoning, which we'll show you running "
"in a moment. This all lines up with recognised standards, zero-trust guidance, "
"the 5G architecture standard, and supports compliance frameworks like GDPR and "
"the EU AI Act.",

# 7. results
"LLAGAMI · 13:30-17:00 · Proof it works\n"
"This isn't a design target, it's a working prototype, already producing real "
"numbers. On our held-out test data, over eleven thousand time windows the model "
"never saw during training, we correctly separated attacks from normal traffic 99% "
"of the time, caught 98% of every attack we injected, and wrongly flagged fewer "
"than 1% of legitimate traffic. All seven threat types are detected. On the left, "
"you can see normal traffic sitting calmly near zero risk while attacks spike "
"clearly above our decision lines, on the right, detection broken down by attack "
"type. The one honest caveat: this proves the method works on data we built "
"ourselves, real traffic is the next validation step, which is exactly what we're "
"asking Fastweb and Vodafone for.",

# 8. gantt
"LLAGAMI · 17:00-19:30 · Schedule\n"
"Here's where we actually are. Everything in green is done already: the threat "
"model, the synthetic data generator, and the baseline detector you just saw "
"results from, that's not a plan, that's built and working. From here to Gate 2 on "
"22 September, we're hardening detection and building out the full numerical "
"analysis. Real-data integration slots in if we're granted access. Gate 3 on 15 "
"October is the live, end-to-end zero-trust gate demo, with the video shoot "
"running in parallel after that.",

# 9. business case + feasibility
"LLAGAMI · 19:30-23:00 · Why it matters, why it's deliverable\n"
"Four reasons this has real value: it avoids risk, catching a compromised "
"automation before it acts, cutting detection time from hours to seconds. It "
"enables safer automation, giving operators the confidence to expand closed-loop, "
"self-healing systems. It supports compliance, every decision is logged and "
"explainable, which is exactly what regulations like GDPR and the EU AI Act ask "
"for. And it's low-effort operationally, automating a kind of monitoring no "
"security team could do by hand at this scale. On feasibility, because we're "
"synthetic-first, no data approval process blocks us from having a working system "
"today, and the baseline numbers already prove the method. Real data only makes it "
"stronger, it isn't a dependency.",

# 10. asks + next steps
"FAUZAN · 23:00-27:00 · Asks and close\n"
"To close, here's what's still open and where we're headed. We're still following "
"up with Fastweb and Vodafone on three things: real or anonymised traffic to "
"validate against, whether FASTedge can let our gate actually block a request "
"inline rather than just flag it, and which agent types matter most to you so we "
"prioritise correctly. Between now and Gate 3 on 15 October, we're hardening the "
"detector, building the full live dashboard demo, and integrating real data if "
"it's made available. We're confident in this direction because the hardest "
"part, proving the detection method actually works, is already done, working, "
"and in front of you today. Thank you, happy to take questions.",
]

for slide, note in zip(prs.slides, NOTES):
    slide.notes_slide.notes_text_frame.text = note

out = os.path.join(SLIDES, "AEGIS_Gate1.pptx")
prs.save(out)
print("Saved", out, "-", len(prs.slides._sldIdLst), "slides")
print("Saved", GANTT_PNG)
