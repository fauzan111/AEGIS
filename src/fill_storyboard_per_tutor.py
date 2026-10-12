# -*- coding: utf-8 -*-
"""Fills in the Gate 3 storyboard draft per the tutor's (Vincenzo Merola)
review comments on `storyboard_draft_team_4 1.pptx`: write the actual
voice-over line for every scene, fill the blank scenes, fix the slide 2
opening (presenters first, not a static image), make the Observe/
Fingerprint/Score/Decide panels real diagrams instead of open questions,
swap out the two mismatched/generic stock images for project-specific
assets we already have, build out the empty results/close slide, and add
each team member's status.

Voice-over wording is pulled from the already-written, already-reviewed
`docs/GATE-3/Gate3_Video_Script.md` wherever it covers the same beat -
this script does not invent new claims, it distributes existing wording
across more, smaller shots than the original 7-segment script, and fills
the gaps (intro bridge lines, shot descriptions) in the same voice.

Run:  .venv/Scripts/python AEGIS/src/fill_storyboard_per_tutor.py
In/Out: AEGIS/slides/GATE-3/storyboard_draft_team_4 1.pptx  (edited in place)
"""

import copy
import io
import os
from pptx import Presentation
from pptx.util import Emu

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "..", "slides", "GATE-3", "storyboard_draft_team_4 1.pptx")
REPORTS = os.path.join(HERE, "..", "reports")

IFOREST_PNG = os.path.join(REPORTS, "aegis_isolation_forest_concept.png")
OPEN5GS_TERMINAL = os.path.join(REPORTS, "GATE-3", "storyboard-shots", "open5gs_terminal.png")
DASH_INCIDENT = os.path.join(REPORTS, "GATE-3", "storyboard-shots", "dash_incident_inspector.png")
DASH_TOPOLOGY = os.path.join(REPORTS, "GATE-3", "storyboard-shots", "dash_topology.png")
OBSERVE_ICON = os.path.join(HERE, "..", "slides", "GATE-3", "_sb_assets", "observe_icon.png")
FINGERPRINT_ICON = os.path.join(HERE, "..", "slides", "GATE-3", "_sb_assets", "fingerprint_icon.png")
SCORE_ICON = os.path.join(HERE, "..", "slides", "GATE-3", "_sb_assets", "score_icon.png")
DECIDE_ICON = os.path.join(HERE, "..", "slides", "GATE-3", "_sb_assets", "decide_icon.png")


# ------------------------------------------------------------------ helpers
def by_pos(slide, x, y, tol=0.3):
    """Find the real caption/field box near (x, y) in inches. Several
    near-zero-height decorative FREEFORM strips live at nearly the same
    coordinates as the actual caption boxes in this template, so distance
    alone picks the wrong shape - among everything within tolerance, pick
    the TALLEST (captions run 0.3-1.1in tall, decoration strips run 0-0.33in)."""
    candidates = []
    for shp in slide.shapes:
        if not shp.has_text_frame:
            continue
        sx, sy = Emu(shp.left).inches, Emu(shp.top).inches
        if abs(sx - x) <= tol and abs(sy - y) <= tol:
            candidates.append(shp)
    if not candidates:
        raise ValueError(f"no shape near ({x},{y})")
    return max(candidates, key=lambda s: Emu(s.height).inches)


def set_caption(shape, text):
    """Replaces a single-paragraph caption shape's text, keeping its run
    formatting (font/size/color inherited from the template)."""
    tf = shape.text_frame
    p0 = tf.paragraphs[0]
    if not p0.runs:
        p0.add_run()
    p0.runs[0].text = text
    for r in list(p0.runs[1:]):
        r._r.getparent().remove(r._r)
    for p in list(tf.paragraphs[1:]):
        p._p.getparent().remove(p._p)


def append_line(shape, text, size_pt=None, italic=None):
    """Appends a new paragraph (a real line break, not an embedded \\n) to
    a caption shape, cloning the first paragraph's formatting as a base."""
    tf = shape.text_frame
    template_p = tf.paragraphs[0]._p
    parent = template_p.getparent()
    p_copy = copy.deepcopy(template_p)
    runs_xml = p_copy.findall(".//{*}r")
    for extra in runs_xml[1:]:
        extra.getparent().remove(extra)
    runs_xml[0].find("{*}t").text = text
    parent.append(p_copy)
    # re-wrap to set size/italic via python-pptx on the new last paragraph
    new_p = tf.paragraphs[-1]
    if new_p.runs:
        if size_pt is not None:
            from pptx.util import Pt
            new_p.runs[0].font.size = Pt(size_pt)
        if italic is not None:
            new_p.runs[0].font.italic = italic


