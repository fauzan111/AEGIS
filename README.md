# AEGIS - Zero-Trust Identity for AI Agents on the Network

**5G Academy 2026 - Fastweb + Vodafone - Team 4**
Topic 2 - Security on Network - Assigned by the Committee on 27 July 2026.

**Live project page:** https://fauzan111.github.io/AEGIS/
**Live dashboard:** https://aegis5gacademy.streamlit.app/

## The idea in one line

As AI agents and automations increasingly act on 5G network control services, a valid credential alone can't prove an agent is what it claims to be. AEGIS builds a **behavioural fingerprint** of each legitimate agent and continuously scores every request against it: a **zero-trust gate for machine identities**.

## The problem

Orchestration tools, closed-loop automation, and AI copilots now call 5G Network Functions directly over the network's control-plane APIs (the Service-Based Interface). A stolen token or a compromised automation still passes normal authentication, the credential is valid, but the actor behind it isn't. Classic authentication cannot answer "is this really our agent, behaving the way it always does?" AEGIS answers that question, aligned with NIST SP 800-207 zero-trust principles: never trust, always verify, verify continuously.

## Project progress

### Gate 1 - Technologies, Planning & Feasibility (complete)

Established the technology approach (behavioural fingerprinting plus rules and ML anomaly detection on the 5G Service-Based Architecture), the project schedule, technical feasibility, and the economic and business case for a zero-trust gate on machine identities.

### Gate 2 - Technical Solution & Architecture (complete)

Delivered the full technical solution: a concrete system architecture, a working end-to-end implementation, and a complete numerical performance analysis, benchmarked against real-world detection research (published network intrusion detection studies, industry SOC false-positive data, and behavioural-analytics literature) rather than tuned for the highest possible numbers.

- **Architecture:** an OBSERVE to FINGERPRINT to SCORE to DECIDE zero-trust gate, covering all seven modelled threats (identity spoofing, compromised agents, reconnaissance, volumetric abuse, slow exfiltration, sequence anomalies, and scope creep).
- **Results, on a held-out test set of about 11,365 request windows:** ROC-AUC 0.965, recall 90.7%, false-positive rate 1.4%, with detection rate intentionally uneven across threats (76 to 100 percent) rather than a uniform, implausible 100 percent everywhere, matching how real detection systems perform in the published research.
- **A live dashboard:** real-time risk scoring, a network-topology view showing which agents are touching which Network Functions, a live-replay mode, and an incident inspector that explains why each decision was made in plain language.
- **A rigorous operating-point justification:** a full ROC and threshold-sensitivity analysis behind the chosen decision thresholds, not just a picked number.

Full Gate 2 report: `docs/GATE-2.md` (also available as a Word document).

### Next: Gate 3 - Proof of Concept (Final)

The final working Proof of Concept demonstration and video, closing the remaining detection gaps, and integrating real network traffic if Fastweb/Vodafone are able to provide it.

## Team

Fauzan Ejaz (Captain), Adithya Zacharia Valavi, Ghazanfar Anees Siddiqui, Llagami Tedi

## Where to find things

- `docs/` - Gate reports, threat model, and architecture documentation
- `slides/` - Gate presentation decks and official report submissions
- `reports/` - evaluation charts, metrics, and the architecture diagram
- `src/` - source code for the traffic generator, detector, and dashboard
- `data/` - the synthetic dataset used for evaluation
