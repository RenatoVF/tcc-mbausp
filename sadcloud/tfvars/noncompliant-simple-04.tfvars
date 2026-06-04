# Pair for compliant-simple-04: same resources, violation = wrong RDS family for HML
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time D"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = false
enable_rds = true
enable_s3 = false
rds_count = 1
rds_instance_class = "db.m5.large" # violates HML db.t* rule
