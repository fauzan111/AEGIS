# GATE 2 - Technical Solution & Architecture

**Project:** AEGIS - Zero-Trust Identity for AI Agents on the Network
**Group:** Team 4 · 5G Academy 2026 · Fastweb + Vodafone
**Topic:** Topic 2 - Security on Network

---

## 2.1 Proposed Technical Solution

As AI agents, orchestration bots, and closed-loop automations increasingly issue commands directly to 5G network control services, classical authentication is no longer sufficient to establish trust. A stolen token, a leaked client certificate, or a compromised automation account will still **pass authentication** - the credential is valid - even though the actor behind it is not the legitimate agent. Classic AAA answers *"is the credential valid?"*. It cannot answer *"is this really the agent we onboarded, behaving the way it always behaves?"*

**AEGIS answers that second question.** It is a **zero-trust gate for machine identities**: it builds a **behavioural fingerprint** of each legitimate agent from how it actually calls the network's APIs, and continuously scores every new request against that fingerprint - aligned with NIST SP 800-207 zero-trust principles (*never trust, always verify; verify continuously; assume breach*).

> **One-line pitch:** credentials prove what you have; AEGIS verifies how you behave.

**Scope.** AEGIS targets service/automation agents (orchestration, closed-loop automation, OSS/BSS jobs, API clients) calling **network control APIs**, modelled on the 5G Service-Based Architecture (SBA) / Service-Based Interface (SBI) - e.g. AMF, SMF, NRF, NEF, PCF, UDM. End-user devices, the data plane, and general "AI safety" are explicitly out of scope: AEGIS guards the **control-plane API surface used by machine actors**, which keeps the problem concrete and solvable within the PoC timeline rather than open-ended.

**The solution in one pipeline:**

```
OBSERVE request patterns & metadata (id, timing, call sequence, payload shape)
   → FINGERPRINT a known-good behavioural baseline per agent
   → SCORE with rules + an ML anomaly/spoof score
   → DECIDE  PASS / STEP-UP / BLOCK   (zero-trust gate dashboard)
```

**Threats the solution is built to catch.** We assume an attacker who has already obtained a valid credential (the realistic case) or controls a legitimate agent, and must therefore be caught by *behaviour*, not by credential checks:

| # | Threat | Behavioural signal AEGIS keys on |
|---|--------|----------------------------------|
| T1 | Identity spoofing / impersonation | Fingerprint mismatch: wrong endpoint mix, timing, sequence for that identity |
| T2 | Compromised agent | Drift from its own baseline: new endpoints, new methods, elevated error rate |
| T3 | Reconnaissance / enumeration | High cardinality of endpoints/targets, many 403/404s, breadth over depth |
| T4 | Volumetric abuse / DoS | Request-rate spike far above the agent's normal envelope |
| T5 | Low-and-slow exfiltration | Abnormal read/GET ratio + payload sizes, off-hours persistence |
| T6 | Replay / sequence anomaly | Broken call-sequence pattern vs the agent's normal call graph |
| T7 | Privilege / scope creep | Calls to NFs never in the agent's baseline scope |

This directly extends the Gate 1 feasibility case: the technology (behavioural fingerprinting + anomaly detection), the risks, and the economic rationale (enabling safe automation, NIS2/GDPR/EU-AI-Act audit evidence) were validated at Gate 1. Gate 2 delivers the concrete architecture (§2.2, with a full system diagram), a working implementation (§2.3), and numerical proof that the approach works (§2.4) - the three things Gate 1 could only describe as intent.

---

## 2.2 Architecture

AEGIS is structured as a four-stage pipeline sitting logically in front of the network's control-plane APIs. Every request an agent sends to a Network Function is observed by the gate before (in production) or in parallel with (in the PoC) reaching the NF.

**System architecture diagram:**

![AEGIS zero-trust gate architecture: agents and Network Functions at the top, the OBSERVE → FINGERPRINT → SCORE → DECIDE pipeline in the center with the rules layer, ML layer, and known-good profile store feeding into it, and the PASS / STEP-UP / BLOCK gate dashboard at the bottom leading to the enforcement point](../reports/aegis_architecture_diagram.png)

