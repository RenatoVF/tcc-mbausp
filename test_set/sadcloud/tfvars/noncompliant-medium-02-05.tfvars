# Par de compliant-medium-02-05: violacao = Ambiente invalido ('homolog')
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 35"
  Ambiente = "homolog"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
ec2_count = 2
rds_count = 1
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
