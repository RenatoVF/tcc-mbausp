# Par de compliant-complex-multi-03: violacao multipla (03, 04A, 04B) - regiao (sa-east-1); EC2 fora da familia 't' em HML; RDS fora da familia 'db.t' em HML
aws_region = "sa-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 88"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = true
enable_elbv2 = true
enable_eks = true
ec2_count = 6
rds_count = 3
instance_type = "m5.large"
rds_instance_class = "db.m5.large"
