# Par de compliant-complex-03-02: violacao = regiao (eu-west-1)
aws_region = "eu-west-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 62"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 5
rds_count = 2
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
