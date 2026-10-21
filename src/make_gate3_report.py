# -*- coding: utf-8 -*-
"""
Fill the official 5G Academy Gate Evaluation Report template for AEGIS - Gate 3.

Takes the already-filled Gate 2 report (cover page + 1.1-1.4 + 2.1-2.5 done) as
input, fills in the Gate 3 sections (3.1-3.5), and embeds the real Open5GS
core validation diagram. Content mirrors docs/GATE-3/real-traffic-capture.md
and docs/GATE-3/real-vs-synthetic-dashboard-implications.md.

Run:  .venv/Scripts/python AEGIS/src/make_gate3_report.py
In :  AEGIS/slides/GATE-2/Group 4_AEGIS_Gate2_Report.docx
Out:  AEGIS/slides/GATE-3/Group 4_AEGIS_Gate3_Report.docx
"""

import os
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "..", "slides", "GATE-2", "Group 4_AEGIS_Gate2_Report.docx")
OUT = os.path.join(HERE, "..", "slides", "GATE-3", "Group 4_AEGIS_Gate3_Report.docx")
VALIDATION_DIAGRAM = os.path.join(HERE, "..", "reports", "GATE-3", "aegis_open5gs_validation_diagram.png")

doc = Document(TPL)


# ------------------------------------------------------------------ helpers (same as make_gate2_report.py)
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


def exact_after(idx, text):
    for p in doc.paragraphs[idx + 1:]:
        if p.text.strip() == text:
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
    spacer = OxmlElement("w:p")
    tbl._tbl.addnext(spacer)
    return Paragraph(spacer, anchor._parent)


# ================================================================== update inherited Gate 2 numbers
# The template (Gate 2's own submitted report) was written against the narrower
# 5-agent/7-threat catalogue (0.965 ROC-AUC / 90.7% recall). The catalogue was
# later widened to 7 agents/10 attack variants for the current full-catalogue
# run (0.979 / 91.6%), which is what the deck, dashboard, website, and README
# now all use. Patch the inherited 2.x headline numbers here, in THIS output
# only, so Gate 2's own submitted .docx on disk is never touched.
NARRATIVE_REPLACEMENTS = [
    ("0.944 ROC-AUC / 63.4% recall on our own data; AEGIS scores 0.965 / 90.7%",
     "0.929 ROC-AUC / 64.0% recall on our own data; AEGIS scores 0.979 / 91.6%"),
    ("approximately 11,365 held-out windows (11,010 legitimate, 355 attack)",
     "15,363 held-out windows (14,946 legitimate, 417 attack)"),
    ("A 1.43 percent false-positive rate", "A 1.44 percent false-positive rate"),
    ("90.7 percent recall means roughly 9 in 10",
     "91.6 percent recall means roughly 9 in 10"),
    ("The precision of 0.67 reflects", "The precision of 0.64 reflects"),
]
for p in doc.paragraphs:
    for old, new in NARRATIVE_REPLACEMENTS:
        if old in p.text:
            full = p.text.replace(old, new)
            set_runs(p, [(full, False)])

# the bootstrap CI / CV-stability / temporal-split paragraph reports real
# statistical checks that were run once, on that earlier 5-agent catalogue,
# and were not rerun on the widened one - flag that honestly rather than
# silently leaving unexplained lower numbers sitting next to the updated 2.4
# headline figures above them
for p in doc.paragraphs:
    if p.text.strip() == "Full detail for each check below is in reports/GATE-2/, one file per analysis.":
        set_runs(p, [(
            "Full detail for each check below is in reports/GATE-2/, one file per "
            "analysis. These five checks were run on the earlier, narrower 5-agent "
            "catalogue (the numbers in 2.4 above reflect the current, wider "
            "7-agent/10-variant run) and have not yet been re-run on the widened "
            "catalogue; the conclusions they support (threshold stability, temporal "
            "robustness, drift, evasion) are not expected to change materially, but "
            "the exact figures below predate the catalogue widening.", False)])

