# Par de compliant-complex-04a-02: violacao = EC2 fora da familia 't' em HML
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 67"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 5
rds_count = 2
instance_type = "m5.large"
rds_instance_class = "db.t2.micro"
