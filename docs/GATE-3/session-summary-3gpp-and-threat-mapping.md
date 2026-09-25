# What was added: 3GPP endpoint grounding + FiGHT/GSMA threat mapping

Summary of the two additions made in this pass, and - honestly - what each
one does and does not change in the dashboard, the detection model, and the
project overall. These are two very different kinds of change: one touches
running code, the other touches only documentation.

## 1. 3GPP-accurate NF endpoint catalog (code change)

**What changed:** `NF_ENDPOINTS` in `AEGIS/src/generate_synthetic_traffic.py`
went from 2-3 endpoints per Network Function to 4-5, all drawn from the real
3GPP service catalogue for that NF (TS 29.518 AMF, TS 29.502 SMF, TS 29.510
NRF, TS 29.507/512/514 PCF, TS 29.503 UDM, TS 29.522 NEF) - e.g. added
`Nnrf_AccessToken/get`, `Npcf_AMPolicyControl/create`,
`Nudm_UEContextManagement/registration`.

**Effect on the model:** re-ran the full evaluation after the change.
ROC-AUC held at 0.979, recall improved slightly (90.5% -> 91.6%), false
positive rate ticked up marginally (1.11% -> 1.44%, still under the ~1.5%
design budget). All 10 attack variants still detect cleanly. Nothing broke -
the wider endpoint variety mostly just gives legitimate agents' baselines a
slightly richer, more realistic shape to learn from.

**Effect on the dashboard:** the dashboard reads whatever endpoint strings
show up in the scored data - nothing is hardcoded to the old short endpoint
list, so no dashboard code needed to change. What *will* look different: the
incident inspector, the raw event table, and any "which endpoint did this
touch" detail will now sometimes show the new, more specialised endpoint
names instead of only the original handful. To someone who knows 5G specs,
this reads as "a real core's traffic," not "a simplified demo model."

**Effect on the project overall:** this is a genuine, if modest, realism
upgrade to the actual system - both the synthetic generator and the earlier
real-traffic validation work are now checked against a broader, more
representative slice of what a real core actually exposes, not just the
minimum surface needed to make the T1-T7 story work.

## 2. MITRE FiGHT / GSMA / ENISA threat-model mapping (documentation only)

**What changed:** a new doc,
`docs/GATE-3/threat-model-external-mapping.md`, mapping AEGIS's T1-T7 threat
categories against MITRE's FiGHT framework (the ATT&CK-equivalent for 5G)
and GSMA/ENISA's public security guidance, with real, verified citations.
5 of 7 threats (T1, T3, T4, T5, T7) match named external attacker
techniques; T2 and T6 have no match in either framework, stated plainly as
AEGIS's own behavioral contributions rather than forced into a fit.

**Effect on the model:** none. No code changed, no detection logic changed,
nothing in `aegis_detect.py` or the generator was touched for this piece.

**Effect on the dashboard:** none directly - the live Streamlit dashboard
doesn't display threat-model documentation, only live detection results, so
there's nothing to see here when running the app.

**Effect on the project overall:** this is entirely a credibility/narrative
upgrade for the Gate 3 report and any future presentation. It changes the
threat model's framing from "seven categories we invented" to "five
categories with recognized external precedent, plus two behavioral patterns
that go beyond what published frameworks currently define" - a stronger,
more defensible claim to make to a technical committee, but it doesn't
change how AEGIS actually behaves at runtime.

## The one-line distinction to keep in mind

The endpoint expansion changed the *system* a little; the threat-model
mapping changed the *story* a lot, changed the *system* not at all. Both are
worth having for Gate 3, but they answer different questions: "does this
look like a real core" (endpoints) versus "is this threat model taken
seriously outside our own project" (FiGHT/GSMA).