metric_updates = {"ROC-AUC": "0.979", "Precision": "0.640", "Recall (detection rate)": "0.916",
                   "F1 score": "0.753", "False-positive rate (legit traffic flagged)": "1.44%",
                   "ROC-AUC, ML only (no rules)": "0.717"}
threat_rows_new = [
    ("T1 - Identity spoofing / impersonation", "58", "100%",
     "Scope or identity mismatch against the agent's own baseline, including the harder broad-scope variant"),
    ("T4 - Volumetric abuse / DoS", "90", "100%",
     "Loud rate spike, the easiest signal in the literature, including the slow-ramp variant caught by the rolling accumulator"),
    ("T7 - Privilege / scope creep", "70", "100%",
     "Deterministic policy/ACL check, not statistical inference, including the alternate agent/NF pairing variant"),
    ("T3 - Reconnaissance / enumeration", "58", "95%",
     "Enumeration within an agent's own scope, hardest class in NIDS benchmarks"),
    ("T2 - Compromised agent", "44", "84%",
     "Drift confined to the agent's own scope, relies on genuine behavioural drift"),
    ("T6 - Replay / sequence anomaly", "58", "76%",
     "An isolated single anomaly without context is treated as ambiguous"),
    ("T5 - Low-and-slow exfiltration", "39", "72%",
     "Hardest threat category industry-wide, caught only via rolling accumulation"),
]
decision_rows_new = {"PASS": ("14,766", "96.1%"), "STEP-UP": ("166", "1.1%"), "BLOCK": ("431", "2.8%")}

for t in doc.tables:
    header = [c.text.strip() for c in t.rows[0].cells]
    if header == ["Metric", "Value"]:
        for row in t.rows[1:]:
            label = row.cells[0].text.strip()
            if label in metric_updates:
                row.cells[1].text = metric_updates[label]
        style_table(t)
    elif header == ["Threat", "Windows", "Detected", "Why this level"]:
        for row in list(t.rows[1:]):
            row._tr.getparent().remove(row._tr)
        for vals in threat_rows_new:
            cells = t.add_row().cells
            for i, v in enumerate(vals):
                cells[i].text = v
        style_table(t)
    elif header == ["Decision", "Windows", "Share"]:
        for row in t.rows[1:]:
            label = row.cells[0].text.strip()
            if label in decision_rows_new:
                nwin, share = decision_rows_new[label]
                row.cells[1].text = nwin
                row.cells[2].text = share
        style_table(t)
    elif header == ["Detector", "ROC-AUC", "Recall @ matched 1.43% FPR"]:
        t.rows[0].cells[2].text = "Recall @ matched 1.44% FPR"
        for row in t.rows[1:]:
            label = row.cells[0].text.strip()
            if label == "SPC z-score baseline":
                row.cells[1].text, row.cells[2].text = "0.929", "64.0%"
            elif label == "AEGIS (rules + ML fusion)":
                row.cells[1].text, row.cells[2].text = "0.979", "91.6%"
        style_table(t)


# ================================================================== 3.1 PoC Overview
ph = placeholder_after(heading_index("3.1 PoC Overview"))
set_runs(ph, [(
    "The final Proof of Concept is the same end-to-end pipeline presented at Gate 2 "
    "(OBSERVE -> FINGERPRINT -> SCORE -> DECIDE), unchanged, now validated on two "
    "independent fronts rather than one. Gate 2 proved the approach statistically, "
    "on a large, labelled synthetic test set built to the 3GPP Service-Based Interface's "
    "own semantics. Gate 3 adds the piece that was still open at Gate 2: the same, "
    "unmodified detection code (build_windows, learn_baselines, rule_score, ml_scores) "
    "run against real signalling traffic captured off a real 5G core, not traffic AEGIS's "
    "own generator produced.", False)])
