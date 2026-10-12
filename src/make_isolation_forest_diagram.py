# -*- coding: utf-8 -*-
"""Illustrative figure for the GATE-3 deck's Isolation Forest deep-dive slide:
why isolating an anomaly takes far fewer random splits than isolating a
normal point. Not a real AEGIS feature space (that's 10-dimensional) - a
2D toy so the mechanism is visible on a slide.

Run:  .venv/Scripts/python AEGIS/src/make_isolation_forest_diagram.py
Out:  AEGIS/reports/aegis_isolation_forest_concept.png
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "reports", "aegis_isolation_forest_concept.png")

rng = np.random.default_rng(7)
INKC, LEGITC, ATKC = "#1F2A37", "#3B82C4", "#D1495B"

normal = rng.normal(loc=(0.42, 0.45), scale=0.11, size=(70, 2))
normal = np.clip(normal, 0.03, 0.97)
anomaly = np.array([0.90, 0.92])

fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.6))

# --- panel 1: isolating the anomaly - few random splits needed
a = ax[0]
a.scatter(normal[:, 0], normal[:, 1], s=28, color=LEGITC, alpha=0.65, label="legit windows")
a.scatter(*anomaly, s=90, color=ATKC, marker="*", zorder=5, label="attack window")
cuts_a = [
    ("v", 0.70), ("h", 0.72), ("v", 0.82),
]
box = [0.0, 1.0, 0.0, 1.0]
for i, (axis, val) in enumerate(cuts_a):
    if axis == "v":
        a.plot([val, val], [box[2], box[3]], color=INKC, lw=1.3, ls="--", alpha=0.8)
        box[0] = val
    else:
        a.plot([box[0], box[1]], [val, val], color=INKC, lw=1.3, ls="--", alpha=0.8)
        box[2] = val
    a.text(box[0] + 0.01, 1.0 - 0.06 * (i + 1), f"split {i+1}", fontsize=10.5, color=INKC)
a.add_patch(Rectangle((box[0], box[2]), box[1]-box[0], box[3]-box[2],
                       fill=False, ec=ATKC, lw=1.6))
a.set_title("Isolating an anomaly: 3 random splits", fontsize=15, fontweight="bold", color=INKC)
a.set_xlim(0, 1); a.set_ylim(0, 1); a.set_xticks([]); a.set_yticks([])
a.legend(frameon=False, fontsize=13, loc="lower left")
for sp in a.spines.values():
    sp.set_visible(False)

# --- panel 2: isolating a normal point - many more splits needed
b = ax[1]
b.scatter(normal[:, 0], normal[:, 1], s=28, color=LEGITC, alpha=0.65)
target = normal[np.argmin(np.sum((normal - [0.42, 0.45])**2, axis=1))]
b.scatter(*target, s=90, color="#0E9384", marker="*", zorder=5)
cuts_b = [
    ("v", 0.55), ("h", 0.60), ("v", 0.30), ("h", 0.30),
    ("v", 0.38), ("h", 0.40), ("v", 0.44),
]
box = [0.0, 1.0, 0.0, 1.0]
for i, (axis, val) in enumerate(cuts_b):
    if axis == "v":
        b.plot([val, val], [box[2], box[3]], color=INKC, lw=1.0, ls="--", alpha=0.6)
        if val < target[0]:
            box[0] = max(box[0], val)
        else:
            box[1] = min(box[1], val)
    else:
        b.plot([box[0], box[1]], [val, val], color=INKC, lw=1.0, ls="--", alpha=0.6)
        if val < target[1]:
            box[2] = max(box[2], val)
        else:
            box[3] = min(box[3], val)
b.add_patch(Rectangle((box[0], box[2]), box[1]-box[0], box[3]-box[2],
                       fill=False, ec="#0E9384", lw=1.6))
b.set_title("Isolating a normal point: 7+ splits", fontsize=15, fontweight="bold", color=INKC)
b.set_xlim(0, 1); b.set_ylim(0, 1); b.set_xticks([]); b.set_yticks([])
for sp in b.spines.values():
    sp.set_visible(False)

fig.suptitle("Isolation Forest: anomalies sit apart, so random splits isolate them fast",
             fontsize=17, fontweight="bold", color=INKC, y=1.02)
fig.text(0.5, -0.04, "Short average path length -> high anomaly score.  Long average path length -> low anomaly score.",
          ha="center", fontsize=12.5, color=INKC)
fig.tight_layout()
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"Saved {OUT}")
