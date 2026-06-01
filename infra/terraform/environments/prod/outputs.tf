output "cluster_name"       { value = module.eks.cluster_name }
output "cluster_endpoint"   { value = module.eks.cluster_endpoint }
output "ecr_urls"           { value = module.ecr.repository_urls }
output "rds_endpoint"       { value = module.rds.endpoint }
output "redis_endpoint"     { value = module.elasticache.primary_endpoint }
output "db_secret_arn"      { value = module.iam.db_secret_arn }
output "redis_secret_arn"   { value = module.iam.redis_secret_arn }
output "model_bucket"       { value = module.iam.model_bucket }

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
