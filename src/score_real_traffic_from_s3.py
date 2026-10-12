# -*- coding: utf-8 -*-
"""
AEGIS - scores real SBI traffic pulled from S3, per the AWS-MVP plan's
Phase 3 checklist: "AEGIS gate pod reads the CSV from S3, runs
OBSERVE -> FINGERPRINT -> SCORE -> DECIDE, writes scored windows back to S3."

Reuses the same validated functions as src/validate_real_traffic_detection.py
(build_windows / learn_baselines / rule_score from aegis_detect.py,
completely unmodified) - only the I/O layer and the schema adapter differ:

  - I/O: reads the newest object under s3://$S3_BUCKET/$S3_INPUT_PREFIX,
    writes the scored result to s3://$S3_BUCKET/$S3_OUTPUT_PREFIX, instead
    of taking a local file path argument.
  - Schema: adapts the OUTPUT schema of src/parse_real_sbi_capture.py
    (ts, caller_nf, callee_nf, method, path, status, resp_size) - what the
    infra/k8s/sbi-capture-job.yaml Job actually uploads - not the raw
    tshark-fields export validate_real_traffic_detection.py's own
    to_aegis_schema() expects (a different, earlier capture format).

Honest scope limitation, not hidden: this bootstraps each caller's baseline
FROM THE SAME capture it then scores (no persisted cross-run baseline store
exists yet - that's Phase 7 territory, once AgentCore agents are generating
sustained traffic over time to actually learn a prior from). By
construction, a window can't look anomalous relative to a baseline derived
from itself - this script proves the pipeline WIRING (S3 in -> detection ->
S3 out) works end-to-end, not detection accuracy on fresh data. Detection
accuracy was already established on a dedicated two-phase experiment in
validate_real_traffic_detection.py and the Gate 3 report; re-proving that
here would need either a persisted baseline or a deliberately-staged
two-phase capture, neither of which exists yet.

Deliberately rules-only, no ML layer: aegis_detect.ml_scores()'s own
docstring requires its calib split to be held out from the fit set ("never
the fit set - otherwise in-sample scores understate the tail and the
operating-point FPR blows up out of sample"). With only one capture and no
persisted baseline, there is no held-out population to calibrate against -
passing the same data for fit/calib/test would silently violate that
precondition rather than honestly bootstrap around it, so this script
doesn't call it at all.

Run:  python AEGIS/src/score_real_traffic_from_s3.py
Env:  S3_BUCKET (required), S3_INPUT_PREFIX (default "parsed/"),
      S3_OUTPUT_PREFIX (default "scored/") - AWS credentials come from the
      usual boto3 chain (IRSA's injected AWS_WEB_IDENTITY_TOKEN_FILE when
      running as the aegis-gate-sa ServiceAccount, same as the AWS CLI used
      elsewhere in this project).
"""
from __future__ import annotations
import io
import os
import sys

import boto3
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from aegis_detect import build_windows, learn_baselines, rule_score, MIN_N_ROLL, STEPUP, BLOCK  # noqa: E402

# No WINDOW override here (unlike validate_real_traffic_detection.py, which
# shrinks it to "5s" for its own deliberately-compressed sub-second
# injection experiment). This script's input spans one real
# CAPTURE_DURATION-second capture (default 60s, see
# infra/docker/sbi-capture/capture_and_upload.sh) - close enough to the
# production 60s tumbling window that the default is the right fit.
# Overriding it would also desync add_rolling_recon_features()'s hardcoded
# k=5 "trailing 5 minutes" (k * WINDOW) from what it actually measures.

EXPECTED_COLUMNS = {"ts", "caller_nf", "callee_nf", "method", "path", "status", "resp_size"}
UNKNOWN_NF = "UNKNOWN"  # parse_real_sbi_capture.py's own placeholder for an unresolved SBI path prefix


