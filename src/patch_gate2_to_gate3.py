# -*- coding: utf-8 -*-
"""Builds AEGIS_Gate3_Official.pptx by patching the full, hand-tweaked
AEGIS_Gate2_Official.pptx (24 slides: cover, index, intro metaphor, Gap/SoA,
architecture, scoring, tools/phases, bug-fix narrative, benchmarking, SPC
head-to-head, per-threat chart, ROC, live-demo video, PoC readiness, Open5GS
plan, path-to-Gate-3, thank-you/links, 5 statistical appendix slides) rather
than regenerating from the base script template - so nothing from earlier
tutor feedback rounds (SPC baseline comparison, the bootstrap/CV/temporal/
drift/evasion appendix, the badge-metaphor intro, the embedded demo video,
the GitHub/dashboard links) gets silently dropped.

Only the items from the latest tutor rehearsal feedback are applied:
  - Relabel every "Gate 2" / "GATE 2" occurrence to Gate 3.
  - Slide 8 (Scoring: Rules + ML, Fused) trimmed to one-liners per card.
  - Slide 9 (Tools, Platforms & Build Phases) replaced with two Isolation
    Forest deep-dive slides (concept diagram, then features/calibration).
  - Slide 10 (What The Evaluation Loop Found & Fixed) deleted.
  - Slide 13's chart swapped for the regenerated, legible aegis_eval.png.
  - Slide 16/17 (PoC readiness + Open5GS plan) updated with the real Gate-3
    Open5GS core validation results, in place of the Gate-2 forward-looking
    plan language.
  - Slide 18 (Path to Gate 3) reframed as remaining work, since this deck
    IS Gate 3 now; AWS is intentionally not mentioned anywhere.
  - A general, conservative font-size bump on small body text for
    readability, skipping kickers, titles, and large stat numbers.

Run:  .venv/Scripts/python AEGIS/src/patch_gate2_to_gate3.py
In :  AEGIS/slides/GATE-3/AEGIS_Gate2_Official.pptx  (pasted-in source)
Out:  AEGIS/slides/GATE-3/AEGIS_Gate3_Official.pptx
"""

import copy
import os
from pptx import Presentation
from pptx.util import Pt, Inches, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

NAVY = RGBColor(0x02, 0x0C, 0x31)
ACCENT = RGBColor(0x01, 0xAB, 0xDB)
ACCENT2 = RGBColor(0x3D, 0x67, 0xB1)
BODY_C = RGBColor(0x33, 0x41, 0x55)
MUTE_C = RGBColor(0x6B, 0x76, 0x88)
CARD_C = RGBColor(0xFF, 0xFF, 0xFF)
HAIR_C = RGBColor(0xE2, 0xE8, 0xF0)
GREEN_C = RGBColor(0x0E, 0x93, 0x84)
FONT = "Montserrat"

HERE = os.path.dirname(os.path.abspath(__file__))
SLIDES_DIR = os.path.join(HERE, "..", "slides", "GATE-3")
SRC = os.path.join(SLIDES_DIR, "AEGIS_Gate2_Official.pptx")
OUT = os.path.join(SLIDES_DIR, "AEGIS_Gate3_Official.pptx")
IFOREST_PNG = os.path.join(HERE, "..", "reports", "aegis_isolation_forest_concept.png")
EVAL_PNG = os.path.join(HERE, "..", "reports", "aegis_eval.png")
ARCH_PNG = os.path.join(HERE, "..", "reports", "GATE-3", "aegis_architecture_diagram_horizontal.png")
OPEN5GS_PNG = os.path.join(HERE, "..", "reports", "GATE-3", "storyboard-shots", "open5gs_terminal.png")


# ------------------------------------------------------------------ helpers
def find_shape_by_text(slide, snippet):
    for shp in slide.shapes:
        if shp.has_text_frame and snippet in shp.text_frame.text:
            return shp
    return None


def set_simple_text(shape, new_text):
    tf = shape.text_frame
    p0 = tf.paragraphs[0]
    if not p0.runs:
        p0.add_run()
    r0 = p0.runs[0]
    r0.text = new_text
    for r in list(p0.runs[1:]):
        r._r.getparent().remove(r._r)
    for p in list(tf.paragraphs[1:]):
        p._p.getparent().remove(p._p)


