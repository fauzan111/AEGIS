output "cluster_name" {
  description = "Run `aws eks update-kubeconfig --name <this> --region <aws_region>` after apply — the EKS module no longer writes a kubeconfig for you."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "ecr_repository_urls" {
  description = "Push pinned images here in Phase 2, e.g. `docker push <url>:v1`."
  value       = { for k, v in aws_ecr_repository.images : k => v.repository_url }
}

output "data_bucket_name" {
  value = aws_s3_bucket.data.id
}

output "sbi_capture_irsa_role_arn" {
  description = "Annotate the sbi-capture-sa ServiceAccount in the aegis namespace with eks.amazonaws.com/role-arn = this, when Phase 2 creates it."
  value       = module.sbi_capture_irsa.arn
}

output "aegis_gate_scorer_irsa_role_arn" {
  description = "Annotate the aegis-gate-scorer-sa ServiceAccount (infra/k8s/aegis-gate-scoring-cronjob.yaml) with eks.amazonaws.com/role-arn = this. NOT the dashboard's aegis-gate-sa - that ServiceAccount has no S3 grant at all, see iam.tf's comment for why."
  value       = module.aegis_gate_scorer_irsa.arn
}
