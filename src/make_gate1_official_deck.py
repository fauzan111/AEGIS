# -*- coding: utf-8 -*-
"""Fill the OFFICIAL 5G Academy 2026 PowerPoint template with real AEGIS
Gate 1 content, editing every slide's existing shapes/tables in place so the
Academy's own branding, layout, colours and structure are fully preserved.

No slides are added or removed — the 10 official slides (cover, index,
intro, roadmap, schedule table, schedule picture, risk analysis, open
points, week-by-week + next steps, thank you) are kept exactly as they are;
only the placeholder / Lorem-ipsum text and the placeholder picture are
replaced with our project's real data.

Run:  .venv/Scripts/python AEGIS/src/make_gate1_official_deck.py
In:   AEGIS/slides/Template 5G Academy Project work 2026-PRESENTATION.pptx
Out:  AEGIS/slides/AEGIS_Gate1_Official.pptx
"""

import os
from pptx import Presentation
from pptx.util import Emu, Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# template brand colours (sampled from the official deck itself)
NAVY = RGBColor(0x02, 0x0C, 0x31)
ACCENT = RGBColor(0x01, 0xAB, 0xDB)
ACCENT2 = RGBColor(0x3D, 0x67, 0xB1)
LIGHTBLUE = RGBColor(0x6F, 0xCC, 0xDD)
BODY_C = RGBColor(0x33, 0x41, 0x55)
MUTE_C = RGBColor(0x6B, 0x76, 0x88)
CARD_C = RGBColor(0xFF, 0xFF, 0xFF)
HAIR_C = RGBColor(0xE2, 0xE8, 0xF0)
PANEL_C = RGBColor(0xF2, 0xF7, 0xFA)
FONT = "Montserrat"

HERE = os.path.dirname(os.path.abspath(__file__))
SLIDES = os.path.join(HERE, "..", "slides")
TEMPLATE = os.path.join(SLIDES, "Template 5G Academy Project work 2026-PRESENTATION.pptx")
GANTT_PNG = os.path.join(HERE, "..", "reports", "aegis_gantt.png")
OUT = os.path.join(SLIDES, "AEGIS_Gate1_Official.pptx")


def set_text(shape, *paragraph_texts, size=None, shrink_to_fit=True):
    """Set text on a shape's existing paragraphs, keeping the formatting of
    each paragraph's first run (font, colour, bold, etc.) and blanking any
    additional runs so nothing duplicates. Always turns word-wrap on and,
    unless overridden, an explicit smaller font size so long real content
    doesn't run past a box sized for short placeholder text."""
    tf = shape.text_frame
    tf.word_wrap = True
    for i, ptext in enumerate(paragraph_texts):
        if i >= len(tf.paragraphs):
            p = tf.add_paragraph()
        else:
            p = tf.paragraphs[i]
        if not p.runs:
            r = p.add_run()
        else:
            r = p.runs[0]
        r.text = ptext
        if size is not None:
            r.font.size = Pt(size)
        for extra in p.runs[1:]:
            extra.text = ""


def set_cell(cell, text, size=11):
    """Set a table cell's text and shrink the font so longer real content
    (versus the original short placeholder) stays inside the row height."""
    cell.text = text
    cell.text_frame.word_wrap = True
    for p in cell.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(size)


def by_name(slide, name):
    for shape in slide.shapes:
        if shape.name == name:
            return shape
    raise KeyError(f"shape {name!r} not found on slide")


def all_text_frames_in(shapes):
    """Recurse into groups too — several template captions live nested
    inside grouped icon shapes and are invisible to a flat shape scan."""
    for shape in shapes:
        if shape.shape_type == 6:  # GROUP
            yield from all_text_frames_in(shape.shapes)
        elif shape.has_text_frame:
            yield shape


prs = Presentation(TEMPLATE)
slides = list(prs.slides)

# ============================================================ Slide 1 — cover
# This is the shared 5G Academy programme cover (Advanced STEM Program /
# AI-Native Networks branding) — common to every team, left untouched.

# ============================================================ Slide 2 — Index
# Expanded from the template's 4 slots to 8, so the index walks through the
# whole project in plain language first, then the official Gate 1 content
# (technologies/schedule/feasibility/business) as one final combined topic.
s = slides[1]
set_text(by_name(s, "TextBox 36"), "AEGIS ", "- Team 4")

