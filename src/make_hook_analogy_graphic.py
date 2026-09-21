# -*- coding: utf-8 -*-
"""Generates the flat-icon "badge vs. agent" comparison graphic used on the
new Gate 2 hook slide (inserted right after the Index). Two side-by-side
scenes in the deck's own palette: a stolen-but-valid office badge that still
gets caught by a guard's judgement, and a stolen-but-valid credential that
still gets caught by AEGIS reading behaviour. No stock art, no external
assets - built from matplotlib patches so it matches the deck's flat,
rounded-rectangle visual language exactly.

Run:  .venv/Scripts/python AEGIS/src/make_hook_analogy_graphic.py
Out:  AEGIS/reports/GATE-2/aegis_hook_analogy.png
"""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "reports", "GATE-2", "aegis_hook_analogy.png")

NAVY = "#020C31"
ACCENT = "#01ABDB"
ACCENT2 = "#3D67B1"
BODY_C = "#334155"
MUTE_C = "#6B7688"
PANEL_C = "#F2F7FA"
GREEN_C = "#0E9384"
FONT = "DejaVu Sans"

FIG_W, FIG_H = 11.67, 2.65
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
plt.rcParams["font.family"] = FONT


def panel(x, w, label, label_color):
    ax.add_patch(FancyBboxPatch((x, 0.1), w, FIG_H - 0.2,
                                 boxstyle="round,pad=0,rounding_size=0.12",
                                 linewidth=0, facecolor=PANEL_C, zorder=1))
    ax.text(x + 0.35, FIG_H - 0.42, label, fontsize=13, fontweight="bold",
            color=label_color, family=FONT, zorder=3)


def draw_badge(cx, cy, scale, color):
    """Flat ID-badge icon: card + lanyard clip + photo circle + text stripes."""
    w, h = 1.05 * scale, 1.35 * scale
    x, y = cx - w / 2, cy - h / 2
    ax.add_patch(Rectangle((cx - 0.09 * scale, y + h), 0.18 * scale, 0.22 * scale,
                            facecolor=MUTE_C, edgecolor="none", zorder=3))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08",
                                 linewidth=0, facecolor=color, zorder=2))
    ax.add_patch(Circle((cx, y + h * 0.68), 0.22 * scale, facecolor="white", zorder=3))
    for i, frac in enumerate((0.32, 0.20, 0.08)):
        ax.add_patch(Rectangle((x + 0.14 * scale, y + frac * h), w - 0.28 * scale, 0.06 * scale,
                                facecolor="white", alpha=0.85, zorder=3))


def draw_robot(cx, cy, scale, color):
    """Flat AI-agent icon: rounded head + two eyes + antenna."""
    w, h = 1.15 * scale, 1.05 * scale
    x, y = cx - w / 2, cy - h / 2
    ax.add_line(Line2D([cx, cx], [y + h, y + h + 0.22 * scale], color=color, linewidth=2.5, zorder=2))
    ax.add_patch(Circle((cx, y + h + 0.26 * scale), 0.06 * scale, facecolor=color, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.14",
                                 linewidth=0, facecolor=color, zorder=2))
    for dx in (-0.28, 0.28):
        ax.add_patch(Circle((cx + dx * scale, cy + 0.05 * scale), 0.12 * scale, facecolor="white", zorder=3))
        ax.add_patch(Circle((cx + dx * scale, cy + 0.05 * scale), 0.05 * scale, facecolor=color, zorder=4))
    ax.add_patch(FancyBboxPatch((cx - 0.22 * scale, y + 0.14 * scale), 0.44 * scale, 0.09 * scale,
                                 boxstyle="round,pad=0,rounding_size=0.04",
                                 linewidth=0, facecolor="white", alpha=0.9, zorder=3))


def scene(x, w, label, label_color, icon_fn, icon_color, line1, line2):
    panel(x, w, label, label_color)
    icon_cx = x + 1.15
    icon_cy = FIG_H * 0.46
    icon_fn(icon_cx, icon_cy, 1.0, icon_color)
    text_x = x + 2.15
    ax.text(text_x, FIG_H * 0.60, "✓  " + line1, fontsize=12.5, fontweight="bold",
            color=GREEN_C, family=FONT, va="center", zorder=3)
    ax.text(text_x, FIG_H * 0.34, line2, fontsize=11.5, color=BODY_C, family=FONT,
            va="center", wrap=True, zorder=3)


scene(0.0, 5.55, "THE OFFICE", ACCENT2, draw_badge, ACCENT2,
      "Badge: valid", "But the guard notices: wrong hallway,\nwrong pace, wrong hours.")

ax.text(FIG_W / 2, FIG_H * 0.58, "=", fontsize=30, fontweight="bold", color=NAVY,
        family=FONT, ha="center", va="center", zorder=3)
ax.text(FIG_W / 2, FIG_H * 0.28, "SAME IDEA", fontsize=9.5, fontweight="bold", color=MUTE_C,
        family=FONT, ha="center", va="center", zorder=3)

scene(FIG_W - 5.55, 5.55, "THE NETWORK", ACCENT, draw_robot, ACCENT,
      "Credentials: valid", "But AEGIS notices: wrong endpoint,\nwrong pace, wrong pattern.")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=200, transparent=False, facecolor="white")
print(f"Saved {OUT}")