def by_label(slide, x, y, label, tol=0.3):
    """Finds the specific 'Scene No.' / 'Shot No.' field box near (x, y).
    There's a same-position, same-height decorative overlay strip (width
    ~3.49in) sitting exactly behind the real field (width ~0.7-1.0in) in
    this template - match on width too, not just position/text, or a
    stale run (this field already reads 'Scene No. 3' instead of the
    pristine 'Scene No.') can resolve to the wrong one of the two."""
    candidates = []
    for shp in slide.shapes:
        if not shp.has_text_frame:
            continue
        if not shp.text_frame.text.strip().startswith(label):
            continue
        sx, sy = Emu(shp.left).inches, Emu(shp.top).inches
        w = Emu(shp.width).inches
        if abs(sx - x) <= tol and abs(sy - y) <= tol and w <= 1.2:
            candidates.append(shp)
    if not candidates:
        raise ValueError(f"no {label!r} field near ({x},{y})")
    return min(candidates, key=lambda s: Emu(s.width).inches)


def set_scene_shot(slide, x, y, scene_no, shot_no=1):
    scene_shp = by_label(slide, x, y, "Scene No.")
    shot_x = Emu(scene_shp.left).inches + 1.74
    shot_shp = by_label(slide, shot_x, y, "Shot No.")
    set_caption(scene_shp, f"Scene No. {scene_no}")
    set_caption(shot_shp, f"Shot No. {shot_no}")


def pic_by_pos(slide, x, y, tol=0.3):
    """Finds the PICTURE shape near (x, y) - by_pos only matches shapes
    with a text frame, which a picture never has."""
    for shp in slide.shapes:
        if shp.shape_type != 13:
            continue
        sx, sy = Emu(shp.left).inches, Emu(shp.top).inches
        if abs(sx - x) <= tol and abs(sy - y) <= tol:
            return shp
    raise ValueError(f"no picture near ({x},{y})")


def clone_shape(template_shape, dest_slide, x, y):
    """Deep-copies a shape's XML into another slide and repositions it -
    used for slide 6, which (unlike slides 2-5) has no caption boxes or
    picture placeholders at all, not even blank ones. Cloning an existing,
    correctly-styled shape keeps the new content visually consistent with
    the rest of the deck instead of adding a plain default text box."""
    new_el = copy.deepcopy(template_shape._element)
    dest_slide.shapes._spTree.append(new_el)
    new_shape = dest_slide.shapes[-1]
    new_shape.left = Emu(int(x * 914400))
    new_shape.top = Emu(int(y * 914400))
    return new_shape


def clone_picture(template_pic, dest_slide, x, y):
    """Copies a picture's actual image bytes into another slide via
    add_picture, rather than deep-copying its XML - a raw XML copy carries
    an r:embed relationship ID that's only valid in the SOURCE slide's own
    .rels file, and silently produces a broken/unopenable image reference
    on any other slide."""
    img = template_pic.image
    pic = dest_slide.shapes.add_picture(
        io.BytesIO(img.blob), Emu(int(x * 914400)), Emu(int(y * 914400)),
        template_pic.width, template_pic.height)
    return pic


def replace_picture(slide, shape, image_path):
    left, top, width, height = shape.left, shape.top, shape.width, shape.height
    shape._element.getparent().remove(shape._element)
    return slide.shapes.add_picture(image_path, left, top, width, height)


prs = Presentation(DECK)
slides = list(prs.slides)
s2, s3, s4, s5, s6, s7 = slides[1], slides[2], slides[3], slides[4], slides[5], slides[6]

# column x-positions and row y-positions used throughout this template
COL = [0.26, 4.08, 7.91]
ROW = [0.76, 4.30]
CAP_ROW1, CAP_ROW2 = 3.1, 6.8  # caption boxes sit ~2.3in below each image row

print("Loaded", DECK)

# ================================================================== SLIDE 2
# Introduction - Segments 1-2 of Gate3_Video_Script.md.
# Tutor: don't open on a static image - open on the presenters. Fill the
# blank 6th panel. Write the voice-over for every panel.