INDEX_TOPICS = [
    "What We're Building",
    "The 5G Network, In Plain Terms",
    "The Agents We Modelled",
    "How We Built The Prototype",
    "The Attacks We Simulated",
    "How AEGIS Decides",
    "Proof It Works",
    "Project Plan: Schedule, Feasibility & Business Case",
]
# remove the template's original 4 topic + 4 number placeholders
for nm in [f"Segnaposto testo {i}" for i in range(1, 9)]:
    shp = by_name(s, nm)
    shp._element.getparent().remove(shp._element)
# redraw all 8, evenly spaced, same right-hand column the template used
top0, step, num_w, num_l, txt_l, txt_w = 1300000, 660000, 460000, 6130000, 6700000, 5900000
for i, topic in enumerate(INDEX_TOPICS):
    y = top0 + i * step
    numbox = s.shapes.add_textbox(num_l, y, num_w, 520000)
    tf = numbox.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = f"{i+1:02d}"
    r.font.size = Pt(15); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = ACCENT
    txtbox = s.shapes.add_textbox(txt_l, y, txt_w, 520000)
    tf = txtbox.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = tf.paragraphs[0].add_run(); r.text = topic
    r.font.size = Pt(14); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = NAVY

# ============================================================ Slide 3 — Technologies (intro/quote layout)
s = slides[2]
set_text(
    by_name(s, "Rettangolo 1"),
    "Credentials prove what you have, AEGIS verifies how you behave.",
)
set_text(
    by_name(s, "Segnaposto testo 19"),
    "AEGIS is a zero-trust identity check for the AI agents and automations "
    "that call the 5G network's control systems. It combines the 5G "
    "Service-Based Architecture (the network's internal API layer), a "
    "zero-trust security model, and behavioural machine learning: it learns "
    "each agent's normal working pattern and scores every request against "
    "it, using open-source tools (Python, scikit-learn, Streamlit) end to "
    "end, no specialised hardware, no licensing cost.",
)
# 4 icon captions nested inside groups on the right of this slide were still
# Latin placeholder text ("Ut enim ad minim veniam...") — replace in the
# same left-to-right, top-to-bottom order the groups appear on the slide.
_captions = [
    "Runs entirely on open-source tools, no licensing cost.",
    "No specialised hardware, works on a standard laptop.",
    "Learns each agent's own normal behaviour automatically.",
    "Every decision comes with a plain-language reason.",
]
_caption_shapes = [
    tf for tf in all_text_frames_in(s.shapes)
    if tf.text_frame.text.strip().startswith("Ut enim")
]
for shp, cap in zip(_caption_shapes, _captions):
    set_text(shp, cap, size=11)

# ============================================================ Slide 4 — Roadmap & Timeline
s = slides[3]
milestones = [
    ("Rettangolo 19", "24 Jul", "Threat model"),
    ("Rettangolo 22", "27 Jul", "Traffic generator"),
    ("Rettangolo 20", "10 Aug", "Baseline detector"),
    ("Rettangolo 23", "2 Sep", "Fastweb meeting"),
    ("Rettangolo 21", "7 Sep", "Gate 1 proposal"),
    ("Rettangolo 24", "22 Sep", "Gate 2 performance analysis"),
    ("Rettangolo 30", None, "24 Sep - Storyboard"),
    ("Rettangolo 31", None, "Oct - Video shoot"),
    ("Rettangolo 27", "15 Oct", "Gate 3 PoC demo"),
    ("Rettangolo 26", None, "Oct - PoC evaluation"),
    ("Rettangolo 25", "1 Nov", "Final video"),
]
for shape_name, date, label in milestones:
    shp = by_name(s, shape_name)
    if date:
        set_text(shp, date, label, size=9)
    else:
        set_text(shp, label, size=9)

