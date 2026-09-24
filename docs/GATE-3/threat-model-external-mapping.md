# AEGIS threat model (T1-T7) vs. external frameworks

Grounds AEGIS's seven threat categories against two real, independently
published sources: **MITRE FiGHT** (the ATT&CK-equivalent technique
framework specifically for 5G networks) and **GSMA FS.57 (MoTIF)** / the
**ENISA 5G Threat Landscape** report. The goal isn't to force a clean 7-for-7
match - it's to show which of AEGIS's threats correspond to named,
externally-recognised attacker techniques, and to be honest about which ones
are AEGIS's own behavioral distinctions rather than a technique someone else
has already catalogued.

Method: pulled the live FiGHT technique pages directly (fight.mitre.org),
cross-checked against GSMA's FS.57 "MoTIF Principles v1.0" document and the
ENISA "Threat Landscape for 5G Networks" report (Dec 2020). Every ID below
was confirmed against a live source, not recalled from memory - where no
clean match could be verified, that's stated plainly rather than papered
over.

## The mapping

| # | AEGIS threat | FiGHT tactic + technique(s) | GSMA / ENISA | Confidence |
|---|---|---|---|---|
| **T1** Identity spoofing | Credential Access / Lateral Movement - **FGT5043** "Unauthorized Access To Core Network Function Via Token Abuse"; **FGT1078** "Valid Accounts" | GSMA FS.57 MOT1212 "Exploitation for Credential Access" - same pattern (stolen credential, abnormal use), different interface family (legacy Diameter, not SBI/OAuth) | Good match |
| **T2** Compromised agent (in-scope drift) | No clean match - closest adjacent is FGT1078 "Valid Accounts", but FiGHT has no technique for "drifts to new endpoints while staying within authorized scope" | No clean match | **AEGIS's own contribution** - see note below |
| **T3** Reconnaissance | Discovery/Reconnaissance - **FGT1046** "Network Service Discovery" (+ FGT1046.501 Protocol Fingerprinting); **FGT5003** "Network Function Service Discovery" | GSMA FS.57 reuses both verbatim (MOT5003, MOT1046) - MOT5003 is marked **"5G-SA: Demonstrated"** by GSMA, i.e. observed in the field, not just theoretical | Strong match |
| **T4** Volumetric abuse | Impact - **FGT1498** "Network Denial of Service" -> **FGT1498.501** "Flooding Core Network Component" | FGT1498.501 cites **ENISA's 5G Threat Landscape report (Dec 2020) directly** - a confirmed FiGHT-to-ENISA citation. GSMA FS.57 has no DoS/flooding technique defined at all. | Strong match |
| **T5** Slow exfiltration | Collection - **FGT5020** "Retrieve UE Subscription Data" (a compromised NF queries UDM for full subscription data per SUPI, since "the UDM does not check that the AMF is the one serving the UE") | GSMA FS.57 MOT5019.302/.303 "Retrieve Subscriber Identity/Network Information" | Good match (the specific "low-and-slow, off-hours" timing signature is AEGIS's own framing, not in the source docs) |
| **T6** Sequence anomaly (orphan PDU-session ops) | No clean match - closest adjacent are FGT5021 "Tunnel ID Uniqueness Failure" and FGT1572.501 "UE Access Via GTP-U", neither of which describes referencing a session that was never validly created | GSMA FS.57's only session/state-integrity technique is MOT1565.001 "Stored Data Manipulation" (deleting a record) - data manipulation, not a broken call-sequence pattern | **AEGIS's own contribution** - see note below |
| **T7** Scope creep | Credential Access/Lateral Movement - **FGT5043.001** "Exploit OAuth2 Scope" - a near-exact match: "the NF Service Consumer can request access to resources beyond its intended scope by including 'additional scope' parameters... gain unauthorized access to various API endpoints and services" | No verified GSMA/ENISA-specific citation for OAuth-scope exploitation | Strong match |

## The honest finding worth stating in the report

Five of seven threats (T1, T3, T4, T5, T7) map onto named, externally
published attacker techniques - three of them (T3, T4, T7) are strong,
near-exact matches, and T4's mapping is independently confirmed by ENISA's
own published threat landscape report, not just FiGHT's say-so.

**T2 (compromised agent, in-scope drift) and T6 (sequence anomaly, orphan
session ops) have no clean match in either framework.** That's not a gap in
AEGIS's threat model - it's the opposite. Both FiGHT and GSMA's MoTIF
catalogue *what an attacker does* (steal a credential, scan for services,
exploit an OAuth scope). AEGIS additionally detects behavioral distinctions
neither framework names as a discrete technique: an agent that drifts
subtly while never technically leaving its authorized scope, and a PDU
session state machine that catches operations referencing a session that
was never validly created in the first place. Worth stating plainly in the
Gate 3 report as a genuine contribution rather than quietly working around
it: **AEGIS's detection model covers five threats with recognized external
precedent, and two behavioral patterns that go beyond what either published
framework currently defines.**

## Sources

- MITRE FiGHT: fight.mitre.org/techniques/FGT5043, FGT5043.001, FGT1078,
  FGT1046, FGT1046.501, FGT5003, FGT1498, FGT1498.501, FGT5020, FGT5021,
  FGT1572.501
- GSMA FS.57 "MoTIF Principles v1.0" (gsma.com)
- ENISA, "Threat Landscape for 5G Networks" report, December 2020
  (enisa.europa.eu)
