# AEGIS - Gate 1 Presentation Script
**Audience: Vodafone + Fastweb committee · 5G Academy 2026 · Team 4**

Read this as a guide, not a word-for-word script - say it in your own voice. Bold lines are the ones worth memorizing exactly.

---

## 1. Open (30 sec) - the hook

> "Good [morning/afternoon]. Our project is called **AEGIS** - Zero-Trust Identity for AI Agents on the Network. The one-line version: **when an AI agent talks to your 5G network, how do you know it's actually behaving like the agent it claims to be - not just holding its credentials?**"

Pause here. Let that land - it's the whole problem in one sentence.

## 2. The problem (1 min)

> "Today, more and more of the traffic hitting 5G core network functions - session management, policy control, subscriber data - isn't a human clicking a button. It's automations and AI agents: orchestration bots, RPA scripts, and soon autonomous AI agents making API calls on someone's behalf.
>
> The security model for that traffic is still just: **'do you have a valid token or API key?'** But a stolen token, a compromised agent, or a misconfigured integration all pass that check perfectly. The credential doesn't tell you whether *the way* the agent is behaving still matches what it's supposed to be doing.
>
> That's the gap our committee assigned us: **Security on the Network**, specifically machine-identity trust."

## 3. Our idea (1 min)

> "Our answer is a **behavioural fingerprint**, not a stronger password. For every legitimate agent, we learn its normal pattern: which network functions it calls, how often, in what sequence, at what times, with what payload sizes. Then every new burst of requests gets scored against that fingerprint in real time, and the gate makes one of three decisions:
>
> - **PASS** - behaves exactly like itself, let it through.
> - **STEP-UP** - somewhat unusual, ask for additional verification.
> - **BLOCK** - clearly doesn't match, stop it before it touches the core.
>
> This is the same principle as **zero-trust for humans** - 'never trust, always verify' - but applied to machine identities."

## 4. How it works - the pipeline (1 min)

