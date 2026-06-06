# Pair for compliant-complex-05: violation = wrong RDS family for HML (use non-db.t)
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time O"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 10
rds_count = 3
instance_type = "t2.small"
rds_instance_class = "db.m5.large" # violates db.t* requirement for HML 
