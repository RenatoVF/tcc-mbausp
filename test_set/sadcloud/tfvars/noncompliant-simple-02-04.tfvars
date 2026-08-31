# Par de compliant-simple-02-04: violacao = Ambiente invalido ('producao')
aws_region = "us-east-1"
required_tags = {
  Projeto = "TCC"
  "Time Responsável" = "Time 09"
  Ambiente = "producao"
}

enable_network = true
enable_ec2 = true
enable_rds = false
enable_s3 = false
ec2_count = 1
instance_type = "t2.micro"