def replace_picture(slide, old_pic_shape, image_path):
    left, top, width, height = (old_pic_shape.left, old_pic_shape.top,
                                 old_pic_shape.width, old_pic_shape.height)
    old_pic_shape._element.getparent().remove(old_pic_shape._element)
    return slide.shapes.add_picture(image_path, left, top, width, height)


def get_picture(slide):
    for shp in slide.shapes:
        if shp.shape_type == 13:
            return shp
    return None


def delete_slide(prs, index):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    rId = slides[index].rId
    prs.part.drop_rel(rId)
    xml_slides.remove(slides[index])


def slide_index(prs, slide):
    for i, s in enumerate(prs.slides):
        if s is slide:
            return i
    raise ValueError("slide not found")


def move_slide(prs, old_index, new_index):
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    el = slides[old_index]
    xml_slides.remove(el)
    xml_slides.insert(new_index, el)


def clear_slide(slide):
    for shp in list(slide.shapes):
        shp._element.getparent().remove(shp._element)


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


def kicker(slide, text_):
    txt(slide, 0.83, 0.02, 10.5, 0.3, [[(text_, 11.5, ACCENT, True)]])


def title(slide, text_):
    txt(slide, 0.83, 0.29, 10.5, 1.0, [[(text_, 29, NAVY, True)]])


def lead(slide, text_, y=1.25):
    txt(slide, 0.83, y, 11.6, 0.5, [[(text_, 13, MUTE_C, False)]])


def picture_scaled(slide, path, x, y, max_w, max_h):
    from PIL import Image as PILImage
    im = PILImage.open(path)
    ar = im.size[0] / im.size[1]
    w, h = max_w, max_w / ar
    if h > max_h:
        h = max_h; w = max_h * ar
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    return pic, w, h


def new_slide_like(prs, template_slide):
    return prs.slides.add_slide(template_slide.slide_layout)


# ------------------------------------------------------------------ load
prs = Presentation(SRC)
slides = list(prs.slides)


# ------------------------------------------------------------------ 1. relabel Gate 2 -> Gate 3 everywhere
for slide in prs.slides:
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            for r in para.runs:
                if "GATE 2" in r.text:
                    r.text = r.text.replace("GATE 2", "GATE 3")
                if "Gate 2" in r.text:
                    r.text = r.text.replace("Gate 2", "Gate 3")

print("Relabelled GATE 2 -> GATE 3 throughout.")


# ------------------------------------------------------------------ 2. slide 8: trim Scoring card text + bump fonts
slide8 = next(s for s in prs.slides if find_shape_by_text(s, "Scoring: Rules") is not None)

set_simple_text(find_shape_by_text(slide8, "Fast, explainable. Hard caps"),
                "Fast, explainable. Flags out-of-scope calls immediately.")
set_simple_text(find_shape_by_text(slide8, "An Isolation Forest, trained"),
                "An Isolation Forest, trained only on legitimate traffic - no labelled "
                "attacks needed.")
set_simple_text(find_shape_by_text(slide8, "risk = max"),
                "risk = max(rule_score, ml_score) - rules veto hard violations, ML catches "
                "subtler drift.")
op_point = find_shape_by_text(slide8, "Operating point:")
set_simple_text(op_point,
                "Tuned for a ~1.5% false-positive budget, not maximum sensitivity - detection "
                "is intentionally uneven across threats.")

# bump the card body/legend text sizes a touch for readability
for label in ("Fast, explainable. An out-of-scope", "An Isolation Forest, trained only",
              "risk = max(rule_score", "Behaves like its known-good self",
              "Challenge: re-authenticate", "Quarantine the identity"):
    shp = find_shape_by_text(slide8, label)
    if shp is not None:
        for para in shp.text_frame.paragraphs:
            for r in para.runs:
                if r.font.size and r.font.size.pt < 12:
                    r.font.size = Pt(12)
for label in ("RULES LAYER", "ML LAYER", "FUSION", "PASS", "STEP-UP", "BLOCK"):
    shp = find_shape_by_text(slide8, label)
    if shp is not None and shp.text_frame.text.strip() == label:
        for para in shp.text_frame.paragraphs:
            for r in para.runs:
                r.font.size = Pt(14)
op_point.text_frame.paragraphs[0].runs[0].font.size = Pt(12.5)

print("Trimmed and enlarged slide 8 (Scoring: Rules + ML, Fused).")


# ------------------------------------------------------------------ 2b. slide 6: trim Gap/Solution/SoA cards
slide6 = next(s for s in prs.slides if find_shape_by_text(s, "The Gap, Our Solution") is not None)

