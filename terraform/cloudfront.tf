resource "aws_cloudfront_origin_access_control" "oac_s3" {
  name                              = "OAC para S3 ${var.env}"
  description                       = "OAC para acceso a bucket S3 desde CloudFront"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_origin_access_control" "oac_lambda" {
  name                              = "OAC para Lambdas ${var.env}"
  description                       = "OAC para acceso a lambdas desde CloudFront"
  origin_access_control_origin_type = "lambda"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}


resource "aws_cloudfront_distribution" "api" {
  # aliases = [var.env == "pro" ?   :  ]
  default_root_object = "index.html"
  comment             = "CDN API ${var.project} ${var.env}"
  origin {
    domain_name              = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.oac_s3.id
    origin_id                = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    origin_path              = "/www"
  }

  origin {
    domain_name              = replace(replace(aws_lambda_function_url.api_rest.function_url, "https://", ""), "/", "")
    origin_access_control_id = aws_cloudfront_origin_access_control.oac_lambda.id
    origin_id                = aws_lambda_function.api_rest.function_name
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      ip_address_type        = "ipv4"
      origin_protocol_policy = "https-only"
      origin_ssl_protocols = [
        "TLSv1.2",
      ]
    }
  }


  enabled         = true
  is_ipv6_enabled = true
  http_version    = "http2and3"
  price_class     = "PriceClass_All"

  default_cache_behavior {
    allowed_methods = [
      "GET",
      "HEAD",
    ]
    # cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # Caching optimized
    # TODO: Modificacion temporal, no cachea para asegurar que siempre llama a la última versión de la lambda durante el desarrollo.action_trigger {
    # De lo contrario, cada vez que se actualiza la lambda, hay que invalidar la caché de CloudFront
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # Caching disabled
    cached_methods = [
      "GET",
      "HEAD",
    ]
    target_origin_id       = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    viewer_protocol_policy = "redirect-to-https"
  }

  ordered_cache_behavior {
    allowed_methods = [
      "GET",
      "HEAD",
    ]
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    cached_methods = [
      "GET",
      "HEAD",
    ]
    compress               = true
    default_ttl            = 0
    max_ttl                = 0
    min_ttl                = 0
    path_pattern           = "index.html"
    smooth_streaming       = false
    target_origin_id       = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
    viewer_protocol_policy = "redirect-to-https"

  }

  ordered_cache_behavior {
    allowed_methods = [
      "GET",
      "HEAD",
      "OPTIONS"
    ]
    cache_policy_id          = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    cached_methods           = ["GET", "HEAD"]
    compress                 = true
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac"
    path_pattern             = "/api/*"
    smooth_streaming         = false
    target_origin_id         = aws_lambda_function.api_rest.function_name
    viewer_protocol_policy   = "redirect-to-https"
  }


  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    # acm_certificate_arn      = 
    # minimum_protocol_version = "TLSv1.2_2021"
    # ssl_support_method       = "sni-only"
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "CDN API ${var.project} ${var.env}"
  }

  lifecycle {
    ignore_changes = [web_acl_id]
  }
}
