# AEGIS - Gate 1 Slide-by-Slide Script (16 slides)
**Vodafone + Fastweb committee · 5G Academy 2026 · Team 4**

Matches `slides/AEGIS_Gate1_Official.pptx` exactly, slide 1 through 16. Say it in your own words - these are talking points, not a transcript. Time estimates assume a ~10-12 min slot; cut the bracketed [optional] lines first if you're running long.

---

### Slide 1 - Title
*(5G Academy logo, "Postgraduate Course 2026")*

> "Good [morning/afternoon]. We're Team 4, and we're presenting **AEGIS** for Gate 1."

Keep this to one breath - it's a title card, don't over-explain it. Let whoever is presenting introduce themselves here if you're splitting speaking roles.

---

### Slide 2 - Index / Team
*(8-part agenda + team names: Fauzan Ejaz (Captain), Adithya Zacharia Valavi, Ghazanfar Anees Siddiqui, Llagami Tedi)*

> "Quick roadmap for the next few minutes: what we're building, a plain-language tour of the 5G network, the agents we modelled, how we built the prototype, the attacks we simulated, how AEGIS decides, the proof it works, and finally the project plan - schedule, feasibility, and business case. I'm [name], and this is [team members] - we'll [split slides / I'll walk through it all], happy to take questions at the end or as we go."

[optional] If team members are each presenting sections, name who covers what here so the committee knows what to expect.

---

### Slide 3 - What We're Building
*(Headline: "Credentials prove what you have, AEGIS verifies how you behave.")*

> "Here's the whole idea in one line: **credentials prove what you have, AEGIS verifies how you behave.**
>
> AEGIS is a zero-trust identity check for the AI agents and automations that call a 5G network's control systems. It combines three things: the **5G Service-Based Architecture** - that's the network's internal API layer - a **zero-trust security model**, and **behavioural machine learning**. Concretely: it learns each agent's normal working pattern, and scores every request against that pattern.
>
> And practically - this runs entirely on **open-source tools**: Python, scikit-learn, Streamlit, end to end. No specialised hardware, no licensing cost. That matters for feasibility, which we'll come back to."

---

### Slide 4 - The 5G Network, In Plain Terms
*(AMF, SMF, NRF, PCF, UDM, NEF - six network functions)*

> "Before the threat model makes sense, a primer on the network itself. A 5G core is a set of specialised systems - **network functions** - each handling one job, talking to each other over standard APIs. Think of it like departments in a company:
>
> - **AMF** - Access & Mobility - keeps track of where a device is and whether it's reachable.
> - **SMF** - Session Management - opens, updates, and closes a device's data session.
> - **NRF** - Network Repository - the internal directory, lets systems find each other.
> - **PCF** - Policy Control - decides and enforces the rules a session must follow.
> - **UDM** - Unified Data Management - holds and serves subscriber data.
> - **NEF** - Network Exposure - the controlled front door for outside apps and automations.
>
> Every agent we model only touches a handful of these - and that's exactly the pattern AEGIS learns to protect."

---

### Slide 5 - The Agents We Modelled
*(5 agent profiles: session orchestrator, inventory job, closed-loop assurance, NRF heartbeat, provisioning agent)*

> "We modelled five automations, each with its own job, schedule, and routine - so AEGIS has something concrete to learn and can tell the moment one of them starts acting unlike itself:
>
> - **Session orchestrator** - opens and closes sessions across AMF, SMF, PCF, runs 24/7 at a steady pace.
> - **Inventory job** - reads records from NRF and UDM only, runs briefly overnight.
> - **Closed-loop assurance** - subscribes to live events on AMF, NEF, PCF, also runs 24/7.
> - **NRF heartbeat service** - registers and pings NRF only, very steady, very low volume.
> - **Provisioning agent** - updates subscriber data via NEF and UDM, business hours only.
>
> Notice each one has a distinct scope and schedule - that's the fingerprint. An inventory job suddenly calling PCF at 3am is already a red flag before any ML model even runs."

---

### Slide 6 - How We Built The Prototype
*(3 steps: traffic simulator, injected attacks, detection engine)*

> "Here's how the prototype is actually built, in three pieces - and it's important to be precise about where the AI actually is:
>
> **One - the traffic simulator.** This is a program we wrote ourselves that plays out a virtual week of activity for all five agents. To be clear: **this is a scripted simulation, not a machine-learning model.** It produced about **210,000 requests**.
>
> **Two - injected attacks.** Into that traffic we inserted seven kinds of attack episodes, each one labelled, so we know exactly which requests are attacks. That's only possible because the data is simulated - we control ground truth.
>
> **Three - the detection engine, the real ML.** A separate program reads all that traffic, builds a behavioural fingerprint per agent, and scores every window for risk. **This is where an actual machine-learning model - an Isolation Forest - is used.**
>
> So to be transparent: steps one and two are engineering and design; the learning happens in step three."

---

### Slide 7 - Technologies & Synthetic Data
*(Tech stack: Python, pandas/numpy, scikit-learn, Streamlit + synthetic data build details)*

