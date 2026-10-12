# -*- coding: utf-8 -*-
"""Mentor feedback: slide 5 ("The Seven Threats We Watch For") is too
chopped-up - seven separate boxes in a grid. Replaces it with a single
clean table (ID / Threat / Behavioural signal), which is also how this
same content was always structured in the underlying docs (docs/GATE-2.md's
threat table). Operates on the CURRENT AEGIS_Gate3_Official.pptx in place -
only removes the seven card shapes and the kicker/title/lead box positions
are left exactly as they are now (including whatever manual tweaks have
already been made to them).

Run:  .venv/Scripts/python AEGIS/src/simplify_slide5_threats_table.py
In/Out: AEGIS/slides/GATE-3/AEGIS_Gate3_Official.pptx  (edited in place)
"""

import os
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

NAVY = RGBColor(0x02, 0x0C, 0x31)
RED_C = RGBColor(0xC0, 0x39, 0x4B)
BODY_C = RGBColor(0x33, 0x41, 0x55)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PANEL_C = RGBColor(0xF2, 0xF7, 0xFA)
HAIR_C = RGBColor(0xE2, 0xE8, 0xF0)
FONT = "Montserrat"

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "..", "slides", "GATE-3", "AEGIS_Gate3_Official.pptx")

THREATS = [
    ("T1", "Identity spoofing", "wrong endpoint mix, timing, sequence for that identity"),
    ("T2", "Compromised agent", "drift from its own baseline: new endpoints, elevated errors"),
    ("T3", "Reconnaissance", "high cardinality of endpoints/targets, many 403/404s"),
    ("T4", "Volumetric abuse", "request-rate spike far above the agent's normal envelope"),
    ("T5", "Slow exfiltration", "abnormal payload sizes, off-hours persistence"),
    ("T6", "Sequence anomaly", "broken call-sequence pattern vs the agent's normal graph"),
    ("T7", "Scope creep", "calls to NFs never in the agent's baseline scope"),
]

prs = Presentation(DECK)
slide5 = next(s for s in prs.slides if any(
    sh.has_text_frame and "The Seven Threats We Watch For" in sh.text_frame.text for sh in s.shapes))

# remove every shape that isn't the kicker/title/lead textbox (those three
# are left exactly where they are now, untouched)
keep_texts = ("PART 1 OF 6", "The Seven Threats We Watch For", "Same four-stage pipeline")
for shp in list(slide5.shapes):
    if shp.has_text_frame and any(k in shp.text_frame.text for k in keep_texts):
        continue
    shp._element.getparent().remove(shp._element)

rows, cols = len(THREATS) + 1, 3
x, y, w, h = 0.83, 2.0, 11.6, 5.1
gfx = slide5.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(h))
table = gfx.table
table.columns[0].width = Inches(0.9)
table.columns[1].width = Inches(2.7)
table.columns[2].width = Inches(8.0)

headers = ("#", "Threat", "Behavioural signal AEGIS keys on")
for c, htext in enumerate(headers):
    cell = table.cell(0, c)
    cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.12)
    cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
    p = cell.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = htext
    r.font.size = Pt(13); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = WHITE

for i, (tid, name, signal) in enumerate(THREATS):
    r_idx = i + 1
    row_fill = WHITE if i % 2 == 0 else PANEL_C
    for c, (text, bold, color, align) in enumerate((
        (tid, True, RED_C, PP_ALIGN.LEFT),
        (name, True, NAVY, PP_ALIGN.LEFT),
        (signal, False, BODY_C, PP_ALIGN.LEFT),
    )):
        cell = table.cell(r_idx, c)
        cell.fill.solid(); cell.fill.fore_color.rgb = row_fill
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.12)
        cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
        p = cell.text_frame.paragraphs[0]
        p.alignment = align
        run = p.add_run(); run.text = text
        run.font.size = Pt(13); run.font.bold = bold; run.font.name = FONT
        run.font.color.rgb = color

table.rows[0].height = Inches(0.55)
for i in range(1, rows):
    table.rows[i].height = Inches((5.1 - 0.55) / len(THREATS))

prs.save(DECK)
print(f"Saved {DECK}  ({len(prs.slides._sldIdLst)} slides) - slide 5 replaced with a single table.")