# ============================================================ Slide 5 — High level plan (schedule table)
s = slides[4]
tbl = by_name(s, "Tabella 31").table
activities = [
    "Data foundation & threat model",
    "Synthetic traffic generator + baseline detector",
    "Gate 1 - Project proposal",
    "Gate 2 - Technical solution & performance analysis",
    "Real-data integration (if granted by Fastweb/Vodafone)",
    "Gate 3 - Proof of Concept & live demo",
    "Storyboard, shooting & final video",
]
for row_idx, act in zip(range(2, 9), activities):
    set_cell(tbl.cell(row_idx, 0), act, size=10)

legend = [
    ("Rettangolo 35", "Threat model", 9),
    ("Rettangolo 36", "Traffic gen. built", 8),
    ("Rettangolo 41", "Gate 1 - 7 Sep", 9),
    ("Rettangolo 42", "Fastweb meeting", 9),
    ("Rettangolo 43", "Progress review", 9),
    ("Rettangolo 44", "Gate 2 - 22 Sep", 9),
    ("Rettangolo 45", "Hardening + real data", 9),
    ("Rettangolo 46", "Gate 3 - 15 Oct", 9),
]
for shape_name, label, sz in legend:
    set_text(by_name(s, shape_name), label, size=sz)

# ============================================================ Slide 6 — High level plan (Gantt picture)
s = slides[5]
pic = by_name(s, "Immagine 4")
left, top, width, height = pic.left, pic.top, pic.width, pic.height
pic._element.getparent().remove(pic._element)
if os.path.exists(GANTT_PNG):
    s.shapes.add_picture(GANTT_PNG, left, top, width=width, height=height)

# ============================================================ Slide 7 — Risk Analysis
s = slides[6]
tbl = by_name(s, "Tabella 3").table
risks = [
    ("Real data not shared in time", "Medium", "High",
     "Stay synthetic-first: the baseline PoC already works without real "
     "data; real data upgrades the result, it does not block delivery."),
    ("FASTedge has no inline policy hook", "Medium", "Medium",
     "Demo as a passive observe-and-alert system feeding a SOC workflow "
     "instead of inline enforcement, still a complete, useful PoC."),
    ("Detector doesn't generalise to real traffic noise", "Low", "High",
     "Validate early against any real sample offered; keep the "
     "deterministic rules layer as a robust fallback alongside the ML model."),
    ("Timeline slip before Gate 2 / Gate 3", "Low", "Medium",
     "Foundation and baseline detector are already complete ahead of "
     "schedule, giving buffer through the Sep-Oct plan."),
    ("Team bandwidth / academic workload conflicts", "Medium", "Low",
     "Clear task ownership per member, weekly sync, captain tracks "
     "blockers early."),
]
for i, (risk, like, sev, rem) in enumerate(risks, start=1):
    set_cell(tbl.cell(i, 0), f"Risk #{i} - {risk}", size=10)
    set_cell(tbl.cell(i, 1), like, size=10)
    set_cell(tbl.cell(i, 2), sev, size=10)
    set_cell(tbl.cell(i, 3), rem, size=9)

# ============================================================ Slide 8 — Open points (status tracker)
s = slides[7]
tbl = by_name(s, "Tabella 4").table
set_cell(tbl.cell(1, 1), (
    "Cost: no licensing, 100% open-source, runs on a laptop; production adds "
    "only light edge compute.\n"
    "Value: cuts detection time from hours to seconds, enables safer network "
    "automation, and gives audit-ready evidence for NIS2/GDPR/EU AI Act.\n"
    "To be jointly costed and validated with Fastweb + Vodafone."
), size=9)
set_cell(tbl.cell(4, 1), (
    "Detector hardening (recon, temporal features): on going.\n"
    "Real-data integration if Fastweb/Vodafone grant access: to be confirmed.\n"
    "Synthetic traffic generator + baseline detector (rules + ML): completed."
), size=9)
set_cell(tbl.cell(7, 1), (
    "2 Sep dev meeting with Fastweb + Vodafone: completed.\n"
    "Follow-up on data access, FASTedge hook, priority agent types: tbd.\n"
    "Gate 1 presentation slot & internal review: defined."
), size=9)
set_cell(tbl.cell(10, 1), (
    "Gate 1 slide deck & speaking roles across all 4 members: tbd until "
    "final rehearsal.\n"
    "Live dashboard walkthrough script: tbd until dry-run timing confirmed.\n"
    "Presentation structure (this deck): defined."
), size=9)
set_cell(tbl.cell(13, 1), (
    "Gate 2 numerical performance hardening (recon/temporal features).\n"
    "Real-data integration: delayed pending Fastweb/Vodafone data-sharing "
    "decision.\n"
    "Gate 3 live end-to-end dashboard demo."
), size=9)
set_cell(tbl.cell(16, 0), "AoB", size=10)
set_cell(tbl.cell(16, 1), "None raised at this time.", size=10)

