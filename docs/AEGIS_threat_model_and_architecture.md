# AEGIS - Threat Model & Architecture

**Zero-Trust Identity for AI Agents on the Network**
5G Academy 2026 · Fastweb + Vodafone · Team 4 · Topic 2 (Security)

---

## 1. Why this problem, now

The network is becoming **AI-native**: closed-loop automation, orchestration
agents, and increasingly LLM-driven copilots issue commands to network control
services instead of humans. In 5G this happens over the **Service-Based
Architecture (SBA)** - Network Functions (AMF, SMF, NRF, NEF, PCF, UDM, …) expose
REST/HTTP2 APIs on the **Service-Based Interface (SBI)**, and automations call
them the same way a human operator's tooling would.

This creates a new identity problem. A stolen token, a leaked client
certificate, or a compromised automation account **passes authentication** - the
credential is valid - while the *actor behind it* is not. Classic AAA
(authentication/authorization) answers **"is the credential valid?"** It does not
answer **"is this really the agent we onboarded, behaving the way it always
behaves?"**

**AEGIS answers the second question.** It is a **zero-trust gate for machine
identities**: it learns each legitimate agent's behavioural fingerprint and
scores every request against it, continuously - aligned with NIST SP 800-207
zero-trust principles (*never trust, always verify; verify continuously; assume
breach*).

> One-line pitch: *credentials prove what you have; AEGIS verifies how you behave.*

---

## 2. Scope (deliberately concrete - not "general AI security")

- **In scope:** service/automation **agents** (orchestration, closed-loop
  automation, OSS/BSS jobs, API clients) that call **network control APIs** -
  modelled on the 5G SBA / SBI.
- **Out of scope for the PoC:** end-user devices, the data plane / user traffic,
  and general "AI safety." AEGIS guards the **control-plane API surface** used by
  machine actors.

Keeping the scope to *orchestration/API agents on network control services* is
what stops this reading as futuristic - it is a control-plane security problem
that exists today.

---

## 3. Assets & trust boundaries

| Asset | Why it matters |
|-------|----------------|
| Network Function control APIs (SBI) | Direct control over sessions, policy, subscribers, slices |
| Agent identities (tokens / certs) | The thing that gets stolen or impersonated |
| Behavioural baselines (fingerprints) | AEGIS's ground truth - must be integrity-protected |
| The gate's decisions | Enforcement point - a bypass defeats the control |

**Trust boundary:** every request from an agent to an NF crosses the AEGIS gate.
The gate sits inline (production vision: an **inline policy check at the edge /
FASTedge**) or observes a mirror of the SBI traffic (PoC: offline log replay).

---

## 4. Adversary model & threat catalogue

We assume an attacker who has **already obtained a valid credential** (the hard,
realistic case) or controls a legitimate agent. AEGIS must catch them by
*behaviour*. Each threat below is something the PoC generates and detects.

| # | Threat | Behavioural signal AEGIS keys on |
|---|--------|----------------------------------|
| T1 | **Identity spoofing / impersonation** - actor uses agent A's token but behaves like a different agent | Fingerprint mismatch: wrong endpoint mix, timing, sequence for that identity |
| T2 | **Compromised agent** - a legit agent starts doing new things | Drift from its own baseline: new endpoints, new methods, elevated error rate |
| T3 | **Reconnaissance / enumeration** - scanning endpoints, IDs | High cardinality of endpoints/targets, many 403/404s, breadth over depth |
| T4 | **Volumetric abuse / DoS** - flooding an NF | Request-rate spike far above the agent's normal envelope |
| T5 | **Low-and-slow exfiltration** - quiet, sustained data pulls | Abnormal read/GET ratio + payload sizes, off-hours persistence |
| T6 | **Replay / sequence anomaly** - valid calls in an invalid order | Broken Markov transition probabilities vs the agent's normal call graph |
| T7 | **Privilege / scope creep** - touching NFs outside its role | Calls to NFs never in the agent's baseline scope |

This catalogue maps cleanly onto what the AI-Native-Security lecture called
**L7 anomaly / threat propagation** and onto the **Zero-Trust Architecture**
material from the Cybersecurity course.

---

## 5. Architecture - OBSERVE → FINGERPRINT → SCORE → DECIDE

