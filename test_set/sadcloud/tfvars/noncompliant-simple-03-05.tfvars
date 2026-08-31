# Par de compliant-simple-03-05: violacao = regiao (eu-central-1)
aws_region = "eu-central-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 15"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = false
enable_rds = true
enable_s3 = false
rds_count = 1
rds_instance_class = "db.t2.micro"
