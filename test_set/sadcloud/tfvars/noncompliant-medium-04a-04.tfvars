# Par de compliant-medium-04a-04: violacao = EC2 fora da familia 't' em HML
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 44"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
ec2_count = 3
rds_count = 2
instance_type = "m5.large"
rds_instance_class = "db.t2.micro"
