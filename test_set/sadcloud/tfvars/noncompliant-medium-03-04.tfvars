# Par de compliant-medium-03-04: violacao = regiao (sa-east-1)
aws_region = "sa-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 39"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
ec2_count = 3
rds_count = 2
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
