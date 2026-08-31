# Par de compliant-simple-multi-04: violacao multipla (01, 04B) - tag 'Projeto' vazia; RDS fora da familia 'db.t' em HML
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 79"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = false
enable_rds = true
enable_s3 = false
rds_count = 1
rds_instance_class = "db.m5.large"
