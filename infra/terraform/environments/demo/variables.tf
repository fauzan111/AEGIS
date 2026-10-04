variable "aws_region" {
  description = "AWS region for the demo environment. Must match the region in this file's own `backend \"s3\"` block in versions.tf — that block can't reference this variable (Terraform evaluates backend config before any variables exist), so if you change this, change the backend block's `region` too. Also must match infra/terraform/bootstrap's aws_region, since that's where the state bucket actually lives."
  type        = string
  default     = "eu-west-1"
}
