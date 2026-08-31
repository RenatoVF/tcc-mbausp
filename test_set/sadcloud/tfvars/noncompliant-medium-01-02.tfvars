# Par de compliant-medium-01-02: violacao = tag 'Projeto' vazia
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 27"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = false
ec2_count = 3
rds_count = 1
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
