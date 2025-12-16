resource "aws_ecr_repository" "api_repository" {
  name                 = "${var.project}-${var.env}-api"
  image_tag_mutability = "MUTABLE"
}

# Permite a Lambda obtener la imagen desde ECR
resource "aws_ecr_repository_policy" "api_repository" {
  repository = aws_ecr_repository.api_repository.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "LambdaECRImageRetrievalPolicy"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy"
        ]
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "api_repository" {
  repository = aws_ecr_repository.api_repository.name
  policy     = data.aws_ecr_lifecycle_policy_document.expire_untagged_images.json
}

data "aws_ecr_lifecycle_policy_document" "expire_untagged_images" {
  rule {
    priority    = 1
    description = "Remove untaged images after 1 week"

    selection {
      tag_status   = "untagged"
      count_type   = "sinceImagePushed"
      count_number = 7
      count_unit   = "days"
    }
    action {
      type = "expire"
    }
  }
}
