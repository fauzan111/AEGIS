# One repo per pinned image the cluster pulls (HLD: "Amazon ECR pinned
# images"). Phase 2 builds and pushes the actual images here.
resource "aws_ecr_repository" "images" {
  for_each = toset(var.ecr_repository_names)

  name                 = each.value
  image_tag_mutability = "IMMUTABLE" # pinned images, not `:latest` floating tags

  # Same reasoning as force_destroy on the S3 data bucket: Phase 2
  # pushes images into these by design, so without this, `terraform
  # destroy` fails with RepositoryNotEmptyException on every teardown.
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Keep only the 10 most recent images per repo — this is a demo
# environment rebuilt often, no need to accumulate old image versions
# indefinitely.
resource "aws_ecr_lifecycle_policy" "images" {
  for_each = aws_ecr_repository.images

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}
