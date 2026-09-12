# -*- coding: utf-8 -*-
"""
AEGIS - synthetic agent / API traffic generator (5G SBA-style).

Produces a labelled dataset of control-plane API requests made by machine agents
to 5G Network Functions over the Service-Based Interface (SBI). A handful of
LEGITIMATE agents each have a stable behavioural profile (which NFs/endpoints
they call, timing, method mix, call-sequence graph, active hours). We then inject
ATTACK episodes that reuse a valid agent identity but behave abnormally, covering
threats T1-T7 from the threat model.

Output: data/aegis_traffic.csv  (one row per request, fully labelled)

Run:  .venv/Scripts/python AEGIS/src/generate_synthetic_traffic.py
"""

from __future__ import annotations
import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG_SEED = 42
random.seed(RNG_SEED)
np.random.seed(RNG_SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ------------------------------------------------------------------ 5G SBA surface
# Network Functions and a few representative SBI endpoints each (Nnf_Service style).
NF_ENDPOINTS = {
    "AMF": ["Namf_Communication/UEContextTransfer", "Namf_EventExposure/subscribe",
            "Namf_MT/EnableUEReachability"],
    "SMF": ["Nsmf_PDUSession/create", "Nsmf_PDUSession/update", "Nsmf_PDUSession/release"],
    "NRF": ["Nnrf_NFManagement/register", "Nnrf_NFDiscovery/search",
            "Nnrf_NFManagement/heartbeat"],
    "PCF": ["Npcf_SMPolicyControl/create", "Npcf_PolicyAuthorization/subscribe"],
    "UDM": ["Nudm_SDM/get", "Nudm_UEAuthentication/get", "Nudm_SDM/subscribe"],
    "NEF": ["Nnef_EventExposure/subscribe", "Nnef_ParameterProvision/update"],
}
ALL_NFS = list(NF_ENDPOINTS)
ENDPOINTS_OF = {nf: eps for nf, eps in NF_ENDPOINTS.items()}
METHODS = ["GET", "POST", "PUT", "DELETE"]


def endpoint_method(endpoint: str) -> str:
    """Rough method by endpoint verb."""
    if any(k in endpoint for k in ["get", "search", "Discovery", "reachability", "Reachability"]):
        return "GET"
    if "release" in endpoint or "Release" in endpoint:
        return "DELETE"
    if "update" in endpoint or "heartbeat" in endpoint:
        return "PUT"
    return "POST"


# ------------------------------------------------------------------ legit agent profiles
# Each agent has: a scope (NFs it is allowed to touch), a typical request rate,
# active hours, a payload size range, and a preferred call sequence (Markov-ish).
AGENTS = {
    "orch-session-mgr": dict(  # session orchestration automation
        scope=["SMF", "PCF", "AMF"], rate_per_min=(8, 16), active_hours=(0, 24),
        payload=(200, 1200), err_rate=0.01,
        seq=["Nsmf_PDUSession/create", "Npcf_SMPolicyControl/create",
             "Nsmf_PDUSession/update", "Nsmf_PDUSession/release"]),
    "oss-inventory-job": dict(  # nightly inventory / discovery job
        scope=["NRF", "UDM"], rate_per_min=(3, 7), active_hours=(1, 5),
        payload=(120, 600), err_rate=0.02,
        seq=["Nnrf_NFDiscovery/search", "Nudm_SDM/get"]),
    "closed-loop-assurance": dict(  # closed-loop automation (OODA) telemetry subscriber
        scope=["AMF", "NEF", "PCF"], rate_per_min=(10, 20), active_hours=(0, 24),
        payload=(150, 900), err_rate=0.015,
        seq=["Namf_EventExposure/subscribe", "Nnef_EventExposure/subscribe",
             "Npcf_PolicyAuthorization/subscribe"]),
    "nrf-heartbeat-svc": dict(  # steady NRF registration/heartbeat service
        scope=["NRF"], rate_per_min=(4, 8), active_hours=(0, 24),
        payload=(80, 300), err_rate=0.005,
        seq=["Nnrf_NFManagement/register", "Nnrf_NFManagement/heartbeat"]),
    "provisioning-agent": dict(  # subscriber provisioning via NEF/UDM
        scope=["NEF", "UDM"], rate_per_min=(2, 6), active_hours=(6, 22),
        payload=(200, 1500), err_rate=0.02,
        seq=["Nnef_ParameterProvision/update", "Nudm_SDM/subscribe"]),
}

BASE_DAY = datetime(2026, 8, 3, 0, 0, 0)  # a Monday
N_DAYS = 5


def pick_endpoint(agent_cfg, prev_ep):
    """Prefer the agent's normal sequence; occasionally jump within scope."""
    seq = agent_cfg["seq"]
    if prev_ep in seq and random.random() < 0.75:
        i = seq.index(prev_ep)
        return seq[(i + 1) % len(seq)]
    if random.random() < 0.6:
        return random.choice(seq)
    nf = random.choice(agent_cfg["scope"])
    return random.choice(ENDPOINTS_OF[nf])


def nf_of_endpoint(ep):
    for nf, eps in NF_ENDPOINTS.items():
        if ep in eps:
            return nf
    return "UNKNOWN"


def gen_legit(agent, cfg, rows):
    """Generate a week of normal behaviour for one agent.

    SMF PDU-session endpoints follow a valid lifecycle: every update/release
    references a session that was previously created (no orphan operations) - so
    legitimate traffic never trips the sequence detector.
    """
    open_sessions = []
    counter = [0]

    def new_sid():
        counter[0] += 1
        return f"{agent}-s{counter[0]}"

    def session_for(ep):
        """Return (endpoint, session_id), normalising invalid ops to a create."""
        if ep == "Nsmf_PDUSession/create":
            sid = new_sid(); open_sessions.append(sid); return ep, sid
        if ep == "Nsmf_PDUSession/update":
            if open_sessions:
                return ep, random.choice(open_sessions)
            sid = new_sid(); open_sessions.append(sid)
            return "Nsmf_PDUSession/create", sid            # nothing open -> make it a create
        if ep == "Nsmf_PDUSession/release":
            if open_sessions:
                return ep, open_sessions.pop(random.randrange(len(open_sessions)))
            sid = new_sid(); open_sessions.append(sid)
            return "Nsmf_PDUSession/create", sid
        return ep, "-"

    for d in range(N_DAYS):
        for hour in range(24):
            lo, hi = cfg["active_hours"]
            active = lo <= hour < hi if lo < hi else (hour >= lo or hour < hi)
            if not active:
                if random.random() > 0.05:                 # rare off-hours trickle
                    continue
            rpm_lo, rpm_hi = cfg["rate_per_min"]
            n = int(np.random.uniform(rpm_lo, rpm_hi) * 60 * np.random.uniform(0.6, 1.0))
            prev = None
            for i in range(n):
                ep = pick_endpoint(cfg, prev); prev = ep
                ep, sid = session_for(ep)
                nf = nf_of_endpoint(ep)
                # monotonic timestamp within the hour so a session's create always
                # precedes its update/release chronologically (no false orphans)
                ts = BASE_DAY + timedelta(days=d, hours=hour,
                                          seconds=(i + random.random()) / max(n, 1) * 3600)
                is_err = random.random() < cfg["err_rate"]
                rows.append(dict(
                    ts=ts, agent_id=agent, nf=nf, endpoint=ep,
                    method=endpoint_method(ep), session_id=sid,
                    resp_size=int(np.random.uniform(*cfg["payload"])),
                    status=(random.choice([403, 404, 500]) if is_err else 200),
                    label="legit", attack_type="none",
                ))


# ------------------------------------------------------------------ attack injectors
def attack_window(day, hour):
    return BASE_DAY + timedelta(days=day, hours=hour, seconds=random.uniform(0, 3600))


def inject_impersonation(rows):  # T1: valid token of agent A, behaviour of another role
    victim = "nrf-heartbeat-svc"      # normally only NRF, low rate
    for _ in range(120):
        if random.random() < 0.45:
            # subtler slice: stays inside the victim's own NF (no scope violation
            # to key on) but bursts through endpoints/rate unlike its normal
            # register/heartbeat pattern - harder, relies on the behavioural/ML
            # layer rather than the deterministic scope rule.
            ep = random.choice(ENDPOINTS_OF["NRF"])
            rows.append(dict(ts=attack_window(2, 14), agent_id=victim, nf="NRF", endpoint=ep,
                             method=endpoint_method(ep), session_id="-",
                             resp_size=int(np.random.uniform(200, 1500)),
                             status=random.choice([200, 200, 404]),
                             label="attack", attack_type="T1_impersonation"))
        else:
            nf = random.choice(["SMF", "UDM", "AMF"])       # way outside its scope
            ep = random.choice(ENDPOINTS_OF[nf])
            rows.append(dict(ts=attack_window(2, 14), agent_id=victim, nf=nf, endpoint=ep,
                             method=endpoint_method(ep), session_id="-",
                             resp_size=int(np.random.uniform(200, 1500)),
                             status=random.choice([200, 200, 403]),
                             label="attack", attack_type="T1_impersonation"))


def inject_compromise(rows):  # T2: legit agent drifts to new endpoints + errors,
                               # but WITHIN its own onboarded NFs - a real compromised
                               # agent doesn't usually announce itself by touching NFs
                               # it was never allowed near; it drifts more quietly
                               # inside its own territory, which is the harder case.
    victim = "oss-inventory-job"       # scope: NRF, UDM
    for _ in range(90):
        nf = random.choice(["NRF", "UDM"])
        ep = random.choice(ENDPOINTS_OF[nf])
        rows.append(dict(ts=attack_window(3, 3), agent_id=victim, nf=nf, endpoint=ep,
                         method=endpoint_method(ep), session_id="-",
                         resp_size=int(np.random.uniform(150, 700)),   # normal-ish size - the
                         status=random.choice([200, 404, 404]),        # tell is endpoint drift + errors, not payload
                         label="attack", attack_type="T2_compromise"))


def inject_recon(rows):  # T3: enumeration WITHIN the attacker's own authorized
                          # scope (querying NFs it has no rights to at all would
                          # just be scope creep/T7, and gets rejected the same
                          # way); real reconnaissance is closer to fuzzing IDs and
                          # endpoints you already have some access to, which is
                          # inherently a weaker, harder-to-catch signal.
    attacker = "provisioning-agent"     # scope: NEF, UDM
    scope_nfs = ["NEF", "UDM"]
    for _ in range(160):
        nf = random.choice(scope_nfs)
        ep = random.choice(ENDPOINTS_OF[nf])
        rows.append(dict(ts=attack_window(1, 11), agent_id=attacker, nf=nf, endpoint=ep,
                         method="GET", session_id="-", resp_size=int(np.random.uniform(50, 200)),
                         status=random.choice([403, 404, 404, 200]),
                         label="attack", attack_type="T3_recon"))


def inject_volumetric(rows):  # T4: flood one NF (each a real new session)
    attacker = "closed-loop-assurance"
    ep = "Nsmf_PDUSession/create"
    for i in range(600):
        rows.append(dict(ts=attack_window(4, 10), agent_id=attacker, nf="SMF", endpoint=ep,
                         method="POST", session_id=f"atk-v-{i}",
                         resp_size=int(np.random.uniform(150, 400)),
                         status=random.choice([200, 200, 429]),
                         label="attack", attack_type="T4_volumetric"))


def inject_exfil(rows):  # T5: low-and-slow reads, off-hours, moderately large
                          # responses - through an endpoint already in the
                          # attacker's own scope (a careful exfil doesn't reach
                          # for a forbidden NF, it quietly over-uses one it's
                          # already trusted with), which is what makes this the
                          # hardest threat: no scope violation, no huge spike,
                          # just a size/timing outlier that a real off-hours
                          # legitimate pull can also occasionally resemble.
    attacker = "provisioning-agent"      # scope: NEF, UDM; active 06:00-22:00
    ep = "Nudm_SDM/get"                  # in scope
    for _ in range(70):
        rows.append(dict(ts=attack_window(3, 1), agent_id=attacker, nf="UDM",
                         endpoint=ep, method="GET", session_id="-",
                         resp_size=int(np.random.uniform(1800, 3200)),
                         status=200, label="attack", attack_type="T5_exfil"))


def inject_sequence(rows):  # T6: release/update of sessions that were never created (orphans)
    attacker = "orch-session-mgr"
    bad_seq = ["Nsmf_PDUSession/release", "Nsmf_PDUSession/update", "Nsmf_PDUSession/release"]
    for k in range(50):
        for ep in bad_seq:
            rows.append(dict(ts=attack_window(2, 16), agent_id=attacker, nf="SMF", endpoint=ep,
                             method=endpoint_method(ep), session_id=f"orphan-{k}",
                             resp_size=int(np.random.uniform(150, 500)),
                             status=random.choice([200, 400]),
                             label="attack", attack_type="T6_sequence"))


def inject_scope_creep(rows):  # T7: touch an NF never in baseline scope
    attacker = "nrf-heartbeat-svc"
    for _ in range(60):
        rows.append(dict(ts=attack_window(4, 20), agent_id=attacker, nf="UDM",
                         endpoint="Nudm_UEAuthentication/get", method="GET", session_id="-",
                         resp_size=int(np.random.uniform(200, 800)),
                         status=200, label="attack", attack_type="T7_scope_creep"))


# ------------------------------------------------------------------ build
def main():
    rows = []
    for agent, cfg in AGENTS.items():
        gen_legit(agent, cfg, rows)

    for inj in (inject_impersonation, inject_compromise, inject_recon,
                inject_volumetric, inject_exfil, inject_sequence, inject_scope_creep):
        inj(rows)

    df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    out = os.path.join(DATA_DIR, "aegis_traffic.csv")
    df.to_csv(out, index=False)

    n = len(df)
    n_atk = int((df.label == "attack").sum())
    print(f"Wrote {out}")
    print(f"  requests: {n:,}   legit: {n - n_atk:,}   attack: {n_atk:,} "
          f"({100 * n_atk / n:.1f}%)")
    print("  agents:", ", ".join(AGENTS))
    print("  attack types:")
    for t, c in df[df.label == 'attack'].attack_type.value_counts().items():
        print(f"    {t:22s} {c:5d}")


if __name__ == "__main__":
    main()
