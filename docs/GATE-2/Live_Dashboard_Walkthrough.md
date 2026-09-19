# AEGIS Live Dashboard - Full Walkthrough Script

**URL:** https://aegis5gacademy.streamlit.app/
**Source:** `src/aegis_dashboard.py`

This is a complete, section-by-section script for explaining the live dashboard out loud - what's on screen, what to click, and what to say. Read it once end to end before presenting so the flow feels natural, not read off a page. Roughly 8-10 minutes if you go through everything; cut to the starred (★) sections if you only have 3-4 minutes.

---

## 1. Hero banner (10 sec)

What's on screen: the Fastweb + Vodafone badge, "Together, we secure the network," the tagline, and an EN/IT toggle.

> "This is the live AEGIS dashboard - the actual system running, not a mockup. Every number and chart you're about to see comes from the same pipeline we described on the slides, scoring real synthetic 5G traffic."

Point out the IT/EN toggle briefly - it's a nice detail showing the project was built with a real operator audience in mind, but don't dwell on it.

---

## 2. Sidebar controls (20 sec)

What's on screen (left rail): STEP-UP threshold slider (default 0.60), BLOCK threshold slider (default 0.85), and an Agents multiselect showing all 5 agent identities.

> "On the left are the two decision thresholds - STEP-UP and BLOCK - and they're not fixed. I can drag either one live and every chart, every count on this page recalculates instantly. This is exactly the kind of dial a SOC operator would tune for their own risk appetite. Below that, I can filter the whole view down to specific agents."

★ **Optional live moment:** drag the BLOCK slider up or down a little and point out the KPI row (next section) changing in real time. Great way to show the app is actually alive, not a screenshot.

---

## 3. KPI row (10 sec)

What's on screen: six stat cards - Windows, PASS, STEP-UP, BLOCK, Attack recall, False-positive rate.

> "These six numbers summarise everything scored so far under the current thresholds and agent filter - how many windows, how the gate decided, and our two headline metrics: recall and false-positive rate."

---

## 4. ★ Live Attack Injection (2-3 min) - the centerpiece

This is the section to spend the most time on. It's the only part of the dashboard that runs the detection pipeline live, in front of the audience, instead of replaying pre-scored history.

What's on screen: a red-dot "Live Attack Injection" header, a caption, a Scenario dropdown (7 real threat types), and a "Launch live attack" button.

> "Everything below this point in the dashboard is browsing history - already-scored traffic. This section is different: it's live. I pick a real attack scenario, click launch, and the actual traffic generator and the actual rules-plus-ML pipeline run right now, scoring it in real time."

**Step 1 - pick a scenario.**
> "Let's say T1 - identity spoofing." *(select it, read the one-line description that appears)* "A valid credential for the NRF heartbeat service starts behaving like a different role."

**Step 2 - launch it.**
Click "🚀 Launch live attack."
> "Watch what happens." *(narrate the two progress messages as they appear: "Generating live attack traffic..." then "Scoring with the live rules+ML pipeline...")* "That's not a canned animation - it's actually building the attack traffic and running it through the same Isolation Forest and rule engine we described on the slides."

**Step 3 - the reveal: Before AEGIS / With AEGIS.**
This is the strongest single moment in the whole demo. Two columns appear side by side.

> "Here's the comparison that matters. On the left - **Before AEGIS** - a classic credential-only check. It's always green, always 'ALLOWED,' because a stolen or misused credential is still a technically valid credential. Classic authentication checks the token, never the behaviour behind it.
>
> On the right - **With AEGIS** - the real decision: *(read whatever it says, e.g.)* **BLOCKED - quarantined, SOC alerted.**
>
> Same exact attack traffic. One side lets it straight through. The other catches it. That's the entire pitch of this project in one screen."

**Step 4 - the why.**
Below the two columns: Agent / Risk score / Decision metrics, then "Why AEGIS decided this."

> "And it's not a black box - it tells you exactly why. *(read the bullet reasons aloud, e.g.)* 'Rule fired: out-of-scope access...' 'ML anomaly: the Isolation Forest finds this window unlike the agent's known-good baseline.' An analyst gets a plain-language reason, not just a number."

If the decision isn't PASS, point out the key-icon line:
> "🔑 This agent's credential was completely valid - the block is on behaviour, not identity. That's the zero-trust gap this whole project closes."

**Step 5 - run it again with a different scenario (if time allows).**
> "Let me pick a completely different attack type - T4, volumetric abuse." *(launch it)* "Same mechanism, different threat, same real-time scoring."

