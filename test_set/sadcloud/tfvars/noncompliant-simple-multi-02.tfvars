# Par de compliant-simple-multi-02: violacao multipla (01, 03) - tag 'Projeto' vazia; regiao (ap-southeast-1)
aws_region = "ap-southeast-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 77"
  Ambiente = "PRD"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
