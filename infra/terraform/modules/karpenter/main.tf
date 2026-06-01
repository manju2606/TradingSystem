# Karpenter IAM + Helm release + NodeClass + NodePool

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}

# ── Karpenter Controller IRSA ─────────────────────────────────────────────────

data "aws_iam_policy_document" "karpenter_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:karpenter:karpenter"]
    }
    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_provider_url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "karpenter_controller" {
  statement {
    sid = "Karpenter"
    actions = [
      "ec2:CreateLaunchTemplate", "ec2:DeleteLaunchTemplate",
      "ec2:CreateFleet", "ec2:RunInstances", "ec2:CreateTags",
      "ec2:TerminateInstances", "ec2:DescribeLaunchTemplates",
      "ec2:DescribeInstances", "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets", "ec2:DescribeInstanceTypes",
      "ec2:DescribeInstanceTypeOfferings", "ec2:DescribeAvailabilityZones",
      "ec2:DescribeImages", "ec2:DescribeSpotPriceHistory",
      "pricing:GetProducts",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "PassNodeRole"
    actions   = ["iam:PassRole"]
    resources = [var.node_role_arn]
  }

  statement {
    sid       = "EKSClusterAccess"
    actions   = ["eks:DescribeCluster"]
    resources = ["arn:aws:eks:${local.region}:${local.account_id}:cluster/${var.cluster_name}"]
  }

  statement {
    sid     = "SQSInterruption"
    actions = ["sqs:DeleteMessage", "sqs:GetQueueUrl", "sqs:GetQueueAttributes", "sqs:ReceiveMessage"]
    resources = [aws_sqs_queue.interruption.arn]
  }
}

resource "aws_iam_role" "karpenter" {
  name               = "${var.cluster_name}-karpenter"
  assume_role_policy = data.aws_iam_policy_document.karpenter_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "karpenter" {
  name   = "${var.cluster_name}-karpenter-policy"
  role   = aws_iam_role.karpenter.name
  policy = data.aws_iam_policy_document.karpenter_controller.json
}

# ── Spot Interruption SQS Queue ───────────────────────────────────────────────

resource "aws_sqs_queue" "interruption" {
  name                      = "${var.cluster_name}-karpenter-interruption"
  message_retention_seconds = 300
  tags                      = var.tags
}

resource "aws_sqs_queue_policy" "interruption" {
  queue_url = aws_sqs_queue.interruption.url
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = ["events.amazonaws.com", "sqs.amazonaws.com"] }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.interruption.arn
    }]
  })
}

resource "aws_cloudwatch_event_rule" "spot_interruption" {
  name        = "${var.cluster_name}-spot-interruption"
  description = "Karpenter spot interruption"
  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Spot Instance Interruption Warning"]
  })
  tags = var.tags
}

resource "aws_cloudwatch_event_target" "spot_interruption" {
  rule = aws_cloudwatch_event_rule.spot_interruption.name
  arn  = aws_sqs_queue.interruption.arn
}

# ── Karpenter Helm Release ────────────────────────────────────────────────────

resource "helm_release" "karpenter" {
  namespace        = "karpenter"
  create_namespace = true
  name             = "karpenter"
  repository       = "oci://public.ecr.aws/karpenter"
  chart            = "karpenter"
  version          = var.karpenter_version
  wait             = true

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.karpenter.arn
  }
  set { name = "settings.clusterName";     value = var.cluster_name }
  set { name = "settings.clusterEndpoint"; value = var.cluster_endpoint }
  set { name = "settings.interruptionQueue"; value = aws_sqs_queue.interruption.name }
}

# ── EC2NodeClass ──────────────────────────────────────────────────────────────

resource "kubernetes_manifest" "node_class" {
  manifest = {
    apiVersion = "karpenter.k8s.aws/v1"
    kind       = "EC2NodeClass"
    metadata   = { name = "default" }
    spec = {
      amiSelectorTerms = [{ alias = "al2023@latest" }]
      role             = split("/", var.node_role_arn)[1]
      subnetSelectorTerms = [
        { tags = { "karpenter.sh/discovery" = var.cluster_name } }
      ]
      securityGroupSelectorTerms = [
        { tags = { "karpenter.sh/discovery" = var.cluster_name } }
      ]
      blockDeviceMappings = [{
        deviceName = "/dev/xvda"
        ebs = {
          volumeSize = "50Gi"
          volumeType = "gp3"
          encrypted  = true
        }
      }]
    }
  }

  depends_on = [helm_release.karpenter]
}

# ── NodePool ──────────────────────────────────────────────────────────────────

resource "kubernetes_manifest" "node_pool" {
  manifest = {
    apiVersion = "karpenter.sh/v1"
    kind       = "NodePool"
    metadata   = { name = "default" }
    spec = {
      template = {
        metadata = { labels = { role = "workload" } }
        spec = {
          nodeClassRef  = { group = "karpenter.k8s.aws"; kind = "EC2NodeClass"; name = "default" }
          requirements = [
            { key = "karpenter.sh/capacity-type"; operator = "In"; values = ["spot", "on-demand"] },
            { key = "kubernetes.io/arch";          operator = "In"; values = ["amd64"] },
            { key = "karpenter.k8s.aws/instance-category"; operator = "In"; values = ["c", "m", "r"] },
            { key = "karpenter.k8s.aws/instance-generation"; operator = "Gt"; values = ["2"] },
          ]
        }
      }
      limits = { cpu = var.max_cpu; memory = var.max_memory }
      disruption = {
        consolidationPolicy = "WhenEmptyOrUnderutilized"
        consolidateAfter    = "1m"
      }
    }
  }

  depends_on = [kubernetes_manifest.node_class]
}
