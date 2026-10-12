# SBI capture & parse: automates the manual runbook in
# docs/GATE-3/real-traffic-capture.md (tcpdump on the SBI port, then
# AEGIS/src/parse_real_sbi_capture.py) as a one-shot Kubernetes Job, per
# the AWS-MVP plan's Phase 2 checklist item.
#
# tshark is required (not just tcpdump) since parse_real_sbi_capture.py
# shells out to it to reassemble HTTP/2 request/response pairs - same
# requirement noted in that script's own docstring.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        tcpdump tshark curl unzip \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI v2, for the final `aws s3 cp` - picks up IRSA credentials from
# the injected AWS_WEB_IDENTITY_TOKEN_FILE automatically, no extra
# config needed beyond the ServiceAccount annotation.
RUN curl -sS "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip \
    && unzip -q awscliv2.zip && ./aws/install && rm -rf awscliv2.zip aws

WORKDIR /app
COPY src/parse_real_sbi_capture.py src/
COPY infra/docker/sbi-capture/capture_and_upload.sh .
RUN chmod +x capture_and_upload.sh

ENTRYPOINT ["./capture_and_upload.sh"]
