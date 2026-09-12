# -*- coding: utf-8 -*-
"""
Fill the official 5G Academy Gate Evaluation Report template for AEGIS - Gate 2.

Takes the already-Gate-1-filled report as input (cover page + 1.1-1.4 done),
fills in the Gate 2 sections (2.1-2.5), marks the Gate-2 checkbox on the cover
page, embeds the architecture diagram, and leaves Gate 3 as template
placeholders (per the template instructions). Content mirrors docs/GATE-2.md.

Run:  .venv/Scripts/python AEGIS/src/make_gate2_report.py
In :  AEGIS/slides/Group 4_AEGIS_Gate1_Report.docx
Out:  AEGIS/slides/Group 4_AEGIS_Gate2_Report.docx
"""

import os
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "slides", "GATE-1", "Group 4_AEGIS_Gate1_Report.docx")
if not os.path.exists(TPL):
    TPL = os.path.join(HERE, "..", "slides", "Group 4_AEGIS_Gate1_Report.docx")
OUT = os.path.join(HERE, "..", "slides", "Group 4_AEGIS_Gate2_Report.docx")
DIAGRAM = os.path.join(HERE, "..", "reports", "aegis_architecture_diagram.png")

doc = Document(TPL)


# ------------------------------------------------------------------ helpers
def heading_index(text):
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == text:
            return i
    return -1


def placeholder_after(idx, marker="["):
    for p in doc.paragraphs[idx + 1:]:
        if p.text.strip().startswith(marker):
            return p
    return None


def set_runs(p, parts):
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    for (t, b) in parts:
        run = p.add_run(t)
        run.bold = b
    return p


def style_or(name, fallback="List Paragraph"):
    try:
        _ = doc.styles[name]
        return name
    except KeyError:
        return fallback


def add_after(anchor, parts, style=None):
    """Insert a new paragraph right after `anchor` (a Paragraph); return it."""
    new_p = OxmlElement("w:p")
    anchor._p.addnext(new_p)
    np = Paragraph(new_p, anchor._parent)
    if style:
        np.style = doc.styles[style]
    for (t, b) in parts:
        run = np.add_run(t)
        run.bold = b
    return np


def bullets_after(anchor, items):
    st = style_or("List Bullet")
    cur = anchor
    for parts in items:
        cur = add_after(cur, parts, style=st)
    return cur


def numbered_after(anchor, items):
    st = style_or("List Number")
    cur = anchor
    for parts in items:
        cur = add_after(cur, parts, style=st)
    return cur


def set_cell_shading(cell, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shd)


def style_table(table):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row_idx, row in enumerate(table.rows):
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9.5)
                if row_idx == 0:
                    for run in p.runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            if row_idx == 0:
                set_cell_shading(cell, "1E5A8A")
            elif row_idx % 2 == 0:
                set_cell_shading(cell, "F2F5F8")


def table_after(anchor, headers, rows):
    """Build a Table Grid table with a header row, insert it right after
    `anchor`, and return the paragraph that now follows the table (so more
    content can keep being appended in order)."""
    tbl = doc.add_table(rows=1, cols=len(headers))
    try:
        tbl.style = "Table Grid"
    except KeyError:
        pass
    for i, h in enumerate(headers):
        tbl.rows[0].cells[i].text = h
    for r in rows:
        cells = tbl.add_row().cells
        for i, val in enumerate(r):
            cells[i].text = str(val)
    style_table(tbl)
    anchor._p.addnext(tbl._tbl)
    # a spacer paragraph after the table, so subsequent add_after calls have
    # a normal paragraph anchor rather than a table element
    spacer = OxmlElement("w:p")
    tbl._tbl.addnext(spacer)
    return Paragraph(spacer, anchor._parent)


# ------------------------------------------------------------------ cover page
# Gate checkboxes and submission date are hand-maintained directly in the docx
# (submission date is 22 Sept) - do not overwrite them here on regeneration.

