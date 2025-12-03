# ============================================================================
# Terraform Backend Configuration (Remote State)
# ============================================================================
# Uses S3 for state storage and DynamoDB for state locking
# 
# IMPORTANT: First time setup requires these steps:
# 1. Comment out this backend block
# 2. Run: terraform init && terraform apply -target=module.terraform_state
# 3. Uncomment this backend block  
# 4. Run: terraform init -migrate-state
# ============================================================================

terraform {
  backend "s3" {
    bucket         = "didin-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-2"
    encrypt        = true
    dynamodb_table = "didin-terraform-locks"
  }
}

# ============================================================================
# Bootstrap Resources for Terraform State
# ============================================================================
# These resources create the S3 bucket and DynamoDB table for remote state
# Run with: terraform apply -target=aws_s3_bucket.terraform_state -target=aws_dynamodb_table.terraform_locks
# ============================================================================

resource "aws_s3_bucket" "terraform_state" {
  bucket = "didin-terraform-state"

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(local.tags, {
    Name = "Terraform State"
  })
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "didin-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = merge(local.tags, {
    Name = "Terraform State Locks"
  })
}
