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

# VPC: vpc.tf · EKS: eks.tf · ECR: ecr.tf · S3: s3.tf · IRSA roles: iam.tf
# K8s namespaces: namespaces.tf · kubernetes provider: k8s-provider.tf
# (see docs/AWS-MVP/implementation-plan.md for the phase this belongs to)
