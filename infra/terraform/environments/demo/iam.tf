# IRSA roles for the two pods that need S3 access (HLD: "Least privilege:
# capture Job s3:PutObject, AEGIS gate s3:GetObject/PutObject"). The
# Bedrock AgentCore role is deliberately NOT here — AgentCore isn't an
# EKS workload, so it doesn't use IRSA the same way, and its exact
# trust-policy pattern is Phase 5 work once that's researched properly.
#
# These roles reference Kubernetes ServiceAccounts (sbi-capture-sa,
# aegis-gate-sa) that don't exist yet — Phase 2's Helm charts create
# them, with the eks.amazonaws.com/role-arn annotation pointing back
# at the role ARNs this file outputs. That's fine; the IAM trust
# relationship just names a namespace+ServiceAccount pair, it doesn't
# require the SA to exist first.

resource "aws_iam_policy" "sbi_capture_s3_put" {
  name        = "${var.cluster_name}-sbi-capture-s3-put"
  description = "Write-only access to the data bucket for the SBI capture/parse Job."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "PutOnly"
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.data.arn}/*"
      }
    ]
  })
}

module "sbi_capture_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.8"

  name = "${var.cluster_name}-sbi-capture"

  oidc_providers = {
    this = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["aegis:sbi-capture-sa"]
    }
  }

  policies = {
    s3_put = aws_iam_policy.sbi_capture_s3_put.arn
  }
}

resource "aws_iam_policy" "aegis_gate_s3_rw" {
  name        = "${var.cluster_name}-aegis-gate-s3-rw"
  description = "Read the captured CSV, write scored windows back — the AEGIS gate pod's actual job."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadWrite"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.data.arn}/*"
      },
      {
        Sid      = "ListBucket"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.data.arn
      }
    ]
  })
}

module "aegis_gate_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.8"

  name = "${var.cluster_name}-aegis-gate"

  oidc_providers = {
    this = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["aegis:aegis-gate-sa"]
    }
  }

  policies = {
    s3_rw = aws_iam_policy.aegis_gate_s3_rw.arn
  }
}