def adapt_schema(raw: pd.DataFrame) -> pd.DataFrame:
    """parse_real_sbi_capture.py's request/response CSV -> AEGIS's internal
    per-request schema that build_windows() expects.

    caller_nf is the natural per-caller identity key for this real-core
    traffic: a general Open5GS capture has no separate "AI agent" actor the
    way validate_real_traffic_detection.py's own dedicated injection script
    did - the Network Functions themselves are the callers here, so each
    distinct caller_nf is treated as one "agent" for fingerprinting
    purposes."""
    missing = EXPECTED_COLUMNS - set(raw.columns)
    if missing:
        raise ValueError(
            f"input is missing expected columns {missing} - is S3_INPUT_PREFIX "
            "really pointing at parse_real_sbi_capture.py output?")

    df = raw.copy()

    # A row with no caller_nf can't be fingerprinted to anyone - give it a
    # visible, distinct sentinel instead of letting it silently vanish via
    # build_windows()'s groupby(...).agg(...), which drops NaN group keys
    # by default with no warning.
    missing_caller = df["caller_nf"].isna().sum()
    if missing_caller:
        print(f"WARNING: {missing_caller} row(s) have no caller_nf - "
              "labelled 'UNKNOWN_CALLER' so they stay visible instead of silently dropping.")
    df["agent_id"] = df["caller_nf"].fillna("UNKNOWN_CALLER")

    # parse_real_sbi_capture.py emits "UNKNOWN" for any path it can't map to
    # a real NF (header-continuation frames, non-SBI traffic that still
    # matched the capture's "tcp port 7777 or sctp" filter) - a capture
    # artifact, not a real call. Scoring it as a real nf risks tripping the
    # scope_violation rule (score 0.95, near-automatic BLOCK) on a parsing
    # artifact rather than real agent behaviour, so these rows are dropped
    # before windowing rather than treated as signal.
    unknown_nf = (df["callee_nf"] == UNKNOWN_NF).sum()
    if unknown_nf:
        print(f"Dropping {unknown_nf} row(s) with callee_nf == '{UNKNOWN_NF}' "
              "(unresolved SBI path - a capture artifact, not a real NF call).")
        df = df[df["callee_nf"] != UNKNOWN_NF].copy()

    df["ts"] = pd.to_datetime(df["ts"], unit="s")
    df["nf"] = df["callee_nf"]
    df["endpoint"] = df["path"]

    # parse_real_sbi_capture.py leaves status/resp_size empty when a
    # request's response frame was never captured (truncated capture
    # window, dropped packet) - fillna(200)/(0) is the least-bad option
    # build_windows() leaves available (it needs both columns numeric, with
    # no "unmeasured" category), but silently calling an unmeasured
    # response "200 OK, 0 bytes" would hide real failures from the
    # error-rate and payload-size rules. Log how many rows this affects so
    # that trade-off is visible, not hidden.
    missing_status = df["status"].isna().sum()
    missing_size = df["resp_size"].isna().sum()
    if missing_status or missing_size:
        print(f"WARNING: {missing_status} row(s) missing status, {missing_size} row(s) missing "
              "resp_size (response never captured) - defaulting to 200/0, which UNDERSTATES "
              "error rate and payload size for those rows.")
    df["resp_size"] = pd.to_numeric(df["resp_size"], errors="coerce").fillna(0)
    df["status"] = pd.to_numeric(df["status"], errors="coerce").fillna(200)

    df["session_id"] = "-"   # not captured in this schema - orphan-session
    df["target_id"] = "-"    # detection (T6) and target-cardinality (T3/T5)
                              # rolling features both go inert, not wrong
    # Not knowable for live traffic by construction - build_windows() and
    # rule_score() both require a label/attack_type column to exist, but
    # "legit" here is the bootstrap assumption this module's docstring is
    # upfront about, not a ground-truth claim about this traffic.
    df["label"] = "legit"
    df["attack_type"] = "none"
    return df[["ts", "agent_id", "nf", "endpoint", "method", "session_id",
               "target_id", "resp_size", "status", "label", "attack_type"]]


