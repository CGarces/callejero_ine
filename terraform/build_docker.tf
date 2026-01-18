
resource "aws_codebuild_project" "api" {
  name         = "${var.project}-${var.env}-api"
  service_role = aws_iam_role.codebuild-service-role.arn
  source {
    buildspec           = "api_rest/buildspec.yml"
    type                = "GITHUB"
    location            = "https://github.com/CGarces/callejero_ine"
    report_build_status = true
    git_clone_depth     = 1
    git_submodules_config {
      fetch_submodules = false
    }
    auth {
      type     = "CODECONNECTIONS"
      resource = "arn:aws:codeconnections:${var.region}:${data.aws_caller_identity.current.account_id}:connection/bdeff464-af64-4c76-a2eb-b52808ffc3c1"
    }
  }
  artifacts {
    type = "NO_ARTIFACTS"
  }
  environment {
    type                        = "LINUX_CONTAINER"
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux-x86_64-standard:5.0"
    privileged_mode             = true
    image_pull_credentials_type = "CODEBUILD"
    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = aws_ecr_repository.api_repository.name
    }
    environment_variable {
      name  = "ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }
    environment_variable {
      name  = "S3_BUCKET_NAME"
      value = aws_s3_bucket.frontend_bucket.bucket
    }
  }
}

resource "aws_codebuild_webhook" "api" {
  project_name = aws_codebuild_project.api.name
  build_type   = "BUILD"
  filter_group {
    filter {
      type    = "EVENT"
      pattern = "PUSH"
    }

    filter {
      type    = "HEAD_REF"
      pattern = "^refs/heads/main$"
    }
  }
}
