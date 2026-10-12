# -*- coding: utf-8 -*-
"""Schematic of the Open5GS validation setup: the real core topology and
how traffic was captured and fed into AEGIS's own detector, unmodified.
Replaces the terminal-screenshot image on the "Beyond Synthetic: A Real 5G
Core" slide - a raw docker-logs screenshot is hard to read on a slide and
doesn't actually explain the setup; a schematic does.

Run:  .venv/Scripts/python AEGIS/src/make_open5gs_validation_diagram.py
Out:  AEGIS/reports/GATE-3/aegis_open5gs_validation_diagram.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "reports", "GATE-3")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "aegis_open5gs_validation_diagram.png")

NAVY = "#020C31"
ACCENT = "#01ABDB"
LIGHT = "#EAF6FB"
GREEN = "#0E9384"
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


def arrow(x0, y0, x1, y1, color=INK, lw=2.0, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=16,
                                  linewidth=lw, color=color, zorder=2, linestyle=ls))


# -------- stage 1: real UE + gNB --------
box(0.3, 3.6, 2.3, 1.1, "UERANSIM\nUE + gNB", LIGHT, ACCENT, tc=NAVY, fs=13)
arrow(2.6, 4.15, 3.5, 4.15)

# -------- stage 2: the real Open5GS core, 14 NFs, AMF called out --------
core_x, core_y, core_w, core_h = 3.5, 2.3, 6.4, 3.7
box(core_x, core_y, core_w, core_h, "", NAVY, ACCENT, fs=1)
ax.text(core_x + core_w / 2, core_y + core_h - 0.4, "Open5GS 5G SA Core - 14 Network Functions",
        ha="center", va="center", fontsize=13.5, fontweight="bold", color="white", zorder=4)
nf_row1 = ["AMF", "SMF", "UDM", "AUSF"]
nf_row2 = ["PCF", "NRF", "UDR", "+ 6 more"]
nf_w, nf_h, nf_gap = 1.35, 0.7, 0.2
nf_x0 = core_x + (core_w - (len(nf_row1) * nf_w + (len(nf_row1) - 1) * nf_gap)) / 2
for i, nf in enumerate(nf_row1):
    x = nf_x0 + i * (nf_w + nf_gap)
    is_amf = nf == "AMF"
    box(x, core_y + core_h - 1.5, nf_w, nf_h, nf,
        ACCENT if is_amf else LIGHT, ACCENT, tc=NAVY, fs=11.5)
    if is_amf:
        amf_x = x + nf_w / 2
for i, nf in enumerate(nf_row2):
    x = nf_x0 + i * (nf_w + nf_gap)
    box(x, core_y + core_h - 2.4, nf_w, nf_h, nf, LIGHT, ACCENT, tc=NAVY, fs=11.5)

# -------- tap: tcpdump on the AMF network namespace --------
arrow(amf_x, core_y + core_h - 1.5, amf_x, core_y - 0.5, color=RED, lw=2.0, ls="--")
tap_w, tap_h = 3.6, 0.95
tap_x = amf_x - tap_w / 2
box(tap_x, core_y - 0.5 - tap_h, tap_w, tap_h,
    "tcpdump on the AMF's\nnetwork namespace", "white", RED, tc=RED, fs=11.5)

# -------- stage 3: parsed into AEGIS's own schema --------
parse_x, parse_y = core_x + core_w + 0.7, 3.6
box(parse_x, parse_y, 2.6, 1.1, "Parsed into AEGIS's\nexisting SBI schema (CSV)", LIGHT, ACCENT, tc=NAVY, fs=11.5)
arrow(core_x + core_w, 4.15, parse_x, parse_y + 0.55)

# -------- stage 4: AEGIS detector, unmodified --------
det_x = parse_x + 2.6 + 0.7
box(det_x, parse_y - 0.2, 2.6, 1.5, "AEGIS detector\n(unmodified code)", NAVY, ACCENT, fs=12.5)
arrow(parse_x + 2.6, parse_y + 0.55, det_x, parse_y + 0.55)

# -------- result --------
box(det_x, parse_y - 1.9, 2.6, 1.3, "2 / 2 real attack\nwindows -> BLOCK", GREEN, GREEN, fs=12.5)
arrow(det_x + 1.3, parse_y - 0.2, det_x + 1.3, parse_y - 0.6)

fig.suptitle("Beyond synthetic: how the real-core validation was wired up",
             fontsize=17, fontweight="bold", color=INK, y=0.99)

fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT, dpi=160, bbox_inches="tight")
print(f"Saved {OUT}")
