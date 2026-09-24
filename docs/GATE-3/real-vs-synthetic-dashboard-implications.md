# Real Open5GS traffic vs. synthetic data - what actually changes

This note answers a specific question: given the real-traffic validation work
in `real-traffic-capture.md`, what would change in the dashboard and the rest
of the pipeline if AEGIS switched from the synthetic generator to real
Open5GS traffic as its primary data source? Nothing described here has been
implemented - this is a scoping note, written before touching anything.

## The caveat that shapes everything else

What's been captured and validated so far is real *core-internal* NF-to-NF
signalling - AMF calling AUSF/UDM/PCF/SMF during a UE registration. That's
genuine 5G core traffic, but it isn't quite the same thing as "AI
agents/automation clients calling into the network," which is AEGIS's actual
thesis. The rogue-agent script built for the detection-validation test
(making direct SBI calls) is closer to that shape, but it's one hand-scripted
identity, not a fleet of distinct automation agents each with their own real
behavioural history. That distinction matters for every point below.

## Dashboard changes, if fully wired up

- **Agent list.** The current 5-7 story-driven names (`orch-session-mgr`,
  `provisioning-agent`, etc.) would need to become something meaningful for
  real traffic: either real subscriber/UE sessions, or a small fleet of
  scripted "agent" identities like the rogue-agent script, each with its own
  real call pattern.
- **Network topology view.** Currently draws "this agent's authorized NFs vs.
  what it actually touched" as a clean bipartite graph. Real traffic shows a
  full mesh (one registration event touches AMF -> AUSF -> UDM -> PCF -> SMF
  -> UPF in sequence) - the topology view would look denser and less like a
  simple "agent has a scope" story.
- **Live attack injection buttons.** Right now they call a Python function
  that fabricates rows instantly. Made real, each click would need to fire
  actual SBI calls against a running Open5GS core and wait for real
  responses - slower, and it requires that core to be alive and reachable at
  demo time.
- **Baselines/thresholds.** The p99-based rules and the ML layer need real
  history to learn from. A short real capture gives thin, noisy baselines -
  already observed directly: the ML layer underfit on the short real test in
  `real-traffic-capture.md`. Detection would likely be less stable until real
  traffic accumulates over days, not minutes.

## Infrastructure changes

The dashboard is currently hosted on Streamlit Community Cloud
(`aegis5gacademy.streamlit.app`) - a lightweight free-tier host with no
Docker support. A live Open5GS core needs persistent multi-container
orchestration, SCTP sockets, and privileged networking - none of that runs
there. Going real would mean either:

- running the demo locally or on a VM with Docker, or
- keeping the public dashboard synthetic and demoing the real pipeline
  separately (recommended for Gate 3 - no live-infra risk during a graded
  demo).

## Evaluation/statistics changes

The bootstrap confidence intervals, the SPC baseline comparison, and the
per-threat breakdown that give Gate 2 its statistical rigor all depend on
having 50-160+ labelled attack windows per threat. Real traffic doesn't come
pre-labelled - building a comparable real evaluation set would mean replaying
synthetic-style attacks against the real core repeatedly (the same approach
already used in `validate_real_traffic_detection.py`), just at much larger
scale and over a longer capture window.

## What stays exactly the same

- The detection code itself (`build_windows`, `learn_baselines`,
  `rule_score`, `ml_scores`) - already proven to run unmodified on real data.
- The CSV schema and the PASS / STEP-UP / BLOCK decision framework.
- The incident inspector's plain-language explainability.
- The endpoint naming convention (already confirmed to match real 3GPP
  services almost exactly).

## Bottom line

Switching the dashboard over to real traffic is a real infrastructure
project (persistent core, real-time capture, a much longer baseline-building
period), not a code change - worth scoping as its own piece of work rather
than folding into Gate 3. What's already done (schema validation in
`real-traffic-capture.md` plus the detection-pipeline test in
`validate_real_traffic_detection.py`) is the right-sized proof for Gate 3's
"real traffic" requirement without taking on live-infrastructure risk for
the actual graded demo.
