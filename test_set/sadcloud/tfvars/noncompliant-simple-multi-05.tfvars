# Par de compliant-simple-multi-05: violacao multipla (02, 03) - Ambiente invalido ('DEV'); regiao (us-west-2)
aws_region = "us-west-2"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 80"
  Ambiente = "DEV"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