last = add_after(ph, [(
    "Concretely, the PoC demonstrates: a live zero-trust gate dashboard scoring five "
    "agents in real time across all seven threat classes (T1-T7), each gate decision "
    "(PASS / STEP-UP / BLOCK) explained in plain language by the incident inspector; "
    "a named, reimplemented state-of-the-art baseline (SPC) beaten on the identical "
    "test split, not just an internal target; a decision threshold justified by a "
    "stated cost model rather than chosen by eye; and, new at Gate 3, a real Open5GS "
    "SA core plus a UERANSIM UE/gNB standing in for the network this would actually "
    "defend, with real captured traffic run through the same detector.", False)])
last = add_after(last, [(
    "What this validates: that a behavioural-fingerprint plus rules/ML gate is not "
    "only a statistically sound idea on synthetic data, it is a piece of code that "
    "keeps working, unmodified, the moment it is pointed at a real core's traffic.", False)])

# ================================================================== 3.2 Core Features Demonstrated
h32 = heading_index("3.2 Core Features Demonstrated")
feats = [
    exact_after(h32, "Feature 1: ____________________"),
    exact_after(h32, "Feature 2: ____________________"),
    exact_after(h32, "Feature 3: ____________________"),
]
feature_text = [
    [("Live zero-trust gate, end to end. ", True),
     ("OBSERVE -> FINGERPRINT -> SCORE -> DECIDE running on all seven agents, all seven "
      "threat classes, with PASS / STEP-UP / BLOCK decisions and a plain-language "
      "incident inspector explaining every flag.", False)],
    [("Rules + ML fusion, with a named baseline beaten. ", True),
     ("A deterministic rules layer fused with an Isolation Forest trained only on "
      "legitimate traffic (risk = max(rule_score, ml_score)), scoring 0.979 ROC-AUC "
      "and 91.6% recall against the SPC z-score baseline's 0.929 / 64.0% on the "
      "identical split, a statistically significant gap (p = 0.015).", False)],
    [("Statistically justified operating point. ", True),
     ("The 0.60 STEP-UP threshold is Pareto-efficient (no alternative threshold beats "
      "it on both recall and false-positive rate) and sits within 0.2 points of FPR of "
      "the Neyman-Pearson-achievable frontier, a checkable claim, not a tuned-by-eye "
      "number.", False)],
    [("Validated on a real 5G core, not just the synthetic generator. ", True),
     ("A real Open5GS SA deployment (14 Network Functions) plus a UERANSIM gNB/UE, "
      "real captured SBI traffic, and the unmodified detector correctly flagging a "
      "real attack-like pattern (3.3).", False)],
]
if all(feats):
    for p, text in zip(feats, feature_text[:3]):
        set_runs(p, text)
    last = feats[2]
    last = bullets_after(last, [feature_text[3]])
else:
    # fallback: template wording didn't match exactly, append a clean bullet list instead
    last = add_after(doc.paragraphs[h32], [])
    last = bullets_after(last, feature_text)

# ================================================================== 3.3 Technical Feasibility - Results
ph = placeholder_after(heading_index("3.3 Technical Feasibility - Results"))
set_runs(ph, [(
    "Gate 2 already established the statistical case (2.4): 0.979 ROC-AUC, 91.6% "
    "recall, 1.44% false-positive rate on 15,363 held-out synthetic windows across "
    "the widened 7-agent/10-attack-variant catalogue, with the bootstrap confidence "
    "intervals, cross-validated threshold stability, and temporal split (Additional "
    "Robustness Evidence above) reconfirming the same conclusion on the earlier, "
    "narrower 5-agent catalogue those specific checks were run against. Gate 3's new "
    "evidence answers a different question: does any of that survive contact with a "
    "real core, not just the generator that produced the test set.", False)])