set_simple_text(find_shape_by_text(slide6, "A credential check proves you have the right token"),
                "Credentials are checked once, at the door - never again. A stolen or "
                "misused identity passes every time.")
set_simple_text(find_shape_by_text(slide6, "A behavioural fingerprint per agent"),
                "A continuous behavioural fingerprint per agent: rules + an Isolation "
                "Forest, fused, gated PASS / STEP-UP / BLOCK.")
set_simple_text(find_shape_by_text(slide6, "Named, reimplemented, and run"),
                "A Statistical Process Control baseline, run on our own data: 0.944 "
                "ROC-AUC / 63.4% recall. AEGIS: 0.965 / 90.7% - a significant gap (p=0.015).")
oneliner = find_shape_by_text(slide6, "One line: credentials prove")
set_simple_text(oneliner,
                "Credentials prove what you have, AEGIS verifies how you behave - and we "
                "can show it beats the classic baseline.")

for label in ("Credentials are checked once", "A continuous behavioural fingerprint",
              "A Statistical Process Control baseline", "Behaves like its known-good self",
              "Challenge: re-authenticate", "Quarantine the identity"):
    shp = find_shape_by_text(slide6, label)
    if shp is not None:
        for para in shp.text_frame.paragraphs:
            for r in para.runs:
                r.font.size = Pt(12)
oneliner.text_frame.paragraphs[0].runs[0].font.size = Pt(12.5)

print("Trimmed slide 6 (Gap, Our Solution, State of the Art).")


# ------------------------------------------------------------------ 2c. slide 7: horizontal architecture diagram, drop the redundant text column
slide7 = next(s for s in prs.slides if find_shape_by_text(s, "System Architecture") is not None)
old_arch_pic = get_picture(slide7)
notes_col = find_shape_by_text(slide7, "Parse request + metadata")
if old_arch_pic is not None:
    old_arch_pic._element.getparent().remove(old_arch_pic._element)
if notes_col is not None:
    notes_col._element.getparent().remove(notes_col._element)
if os.path.exists(ARCH_PNG):
    _, apw, aph = picture_scaled(slide7, ARCH_PNG, 0.83, 1.95, 11.6, 5.0)
    # recentre horizontally since the diagram's own aspect ratio determines its width
    arch_pic = get_picture(slide7)
    arch_pic.left = Emu(int((13.333 - apw) / 2 * 914400))
print("Replaced slide 7 with the horizontal architecture diagram, dropped the redundant text column.")


# ------------------------------------------------------------------ 3. slide 9: replace with Isolation Forest, part 1 (concept)
slide9 = next(s for s in prs.slides if find_shape_by_text(s, "Tools, Platforms & Build Phases") is not None)
idx9 = slide_index(prs, slide9)
kicker9_text = find_shape_by_text(slide9, "IMPLEMENTATION STRATEGY").text_frame.text
clear_slide(slide9)

kicker(slide9, kicker9_text.replace("PART 3 OF 6", "PART 3 OF 6"))
title(slide9, "How Isolation Forest Works")
lead(slide9, "The model that does the heavy lifting in the ML layer - no labelled attacks, "
             "just a simple idea applied many times over.")
if os.path.exists(IFOREST_PNG):
    _, pw, ph = picture_scaled(slide9, IFOREST_PNG, 0.83, 1.9, 11.6, 3.95)
    next_y = 1.9 + ph + 0.2
else:
    next_y = 2.2
pts = [
    "An Isolation Forest builds many random binary-split trees over the feature "
    "space: at each node, pick a random feature and a random split value.",
    "An anomaly sits apart from the bulk of normal traffic, so a handful of random "
    "splits isolates it (short path length). A normal point is surrounded by "
    "similar points and takes many more splits to isolate on its own.",
    "Anomaly score = how short the average isolation path is across the whole "
    "forest, normalised to roughly 0..1. Short path -> high score -> looks like an attack.",
]
runs = [[("-  ", 13, ACCENT, True), (p, 13, BODY_C, False)] for p in pts]
txt(slide9, 0.83, next_y, 11.6, 1.8, runs, line_spacing=1.25)

print("Replaced slide 9 with 'How Isolation Forest Works'.")


# ------------------------------------------------------------------ 4. new slide: Isolation Forest, part 2 (features/calibration)
slide9b = new_slide_like(prs, slide9)
move_slide(prs, slide_index(prs, slide9b), idx9 + 1)