# ================================================================== 2.1 Proposed Technical Solution
ph = placeholder_after(heading_index("2.1 Proposed Technical Solution"))
set_runs(ph, [(
    "As AI agents, orchestration bots, and closed-loop automations increasingly issue commands "
    "directly to 5G network control services, classical authentication is no longer sufficient to "
    "establish trust. A stolen token, a leaked client certificate, or a compromised automation "
    "account will still pass authentication - the credential is valid - even though the actor "
    "behind it is not the legitimate agent. Classic AAA answers “is the credential valid?” "
    "It cannot answer “is this really the agent we onboarded, behaving the way it always "
    "behaves?”", False)])
last = add_after(ph, [(
    "AEGIS answers that second question. It is a zero-trust gate for machine identities: it builds "
    "a behavioural fingerprint of each legitimate agent from how it actually calls the network's "
    "APIs, and continuously scores every new request against that fingerprint, aligned with NIST "
    "SP 800-207 zero-trust principles (never trust, always verify; verify continuously; assume "
    "breach).", False)])
last = add_after(last, [("One-line pitch: ", True),
                         ("credentials prove what you have; AEGIS verifies how you behave.", False)])
last = add_after(last, [(
    "Scope. AEGIS targets service/automation agents (orchestration, closed-loop automation, "
    "OSS/BSS jobs, API clients) calling network control APIs, modelled on the 5G Service-Based "
    "Architecture (SBA) / Service-Based Interface (SBI): AMF, SMF, NRF, NEF, PCF, UDM. End-user "
    "devices, the data plane, and general “AI safety” are explicitly out of scope: AEGIS "
    "guards the control-plane API surface used by machine actors, which keeps the problem concrete "
    "and solvable within the PoC timeline rather than open-ended.", False)])
last = add_after(last, [(
    "The solution in one pipeline: OBSERVE request patterns and metadata (id, timing, call "
    "sequence, payload shape) -> FINGERPRINT a known-good behavioural baseline per agent -> "
    "SCORE with rules plus an ML anomaly/spoof score -> DECIDE PASS / STEP-UP / BLOCK "
    "(zero-trust gate dashboard).", False)])
last = add_after(last, [(
    "Threats the solution is built to catch. We assume an attacker who has already obtained a "
    "valid credential (the realistic case) or controls a legitimate agent, and must therefore be "
    "caught by behaviour, not by credential checks:", False)])
last = table_after(last, ["#", "Threat", "Behavioural signal AEGIS keys on"], [
    ("T1", "Identity spoofing / impersonation", "Fingerprint mismatch: wrong endpoint mix, timing, sequence for that identity"),
    ("T2", "Compromised agent", "Drift from its own baseline: new endpoints, new methods, elevated error rate"),
    ("T3", "Reconnaissance / enumeration", "High cardinality of endpoints/targets, many 403/404s, breadth over depth"),
    ("T4", "Volumetric abuse / DoS", "Request-rate spike far above the agent's normal envelope"),
    ("T5", "Low-and-slow exfiltration", "Abnormal read/GET ratio and payload sizes, off-hours persistence"),
    ("T6", "Replay / sequence anomaly", "Broken call-sequence pattern vs the agent's normal call graph"),
    ("T7", "Privilege / scope creep", "Calls to NFs never in the agent's baseline scope"),
])
last = add_after(last, [(
    "This directly extends the Gate 1 feasibility case: the technology (behavioural fingerprinting "
    "and anomaly detection), the risks, and the economic rationale (enabling safe automation, "
    "NIS2/GDPR/EU-AI-Act audit evidence) were validated at Gate 1. Gate 2 delivers the concrete "
    "architecture (2.2, with a full system diagram), a working implementation (2.3), and numerical "
    "proof that the approach works (2.4), the three things Gate 1 could only describe as intent.", False)])

# ================================================================== 2.2 Architecture
ph = placeholder_after(heading_index("2.2 Architecture"))
for r in list(ph.runs):
    r._element.getparent().remove(r._element)
