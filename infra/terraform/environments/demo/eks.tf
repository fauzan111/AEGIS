# EKS cluster, matches the tutor's HLD: "Amazon EKS cluster aegis-mvp -
# managed node group - 2 x m5.xlarge (on-demand)". v21 module API —
# note this is NOT the older cluster_name/cluster_version shape used
# in pre-v21 tutorials; see infra/terraform/README.md.
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  # Access entries (not the legacy aws-auth ConfigMap) — the v21 default.
  authentication_mode                      = "API"
  enable_cluster_creator_admin_permissions = true

  # The module's own default is endpoint_private_access = true,
  # endpoint_public_access = false — API server reachable only from
  # inside the VPC. That breaks `terraform apply` itself (the
  # kubernetes_namespace_v1 resources and this file's own kubectl
  # instructions both need to reach the API server), since this is
  # meant to be run from a demo operator's own laptop, not a bastion
  # inside the VPC. Restrict to known IPs via
  # eks_public_access_cidrs, don't leave this wide open.
  endpoint_public_access       = true
  endpoint_public_access_cidrs = var.eks_public_access_cidrs

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  # IRSA (IAM Roles for Service Accounts) — used in iam.tf for the
  # capture Job and AEGIS gate pods' S3 access. The HLD's own label for
  # this is "IAM roles (IRSA + AgentCore)".
  enable_irsa = true

  eks_managed_node_groups = {
    default = {
      instance_types = [var.node_instance_type]
      capacity_type  = "ON_DEMAND"

      min_size     = var.node_count
      max_size     = var.node_count
      desired_size = var.node_count
    }
  }
}

# The module stopped generating a kubeconfig file in v21 — this is the
# documented replacement, run once after `apply`:
#   aws eks update-kubeconfig --name <cluster_name> --region <region>