set_scene_shot(s2, COL[0], ROW[0], 1)
cap = by_pos(s2, COL[0], CAP_ROW1)
set_caption(cap, "Both presenters on camera, lab/office set - cold open. "
                 "(Swap out the watermarked 'OpenArt' stock photo currently placed here - "
                 "it can't go in the final submission. Start on us talking, not an image.)")
append_line(cap, "FAUZAN: A stolen ID badge still opens the door. The lock doesn't know it's not you.")
append_line(cap, "LLAGAMI: Now picture that badge isn't a person. It's an AI agent, or an "
                  "automated script, calling into a live 5G core. Same problem. Bigger blast radius.")

set_scene_shot(s2, COL[1], ROW[0], 2)
cap = by_pos(s2, COL[1], CAP_ROW1)
set_caption(cap, "5G Core Network diagram (AMF / SMF / UDM / UPF / PCF / NRF), held on screen "
                 "while Fauzan keeps talking")
append_line(cap, "FAUZAN: We're Fauzan and Llagami. This is AEGIS. A 5G core isn't one system - "
                  "it's a mesh of network functions, AMF, UDM, SMF, PCF, talking to each other "
                  "constantly over an API layer called the Service-Based Interface.")

set_scene_shot(s2, COL[2], ROW[0], 3)
cap = by_pos(s2, COL[2], CAP_ROW1)
set_caption(cap, "AI agents (orchestration, traffic, security, service) calling into the same core")
append_line(cap, "And increasingly, it's not just humans and devices calling into that mesh. It's "
                  "automation - orchestration agents, provisioning scripts, AI-driven operations "
                  "tools, all with real credentials and real access.")

set_scene_shot(s2, COL[0], ROW[1], 4)
cap = by_pos(s2, COL[0], CAP_ROW2)
set_caption(cap, "A compromised AI agent using a valid credential to get in - still needs a shot "
                 "(simple graphic or a short dramatised clip, not sourced yet)")
append_line(cap, "The problem is: a credential check only proves you have the key. It says "
                  "nothing about whether you're using it the way you're supposed to.")

set_scene_shot(s2, COL[1], ROW[1], 5)
cap = by_pos(s2, COL[1], CAP_ROW2)
set_caption(cap, "AEGIS logo and tagline card")
append_line(cap, "That's what AEGIS does. It's a zero-trust behavioural layer that sits on top "
                  "of the credential check.")

set_scene_shot(s2, COL[2], ROW[1], 6)
cap = by_pos(s2, COL[2], CAP_ROW2)
set_caption(cap, "Was blank - filled per tutor note. Simple on-screen text: 'Is this token "
                 "valid?' crossed out, replaced by 'Does this agent still behave like itself?'")
append_line(cap, "It doesn't ask 'is this token valid.' It asks 'does this agent's behaviour "
                  "still look like itself.'")

print("Slide 2 done.")

# ================================================================== SLIDE 3
# Project Vision - Segment 3 of the script (the pipeline). Tutor asked:
# is the 4-step graphic a scrolling image, and are Observe/Fingerprint/
# Score/Decide meant to be separate diagrams. Answer: no, the overview is
# one static strip (already built); yes, each stage gets its own icon,
# reused from the official Gate 3 deck rather than made from scratch.

set_scene_shot(s3, COL[0], ROW[0], 7)
cap = by_pos(s3, COL[0], CAP_ROW1)
set_caption(cap, "The group discussing the project in the Academy")
append_line(cap, "LLAGAMI, on camera: AEGIS runs every call through four stages.")

set_scene_shot(s3, COL[1], ROW[0], 8)
cap = by_pos(s3, COL[1], CAP_ROW1 - 0.1)
set_caption(cap, "Schematic showing the 4-step process of AEGIS (Observe -> Fingerprint -> "
                 "Score -> Decide). Answering the tutor's question: this is ONE static strip "
                 "graphic, already built - hold it on screen for the whole line, not a scroll.")
append_line(cap, "OBSERVE logs every request an agent makes, and every call pattern behind it. "
                  "FINGERPRINT turns that into a behavioural signature, unique per agent. SCORE "
                  "compares that signature against what's normal, using two layers together: "
                  "deterministic rules, and an Isolation Forest model trained only on legitimate "
                  "traffic. DECIDE turns the combined score into one of three outcomes: pass it "
                  "through, step up and verify, or block it outright.")