run = ph.add_run(
    "AEGIS is structured as a four-stage pipeline sitting logically in front of the network's "
    "control-plane APIs. Every request an agent sends to a Network Function is observed by the "
    "gate before (in production) or in parallel with (in the PoC) reaching the NF. See Figure 2.1."
)
if os.path.exists(DIAGRAM):
    fig_p = add_after(ph, [])
    fig_p.add_run().add_picture(DIAGRAM, width=Inches(6.3))
    cap = add_after(fig_p, [("Figure 2.1 - AEGIS system architecture: OBSERVE -> FINGERPRINT -> "
                             "SCORE -> DECIDE, with the rules layer, ML layer, and known-good "
                             "profile store feeding SCORE, and PASS / STEP-UP / BLOCK as the "
                             "three decision outcomes.", False)])
    for r in cap.runs:
        r.italic = True
        r.font.size = Pt(9)
    last = cap
else:
    last = ph

last = add_after(last, [("Component description:", True)])
last = bullets_after(last, [
    [("OBSERVE. ", True),
     ("Every request is parsed into a normalized event: agent identity, HTTP method, target "
      "Network Function, endpoint, timestamp, and payload size. Events are grouped into a "
      "per-agent stream, the unit the rest of the pipeline operates on.", False)],
    [("FINGERPRINT. ", True),
     ("Requests are aggregated into sliding 60-second windows and turned into a feature vector "
      "per agent, per window: volume/rate, surface (distinct NFs/endpoints/target IDs), method "
      "mix, sequence, errors, payload, temporal (hour-of-day), and cross-window breadth (a "
      "rolling union of endpoints/NFs and error count over the trailing 5 minutes, so "
      "reconnaissance spread thin enough to look quiet in any single window is still caught). "
      "These vectors are compared against a known-good profile store, the behavioural baseline "
      "built for each agent during onboarding.", False)],
    [("SCORE. ", True),
     ("Two layers run in parallel and are fused. The rules layer (fast, explainable) applies hard "
      "caps and forbidden transitions, a session-state machine that tracks PDU-session lifecycle "
      "(catching orphaned update/release calls, T6), and rolling 5-minute accumulators (breadth, "
      "error count, peak payload) that catch cumulative anomalies too sparse for any single window "
      "(the mechanism behind T3 and T5 detection). The ML layer is an Isolation Forest trained "
      "only on legitimate traffic, engaging once an agent has at least 10 requests in the trailing "
      "5 minutes. Fusion: risk equals the maximum of the rule score and the ML score. Thresholds "
      "are tuned for a realistic false-positive budget (about 1.5 percent) rather than maximum "
      "sensitivity, which is why detection is intentionally not uniform across threats (see 2.4).", False)],
    [("DECIDE. ", True),
     ("The fused risk score maps to PASS (low risk, behaves like its known-good self), STEP-UP "
      "(medium risk: re-authentication, approval, or throttling), or BLOCK (high risk: quarantine "
      "the identity, alert the SOC).", False)],
    [("Trust boundary. ", True),
     ("Every request from an agent to a Network Function crosses the AEGIS gate. In production "
      "this is envisioned as an inline policy check at the edge (FASTedge); for the PoC it runs as "
      "an offline/log-replay analysis over synthetic SBI-style traffic.", False)],
    [("Dashboard / enforcement surface. ", True),
     ("A Streamlit application exposes, per agent, current risk, PASS/STEP-UP/BLOCK status, a "
      "breakdown of detections by threat type, and an incident inspector with a plain-language "
      "explanation of why a request was flagged.", False)],
])

# ================================================================== 2.3 Implementation Strategy
ph = placeholder_after(heading_index("2.3 Implementation Strategy"))
set_runs(ph, [("Methodology. ", True),
              ("AEGIS is built bottom-up, PoC-first, and evaluation-driven: the ML/security "
               "equivalent of test-driven development. No rule or model change is kept unless it "
               "is immediately re-scored against the full labelled dataset and shown to improve "
               "(or at least not regress) the numbers in 2.4. Each of the four architectural "
               "stages is a separately runnable, separately verifiable script.", False)])
