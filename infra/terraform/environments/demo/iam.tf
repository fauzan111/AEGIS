# IRSA roles for the two workloads that need S3 access (HLD: "Least
# privilege: capture Job s3:PutObject, AEGIS gate s3:GetObject/PutObject").
# The Bedrock AgentCore role is deliberately NOT here — AgentCore isn't an
# EKS workload, so it doesn't use IRSA the same way, and its exact
# trust-policy pattern is Phase 5 work once that's researched properly.
#
# These roles reference Kubernetes ServiceAccounts (sbi-capture-sa,
# aegis-gate-scorer-sa) that don't exist yet — infra/k8s/sbi-capture-job.yaml
# and infra/k8s/aegis-gate-scoring-cronjob.yaml create them, with the
# eks.amazonaws.com/role-arn annotation pointing back at the role ARNs this
# file outputs. That's fine; the IAM trust relationship just names a
# namespace+ServiceAccount pair, it doesn't require the SA to exist first.
#
# Reviewed finding, fixed here: the public-facing Streamlit dashboard
# (infra/helm/aegis-gate/, ServiceAccount aegis-gate-sa) does NOT get an S3
# grant at all, even though its name suggests "the AEGIS gate." It doesn't
# touch S3 (confirmed: no boto3/s3 usage in src/aegis_dashboard.py) - only
# the scorer CronJob (src/score_real_traffic_from_s3.py, a separate image,
# infra/docker/aegis-gate-scorer/) does, so only ITS ServiceAccount
# (aegis-gate-scorer-sa) gets this role. An earlier revision reused the
# dashboard's SA for both, which doesn't work: the IRSA annotation grants
# credentials via STS regardless of whether the pod's image has boto3
# installed, so reusing one SA across both would have left the
# public-facing pod holding standing S3 read/write credentials it has no
# code path to use on purpose - an unnecessary blast-radius expansion if
# that pod is ever compromised, not a hypothetical one.

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

resource "aws_iam_policy" "aegis_gate_scorer_s3" {
  name        = "${var.cluster_name}-aegis-gate-scorer-s3"
  description = "Read parsed/*, write scored/* — exactly the two prefixes src/score_real_traffic_from_s3.py touches (S3_INPUT_PREFIX/S3_OUTPUT_PREFIX), not the whole bucket."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadParsed"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.data.arn}/parsed/*"
      },
      {
        Sid      = "WriteScored"
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.data.arn}/scored/*"
      },
      {
        # list_objects_v2's Prefix filter (how latest_s3_key() finds the
        # newest parsed/ object) needs bucket-level ListBucket - there's no
        # object-level equivalent - scoped down with a condition so it can
        # only enumerate under parsed/, matching the Get/Put scoping above.
        Sid       = "ListParsedOnly"
        Effect    = "Allow"
        Action    = ["s3:ListBucket"]
        Resource  = aws_s3_bucket.data.arn
        Condition = {
          StringLike = { "s3:prefix" = ["parsed/*"] }
        }
      }
    ]
  })
}

module "aegis_gate_scorer_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.8"

  name = "${var.cluster_name}-aegis-gate-scorer"

  oidc_providers = {
    this = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["aegis:aegis-gate-scorer-sa"]
    }
  }

  policies = {
    s3 = aws_iam_policy.aegis_gate_scorer_s3.arn
  }
}
