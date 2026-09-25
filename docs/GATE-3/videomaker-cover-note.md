# Cover note for the videomaker briefing

Quick summary ahead of the storyboard alignment meeting - full detail is in
`slides/GATE-3/AEGIS_Gate3_Storyboard.pptx`, this is just the "what's ready
vs. what we need to shoot" breakdown so the meeting can move fast.

**Total runtime target:** ~2:45, 8 storyboard pages, 48 shots.

## Already have it - just needs editing in

- **The entire live-demo section is already recorded**: `AEGIS_Live_Demo.mp4`
  covers the dashboard walkthrough, live attack injection, risk score
  climbing, the decision moment, and the before/after comparison. This is
  the single biggest reuse - most of the "parte test" page needs no new
  shooting at all.
- **Architecture and pipeline visuals**: the architecture diagram and the
  OBSERVE/FINGERPRINT/SCORE/DECIDE pipeline cards, PASS/STEP-UP/BLOCK
  decision pills, and the Open5GS real-core diagram all exist as slides
  already (Gate 2 deck + `assets/architecture.png`).
- **The badge/network hook graphic** (the "office vs. network" comparison
  image) is already built and used as our own Gate 2 hook slide.
- **Branding, logo, and closing links** slide already exists (Gate 2 deck,
  Slide 19).

## Needs fresh shooting (live-action)

- Opening hook: an ID badge scan at a door (a few seconds, sets up the whole
  video's framing).
- Brief team B-roll (working at laptops).
- A NOC/SOC-operator-style shot for the problem section.
- Screen recording: the real Open5GS core starting up in Docker, and a real
  device registering onto it - this is new, but it's just recording work
  we've already done technically, not new engineering.
- Screen recording: the incident inspector panel's plain-language
  explanation, live on the dashboard.

## Needs fresh graphics/text cards (no shooting, just design)

- A handful of text/tagline cards (zero-trust line, closing tagline, "trust
  can't be a one-time check").
- A business-impact graphic for the problem section.
- A privacy/GDPR concept graphic and a production-deployment (network-edge)
  concept graphic - both already written up conceptually in
  `docs/GATE-3/real-vs-synthetic-dashboard-implications.md`, just need a
  visual treatment.
- A small results graphic pulling our real-traffic detection result (2 of 2
  real attack windows correctly flagged) into a clean on-screen stat.

## Bottom line for the meeting

Most of the video's technical substance already exists in some form - the
job is mostly editing, a short list of new screen recordings, and a handful
of live-action B-roll shots, not building new material from scratch.