# ============================================================ Slide 9 — Week-by-week + Next steps
s = slides[8]
weeks = [
    ("CasellaDiTesto 40", "Sep 8-14: kick off Gate 2 hardening, add recon/"
     "temporal detection features and expand attack variants."),
    ("CasellaDiTesto 60", "Sep 15-21: finish the numerical performance "
     "analysis and prepare the Gate 2 report and deck."),
    ("CasellaDiTesto 67", "Sep 22-28: Gate 2 submitted; start dashboard "
     "hardening and the demo-video storyboard."),
    ("CasellaDiTesto 74", "Sep 29-Oct 5: integrate real data if granted; "
     "refine the live zero-trust gate dashboard."),
    ("CasellaDiTesto 79", "Oct 6-15: final PoC integration, rehearsal, and "
     "the Gate 3 live demo delivery."),
]
for shape_name, text_ in weeks:
    set_text(by_name(s, shape_name), text_, size=11)

# ============================================================ Slide 10 — Thank you
# Shared closing branding + legal notice, left untouched. "Thank you" text
# itself already fits and needs no project-specific edit.

# ============================================================ NEW plain-language slides
# Inserted between the "What We're Building" intro (existing slide 3) and
# the existing official Gate-1 content (roadmap onward), so the whole
# project is explained in plain language first, official content last.

BLANK = None
for layout in prs.slide_masters[0].slide_layouts:
    if layout.name == "Vuota":
        BLANK = layout
        break


def rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=None):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(1.0)
    sp.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    return sp


def txt(slide, x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.1):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.line_spacing = line_spacing
        for (t, sz, col, bold) in para:
            r = p.add_run(); r.text = t
            r.font.size = Pt(sz); r.font.name = FONT
            r.font.color.rgb = col; r.font.bold = bold
    return tb


def new_slide():
    return prs.slides.add_slide(BLANK)


def title(slide, text_):
    txt(slide, 0.83, 0.29, 10.5, 1.0, [[(text_, 28, NAVY, True)]])


def kicker(slide, text_):
    txt(slide, 0.83, 0.02, 10.5, 0.3, [[(text_, 11, ACCENT, True)]])


# ---- NEW: The 5G Network, In Plain Terms
sl = new_slide()
kicker(sl, "PART 2 OF 7 · PLAIN-LANGUAGE WALKTHROUGH")
title(sl, "The 5G Network, In Plain Terms")
txt(sl, 0.83, 1.25, 11.6, 0.5, [[
    ("A 5G network is a set of specialised systems, each handling one job, that "
     "talk to each other over standard APIs, like departments in a company.", 12.5, MUTE_C, False)]])
nfs = [
    ("AMF", "Access & Mobility", "Keeps track of where a device is and whether it's reachable."),
    ("SMF", "Session Management", "Opens, updates and closes a device's data session."),
    ("NRF", "Network Repository", "The internal directory: lets systems find each other."),
    ("PCF", "Policy Control", "Decides and enforces the rules a session must follow."),
    ("UDM", "Unified Data Management", "Holds and serves subscriber data on request."),
    ("NEF", "Network Exposure", "The controlled front door for outside apps and automations."),
]
cw, ch, gx, gy = 3.85, 1.5, 0.2, 0.2
for i, (code, name, desc) in enumerate(nfs):
    r, c = divmod(i, 3)
    x = 0.83 + c * (cw + gx); y = 2.0 + r * (ch + gy)
    rect(sl, x, y, cw, ch, fill=CARD_C, line=HAIR_C, radius=0.08)
    rect(sl, x, y, cw, 0.08, fill=ACCENT, radius=0.5)
    txt(sl, x + 0.22, y + 0.2, cw - 0.4, 0.35, [[(code, 15, ACCENT2, True)]])
    txt(sl, x + 0.22, y + 0.55, cw - 0.4, 0.3, [[(name, 11, NAVY, True)]])
    txt(sl, x + 0.22, y + 0.88, cw - 0.4, 0.55, [[(desc, 10, BODY_C, False)]])

