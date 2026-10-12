# AEGIS gate scorer: runs src/score_real_traffic_from_s3.py as a one-shot
# batch Job (infra/k8s/aegis-gate-scoring-cronjob.yaml), built from the repo
# root: docker build -f infra/docker/aegis-gate-scorer/Dockerfile .
#
# A separate image from infra/docker/aegis-gate/ (the public Streamlit
# dashboard) on purpose - see that Dockerfile's comment for why. This image
# has no exposed port, no web server, and no user-facing attack surface at
# all; it runs one script against one S3 bucket on a schedule and exits.
FROM python:3.11-slim

WORKDIR /app

COPY infra/docker/aegis-gate-scorer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/aegis_detect.py src/parse_real_sbi_capture.py src/score_real_traffic_from_s3.py src/

RUN useradd --create-home --uid 10001 scorer && chown -R scorer:scorer /app
USER scorer

ENTRYPOINT ["python", "src/score_real_traffic_from_s3.py"]
