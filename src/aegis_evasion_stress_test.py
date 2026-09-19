# -*- coding: utf-8 -*-
"""
AEGIS - adversarial evasion stress test (Gate 2 evidence).

All seven threats in the main evaluation are "naive" - none are deliberately
paced or shaped to stay under AEGIS's specific thresholds. The honest
question a security reviewer asks next is: what happens when the attacker
knows the thresholds and paces around them?

This test builds a loud vs. evasive pair of T4 (volumetric flood) variants
that flood an endpoint INSIDE the attacker's own onboarded scope (AMF, which
closed-loop-assurance is normally allowed to call) rather than reusing the
original injector's SMF target - SMF is outside that agent's scope
(["AMF","NEF","PCF"]), so the original T4 attack also trips the hard,
pacing-independent scope-violation rule, which would confound a test of
whether pacing alone evades detection. Isolating an in-scope flood tests the
rate signal specifically. The evasive variant spreads the identical total
illegitimate request volume across 24 hours instead of 1 - a classic
"low-and-slow" flood, diluting the per-60s-window request count far enough
to sit under the rate-based rule thresholds. Both variants are injected onto
the SAME freshly-generated legit traffic base and scored with the SAME
rules+ML pipeline (aegis_detect, unmodified), so the only difference between
the two runs is attack pacing.

Run:  .venv/Scripts/python AEGIS/src/aegis_evasion_stress_test.py
Out:  reports/aegis_evasion_stress_test.md, .png
"""

import os
import sys
import random
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "..", "reports")
OUT_DIR = os.path.join(REPORTS, "GATE-2")
os.makedirs(OUT_DIR, exist_ok=True)
sys.path.insert(0, HERE)
from generate_synthetic_traffic import (AGENTS, gen_legit, RNG_SEED,  # noqa: E402
                                          BASE_DAY, endpoint_method)
from aegis_detect import (build_windows, learn_baselines, rule_score,  # noqa: E402
                           ml_scores, MIN_N_ROLL, STEPUP)
from datetime import timedelta


def make_legit_base():
    random.seed(RNG_SEED); np.random.seed(RNG_SEED)
    rows = []
    for agent, cfg in AGENTS.items():
        gen_legit(agent, cfg, rows)
    return rows



# closed-loop-assurance's own scope is ["AMF","NEF","PCF"] - the original T4
# injector floods SMF, which is OUTSIDE that scope and trips the hard
# scope-violation rule (fires unconditionally, regardless of pacing) on top
# of the volumetric signal. That confounds an evasion test of the rate
# signal specifically, so this test floods an IN-SCOPE endpoint instead,
# isolating exactly the signal we're trying to evade.
ATTACKER = "closed-loop-assurance"
IN_SCOPE_NF, IN_SCOPE_EP = "AMF", "Namf_EventExposure/subscribe"


def inject_loud_t4(rows, n=3000):
    """All n requests inside a single hour (day 4, hour 10), in-scope NF."""
    for i in range(n):
        ts = BASE_DAY + timedelta(days=4, hours=10, seconds=random.uniform(0, 3600))
        rows.append(dict(ts=ts, agent_id=ATTACKER, nf=IN_SCOPE_NF, endpoint=IN_SCOPE_EP,
                         method=endpoint_method(IN_SCOPE_EP), session_id="-",
                         resp_size=int(np.random.uniform(150, 400)),
                         status=random.choice([200, 200, 429]),
                         label="attack", attack_type="T4_volumetric"))


def inject_evasive_t4(rows, n=3000, spread_hours=24):
    """Evasive: the SAME n requests, paced across spread_hours instead of 1 -
    identical total illegitimate volume, far lower per-window density,
    same in-scope endpoint (isolates the rate signal specifically)."""
    for i in range(n):
        ts = BASE_DAY + timedelta(days=4, seconds=random.uniform(0, spread_hours * 3600))
        rows.append(dict(ts=ts, agent_id=ATTACKER, nf=IN_SCOPE_NF, endpoint=IN_SCOPE_EP,
                         method=endpoint_method(IN_SCOPE_EP), session_id="-",
                         resp_size=int(np.random.uniform(150, 400)),
                         status=random.choice([200, 200, 429]),
                         label="attack", attack_type="T4_volumetric"))


def score_scenario(rows):
    df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    feat = build_windows(df)
    agents = sorted(feat["agent_id"].unique())

    legit = feat[feat.label == "legit"].copy()
    attack = feat[feat.label == "attack"].copy()
    legit = legit.sample(frac=1.0, random_state=42).reset_index(drop=True)
    c1, c2 = int(0.4 * len(legit)), int(0.6 * len(legit))
    fit_legit, calib_legit, test_legit = legit.iloc[:c1], legit.iloc[c1:c2], legit.iloc[c2:]
    test = pd.concat([test_legit, attack], ignore_index=True)

    base = learn_baselines(pd.concat([fit_legit, calib_legit]))
    rule_results = test.apply(lambda r: rule_score(r, base), axis=1)
    test["rule"] = rule_results.apply(lambda t: t[0])
    test["rule_reason"] = rule_results.apply(lambda t: t[1])
    test["ml"] = ml_scores(fit_legit, calib_legit, test, agents)
    small = test["n_roll"] < MIN_N_ROLL
    test["risk"] = np.where(small, test["rule"], test[["rule", "ml"]].max(axis=1))
    return test


