# Pair for compliant-medium-01: violation = region
aws_region = "eu-west-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time F"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
ec2_count = 2
rds_count = 1
instance_type = "t2.small"
rds_instance_class = "db.t2.micro"
