# -*- coding: utf-8 -*-
"""Rewords the "Gate 3 Results: What Actually Changed" slide to drop the
Gate 2 -> Gate 3 delta framing, per the user's explicit choice: keep the
slide, but present only the current numbers and the "what shapes them"
bullets, with no gate-to-gate comparison language.

Run:  .venv/Scripts/python AEGIS/src/reword_gate3_results_slide.py
In/Out: AEGIS/slides/GATE-3/AEGIS_Gate3_Official.pptx  (edited in place)
"""

import copy
import os
from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "..", "slides", "GATE-3", "AEGIS_Gate3_Official.pptx")


def find_shape_by_text(slide, snippet):
    for shp in slide.shapes:
        if shp.has_text_frame and snippet in shp.text_frame.text:
            return shp
    return None


def find_slide_by_text(prs, snippet):
    for s in prs.slides:
        if find_shape_by_text(s, snippet) is not None:
            return s
    raise ValueError(f"no slide contains {snippet!r}")


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


def set_bullets(shape, bullets):
    tf = shape.text_frame
    template_p = tf.paragraphs[0]._p
    parent = template_p.getparent()
    new_ps = []
    for text in bullets:
        p_copy = copy.deepcopy(template_p)
        runs_xml = p_copy.findall(".//{*}r")
        for extra in runs_xml[2:]:
            extra.getparent().remove(extra)
        prefix_r, body_r = runs_xml[0], runs_xml[1]
        body_r.find("{*}t").text = text
        new_ps.append(p_copy)
    for p in list(tf.paragraphs):
        p._p.getparent().remove(p._p)
    for p in new_ps:
        parent.append(p)


prs = Presentation(DECK)
slide = find_slide_by_text(prs, "Gate 3 Results: What Actually Changed")

set_simple_text(find_shape_by_text(slide, "Gate 3 Results: What Actually Changed"),
                "What Drives Detection Performance")

set_simple_text(
    find_shape_by_text(slide, "Two separate advances, not one"),
    "Four headline numbers from the full 7-agent / 10-variant catalogue, and the "
    "concrete changes behind them - kept separate from the real-core validation on "
    "the previous slide so neither claim overstates the other.")

# four stat cards: value -> single current number, sub-label -> neutral
for value_snippet, new_value in [
    ("0.965  ->  0.979", "0.979"),
    ("90.7%  ->  91.6%", "91.6%"),
    ("1.4%  ->  1.44%", "1.44%"),
    ("0.67  ->  0.64", "0.64"),
]:
    set_simple_text(find_shape_by_text(slide, value_snippet), new_value)

for sub_snippet in ["Gate 2 -> Gate 3 (harder test set)", "Gate 2 -> Gate 3"]:
    while True:
        shp = find_shape_by_text(slide, sub_snippet)
        if shp is None:
            break
        set_simple_text(shp, "current benchmark")

set_simple_text(find_shape_by_text(slide, "WHAT DROVE THE CHANGE"),
                "WHAT SHAPES THESE NUMBERS")

set_bullets(find_shape_by_text(slide, "Catalogue widened"), [
    "Catalogue spans 7 agent types and 10 attack variants, including harder v2 "
    "and slow-ramp forms designed to be tougher to catch, not easier.",
    "T3 recon and T5 exfiltration are hardened with a rolling per-target-ID "
    "cardinality feature - the two statistically subtlest threats in the catalogue.",
    "Precision and false-positive rate sit slightly lower than a narrower "
    "benchmark would show - expected on a harder, more varied test set, and "
    "reported honestly rather than hidden.",
])

set_simple_text(
    find_shape_by_text(slide, "Not from the real Open5GS capture"),
    "Not from the real Open5GS capture: the detector is still trained only on "
    "synthetic data. Real traffic (previous slide) validates that the same code "
    "works on real signalling.")

prs.save(DECK)
print("Saved", DECK)
