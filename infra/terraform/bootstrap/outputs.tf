output "state_bucket_name" {
  description = "Name of the S3 bucket holding Terraform state for every other environment. Copy this into environments/demo/backend.tf."
  value       = aws_s3_bucket.tfstate.id
}

output "aws_region" {
  description = "Region the state bucket lives in — the demo environment's backend config must match."
  value       = var.aws_region
}