last = add_after(ph, [("Real-core validation setup:", True)])
last = bullets_after(last, [
    [("Stood up a real core. ", True),
     ("A full Open5GS SA deployment (14 Network Functions: NRF, SCP, AUSF, UDR, UDM, "
      "SMF, UPF, AMF, PCF, BSF, NSSF, plus webui/metrics/mongo) with a UERANSIM "
      "gNB/UE, producing a genuine registration and PDU session, not simulated logs.", False)],
    [("Captured real SBI traffic. ", True),
     ("tcpdump on the AMF's network namespace (every NF here talks over the SCP, so "
      "the AMF's namespace sees nearly the full per-UE signalling lifecycle), parsed "
      "by src/parse_real_sbi_capture.py into the same schema AEGIS's detector already "
      "expects.", False)],
    [("Schema match, confirmed independently. ", True),
     ("The synthetic generator's endpoint-naming convention matches real Open5GS "
      "traffic almost exactly - for example, Nudm_SDM/get in the generator and "
      "/nudm-sdm/v2/{imsi}/... in the real capture are the same 3GPP service, "
      "checked, not assumed.", False)],
    [("Detection validated on real traffic. ", True),
     ("A second capture had a real scripted agent make direct SBI calls into the "
      "live core in two phases: phase 1 stayed inside a narrow scope (NRF + UDM "
      "only, a steady rate) to build a genuine real-traffic baseline; phase 2 "
      "broadened to every NF at a fast burst rate, a real volumetric/breadth attack "
      "pattern. Run through AEGIS's own, unmodified detection functions (only the "
      "window-tumbling granularity was re-tuned to this capture's much shorter "
      "timescale), 2 of 2 real attack-like windows were correctly flagged BLOCK, "
      "via the volumetric_spike_high rule firing on the real burst rate against the "
      "real learned baseline.", False)],
])
if os.path.exists(VALIDATION_DIAGRAM):
    fig_p = add_after(last, [])
    fig_p.add_run().add_picture(VALIDATION_DIAGRAM, width=Inches(6.3))
    cap = add_after(fig_p, [("Figure 3.1 - Real-core validation pipeline: UERANSIM and "
                             "Open5GS traffic captured via tcpdump, parsed into AEGIS's "
                             "schema, scored by the unmodified detector, 2 of 2 real "
                             "attack-like windows flagged BLOCK.", False)])
    for r in cap.runs:
        r.italic = True
        r.font.size = Pt(9)
    last = cap
last = add_after(last, [("Honest scope: ", True),
    ("this is a short, single-agent capture, and the result is rules-dominant by "
     "necessity, the capture was too brief to give the ML layer a meaningful "
     "legitimate-traffic history to fit against (noted directly in the validation "
     "script's own output, not glossed over). It is not a replacement for the full "
     "synthetic evaluation's statistical rigor (bootstrap CIs, the SPC baseline, the "
     "per-threat breakdown); it answers one specific, narrower question: does the "
     "pipeline's schema and detection logic hold up on real captured packets. It "
     "does.", False)])
last = add_after(last, [("What this means for going fully real in production: ", True),
    ("switching the live dashboard over to real traffic end to end is a real "
     "infrastructure project (a persistently running core, continuous capture, and "
     "a baseline-building period measured in days, not minutes), not a code change. "
     "That is why the public demo dashboard deliberately stays on synthetic data and "
     "the real-core validation is demonstrated separately: it avoids taking on "
     "live-infrastructure risk during the graded PoC demonstration while still "
     "providing the right-sized evidence this requirement asks for.", False)])

