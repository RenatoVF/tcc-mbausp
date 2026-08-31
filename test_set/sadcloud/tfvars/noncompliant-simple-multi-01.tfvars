# Par de compliant-simple-multi-01: violacao multipla (01, 02) - tag 'Projeto' vazia; Ambiente invalido ('STG')
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 76"
  Ambiente = "STG"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
