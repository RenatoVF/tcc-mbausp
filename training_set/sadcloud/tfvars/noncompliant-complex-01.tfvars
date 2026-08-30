# Pair for compliant-complex-01: violation = region
aws_region = "ap-southeast-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time K"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 4
rds_count = 2
instance_type = "t2.small"
rds_instance_class = "db.t2.micro"
