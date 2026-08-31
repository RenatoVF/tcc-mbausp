# Par de compliant-simple-01-03: violacao = tag 'Time Responsável' vazia
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = ""
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = false
enable_rds = false
enable_s3 = true
