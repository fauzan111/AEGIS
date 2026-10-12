# AEGIS gate — Helm

Our own chart, not a third-party one (unlike open5gs/ueransim) — there's nothing to pull. A plain Deployment + ClusterIP Service + a ServiceAccount with no AWS credentials, wrapping `infra/docker/aegis-gate/Dockerfile` (the public-facing Streamlit dashboard).

This pod does not touch S3 and gets no IRSA annotation on purpose — see `values.yaml`'s `serviceAccount` comment. The real-traffic S3 scoring path lives in a separate image and chart-free manifest: `infra/docker/aegis-gate-scorer/` + `infra/k8s/aegis-gate-scoring-cronjob.yaml`.

## Build and push the image first

```bash
cd AEGIS   # repo root, so the Dockerfile's COPY paths resolve
ECR_URL=$(terraform -chdir=infra/terraform/environments/demo output -json ecr_repository_urls | jq -r '."aegis-mvp/aegis-gate"')
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin "${ECR_URL%/*}"

docker build -f infra/docker/aegis-gate/Dockerfile -t "$ECR_URL:v1" .
docker push "$ECR_URL:v1"
```

## Install

```bash
helm install aegis-gate . \
  --namespace aegis \
  --set image.repository="$ECR_URL"
```

## Why the dashboard works without any AWS access

The image bakes in `data/aegis_traffic.csv` and runs `aegis_detect.py` at
*build* time (see the Dockerfile), so the dashboard's live-attack-injection
tab has a baseline to score against the moment the pod starts — it never
needed S3 to begin with. If a future phase adds a dashboard tab that reads
real scored windows from S3 directly, that's the point to revisit this
chart's ServiceAccount and add a properly-scoped IRSA grant for it —
deliberately not pre-provisioned now for a feature that doesn't exist yet.

## Verify

```bash
kubectl -n aegis get pods -l app.kubernetes.io/name=aegis-gate
kubectl -n aegis port-forward svc/aegis-gate 8501:8501
# then open http://localhost:8501
```