*Figure 2.1 - AEGIS system architecture. Source files for editing: `reports/aegis_architecture_diagram.mmd` (Mermaid source, single source of truth) and `reports/aegis_architecture_diagram.excalidraw` (editable scene - open at excalidraw.com to adjust layout without touching the source). Color key: blue = external actors/enforcement boundary, dark slate = the four pipeline stages, light teal = the rules/ML/profile-store components feeding SCORE, and the PASS (teal) / STEP-UP (amber) / BLOCK (red) decision outcomes.*

Textual walkthrough of the same flow, for reference:

```
        Agents / automations                 Network Functions (SBA)
   (orchestration, OSS, API clients, LLM copilots)   AMF · SMF · NRF · NEF · PCF · UDM …
                    │
                    │  request (agent id, method, NF, endpoint, timestamp, payload size)
                    ▼
        ┌───────────────────┐
        │   1. OBSERVE       │  parse request + metadata; assemble a per-agent request stream
        └─────────┬──────────┘
                   ▼
        ┌───────────────────┐        ┌────────────────────────────┐
        │  2. FINGERPRINT    │ <───── │   Known-good profile store │
        │  windowed feature  │        │  (behavioural baseline per │
        │  vector per agent  │ ─────► │        agent identity)     │
        └─────────┬──────────┘        └────────────────────────────┘
                   ▼
        ┌───────────────────┐
        │    3. SCORE        │  rules (hard limits) + ML anomaly score  →  risk in [0,1]
        └─────────┬──────────┘
                   ▼
        ┌───────────────────┐
        │    4. DECIDE       │  thresholds  →  PASS / STEP-UP / BLOCK  (+ plain-language "why")
        └─────────┬──────────┘
                   ▼
        Zero-trust gate dashboard  ·  enforcement point (inline at the edge / FASTedge in production)
```

**Component description:**

- **OBSERVE.** Every request is parsed into a normalized event: agent identity, HTTP method, target Network Function, endpoint, timestamp, and payload size. Events are grouped into a per-agent stream, which is the unit the rest of the pipeline operates on.
- **FINGERPRINT.** Requests are aggregated into sliding time windows (60 seconds in the PoC) and turned into a feature vector per agent, per window:
  - *Volume / rate* - requests per window, inter-arrival mean & variance
  - *Surface* - distinct NFs, endpoints, and target IDs touched (cardinality)
  - *Method mix* - GET/POST/PUT/DELETE ratios, read-vs-write balance
  - *Sequence* - how surprising the observed call order is versus the agent's normal call graph
  - *Errors* - 4xx/5xx rate (lights up on recon and scope-creep)
  - *Payload* - request/response size distribution
  - *Temporal* - hour-of-day / off-hours activity vs. the agent's usual pattern
  - *Cross-window breadth* - a rolling union of endpoints/NFs and error count over the trailing 5 minutes per agent, so reconnaissance spread thin enough to look quiet in any single 60-second window is still caught once its accumulated breadth is considered

  These vectors are compared against a **known-good profile store** - the behavioural baseline built for each legitimate agent identity during onboarding/training.
- **SCORE.** Two layers run in parallel and are fused:
  - *Rules layer* (fast, explainable): hard caps and forbidden transitions - e.g., an agent touching an NF outside its onboarded scope is flagged immediately. Includes a **session-state machine** that tracks PDU-session lifecycle per agent to catch orphaned session update/release calls (T6), and **rolling 5-minute accumulators** (cross-window endpoint/NF breadth, error count, and peak payload size) that catch agents whose *cumulative* behaviour over a short horizon is anomalous even when no single window is large enough to trip a volume-based check - the mechanism that makes reconnaissance (T3) and low-and-slow exfiltration (T5) detectable at all, since both are attacks that are, by definition, too sparse per-window to see otherwise.
  - *ML layer* (unsupervised): an **Isolation Forest**, trained only on legitimate traffic (no labelled attacks needed), scores how anomalous a window's feature vector is relative to that agent's own history. It only engages once an agent has accumulated enough recent traffic (≥10 requests in the trailing 5 minutes) for a fingerprint to be statistically meaningful - below that, only the deterministic rules apply.
  - *Fusion:* `risk = max(rule_score, ml_score)`, giving the rules layer veto power on hard violations while letting the ML layer catch subtler drift.
  - *Operating point:* thresholds and rule sensitivities are deliberately tuned for a **realistic false-positive budget (~1.5%)** rather than maximum sensitivity - see §2.4 for why this means detection is intentionally not uniform across threats.