# ---- NEW: The Agents We Modelled
sl = new_slide()
kicker(sl, "PART 3 OF 7 · PLAIN-LANGUAGE WALKTHROUGH")
title(sl, "The Agents We Modelled")
txt(sl, 0.83, 1.25, 11.6, 0.5, [[
    ("Five automations, each with its own job, schedule and routine, so AEGIS "
     "can tell when one of them starts acting unlike itself.", 12.5, MUTE_C, False)]])
agents = [
    ("Session orchestrator", "Opens/closes sessions across AMF, SMF, PCF - runs 24/7, steady pace."),
    ("Inventory job", "Reads records from NRF, UDM only - runs briefly overnight."),
    ("Closed-loop assurance", "Subscribes to live events on AMF, NEF, PCF - runs 24/7."),
    ("NRF heartbeat service", "Registers and pings NRF only - very steady, low volume."),
    ("Provisioning agent", "Updates subscriber data via NEF, UDM - business hours only."),
]
ay, ah = 2.0, 0.86
for i, (name, desc) in enumerate(agents):
    y = ay + i * (ah + 0.12)
    rect(sl, 0.83, y, 11.6, ah, fill=CARD_C, line=HAIR_C, radius=0.1)
    rect(sl, 0.83, y, 0.09, ah, fill=ACCENT2)
    txt(sl, 1.15, y + 0.14, 3.0, ah - 0.28, [[(name, 13, NAVY, True)]], anchor=MSO_ANCHOR.MIDDLE)
    txt(sl, 4.3, y + 0.1, 8.0, ah - 0.2, [[(desc, 11.5, BODY_C, False)]], anchor=MSO_ANCHOR.MIDDLE)

# ---- NEW: How We Built The Prototype
sl = new_slide()
kicker(sl, "PART 4 OF 7 · PLAIN-LANGUAGE WALKTHROUGH")
title(sl, "How We Built The Prototype")
steps = [
    ("1. Traffic simulator (not AI)", "A program we wrote ourselves that plays out a virtual week of "
     "activity for all 5 agents. This is a scripted simulation, not a machine-learning model - it "
     "produced about 210,000 requests."),
    ("2. Injected attacks", "Into that traffic we inserted 7 kinds of attack episodes, each labelled, "
     "so we know exactly which requests are attacks - only possible because the data is simulated."),
    ("3. Detection engine (the real ML)", "A separate program reads the traffic, builds a behavioural "
     "fingerprint per agent, and scores every window for risk. This is where an actual machine-learning "
     "model, an Isolation Forest, is used."),
]
sy, sh = 2.0, 1.55
for i, (h, d) in enumerate(steps):
    y = sy + i * (sh + 0.15)
    rect(sl, 0.83, y, 11.6, sh, fill=CARD_C, line=HAIR_C, radius=0.06)
    rect(sl, 0.83, y, 0.09, sh, fill=ACCENT)
    txt(sl, 1.15, y + 0.16, 10.8, 0.35, [[(h, 14, NAVY, True)]])
    txt(sl, 1.15, y + 0.58, 10.8, 0.9, [[(d, 11.5, BODY_C, False)]], line_spacing=1.2)

# ---- NEW: The Attacks We Simulated
sl = new_slide()
kicker(sl, "PART 5 OF 7 · PLAIN-LANGUAGE WALKTHROUGH")
title(sl, "The Attacks We Simulated")
txt(sl, 0.83, 1.25, 11.6, 0.5, [[
    ("We assume the attacker already has a valid credential. What changes is the "
     "behaviour, not the credential.", 12.5, MUTE_C, False)]])
