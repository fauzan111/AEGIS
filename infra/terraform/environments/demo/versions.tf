terraform {
  required_version = ">= 1.16.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.67"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 3.3"
    }
  }

  backend "s3" {
    # TODO: replace once `terraform apply` has run in infra/terraform/bootstrap
    # and printed the `state_bucket_name` output. This bucket doesn't exist
    # yet — that's expected until Phase 0's deploy-time step runs.
    bucket = "REPLACE-WITH-BOOTSTRAP-OUTPUT-state_bucket_name"
    key    = "environments/demo/terraform.tfstate"
    # Backend blocks can't reference variables (Terraform evaluates this
    # before any variables exist), so this is a literal that has to be
    # kept in sync by hand with var.aws_region in this same directory's
    # variables.tf, and with aws_region in infra/terraform/bootstrap
    # (that's the account/region the bucket below actually lives in).
    region = "eu-west-1"

    # S3-native locking (Terraform >= 1.11) — no DynamoDB table needed.
    # Every teammate and CI runner must be on Terraform >= 1.16 for this
    # to actually protect concurrent applies; see infra/terraform/README.md.
    use_lockfile = true
  }
}
