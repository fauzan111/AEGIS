# AEGIS — Gate 3 Video Script

Word-for-word script for the Gate 3 project video. Format: two presenters on camera in a lab/office set, cutting to slides, graphics, and screen recordings while they talk. Target runtime ~8 minutes, in line with past 5G Academy project-work videos (MEI 5:21, SmartTrainer 9:47, BufalaCare 13:22).

Speaker labels: **FAUZAN** and **LLAGAMI**. Swap lines freely if a different split feels more natural once you're rehearsing out loud — the timing per segment matters more than who says which exact sentence.

Every `[CUT TO: ...]` cue points at a file that already exists in this repo. Nothing here requires new graphics.

---

## Segment 1 — Cold open (0:00–0:30)

**Both, on camera, lab background.**

**FAUZAN:** A stolen ID badge still opens the door. The lock doesn't know it's not you.

**LLAGAMI:** Now picture that badge isn't a person. It's an AI agent, or an automated script, calling into a live 5G core. Same problem. Bigger blast radius.

**FAUZAN:** We're Fauzan and Llagami. This is AEGIS.

[CUT TO: reports/GATE-2/aegis_hook_analogy.png, hold 2 seconds]

---

## Segment 2 — The problem and what AEGIS is (0:30–1:30)

**FAUZAN, on camera.**

A 5G core isn't one system. It's a mesh of network functions, AMF, UDM, SMF, PCF, talking to each other constantly over an API layer called the Service-Based Interface. And increasingly, it's not just humans and devices calling into that mesh. It's automation. Orchestration agents, provisioning scripts, AI-driven operations tools, all with real credentials and real access.

The problem is: a credential check only proves you have the key. It says nothing about whether you're using it the way you're supposed to.

[CUT TO: assets/architecture.png]

That's what AEGIS does. It's a zero-trust behavioural layer that sits on top of the credential check. It doesn't ask "is this token valid." It asks "does this agent's behaviour still look like itself."

---

## Segment 3 — How it works (1:30–3:00)

**LLAGAMI, on camera.**

[CUT TO: pipeline graphic — slides/GATE-2/AEGIS_Gate2_Official.pptx pipeline slide, or reports/GATE-2 architecture panel showing OBSERVE / FINGERPRINT / SCORE / DECIDE]

AEGIS runs every call through four stages. OBSERVE logs every request an agent makes, and every call pattern behind it. FINGERPRINT turns that into a behavioural signature, unique per agent. SCORE compares that signature against what's normal, using two layers together: deterministic rules, and an Isolation Forest model trained only on legitimate traffic. DECIDE turns the combined score into one of three outcomes: pass it through, step up and verify, or block it outright.

We built this against seven distinct threat patterns, things like identity spoofing, reconnaissance, slow data exfiltration, an agent quietly drifting outside its authorised scope. And this gate, we checked it against a real published framework. Five of our seven threats map directly onto named attacker techniques in MITRE FiGHT, the ATT&CK equivalent for 5G. The other two, we're upfront about it: they're behavioural patterns we catch that neither FiGHT nor GSMA's own threat catalogue currently names.

[CUT TO: docs/GATE-3/threat-model-external-mapping.md table, or a simple on-screen graphic of the T1–T7 mapping]

---

## Segment 4 — Live demo (3:00–5:00)

**Both, voice-over a screen recording of the live dashboard.**

**FAUZAN:** Let's show you, live.

[CUT TO: screen recording — dashboard home / scenario picker, reports/GATE-3/storyboard-shots/dash_home.png as the opening frame]

**FAUZAN:** This is the AEGIS dashboard. We pick an attack scenario here, credential replay, and launch it.

[CUT TO: screen recording — live attack injection, reports/GATE-3/storyboard-shots/dash_live_attack.png]

**LLAGAMI:** This isn't a replay of pre-recorded data. It's the real detection pipeline scoring live traffic as it happens. Watch the risk score.

*[pause for the risk score to climb on screen]*

**LLAGAMI:** And there it is. Same attack that would pass a credential-only check gets flagged and blocked here, because the behaviour doesn't match the agent's history.