set_scene_shot(s3, COL[2], ROW[0], 9)
cap = by_pos(s3, COL[2], CAP_ROW1)
set_caption(cap, "Observe: its own icon, reused from the official deck (slides/GATE-3/_sb_assets/"
                 "observe_icon.png) - a real diagram, not an open question")
append_line(cap, "We built this against seven distinct threat patterns - identity spoofing, "
                  "reconnaissance, slow data exfiltration, an agent quietly drifting outside its "
                  "authorised scope.")

set_scene_shot(s3, COL[0], ROW[1], 10)
cap = by_pos(s3, COL[0], CAP_ROW2)
set_caption(cap, "Fingerprint: its own icon (slides/GATE-3/_sb_assets/fingerprint_icon.png)")
append_line(cap, "And this gate, we checked it against a real published framework. Five of our "
                  "seven threats map directly onto named attacker techniques in MITRE FiGHT, the "
                  "ATT&CK equivalent for 5G.")

set_scene_shot(s3, COL[1], ROW[1], 11)
cap = by_pos(s3, COL[1], CAP_ROW2)
set_caption(cap, "Score: its own icon (slides/GATE-3/_sb_assets/score_icon.png)")
append_line(cap, "The other two, we're upfront about it: they're behavioural patterns we catch "
                  "that neither FiGHT nor GSMA's own threat catalogue currently names.")

set_scene_shot(s3, COL[2], ROW[1], 12)
cap = by_pos(s3, COL[2], CAP_ROW2)
set_caption(cap, "Decide: its own icon (slides/GATE-3/_sb_assets/decide_icon.png), then cut to "
                 "the docs/GATE-3/threat-model-external-mapping.md table on screen")

print("Slide 3 done.")

# ================================================================== SLIDE 4
# Project Realization - rest of Segment 3 (ML layer) + Segment 5 opener
# (Open5GS). Tutor: too much detail on screen, generic ML image, unclear
# who's talking in the terminal shot and whether it's two shots.

set_scene_shot(s4, COL[0], ROW[0], 13)
pic = pic_by_pos(s4, COL[0], 1.09)
# generic "brain full of gears" stock image -> the project's own Isolation
# Forest diagram, answering the tutor's note directly
pic = replace_picture(s4, pic, IFOREST_PNG)
cap = by_pos(s4, COL[0], CAP_ROW1)
set_caption(cap, "Isolation Forest concept diagram (reports/aegis_isolation_forest_concept.png) "
                 "- our own, not generic ML clip-art. Kept simple: just the 'anomalies get "
                 "isolated faster' idea, not the full features/calibration slide.")
append_line(cap, "An Isolation Forest, trained only on legitimate traffic. Anomalies sit apart "
                  "from the crowd, so a handful of random splits isolates them fast - no "
                  "labelled attacks needed.")

set_scene_shot(s4, COL[1], ROW[0], 14)
cap = by_pos(s4, COL[1], CAP_ROW1)
set_caption(cap, "One of the team members explaining the algorithm, on camera - this is the "
                 "'who' and 'what they say' the tutor asked about")
append_line(cap, "Rules catch the obvious, out-of-scope calls instantly. The Isolation Forest "
                  "catches the subtler drift. We fuse both into one risk score.")

set_scene_shot(s4, COL[2], ROW[0], 15)
pic = pic_by_pos(s4, COL[2], 1.12)
# the old image was Open5GCore (a different, unrelated open-source project)
# mislabelled as Open5GS - swap for our own real Open5GS terminal capture
pic = replace_picture(s4, pic, OPEN5GS_TERMINAL)
cap = by_pos(s4, COL[2], CAP_ROW1)
set_caption(cap, "Real Open5GS terminal capture (reports/GATE-3/storyboard-shots/"
                 "open5gs_terminal.png) - the old image here was actually Open5GCore, a "
                 "different project, wrong diagram for what we built")
append_line(cap, "For Gate 3 we wanted to know: does this actually hold up against a real 5G "
                  "core, not just our own simulation.")

set_scene_shot(s4, COL[0], ROW[1], 16)
cap = by_pos(s4, COL[0], CAP_ROW2)
set_caption(cap, "Same terminal, close-up: the actual Open5GS/UERANSIM containers coming up. "
                 "Confirms the tutor's question - yes, two separate shots: one of a team member "
                 "talking (scene 14), one of the terminal content itself (this one).")