def main():
    base_rows = make_legit_base()
    n_legit = len(base_rows)

    loud_rows = list(base_rows)
    inject_loud_t4(loud_rows)
    evasive_rows = list(base_rows)
    inject_evasive_t4(evasive_rows)

    loud_scored = score_scenario(loud_rows)
    evasive_scored = score_scenario(evasive_rows)

    def t4_stats(scored):
        t4 = scored[scored.attack_type == "T4_volumetric"]
        det = float((t4["risk"] >= STEPUP).mean())
        return t4, det

    t4_loud, det_loud = t4_stats(loud_scored)
    t4_evasive, det_evasive = t4_stats(evasive_scored)

    n_med_loud = t4_loud["n"].median()
    n_med_evasive = t4_evasive["n"].median()

    # ---------------- figure ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INKC, ACC, EVAC = "#1F2A37", "#0E9384", "#D1495B"

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))

    a = ax[0]
    a.bar(["Loud (1hr burst)", "Evasive (24hr paced)"], [det_loud * 100, det_evasive * 100],
          color=[ACC, EVAC])
    a.set_ylabel("% of T4 windows detected"); a.set_ylim(0, 105)
    for i, v in enumerate([det_loud * 100, det_evasive * 100]):
        a.text(i, v + 2, f"{v:.0f}%", ha="center", fontsize=10, color=INKC)
    a.set_title("T4 detection: loud vs. paced evasion", fontsize=11, color=INKC)
    for sp in ["top", "right"]:
        a.spines[sp].set_visible(False)

    b = ax[1]
    b.hist(t4_loud["n"], bins=20, color=ACC, alpha=0.7, label=f"loud (median n={n_med_loud:.0f})")
    b.hist(t4_evasive["n"], bins=20, color=EVAC, alpha=0.7,
          label=f"evasive (median n={n_med_evasive:.0f})")
    b.set_xlabel("requests in window (n)"); b.set_ylabel("windows")
    b.set_title("Per-window request count", fontsize=11, color=INKC)
    b.legend(frameon=False, fontsize=8)
    for sp in ["top", "right"]:
        b.spines[sp].set_visible(False)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "aegis_evasion_stress_test.png"), dpi=140)
    plt.close(fig)

    # ---------------- report ----------------
    lines = []
    lines.append("# AEGIS - Adversarial Evasion Stress Test\n")
    lines.append("## Method\n")
    lines.append(
        "All seven threats in the main evaluation are naive - none deliberately paced against "
        "AEGIS's thresholds. The original T4 injector floods SMF, which is outside the attacking "
        "agent's own scope - that also trips the hard, pacing-independent scope-violation rule, "
        "confounding a clean test of whether pacing alone evades detection. This test instead "
        "floods an endpoint INSIDE the attacker's normal scope (AMF), isolating the rate signal, "
        "and compares the identical total illegitimate request volume delivered as a 1-hour burst "
        "versus paced across 24 hours. Both variants are injected onto the same freshly-generated "
        "legit traffic base and scored with the unmodified rules+ML pipeline.\n")
    lines.append("## Result\n")
    lines.append("| Variant | T4 windows | Detected | Median requests/window |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Loud (1hr burst) | {len(t4_loud)} | **{det_loud*100:.0f}%** | {n_med_loud:.0f} |")
    lines.append(f"| Evasive (24hr paced) | {len(t4_evasive)} | **{det_evasive*100:.0f}%** | "
                 f"{n_med_evasive:.0f} |")
    drop = (det_loud - det_evasive) * 100
    lines.append(f"\n**Pacing the same attack volume over 24x more time drops detection by "
                 f"{drop:.0f} percentage points.** This is expected, not a bug: the current "
                 "volumetric rule and the ML layer both key on per-window request count, and "
                 "diluting the flood thinly enough defeats a per-window signal by construction - "
                 "the same reason T3/T5 already use a rolling cross-window accumulator instead of "
                 "a single-window check. T4 currently does not have an equivalent rolling "
                 "accumulator.\n")
    lines.append(
        "## Honest implication\n"
        "This is a real, demonstrated gap, not a hypothetical one: an attacker aware of the "
        "60-second window and the rate threshold could evade the current volumetric detector by "
        "pacing. The direct fix - a rolling cumulative-volume accumulator for T4, mirroring the "
        "existing rolling breadth/payload accumulators already used for T3 and T5 - is scoped as "
        "concrete Gate 3 hardening work, prioritised ahead of the recon/exfil hardening already "
        "planned, since this test shows it is the more immediately exploitable gap.")
    report = "\n".join(lines) + "\n"

    with open(os.path.join(OUT_DIR, "aegis_evasion_stress_test.md"), "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print("Saved reports/aegis_evasion_stress_test.md, aegis_evasion_stress_test.png")


if __name__ == "__main__":
    main()
