
# IAM Role para EventBridge Scheduler
resource "aws_iam_role" "scheduler-cron-role" {
  name = "${var.project}-${var.env}-cron-role"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# IAM Policy para que el Scheduler pueda iniciar CodeBuild
resource "aws_iam_policy" "scheduler-execution-policy" {
  name = "Amazon-EventBridge-Scheduler-Execution-Policy-${var.project}-${var.env}"
  path = "/service-role/"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "codebuild:StartBuild"
        ]
        Resource = [
          aws_codebuild_project.cron.arn
        ]
      }
    ]
  })
}

# Adjuntar la política al rol
resource "aws_iam_role_policy_attachment" "scheduler-policy-attach" {
  role       = aws_iam_role.scheduler-cron-role.name
  policy_arn = aws_iam_policy.scheduler-execution-policy.arn
}

resource "aws_codebuild_project" "cron" {
  name         = "${var.project}-${var.env}-cron"
  service_role = aws_iam_role.codebuild-service-role.arn
  source {
    buildspec           = "scripts/buildspec.yml"
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
      name  = "S3_BUCKET_NAME"
      value = aws_s3_bucket.frontend_bucket.bucket
    }
  }
}

resource "aws_scheduler_schedule" "cron_ine" {
  name                         = "${var.project}-${var.env}-cron"
  group_name                   = "default"
  schedule_expression          = "rate(1 days)"
  schedule_expression_timezone = "Europe/Madrid"
  state                        = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_codebuild_project.cron.arn
    role_arn = aws_iam_role.scheduler-cron-role.arn

    retry_policy {
      maximum_event_age_in_seconds = 86400
      maximum_retry_attempts       = 0
    }
  }
}
