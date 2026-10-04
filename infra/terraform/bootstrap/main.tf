provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "aegis-mvp"
      ManagedBy = "terraform"
      Component = "state-bootstrap"
    }
  }
}

resource "aws_s3_bucket" "tfstate" {
  bucket = var.state_bucket_name

  # Safety net: an accidental `terraform destroy` on this config won't
  # delete the bucket (and with it, every other environment's state)
  # unless someone deliberately removes this lifecycle block first.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    # Not required for the lock itself (use_lockfile's conditional writes
    # handle that, independent of versioning) — this is here so a bad
    # apply or an accidental overwrite has a rollback path via old
    # object versions.
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    id     = "expire-noncurrent-state-versions"
    status = "Enabled"

    # This bucket is never torn down, so without this every apply across
    # every demo cycle adds a noncurrent version that would otherwise
    # live forever. State files are tiny, but there's no reason to let
    # it grow unbounded.
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      # AES256 (SSE-S3) rather than SSE-KMS: no sensitive data beyond
      # resource IDs/ARNs lives in this state, so the extra per-request
      # KMS cost and moving part isn't worth it for a setup whose whole
      # goal is staying simple.
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "tfstate_tls_only" {
  bucket = aws_s3_bucket.tfstate.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.tfstate.arn,
          "${aws_s3_bucket.tfstate.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