- **DECIDE.** The fused risk score is mapped to a three-way decision:

  | Risk | Decision | Meaning |
  |------|----------|---------|
  | Low | **PASS** | Behaves like its known-good self |
  | Medium | **STEP-UP** | Challenge: re-authentication / approval / throttling |
  | High | **BLOCK** | Quarantine the identity, alert the SOC |

- **Trust boundary.** Every request from an agent to a Network Function crosses the AEGIS gate. In production, the gate is envisioned as an **inline policy check at the edge (FASTedge)**; for the PoC, it operates as an offline/log-replay analysis over synthetic SBI-style traffic, which is architecturally equivalent but avoids requiring live network access.
- **Dashboard / enforcement surface.** A Streamlit application exposes, per agent: current risk, PASS/STEP-UP/BLOCK status, a breakdown of detections by threat type, and an incident inspector with a plain-language explanation of *why* a request was flagged - the human-facing enforcement and audit surface for the gate.

---

## 2.3 Implementation Strategy

**Methodology.** AEGIS is built **bottom-up, PoC-first, and evaluation-driven** - the ML/security equivalent of test-driven development: no rule or model change is kept unless it's immediately re-scored against the full labelled dataset and shown to improve (or at least not regress) the numbers in §2.4. Each of the four architectural stages (§2.2) is a separately runnable, separately verifiable script, so the pipeline can be inspected and debugged stage-by-stage rather than as one opaque system. This is also why the two design bugs described below (step 7) were caught at all - an evaluation-driven loop surfaces a rule that's "too easy" or "too eager" the same day it's introduced, rather than at Gate review time.

**Tools & platforms:**

| Layer | Tool / platform | Role |
|---|---|---|
| Language/runtime | Python 3.12 | Single language across generation, detection, and dashboard for a small team to maintain |
| Data generation & processing | pandas, NumPy | Synthetic SBI-traffic generation, windowing, feature engineering |
| Anomaly detection | scikit-learn (Isolation Forest) | Unsupervised ML layer, trained on legitimate traffic only; one-class SVM / autoencoder identified as alternatives for later hardening |
| Visualization / gate UI | Streamlit, Matplotlib | Live zero-trust gate dashboard (deployed on Streamlit Community Cloud) and evaluation charts |
| Deck/report tooling | `python-docx`, `python-pptx` | Reproducible generation/patching of the Gate decks and written reports |
| Delivery | Git/GitHub, GitHub Pages | Version control and a public showcase site linking to the live dashboard |

**Implementation phases:**

| Phase | Output | Primary file(s) |
|---|---|---|
| 1. Synthetic environment | Labelled SBI-style traffic, 5 agents, T1-T7 | `src/generate_synthetic_traffic.py` → `data/aegis_traffic.csv` |
| 2. Fingerprinting | Per-agent windowed feature vectors | `src/aegis_detect.py` (`build_windows`, `add_rolling_recon_features`) |
| 3. Rules layer | Deterministic scope/session/rolling checks | `src/aegis_detect.py` (`rule_score`, `flag_orphans`) |
| 4. ML layer | Isolation Forest fit on legit-only traffic | `src/aegis_detect.py` (`ml_scores`) |
| 5. Fusion & decision | Risk scoring, PASS/STEP-UP/BLOCK | `src/aegis_detect.py` (`main`, `decision`) |
| 6. Dashboard | Live zero-trust gate UI | `src/aegis_dashboard.py` |
| 7. Evaluation & iteration | Metrics, charts, bug-fixing loop | `reports/aegis_baseline_metrics.md`, `reports/aegis_eval.png` |

**Step-by-step implementation:**

