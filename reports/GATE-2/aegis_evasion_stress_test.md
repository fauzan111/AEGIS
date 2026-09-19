# AEGIS - Adversarial Evasion Stress Test

## Method

All seven threats in the main evaluation are naive - none deliberately paced against AEGIS's thresholds. The original T4 injector floods SMF, which is outside the attacking agent's own scope - that also trips the hard, pacing-independent scope-violation rule, confounding a clean test of whether pacing alone evades detection. This test instead floods an endpoint INSIDE the attacker's normal scope (AMF), isolating the rate signal, and compares the identical total illegitimate request volume delivered as a 1-hour burst versus paced across 24 hours. Both variants are injected onto the same freshly-generated legit traffic base and scored with the unmodified rules+ML pipeline.

## Result

| Variant | T4 windows | Detected | Median requests/window |
|---|---|---|---|
| Loud (1hr burst) | 60 | **100%** | 62 |
| Evasive (24hr paced) | 1254 | **0%** | 14 |

**Pacing the same attack volume over 24x more time drops detection by 100 percentage points.** This is expected, not a bug: the current volumetric rule and the ML layer both key on per-window request count, and diluting the flood thinly enough defeats a per-window signal by construction - the same reason T3/T5 already use a rolling cross-window accumulator instead of a single-window check. T4 currently does not have an equivalent rolling accumulator.

## Honest implication
This is a real, demonstrated gap, not a hypothetical one: an attacker aware of the 60-second window and the rate threshold could evade the current volumetric detector by pacing. The direct fix - a rolling cumulative-volume accumulator for T4, mirroring the existing rolling breadth/payload accumulators already used for T3 and T5 - is scoped as concrete Gate 3 hardening work, prioritised ahead of the recon/exfil hardening already planned, since this test shows it is the more immediately exploitable gap.