kicker(slide9b, kicker9_text)
title(slide9b, "Training, Features & Calibration")
lead(slide9b, "Unsupervised by design - the gate has to recognise drift from agents it has "
              "never seen attacked, not just the attacks in our synthetic catalogue.")
txt(slide9b, 0.83, 1.9, 5.55, 0.4, [[("10 INPUT FEATURES PER WINDOW", 13.5, ACCENT2, True)]])
features = [
    "n - request count", "distinct_nf - Network Functions touched",
    "distinct_ep - distinct endpoints", "err_rate - fraction of 4xx/5xx",
    "get_frac / write_frac - method mix", "mean_resp / max_resp - payload size",
    "hour - time of day", "distinct_target_roll - rolling subscriber/record breadth",
]
runs = [[("-  ", 12, ACCENT, True), (f, 12, BODY_C, False)] for f in features]
txt(slide9b, 0.83, 2.35, 5.55, 3.5, runs, line_spacing=1.3)

txt(slide9b, 6.75, 1.9, 5.7, 0.4, [[("WHY IT FITS A ZERO-TRUST GATE", 13.5, ACCENT, True)]])
why = [
    ("No labelled attacks needed", "Fit only on each agent's own legit traffic - an "
     "unlabelled 'normal', which is all a new agent's own history ever gives you."),
    ("Per-agent identity, one-hot", "The model learns each agent's own normal, so "
     "impersonation (T1) shows up as unlike-itself, not unlike-everyone-else."),
    ("300 trees, contamination 0.02", "scikit-learn IsolationForest(n_estimators=300, "
     "contamination=0.02); engages once an agent has 10+ requests in the trailing "
     "5 minutes."),
    ("Calibrated on held-out legit data", "Scores are mapped to 0..1 using a legit "
     "split the model never trained on - in-sample calibration would understate the "
     "tail and blow up the real-world false-positive rate."),
]
wy, wh = 2.35, 0.95
for i, (h, d) in enumerate(why):
    y = wy + i * (wh + 0.08)
    rect(slide9b, 6.75, y, 5.7, wh, fill=CARD_C, line=HAIR_C, radius=0.08)
    rect(slide9b, 6.75, y, 0.07, wh, fill=ACCENT2)
    txt(slide9b, 7.0, y + 0.08, 5.3, 0.3, [[(h, 12, NAVY, True)]])
    txt(slide9b, 7.0, y + 0.37, 5.3, wh - 0.4, [[(d, 10.5, BODY_C, False)]], line_spacing=1.15)

print("Inserted new slide: 'Training, Features & Calibration'.")


# ------------------------------------------------------------------ 5. delete old slide 10 (bug-fix narrative)
slide10 = next(s for s in prs.slides if find_shape_by_text(s, "What The Evaluation Loop Found") is not None)
delete_slide(prs, slide_index(prs, slide10))
print("Deleted the 'What The Evaluation Loop Found & Fixed' slide.")


# ------------------------------------------------------------------ 6. slide 13: swap in the fixed, legible chart
slide13 = next(s for s in prs.slides if find_shape_by_text(s, "Detection Rate Per Threat") is not None
               and find_shape_by_text(s, "Deliberately Not Uniform") is not None)
old_pic = get_picture(slide13)
if old_pic is not None and os.path.exists(EVAL_PNG):
    replace_picture(slide13, old_pic, EVAL_PNG)
    print("Swapped slide 13's chart for the regenerated, legible aegis_eval.png.")


# ------------------------------------------------------------------ 6b. slide 12: trim the SPC head-to-head paragraph
slide12 = next(s for s in prs.slides if find_shape_by_text(s, "State of the Art, Head-to-Head") is not None)
spc_para = find_shape_by_text(slide12, "Statistical Process Control (SPC), the classic")
set_simple_text(spc_para,
                "SPC, the classic control-chart baseline, run on the same split as AEGIS: "
                "strong on loud signals (T4 100%, T1 94%), blind to subtler ones (T2 21%, "
                "T3 27%, T6 51%) - the measured case for behavioural fingerprinting + fusion.")
spc_para.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
print("Trimmed slide 12 (State of the Art, Head-to-Head).")


