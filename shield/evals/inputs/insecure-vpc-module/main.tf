# Deliberately insecure VPC module for Shield agent evals
# DO NOT use in production — every issue here is intentional

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "eval-vpc"
  }
}

# ISSUE: Wildcard IAM policy (security-reviewer should catch)
resource "aws_iam_role" "admin" {
  name = "admin-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "admin_policy" {
  name = "admin-policy"
  role = aws_iam_role.admin.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

# ISSUE: Security group open to 0.0.0.0/0 on SSH (security-reviewer should catch)
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Web security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ISSUE: 3 NAT gateways with no disable flag (cost-reviewer should catch)
resource "aws_nat_gateway" "az1" {
  allocation_id = aws_eip.nat_az1.id
  subnet_id     = aws_subnet.public_az1.id
}

resource "aws_nat_gateway" "az2" {
  allocation_id = aws_eip.nat_az2.id
  subnet_id     = aws_subnet.public_az2.id
}

resource "aws_nat_gateway" "az3" {
  allocation_id = aws_eip.nat_az3.id
  subnet_id     = aws_subnet.public_az3.id
}

resource "aws_eip" "nat_az1" {}
resource "aws_eip" "nat_az2" {}
resource "aws_eip" "nat_az3" {}

# ISSUE: Hardcoded API key in variable default (security-reviewer should catch)
variable "api_secret" {
  type    = string
  default = "sk-1234567890abcdef"
}

# ISSUE: CloudWatch log group without KMS encryption (security-reviewer should catch)
resource "aws_cloudwatch_log_group" "flow_logs" {
  name = "/vpc/flow-logs"
}

# ISSUE: No deletion protection on RDS (operations-reviewer should catch)
resource "aws_db_instance" "main" {
  identifier     = "eval-db"
  engine         = "postgres"
  instance_class = "db.t3.micro"
  allocated_storage = 20
  username       = "admin"
  password       = var.api_secret

  deletion_protection = false
  skip_final_snapshot = true
}

# ISSUE: S3 bucket without encryption or public access block (security-reviewer should catch)
resource "aws_s3_bucket" "data" {
  bucket = "eval-data-bucket"
}

# OK: Port 443 open to 0.0.0.0/0 is intentional for ALB
# (security-reviewer should NOT flag this as an issue)

resource "aws_subnet" "public_az1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
}

resource "aws_subnet" "public_az2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
}

resource "aws_subnet" "public_az3" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1c"
}
