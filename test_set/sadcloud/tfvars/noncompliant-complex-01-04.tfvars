# Par de compliant-complex-01-04: violacao = tag 'Projeto' vazia
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 54"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 7
rds_count = 3
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
