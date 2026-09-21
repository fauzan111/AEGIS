# -*- coding: utf-8 -*-
"""Generates the four flat phase-icons (OBSERVE / FINGERPRINT / SCORE /
DECIDE) used on the Gate 2 "Proposed Technical Solution" pipeline slide -
one colored circle badge per phase with a simple white glyph, matching the
flat-icon language already established by make_hook_analogy_graphic.py.

Run:  .venv/Scripts/python AEGIS/src/make_pipeline_icons.py
Out:  AEGIS/reports/GATE-2/icon_observe.png, icon_fingerprint.png,
      icon_score.png, icon_decide.png
"""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Arc, Wedge, Polygon
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "reports", "GATE-2")

ACCENT = "#01ABDB"
ACCENT2 = "#3D67B1"
AMBER_C = "#E0A100"
GREEN_C = "#0E9384"


def new_canvas():
    fig = plt.figure(figsize=(2, 2), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1)
    ax.set_aspect("equal"); ax.axis("off")
    return fig, ax


def save(fig, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=200, transparent=True)
    print(f"Saved {path}")


def observe():
    fig, ax = new_canvas()
    ax.add_patch(Circle((0, 0), 0.92, facecolor=ACCENT, zorder=1))
    ax.add_patch(Circle((-0.12, 0.12), 0.34, facecolor="none", edgecolor="white",
                         linewidth=7, zorder=2))
    ax.add_line(Line2D([0.14, 0.42], [-0.14, -0.42], color="white", linewidth=8,
                        solid_capstyle="round", zorder=2))
    save(fig, "icon_observe.png")


def fingerprint():
    fig, ax = new_canvas()
    ax.add_patch(Circle((0, 0), 0.92, facecolor=ACCENT2, zorder=1))
    for r in (0.58, 0.44, 0.30, 0.16):
        ax.add_patch(Arc((0, 0.05), 2 * r, 2.3 * r, angle=0, theta1=200, theta2=340,
                          color="white", linewidth=6, zorder=2))
    save(fig, "icon_fingerprint.png")


def score():
    fig, ax = new_canvas()
    ax.add_patch(Circle((0, 0), 0.92, facecolor=AMBER_C, zorder=1))
    ax.add_patch(Wedge((0, -0.15), 0.62, 20, 160, width=0.09,
                        facecolor="white", edgecolor="none", zorder=2))
    ax.add_line(Line2D([0, 0.32], [-0.15, 0.28], color="white", linewidth=7,
                        solid_capstyle="round", zorder=3))
    ax.add_patch(Circle((0, -0.15), 0.08, facecolor="white", zorder=4))
    save(fig, "icon_score.png")


def decide():
    fig, ax = new_canvas()
    ax.add_patch(Circle((0, 0), 0.92, facecolor=GREEN_C, zorder=1))
    shield = Polygon([(-0.4, 0.5), (0.4, 0.5), (0.4, -0.05), (0, -0.55),
                       (-0.4, -0.05)], closed=True, facecolor="none",
                      edgecolor="white", linewidth=7, joinstyle="round", zorder=2)
    ax.add_patch(shield)
    ax.add_line(Line2D([-0.18, -0.02, 0.28], [0.02, -0.18, 0.22], color="white",
                        linewidth=7, solid_capstyle="round", solid_joinstyle="round",
                        zorder=3))
    save(fig, "icon_decide.png")


if __name__ == "__main__":
    observe()
    fingerprint()
    score()
    decide()
