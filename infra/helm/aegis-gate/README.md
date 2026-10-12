# AEGIS gate — Helm

Our own chart, not a third-party one (unlike open5gs/ueransim) — there's nothing to pull. A plain Deployment + ClusterIP Service + an IRSA-annotated ServiceAccount, wrapping `infra/docker/aegis-gate/Dockerfile`.

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
ROLE_ARN=$(terraform -chdir=infra/terraform/environments/demo output -raw aegis_gate_irsa_role_arn)
BUCKET=$(terraform -chdir=infra/terraform/environments/demo output -raw data_bucket_name)

helm install aegis-gate . \
  --namespace aegis \
  --set image.repository="$ECR_URL" \
  --set serviceAccount.roleArn="$ROLE_ARN" \
  --set env.s3Bucket="$BUCKET"
```

## Why the dashboard still works without S3 wired up yet

The image bakes in `data/aegis_traffic.csv` and runs `aegis_detect.py` at
*build* time (see the Dockerfile), so the dashboard's live-attack-injection
tab has a baseline to score against the moment the pod starts — it doesn't
block on S3 being readable. `env.s3Bucket` is plumbed through now so
Phase 3's move to reading/writing S3 directly is a code change in
`aegis_dashboard.py`/`aegis_detect.py`, not another round of infra work.

## Verify

```bash
kubectl -n aegis get pods -l app.kubernetes.io/name=aegis-gate
kubectl -n aegis port-forward svc/aegis-gate 8501:8501
# then open http://localhost:8501
```
