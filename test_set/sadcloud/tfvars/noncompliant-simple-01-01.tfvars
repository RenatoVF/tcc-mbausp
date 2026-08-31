# Par de compliant-simple-01-01: violacao = tag 'Time Responsável' vazia
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = ""
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
