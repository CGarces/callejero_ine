locals {
  lambda_name = "api_rest-${var.project}-${var.env}"
  lambda_code = <<-EOF
import json


def lambda_handler(event, context):
		return {
				"statusCode": 200,
				"headers": {"content-type": "application/json"},
				"body": json.dumps({"message": "ok", "event": event}),
		}
EOF
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/api_rest.zip"

  source {
    content  = local.lambda_code
    filename = "lambda_function.py"
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${local.lambda_name}-role"
  assume_role_policy = <<-POLICY
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Action": "sts:AssumeRole",
			"Principal": {"Service": "lambda.amazonaws.com"},
			"Effect": "Allow"
		}
	]
}
POLICY
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "api_rest" {
  function_name = local.lambda_name
  role          = aws_iam_role.lambda_exec.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.14"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  timeout     = 10
  memory_size = 128
  publish     = true
}

resource "aws_lambda_function_url" "api_rest" {
  function_name      = aws_lambda_function.api_rest.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET"]
    allow_headers = ["*"]
  }
}
