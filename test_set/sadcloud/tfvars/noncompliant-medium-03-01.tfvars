# Par de compliant-medium-03-01: violacao = regiao (us-west-2)
aws_region = "us-west-2"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 36"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = false
ec2_count = 2
rds_count = 1
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
