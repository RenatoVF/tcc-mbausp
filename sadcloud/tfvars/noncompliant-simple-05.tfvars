# Pair for compliant-simple-05: same resources, violation = missing tag (Projeto)
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time E"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.small"
