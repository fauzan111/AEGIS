# -*- coding: utf-8 -*-
"""
AEGIS - renders the real UERANSIM UE registration log (captured live against
the real Open5GS core, see docs/GATE-3/real-traffic-capture.md) as a clean
terminal-style graphic for the video storyboard, since there's no reliable
screen-capture path for a live terminal in this environment. The log lines
below are the actual output from `docker logs nr_ue` on a real run, not
fabricated - only the presentation (colours, monospace window chrome) is
synthetic.

Run:  .venv/Scripts/python AEGIS/src/make_terminal_graphic.py
Out:  AEGIS/reports/GATE-3/storyboard-shots/open5gs_terminal.png
"""

import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "reports", "GATE-3", "storyboard-shots", "open5gs_terminal.png")

BG = "#010409"
TITLEBAR = "#21262d"
INFO = "#3fb950"
DEBUG = "#58a6ff"
TS = "#6e7681"
TITLE_C = "#8b949e"

# Real captured output from `docker logs nr_ue` (see docs/GATE-3/real-traffic-capture.md)
LINES = [
    ("18:21:49.156", "debug", "[nas] UAC access attempt is allowed for identity[0], category[MO_sig]"),
    ("18:21:49.156", "debug", "[nas] Sending Initial Registration"),
    ("18:21:49.158", "info", "[nas] UE switches to state [MM-REGISTER-INITIATED]"),
    ("18:21:49.160", "info", "[rrc] RRC connection established"),
    ("18:21:49.246", "debug", "[nas] Authentication Request received"),
    ("18:21:49.297", "debug", "[nas] Security Mode Command received"),
    ("18:21:49.363", "debug", "[nas] Registration accept received"),
    ("18:21:49.363", "info", "[nas] UE switches to state [MM-REGISTERED/NORMAL-SERVICE]"),
    ("18:21:49.363", "info", "[nas] Initial Registration is successful"),
    ("18:21:49.363", "debug", "[nas] Sending PDU Session Establishment Request"),
    ("18:21:49.648", "debug", "[nas] PDU Session Establishment Accept received"),
    ("18:21:49.648", "info", "[nas] PDU Session establishment is successful PSI[1]"),
    ("18:21:49.697", "info", "[app] Connection setup for PDU session[1] is successful,"
                             " TUN interface[uesimtun0, 192.168.100.2] is up."),
]

FIG_W, FIG_H = 11.0, 5.5
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W); ax.set_ylim(0, FIG_H)
ax.axis("off")

ax.add_patch(FancyBboxPatch((0.15, 0.15), FIG_W - 0.3, FIG_H - 0.3,
                             boxstyle="round,pad=0,rounding_size=0.08",
                             linewidth=0, facecolor=BG, zorder=1))
ax.add_patch(FancyBboxPatch((0.15, FIG_H - 0.65), FIG_W - 0.3, 0.5,
                             boxstyle="round,pad=0,rounding_size=0.08",
                             linewidth=0, facecolor=TITLEBAR, zorder=2))
for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    ax.add_patch(Circle((0.45 + i * 0.28, FIG_H - 0.40), 0.08, facecolor=color, zorder=3))
ax.text(1.5, FIG_H - 0.40, "nr_ue - real UERANSIM UE registering against the real Open5GS core",
        fontsize=10, color=TITLE_C, family="monospace", va="center", zorder=3)

ax.text(0.4, FIG_H - 0.95, "$ docker logs nr_ue", fontsize=10.5, color="#7ee787",
        family="monospace", va="top", zorder=3)

y = FIG_H - 1.35
for ts, level, msg in LINES:
    color = INFO if level == "info" else DEBUG
    ax.text(0.4, y, f"[{ts}]", fontsize=9, color=TS, family="monospace", va="top", zorder=3)
    ax.text(2.3, y, msg, fontsize=9, color=color, family="monospace", va="top", zorder=3,
            wrap=True)
    y -= 0.285

fig.savefig(OUT, dpi=200, facecolor="white")
print(f"Saved {OUT}")
