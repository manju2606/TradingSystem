# Run once to create the S3 + DynamoDB backend resources before any other terraform apply.
# terraform -chdir=infra/terraform/bootstrap apply

provider "aws" {
  region = var.region
}

variable "region" {
  default = "ap-south-1"
}

variable "account_id" {
  description = "AWS account ID — used to make the bucket name globally unique"
}

resource "aws_s3_bucket" "state" {
  bucket        = "trading-terraform-state-${var.account_id}"
  force_destroy = false

  tags = { Name = "trading-terraform-state" }
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "locks" {
  name         = "trading-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = { Name = "trading-terraform-locks" }
}

output "state_bucket" { value = aws_s3_bucket.state.bucket }
output "lock_table"   { value = aws_dynamodb_table.locks.name }
