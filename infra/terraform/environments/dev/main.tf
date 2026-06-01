provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", local.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", local.cluster_name]
    }
  }
}

terraform {
  backend "s3" {}   # init with: terraform init -backend-config=../../backend.hcl
}

locals {
  env          = "dev"
  cluster_name = "${var.project}-${local.env}"
  prefix       = "${var.project}-${local.env}"
  model_bucket = "${var.project}-models-${local.env}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project     = var.project
    Environment = local.env
    ManagedBy   = "terraform"
  }
}

data "aws_caller_identity" "current" {}

# ── VPC ───────────────────────────────────────────────────────────────────────

module "vpc" {
  source       = "../../modules/vpc"
  name         = local.prefix
  cluster_name = local.cluster_name
  vpc_cidr     = var.vpc_cidr

  single_nat_gateway = true   # cost-saving in dev
}

# ── IAM (must come before EKS — cluster/node roles needed first) ───────────────

module "iam" {
  source            = "../../modules/iam"
  prefix            = local.prefix
  env               = local.env
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  model_bucket      = local.model_bucket

  db_username      = var.db_password != "" ? "trading" : "trading"
  db_password      = var.db_password
  db_host          = module.rds.address
  redis_host       = module.elasticache.primary_endpoint
  redis_auth_token = var.redis_auth_token

  depends_on = [module.eks]
}

# ── EKS ───────────────────────────────────────────────────────────────────────

module "eks" {
  source             = "../../modules/eks"
  cluster_name       = local.cluster_name
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  cluster_role_arn   = module.iam_roles.cluster_role_arn
  node_role_arn      = module.iam_roles.node_role_arn
  ebs_csi_role_arn   = module.iam_roles.ebs_csi_role_arn

  system_node_instance_types = ["t3.medium"]
  system_node_desired        = 2
  system_node_min            = 2
  system_node_max            = 3
}

# Separate pre-EKS IAM roles module (no IRSA — those depend on OIDC which needs the cluster)
module "iam_roles" {
  source = "../../modules/iam_roles"
  prefix = local.prefix
}

# ── RDS ───────────────────────────────────────────────────────────────────────

module "rds" {
  source               = "../../modules/rds"
  identifier           = "${local.prefix}-postgres"
  vpc_id               = module.vpc.vpc_id
  db_subnet_group_name = module.vpc.db_subnet_group_name
  allowed_security_group_ids = [module.eks.node_security_group_id]

  instance_class        = "db.t3.micro"
  allocated_storage     = 20
  max_allocated_storage = 50
  password              = var.db_password

  multi_az            = false
  deletion_protection = false
  skip_final_snapshot = true
  backup_retention_days = 1
}

# ── ElastiCache ───────────────────────────────────────────────────────────────

module "elasticache" {
  source                    = "../../modules/elasticache"
  cluster_id                = "${local.prefix}-redis"
  vpc_id                    = module.vpc.vpc_id
  cache_subnet_group_name   = module.vpc.cache_subnet_group_name
  allowed_security_group_ids = [module.eks.node_security_group_id]

  node_type        = "cache.t3.micro"
  num_cache_nodes  = 1
  auth_token       = var.redis_auth_token
  snapshot_retention_days = 0
}

# ── ECR ───────────────────────────────────────────────────────────────────────

module "ecr" {
  source            = "../../modules/ecr"
  repository_names  = ["trading-api", "trading-streamlit"]
  images_to_keep    = 5
  force_delete      = true   # allow destroy in dev
}

# ── Karpenter ─────────────────────────────────────────────────────────────────

module "karpenter" {
  source             = "../../modules/karpenter"
  cluster_name       = local.cluster_name
  cluster_endpoint   = module.eks.cluster_endpoint
  oidc_provider_arn  = module.eks.oidc_provider_arn
  oidc_provider_url  = module.eks.oidc_provider_url
  node_role_arn      = module.iam_roles.node_role_arn

  max_cpu    = "50"
  max_memory = "200Gi"

  depends_on = [module.eks]
}
