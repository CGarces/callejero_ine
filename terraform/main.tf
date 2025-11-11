terraform {
  backend "s3" {
    bucket               = "callejero-terraform"
    region               = "eu-west-1"
    workspace_key_prefix = "workspaces"
    key                  = "callejero.tfstate"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.11"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Environment = var.env
      Project     = var.project
    }
  }
}