last = add_after(ph, [("Tools and platforms:", True)])
last = table_after(last, ["Layer", "Tool / platform", "Role"], [
    ("Language/runtime", "Python 3.12", "Single language across generation, detection, and dashboard"),
    ("Data generation & processing", "pandas, NumPy", "Synthetic SBI-traffic generation, windowing, feature engineering"),
    ("Anomaly detection", "scikit-learn (Isolation Forest)", "Unsupervised ML layer, trained on legitimate traffic only"),
    ("Visualization / gate UI", "Streamlit, Matplotlib", "Live zero-trust gate dashboard and evaluation charts"),
    ("Deck/report tooling", "python-docx, python-pptx", "Reproducible generation of the Gate decks and reports"),
    ("Delivery", "Git/GitHub, GitHub Pages", "Version control and a public showcase site"),
])
last = add_after(last, [("Implementation phases:", True)])
last = table_after(last, ["Phase", "Output", "Primary file(s)"], [
    ("1. Synthetic environment", "Labelled SBI-style traffic, 5 agents, T1-T7", "generate_synthetic_traffic.py"),
    ("2. Fingerprinting", "Per-agent windowed feature vectors", "aegis_detect.py (build_windows)"),
    ("3. Rules layer", "Deterministic scope/session/rolling checks", "aegis_detect.py (rule_score)"),
    ("4. ML layer", "Isolation Forest fit on legit-only traffic", "aegis_detect.py (ml_scores)"),
    ("5. Fusion & decision", "Risk scoring, PASS/STEP-UP/BLOCK", "aegis_detect.py (main, decision)"),
    ("6. Dashboard", "Live zero-trust gate UI", "aegis_dashboard.py"),
    ("7. Evaluation & iteration", "Metrics, charts, bug-fixing loop", "aegis_baseline_metrics.md"),
])
last = add_after(last, [("Step-by-step, and what the evaluation loop caught:", True)])
last = numbered_after(last, [
    [("Synthetic traffic generation produced 210,000 requests across 5 legitimate agent profiles "
      "with realistic PDU-session lifecycles, plus the seven threat scenarios injected as labelled "
      "anomalous segments, removing the dependency on real operator logs.", False)],
    [("Feature engineering turned the windowed request stream into the behavioural feature vectors "
      "described in 2.2.", False)],
    [("The rules layer implements deterministic scope, rate, and session-sequence checks. An "
      "earlier T6 window-count heuristic was replaced with a session-ID state machine after it was "
      "found to false-fire on legitimate bursty traffic.", False)],
    [("The ML layer, an Isolation Forest, is fit only on legitimate traffic with a held-out "
      "calibration split.", False)],
    [("Fusion and decision policy combine rule and ML scores into PASS / STEP-UP / BLOCK.", False)],
    [("The dashboard exposes per-agent risk, decisions, per-threat breakdown, and the incident "
      "inspector.", False)],
    [("Evaluation and iteration: re-scoring after every change surfaced two real bugs, not just "
      "tuning cosmetics. First, T3 and T5 are naturally sparse per window; rolling 5-minute "
      "accumulators fixed this generically. Second, the initial T2 and T5 attack scenarios both "
      "had the injected agent call a Network Function outside its own onboarded scope, "
      "indistinguishable from T7 to the rules layer, so both were trivially caught by the scope "
      "rule rather than the drift/payload logic they were meant to test. Redesigning both to stay "
      "within the attacking agent's own scope forced detection to rely on the intended statistical "
      "signal, which is the origin of the non-uniform per-threat numbers in 2.4.", False)],
])

# ================================================================== 2.4 Numerical Performance Analysis
ph = placeholder_after(heading_index("2.4 Numerical Performance Analysis"))
set_runs(ph, [(
    "Benchmarking against real-world detection systems, not just internal targets. Before "
    "finalizing the operating point, we researched how comparable systems perform in practice, "
    "since a PoC that reports 100 percent detection on everything is a red flag to anyone who has "
    "looked at production security data, not a strength.", False)])
