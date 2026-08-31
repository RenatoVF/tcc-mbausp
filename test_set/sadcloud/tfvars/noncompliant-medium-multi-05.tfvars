# Par de compliant-medium-multi-05: violacao multipla (01, 03, 04A) - tag 'Projeto' vazia; regiao (us-west-2); EC2 fora da familia 't' em HML
aws_region = "us-west-2"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 85"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
ec2_count = 2
rds_count = 1
instance_type = "m5.large"
rds_instance_class = "db.t2.micro"
