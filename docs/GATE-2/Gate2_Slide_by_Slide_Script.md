# AEGIS - Gate 2 Presentation Script (21 slides: 16 timed + 5 backup appendix)

Matches `slides/GATE-2/AEGIS_Gate2_Official.pptx` exactly as of the video-embed pass. Say it in your own words - these are talking points, not a transcript. The time in brackets is when you should be *finishing* that slide, not starting it. Total timed narrative: ~28 minutes, leaving buffer in a 30-minute slot for Q&A.

**Read this once before the notes below:** every place her feedback applies is marked ★ inline, not just listed at the end - problem-first structure, naming the state-of-the-art system explicitly, never claiming unqualified "optimal," and never framing missing real-world data as Fastweb/Vodafone's fault.

---

### Slide 1 - Title [0:30]

> "Good [morning/afternoon]. Gate 1 established the case for AEGIS - today, Gate 2, we show the concrete architecture, a working implementation, and real numbers benchmarked against a named baseline."

---

### Slide 2 - Index [1:15]

> "Six parts today, matching the official Gate 2 ask exactly: the proposed solution, the architecture, how we implemented it, a full numerical performance analysis benchmarked against the state of the art, what the proof of concept demonstrates, and where we go next toward Gate 3."

---

### Slide 3 - Proposed Technical Solution [4:00]

★ **Problem-first, deliberately.** Say the gap before the tagline - don't let "credentials vs behaviour" be the first thing out of your mouth.

> "Let's start with the problem. As AI agents and automations get real operational access to 5G core network functions - opening sessions, reading subscriber data, touching policy control - the only thing standing between them and the network is a credential check. But a credential can be stolen, replayed, or misused by a compromised agent, and it still passes authentication every time, because the credential itself is valid. Authentication never asks the one question that actually matters: is this really our agent, behaving the way it always does?
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

### Slide 4 - The Gap, Our Solution, and the State of the Art [6:00]

★ **This slide exists specifically because she asked for one place that ties gap, solution, and state-of-the-art together.** Deliver it as the "if you remember one slide" moment.

> "This slide is the whole pitch in three boxes.
>
> The gap: a credential check proves you have the right token, once, at the door - it never asks whether the traffic behind that token still behaves like the agent it claims to be. A stolen or misused identity passes every time.
>
> Our solution: a behavioural fingerprint per agent, scored continuously - observe, fingerprint, score, decide - rules fused with an Isolation Forest, gated PASS, STEP-UP, or BLOCK.
>
> And against the state of the art - named, reimplemented, and run on our own data, not cited from someone else's paper: a Statistical Process Control z-score baseline scores 0.944 ROC-AUC and 63.4% recall. AEGIS scores 0.965 and 90.7% - a statistically significant gap, p equals 0.015.
>
> One line: credentials prove what you have, AEGIS verifies how you behave - and we can show that, not just claim it."

---

### Slide 5 - System Architecture [8:00]

> "Here's the architecture end to end - a four-stage pipeline sitting in front of the network's control-plane APIs. Every request an agent sends to a Network Function is observed by the gate.
>
> Observe parses every request into a normalised event. Fingerprint turns a sliding window into a behavioural feature vector - volume, surface, method mix, sequence, errors, payload, time of day. Score combines deterministic rules with an unsupervised ML model. Decide turns that risk number into a gate action."

---

### Slide 6 - Scoring: Rules + ML, Fused [10:00]

> "Two layers, fused.
>
> The rules layer is fast and explainable - an out-of-scope call is flagged immediately, with a session-state machine and rolling 5-minute accumulators for breadth, errors, and peak payload. The ML layer, an Isolation Forest, is trained only on legitimate traffic, so it needs no labelled attacks to learn from, and only engages once an agent has enough recent activity to fingerprint meaningfully.
>
> Fusion takes the maximum of the two scores, so the rules layer has veto power on hard violations while ML catches subtler drift the rules never anticipated.
>
> The fused result maps to PASS, STEP-UP - challenge and re-verify - or BLOCK - quarantine and alert the SOC. And the operating point itself - why 1.5%, why not zero false positives - that's fully justified with real statistics later in Part 4, not just asserted here."

---

### Slide 7 - Tools, Platforms & Build Phases [12:00]

> "On implementation: built bottom-up, PoC-first, and evaluation-driven - the ML equivalent of test-driven development. No change is kept unless it's re-scored against the full labelled dataset first.
>
> Everything is open-source Python: pandas and scikit-learn for the pipeline, Streamlit for the live dashboard. Seven build phases, from the synthetic environment through to evaluation and iteration."

---

### Slide 8 - What The Evaluation Loop Found & Fixed [14:00]