last = bullets_after(ph, [
    [("Published NIDS studies on CICIDS2017/UNSW-NB15 consistently show volumetric/DoS attacks "
      "detected at 97 to 99.8 percent (large, unambiguous signal), while reconnaissance and other "
      "low-frequency attack classes detect far lower unless heavy class-balancing is applied.", False)],
    [("Industry SOC data (Microsoft/Omdia State of the SOC 2025, SANS 2025 Detection and Response "
      "Survey) puts typical false-positive rates at 46 to 83 percent, with elite, well-tuned SOCs "
      "under 10 percent, and under 5 percent considered excellent.", False)],
    [("UEBA/insider-threat research shows a hard precision/recall tradeoff: models reporting "
      "near-perfect recall do so by sacrificing precision, sometimes to as low as 0.54; "
      "low-and-slow exfiltration is consistently the hardest category.", False)],
])
last = add_after(last, [(
    "We therefore tuned AEGIS's decision thresholds and rule sensitivities for a realistic "
    "false-positive budget (about 1.5 percent), in the well-tuned-not-superhuman range, rather "
    "than for maximum sensitivity, and treated a non-uniform, threat-dependent detection rate as "
    "the expected, correct outcome rather than something to eliminate.", False)])
last = add_after(last, [(
    "Test set: approximately 11,365 held-out windows (11,010 legitimate, 355 attack), 60-second "
    "window size, decision thresholds STEP-UP at 0.6 or above and BLOCK at 0.85 or above.", False)])
last = add_after(last, [("Headline metrics (rules + ML fused):", True)])
last = table_after(last, ["Metric", "Value"], [
    ("ROC-AUC", "0.965"),
    ("Precision", "0.672"),
    ("Recall (detection rate)", "0.907"),
    ("F1 score", "0.772"),
    ("False-positive rate (legit traffic flagged)", "1.43%"),
    ("ROC-AUC, ML only (no rules)", "0.721"),
])
last = add_after(last, [("Detection rate per threat type, deliberately not uniform:", True)])
last = table_after(last, ["Threat", "Windows", "Detected", "Why this level"], [
    ("T4 - Volumetric abuse / DoS", "60", "100%", "Loud rate spike, the easiest signal in the literature"),
    ("T7 - Privilege / scope creep", "35", "100%", "Deterministic policy/ACL check, not statistical inference"),
    ("T1 - Identity spoofing / impersonation", "54", "96%", "Mostly a scope mismatch, with a stealthier in-scope variant mixed in"),
    ("T6 - Replay / sequence anomaly", "57", "93%", "An isolated single anomaly without context is treated as ambiguous"),
    ("T2 - Compromised agent", "43", "91%", "Drift confined to the agent's own scope, relies on genuine behavioural drift"),
    ("T3 - Reconnaissance / enumeration", "60", "80%", "Enumeration within an agent's own scope, hardest class in NIDS benchmarks"),
    ("T5 - Low-and-slow exfiltration", "46", "76%", "Hardest threat category industry-wide, caught only via rolling accumulation"),
])
last = add_after(last, [(
    "Two of these threats (T4, T7) are legitimately near 100 percent because they are not "
    "statistical detection problems, a rate cap and a scope/ACL check are deterministic lookups. "
    "The other five sit in a genuine 76 to 96 percent spread that tracks the strength of their "
    "underlying behavioural signal: loud beats subtle, and diffuse/low-and-slow attacks are always "
    "the hardest.", False)])
