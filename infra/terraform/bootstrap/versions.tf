terraform {
  required_version = ">= 1.16.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.67"
    }
  }

  # Intentionally local state. This config creates the S3 bucket that the
  # *real* infra (environments/demo) stores its state in — it can't use
  # that same bucket for its own state before the bucket exists. Run this
  # once per AWS account, keep terraform.tfstate here checked out of git
  # (see .gitignore), and don't touch it again unless the bucket itself
  # needs to change.
}
