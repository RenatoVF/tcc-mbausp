# Par de compliant-complex-multi-01: violacao multipla (01, 03, 04B) - tag 'Projeto' vazia; regiao (eu-west-1); RDS fora da familia 'db.t' em HML
aws_region = "eu-west-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 86"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 4
rds_count = 2
instance_type = "t2.micro"
rds_instance_class = "db.m5.large"
