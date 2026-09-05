# AEGIS - Zero-Trust Identity for AI Agents on the Network

**5G Academy 2026 · Fastweb + Vodafone · Team 4**
Topic 2 - Security on Network · Assigned by the Committee on 27 July 2026.

## The idea in one line
As AI agents and automations start acting on 5G network control services, a
credential alone can't prove an agent is what it claims to be. AEGIS builds a
**behavioural fingerprint** of each legitimate agent and scores every request
against it - a **zero-trust gate for machine identities**.

## Pipeline
`OBSERVE` request patterns & metadata (id, timing, call sequence, payload shape)
→ `FINGERPRINT` a known-good behavioural baseline per agent
→ `SCORE` rules + ML anomaly / spoof score
→ `DECIDE` **PASS / STEP-UP / BLOCK** (zero-trust gate dashboard)

## Data strategy
- **Simulation-first (no blockers):** synthetic agent / API traffic with a few
  legit-agent profiles + injected spoofed / anomalous behaviour - sufficient for
  the full PoC.
- **Real data (upgrade, if offered):** real M2M / API-gateway logs to model.
- **Production vision:** the gate as an inline policy check at the edge (FASTedge).

## Folder layout
- `docs/`      - threat model, architecture, specs, meeting notes
- `data/`      - synthetic datasets (generated) + any real samples
- `src/`       - synthetic-data generator, fingerprint + scoring models, gate
- `notebooks/` - exploration & evaluation
- `slides/`    - Gate decks (Sept 2 meeting, Gate 1…)
- `reports/`   - written Gate reports

## Tech stack (planned)
- Synthetic traffic generator (Python)
- Anomaly detection: Isolation Forest / one-class SVM / autoencoder + deterministic rules
- Scoring gate + dashboard (Streamlit) with PASS / STEP-UP / BLOCK
- Open-source only for the PoC; FastwebAI / MIIA optional for a "why blocked" explainer

## Working PoC baseline 
End-to-end, reproducible pipeline on synthetic 5G SBA traffic:
- `src/generate_synthetic_traffic.py` → `data/aegis_traffic.csv` - 210k requests,
  5 legit agents (with PDU-session lifecycle) + injected attacks T1–T7.
- `src/aegis_detect.py` → `reports/` - windowed fingerprints, Isolation Forest
  (fit on legit only, held-out calibration) + rules + a **session state machine**
  (orphan release/update = T6), fused into PASS/STEP-UP/BLOCK. Writes
  `aegis_baseline_metrics.md`, `scored_windows.csv`, `aegis_eval.png`.
- `src/aegis_dashboard.py` - Streamlit **zero-trust gate**: per-agent risk,
  PASS/STEP-UP/BLOCK, per-threat detection, incident inspector with plain-language
  "why". Run: `.venv/Scripts/streamlit run AEGIS/src/aegis_dashboard.py`.
- `src/make_gate1_deck.py` → `slides/AEGIS_Gate1.pptx` (9 slides) + `reports/aegis_gantt.png`.

**Results (held-out test, 11,343 windows):**
| Metric | Value |
|---|---|
| ROC-AUC | **0.99** |
| Precision | 0.79 |
| Recall | **0.98** |
| False-positive rate | **0.8%** |

Detection: **all 7 threats T1–T7 covered** - T1/T2/T4/T5/T6/T7 ≈ 100%, T3 recon 89%.
(T6 closed via session-ID state machine; the earlier window-count heuristic was
removed because it false-fired on legit traffic - see git history / threat model.)

**Next :** harden recon + temporal features, ROC operating-point
analysis, integrate real logs if granted, more agent/attack variants.