[CUT TO: screen recording — incident inspector, reports/GATE-3/storyboard-shots/dash_incident_inspector.png]

**FAUZAN:** Every decision comes with a plain-language explanation. Not a black box. You can see exactly which rule or which score pushed this over the line.

[CUT TO: screen recording — network topology view, reports/GATE-3/storyboard-shots/dash_topology.png]

**FAUZAN:** And this view shows the whole picture at once. Every agent, its authorised scope, and the one that just stepped outside it.

---

## Segment 5 — Gate 3: proving it against a real core (5:00–6:30)

**LLAGAMI, on camera.**

Everything up to now, including Gate 2, was validated against synthetic traffic we generated ourselves. For Gate 3, we wanted to know: does this actually hold up against a real 5G core, not just our own simulation.

[CUT TO: reports/GATE-3/storyboard-shots/open5gs_terminal.png]

So we stood up a real Open5GS 5G core, brought up a real UE with UERANSIM, and captured the actual signalling traffic. First thing we checked: does our synthetic data even look like the real thing. It does, almost exactly. The endpoint names and call patterns our generator produces match real captured 3GPP service calls.

**LLAGAMI:** Then we went further. We ran real attack-like traffic, not simulated, straight into AEGIS's actual detection code, completely unmodified. Two out of two real attack windows were correctly flagged and blocked.

[CUT TO: simple on-screen stat card — "2 / 2 real attack windows correctly blocked"]

**LLAGAMI:** That's a small-scale result, we're honest about that in our own report. But it's proof the detection logic works on traffic that never touched our synthetic generator.

---

## Segment 6 — Results (6:30–7:30)

**FAUZAN, on camera.**

[CUT TO: stats graphic — ROC-AUC 0.979, recall 91.6%, false positive rate 1.44%]

For Gate 3 we also widened the catalogue, from five agents and seven threats to seven agents and ten threat variants, including two deliberately extreme agent profiles. Across all of that, AEGIS holds at 0.979 ROC-AUC, 91.6 percent recall, and a 1.44 percent false positive rate, inside our own 1.5 percent budget.

We also hardened the two weakest spots we found at Gate 2. Reconnaissance detection went from 80 to 95 percent. Exfiltration went from 76 to 80. Both bootstrap-validated, not a lucky run.

[CUT TO: Gate 2 SPC baseline comparison graphic, framed as "at Gate 2" — AEGIS 0.965 ROC-AUC / 90.7% recall vs. the SPC statistical baseline at 0.944 / 63.4%]

**FAUZAN:** And going back to Gate 2, when we benchmarked against a real published baseline, a statistical process control detector, the same one used in industrial monitoring, AEGIS caught 90.7 percent of attacks against the baseline's 63.4.

---

## Segment 7 — Close (7:30–8:00)

**Both, on camera.**

**LLAGAMI:** A credential proves what you have.

**FAUZAN:** AEGIS verifies how you behave.

**Both:** Thanks for watching.

[CUT TO: AEGIS logo card, tagline beneath]

---

## Notes for the shoot

- **Pacing:** the word counts above land near 130 words per minute, a comfortable, clear pace. Read each segment out loud once before shoot day and adjust — if either of you naturally reads faster or slower, retime rather than rushing on camera.
- **Segment 4 (live demo):** this is voice-over, not on-camera talking. Record the screen capture first (or reuse `AEGIS_Live_Demo.mp4` if it already covers this exact flow), then record the voice-over separately timed to the footage. Easier to get both right than doing it live in one take.
- **Segment 5's stat card:** keep it to the "2 / 2" framing exactly as validated. Don't round it up into a bigger claim, the real-traffic test was small-scale and the report says so plainly, the video should match.
- **Segment 6's SPC comparison:** that comparison was run at Gate 2, on the original 5-agent/7-threat catalogue, not the widened Gate 3 one. The script above frames it that way ("going back to Gate 2") deliberately, don't blur the two into one claim.
- **Wardrobe/set:** matches the dashboard's own dark navy and cyan palette if you want a visual through-line, but plain and professional is fine too.
