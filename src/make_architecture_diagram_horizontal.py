# -*- coding: utf-8 -*-
"""Horizontal replacement for reports/aegis_architecture_diagram.png (which
was a tall, vertical flowchart - hard to place well on a 16:9 slide). Same
OBSERVE -> FINGERPRINT -> SCORE -> DECIDE pipeline, laid out left to right
so it reads naturally on a widescreen slide; the per-stage prose already
lives in a text column next to the image on the slide itself, so this stays
diagram-only (no restating of the stage descriptions in the image).

Run:  .venv/Scripts/python AEGIS/src/make_architecture_diagram_horizontal.py
Out:  AEGIS/reports/GATE-3/aegis_architecture_diagram_horizontal.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "reports", "GATE-3")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "aegis_architecture_diagram_horizontal.png")

NAVY = "#020C31"
ACCENT = "#01ABDB"
LIGHT = "#EAF6FB"
GREEN = "#0E9384"
AMBER = "#E0A100"
RED = "#C0394B"
INK = "#1F2A37"

FIG_W, FIG_H = 17.5, 6.6
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W); ax.set_ylim(0, FIG_H)
ax.axis("off")


def box(x, y, w, h, text, fc, ec, tc="white", fs=13, fw="bold"):
    assert x >= 0 and x + w <= FIG_W, f"box out of bounds: {text!r} x={x} w={w}"
    assert y >= 0 and y + h <= FIG_H, f"box out of bounds: {text!r} y={y} h={h}"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                 linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight=fw, color=tc, zorder=4, linespacing=1.3)


def arrow(x0, y0, x1, y1, color=INK, lw=2.0, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=16,
                                  linewidth=lw, color=color, zorder=2))


# source: where traffic comes from
box(0.3, 2.65, 1.9, 0.9, "Agents /\nAutomations", LIGHT, ACCENT, tc=NAVY, fs=12)

# main horizontal pipeline
stage_w, stage_h, gap = 2.6, 1.1, 0.7
stages = ["OBSERVE", "FINGERPRINT", "SCORE", "DECIDE"]
x = 2.7
stage_x = []
for s in stages:
    stage_x.append(x)
    box(x, 2.55, stage_w, stage_h, s, NAVY, ACCENT, fs=16)
    x += stage_w + gap

arrow(2.2, 3.1, 2.7, 3.1)
for i in range(len(stages) - 1):
    x0 = stage_x[i] + stage_w
    x1 = stage_x[i + 1]
    arrow(x0, 3.1, x1, 3.1)

decide_x = stage_x[-1] + stage_w / 2

# FINGERPRINT reads/writes a baseline store below it - a single
# double-headed arrow reads as "read/write" at a glance; the old two
# separate parallel lines were easy to misread as two one-way arrows
# pointing the same direction
fp_x = stage_x[1]
box(fp_x - 0.1, 0.35, stage_w + 0.2, 0.85, "Known-good profile store\n(per-agent baseline)",
    LIGHT, ACCENT, tc=NAVY, fs=10.5)
arrow(fp_x + stage_w / 2, 1.2, fp_x + stage_w / 2, 2.55, color="#6B7280", style="<|-|>")

# SCORE fan-in: rules + ML feed the SCORE stage from below
score_x = stage_x[2]
sub_w = (stage_w - 0.3) / 2
box(score_x, 0.35, sub_w, 0.85, "Rules layer", LIGHT, ACCENT, tc=NAVY, fs=10.5)
box(score_x + sub_w + 0.3, 0.35, sub_w, 0.85, "ML layer\n(Isolation Forest)", LIGHT, ACCENT, tc=NAVY, fs=10)
arrow(score_x + sub_w / 2, 1.2, score_x + 0.5, 2.55)
arrow(score_x + sub_w + 0.3 + sub_w / 2, 1.2, score_x + stage_w - 0.5, 2.55)

# decision fan-out: PASS / STEP-UP / BLOCK - more breathing room above
# DECIDE and below the enforcement block than the original tight spacing
chip_w, chip_h = 1.6, 0.7
chip_y = 4.3
chips = [("PASS", GREEN), ("STEP-UP", AMBER), ("BLOCK", RED)]
chip_total_w = len(chips) * chip_w + (len(chips) - 1) * 0.35
cx0 = decide_x - chip_total_w / 2
cxs = []
for i, (label, color) in enumerate(chips):
    cx = cx0 + i * (chip_w + 0.35)
    cxs.append(cx)
    box(cx, chip_y, chip_w, chip_h, label, color, color, fs=12)
    arrow(decide_x, 3.65, cx + chip_w / 2, chip_y)

# enforcement block, fed by all three decisions
enf_w, enf_y = 4.4, 5.45
enf_x = decide_x - enf_w / 2
box(enf_x, enf_y, enf_w, 0.75, "Enforcement block\ninline at the edge (FASTedge in production)",
    NAVY, ACCENT, fs=11)
for cx in cxs:
    arrow(cx + chip_w / 2, chip_y + chip_h, enf_x + enf_w / 2, enf_y, lw=1.6)

fig.suptitle("AEGIS pipeline: OBSERVE -> FINGERPRINT -> SCORE -> DECIDE",
             fontsize=16, fontweight="bold", color=NAVY, y=0.99)

fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT, dpi=160, bbox_inches="tight")
print(f"Saved {OUT}")