last = add_after(last, [("Gate decisions on the test set:", True)])
last = table_after(last, ["Decision", "Windows", "Share"], [
    ("PASS", "10,886", "95.8%"),
    ("STEP-UP", "148", "1.3%"),
    ("BLOCK", "331", "2.9%"),
])
last = add_after(last, [("Interpretation:", True)])
last = bullets_after(last, [
    [("A 1.43 percent false-positive rate sits inside the well-tuned-SOC band from the industry "
      "data above, without claiming an implausible near-zero rate.", False)],
    [("90.7 percent recall means roughly 9 in 10 attacks are caught before reaching PASS, strong "
      "but honestly short of perfect, consistent with real behavioural/UEBA systems at comparable "
      "false-positive budgets.", False)],
    [("The precision of 0.67 reflects the same recall/precision tension documented across the UEBA "
      "literature; the STEP-UP tier absorbs medium-confidence cases into a re-authentication "
      "challenge rather than an outright block.", False)],
])

# ================================================================== 2.5 Expected PoC
ph = placeholder_after(heading_index("2.5 Expected Proof of Concept (PoC)"))
set_runs(ph, [(
    "Unlike a purely forward-looking PoC description, AEGIS already has a working, demonstrable "
    "baseline implementing the full pipeline end to end on synthetic data, matching the "
    "architecture in Figure 2.1 exactly.", False)])
last = add_after(ph, [("Live demo script:", True)])
last = numbered_after(last, [
    [("Agent overview. ", True), ("Open the dashboard and show all 5 legitimate agents with their "
      "live risk scores, all sitting in PASS.", False)],
    [("Trigger a threat. ", True), ("Select a scored window for one of T1-T7 (for example, T4 "
      "volumetric) and show the dashboard flip that agent to BLOCK in real time.", False)],
    [("Open the incident inspector. ", True), ("Show the plain-language why: which feature tripped "
      "(rate spike, scope violation, rolling breadth), tracing back to the rules or ML layer that "
      "produced it.", False)],
    [("Repeat across threat types. ", True), ("Cycle through a spoofing case (T1), a quiet "
      "within-scope drift case (T2), and a low-and-slow exfiltration case (T5), showing the full "
      "spread of detection difficulty from 2.4 live.", False)],
    [("Show the numbers. ", True), ("Bring up the metrics report and evaluation chart alongside "
      "the dashboard: ROC-AUC, recall, false-positive rate, and the per-threat table.", False)],
    [("Make the zero-trust gap concrete. ", True), ("Point to a flagged window where the request "
      "used a fully valid credential but was still blocked on behaviour, the exact gap in classical "
      "AAA that AEGIS closes.", False)],
])
last = add_after(last, [("PoC readiness at Gate 2:", True)])
last = table_after(last, ["Capability", "Status"], [
    ("Synthetic SBI-style traffic generator (5 agents, T1-T7)", "Done"),
    ("Fingerprinting, rules layer, ML layer, fusion, decision policy", "Done"),
    ("Live dashboard with incident inspector", "Done"),
    ("Numerical evaluation (ROC-AUC, recall, precision, FPR, per-threat)", "Done"),
    ("ROC operating-point / threshold sensitivity analysis", "Done"),
    ("Real M2M / API-gateway traffic", "Not yet, synthetic only, blocked on Fastweb/Vodafone data access"),
])
last = add_after(last, [(
    "What this validates: that a behavioural-fingerprint plus rules/ML gate is a practical way to "
    "add a continuous-verification layer on top of existing credential-based authentication for "
    "machine identities on 5G control-plane APIs, trainable without labelled attacks, and "
    "numerically effective at a realistic operating point.", False)])
last = add_after(last, [("Path to Gate 3:", True)])
last = bullets_after(last, [
    [("Closing the gap on the hardest threats (T3 recon at 80 percent, T5 exfiltration at 76 "
      "percent) with richer features, such as per-target-ID cardinality.", False)],
    [("Integrating real M2M / API-gateway logs if made available by Fastweb/Vodafone, the one "
      "open item outside our control.", False)],
    [("Recording the final video demonstration from the live demo script above.", False)],
    [("Expanding the number of agent and attack variants to stress-test generalization.", False)],
])

doc.save(OUT)
print("Saved", OUT)
print("Tables:", len(doc.tables), "| paragraphs:", len(doc.paragraphs))
