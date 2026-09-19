# AEGIS - Gate 2 Presentation Script (14 slides, 30 minutes)

Matches `slides/GATE-2/AEGIS_Gate2_Official.pptx` exactly, slide 1 through 14. Say it in your own words - these are talking points, not a transcript. The time in brackets is when you should be finishing that slide, not starting it.

---

### Slide 1 - Title [0:30]

> "Good [morning/afternoon]. Gate 1 established the case for AEGIS - today, Gate 2, we show the concrete architecture, a working implementation, and real numbers."

---

### Slide 2 - Index [1:00]

> "Six parts today, matching the official Gate 2 ask exactly: the proposed solution, the architecture, how we implemented it, a full numerical performance analysis benchmarked against the state of the art, what the proof of concept demonstrates, and where we go next toward Gate 3."

---

### Slide 3 - Proposed Technical Solution [4:00]

> "Let's start with the problem. As AI agents and automations get real operational access to 5G core network functions - opening sessions, reading subscriber data, touching policy control - the only thing standing between them and the network is a credential check. But a credential can be stolen, replayed, or misused by a compromised or misconfigured agent, and it still passes authentication every time, because the credential itself is valid. Authentication never asks the one question that actually matters: is this really our agent, behaving the way it always does?
>
> That's the gap we're closing. One line to remember us by: credentials prove what you have, AEGIS verifies how you behave.
>
> Our solution: a behavioural fingerprint for every agent, and a pipeline that scores every request against it. In one line - observe, fingerprint, score, decide.
>
> And here are the seven threats we catch by behaviour, not by credential checks:
> - T1, identity spoofing - wrong endpoint mix, timing, or sequence for that identity.
> - T2, compromised agent - drift from its own baseline: new endpoints, elevated errors.
> - T3, reconnaissance - high cardinality of endpoints and targets, many 403/404s.
> - T4, volumetric abuse - a request-rate spike far above the agent's normal envelope.
> - T5, slow exfiltration - abnormal payload sizes, off-hours persistence.
> - T6, sequence anomaly - a broken call-sequence pattern versus the agent's normal graph.
> - T7, scope creep - calls to network functions never in the agent's baseline scope.
>
> All seven are built, and as we'll show, all seven are detected."

---

### Slide 4 - Architecture: Pipeline Diagram [7:00]

> "Think of this like a checkpoint every agent's traffic has to pass through before it ever reaches the real network functions - AMF, SMF, and the rest. Four steps, left to right, and I'll walk through each box.
>
> **Observe** - every single request an agent sends gets logged: who sent it, what it asked for, when, how big it was. Nothing is judged yet, we're just watching and building a history per agent.
>
> **Fingerprint** - we take a short rolling window of that agent's recent activity - about a minute - and turn it into a set of numbers: how many requests, how many different endpoints it touched, its error rate, its payload sizes, the time of day, and a slightly longer memory that catches slower attacks spread thin across many windows.
>
> **Score** - two layers grade that fingerprint. A rules layer catches the obvious stuff, like touching something out of scope. An ML layer - trained only on normal traffic - catches subtler drift a fixed rule would miss. We take whichever of the two scores is higher, so nothing obvious slips through just because the ML layer didn't flag it.
>
> **Decide** - that final risk number crosses one of two thresholds and becomes an action: PASS, STEP-UP, or BLOCK - fully automatic, no one has to be watching a screen for this decision to happen.
>
> So in one breath: every request is observed, turned into a rolling behavioural fingerprint, scored two ways, and gated in real time."

---

### Slide 5 - Architecture: Scoring & Decision [9:30]

> "Two layers, fused.
>
> The rules layer is fast and explainable - a scope violation is flagged immediately, and a session-state machine tracks PDU-session lifecycle. The ML layer, an Isolation Forest, is trained only on legitimate traffic, so it needs no labelled attacks to learn from. Fusion takes the maximum of the two scores, so the rules layer has veto power on hard violations while ML catches subtler drift.
>
> The fused result maps to PASS - behaves like its known-good self, STEP-UP - challenge it: re-authenticate, approve, or throttle, or BLOCK - quarantine the identity and alert the SOC."

---

### Slide 6 - Implementation Strategy: Tools & Phases [12:00]

> "On implementation: we built this bottom-up and evaluation-driven - the ML equivalent of test-driven development. No change is kept unless it's re-scored against the full labelled dataset first.
>
> Everything is open-source Python: pandas and scikit-learn for the pipeline, Streamlit for the live dashboard. Seven build phases, from the synthetic environment through to evaluation and iteration."

---

### Slide 7 - Implementation Strategy: What We Found & Fixed [14:30]