Walk through this like a diagram in your head (it's on the slide):

> "The pipeline has four stages: **Observe → Fingerprint → Score → Decide.**
>
> We **observe** each agent's request stream - timing, call sequence, which network function, response sizes. We build a **fingerprint** - a statistical baseline of normal behaviour per agent, in 60-second windows. We **score** every new window two ways: deterministic **rules** for known bad patterns, plus a **machine-learning anomaly model** - an Isolation Forest - trained only on legitimate traffic, so it flags anything that doesn't look like 'normal.' Those two scores get fused into a single risk score, and the gate **decides** PASS, STEP-UP, or BLOCK."

## 5. Why simulation-first (30 sec) - preempt the "is this real data" question

> "Since we don't yet have access to real M2M / API-gateway logs, we built this **simulation-first**, so there's no blocker to having a working proof of concept today. We generated **210,000 realistic 5G service-based-architecture requests** across 5 legitimate agent profiles, each with a full PDU-session lifecycle, and then deliberately injected seven categories of attack behaviour on top. If real anonymized logs become available, the same pipeline drops straight in - we'd just retrain the fingerprint on real traffic."

## 6. The seven threats (1 min) - shows rigor, not just a toy demo

> "We didn't invent generic anomalies - we modeled seven concrete threat patterns relevant to machine identity abuse on a 5G core:
>
> 1. **T1 - Impersonation**: valid token, but behaviour of a different role.
> 2. **T2 - Compromise**: a legitimate agent starts drifting - new endpoints, rising errors.
> 3. **T3 - Recon**: broad enumeration across many endpoints, high 403/404 rate.
> 4. **T4 - Volumetric abuse**: flooding one network function.
> 5. **T5 - Exfiltration**: slow, quiet reads pulling unusually large responses.
> 6. **T6 - Bad sequence**: releasing or updating a session that was never legitimately created - an orphan operation.
> 7. **T7 - Scope creep**: touching a network function the agent was never onboarded to access.
>
> Each one gets injected into the synthetic traffic and we measure whether AEGIS catches it."

## 7. Results (1 min) - the numbers slide, say them with confidence

> "On a held-out test set of over 11,000 sixty-second windows, AEGIS achieves:
>
> - **ROC-AUC of 0.99**
> - **98% recall** - it catches almost every attack
> - **Precision of 0.79**
> - and a **false-positive rate under 1%** - so it's not crying wolf on normal traffic.
>
> Broken down by threat: **T1, T2, T4, T5, T6, and T7 are detected essentially 100% of the time**; **T3, pure reconnaissance, is caught 89%** of the time - that's our hardest case because low-and-slow recon can look a lot like a curious-but-legitimate agent, and it's honestly where we want to spend more effort next."

If asked "why not 100% on T3": say exactly that - recon is the noisiest signal, and pushing it higher without hurting the false-positive rate is next-phase work.

## 8. Now hand off to the live demo

> "Let me show you this running live rather than just talk about it."

*(Switch to the browser / Streamlit app now - see Section 9 below.)*

## 9. Live Streamlit demo - what to click and say

Have the app running beforehand: `streamlit run AEGIS/src/aegis_dashboard.py` (or wherever it's hosted). Practice this flow once tonight so your hands know it.

**Step 1 - Orient them on the screen (15 sec)**
> "This is the **zero-trust gate**, a NOC/SOC-style live view. Every row here is one 60-second window of an agent's traffic, scored and gated."

Point at the top KPI row:
> "Windows scored, how many PASSed, how many got STEP-UP, how many got BLOCKed, and our two headline numbers - attack recall and false-positive rate - updating live as you filter."

**Step 2 - Risk-over-time chart (15 sec)**
> "This chart is risk score over time per window. The blue dots are legitimate traffic sitting low, near zero. The red X's are actual injected attacks - and you can see they cluster up near the STEP-UP and BLOCK lines. That separation is the model doing its job."

**Step 3 - Thresholds are adjustable (15 sec)** - great interactive moment
> "These aren't hard-coded. I can drag the STEP-UP and BLOCK thresholds live -"
*(drag the sidebar sliders)*
> "- and watch the PASS/STEP-UP/BLOCK counts and the false-positive rate react instantly. This is exactly the kind of dial a SOC operator would tune for their own risk appetite."

**Step 4 - Per-threat detection chart (10 sec)**
> "This bar chart breaks detection down per threat category, so an operator can see at a glance which attack types the gate is strong or weak against - you can see T3 recon is the shortest bar, matching what I just said."

**Step 5 - Incident inspector - the "wow" moment (30-45 sec)**
> "This is the part I'd want a SOC analyst to actually use day to day."

Scroll to the incident table, pick a high-risk BLOCK row, select it in the dropdown:
> "Here's a specific flagged window. It shows me the agent ID, the decision, the risk score, and the breakdown between rule-based score and ML score. But most importantly -"

Point at the "Why AEGIS flagged this" section:
> "- it gives a **plain-language explanation**: for example, '3 orphan session operations - update or release of a PDU session that was never created.' An analyst doesn't have to reverse-engineer a black-box score - they get a human-readable reason, tied back to the actual threat pattern. And at the bottom we show the ground truth for this synthetic case, so you can see the model was right."

**Step 6 - Close the demo (10 sec)**
> "So end to end: synthetic 5G traffic in, behavioural fingerprint and ML scoring in the middle, and a live, explainable, adjustable gate on the output. All open-source, all reproducible - the whole pipeline runs in a few minutes from raw traffic generation to this dashboard."

## 10. Production vision / what's next (45 sec)

> "Our production vision is this running as an **inline policy check at the edge** - for example on FASTedge - sitting in front of the 5G core network functions, gating machine-agent traffic before it reaches anything sensitive.
>
> For Gate 2, our priorities are: **hardening recon detection** with better temporal features, doing a proper **ROC operating-point analysis** to pick thresholds with real cost tradeoffs instead of round numbers, and - if the committee can grant access - **validating against real M2M or API-gateway logs** instead of only synthetic data. We'd also want to expand the agent and attack variety to stress-test it further."

## 11. Close (15 sec)

> "To summarize: as AI agents get real operational access to 5G network functions, a token isn't enough proof of identity anymore. AEGIS shows that a behavioural fingerprint plus a lightweight zero-trust gate can catch impersonation, compromise, and abuse with 98% recall and under 1% false positives - and do it in a way a human operator can actually trust and explain. Happy to take questions, and happy to dig into any part of the pipeline live."

---

## Anticipated Q&A (prep these, don't read them out loud)

**Q: How is this different from a normal WAF / API gateway rate limiter?**
> A rate limiter only sees volume. We build a per-agent behavioural baseline across timing, sequence, target scope, and payload shape - so we catch things like scope creep or orphan sessions that never look like a "spike" at all.

**Q: What happens on STEP-UP in practice?**
> In production this would trigger additional verification - e.g. a secondary attestation check, a short-lived re-auth, or routing to a human/SOC review - rather than an outright block, so we don't kill legitimate-but-unusual behaviour.

**Q: Isn't Isolation Forest trained only on legit traffic a weakness - won't it drift as agents evolve?**
> Yes, that's a real operational concern - the baseline needs periodic retraining as agent behaviour legitimately evolves. That's part of why we fuse it with deterministic rules, which don't drift, and it's on our Gate 2 list to test retraining cadence.

**Q: Why 60-second windows?**
> Long enough to see behavioural patterns (call sequences, rates) rather than single-request noise, short enough to react before real damage - it's a tunable parameter, not fundamental to the approach.

**Q: Data privacy / can you actually get real logs?**
> That's exactly why we built simulation-first - zero dependency on getting real data to deliver a working Gate 1 PoC. If Vodafone/Fastweb can share anonymized or synthetic-but-realistic API-gateway logs, the same pipeline retrains directly on them.

---

## Logistics checklist for tomorrow
- [ ] Start Streamlit locally *before* you walk in: `streamlit run AEGIS/src/aegis_dashboard.py` (from repo root, using your `.venv`)
- [ ] Confirm `reports/scored_windows.csv` exists and loads without error (re-run `src/aegis_detect.py` if stale)
- [ ] Have the live GitHub Pages link open as backup: https://fauzan111.github.io/AEGIS/
- [ ] Pre-select one clean BLOCK example in the incident inspector so you're not fumbling live
- [ ] Know your two headline numbers cold: **0.99 ROC-AUC, 98% recall, <1% false-positive rate**
