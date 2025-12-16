resource "aws_iam_role" "lambda_exec" {
  name = "api_rest-${var.project}-${var.env}-role"
  assume_role_policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Action" : "sts:AssumeRole",
          "Principal" : { "Service" : "lambda.amazonaws.com" },
          "Effect" : "Allow"
        }
      ]
    }
  )
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "api_rest" {
  function_name = "api_rest-${var.project}-${var.env}"
  image_uri     = "${aws_ecr_repository.api_repository.repository_url}:latest"
  package_type  = "Image"
  role          = aws_iam_role.lambda_exec.arn

  timeout     = 30
  memory_size = 1024
  publish     = true

  environment {
    variables = {
      "AWS_LWA_ASYNC_INIT" = "true"
    }
  }

}

resource "aws_lambda_permission" "api_rest_cf" {
  statement_id           = "AllowCloudFrontServicePrincipal"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.api_rest.function_name
  principal              = "*" #TODO deberia ser "cloudfront.amazonaws.com", pero no funciona ¿?
  source_arn             = aws_cloudfront_distribution.api.arn
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "api_rest_cf_invoke" {
  statement_id  = "AllowCloudFrontServicePrincipalInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_rest.function_name
  principal     = "cloudfront.amazonaws.com"
  source_arn    = aws_cloudfront_distribution.api.arn
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