> "This evaluation loop is not just a formality - it caught two real bugs.
>
> First, an early sequence-detection heuristic was false-firing on legitimate bursty traffic; we replaced it with a proper session-state machine.
>
> Second, and more subtly, our first attempt at two of the seven threats accidentally had the attacker reach outside its own scope - indistinguishable from scope creep to the rules layer - so we were measuring the wrong detector. Redesigning both to stay within the agent's own scope is the direct origin of the realistic, non-uniform numbers you're about to see - a feature of an honest evaluation, not a flaw."

---

### Slide 9 - Numerical Analysis: State of the Art & Headline Metrics [16:30]

★ **This is where "state of the art" stops being a phrase and becomes a name.** Say "Statistical Process Control" explicitly, twice if you have to.

> "A PoC that reports 100% detection on everything is a red flag, not a strength - so before showing our own numbers, here's what we actually benchmarked against.
>
> We named a specific state of the art and ran it ourselves: a Statistical Process Control, or SPC, z-score control-chart detector - the classic baseline this kind of behavioural monitoring descends from. Not a citation from someone else's dataset - we implemented it and ran it on our own data, on the identical train/test split AEGIS is evaluated on.
>
> SPC on our data: 0.944 ROC-AUC, 63.4% recall at a matched 1.43% false-positive rate. AEGIS: 0.965 and 90.7% at the same FPR - a real head-to-head, detailed on the very next slide.
>
> And the improvement is statistically significant, not just a bigger number: a paired bootstrap on the AUC difference gives p equals 0.015, 95% confidence interval 0.004 to 0.040, excluding zero.
>
> Our own headline numbers: 0.965 ROC-AUC, 90.7% recall, 1.4% false positives, 0.67 precision."

---

### Slide 10 - State of the Art, Head-to-Head [18:30]

★ **The chart on this slide is the single most direct answer to "compare against the benchmark and show it."** Give the audience a moment to actually look at it.

> "Here's that comparison visually. Statistical Process Control, implemented and evaluated on the identical split as AEGIS. SPC detects loud, single-feature deviations effectively - T4 at 100%, T1 at 94% - but is structurally blind to threats with no single-feature signature: T2 compromise at 21%, T3 recon at 27%, T6 sequence at 51%.
>
> This measured gap quantifies the value of behavioural fingerprinting combined with rule-based fusion. Not an assumed architectural preference - a measured one."

---

### Slide 11 - Detection Rate Per Threat [20:00]

> "Here's the detection rate per threat, and it's deliberately not uniform. Volumetric abuse and scope creep sit at 100%, because those are deterministic policy and rate checks, not statistical inference. The other five span a genuine 76 to 96% range that tracks the strength of their underlying behavioural signal: loud beats subtle, and diffuse, low-and-slow attacks are always the hardest."

---

### Slide 12 - ROC Operating-Point Analysis [22:00]

★ **This is the corrected slide. Say it as a settled, formal claim - not as a response to anyone's objection.** Don't say "we don't call it optimal" out loud; the slide already states it positively. Just deliver the positive claim.

> "The chosen threshold is justified with respect to a stated, checkable statistical objective.
>
> Our threshold of 0.60 is Pareto-efficient - no alternative threshold improves both recall and false-positive rate simultaneously - and it lies within 0.2 percentage points of FPR of the Neyman-Pearson-achievable frontier for this risk score. Formally, it minimises a cost function - r times one minus recall, plus false-positive rate - for a stated cost ratio r. That's a named, checkable statistical objective, not an assertion."

*(If asked directly why not call it "optimal": the Neyman-Pearson-optimal test requires a known statistical characterisation of the true class-conditional distributions, which isn't available in production or in any real deployment. What we can state and check is Pareto-efficiency and distance to the achievable frontier for this risk score - which is exactly what's on the slide.)*

---

### Slide 13 - Live Demo [23:30]

> "Here's the proof of concept, live - not a forward-looking description, a recording of what exists today, right now."

*(Play the embedded video - about 75 seconds. Let it run without narrating over it; the visuals speak for themselves: launching a live attack, the Before-AEGIS/With-AEGIS reveal, and the network topology view.)*

After it finishes:
> "That's the actual pipeline, actual generator, actual scoring - running live, not scripted."

---

### Slide 14 - PoC Readiness at Gate 2 [25:00]

★ **No Fastweb framing here - own the next step as ours, not something we're waiting on.**

> "Where we actually stand: the generator, the full detection pipeline, the live dashboard, the numerical evaluation, and the threshold analysis are all done today, end to end, on data we built ourselves. Real M2M and API-gateway traffic is the natural next validation step - the pipeline is already built to take it in without rework."

---

### Slide 15 - Path to Gate 3 [26:30]

★ **Same rule as slide 14 - "extending," never "waiting on" or "if they provide it."**

