"""Build the AEGIS technical overview document for Fastweb / Vodafone.

Pulls content from docs/AEGIS_threat_model_and_architecture.md,
reports/aegis_baseline_metrics.md and data/aegis_traffic.csv so the
document stays consistent with the actual working PoC.
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "AEGIS_Tech_Overview_for_Fastweb.docx"

NAVY = RGBColor(0x0B, 0x1F, 0x3A)
ACCENT = RGBColor(0x1E, 0x5A, 0x8A)
GREY = RGBColor(0x55, 0x55, 0x55)


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
                    run.font.size = Pt(10)
                if row_idx == 0:
                    for run in p.runs:
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            if row_idx == 0:
                set_cell_shading(cell, "1E5A8A")
            elif row_idx % 2 == 0:
                set_cell_shading(cell, "F2F5F8")


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
    for r in rows:
        cells = table.add_row().cells
        for i, val in enumerate(r):
            cells[i].text = str(val)
    style_table(table)
    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    return table


def h1(doc, text, number=None):
    p = doc.add_heading(level=1)
    run = p.add_run(f"{number}. {text}" if number else text)
    run.font.color.rgb = NAVY
    return p


def h2(doc, text):
    p = doc.add_heading(level=2)
    run = p.add_run(text)
    run.font.color.rgb = ACCENT
    return p


def body(doc, text, bold=False, italic=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(11)
    run.font.bold = bold
    run.font.italic = italic
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    run.font.size = Pt(11)
    return p


doc = Document()

# base style
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

# --- Title page ---
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("AEGIS")
run.font.size = Pt(36)
run.font.bold = True
run.font.color.rgb = NAVY

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run("Zero Trust Identity for AI Agents on the Network")
run.font.size = Pt(16)
run.font.color.rgb = ACCENT

sub2 = doc.add_paragraph()
sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub2.add_run("Technical Overview for Fastweb and Vodafone")
run.font.size = Pt(13)
run.font.italic = True
run.font.color.rgb = GREY

sub3 = doc.add_paragraph()
sub3.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub3.add_run(
    "Prepared to support the discussion on what data and access can be "
    "shared to complete the project within the given timeframe."
)
run.font.size = Pt(11)
run.font.color.rgb = GREY

doc.add_paragraph()
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = meta.add_run(
    "5G Academy 2026, Fastweb + Vodafone, Topic 2, Security\n"
    "Team 4, Fauzan Ejaz (Captain), Adithya Zacharia Valavi, "
    "Ghazanfar Anees Siddiqui, Llagami Tedi"
)
run.font.size = Pt(10)
run.font.color.rgb = GREY

doc.add_page_break()

# --- 1. What we're building ---
h1(doc, "What We Are Building", 1)
body(
    doc,
    "As AI agents and automations increasingly act on the 5G network control "
    "plane, orchestration tools, closed-loop automation, OSS jobs and LLM "
    "copilots now call Network Functions over the Service-Based Interface "
    "(SBI), the same control APIs a human operator's tooling uses.",
)
body(
    doc,
    "A stolen token or a compromised automation account still passes normal "
    "authentication (AAA): the credential is valid, but the actor behind it "
    "is not. Authentication only answers the question \"is the credential "
    "valid?\". It never answers \"is this really our agent, behaving the way "
    "it always behaves?\"",
)
body(
    doc,
    "AEGIS answers the second question. It is a zero trust gate for machine "
    "identities: it learns each legitimate agent's behavioural fingerprint "
    "and scores every request against it, continuously, in line with NIST "
    "SP 800-207 zero trust principles (never trust, always verify; verify "
    "continuously; assume breach).",
    italic=False,
)
p = body(doc, "One line pitch: ", bold=True)
p.add_run(
    "credentials prove what you have, AEGIS verifies how you behave."
).italic = True

h2(doc, "Scope")
bullet(
    doc,
    "In scope: service and automation agents (orchestration, closed-loop "
    "automation, OSS/BSS jobs, API clients) calling network control APIs, "
    "modelled on the 5G SBA / SBI.",
)
bullet(
    doc,
    "Out of scope for the PoC: end-user devices, the data plane / user "
    "traffic, and general AI safety. AEGIS guards the control-plane API "
    "surface used by machine actors, not end users.",
)
body(
    doc,
    "This scope is deliberately concrete: a control-plane security problem "
    "that already exists today, not a general AI safety concept.",
)

# --- 2. Threat model ---
h1(doc, "Threat Model", 2)
body(
    doc,
    "We assume the attacker has already obtained a valid credential or "
    "controls a legitimate agent, the realistic and hard case. AEGIS is "
    "built to catch them by behaviour rather than by credential validity. "
    "Each threat below is generated and detected in the current PoC.",
)

threat_rows = [
    ("T1", "Identity spoofing / impersonation",
     "Actor uses agent A's token but behaves like a different agent",
     "Fingerprint mismatch: wrong endpoint mix, timing, sequence for that identity"),
    ("T2", "Compromised agent",
     "A legitimate agent starts doing new things",
     "Drift from its own baseline: new endpoints, new methods, elevated error rate"),
    ("T3", "Reconnaissance / enumeration",
     "Scanning endpoints and IDs",
     "High cardinality of endpoints/targets, many 4xx errors, breadth over depth"),
    ("T4", "Volumetric abuse / DoS",
     "Flooding a Network Function",
     "Request-rate spike far above the agent's normal envelope"),
    ("T5", "Low and slow exfiltration",
     "Quiet, sustained data pulls",
     "Abnormal read/GET ratio and payload sizes, off-hours persistence"),
    ("T6", "Replay / sequence anomaly",
     "Valid calls issued in an invalid order",
     "Broken transition probabilities vs the agent's normal call graph (session state machine)"),
    ("T7", "Privilege / scope creep",
     "Touching Network Functions outside its role",
     "Calls to NFs never present in the agent's baseline scope"),
]
add_table(
    doc,
    ["ID", "Threat", "What it looks like", "Behavioural signal AEGIS keys on"],
    threat_rows,
    widths=[0.4, 1.4, 1.9, 2.7],
)
doc.add_paragraph()
body(
    doc,
    "All seven threats are currently detected in the working baseline "
    "(see Section 4 for results per threat).",
)

# --- 3. Architecture ---
h1(doc, "Architecture", 3)
body(
    doc,
    "AEGIS is a zero trust gate placed on every agent to Network Function "
    "request, following an OBSERVE, FINGERPRINT, SCORE, DECIDE pipeline. "
    "In production, this would run as an inline policy check at the edge "
    "(FASTedge).",
)

arch_rows = [
    ("1. Observe", "Parse each request and its metadata: agent id, method, "
     "target NF, endpoint, timestamp, payload size, status code. Assemble "
     "a per-agent request stream."),
    ("2. Fingerprint", "Compute a windowed behavioural feature vector for "
     "the agent and compare it against that agent's own known-good "
     "baseline."),
    ("3. Score", "Combine a deterministic rules layer (hard limits, "
     "forbidden transitions) with an unsupervised ML anomaly score "
     "(Isolation Forest, trained only on legitimate traffic) into a "
     "single risk value between 0 and 1."),
    ("4. Decide", "Apply thresholds to the risk score to produce PASS, "
     "STEP-UP or BLOCK, with a plain-language reason."),
]
add_table(doc, ["Stage", "What happens"], arch_rows, widths=[1.3, 5.1])
doc.add_paragraph()

h2(doc, "Behavioural fingerprint, feature set")
body(doc, "Computed per agent over a sliding window of recent requests:")
bullet(doc, "Volume / rate: requests per window, inter-arrival mean and variance")
bullet(doc, "Surface: distinct NFs, distinct endpoints, distinct target IDs (cardinality)")
bullet(doc, "Method mix: GET/POST/PUT/DELETE ratios, read vs write balance")
bullet(doc, "Sequence: transition probabilities over the endpoint call graph, "
             "how surprising the observed sequence is versus the agent's normal graph")
bullet(doc, "Errors: 4xx/5xx rate (recon and scope creep show up here)")
bullet(doc, "Payload: request/response size distribution")
bullet(doc, "Temporal: hour-of-day and off-hours activity versus the agent's usual pattern")

h2(doc, "Decision policy")
decision_rows = [
    ("Low", "PASS", "Behaves like its known-good self"),
    ("Medium", "STEP-UP", "Challenge: re-authentication, approval, or throttle"),
    ("High", "BLOCK", "Quarantine the identity, alert the SOC"),
]
add_table(doc, ["Risk", "Decision", "Meaning"], decision_rows, widths=[1.2, 1.2, 4.0])
doc.add_paragraph()
body(
    doc,
    "The gate sits inline on the request path in production (FASTedge policy "
    "check), or observes a mirror of SBI traffic in the current PoC (offline "
    "log replay).",
)

# --- 4. Current results ---
h1(doc, "Current Results", 4)
body(
    doc,
    "These results are from a working prototype, not a design target. They "
    "are measured on synthetic 5G SBA traffic (210k generated requests, 5 "
    "legitimate agent profiles including full PDU-session lifecycles, plus "
    "injected attacks T1 to T7), evaluated on 11,343 held-out request "
    "windows (60 second windows; decision thresholds STEP-UP at 0.5, BLOCK "
    "at 0.8).",
)

metrics_rows = [
    ("ROC-AUC", "0.992"),
    ("Precision", "0.790"),
    ("Recall (detection rate)", "0.983"),
    ("F1 score", "0.876"),
    ("False-positive rate on legit traffic", "0.83%"),
    ("ROC-AUC, ML only, no rules", "0.726"),
]
add_table(doc, ["Metric", "Value"], metrics_rows, widths=[3.5, 2.5])
doc.add_paragraph()

h2(doc, "Detection rate per threat")
per_threat_rows = [
    ("T1 Impersonation", "48", "100%"),
    ("T2 Compromise", "47", "100%"),
    ("T3 Recon", "56", "89%"),
    ("T4 Volumetric", "60", "100%"),
    ("T5 Exfiltration", "42", "100%"),
    ("T6 Sequence", "57", "100%"),
    ("T7 Scope creep", "39", "100%"),
]
add_table(doc, ["Threat", "Windows evaluated", "Detected"], per_threat_rows, widths=[2.5, 2.0, 1.5])
doc.add_paragraph()

h2(doc, "Gate decisions on the test set")
gate_rows = [
    ("PASS", "10,909"),
    ("STEP-UP", "55"),
    ("BLOCK", "379"),
]
add_table(doc, ["Decision", "Windows"], gate_rows, widths=[2.5, 2.0])
doc.add_paragraph()
body(
    doc,
    "Important caveat: this is a synthetic-first result. It demonstrates "
    "that the detection method works and is well calibrated, not that it "
    "has been validated against real network traffic patterns, seasonality "
    "or noise. That validation is exactly what real or anonymised data "
    "would give us.",
    italic=True,
)

# --- 5. Data specification ---
h1(doc, "Data Specification, What We Need From You", 5)
body(
    doc,
    "This section exists to help you decide what you can share with us, "
    "and on what terms, given the project timeline (Gate 2 on 22 September, "
    "Gate 3 on 15 October).",
)

h2(doc, "The field schema our detector already runs on")
body(
    doc,
    "Our synthetic generator and detector are built around the following "
    "per-request record. This is the shape of data we would need, whether "
    "synthetic or real:",
)
schema_rows = [
    ("ts", "Timestamp of the request"),
    ("agent_id", "Identity of the calling agent or automation"),
    ("nf", "Target Network Function (for example AMF, SMF, NRF, NEF, PCF, UDM)"),
    ("endpoint", "SBI service operation called (for example Nsmf_PDUSession/create)"),
    ("method", "HTTP method (GET/POST/PUT/DELETE)"),
    ("session_id", "Session or correlation identifier, where applicable"),
    ("resp_size", "Response payload size"),
    ("status", "HTTP status code returned"),
    ("label / attack_type", "Ground-truth tag, present in our synthetic data for evaluation only, not expected in real logs"),
]
add_table(doc, ["Field", "Description"], schema_rows, widths=[1.6, 4.4])
doc.add_paragraph()

h2(doc, "What we explicitly do not need")
bullet(doc, "No subscriber-identifying data (IMSI, MSISDN, user identity, or similar)")
bullet(doc, "No payload content or message bodies, only size and metadata")
bullet(doc, "No data plane / user traffic, only control-plane API calls")
body(
    doc,
    "The detector operates entirely on request metadata and timing, so the "
    "data we need is naturally low-sensitivity by design.",
)

h2(doc, "Options, in order of preference")
options_rows = [
    ("1", "Real SBI / API-gateway logs (even a limited time window)",
     "Highest value: lets us validate against real traffic patterns and calibrate thresholds honestly"),
    ("2", "Aggregated or anonymised logs (field-level, agent IDs pseudonymised)",
     "Good middle ground: preserves behavioural structure without exposing raw identity"),
    ("3", "A schema-confirmed sample or field distributions only (no full logs)",
     "Lets us tune our synthetic generator to match your real traffic shape"),
    ("4", "Stay fully synthetic",
     "No blockers for us either way, but the PoC stays a controlled demonstration rather than a validated one"),
]
add_table(doc, ["Option", "Description", "What it gives us"], options_rows, widths=[0.5, 2.8, 2.7])
doc.add_paragraph()
body(
    doc,
    "Whatever you are able to share, and under whatever access or review "
    "process you require, works for us. We are asking now so we can plan "
    "Gate 2 (22 September) around what will actually be available.",
)

# --- 6. Integration ask ---
h1(doc, "Integration Ask, FASTedge", 6)
body(
    doc,
    "The current PoC is a detector: it scores risk and shows PASS, STEP-UP "
    "or BLOCK on a dashboard, but does not itself stop a request. Whether "
    "the Gate 3 demo (15 October) can show real inline enforcement, rather "
    "than monitoring only, depends on one question:",
)
body(
    doc,
    "Does FASTedge expose a hook where a policy check can run inline on "
    "the request path, so that a BLOCK decision from AEGIS can actually "
    "stop the call, not just flag it after the fact?",
    italic=True,
)
body(
    doc,
    "If such a hook exists, we would want to understand its request/response "
    "contract (what is passed in, what a policy check is expected to "
    "return, and the latency budget available) so we can design the "
    "integration correctly from Gate 2 onward, rather than retrofitting it "
    "at the end.",
)
body(
    doc,
    "If no such hook exists yet, we will demonstrate the gate as a passive "
    "observe-and-alert system feeding a SOC workflow, which is still a "
    "complete and useful PoC, just a different one to build toward.",
)

doc.add_paragraph()
h2(doc, "Related question")
body(
    doc,
    "Alongside the data and integration questions above, it would help to "
    "know which agent or automation types are most security-relevant to "
    "you today (orchestration, OSS jobs, closed-loop automation, external "
    "NEF consumers), so we can prioritise the agent and threat profiles we "
    "build out for Gate 2 to match your real risk surface.",
)

doc.add_paragraph()
footer = doc.add_paragraph()
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = footer.add_run(
    "AEGIS, Zero Trust Identity for AI Agents, Team 4, 5G Academy 2026"
)
run.font.size = Pt(9)
run.font.color.rgb = GREY

OUT.parent.mkdir(exist_ok=True)
doc.save(OUT)
print(f"Saved to {OUT}")
