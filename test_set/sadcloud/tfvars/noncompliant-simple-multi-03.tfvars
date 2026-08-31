# Par de compliant-simple-multi-03: violacao multipla (01, 04A) - tag 'Projeto' vazia; EC2 fora da familia 't' em HML
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 78"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "m5.large"
