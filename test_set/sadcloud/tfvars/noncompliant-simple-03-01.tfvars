# Par de compliant-simple-03-01: violacao = regiao (us-west-2)
aws_region = "us-west-2"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 11"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