> "This evaluation loop is not just a formality - it caught two real bugs.
>
> First, an early sequence-detection heuristic was false-firing on legitimate bursty traffic; we replaced it with a proper session-state machine.
>
> Second, and more subtly, our first attempt at two of the seven threats accidentally had the attacker reach outside its own scope - which is a different threat entirely - so we were measuring the wrong detector. Fixing that is the direct origin of the realistic, non-uniform numbers you're about to see."

---

### Slide 8 - Numerical Analysis: State of the Art & Headline Metrics [17:30]

> "This is a direct comparison, three numbers, state of the art versus AEGIS, side by side.
>
> **Loud, volumetric attacks** - literature reports 97 to 99 percent detection. Our volumetric threat, T4, hits 100 percent - right in line.
>
> **Rare, subtle attack classes** - literature shows much lower detection here, because low-signal behaviour is genuinely hard to separate from noise. Our hardest case, slow exfiltration, comes in at 76 percent - tracking that same pattern rather than claiming an unrealistic number on something that's fundamentally difficult.
>
> **False-positive rate** - this is the one that decides whether a system survives in production. Industry SOC data puts typical false-positive rates at 46 to 83 percent, and even elite, well-resourced SOCs still run around 10 percent. We're at 1.4 percent - meaningfully below best-in-class.
>
> So the headline isn't 'we beat everyone everywhere.' It's that our numbers land exactly where the state of the art predicts they should: near-perfect on loud signals, honestly harder on subtle ones, and well ahead of industry on the false-positive rate that actually determines whether anyone trusts this day to day. Overall: 0.965 ROC-AUC, 90.7 percent recall, 1.4 percent false positives."

---

### Slide 9 - Numerical Analysis: Per-Threat Detection [19:30]

> "Here's the detection rate per threat, and it's deliberately not uniform. Volumetric abuse and scope creep sit at 100 percent, because those are loud, deterministic signals. The other five span 76 to 96 percent, tracking exactly how subtle each threat's behavioural signature actually is. Low-and-slow exfiltration, at 76 percent, is the hardest case - which matches the literature."

---

### Slide 10 - Numerical Analysis: ROC Operating-Point [21:30]

> "We didn't just pick a threshold, we justified it. The statistically optimal point would catch slightly more attacks, but at more than double the false-positive rate. Our chosen threshold trades a small amount of recall for a materially lower false-positive rate - the right tradeoff for a system that has to run continuously without alert fatigue."

---

### Slide 11 - Expected PoC: Live Demo Script [24:00]

> "Here's what the proof of concept actually demonstrates, live, today - not a future promise.
>
> - Agent overview - all five agents at a glance, live risk scores.
> - Trigger a threat - watch the gate react in real time.
> - Incident inspector - open a plain-language reason for the flag.
> - Cycle through difficulty - easy and hard cases side by side.
> - Show the numbers - the live view next to the metrics.
> - Make zero-trust concrete - a valid credential, still blocked on behaviour."

*(If pairing this slide with an actual live Streamlit walkthrough, switch to the browser here and run through these six steps before moving on.)*

---

### Slide 12 - Expected PoC: Readiness [26:00]

> "Where we actually stand: the generator, the full detection pipeline, the live dashboard, the numerical evaluation, and the threshold analysis are all done today, end to end, on data we built ourselves. The next stage of maturity is validating this same pipeline against real network traffic - the architecture is already designed to take that in without any rework."

---

### Slide 13 - Path to Gate 3 [28:30]

> "Looking ahead to Gate 3: harden the two hardest threats with richer features, extend the pipeline to real network traffic as the next validation step, record the final demo video, and expand our agent and attack coverage to stress-test how well this generalises."

---

### Slide 14 - Thank You / Closing [30:00]

> "To close: Gate 1 was the plan, Gate 2 is the working system with real, honestly benchmarked numbers behind it. We're confident in this direction and looking forward to your questions. Thank you."

---

## Appendix - Live Dashboard Walkthrough (detailed, for Slide 11)

Use this when you actually switch to the browser at slide 11, instead of just reading the six bullets. Matches the live dashboard exactly (`src/aegis_dashboard.py` / aegis5gacademy.streamlit.app).

**1. Land on the hero banner (5 sec)**
> "This is the live gate, running right now against our scored traffic."
Point at the tagline: *"Credentials prove what you have, AEGIS verifies how you behave."*

**2. Sidebar controls (15 sec)**
> "On the left, the two thresholds we just walked through - STEP-UP and BLOCK - are live sliders, not fixed numbers. I can drag either one and every chart and count on this page updates instantly. Below that, I can filter down to specific agents, and enable **live replay** - which streams the scored windows in time order, like watching a real SOC feed, instead of dumping the whole dataset at once."

