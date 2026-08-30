# Pair for compliant-simple-01: same resources, violation = region
aws_region = "us-west-2"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time A"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
