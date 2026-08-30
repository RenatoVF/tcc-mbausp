aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time C"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro" # t family enforced for HML
rds_instance_class = "db.t2.micro"
