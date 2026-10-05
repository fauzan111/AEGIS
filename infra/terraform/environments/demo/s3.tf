# Data bucket for pcap / CSV / scored-windows (HLD: "Amazon S3 pcap /
# CSV / scores"). Same hardening pattern as the state bucket in
# infra/terraform/bootstrap (encryption, public-access block, TLS-only),
# except this one is NOT prevent_destroy — it's meant to go away with
# the rest of the demo environment on `terraform destroy`.
resource "aws_s3_bucket" "data" {
  bucket = var.data_bucket_name

  # This bucket churns constantly (every demo run writes new captures/
  # scores) and only has a 7-day expiry, so it's very likely non-empty
  # at teardown time. Without force_destroy, `terraform destroy` right
  # after a demo would fail with BucketNotEmpty — directly against the
  # point of this being a short-lived, cleanly-destroyable environment.
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "data_tls_only" {
  bucket = aws_s3_bucket.data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*",
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

resource "aws_s3_bucket_lifecycle_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "expire-captures-after-7-days"
    status = "Enabled"

    # HLD: "write-only, 7-day lifecycle expiry" — this is a demo
    # environment generating pcap/CSV data on every run, not a
    # permanent data lake.
    expiration {
      days = 7
    }
  }
}
