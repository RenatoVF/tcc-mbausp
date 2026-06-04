aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time B"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = false
enable_rds = true
enable_s3 = false
ec2_count = 0
rds_count = 1
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
