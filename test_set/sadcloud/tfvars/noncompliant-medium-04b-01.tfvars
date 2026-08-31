# Par de compliant-medium-04b-01: violacao = RDS fora da familia 'db.t' em HML
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 46"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = false
ec2_count = 2
rds_count = 1
instance_type = "t2.micro"
rds_instance_class = "db.m5.large"
