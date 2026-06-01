output "role_arn"               { value = aws_iam_role.karpenter.arn }
output "interruption_queue_url" { value = aws_sqs_queue.interruption.url }