> "Two things on this slide: what we built with, and how the synthetic data itself was constructed.
>
> **Stack** - Python for everything, free and industry-standard; pandas and numpy to handle the 210,000 requests as structured data; scikit-learn, the standard ML library, which is where the Isolation Forest comes from; and Streamlit, which turns the Python detector into the live, interactive gate dashboard you'll see in a moment.
>
> **How the synthetic data was built** - six network functions modelled with realistic API endpoints, five agent profiles each with its own scope, schedule, and call sequence played out over a simulated week, and seven attack types injected on top, each ground-truth labelled for evaluation. Everything here is free and open source, and real M2M or API-gateway logs are pluggable later if Fastweb and Vodafone can share them.
>
> One more time, because it matters: **the data generator is a scripted simulation, not AI. The Isolation Forest is the only place machine learning is actually used - on the detection side.**"

---

### Slide 8 - The Attacks We Simulated
*(T1-T7 threat cards)*

> "Here are the seven threats, and the framing that matters: **we assume the attacker already has a valid credential.** What changes is the behaviour, not the credential - that's the whole premise of zero-trust for machine identities.
>
> - **T1 - Impersonation** - acts like a different agent than the one it's authenticated as.
> - **T2 - Compromised agent** - a legitimate agent drifts to new behaviour.
> - **T3 - Recon / scanning** - probes broadly, generates many errors.
> - **T4 - Volumetric flood** - request rate spikes hard.
> - **T5 - Slow exfiltration** - quiet, large data pulls.
> - **T6 - Broken sequence** - closes or updates a session that was never opened.
> - **T7 - Scope creep** - touches systems outside its role.
>
> None of these require stealing a better credential - they're all things a valid-but-misused identity would do."

---

### Slide 9 - How AEGIS Decides
*(Observe → Fingerprint → Score → Decide pipeline; PASS / STEP-UP / BLOCK)*

> "This is the engine room. Four stages:
>
> **Observe** - log every request: agent, target, timing, size, status.
> **Fingerprint** - compare the last 60 seconds of activity to that agent's own normal.
> **Score** - hard rules plus an ML model, trained on legitimate traffic only, combine into one risk number.
> **Decide** - fixed thresholds turn that risk number into **PASS, STEP-UP, or BLOCK**, automatically.
>
> - PASS means it behaves like itself.
> - STEP-UP means challenge it, re-verify.
> - BLOCK means quarantine it and alert a human.
>
> And this line is important: **there is no person watching in real time.** The decision is fully automatic - a human only gets involved after a STEP-UP or BLOCK has already been raised. That's what makes this operationally realistic at network scale."

---

### Slide 10 - Proof It Works
*(0.99 ROC-AUC, 98% recall, 0.8% false positives, 7/7 threats covered + honest caveat)*

> "The numbers, measured on **11,343 held-out windows** the model never trained on:
>
> - **0.99 ROC-AUC**
> - **98% recall** - of injected attacks caught
> - **0.8% false positives** - legitimate traffic wrongly flagged
> - **7 out of 7 threats covered**
>
> Attacks separate cleanly from normal traffic at that ROC-AUC, and we're only mis-flagging less than 1 in 100 legitimate windows.
>
> Now the honest caveat, and I want to say this plainly rather than have you ask it: **this is synthetic-first.** It proves the method works and is well-calibrated - it does not yet prove it holds up on real network traffic. That validation is exactly what real or anonymised data from Fastweb and Vodafone would give us, and it's the single biggest thing that would move this from 'promising PoC' to 'production-credible.'"

---

### Slide 11 - Project Roadmap & Timeline
*(Gantt-style: 24 Jul threat model → 27 Jul traffic generator → 10 Aug baseline detector → 2 Sep Fastweb meeting → 7 Sep Gate 1 proposal → 22 Sep Gate 2 → 24 Sep storyboard → Oct PoC evaluation / video shoot → 15 Oct Gate 3 → 1 Nov final video)*

> "Zooming out to the project plan. This is where we've been and where we're going: threat model on 24 July, traffic generator by 27 July, the baseline detector by 10 August - so the core PoC you just saw was actually done well before today. We met with Fastweb on 2 September, and now Gate 1 today, 7 September.
>
> Ahead of us: Gate 2 performance hardening by 22 September, a storyboard for the demo video from 24 September, PoC evaluation and the video shoot through October, Gate 3's live PoC demo on 15 October, and the final video by 1 November."

---

### Slide 12 - High Level Plan
*(Visual roadmap / org-style diagram image)*

> "This is the same plan laid out visually - [point to the diagram] - foundation work already behind us, hardening and real-data integration in the middle, and the live Gate 3 demo as the finish line. I won't re-read every box, but the shape to notice is: **the risky, uncertain work is front-loaded and already done; what's left is refinement.**"

---