```
        Agents / automations                 Network Functions (SBA)
        (orchestration, OSS,        ┌────────────────────────────────┐
         API clients, copilots)     │  AMF · SMF · NRF · NEF · PCF …  │
                │                   └────────────────────────────────┘
                │  request (id, method, NF, endpoint, ts, size)
                ▼
        ┌───────────────┐
        │  1. OBSERVE   │  parse request + metadata; assemble per-agent stream
        └──────┬────────┘
               ▼
        ┌───────────────┐        ┌──────────────────────────┐
        │ 2. FINGERPRINT│ <───── │  Known-good profile store │
        │  windowed     │        │  (behavioural baseline    │
        │  feature vec  │ ─────► │   per agent identity)     │
        └──────┬────────┘        └──────────────────────────┘
               ▼
        ┌───────────────┐
        │  3. SCORE     │  rules (hard limits) + ML anomaly score  → risk 0..1
        └──────┬────────┘
               ▼
        ┌───────────────┐
        │  4. DECIDE    │  thresholds → PASS / STEP-UP / BLOCK
        └──────┬────────┘   (+ optional "why" explanation)
               ▼
      zero-trust gate dashboard  ·  enforcement (inline at FASTedge in prod)
```

### Behavioural fingerprint - the feature set
Computed per agent over a sliding window of recent requests:

- **Volume / rate:** requests per window, inter-arrival mean & variance.
- **Surface:** distinct NFs, distinct endpoints, distinct target IDs (cardinality).
- **Method mix:** GET/POST/PUT/DELETE ratios; read-vs-write balance.
- **Sequence:** transition probabilities over the endpoint call graph (Markov) -
  how *surprising* the observed sequence is vs the agent's normal graph.
- **Errors:** 4xx/5xx rate (recon and scope-creep light up here).
- **Payload:** request/response size distribution.
- **Temporal:** hour-of-day / off-hours activity vs the agent's usual pattern.

### Scoring
- **Rules layer** (fast, explainable): hard caps and forbidden transitions -
  e.g. an agent touching an NF outside its onboarded scope → immediate flag.
- **ML layer** (unsupervised, per behaviour): **Isolation Forest** as the
  baseline anomaly detector (one-class SVM / autoencoder as alternatives),
  trained **only on legitimate traffic** so it needs no labelled attacks. Output
  a normalised anomaly score.
- **Fusion:** `risk = max(rule_score, ml_score)` → mapped to a decision.

### Decision policy
| Risk | Decision | Meaning |
|------|----------|---------|
| low | **PASS** | behaves like its known-good self |
| medium | **STEP-UP** | challenge: re-auth / require approval / throttle |
| high | **BLOCK** | quarantine the identity, alert the SOC |

---

## 6. PoC scope (what we commit to by 15 October)

Build a **rules + ML classifier** on **synthetic agent/API traffic** with a few
legit-agent profiles and injected spoofed/anomalous behaviour, and demo the
**verify-vs-spoof scoring gate (PASS / STEP-UP / BLOCK) live**. Explicitly a
**telecom-security prototype on synthetic logs** - that is what keeps it grounded,
not futuristic.

- **Inputs:** generated SBI-style request logs (this repo's generator).
- **Core:** fingerprint features → Isolation Forest + rules → risk → decision.
- **Output:** a dashboard showing, per agent, its baseline vs live behaviour and
  the gate decision, plus a **numerical performance analysis** (precision/recall,
  ROC-AUC, per-attack detection rate, false-positive rate) - the Gate 2 evidence.

## 7. Numerical evaluation plan (Gate 2)
- **Labelled test set:** each synthetic request tagged legit/attack + attack type.
- **Metrics:** precision, recall, F1, ROC-AUC (overall); **detection rate per
  attack type (T1–T7)**; **false-positive rate on legit traffic** (adoption
  killer if high); decision latency per request.
- **Baselines to beat:** a naive rate-threshold rule; a random gate.

## 8. Standards & course hooks (talking points)
- **NIST SP 800-207** Zero-Trust Architecture (continuous verification).
- **3GPP SBA / SBI** - the realistic API surface agents call.
- **TM Forum / closed-loop (OODA)** - AEGIS is the *guardrail* on the autonomous
  network the Fastweb lecture describes.
- Course anchors: Zero-Trust Architectures (Cybersecurity), ML-based intrusion
  detection & L7 anomaly (AI-Native Security), Trustworthy-AI/XAI (the "why
  blocked" explainer).

## 9. Open questions for Fastweb (Sept 2)
1. Is there **real M2M / API-gateway / SBI traffic** we could model, or should we
   stay fully synthetic for the PoC?
2. Does **FASTedge** expose a hook for an **inline policy check** (so the gate can
   enforce, not just observe)?
3. Which agent/automation types are most security-relevant to you today
   (orchestration, OSS jobs, closed-loop automation, external NEF consumers)?