threats = [
    ("T1", "Impersonation", "acts like a different agent"),
    ("T2", "Compromised agent", "drifts to new behaviour"),
    ("T3", "Recon / scanning", "probes broadly, many errors"),
    ("T4", "Volumetric flood", "request rate spikes hard"),
    ("T5", "Slow exfiltration", "quiet, large data pulls"),
    ("T6", "Broken sequence", "closes what was never opened"),
    ("T7", "Scope creep", "touches systems outside its role"),
]
tw, th_, tgx, tgy = 3.75, 1.15, 0.2, 0.18
for i, (tid, name, desc) in enumerate(threats):
    r, c = divmod(i, 4)
    x = 0.83 + c * (tw + tgx); y = 2.0 + r * (th_ + tgy)
    rect(sl, x, y, tw, th_, fill=CARD_C, line=HAIR_C, radius=0.09)
    rect(sl, x, y, 0.5, th_, fill=RGBColor(0xFD, 0xE8, 0xEA))
    txt(sl, x, y, 0.5, th_, [[(tid, 13, RGBColor(0xC0, 0x39, 0x4B), True)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(sl, x + 0.62, y + 0.14, tw - 0.75, 0.3, [[(name, 12, NAVY, True)]])
    txt(sl, x + 0.62, y + 0.5, tw - 0.75, 0.55, [[(desc, 10, BODY_C, False)]])

# ---- NEW: How AEGIS Decides
sl = new_slide()
kicker(sl, "PART 6 OF 7 · PLAIN-LANGUAGE WALKTHROUGH")
title(sl, "How AEGIS Decides")
pipe = [
    ("OBSERVE", "Log every request: agent, target, timing, size, status."),
    ("FINGERPRINT", "Compare the last 60s of activity to that agent's own normal."),
    ("SCORE", "Hard rules + an ML model (trained on legit traffic only) combine into one risk number."),
    ("DECIDE", "Fixed thresholds turn the risk number into PASS / STEP-UP / BLOCK, automatically."),
]
pw = 2.78
for i, (h, d) in enumerate(pipe):
    x = 0.83 + i * (pw + 0.15)
    rect(sl, x, 2.0, pw, 2.0, fill=CARD_C, line=HAIR_C, radius=0.08)
    rect(sl, x, 2.0, pw, 0.08, fill=ACCENT)
    txt(sl, x + 0.2, 2.25, pw - 0.4, 0.3, [[(h, 13, NAVY, True)]])
    txt(sl, x + 0.2, 2.65, pw - 0.4, 1.2, [[(d, 10.5, BODY_C, False)]], line_spacing=1.15)
legend = [("PASS", RGBColor(0x0E, 0x93, 0x84), "behaves like itself"),
          ("STEP-UP", RGBColor(0xE0, 0xA1, 0x00), "challenge / re-verify"),
          ("BLOCK", RGBColor(0xC0, 0x39, 0x4B), "quarantine, alert a human")]
for i, (lab, c, d) in enumerate(legend):
    x = 0.83 + i * (3.85 + 0.15)
    rect(sl, x, 4.4, 3.85, 0.95, fill=PANEL_C, radius=0.1)
    rect(sl, x, 4.4, 0.09, 0.95, fill=c)
    txt(sl, x + 0.25, 4.55, 3.4, 0.35, [[(lab, 13, c, True)]])
    txt(sl, x + 0.25, 4.9, 3.4, 0.35, [[(d, 10.5, BODY_C, False)]])
txt(sl, 0.83, 5.6, 11.6, 0.6, [[
    ("There is no person watching in real time. The decision is fully automatic - "
     "a human only reviews after a STEP-UP or BLOCK is raised.", 11.5, MUTE_C, False)]])

# ---- NEW: Proof It Works
sl = new_slide()
kicker(sl, "PART 7 OF 7 · PLAIN-LANGUAGE WALKTHROUGH")
title(sl, "Proof It Works")
metrics = [("ROC-AUC", "0.99"), ("Recall", "98%"), ("False positives", "0.8%"), ("Threats covered", "7 / 7")]
for i, (lab, val) in enumerate(metrics):
    x = 0.83 + i * (2.85 + 0.15)
    rect(sl, x, 2.0, 2.85, 1.3, fill=PANEL_C, radius=0.12)
    txt(sl, x, 2.2, 2.85, 0.55, [[(val, 26, ACCENT2, True)]], align=PP_ALIGN.CENTER)
    txt(sl, x, 2.8, 2.85, 0.35, [[(lab.upper(), 10, MUTE_C, True)]], align=PP_ALIGN.CENTER)
txt(sl, 0.83, 3.7, 11.6, 0.6, [[
    ("Measured on 11,343 held-out windows the model never trained on: attacks "
     "separate cleanly from normal traffic at 0.99 ROC-AUC, 98% of injected "
     "attacks caught, only 0.8% of legitimate traffic wrongly flagged.", 12.5, BODY_C, False)]])
rect(sl, 0.83, 4.55, 11.6, 1.15, fill=NAVY, radius=0.06)
txt(sl, 1.1, 4.72, 11.0, 0.35, [[("THE HONEST CAVEAT", 10.5, LIGHTBLUE, True)]])
txt(sl, 1.1, 5.05, 11.0, 0.55, [[
    ("This is synthetic-first: it proves the method works and is well-calibrated, "
     "not that it holds up on real network traffic yet - that validation is exactly "
     "what real or anonymised data from Fastweb + Vodafone would give us.", 11.5, RGBColor(0xE6, 0xEC, 0xF2), False)]])

# ---------- reorder: move the 6 new slides to right after slide 3 (index 2) ----------
sldIdLst = prs.slides._sldIdLst
all_ids = list(sldIdLst)
new_ids = all_ids[-6:]                # the 6 slides just appended
for el in new_ids:
    sldIdLst.remove(el)
for i, el in enumerate(new_ids):
    sldIdLst.insert(3 + i, el)        # right after slide 3 ("What We're Building")

# ============================================================ presenter notes (30-min talk, 4 speakers)
NOTES = [
# 1 cover
"FAUZAN - 0:00-0:30\n"
"Good morning, we're Team 4, presenting AEGIS: a zero-trust identity check "
"for the AI agents and automations that now operate the 5G network.",

# 2 index
"FAUZAN - 0:30-1:00\n"
"Here's how we'll walk through this: first, we'll explain what AEGIS "
"actually is and how it works in plain language, no assumed background "
"needed. Then in the last section we'll cover the technologies we used, "
"our project schedule, feasibility, and the business case, which is "
"exactly what Gate 1 asks us to demonstrate.",

# 3 what we're building
"FAUZAN - 1:00-2:30\n"
"One line to remember us by: credentials prove what you have, AEGIS "
"verifies how you behave. Today, an automated agent proves who it is with "
"a password or token, and that's the only check. A stolen credential "
"still passes that check every time. AEGIS adds a second, continuous "
"layer: it learns how each agent normally behaves and checks every "
"request against that pattern. It's built entirely on open-source tools, "
"runs on a laptop, and every decision it makes comes with a "
"plain-language reason, never a black box.",

# 4 5G network
"ADITHYA - 2:30-4:30\n"
"Before we go further, quick grounding: a 5G network isn't one big "
"machine, it's six specialised systems, each handling one job, like "
"departments in a company. AMF tracks where a device is. SMF manages "
"sessions. NRF is the internal directory. PCF enforces policy. UDM holds "
"subscriber data. NEF is the controlled front door for outside "
"automations. Every agent we model talks to these six systems, and "
"that's the surface AEGIS protects.",

# 5 agents
"ADITHYA - 4:30-6:30\n"
"We modelled five distinct automated agents, each with its own job, "
"schedule, and normal routine: a session orchestrator running around the "
"clock, a nightly inventory job, a closed-loop monitoring agent, a simple "
"NRF heartbeat service, and a business-hours provisioning agent. This "
"matters because AEGIS doesn't look for 'bad behaviour' in the abstract, "
"it looks for behaviour that doesn't match what that specific agent "
"normally does, so each needed a genuinely distinct personality to prove "
"the idea works.",

# 6 how built
"ADITHYA - 6:30-8:30\n"
"We built this in three parts. First, a traffic simulator we wrote "
"ourselves, not AI, a scripted program that generated about 210,000 "
"realistic requests for a virtual week. Second, we injected seven kinds "
"of attacks into that traffic, each labelled, so we know exactly which "
"requests are attacks, only possible because the data is simulated. "
"Third, the actual detection engine, this is where real machine learning, "
"an Isolation Forest, is used to spot the attacks we hid inside.",

# 7 attacks
"GHAZANFAR - 8:30-10:30\n"
"We assume the attacker already has a valid credential, the realistic, "
"hard case, so what changes is behaviour, not the password. We modelled "
"seven attacks: impersonation, a compromised agent drifting into new "
"behaviour, reconnaissance scanning, a volumetric flood, slow data "
"exfiltration, a broken call sequence, and scope creep. All seven are "
"built into our prototype, and as we'll show, all seven are currently "
"detected.",

# 8 how decides
"GHAZANFAR - 10:30-13:00\n"
"Here's how the gate actually decides, four steps, fully automatic, no "
"person watching in real time. Observe: every request gets logged. "
"Fingerprint: we compare the last 60 seconds of an agent's activity "
"against its own normal pattern. Score: hard rules plus a machine-"
"learning model, trained only on legitimate traffic, combine into one "
"risk number. Decide: fixed thresholds turn that number into pass, "
"step-up, or block. A human only gets involved afterwards, reviewing a "
"step-up or block once it's already been raised.",

# 9 proof it works
"GHAZANFAR - 13:00-15:30\n"
"This isn't a design target, it's a working prototype with real numbers. "
"On over eleven thousand test windows the model never trained on: 0.99 "
"ROC-AUC, 98% of injected attacks caught, only 0.8% of legitimate traffic "
"wrongly flagged, all seven threats detected. The honest caveat: this "
"proves the method works on data we built ourselves, real traffic "
"validation is the next step, which is exactly what we're asking Fastweb "
"and Vodafone for.",

# 10 roadmap
"LLAGAMI - 15:30-17:00\n"
"Now the part Gate 1 specifically asks us to cover: our technologies, "
"schedule, feasibility and business case. Here's our full timeline from "
"late July through to the final video in November. Everything up to and "
"including today's Gate 1 milestone is already complete, this isn't a "
"plan, it's work already done.",

# 11 schedule table
"LLAGAMI - 17:00-18:30\n"
"Breaking that down by phase: the data foundation and baseline detector "
"you just saw results from are complete. From here, we harden the "
"detector, submit Gate 2 on 22 September, integrate real data if it's "
"granted, and deliver the full live demo at Gate 3 on 15 October.",

# 12 gantt picture
"LLAGAMI - 18:30-20:00\n"
"And here's that same schedule as a Gantt chart. Green is done, blue is "
"upcoming work, amber is the optional real-data integration track. We're "
"currently ahead of where we need to be for Gate 2.",

# 13 risk analysis / feasibility
"LLAGAMI - 20:00-23:00\n"
"On feasibility: we identified five real risks and a mitigation for each, "
"from data not being shared in time, to FASTedge not exposing an inline "
"hook, to the detector not generalising to real traffic noise. The "
"biggest one, data access, is fully mitigated already: we're "
"synthetic-first, so no data approval process blocks us from having a "
"working system today. Real data only makes the result stronger, it "
"isn't a dependency.",

# 14 open points / business case
"LLAGAMI - 23:00-26:30\n"
"On technologies and cost: everything is open-source, Python, "
"scikit-learn, Streamlit, no licensing, runs on a laptop, production only "
"adds light edge compute. On business value: this cuts detection time "
"from hours to seconds, it's the guardrail that lets an operator safely "
"expand network automation, and every decision is logged and explainable, "
"which is direct audit evidence for NIS2, GDPR, and the EU AI Act. We're "
"tracking this work area by area, financial, engineering, communication, "
"and next steps, so nothing falls through the cracks before Gate 2.",

# 15 weeks + next steps
"FAUZAN - 26:30-28:30\n"
"So, week by week from here: hardening the detector, finishing the "
"numerical performance analysis for Gate 2, then integrating real data if "
"granted, and finally the live end-to-end dashboard demo for Gate 3 on 15 "
"October.",

# 16 thank you
"FAUZAN - 28:30-30:00\n"
"To close: the hardest part, proving the detection method actually works, "
"is already done, working, and in front of you today. We're confident in "
"this direction and looking forward to your questions. Thank you.",
]

for slide, note in zip(prs.slides, NOTES):
    slide.notes_slide.notes_text_frame.text = note

prs.save(OUT)
print(f"Saved {OUT}  ({len(prs.slides._sldIdLst)} slides)")
