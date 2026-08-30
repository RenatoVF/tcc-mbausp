# Pair for compliant-medium-02: violation = wrong EC2 family for HML
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time G"
  Ambiente = "HML"
}

enable_network = true
enable_ec2 = true
enable_rds = true
enable_s3 = false
ec2_count = 2
rds_count = 1
instance_type = "m5.large" # violates HML t-family rule
rds_instance_class = "db.t2.micro"
