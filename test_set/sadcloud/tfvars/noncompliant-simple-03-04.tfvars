# Par de compliant-simple-03-04: violacao = regiao (sa-east-1)
aws_region = "sa-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 14"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