### Slide 13 - Risk Analysis
*(5 risks: real data not shared, FASTedge has no inline hook, detector doesn't generalise, timeline slip, team bandwidth)*

> "We did a proper risk pass rather than assuming everything goes to plan. Five risks, each with likelihood, severity, and how we'd handle it:
>
> - **Real data not shared in time** - medium likelihood, high severity - mitigation: stay synthetic-first, the baseline PoC already works without real data, so real data upgrades the result but doesn't block delivery.
> - **FASTedge has no inline policy hook** - medium/medium - we'd demo as a passive observe-and-alert system feeding a SOC workflow instead of inline enforcement - still a complete, useful PoC.
> - **Detector doesn't generalise to real traffic noise** - low likelihood, high severity - we'd validate early against any real sample offered, and keep the deterministic rules layer as a robust fallback alongside the ML model.
> - **Timeline slip before Gate 2 or 3** - low/medium - foundation and baseline detector are already complete ahead of schedule, giving us buffer.
> - **Team bandwidth / academic workload conflicts** - medium/low - clear task ownership per member, weekly sync, captain tracks blockers early.
>
> The pattern across all five: **our biggest structural risk - not having real data - is the one we deliberately designed around from day one.**"

---

### Slide 14 - Open Points
*(Table: Financial / Engineering / Communication / Presentation / Next Steps / AOB)*

> "A quick status table across the areas the committee will want visibility into:
>
> - **Financial** - no licensing cost, 100% open source, runs on a laptop today; production would add only light edge compute. Value case: cuts detection time from hours to seconds, enables safer network automation, and gives audit-ready evidence for NIS2, GDPR, and the EU AI Act. This is to be jointly costed and validated with Fastweb and Vodafone.
> - **Engineering** - synthetic traffic generator and baseline detector: **completed.** Detector hardening for recon and temporal features: **ongoing.** Real-data integration, if granted: **to be confirmed.**
> - **Communication** - the 2 September dev meeting with Fastweb and Vodafone: **completed.** Follow-up on data access, the FASTedge hook, and priority agent types: **TBD.**
> - **Presentation** - this deck's structure: **defined.** Speaking roles and the live dashboard walkthrough script: **TBD until final rehearsal.**
> - **Next steps** - Gate 2 performance hardening, real-data integration pending Fastweb/Vodafone's decision, and the Gate 3 live demo.
> - **AOB** - nothing raised at this time.
>
> This slide is really us saying: **here's exactly what's locked in, and here's exactly what's still open and depends on you.**"

---

### Slide 15 - Next Steps
*(Week-by-week: Week 1 Sep 8-14, Week 2 Sep 15-21, Week 3 Sep 22-28, Week 4 Sep 29-Oct 5, Final week Oct 6-15)*

> "Concretely, week by week from here:
>
> - **Week 1, Sep 8-14** - kick off Gate 2 hardening, add recon and temporal detection features, expand attack variants.
> - **Week 2, Sep 15-21** - finish the numerical performance analysis, prepare the Gate 2 report and deck.
> - **Week 3, Sep 22-28** - submit Gate 2, start dashboard hardening and the demo-video storyboard.
> - **Week 4, Sep 29-Oct 5** - integrate real data if granted, refine the live zero-trust gate dashboard.
> - **Final week, Oct 6-15** - final PoC integration, rehearsal, and the Gate 3 live demo delivery.
>
> So there's a clear, dated path from what you saw today to a live end-to-end demo at Gate 3."

---

### Slide 16 - Thank You / Closing
*(Confidentiality notice + "Thank you")*

> "That's AEGIS: a behavioural, zero-trust gate for machine identities on the 5G network, proven on synthetic traffic with 98% recall and under 1% false positives, with a clear, de-risked path to real-data validation alongside Fastweb and Vodafone. Thank you - we're happy to take questions, or to walk through the live dashboard in more depth if that's useful."

[If the live Streamlit demo is being shown separately from these 16 slides, this is the natural point to say: *"Before questions, let me show this actually running -"* and switch over. See the separate live-demo script for that walkthrough.]

---

## Timing guide (rough, adjust to your slot)
| Slides | Topic | Suggested time |
|---|---|---|
| 1-2 | Title + agenda | 30-45 sec |
| 3 | What we're building | 45 sec |
| 4-5 | Network primer + agents | 1.5 min |
| 6-7 | Build + tech stack | 1.5-2 min |
| 8-9 | Attacks + decision engine | 1.5-2 min |
| 10 | Results + caveat | 1 min |
| 11-12 | Roadmap/plan | 1 min |
| 13-14 | Risk + open points | 1.5 min |
| 15-16 | Next steps + close | 1 min |
| **Total** | | **~10-12 min** + Q&A |

## Notes for delivery
- Slides 6, 7, and 9 each contain an explicit "this is/isn't ML" clarification - hit those lines precisely. A committee of network engineers will notice if you blur "scripted simulation" and "machine learning," and being precise here builds credibility fast.
- Slide 10's caveat line is your strongest credibility move in the whole deck - say it before anyone can ask "but is this real data?"
- Slides 13-14 are where a technical committee tends to ask questions - know the risk table cold, especially Risk #1 and Risk #2.
- If time is tight, the safest slides to compress (not cut) are 11 and 12 - they repeat the same timeline in two forms.
