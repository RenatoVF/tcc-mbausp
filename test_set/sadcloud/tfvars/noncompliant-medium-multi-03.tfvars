# Par de compliant-medium-multi-03: violacao multipla (04A, 04B) - EC2 fora da familia 't' em HML; RDS fora da familia 'db.t' em HML
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 83"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = false
ec2_count = 2
rds_count = 2
instance_type = "m5.large"
rds_instance_class = "db.m5.large"
