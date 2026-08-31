# Par de compliant-complex-multi-05: violacao multipla (03, 04A) - regiao (us-west-2); EC2 fora da familia 't' em HML
aws_region = "us-west-2"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 90"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 8
rds_count = 2
instance_type = "m5.large"
rds_instance_class = "db.t2.micro"
