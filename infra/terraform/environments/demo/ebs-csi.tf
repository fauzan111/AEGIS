# EKS Pod Identity role for the aws-ebs-csi-driver addon (wired into
# eks.tf's addons block). Needed so the Open5GS chart's bundled
# MongoDB (Phase 2) can actually get its PersistentVolumeClaim bound,
# without this the Mongo pod sits Pending forever.
#
# This is deliberately NOT the same IRSA mechanism as iam.tf's two
# AEGIS workload roles. Pod Identity is the current module-recommended
# path for addon-level roles specifically (the eks module's own
# karpenter submodule made the same switch in v21); the HLD's "IRSA"
# label refers to the AEGIS application workloads in iam.tf, which
# stay on classic IRSA as named there.
#
# attach_aws_ebs_csi_policy builds this module's own tag-conditioned
# least-privilege policy document (CreateVolume/DeleteVolume scoped to
# ebs.csi.aws.com/cluster + CSIVolumeName tags), it does NOT attach
# the AWS-managed AmazonEBSCSIDriverPolicy ARN. Confirmed by reading
# the vendored module's aws_ebs_csi.tf rather than assuming from the
# variable's name; the result is at least as tight as the managed
# policy, since the few actions left on Resource = "*" (Attach/Detach/
# Describe*/CreateSnapshot) don't support resource-level scoping at all.
#
# EKS Pod Identity associations only function once the
# eks-pod-identity-agent DaemonSet addon is ACTIVE in the cluster.
# This is a standalone resource (not inside module.eks's own addons
# map in eks.tf) specifically so module.ebs_csi_pod_identity below can
# depend_on it directly without creating a cycle: eks.tf's
# aws-ebs-csi-driver addon entry already needs this module's
# iam_role_arn output, so this module can't also depend on anything
# read back through module.eks's merged cluster_addons output (that
# shape is a real cycle, confirmed by `terraform validate`).
#
# depends_on module.eks.eks_managed_node_groups specifically, not
# module.eks as a whole: depending on the whole module pulls in every
# output, including cluster_addons, which is exactly the cycle above.
# eks_managed_node_groups mirrors how the module's own non-before_compute
# addons (coredns, kube-proxy) wait on node group creation before
# applying, which this addon should too since it's a regular DaemonSet
# like those, not a before_compute one like vpc-cni.
resource "aws_eks_addon" "pod_identity_agent" {
  cluster_name  = module.eks.cluster_name
  addon_name    = "eks-pod-identity-agent"
  addon_version = data.aws_eks_addon_version.pod_identity_agent.version

  depends_on = [module.eks.eks_managed_node_groups]
}

data "aws_eks_addon_version" "pod_identity_agent" {
  addon_name         = "eks-pod-identity-agent"
  kubernetes_version = var.kubernetes_version
  most_recent        = true
}

module "ebs_csi_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 2.9"

  name                      = "${var.cluster_name}-ebs-csi"
  attach_aws_ebs_csi_policy = true

  association_defaults = {
    namespace       = "kube-system"
    service_account = "ebs-csi-controller-sa"
  }
  associations = {
    main = { cluster_name = module.eks.cluster_name }
  }

  depends_on = [aws_eks_addon.pod_identity_agent]
}

# Default StorageClass for every PVC in the cluster — gp3 is cheaper
# and at least as fast as the older gp2 default. MongoDB's PVC (and
# anything else Phase 2/3 adds) picks this up automatically since it's
# marked default.
resource "kubernetes_storage_class_v1" "gp3_default" {
  metadata {
    name = "gp3"
    annotations = {
      "storageclass.kubernetes.io/is-default-class" = "true"
    }
  }

  storage_provisioner = "ebs.csi.aws.com"
  reclaim_policy      = "Delete" # matches the short-lived, torn-down-after-demo design
  volume_binding_mode = "WaitForFirstConsumer"

  parameters = {
    type = "gp3"
  }

  depends_on = [module.eks]
}