1. **Synthetic traffic generation** (`src/generate_synthetic_traffic.py`) - produces `data/aegis_traffic.csv`: **210,000 requests** across **5 legitimate agent profiles**, each with realistic PDU-session lifecycle behaviour, plus the seven threat scenarios (T1-T7) injected as labelled anomalous segments. This removed the dependency on obtaining real operator logs and let the whole pipeline be built and validated immediately.
2. **Feature engineering / fingerprinting** - the raw request stream is windowed (60s windows) and turned into the behavioural feature vectors described in §2.2 (volume, surface, method mix, sequence, errors, payload, temporal), computed per agent.
3. **Rules layer** - deterministic, explainable checks: scope violations (NF outside baseline), hard-rate caps, and a **session-ID state machine** that tracks legitimate PDU-session open/update/release transitions per agent to catch sequence anomalies (T6) without false-firing on legitimate concurrent sessions - an issue found and fixed during iteration (an earlier window-count heuristic was replaced once it proved to misfire on legitimate bursty traffic).
4. **ML layer** - an Isolation Forest is fit **only on legitimate traffic**, with a held-out calibration split used to set operating thresholds, so the model needs no labelled attack data to train (only to evaluate).
5. **Fusion & decision policy** (`src/aegis_detect.py`) - rule score and ML anomaly score are fused (`max`) into a single risk value, thresholded into PASS / STEP-UP / BLOCK, and written out as `reports/scored_windows.csv`, `reports/aegis_baseline_metrics.md`, and `reports/aegis_eval.png`.
6. **Dashboard** (`src/aegis_dashboard.py`) - a Streamlit zero-trust gate UI showing per-agent risk, PASS/STEP-UP/BLOCK decisions, per-threat detection breakdown, and an incident inspector with a plain-language "why," running against the scored output.
7. **Evaluation & iteration** - metrics (ROC-AUC, precision, recall, F1, false-positive rate, per-threat detection rate) are recomputed after every change to the rules/ML layers. This iterative loop surfaced and fixed several concrete issues during development, not just tuning cosmetics:
   - An earlier T6 window-count heuristic was replaced with a session-ID state machine after it was found to false-fire on legitimate bursty traffic.
   - T3 (reconnaissance) and T5 (exfiltration) are naturally sparse per window - inspecting the missed cases showed 1-3 requests per 60-second window, too few to ever trip a single-window statistical check. Rolling 5-minute accumulators (breadth, error count, peak payload - §2.2) fixed this class of miss generically, rather than with a one-off rule per threat.
   - **A more subtle bug:** the initial T2 (compromise) and T5 (exfiltration) attack scenarios both had the injected agent call a Network Function outside its own onboarded scope. That's indistinguishable from T7 (scope creep) as far as the rules layer is concerned, so both were trivially caught by the deterministic scope-violation rule at ~100% - not by the drift/payload-anomaly logic they were meant to test. Redesigning both scenarios to stay **within** the attacking agent's own authorized scope (a more realistic model of a compromised or exfiltrating agent, which doesn't usually announce itself by reaching for resources it was never granted) forced detection to rely on the intended statistical signal, and immediately dropped their measured detection rate to a realistic level - this is the origin of the non-uniform per-threat numbers in §2.4.
   - Decision thresholds were then re-tuned from an initial "catch everything" setting down to a **realistic false-positive budget (~1.5%)**, consistent with published SOC benchmarks where even well-tuned detection sits in the low single digits, not zero (see §2.4 sources).

Both the T6 heuristic fix and the T2/T5 scope-confound fix above are direct products of the evaluation-driven loop described at the top of this section: neither would have surfaced from code review alone, only from re-scoring against the full labelled set the same day the change was made.

---

## 2.4 Numerical Performance Analysis

**Benchmarking against real-world detection systems, not just internal targets.** Before finalizing the operating point, we researched how comparable systems perform in practice, since a PoC that reports 100% detection on everything is a red flag to anyone who has looked at production security data, not a strength:
- Published NIDS studies on CICIDS2017/UNSW-NB15 consistently show **volumetric/DoS attacks detected at 97-99.8%** (large, unambiguous signal) while **reconnaissance and other low-frequency attack classes detect far lower** unless heavy class-balancing is applied - one calibration study only raised a minority class from 0% to 80% recall with special techniques.
- Industry SOC data (Microsoft/Omdia *State of the SOC 2025*, SANS *2025 Detection & Response Survey*) puts **typical false-positive rates at 46-83%**, with **"elite," well-tuned SOCs at under 10%**, and under 5% considered excellent - a 0% false-positive rate is not a realistic target for any behavioural detector.
- UEBA/insider-threat research shows a hard precision/recall tradeoff: models reporting near-perfect recall (e.g., an LSTM autoencoder at 1.00 recall on insider threats) do so by sacrificing precision to as low as 0.54; **low-and-slow exfiltration is consistently the hardest category**, consistent with the ~77-day average real-world dwell time cited for insider threats.

We therefore tuned AEGIS's decision thresholds and rule sensitivities for a **realistic false-positive budget (~1.5%)** - in the "well-tuned, not superhuman" range - rather than for maximum sensitivity, and treated a non-uniform, threat-dependent detection rate as the expected, correct outcome rather than something to eliminate.

**Test set:** ~11,365 held-out windows (11,010 legitimate, 355 attack), 60-second window size, decision thresholds **STEP-UP ≥ 0.6** and **BLOCK ≥ 0.85**.

**Headline metrics (rules + ML fused):**

| Metric | Value |
|---|---|
| ROC-AUC | **0.965** |
| Precision | 0.672 |
| Recall (detection rate) | **0.907** |
| F1 score | 0.772 |
| False-positive rate (legit traffic flagged) | **1.43%** |
| ROC-AUC - ML only (no rules) | 0.721 |

These sit comfortably inside the range reported in the literature above: an FPR under 2% is "elite-SOC" territory, not the 0.0X% that would raise suspicion of a leaky evaluation, and a precision of 0.67 is in line with (in fact better than) several published UEBA results that trade precision for recall.

**Detection rate per threat type - deliberately not uniform:**

| Threat | Windows | Detected | Why this level |
|---|---|---|---|
| T4 - Volumetric abuse / DoS | 60 | **100%** | Loud rate spike - the easiest signal in the literature |
| T7 - Privilege / scope creep | 35 | **100%** | A deterministic policy/ACL check, not a statistical inference - real access-control violation logging is expected to be complete by design |
| T1 - Identity spoofing / impersonation | 54 | 96% | Mostly a scope mismatch (strong signal), with a stealthier in-scope-probing variant mixed in that is genuinely harder |
| T6 - Replay / sequence anomaly | 57 | 93% | Session-state violations are strong evidence, but an isolated single anomaly without corroborating context is treated as ambiguous (could be a benign retry) |
| T2 - Compromised agent | 43 | 91% | Drift is confined to the agent's own onboarded scope (no free scope-violation signal), so detection relies on genuine behavioural drift |
| T3 - Reconnaissance / enumeration | 60 | 80% | Enumeration within an agent's own authorized scope, the hardest class in published NIDS benchmarks |
| T5 - Low-and-slow exfiltration | 46 | 76% | The hardest threat category industry-wide; caught only via a rolling cross-window payload-size accumulator, not any single-window signal |

Two of these threats (T4, T7) are legitimately near-100% because they are *not* statistical detection problems - a rate cap and a scope/ACL check are deterministic lookups, and real production systems are expected to catch these essentially every time. The other five sit in a genuine 76-96% spread that tracks the strength of their underlying behavioural signal, matching the pattern in every benchmark cited above: loud beats subtle, and diffuse/low-and-slow attacks are always the hardest.

**Gate decisions on the test set:**

| Decision | Windows | Share |
|---|---|---|
| PASS | 10,886 | 95.8% |
| STEP-UP | 148 | 1.3% |
| BLOCK | 331 | 2.9% |

**Interpretation:**
- A **1.43% false-positive rate** sits inside the "well-tuned SOC" band from the industry data above (elite <10%, excellent <5%) without claiming an implausible near-zero rate.
- **90.7% recall** means roughly 9 in 10 attacks are caught before reaching "PASS" - strong, but honestly short of perfect, which is consistent with recall figures reported for real behavioural/UEBA systems at comparable false-positive budgets.
- The **precision of 0.67** reflects the same recall/precision tension documented across the UEBA literature: catching subtle threats (T3, T5) at a low false-positive rate necessarily means the gate occasionally flags legitimate but unusual behaviour, which the STEP-UP tier (re-authentication, not an outright block) is designed to absorb without disrupting the agent outright.
- These results still substantially exceed the two baselines identified in the threat model (a naive rate-threshold rule, and a random gate).

---

## 2.5 Expected Proof of Concept (PoC)

Unlike a purely forward-looking PoC description, AEGIS already has a **working, demonstrable baseline** implementing the full pipeline end to end on synthetic data, matching the architecture in Figure 2.1 (§2.2) exactly, not a simplified stand-in for it.

**Live demo script.** Walking through the actual Streamlit dashboard (`src/aegis_dashboard.py`), the Gate 2 demonstration follows the same path a reviewer's eye would take through the architecture diagram:

1. **Agent overview.** Open the dashboard and show all 5 legitimate agents with their live risk scores, all sitting in PASS, matching their known-good baseline (the FINGERPRINT stage in Figure 2.1).
2. **Trigger a threat.** Select a scored window for one of T1-T7 (e.g. T4 volumetric) and show the dashboard flip that agent to BLOCK in real time.
3. **Open the incident inspector.** Show the plain-language "why": which feature tripped (rate spike, scope violation, rolling breadth, and so on), tracing directly back to the rules layer or ML layer box in the diagram that produced it.
4. **Repeat across threat types.** Cycle through a spoofing case (T1), a quiet within-scope drift case (T2), and a low-and-slow exfiltration case (T5), to show the full spread of detection difficulty from §2.4 live, not just the easy cases.
5. **Show the numbers.** Bring up `reports/aegis_baseline_metrics.md` and `reports/aegis_eval.png` alongside the dashboard: ROC-AUC, recall, false-positive rate, and the per-threat table, so the qualitative demo and the quantitative evidence are shown side by side.
6. **Make the zero-trust gap concrete.** Point to a flagged window where the request used a fully valid credential (authentication succeeded) but was still blocked on behaviour, the exact gap in classical AAA that AEGIS closes (§2.1).

**PoC readiness at Gate 2:**

| Capability | Status |
|---|---|
| Synthetic SBI-style traffic generator (5 agents, T1-T7) | Done |
| Fingerprinting, rules layer, ML layer, fusion, decision policy | Done |
| Live dashboard with incident inspector | Done |
| Numerical evaluation (ROC-AUC, recall, precision, FPR, per-threat) | Done |
| ROC operating-point / threshold sensitivity analysis | Done (`reports/aegis_threshold_sensitivity.png`) |
| Real M2M / API-gateway traffic | Not yet, synthetic only, blocked on Fastweb/Vodafone data access |

**What this validates:** that a behavioural-fingerprint plus rules/ML gate is a practical way to add a continuous-verification layer on top of existing credential-based authentication for machine identities on 5G control-plane APIs, trainable without labelled attacks, and numerically effective at a realistic operating point, without requiring changes to the underlying Network Functions themselves.

**Path to Gate 3 (what the PoC does not yet cover, to be closed next):**
- Closing the gap on the hardest threats (T3 recon at 80%, T5 exfiltration at 76%) with richer features, e.g. per-target-ID cardinality, not just per-endpoint, rather than pushing the current rolling accumulators further and risking the false-positive budget.
- Integrating real M2M / API-gateway logs if made available by Fastweb/Vodafone, as an upgrade path from the fully synthetic PoC: real traffic will validate whether these numbers hold or whether the operating point needs re-tuning. This is the one open item outside our control, and is the direct ask carried over from the threat model's open questions for Fastweb.
- Recording the final video demonstration (Gate 3 §3.4) from the live demo script above.
- Expanding the number of agent and attack variants to stress-test generalization beyond the current 5-agent / 7-threat catalogue.
