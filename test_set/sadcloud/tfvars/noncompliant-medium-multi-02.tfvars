# Par de compliant-medium-multi-02: violacao multipla (03, 04B) - regiao (ap-southeast-1); RDS fora da familia 'db.t' em HML
aws_region = "ap-southeast-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 82"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = false
ec2_count = 3
rds_count = 1
instance_type = "t2.micro"
rds_instance_class = "db.m5.large"
