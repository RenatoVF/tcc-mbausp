# Par de compliant-simple-01-04: violacao = tag 'Projeto' vazia
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 04"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
