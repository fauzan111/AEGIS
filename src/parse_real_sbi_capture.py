# -*- coding: utf-8 -*-
"""
AEGIS - parses a real Open5GS SBI packet capture (tcpdump/tshark) into a
labelled request-log CSV in the same spirit as the synthetic generator's
output, for Gate 3's "real M2M/API-gateway traffic" validation step.

This is NOT meant to replace the synthetic pipeline - it's the honest,
"does AEGIS's schema and NF-naming convention survive contact with a real
5G core" check, per the plan on Gate 2 slide 17 (Open5GS + tcpdump/tshark).

How the capture was produced (see docs/GATE-3/real-traffic-capture.md for
the full runbook): a real Open5GS 5G SA core (herlesupreeth/docker_open5gs)
plus a UERANSIM UE were brought up in Docker, a subscriber was registered
through the core's own webui API, and tcpdump captured tcp port 7777
(the SBI HTTP/2 port every NF listens on) on the AMF container's network
namespace during a live UE registration + PDU session establishment.

Requires tshark on PATH (part of Wireshark), or a netshoot-style Docker
image if not installed locally.

Run:  python AEGIS/src/parse_real_sbi_capture.py <path-to-pcap> [out.csv]
"""

from __future__ import annotations
import csv
import os
import subprocess
import sys
import urllib.parse
from collections import defaultdict

# IP -> NF name, from open5gs-testbed/.env - only the NFs actually deployed
# in the sa-deploy.yaml core used for this capture.
IP_TO_NF = {
    "172.22.0.2": "MONGO", "172.22.0.7": "SMF", "172.22.0.8": "UPF",
    "172.22.0.10": "AMF", "172.22.0.11": "AUSF", "172.22.0.12": "NRF",
    "172.22.0.13": "UDM", "172.22.0.14": "UDR", "172.22.0.27": "PCF",
    "172.22.0.28": "NSSF", "172.22.0.29": "BSF", "172.22.0.35": "SCP",
}

# SBI path prefix (3GPP TS 29.xxx service name) -> owning NF. This is the
# real 3GPP naming convention AEGIS's synthetic generator already mirrors
# (Nnrf_NFManagement, Nudm_SDM, ...), confirmed here against genuine traffic.
PATH_PREFIX_TO_NF = {
    "nnrf-nfm": "NRF", "nnrf-disc": "NRF",
    "nudm-sdm": "UDM", "nudm-uecm": "UDM", "nudm-ueau": "UDM",
    "nausf-auth": "AUSF",
    "npcf-am-policy-control": "PCF", "npcf-smpolicycontrol": "PCF",
    "nsmf-pdusession": "SMF",
    "namf-comm": "AMF", "namf-evts": "AMF",
    "nbsf-management": "BSF",
    "nnssf-nsselection": "NSSF",
}


def nf_from_path(path: str) -> str:
    if not path:
        return "UNKNOWN"
    parts = path.strip("/").split("/")
    return PATH_PREFIX_TO_NF.get(parts[0].lower(), parts[0].upper() if parts[0] else "UNKNOWN")


TSHARK_FIELDS = ["frame.time_epoch", "ip.src", "ip.dst", "tcp.stream",
                 "http2.headers.method", "http2.headers.path", "http2.headers.status",
                 "http2.headers.content_length", "http2.streamid"]


def tshark_command(pcap_path: str) -> list[str]:
    """The exact tshark invocation this parser expects - print with --print-cmd
    if you need to run it yourself (e.g. inside a netshoot container) and pipe
    the output back in via stdin ('-' as the pcap argument)."""
    cmd = ["tshark", "-r", pcap_path, "-d", "tcp.port==7777,http2",
           "-Y", "http2.type==1", "-T", "fields", "-E", "separator=;",
           "-E", "occurrence=f"]
    for f in TSHARK_FIELDS:
        cmd += ["-e", f]
    return cmd


def run_tshark(pcap_path: str) -> list[dict]:
    if pcap_path == "-":
        out = sys.stdin.read()
    else:
        cmd = tshark_command(pcap_path)
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        except FileNotFoundError:
            print("tshark not found on PATH. Either install Wireshark, or run tshark "
                  "in a netshoot-style Docker container and pipe its output in:\n"
                  f"  docker run --rm -v <dir>:/captures nicolaka/netshoot "
                  f"{' '.join(tshark_command('/captures/your.pcap'))} | "
                  f"python {os.path.basename(__file__)} -", file=sys.stderr)
            sys.exit(1)

    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        cols = line.split(";")
        cols += [""] * (len(TSHARK_FIELDS) - len(cols))
        ts, src, dst, stream, method, path, status, clen, h2sid = cols[:9]
        rows.append(dict(ts=float(ts) if ts else 0.0, src=src, dst=dst,
                         stream=stream, method=method,
                         path=urllib.parse.unquote(path) if path else "",
                         status=status, content_length=clen, h2sid=h2sid))
    return rows


def pair_requests_responses(rows: list[dict]) -> list[dict]:
    """HTTP/2 multiplexes many exchanges over one TCP stream, distinguished by
    stream id - match each request frame to the response frame that shares
    (tcp.stream, http2.streamid) and carries a status code."""
    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["stream"], r["h2sid"])].append(r)

    requests = []
    for key, frames in by_key.items():
        frames.sort(key=lambda r: r["ts"])
        req = next((f for f in frames if f["method"]), None)
        resp = next((f for f in frames if f["status"]), None)
        if req is None:
            continue
        requests.append(dict(
            ts=req["ts"],
            caller_ip=req["src"], callee_ip=req["dst"],
            caller_nf=IP_TO_NF.get(req["src"], req["src"]),
            callee_nf=nf_from_path(req["path"]),
            method=req["method"], path=req["path"],
            status=int(resp["status"]) if resp and resp["status"] else None,
            resp_size=int(resp["content_length"]) if resp and resp["content_length"] else None,
        ))
    requests.sort(key=lambda r: r["ts"])
    return requests


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path-to-pcap> [out.csv]", file=sys.stderr)
        sys.exit(1)
    pcap_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "reports", "GATE-3",
        "real_sbi_capture.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    rows = run_tshark(pcap_path)
    requests = pair_requests_responses(rows)

    fieldnames = ["ts", "caller_nf", "callee_nf", "method", "path", "status", "resp_size"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in requests:
            w.writerow({k: r[k] for k in fieldnames})

    print(f"Parsed {len(requests)} real SBI request/response exchanges from {pcap_path}")
    print(f"Wrote {out_path}")
    print("\nCallee NF breakdown (which real service each call actually hit):")
    counts = defaultdict(int)
    for r in requests:
        counts[r["callee_nf"]] += 1
    for nf, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {nf:8s} {c}")


if __name__ == "__main__":
    main()
