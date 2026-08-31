# Par de compliant-complex-multi-02: violacao multipla (01, 04A, 04B) - tag 'Projeto' vazia; EC2 fora da familia 't' em HML; RDS fora da familia 'db.t' em HML
aws_region = "us-east-1"
required_tags = {
  Projeto = ""
  "Time Responsável" = "Time 87"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 5
rds_count = 2
instance_type = "m5.large"
rds_instance_class = "db.m5.large"
