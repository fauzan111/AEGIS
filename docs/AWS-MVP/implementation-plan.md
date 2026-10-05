# AEGIS MVP on AWS — Implementation Plan

Working checklist for the architecture in `slides/aegis-mvp-aws-architecture.drawio`, proposed by the AWS tutor. Seven phases, roughly in dependency order — each one mostly needs the one before it done. Work through them one at a time; check items off as they land.

Four open questions are already out to the tutor (account/billing ownership, Bedrock AgentCore region availability in `eu-west-1`, Gate 3 vs. Gate 4 timeline, Terraform apply access). **None of them block starting.** The real split is **author now, apply once confirmed** — every phase below separates "write/prepare" (no AWS access needed, start immediately) from "deploy" (needs real credentials and the region answer). Only the deploy steps wait.

## Phase 0 — Groundwork (fully unblocked) ✅ done 2026-10-05

- [x] Install and pin tool versions: Terraform 1.16.4, `hashicorp/aws` provider `~> 6.67`, kubectl 1.36.1 (already present, confirmed compatible), Helm 4.3.0, AWS CLI 2.37.9, eksctl 0.230.0 — all via `winget`, see `infra/terraform/README.md` for the full table and rationale
- [x] Decided the state backend: **S3 with native locking (`use_lockfile = true`), no DynamoDB table.** Current (2026) recommended approach for Terraform ≥1.11 — fewer moving parts, right-sized for a 2-3 person team on a short-lived env. Full reasoning in `infra/terraform/README.md`. One hard requirement: everyone applying must be on Terraform ≥1.11 (we're pinning 1.16) or the lock doesn't protect anything.
- [x] Set up `infra/` directory: `infra/terraform/bootstrap` (creates the state bucket, stays on local state — solves the chicken-and-egg problem of needing a bucket before you have a bucket), `infra/terraform/environments/demo` (the actual MVP infra, empty until Phase 1), `infra/helm/`, `infra/k8s/`. Both Terraform configs pass `terraform validate`.
- [x] Noted for Phase 1: `terraform-aws-modules/eks/aws` v21 is the current standard EKS module — its API renamed `cluster_name`→`name`, dropped the old `aws-auth` ConfigMap for access-entry auth. Don't follow older v19/v20 tutorials when writing Phase 1.
- [ ] *(Deploy-time only, waits on his answer)* Confirm AWS account access: who has console/CLI credentials, personal account, team account, or AWS Educate/sponsored credits — needed before `bootstrap`'s `terraform apply` can actually run

## Phase 1 — AWS foundation (Terraform) ✅ written + reviewed 2026-10-06

**Written and validated** (`infra/terraform/environments/demo/`, passes `terraform validate`, reviewed by the `iac-reviewer` agent — one blocker and two high findings caught and fixed, see `infra/terraform/README.md`):

- [x] VPC `10.0.0.0/16`, single AZ, public + private subnets (`vpc.tf`, `terraform-aws-modules/vpc/aws` v6.7.3)
- [x] Internet Gateway (public subnet) + NAT Gateway (egress-only from private subnet) — the module defaults handle both
- [x] EKS cluster `aegis-mvp` + managed node group (2× `m5.xlarge`, on-demand) (`eks.tf`, `terraform-aws-modules/eks/aws` v21.26.0)
- [x] ECR repositories for pinned images (Open5GS, UERANSIM, AEGIS gate, capture job) (`ecr.tf`)
- [x] S3 bucket for pcap/CSV/scored-windows, 7-day lifecycle expiry (`s3.tf`)
- [x] IAM roles: IRSA for the capture Job (`s3:PutObject` only) and the AEGIS gate pod (`s3:GetObject`/`PutObject`/`ListBucket`) (`iam.tf`)
- [x] Kubernetes namespaces: `ueransim`, `open5gs`, `aegis` (`namespaces.tf`)
- [ ] *Deferred to Phase 5, not forgotten:* the separate AgentCore role (`bedrock:InvokeModel` scoped to one model ARN) — AgentCore isn't an EKS workload so it doesn't use IRSA the same way; its trust-policy pattern needs its own research when Phase 5 starts

**Deploy-time only:** `terraform apply` against the real account — waits on account access, and on setting `eks_public_access_cidrs` to a real IP (checked-in default is a deliberately invalid placeholder, not `0.0.0.0/0`).

## Phase 2 — Lift-and-shift the existing stack into Helm charts

Mostly translation work — you already have this running in Docker Compose (`docs/GATE-3/real-traffic-capture.md`).

- [ ] Open5GS Helm chart: NRF, SCP, AUSF, UDR, UDM, SMF, UPF, AMF, PCF, BSF, NSSF, WebUI, MongoDB (on EBS volume) — check for an existing community chart before writing one from scratch
- [ ] UERANSIM Helm chart: UE + gNB
- [ ] Dockerfile + Helm chart for the AEGIS gate (wraps `src/aegis_detect.py` + the Streamlit dashboard)
- [ ] Kubernetes Job manifest for the SBI capture & parse step — pinned to the SCP node, host network, runs `tcpdump` on `:7777` and feeds `src/parse_real_sbi_capture.py` (same logic as the manual runbook, now automated)
- [ ] Synthetic subscriber K/OP values in a namespaced Kubernetes Secret — never real SIM data (matches the existing privacy-safe pattern already documented in `docs/GATE-3/real-vs-synthetic-dashboard-implications.md`)

## Phase 3 — Data pipeline wiring

- [ ] Capture Job uploads raw pcap + parsed CSV to S3
- [ ] AEGIS gate pod reads the CSV from S3, runs OBSERVE → FINGERPRINT → SCORE → DECIDE (unmodified pipeline — same code path already validated in `src/validate_real_traffic_detection.py`)
- [ ] AEGIS gate writes scored windows back to S3
- [ ] End-to-end smoke test: trigger one registration, confirm a row appears scored in S3 within a reasonable time

## Phase 4 — Public access layer

- [ ] Internal ALB in front of the dashboard (VPC origin, WebSocket support, no caching)
- [ ] Internal NLB exposing the SCP's `:7777` — reachable only from the AgentCore security group
- [ ] CloudFront distribution (VPC origin) in front of the ALB
- [ ] AWS WAF with an IP allowlist attached to CloudFront — this is the only public entry point; everything else (ALB, NLB, all NF services) stays internal/ClusterIP
- [ ] Verify: can you reach the dashboard over HTTPS from an allowlisted IP, and confirm it's actually blocked from outside the allowlist

## Phase 5 — Bedrock AgentCore agents (the new, hardest part — likely needs tutor help)

**Write and test now**, against whatever region Bedrock is actually available in today (us-east-1 is the safe default) — the application code doesn't care which region it talks to until the final deploy, and repointing it later is a one-line config change:

- [ ] Build the "legit" agent: reasons with a Bedrock LLM, calls SBI APIs via the internal NLB with a valid AgentCore Identity token, Phase 1 baseline behaviour (steady, in-scope calls)
- [ ] Build the "rogue" agent: same plumbing, but driven by a malicious goal or an injected prompt — Phase 2 behaviour, the thing AEGIS is supposed to catch
- [ ] Write the AgentCore Identity/VPC-mode Terraform (ENIs in the private subnet) alongside Phase 1's infra
- [ ] Write the AgentCore IAM role scoped to exactly one model ARN for `bedrock:InvokeModel` (no broader Bedrock access)
- [ ] Test both agents against a mocked or locally-run SCP endpoint if the real EKS cluster isn't up yet

**Deploy-time only:** confirm `eu-west-1` availability and redeploy there if needed; stand up the real AgentCore Runtime in VPC mode against the live cluster; validate both phases produce distinguishable traffic in the AEGIS gate's live scoring (legit → PASS, rogue → STEP-UP/BLOCK).

## Phase 6 — Security and cost guardrails (verify, don't just build)

- [ ] Re-check: is there any path to the cluster other than CloudFront+WAF? (There shouldn't be.)
- [ ] Re-check: are all NF services ClusterIP-only, with no accidental LoadBalancer/NodePort exposure?
- [ ] Re-check: does the NLB really accept connections only from the AgentCore security group?
- [ ] Re-check: least-privilege IAM — no role has more than the single permission it actually needs
- [ ] Confirm single-AZ, on-demand-only, no autoscaling beyond the fixed 2-node group (keeps cost bounded and predictable)
- [ ] Run `terraform destroy` once as a dry run before the real demo, to confirm the whole thing actually tears down cleanly with nothing orphaned (EBS volumes, ENIs, S3 objects)

## Phase 7 — End-to-end validation and demo rehearsal

- [ ] Walk the full 10-step flow from the diagram, live, start to finish: Terraform apply → Helm install → UE registers → SBI calls flow through SCP → AgentCore agents act (legit then rogue) → capture Job tails it → AEGIS gate scores it → dashboard shows the PASS/STEP-UP/BLOCK result over CloudFront
- [ ] Time the full spin-up (Terraform + Helm + first scored result) so you know how long before a demo you need to start provisioning
- [ ] Rehearse the teardown too — `terraform destroy` as part of the actual rehearsal, not just a one-off test

## What's genuinely new vs. what's just relocated

Worth keeping straight as you work through this:

- **Relocated, not reinvented:** Open5GS core, UERANSIM, the AEGIS detection pipeline (`aegis_detect.py`), the SBI capture/parse logic. These already work locally — Phase 2 is packaging, not redesigning.
- **Genuinely new:** Bedrock AgentCore agents (legit + rogue), the AgentCore Identity/VPC-mode wiring, and the CloudFront+WAF public-access layer. Budget the most time and the most tutor check-ins here.
