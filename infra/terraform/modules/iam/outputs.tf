output "cluster_role_arn"   { value = aws_iam_role.cluster.arn }
output "node_role_arn"      { value = aws_iam_role.node.arn }
output "ebs_csi_role_arn"   { value = aws_iam_role.ebs_csi.arn }
output "api_role_arn"       { value = aws_iam_role.api.arn }
output "model_bucket"       { value = aws_s3_bucket.models.bucket }
output "db_secret_arn"      { value = aws_secretsmanager_secret.db.arn }
output "redis_secret_arn"   { value = aws_secretsmanager_secret.redis.arn }
