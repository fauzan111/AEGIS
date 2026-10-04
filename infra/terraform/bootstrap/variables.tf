variable "aws_region" {
  description = "AWS region for the state bucket. Should match the region the demo environment itself will deploy into."
  type        = string
  default     = "eu-west-1"
}

variable "state_bucket_name" {
  description = "Globally-unique S3 bucket name for Terraform state. S3 bucket names are global across all AWS accounts, so the default below will likely collide — override it with -var or a tfvars file."
  type        = string
  default     = "aegis-mvp-tfstate"
}