Point out the **Recent live triggers** table that's now accumulating a log of every scenario you've launched this session - agent, decision, risk score, timestamp.

> "This builds a running log for the session, so if you want to see three or four different attack types back to back, they're all here."

**If the panel wants to try it themselves:** let them pick a scenario and click launch. This is genuinely the best moment to hand over control - it's far more convincing when they trigger it, not you.

---

## 5. Tab 1 - Live overview (30 sec)

Click the "Live overview" tab (this is the default/first tab).

What's on screen: a "Risk over time" scatter plot (blue = legit, red X = attack) and a "Detection per threat" bar chart, plus a scrolling "Live event feed" below.

> "This tab is the historical view - all ~11,000 scored windows from our evaluation set. Blue dots are legitimate traffic sitting low near zero risk; red X's are actual attacks, and you can see them cluster up near the threshold lines. Next to it, detection rate broken down per threat type - you can see at a glance which threats are easy versus hard for us."

Point at the live event feed:
> "And this is a scrolling feed of the most recent flagged incidents - agent, decision, risk score, and the actual reason - like a real SOC alert stream."

---

## 6. Tab 2 - Network topology (1 min) - now animated

Click the "Network topology" tab.

What's on screen: a bipartite graph - agents on the left, 5G Network Functions (AMF, SMF, NRF, PCF, UDM, NEF) on the right, connected by thin grey lines showing each agent's authorized scope.

> "This is the agent-to-network-function map. Grey lines are what each agent is *supposed* to touch, based on its onboarding scope."

**If you land here right after launching a live attack** (do this deliberately - launch an attack, then immediately switch to this tab):
> "Watch this - because I just launched a live attack, the graph pulses in the highlighted path in real time." *(the edge visibly grows from thin/faint to thick/bright over a few frames)* "That's the actual incident I just triggered, not old data. Solid line means in-scope; dashed line means a scope violation - a network function this agent was never authorised to touch."

Read the caption below the graph:
> "'Most recent incident shown: [agent] at just now (live attack), decision [X], touching NF(s): [list].' - this always reflects whichever incident is freshest, live attack or historical replay."

---

## 7. Tab 3 - Incident inspector (1 min)

Click the "Incident inspector" tab.

What's on screen: a sortable table of every flagged window (STEP-UP or BLOCK), highest risk first, and a dropdown to inspect any individual one.

> "This is what a SOC analyst would actually use day to day. Every flagged window, sortable, with the rule score and ML score broken out separately."

Select a high-risk row from the dropdown.
> "Pick one, and you get the full picture: the decision, the risk breakdown between rule and ML, which network functions it touched, and - same as the live attack panel - a plain-language reason why. At the bottom, since this is synthetic data we control, we can even show ground truth: was this really an attack, or a false positive?"

---

## 8. Closing line (10 sec)

> "So end to end: adjustable thresholds, a live-attack panel that runs the real pipeline in front of you, an animated topology view, and a fully explainable incident inspector - all running against the same numbers we walked through on the slides. This isn't a demo of a demo - it's the actual system."

---

## Quick reference: talking points if asked questions mid-demo

- **"Is this real-time on real network traffic?"** No - synthetic 5G SBA traffic, generated and scored live in front of you. Explicitly flagged as the honest caveat on the slides; real traffic integration is the next validation step.
- **"What happens if I change the thresholds during a live attack?"** The Live Attack Injection panel respects whatever the sidebar sliders are currently set to - drag BLOCK up before launching an attack and you'll see it correctly downgrade to STEP-UP if the risk score no longer clears the new bar.
- **"Can I trigger more than one attack type?"** Yes - the scenario dropdown has all 7 threats (T1-T7), and the "Recent live triggers" table keeps a running log of everything launched in the session.
- **"Why does [scenario] always hit the same agent?"** Each of the 7 scenarios reuses the exact, already-validated attacker/victim pairing from the threat model (e.g. T1 always targets the NRF heartbeat service) - not arbitrary, it's the same design used in the Gate 2 numerical evaluation.

## Practical notes for presenting

- **First load is slower.** The app fits its baselines from ~210,000 rows the first time anyone launches a live attack after a cold start (Streamlit Cloud spins the app down when idle). Launch one attack scenario yourself a minute or two before the audience arrives so the cache is warm and the live-attack response feels instant.
- **Have a scenario picked in advance** for the live moment (T1 or T4 read clearly on screen and produce a clean BLOCK), but don't be afraid to let the panel choose - the pipeline handles all 7 correctly.
- **If Streamlit Cloud is asleep** when you arrive, it needs ~30-60 seconds to wake up on first load - open the tab early.
