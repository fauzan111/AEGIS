# AEGIS — Gate 3 Video: Brief for the Videographer

One-page brief to hand to the videographer at the academy before the shoot. Full spoken script is in `docs/GATE-3/Gate3_Video_Script.md` — bring a printed or on-phone copy of that to set as a reference/teleprompter.

## What this is

A Gate 3 project presentation video for the 5G Academy program (Università di Napoli Federico II, Nokia, TIM). Two presenters, on camera, walking through what we built. Style should match the program's own back-catalogue of student project videos.

**Style reference:** youtube.com/@5gacademy277 — closest matches to what we're going for are "MEI | Project Work | 5G Academy 2025" (5:21), "SmartTrainer | Project work | 5G Academy 2024" (9:47), and "BufalaCare | Project work | 5G Academy 2024" (13:22). Same channel, same academic-presentation tone: two people talking through their project clearly and directly, not a marketing ad.

## Format

- Two presenters on camera, splitting sections (see script for exact split).
- **No slides or screens need to be in the shot.** We talk continuously to camera; you cut in our provided graphics, screenshots, and a screen recording during editing. This keeps the shoot simple: just film us clearly and cleanly, no monitor/projector setup needed in the room.
- Target final runtime: ~8 minutes.
- Aspect ratio / resolution: 16:9, 1920x1080 (matches every other visual asset in the project).

## Shot list

Film each script segment as its own clean take (easier to re-take a bad section without reshooting the whole thing). Segment numbers match `Gate3_Video_Script.md`:

| # | Segment | Who's on camera | Approx length |
|---|---|---|---|
| 1 | Cold open | Both | 0:30 |
| 2 | Problem + what AEGIS is | Fauzan | 1:00 |
| 3 | How it works (pipeline) | Llagami | 1:30 |
| 4 | Live demo | **Voice-over only, no camera** — record separately, timed to the screen recording | 2:00 |
| 5 | Gate 3 real-core validation | Llagami | 1:30 |
| 6 | Results | Fauzan | 1:00 |
| 7 | Close | Both | 0:30 |

Also worth grabbing, if time allows, for editing flexibility:
- A few extra seconds of B-roll: both of us walking into the lab/office, sitting down, general working shots.
- One or two wide shots of the room/set, for cutaways between segments.
- Individual clean takes of segments 2, 3, 5, and 6 with a beat of silence before/after each line, easier to trim than a single unbroken take.

## Assets to hand over for editing

Everything below already exists, no new graphics need to be made:

- `assets/architecture.png` — system architecture diagram (segment 2)
- Pipeline / decision-system graphic from `slides/GATE-2/AEGIS_Gate2_Official.pptx` (segment 3)
- `docs/GATE-3/threat-model-external-mapping.md` table, or a simple graphic version of it (segment 3)
- Screen recording of the live dashboard walkthrough — either reuse `slides/GATE-2/AEGIS_Live_Demo.mp4` if it already covers scenario-pick → launch → reveal → topology, or record fresh (segment 4)
- `reports/GATE-3/storyboard-shots/dash_home.png`, `dash_live_attack.png`, `dash_incident_inspector.png`, `dash_topology.png` (segment 4, as stills if a fresh recording isn't available in time)
- `reports/GATE-3/storyboard-shots/open5gs_terminal.png` (segment 5)
- A simple "2 / 2 real attack windows correctly blocked" stat card (segment 5)
- A stats graphic: ROC-AUC 0.979, recall 91.6%, FP rate 1.44% (segment 6)
- The Gate 2 SPC baseline comparison graphic, 0.965/90.7% vs. 0.944/63.4% (segment 6, labeled clearly as a Gate 2 result)
- `reports/GATE-2/aegis_hook_analogy.png` (segment 1 open, hold 2 seconds)
- AEGIS logo + tagline card (segment 7 close)

## Questions to settle with the videographer on the day

- Do they want the full script read once through per segment, or line-by-line with pauses for easier editing? (Our default: whole segment per take, see shot list above.)
- Delivery format and deadline for the edited file.
- Whether they'd rather receive the graphic files ahead of time or on a USB/drive at the shoot.

## Contact / team

Fauzan Ejaz (Captain), Llagami Tedi — AEGIS, Team 4.
