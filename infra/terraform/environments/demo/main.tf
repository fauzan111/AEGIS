provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "aegis-mvp"
      ManagedBy   = "terraform"
      Environment = "demo"
    }
  }
}

# VPC, EKS, ECR, S3 data buckets, and IAM roles land here in Phase 1
# (see docs/AWS-MVP/implementation-plan.md). This file intentionally
# stops at the provider block until that phase starts — Phase 0's job
# was tooling and structure, not resources.
