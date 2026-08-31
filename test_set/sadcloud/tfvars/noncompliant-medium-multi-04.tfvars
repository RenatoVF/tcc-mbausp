# Par de compliant-medium-multi-04: violacao multipla (01, 02, 03) - tag 'Projeto' vazia; Ambiente invalido ('homolog'); regiao (eu-central-1)
aws_region = "eu-central-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 84"
  Ambiente = "homolog"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
ec2_count = 3
rds_count = 2
instance_type = "t2.micro"
rds_instance_class = "db.t2.micro"
