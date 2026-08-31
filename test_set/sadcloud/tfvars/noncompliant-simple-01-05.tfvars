# Par de compliant-simple-01-05: violacao = tag 'Projeto' vazia
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 05"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = false
enable_rds = true
enable_s3 = false
rds_count = 1
rds_instance_class = "db.t2.micro"