**3. Turn on live replay and hit Play (15 sec)**
Toggle "Enable live replay," hit Play.
> "Watch the playhead move - this is traffic arriving window by window. Nothing's flagged yet because these are quiet agents behaving normally."
Let it run until an attack window shows up in the KPI row or event feed.
> "There - risk just spiked. That's an attack window arriving, and the gate reacted the instant it crossed threshold."

**4. KPI row (10 sec)**
> "Six numbers, always live: total windows, how many PASSed, STEP-UP, BLOCK, and our two headline metrics - attack recall and false-positive rate - recalculating as replay plays or as I change filters."

**5. Tab 1 - Live overview (20 sec)**
> "Risk over time - blue dots are legitimate traffic sitting low, red X's are actual attacks clustering up near the threshold lines. Next to it, detection rate per threat, so you can see at a glance which threats we catch hardest versus easiest. And below, a live event feed - a scrolling list of the most recent flagged incidents, each with agent, decision, risk score, and the actual reason, like a real SOC alert stream."

**6. Tab 2 - Network topology (20 sec)** - this is the newest, most visual tab
> "This is the agent-to-network-function map. Grey lines are each agent's authorized scope - what it's *supposed* to touch. When there's an incident, we highlight it in colour, and if the dashed line shows up, that's a scope violation - the agent reaching a network function it was never onboarded to access. You can see the actual attack path, not just a score."

**7. Tab 3 - Incident inspector (30 sec)** - the closing "wow" moment
> "This is what a SOC analyst would actually use. Every flagged window in a sortable table - risk, rule score, ML score, error rate, everything. I'll pick one -"
*(select a high-risk row from the dropdown)*
> "- and here's the decision, the risk breakdown between rule and ML, which network functions it touched, and most importantly: **why AEGIS flagged it.** Not a black-box number - the actual rule that fired, in plain language. And ground truth at the bottom confirms whether this was a real attack or a false positive, since this is synthetic data we control."

**8. Close the demo (10 sec)**
> "So end to end: adjustable thresholds, a live replaying feed, a topology view of what's actually being touched, and an explainable incident inspector - all running against the same numbers we just walked through on the slides."

---

## Timing guide
| Slides | Topic | Cumulative time |
|---|---|---|
| 1-2 | Title + agenda | 0:00-1:00 |
| 3 | Proposed technical solution + threat catalogue | 1:00-4:00 |
| 4-5 | Architecture: pipeline + scoring/decision | 4:00-9:30 |
| 6 | Implementation: tools & phases | 9:30-12:00 |
| 7 | Implementation: bugs found & fixed | 12:00-14:30 |
| 8-9 | Numerical analysis: benchmarking + per-threat | 14:30-19:30 |
| 10 | Numerical analysis: ROC operating point | 19:30-21:30 |
| 11-12 | Expected PoC: demo script + readiness | 21:30-26:00 |
| 13 | Path to Gate 3 | 26:00-28:30 |
| 14 | Close | 28:30-30:00 |
| **Total** | | **30:00** |

## Notes for delivery
- Open with the problem statement before the solution (now built into slide 3's opening lines) - state the gap plainly before describing how we close it. Don't let the "credentials vs behaviour" line be the first thing out of your mouth; the problem comes first, the tagline second.
- Slide 8 is doing double duty as the state-of-the-art section - say the words "state of the art" out loud there so the committee clearly hears it as a distinct, deliberate part of the talk, not just a footnote before our own numbers.
- Never frame the lack of real traffic as something Fastweb/Vodafone withheld. We built a complete, self-sufficient PoC on synthetic data by design - real traffic is framed as the next upgrade we're pursuing, not a blocker we're stuck on. This applies to slides 8, 12, 13, and any Q&A on data access.
- This is a technical-solution review, not a pitch - lean on precision over enthusiasm. The committee already bought the idea at Gate 1; today they're checking whether the architecture, numbers, and PoC actually hold up.
- Slide 7 (bugs found & fixed) is the strongest credibility moment in the deck - it shows real engineering rigor, not just tuned-to-look-good numbers. Don't rush it.
- Slide 9's non-uniform per-threat numbers will draw questions if undersold - say plainly that 100% everywhere would be the red flag, not the goal, and point back to the benchmarking research on slide 8.
- Slide 12's one open item (real traffic) should land as "our own natural next step," not as something we're waiting on someone else for. Never say the words "Fastweb didn't give us data" or "blocked" out loud - if asked directly in Q&A, say we built and validated everything ourselves on synthetic data by design, and real traffic is simply the next upgrade.
- If time is tight, the safest slides to compress (not cut) are 4-5 (architecture) and 11-12 (PoC) - each pair covers one idea from two angles.
- If running long, cut to the bolded numbers on slides 8-10 and skip the supporting literature citations - the committee can ask for detail in Q&A.
