variable "aws_region" {
  description = "AWS region for the demo environment. Must match the region in this file's own `backend \"s3\"` block in versions.tf — that block can't reference this variable (Terraform evaluates backend config before any variables exist), so if you change this, change the backend block's `region` too. Also must match infra/terraform/bootstrap's aws_region, since that's where the state bucket actually lives."
  type        = string
  default     = "eu-west-1"
}

variable "az" {
  description = "Single availability zone for this demo environment. Everything here is deliberately single-AZ (no HA) to keep cost and complexity down for a short-lived demo."
  type        = string
  default     = "eu-west-1a"
}

variable "cluster_name" {
  description = "EKS cluster name, matches the tutor's HLD (slides/aegis-mvp-aws-architecture.drawio)."
  type        = string
  default     = "aegis-mvp"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. Kept in standard support (not extended) and within +/-1 minor version of the kubectl client version pinned in infra/terraform/README.md — see that file before changing this."
  type        = string
  default     = "1.36"
}

variable "node_instance_type" {
  description = "Managed node group instance type, matches the tutor's HLD."
  type        = string
  default     = "m5.xlarge"
}

variable "node_count" {
  description = "Fixed node count, matches the tutor's HLD (2 nodes, on-demand, no autoscaling beyond this)."
  type        = number
  default     = 2
}

variable "ecr_repository_names" {
  description = "One ECR repo per pinned image the cluster pulls, per the HLD's namespaces: open5gs, ueransim, the AEGIS gate, and the SBI capture/parse job."
  type        = list(string)
  default     = ["aegis-mvp/open5gs", "aegis-mvp/ueransim", "aegis-mvp/aegis-gate", "aegis-mvp/sbi-capture"]
}

variable "data_bucket_name" {
  description = "S3 bucket for pcap/CSV/scored-windows (the HLD's 'Amazon S3 pcap / CSV / scores'). Globally unique, so the default below will likely collide — override it."
  type        = string
  default     = "aegis-mvp-data"
}

variable "eks_public_access_cidrs" {
  description = "CIDRs allowed to reach the EKS API server's public endpoint (kubectl from a demo operator's laptop). TODO: replace the default with the actual office/home IP(s) before `apply` — 0.0.0.0/0 here would leave the control plane open to the whole internet, which is not acceptable even for a throwaway demo. This is exactly the kind of thing Phase 6's guardrail re-check should re-verify got a real value."
  type        = list(string)
  default     = ["REPLACE-WITH-YOUR-ACTUAL-IP/32"]
}
