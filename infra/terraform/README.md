# AEGIS MVP — Terraform

Phase 0 + Phase 1 of the AWS architecture in `slides/aegis-mvp-aws-architecture.drawio`. See `docs/AWS-MVP/implementation-plan.md` for the full 7-phase plan this fits into.

## Layout

```
infra/terraform/
  bootstrap/              one-time setup: creates the S3 bucket everything else stores state in
  environments/demo/      the actual MVP infra: VPC, EKS, ECR, S3 data bucket, IRSA roles, K8s namespaces
infra/helm/                Helm charts for Open5GS, UERANSIM, the AEGIS gate (Phase 2)
infra/k8s/                 raw K8s manifests, e.g. the SBI capture Job (Phase 2/3)
```

`environments/demo/` file-by-file: `vpc.tf`, `eks.tf`, `k8s-provider.tf` (kubernetes provider, authenticates via `aws eks get-token`), `namespaces.tf` (the three namespaces: `ueransim`, `open5gs`, `aegis`), `ecr.tf`, `s3.tf`, `iam.tf` (the two IRSA roles), plus `main.tf`/`variables.tf`/`outputs.tf`/`versions.tf`.

Two separate Terraform configs, not one, because of a chicken-and-egg problem: the `environments/demo` config wants to store its state in S3, but that S3 bucket has to be created by *something* first. `bootstrap/` solves that — it's a tiny config that creates just the state bucket, stays on local state forever, and you run it exactly once per AWS account.

## Tool versions (pinned, as of Oct 2026)

| Tool | Version | Why this one |
|---|---|---|
| Terraform CLI | 1.16.4 (installed) / `>= 1.16.0, < 2.0.0` (required in code) | 1.15.x hit end-of-life; 1.16 is current stable. 1.17 is still in beta, not GA — not used. |
| `hashicorp/aws` provider | `~> 6.67` | Latest stable; v6 line has per-resource region support, no breaking changes relevant to a greenfield project. |
| `terraform-aws-modules/eks/aws` | `~> 21.0` (resolved 21.26.0) | Current major version of the standard community EKS module. v21's API renamed `cluster_name` → `name`, `cluster_version` → `kubernetes_version`, and dropped the old `aws-auth` ConfigMap in favor of access entries (`authentication_mode = "API"`) — don't copy older v19/v20 tutorials. |
| `terraform-aws-modules/vpc/aws` | `~> 6.7` (resolved 6.7.3) | Current major version of the standard community VPC module. Requires `aws` provider `>= 6.28` — don't mix with an old `~> 5.0` provider pin from older tutorials. |
| `terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts` | `~> 6.8` (resolved 6.8.2) | IRSA role module. Note the submodule was renamed — older tutorials call it `iam-role-for-service-accounts-eks`, which 404s on the current module source. Its plain output is just `arn` (not `irsa_arn`; that name belongs to the separate `wrappers/` variant). |
| `hashicorp/kubernetes` provider | `~> 3.3` (resolved 3.3.0) | Needed once `environments/demo` creates K8s namespaces directly. v3 deprecated `kubernetes_namespace` in favor of `kubernetes_namespace_v1` — used the latter from the start. |
| kubectl | 1.36.1 (already installed) | Fine against any EKS cluster at 1.35, 1.36, or 1.37 (Kubernetes skew policy is ±1 minor version). Don't pick an older/extended-support EKS version (1.30-1.32) without upgrading kubectl, or without downgrading it. |
| Helm | 4.3.0 | Helm 3 is maintenance-only; 4 is current. |
| AWS CLI | 2.37.9 | Latest v2 line. |
| eksctl | 0.230.0 | Only used for occasional one-off cluster inspection/debugging — Terraform (via the EKS module) is what actually provisions the cluster, not eksctl. |

All four CLI tools were installed via `winget` on this machine. If you're setting up a second machine: `winget install Hashicorp.Terraform`, `winget install Helm.Helm`, `winget install Amazon.AWSCLI`, `winget install eksctl.eksctl`.

## State backend: S3 native locking, no DynamoDB

Terraform 1.11+ supports locking state directly in S3 (via conditional writes), which removes the old requirement for a separate DynamoDB lock table. We're using that (`use_lockfile = true` in `environments/demo/versions.tf`), not DynamoDB.

**Why this is the right call here:** fewer moving parts (no extra AWS resource, no extra IAM permissions, nothing else to tear down), and this is a small team on a short-lived demo environment, not an enterprise multi-team setup where DynamoDB's independent inspectability would matter more.

**The one thing this requires:** every person and every CI runner applying this config must run Terraform **1.11 or newer** (we're pinning 1.16). An older Terraform binary doesn't know about the lock file and will write to state without respecting it — the protection only works if everyone's tooling honors it. If someone on the team is on an old Terraform install, upgrade it before they run `apply`, don't skip this.

## Running it

**One-time, per AWS account:**

```bash
cd infra/terraform/bootstrap
terraform init
terraform apply -var="state_bucket_name=<pick-a-globally-unique-name>"
# copy the `state_bucket_name` output into environments/demo/versions.tf's backend block
```

**Every other apply, against the demo environment:**

```bash
cd infra/terraform/environments/demo
terraform init    # will fail until the backend bucket line above is filled in and the bucket exists
terraform plan -var='eks_public_access_cidrs=["<your-actual-ip>/32"]'
terraform apply   -var='eks_public_access_cidrs=["<your-actual-ip>/32"]'
aws eks update-kubeconfig --name aegis-mvp --region eu-west-1   # the module doesn't write a kubeconfig for you
```

**Don't skip the `eks_public_access_cidrs` override.** The checked-in default is a deliberately invalid placeholder — it'll fail loudly at `apply` rather than silently leaving the EKS API server open to the whole internet, which is what you'd get by defaulting to `0.0.0.0/0`.

**Tearing down** (this whole environment is designed to be destroyed after each demo):

```bash
cd infra/terraform/environments/demo
terraform destroy
```

Don't run `terraform destroy` in `bootstrap/` casually — that deletes the state bucket for every other environment. It has `prevent_destroy = true` set specifically so that doesn't happen by accident.

## What's NOT here yet

Phase 1 covers the VPC, EKS cluster, ECR repos, S3 data bucket, and two IRSA roles (capture Job, AEGIS gate). **Not** in Phase 1, deliberately deferred:

- The Bedrock AgentCore IAM role from the HLD — AgentCore isn't an EKS workload, so it doesn't use IRSA the same way, and its exact trust-policy pattern needs its own research when Phase 5 starts.
- The actual Open5GS/UERANSIM/AEGIS-gate Helm charts and container images (Phase 2) — the namespaces and ECR repos exist, nothing's deployed into them yet.
- CloudFront, WAF, the internal ALB/NLB (Phase 4).

Both Terraform configs pass `terraform validate` and were reviewed by the `iac-reviewer` agent before being considered done. Phase 1's review caught and fixed: the EKS module's own default (`endpoint_public_access = false`) would have broken `apply` itself (the namespace resources and kubectl both need to reach the API server from outside the VPC), and the S3 bucket / ECR repos needed `force_destroy`/`force_delete` or `terraform destroy` would fail with `BucketNotEmpty`/`RepositoryNotEmptyException` on every teardown.

**Also still open, waiting on the AWS tutor:** which AWS account to actually target, and whether Bedrock AgentCore (Phase 5) is available in `eu-west-1` or needs a different region. Neither blocks writing Terraform — only the real `terraform apply` against a live account waits on that.