append_line(cap, "So we stood up a real Open5GS 5G core, brought up a real UE with UERANSIM, "
                  "and captured the actual signalling traffic.")

set_scene_shot(s4, COL[1], ROW[1], 17)
cap = by_pos(s4, COL[1], CAP_ROW2)
set_caption(cap, "Was blank - filled per tutor note. Side-by-side: our synthetic generator's "
                 "endpoint names next to the real captured SBI paths")
append_line(cap, "First thing we checked: does our synthetic data even look like the real thing. "
                  "It does, almost exactly - the endpoint names and call patterns our generator "
                  "produces match real captured 3GPP service calls.")

set_scene_shot(s4, COL[2], ROW[1], 18)
cap = by_pos(s4, COL[2], CAP_ROW2)
set_caption(cap, "Was blank - filled per tutor note. Simple stat card: '2 / 2 real attack "
                 "windows correctly blocked'")
append_line(cap, "Then we went further. We ran real attack-like traffic, not simulated, "
                  "straight into AEGIS's actual detection code, completely unmodified. Two out "
                  "of two real attack windows were correctly flagged and blocked. That's a "
                  "small-scale result, we're honest about that - but it's proof the detection "
                  "logic works on traffic that never touched our synthetic generator.")

print("Slide 4 done.")

# ================================================================== SLIDE 5
# Dashboard Presentation - Segment 4 (live demo). Tutor: write the actual
# voice-over for what's said while the dashboard is shown. The "end
# screen" panel here is premature (results/close haven't happened yet) -
# repurposed as a bridge into slide 6 instead.

set_scene_shot(s5, COL[0], ROW[0], 19)
cap = by_pos(s5, COL[0], CAP_ROW1)
set_caption(cap, "Dashboard home screenshot (reports/GATE-3/storyboard-shots/dash_home.png)")
append_line(cap, "FAUZAN: Let's show you, live. This is the AEGIS dashboard. We pick an attack "
                  "scenario here, credential replay, and launch it.")

set_scene_shot(s5, COL[1], ROW[0], 20)
cap = by_pos(s5, COL[1], CAP_ROW1)
set_caption(cap, "Live attack injection screenshot (reports/GATE-3/storyboard-shots/"
                 "dash_live_attack.png) - pause for the risk score to visibly climb")
append_line(cap, "LLAGAMI: This isn't a replay of pre-recorded data. It's the real detection "
                  "pipeline scoring live traffic as it happens. Watch the risk score. And there "
                  "it is - same attack that would pass a credential-only check gets flagged and "
                  "blocked here, because the behaviour doesn't match the agent's history.")

pic = pic_by_pos(s5, COL[2], 1.07)
# this panel's AEGIS logo card belongs at the very end of the video, not
# here mid-demo - swap for the incident inspector, which is what the
# voice-over for this beat actually needs on screen
pic = replace_picture(s5, pic, DASH_INCIDENT)
set_scene_shot(s5, COL[2], ROW[0], 21)
cap = by_pos(s5, COL[2], CAP_ROW1)
set_caption(cap, "Incident inspector screenshot (reports/GATE-3/storyboard-shots/"
                 "dash_incident_inspector.png) - swapped out the AEGIS logo card that was here, "
                 "it belongs at the very end of the video (slide 6), not mid-demo")
append_line(cap, "FAUZAN: Every decision comes with a plain-language explanation. Not a black "
                  "box. You can see exactly which rule or which score pushed this over the line.")

set_scene_shot(s5, COL[0], ROW[1], 22)
cap = by_pos(s5, COL[0], CAP_ROW2)
set_caption(cap, "Was blank - filled per tutor note. Network topology screenshot "
                 "(reports/GATE-3/storyboard-shots/dash_topology.png)")
append_line(cap, "And this view shows the whole picture at once. Every agent, its authorised "
                  "scope, and the one that just stepped outside it.")

set_scene_shot(s5, COL[1], ROW[1], 23)
cap = by_pos(s5, COL[1], CAP_ROW2)
set_caption(cap, "Was blank - optional B-roll if time allows: both presenters reacting to the "
                 "live result on a second monitor, wide two-shot")

set_scene_shot(s5, COL[2], ROW[1], 24)
cap = by_pos(s5, COL[2], CAP_ROW2)
set_caption(cap, "Was blank - bridge text card: 'But does this hold up against a REAL 5G core?' "
                 "- carries into slide 6's real-core validation and results")