# ------------------------------------------------------------------ 6c. slide 14: trim the ROC operating-point paragraph
slide14 = next(s for s in prs.slides if find_shape_by_text(s, "ROC Operating-Point Analysis") is not None)
roc_para = find_shape_by_text(slide14, "The chosen threshold (0.60) is Pareto-efficient")
set_simple_text(roc_para,
                "0.60 is Pareto-efficient - no alternative threshold beats it on both "
                "recall and FPR - and sits within 0.2 points of the Neyman-Pearson "
                "frontier. It minimises a stated cost function, not an unlabelled 'optimal'.")
roc_para.text_frame.paragraphs[0].runs[0].font.size = Pt(14)
print("Trimmed slide 14 (ROC Operating-Point Analysis).")


# ------------------------------------------------------------------ 7. slide 16 + 17: real Open5GS results, not a forward plan
slide16 = next(s for s in prs.slides if find_shape_by_text(s, "PoC Readiness at Gate") is not None)
not_yet_label = find_shape_by_text(slide16, "NOT YET")
if not_yet_label is not None:
    set_simple_text(not_yet_label, "DONE")
    # the status pill is the rounded-rect shape sized 1.5in directly behind the label;
    # find it by position match rather than by name (names aren't stable across edits)
    lbl_top = not_yet_label.top
    for shp in slide16.shapes:
        if shp.shape_type == 1 and shp.top == lbl_top and shp.width < Emu(2000000):
            shp.fill.fore_color.rgb = GREEN_C
set_simple_text(find_shape_by_text(slide16, "Real M2M/API-gateway traffic is the natural next"),
                "Confirmed on a real Open5GS 5G SA core: schema matches our synthetic "
                "generator independently, and 2 of 2 real attack-like windows were correctly "
                "flagged BLOCK by AEGIS's own unmodified detection code.")
print("Flipped slide 16's 'Real M2M/API-gateway traffic' row to DONE.")

slide17 = next(s for s in prs.slides if find_shape_by_text(s, "Real M2M / API-gateway traffic") is not None
               and find_shape_by_text(s, "Allows us to generate") is not None)
kicker17_text = find_shape_by_text(slide17, "EXPECTED PROOF OF CONCEPT").text_frame.text
clear_slide(slide17)

kicker(slide17, kicker17_text)
title(slide17, "Beyond Synthetic: A Real 5G Core")
lead(slide17, "Gate 2's roadmap item - validate against real M2M / API-gateway traffic, "
              "not just the synthetic generator. Done for Gate 3.")
if os.path.exists(OPEN5GS_PNG):
    _, opw, oph = picture_scaled(slide17, OPEN5GS_PNG, 0.83, 1.9, 5.7, 4.3)
    right_x = 0.83 + 5.7 + 0.35
else:
    right_x = 0.83
right_w = max(11.6 - (right_x - 0.83), 4.5)
steps = [
    ("Stood up a real core", "A full Open5GS SA deployment (14 NFs) plus a UERANSIM "
     "gNB/UE - a genuine registration and PDU session, not simulated logs."),
    ("Captured real SBI traffic", "tcpdump on the AMF's network namespace, parsed into "
     "the same schema AEGIS's detector already expects."),
    ("Schema matches, confirmed", "Real captured paths (/nudm-sdm/v2/..., "
     "/nsmf-pdusession/v1/sm-contexts) line up with our synthetic generator's naming "
     "convention almost exactly."),
    ("Detection validated on real traffic", "AEGIS's own unmodified detection code: "
     "2 of 2 real attack-like windows correctly flagged BLOCK."),
]
sy, sh_ = 1.9, 1.0
for i, (h, d) in enumerate(steps):
    y = sy + i * (sh_ + 0.1)
    rect(slide17, right_x, y, right_w, sh_, fill=CARD_C, line=HAIR_C, radius=0.07)
    rect(slide17, right_x, y, 0.07, sh_, fill=GREEN_C)
    txt(slide17, right_x + 0.2, y + 0.1, right_w - 0.4, 0.3, [[(h, 13, NAVY, True)]])
    txt(slide17, right_x + 0.2, y + 0.42, right_w - 0.4, sh_ - 0.46, [[(d, 11, BODY_C, False)]],
        line_spacing=1.15)
txt(slide17, 0.83, 6.35, 11.6, 0.6, [[
    ("Honest scope: a short, single-agent capture - rules-dominant, not a replacement "
     "for the full synthetic evaluation's statistical rigor.", 11.5, MUTE_C, False)]],
    line_spacing=1.2)