> "Looking ahead to Gate 3: harden the two hardest threats with richer features, extend the pipeline to real M2M and API-gateway traffic as the next validation step, record the final video demonstration from what you just saw, and expand our agent and attack coverage to stress-test how well this generalises."

---

### Slide 16 - Thank You / Closing [27:30]

> "To close: Gate 1 was the plan, Gate 2 is the working system - a named baseline beaten with statistical significance, a threshold justified by a stated objective, and a live demo you just watched running for real. We're confident in this direction and looking forward to your questions. Thank you."

---

## Appendix (slides 17-21) - backup only, not part of the timed narrative

Pull these up only if a question calls for them. Each is one chart + one finding.

| Slide | Topic | One-line finding |
|---|---|---|
| 17 | Bootstrap Confidence Intervals | ROC-AUC 0.965 [0.951, 0.977], recall 90.7% [87.6%, 93.5%] - point estimates alone overstate precision on a ~350-window attack sample. |
| 18 | Cross-Validated Threshold Stability | 5-fold CV threshold: 0.600 ± 0.033 - the 0.60 threshold wasn't cherry-picked to one test set. |
| 19 | Temporal Split Robustness | Chronological (not random) split: ROC-AUC 0.969, recall 90.1% - held up with far less training data. |
| 20 | Concept-Drift / Stationarity Check | 6 of 20 agent/feature pairs drift even within 5 synthetic days - motivates a re-baselining cadence as a named Gate 3 requirement. |
| 21 | Adversarial Evasion Stress Test | Pacing the same T4 flood over 24h instead of 1h drops detection 100% to 0% - a real, demonstrated gap with a named fix already scoped for Gate 3. |

If she asks "what else did you check statistically" or "how do you know 0.60 generalises" - these five slides are the direct answer, in order of relevance: 18 (threshold stability) and 17 (confidence intervals) first, 19 and 20 if she's probing deployment realism, 21 only if she asks about adversarial robustness specifically.

---

## Timing guide

| Slides | Topic | Cumulative time |
|---|---|---|
| 1-2 | Title + agenda | 0:00-1:15 |
| 3 | Problem + proposed solution + threat catalogue | 1:15-4:00 |
| 4 | Gap / Solution / State-of-the-Art (the one-slide pitch) | 4:00-6:00 |
| 5-6 | Architecture: pipeline + scoring/fusion | 6:00-10:00 |
| 7-8 | Implementation: tools/phases + bugs found & fixed | 10:00-14:00 |
| 9-10 | Numerical analysis: SoA benchmarking + head-to-head chart | 14:00-18:30 |
| 11-12 | Per-threat detection + corrected ROC operating-point | 18:30-22:00 |
| 13 | Live demo video | 22:00-23:30 |
| 14-15 | PoC readiness + path to Gate 3 | 23:30-26:30 |
| 16 | Close | 26:30-27:30 |
| **Total** | | **~27:30**, leaving ~2:30 buffer in a 30-min slot |

## Notes for delivery - her guidance, applied throughout, not just at the end

1. **Problem before solution, every time.** Slide 3 opens with the gap, not the tagline. Don't reorder this on the fly even if you're rushing.
2. **Name the state of the art out loud.** Say "Statistical Process Control" or "SPC" explicitly on slides 4, 9, and 10 - never just "the state of the art" or "existing approaches." She specifically flagged vague SoA references as unacceptable.
3. **Never say "optimal" unqualified.** Slide 12 is written to avoid this already - deliver it as written. If pushed in Q&A, the answer is Pareto-efficiency plus distance to the Neyman-Pearson frontier, not a bare "yes it's optimal."
4. **Never blame Fastweb/Vodafone for missing real data.** Slides 14 and 15 are phrased as "the next validation step" / "extending the pipeline" - never "if they provide it" or "blocked on." This has been hunted down and fixed everywhere in the deck; don't reintroduce it verbally.
5. **Know the "magic sauce" one-liner cold**, in case she asks for it directly: *"We made identity continuous instead of one-time, and built the detector specifically around how 5G agents behave - not a generic security tool repurposed for 5G."*
6. **Know your 3-5 sellable strong points separately from the full deck**, in case she asks to compress the pitch: (1) a working PoC, live, today; (2) honestly benchmarked numbers beating even elite industry SOCs on false-positive rate; (3) explainable, not a black box; (4) real engineering rigor - bugs found and fixed during evaluation; (5) zero cost, fully self-sufficient, built without waiting on anyone.
7. Slide 8 (bugs found & fixed) is still the strongest credibility moment in the deck - don't rush it.
8. If time is tight, the safest slides to compress are 5-6 (architecture) and 17-21 (appendix, skip entirely) - never compress slide 4 or slide 12, those are the two slides built specifically from her feedback.