print("Slide 5 done.")

# ================================================================== SLIDE 6
# Was completely empty - no caption boxes, no picture placeholders, just
# the Scene/Shot number scaffolding (confirmed by inspection). Tutor's
# biggest note: "everything else is missing - schematics, voiceovers (and
# which scene they're told in), some results at the end." Built out using
# his proposed ordering for this back half of the video: Segment 6
# (results) and Segment 7 (close) of the script, plus an honest "still
# synthetic-trained" caveat he didn't ask for by name but that the
# existing script already carries (Segment 5's closing line).

caption_template = by_pos(s2, COL[2], CAP_ROW1)  # a plain single-run caption, reused as a style template
logo_template = pic_by_pos(s2, COL[1], 4.66)       # the AEGIS logo card, reused for the closing shot

def new_caption(x, y, text):
    shp = clone_shape(caption_template, s6, x, y)
    set_caption(shp, text)
    return shp

set_scene_shot(s6, COL[0], ROW[0], 25)
cap = new_caption(COL[0], CAP_ROW1, "Stats graphic to build: ROC-AUC 0.979, recall 91.6%, "
                  "false-positive rate 1.44%")
append_line(cap, "FAUZAN, on camera: For Gate 3 we also widened the catalogue, from five agents "
                  "and seven threats to seven agents and ten threat variants, including two "
                  "deliberately extreme agent profiles. Across all of that, AEGIS holds at 0.979 "
                  "ROC-AUC, 91.6 percent recall, and a 1.44 percent false positive rate, inside "
                  "our own 1.5 percent budget.")

set_scene_shot(s6, COL[1], ROW[0], 26)
cap = new_caption(COL[1], CAP_ROW1, "Before/after bars to build: reconnaissance 80 -> 95%, "
                  "exfiltration 76 -> 80%")
append_line(cap, "We also hardened the two weakest spots we found earlier. Reconnaissance "
                  "detection went from 80 to 95 percent. Exfiltration went from 76 to 80. Both "
                  "bootstrap-validated, not a lucky run.")

set_scene_shot(s6, COL[2], ROW[0], 27)
cap = new_caption(COL[2], CAP_ROW1, "Baseline comparison graphic (the one already in the main "
                  "deck's 'State of the Art, Head-to-Head' slide) - NEEDS A TEAM DECISION: the "
                  "exact numbers on that chart changed recently when the catalogue was widened, "
                  "so confirm which version/numbers this scene should show before the shoot")
append_line(cap, "And when we benchmarked against a real published baseline - a statistical "
                  "process control detector, the same kind used in industrial monitoring - AEGIS "
                  "caught noticeably more attacks than that baseline, at the same false-positive "
                  "budget.")

set_scene_shot(s6, COL[0], ROW[1], 28)
cap = new_caption(COL[0], CAP_ROW2, "Simple on-screen text: 'Still synthetic-trained'")
append_line(cap, "LLAGAMI: Worth saying plainly - the detector is still trained only on synthetic "
                  "data. The real-core test validates that the same code works on real "
                  "signalling, it doesn't replace the full synthetic evaluation's statistical "
                  "rigor.")

set_scene_shot(s6, COL[1], ROW[1], 29)
cap = new_caption(COL[1], CAP_ROW2, "Both presenters on camera - the close")
append_line(cap, "LLAGAMI: A credential proves what you have.")
append_line(cap, "FAUZAN: AEGIS verifies how you behave.")
append_line(cap, "Both: Thanks for watching.")

set_scene_shot(s6, COL[2], ROW[1], 30)
clone_picture(logo_template, s6, COL[2], 4.59)
cap = new_caption(COL[2], CAP_ROW2, "AEGIS logo + tagline card, hold 2 seconds")

print("Slide 6 done.")

# ================================================================== SLIDE 7
# Meet the team - tutor: "please write your student status". Using the
# same "Postgraduate Course" framing the official deck's own cover slide
# already uses for the 5G Academy programme - confirm/adjust the exact
# wording with the team if this isn't quite right.

for name, shape_id in [("Fauzan Ejaz", 29), ("Tedi Llagami", 27)]:
    shp = next(s for s in s7.shapes if s.shape_id == shape_id)
    append_line(shp, "Postgraduate Student, 5G Academy 2025/26", size_pt=14, italic=True)

print("Slide 7 done.")

prs.save(DECK)
print("Saved all slides.")