def score(df: pd.DataFrame) -> pd.DataFrame | None:
    """Runs the unmodified OBSERVE -> FINGERPRINT -> SCORE -> DECIDE rules
    pipeline over one capture's windows (no ML layer - see module
    docstring). Returns None if the capture was too sparse to build even
    one window - a real, expected outcome for a short/quiet capture, not a
    bug, so callers should treat it the same as "nothing to score"."""
    feat = build_windows(df)
    if feat.empty:
        return None

    base = learn_baselines(feat)
    rule_results = feat.apply(lambda r: rule_score(r, base), axis=1, result_type="expand")
    feat[["rule", "rule_reason"]] = rule_results

    feat["ml"] = 0.0  # see module docstring for why this stays 0, not a TODO
    small = feat["n_roll"] < MIN_N_ROLL
    feat["risk"] = feat[["rule", "ml"]].max(axis=1)
    feat.loc[small, "risk"] = feat.loc[small, "rule"]
    feat["decision"] = pd.cut(feat["risk"], bins=[-1, STEPUP, BLOCK, 2],
                               labels=["PASS", "STEP-UP", "BLOCK"])
    return feat


def latest_s3_key(s3, bucket: str, prefix: str) -> str | None:
    """Newest object under prefix, paginated - a plain list_objects_v2 call
    silently truncates at 1000 keys and would start returning a stale
    "latest" once this bucket's parsed/ prefix (fed every 5 minutes by the
    scoring CronJob) grows past that, with no error or warning."""
    paginator = s3.get_paginator("list_objects_v2")
    newest = None
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if newest is None or obj["LastModified"] > newest["LastModified"]:
                newest = obj
    return newest["Key"] if newest else None


def main():
    bucket = os.environ["S3_BUCKET"]
    input_prefix = os.environ.get("S3_INPUT_PREFIX", "parsed/")
    output_prefix = os.environ.get("S3_OUTPUT_PREFIX", "scored/")

    s3 = boto3.client("s3")

    key = latest_s3_key(s3, bucket, input_prefix)
    if key is None:
        print(f"No objects under s3://{bucket}/{input_prefix} - nothing to score. Exiting 0.")
        return

    print(f"Downloading s3://{bucket}/{key}")
    obj = s3.get_object(Bucket=bucket, Key=key)
    raw = pd.read_csv(io.BytesIO(obj["Body"].read()))

    df = adapt_schema(raw)
    print(f"Loaded {len(df)} real SBI requests from {len(df['agent_id'].unique())} "
          f"caller(s): {sorted(df['agent_id'].unique())}")

    scored = score(df)
    if scored is None:
        print("Capture was too sparse to build even one window - nothing to score. Exiting 0. "
              "(A real, expected outcome for a short/quiet capture, not a failure.)")
        return

    out_cols = ["win", "agent_id", "n", "rule", "rule_reason", "ml", "risk", "decision"]
    out_buf = io.StringIO()
    scored[out_cols].to_csv(out_buf, index=False)

    out_key = f"{output_prefix}scored_{os.path.basename(key)}"
    s3.put_object(Bucket=bucket, Key=out_key, Body=out_buf.getvalue().encode("utf-8"))
    print(f"Wrote {len(scored)} scored windows to s3://{bucket}/{out_key}")

    counts = scored["decision"].value_counts()
    for d in ["PASS", "STEP-UP", "BLOCK"]:
        print(f"  {d:8s} {counts.get(d, 0)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # A capture-content problem (bad schema, too sparse) is already
        # handled above with a clean exit - anything that reaches here is
        # an unexpected failure (S3 throttling/network error, a malformed
        # upload pandas can't parse, ...). Fail loudly with context rather
        # than a bare traceback, so `kubectl logs` on a failed CronJob run
        # states what actually broke instead of just where.
        print(f"FATAL: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