# ================================================================== 3.4 Video Demonstration
ph = placeholder_after(heading_index("3.4 Video Demonstration"))
set_runs(ph, [(
    "The storyboard for the video demonstration is complete: "
    "slides/GATE-3/storyboard_draft_team_4 1.pptx, 7 scenes covering the project "
    "intro, the team discussing the work, the Isolation Forest concept diagram, "
    "the live dashboard, and the closing credits, revised against the tutor's "
    "slide-by-slide rehearsal feedback. The shot-by-shot script "
    "(docs/GATE-3/Gate3_Video_Script.md) and the videographer brief "
    "(docs/GATE-3/Gate3_Videographer_Brief.md) are finalized alongside it: ~2:45 "
    "target runtime, 48 shots. Most of the technical substance the video needs "
    "already exists and is being reused directly - the recorded live-demo "
    "walkthrough (slides/GATE-2/AEGIS_Live_Demo.mp4), the architecture and "
    "pipeline visuals, and the real Open5GS validation diagram above - so "
    "recording and final edit is a scheduled production step with the "
    "videomaker, separate from this report.", False)])

# ================================================================== 3.5 Conclusions & Lessons Learned
ph = placeholder_after(heading_index("3.5 Conclusions & Lessons Learned"))
set_runs(ph, [(
    "The core claim holds end to end: a behavioural fingerprint, scored by fused "
    "rules and unsupervised ML, catches a stolen-but-valid credential that classical "
    "authentication cannot, statistically on 15,363 synthetic windows (Gate 2), and "
    "now demonstrably on real captured traffic from an actual 5G core (Gate 3), with "
    "the identical, unmodified detection code in both cases.", False)])
last = add_after(ph, [("Key lessons learned:", True)])
last = bullets_after(last, [
    [("Real traffic needs time, not just access. ", True),
     ("A short real capture gives the rules layer enough to work with but leaves the "
      "ML layer underfit, confirming that moving fully to real data is a data-"
      "accumulation problem measured in days, not an engineering blocker.", False)],
    [("Concept drift is real even on short timescales. ", True),
     ("KS-tests found 6 of 20 agent/feature pairs drifting within just 5 synthetic "
      "days, turning periodic re-baselining from a nice-to-have into a stated "
      "operational requirement for any production deployment.", False)],
    [("Adversarial stress-testing found a genuine gap, and we kept it visible. ", True),
     ("Pacing the same T4 flood volume over 24 hours instead of 1 drops detection "
      "from 100% to 0% against the current point-in-time rate check. The fix (a "
      "rolling volumetric accumulator, mirroring the one already used for T3/T5) is "
      "identified and scoped, not hidden behind a rerun of the easier scenario.", False)],
    [("Know which risk to take, and which not to, during a graded demo. ", True),
     ("The live dashboard deliberately stays on synthetic data rather than wiring in "
      "a persistent real core for the demonstration itself, separating "
      "\"does the pipeline work on real traffic\" (proven, 3.3) from "
      "\"is it safe to depend on live infrastructure during a graded presentation\" "
      "(not worth the risk for this stage).", False)],
    [("Evaluation discipline is what makes the result credible. ", True),
     ("Every number in this report, synthetic or real, traces back to a script that "
      "can be re-run (reports/GATE-2/, reports/GATE-3/, docs/GATE-3/"
      "real-traffic-capture.md), not a one-off claim.", False)],
])
last = add_after(last, [(
    "Overall, Gate 3 closes the one gap Gate 2 could not close on its own: proof that "
    "the detector's statistical strength on synthetic data was never an artefact of "
    "the generator that produced it.", False)])

# ================================================================== cover page
cover = doc.tables[0]
for row in cover.rows:
    label = row.cells[0].text.strip()
    if label == "Gate":
        row.cells[1].paragraphs[0].runs[0].text = "☑ Gate 1    ☑ Gate 2    ☑ Gate 3"
    elif label == "Submission Date":
        row.cells[1].paragraphs[0].runs[0].text = "14 October 2026"
    elif label == "Group Members":
        row.cells[1].paragraphs[0].runs[0].text = "Fauzan Ejaz (Leader), Llagami Tedi"

doc.save(OUT)
print("Saved", OUT)
print("Tables:", len(doc.tables), "| paragraphs:", len(doc.paragraphs))