print("Replaced slide 17 with 'Beyond Synthetic: A Real 5G Core' results.")


# ------------------------------------------------------------------ 8. slide 18: reframe "Path to Gate 3" as remaining work
slide18 = next(s for s in prs.slides if find_shape_by_text(s, "What's Next") is not None)
set_simple_text(find_shape_by_text(slide18, "PATH TO GATE 3"), "PART 6 OF 6 - REMAINING WORK")
set_simple_text(find_shape_by_text(slide18, "What's Next"), "Remaining Work Before Final Submission")

remaining = [
    "Record and edit the final video demonstration from the live demo script - "
    "storyboard and supporting animations are already built.",
    "Keep stress-testing generalisation: further agent and attack-variant coverage "
    "beyond the current 7-agent / 10-variant catalogue.",
    "Continue hardening the two remaining softer spots, T2 compromise and T6 "
    "sequence, with the same rolling-signal approach already used for T3 and T5.",
]
# reuse the existing 4 item boxes' shapes/positions; remove the 4th (now unused)
item_shapes = []
for shp in slide18.shapes:
    if shp.has_text_frame and shp.text_frame.text.strip().startswith(
            ("Close the gap", "Integrate real M2M", "Extend the pipeline",
             "Record the final video", "Expand the number")):
        item_shapes.append(shp)
# these text boxes sit inside PANEL_C rounded-rect rows; find the rows by top position
rows = sorted({shp.top for shp in item_shapes})
texts_by_row = {}
for shp in item_shapes:
    texts_by_row.setdefault(shp.top, shp)
for i, row_top in enumerate(rows):
    shp = texts_by_row[row_top]
    if i < len(remaining):
        set_simple_text(shp, remaining[i])
        for r in shp.text_frame.paragraphs[0].runs:
            r.font.size = Pt(13)
    else:
        # extra 4th row no longer needed - remove its text + its two backing rects
        row_y = shp.top
        for other in list(slide18.shapes):
            if other.top == row_y:
                other._element.getparent().remove(other._element)
print("Reframed slide 18 as 'Remaining Work Before Final Submission'.")


# ------------------------------------------------------------------ 9. fix pre-existing index-slide issues
# (both present already in the pasted-in Gate-2 source, not introduced by this
# script - fixed here since they're clear oversights, not content changes)
index_slide = prs.slides[1]
team_box = find_shape_by_text(index_slide, "Fauzan")
if team_box is not None and "Adithya" not in team_box.text_frame.text:
    tf = team_box.text_frame
    template_p = tf.paragraphs[1]._p  # "Fauzan Ejaz (Captain)" - bold run formatting to copy
    for name in ("Ghazanfar Anees Siddiqui", "Adithya Zacharia Valavi"):
        p_copy = copy.deepcopy(template_p)
        runs_xml = p_copy.findall(".//{*}r")
        for extra in runs_xml[1:]:
            extra.getparent().remove(extra)
        runs_xml[0].find("{*}t").text = name
        template_p.addnext(p_copy)
    print("Restored the two missing team members on the index slide's team box.")

topic6 = find_shape_by_text(index_slide, "Path to Gate 3")
if topic6 is not None and topic6.text_frame.text.strip() == "Path to Gate 3":
    set_simple_text(topic6, "Remaining Work")
    print("Updated index topic 06 label to match the renamed closing section.")


# ------------------------------------------------------------------ 10. deck-wide, conservative font-size bump
# Applied last so it also catches slides not touched above. Deliberately
# small steps (never more than +1.5pt) to avoid overflowing the many
# fixed-size card layouts across the deck, since there's no renderer in
# this environment to visually confirm nothing clips.
bumped = 0
for slide in prs.slides:
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        for para in shape.text_frame.paragraphs:
            for r in para.runs:
                if r.font.size is None:
                    continue
                pt = r.font.size.pt
                if pt < 10:
                    new = 11.0
                elif pt < 11:
                    new = 12.0
                elif pt < 12.5:
                    new = pt + 1.0
                elif pt < 14:
                    new = pt + 0.5
                else:
                    continue
                if new > pt:
                    r.font.size = Pt(new)
                    bumped += 1
print(f"Bumped font size on {bumped} text runs deck-wide for readability.")


# ------------------------------------------------------------------ save
os.makedirs(SLIDES_DIR, exist_ok=True)
prs.save(OUT)
print(f"Saved {OUT}  ({len(prs.slides._sldIdLst)} slides)")
