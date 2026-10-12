#!/bin/sh
# Automates docs/GATE-3/real-traffic-capture.md's manual steps 4-5:
# tcpdump the SBI port for a fixed window, parse into AEGIS's CSV
# schema, upload both to S3. Requires hostNetwork: true on the pod and
# scheduling onto the same node as the open5gs-scp pod (see
# infra/k8s/sbi-capture-job.yaml) - tcpdump here only sees traffic that
# actually crosses this node.
#
# Honest gap, not yet automated: the manual runbook restarts the UE pod
# partway through the capture window to guarantee a fresh registration
# is actually in the capture. This script does not do that - it just
# captures whatever SBI traffic happens to cross this node during
# CAPTURE_DURATION. If nothing is actively registering, the capture can
# come back empty. Triggering a UE restart from here would mean this
# Job's ServiceAccount also needs RBAC to patch pods in the ueransim
# namespace, which is out of scope for the read-only/write-only IRSA
# split this Job was deliberately given - flagged for Phase 3, not
# silently assumed away.
set -eu

: "${S3_BUCKET:?S3_BUCKET env var is required}"
CAPTURE_DURATION="${CAPTURE_DURATION:-60}"
CAPTURE_IFACE="${CAPTURE_IFACE:-any}"
CAPTURE_FILTER="${CAPTURE_FILTER:-tcp port 7777 or sctp}"

TS=$(date -u +%Y%m%dT%H%M%SZ)
PCAP=/tmp/sbi_capture_${TS}.pcap
CSV=/tmp/real_sbi_capture_${TS}.csv

echo "Capturing '${CAPTURE_FILTER}' on ${CAPTURE_IFACE} for ${CAPTURE_DURATION}s -> ${PCAP}"
set +e
timeout "${CAPTURE_DURATION}" tcpdump -i "${CAPTURE_IFACE}" -w "${PCAP}" ${CAPTURE_FILTER}
TCPDUMP_RC=$?
set -e

# 124 = timeout fired and killed tcpdump - the expected outcome, since
# we deliberately give it no packet-count limit and want it to run the
# full window. 0 = tcpdump stopped on its own before the deadline,
# harmless. Anything else (bad interface, permission denied because a
# capability wasn't actually granted, OOM-killed, ...) is a real failure
# that must NOT be allowed to look identical to "no SBI traffic this
# window" - that was the bug in the previous `|| true` version: it
# swallowed every failure mode and reported success either way.
case "$TCPDUMP_RC" in
    0|124) ;;
    *)
        echo "tcpdump exited with unexpected status $TCPDUMP_RC - treating as a real failure, not an empty capture." >&2
        exit 1
        ;;
esac

if [ ! -s "${PCAP}" ]; then
    echo "No packets captured (empty pcap) - nothing to parse or upload. Exiting 0 (not a Job failure; absence of SBI traffic during this window is a real, expected outcome, not a bug)."
    exit 0
fi

echo "Parsing ${PCAP} -> ${CSV}"
python src/parse_real_sbi_capture.py "${PCAP}" "${CSV}"

echo "Uploading to s3://${S3_BUCKET}/raw/$(basename "${PCAP}")"
aws s3 cp "${PCAP}" "s3://${S3_BUCKET}/raw/$(basename "${PCAP}")"

echo "Uploading to s3://${S3_BUCKET}/parsed/$(basename "${CSV}")"
aws s3 cp "${CSV}" "s3://${S3_BUCKET}/parsed/$(basename "${CSV}")"

echo "Done."
