resource "aws_iam_policy" "CodeBuildBasePolicy" {
  name = "CodeBuildBasePolicy-${var.project}-${var.env}-${var.region}"
  path = "/service-role/"
  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Resource" : [
            "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/codebuild/${var.project}-${var.env}-*",
            "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/codebuild/${var.project}-${var.env}-*:*"
          ],
          "Action" : [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ]
        },
        {
          "Effect" : "Allow",
          "Resource" : [
            "arn:aws:s3:::codepipeline-${var.region}-*"
          ],
          "Action" : [
            "s3:PutObject",
            "s3:GetObject",
            "s3:GetObjectVersion",
            "s3:GetBucketAcl",
            "s3:GetBucketLocation"
          ]
        },
        {
          "Effect" : "Allow",
          "Resource" : ["*"],
          "Action" : [
            "ecr:GetAuthorizationToken"
          ]
        },
        {
          "Effect" : "Allow",
          "Resource" : ["${aws_ecr_repository.api_repository.arn}"],
          "Action" : [
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:GetRepositoryPolicy",
            "ecr:DescribeRepositories",
            "ecr:ListImages",
            "ecr:DescribeImages",
            "ecr:BatchGetImage",
            "ecr:InitiateLayerUpload",
            "ecr:UploadLayerPart",
            "ecr:CompleteLayerUpload",
            "ecr:PutImage"
          ]
        },
        {
          "Effect" : "Allow",
          "Action" : [
            "codebuild:CreateReportGroup",
            "codebuild:CreateReport",
            "codebuild:UpdateReport",
            "codebuild:BatchPutTestCases",
            "codebuild:BatchPutCodeCoverages"
          ],
          "Resource" : [
            "arn:aws:codebuild:${var.region}:${data.aws_caller_identity.current.account_id}:report-group/${var.project}-${var.env}-*"
          ]
        },
        {
          Action = [
            "lambda:UpdateFunctionCode",
          ]
          Effect   = "Allow"
          Resource = [aws_lambda_function.api_rest.arn]
        },
      ]
    }
  )
}

resource "aws_iam_policy" "CodeBuildCodeConnectionsSourceCredentialsPolicy" {
  name = "CodeBuildCodeConnectionsSourceCredentialsPolicy-${var.project}-${var.env}"
  path = "/service-role/"
  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Action" : [
            "codestar-connections:GetConnectionToken",
            "codestar-connections:GetConnection",
            "codeconnections:GetConnectionToken",
            "codeconnections:GetConnection",
            "codeconnections:UseConnection"
          ],
          "Resource" : [
            "arn:aws:codeconnections:eu-west-1:${data.aws_caller_identity.current.account_id}:connection/bdeff464-af64-4c76-a2eb-b52808ffc3c1"
          ]
        }
      ]
    }
  )
}



resource "aws_iam_role" "codebuild-service-role" {
  path = "/service-role/"
  name = "codebuild-${var.project}-${var.env}-service-role"
  assume_role_policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Principal" : { "Service" : "codebuild.amazonaws.com" },
          "Action" : "sts:AssumeRole"
        }
      ]
    }
  )
  max_session_duration = 3600
}


resource "aws_iam_role_policy_attachment" "codebuild-service-role-attachment" {
  role       = aws_iam_role.codebuild-service-role.name
  policy_arn = aws_iam_policy.CodeBuildBasePolicy.arn
}

resource "aws_iam_role_policy_attachment" "codebuild-service-role-attachment2" {
  role       = aws_iam_role.codebuild-service-role.name
  policy_arn = aws_iam_policy.CodeBuildCodeConnectionsSourceCredentialsPolicy.arn
}

