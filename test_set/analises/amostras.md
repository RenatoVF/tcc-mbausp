# Mapeamento dos 180 casos do test_set (90 pares)

Gerado por `common/sadcloud/gerar_test_set.py`, seed fixa `20260831` (documentada no cabecalho do script, para reprodutibilidade).

| Arquivo Compliant | Arquivo Non-compliant | Complexidade | Regra(s) Violada(s) | Recursos | Violacao |
|---|---|---|---|---|---|
| compliant-simple-01-01 | noncompliant-simple-01-01 | simple | 01 | EC2(1) | violacao = tag 'Time Responsável' vazia |
| compliant-simple-01-02 | noncompliant-simple-01-02 | simple | 01 | RDS(1) | violacao = tag 'Time Responsável' vazia |
| compliant-simple-01-03 | noncompliant-simple-01-03 | simple | 01 | S3 | violacao = tag 'Time Responsável' vazia |
| compliant-simple-01-04 | noncompliant-simple-01-04 | simple | 01 | EC2(1) | violacao = tag 'Projeto' vazia |
| compliant-simple-01-05 | noncompliant-simple-01-05 | simple | 01 | RDS(1) | violacao = tag 'Projeto' vazia |
| compliant-simple-02-01 | noncompliant-simple-02-01 | simple | 02 | EC2(1) | violacao = Ambiente invalido ('DEV') |
| compliant-simple-02-02 | noncompliant-simple-02-02 | simple | 02 | RDS(1) | violacao = Ambiente invalido ('STG') |
| compliant-simple-02-03 | noncompliant-simple-02-03 | simple | 02 | S3 | violacao = Ambiente invalido ('QA') |
| compliant-simple-02-04 | noncompliant-simple-02-04 | simple | 02 | EC2(1) | violacao = Ambiente invalido ('producao') |
| compliant-simple-02-05 | noncompliant-simple-02-05 | simple | 02 | RDS(1) | violacao = Ambiente invalido ('homolog') |
| compliant-simple-03-01 | noncompliant-simple-03-01 | simple | 03 | EC2(1) | violacao = regiao (us-west-2) |
| compliant-simple-03-02 | noncompliant-simple-03-02 | simple | 03 | RDS(1) | violacao = regiao (eu-west-1) |
| compliant-simple-03-03 | noncompliant-simple-03-03 | simple | 03 | S3 | violacao = regiao (ap-southeast-1) |
| compliant-simple-03-04 | noncompliant-simple-03-04 | simple | 03 | EC2(1) | violacao = regiao (sa-east-1) |
| compliant-simple-03-05 | noncompliant-simple-03-05 | simple | 03 | RDS(1) | violacao = regiao (eu-central-1) |
| compliant-simple-04a-01 | noncompliant-simple-04a-01 | simple | 04A | EC2(1) | violacao = EC2 fora da familia 't' em HML |
| compliant-simple-04a-02 | noncompliant-simple-04a-02 | simple | 04A | EC2(1) | violacao = EC2 fora da familia 't' em HML |
| compliant-simple-04a-03 | noncompliant-simple-04a-03 | simple | 04A | EC2(1) | violacao = EC2 fora da familia 't' em HML |
| compliant-simple-04a-04 | noncompliant-simple-04a-04 | simple | 04A | EC2(1) | violacao = EC2 fora da familia 't' em HML |
| compliant-simple-04a-05 | noncompliant-simple-04a-05 | simple | 04A | EC2(1) | violacao = EC2 fora da familia 't' em HML |
| compliant-simple-04b-01 | noncompliant-simple-04b-01 | simple | 04B | RDS(1) | violacao = RDS fora da familia 'db.t' em HML |
| compliant-simple-04b-02 | noncompliant-simple-04b-02 | simple | 04B | RDS(1) | violacao = RDS fora da familia 'db.t' em HML |
| compliant-simple-04b-03 | noncompliant-simple-04b-03 | simple | 04B | RDS(1) | violacao = RDS fora da familia 'db.t' em HML |
| compliant-simple-04b-04 | noncompliant-simple-04b-04 | simple | 04B | RDS(1) | violacao = RDS fora da familia 'db.t' em HML |
| compliant-simple-04b-05 | noncompliant-simple-04b-05 | simple | 04B | RDS(1) | violacao = RDS fora da familia 'db.t' em HML |
| compliant-medium-01-01 | noncompliant-medium-01-01 | medium | 01 | EC2(2), RDS(1), S3 | violacao = tag 'Time Responsável' vazia |
| compliant-medium-01-02 | noncompliant-medium-01-02 | medium | 01 | EC2(3), RDS(1), S3 | violacao = tag 'Projeto' vazia |
| compliant-medium-01-03 | noncompliant-medium-01-03 | medium | 01 | EC2(2), RDS(2), S3 | violacao = tag 'Projeto' vazia |
| compliant-medium-01-04 | noncompliant-medium-01-04 | medium | 01 | EC2(3), RDS(2), S3 | violacao = tag 'Projeto' vazia |
| compliant-medium-01-05 | noncompliant-medium-01-05 | medium | 01 | EC2(2), RDS(1), S3 | violacao = tag 'Time Responsável' vazia |
| compliant-medium-02-01 | noncompliant-medium-02-01 | medium | 02 | EC2(2), RDS(1), S3 | violacao = Ambiente invalido ('DEV') |
| compliant-medium-02-02 | noncompliant-medium-02-02 | medium | 02 | EC2(3), RDS(1), S3 | violacao = Ambiente invalido ('STG') |
| compliant-medium-02-03 | noncompliant-medium-02-03 | medium | 02 | EC2(2), RDS(2), S3 | violacao = Ambiente invalido ('QA') |
| compliant-medium-02-04 | noncompliant-medium-02-04 | medium | 02 | EC2(3), RDS(2), S3 | violacao = Ambiente invalido ('producao') |
| compliant-medium-02-05 | noncompliant-medium-02-05 | medium | 02 | EC2(2), RDS(1), S3 | violacao = Ambiente invalido ('homolog') |
| compliant-medium-03-01 | noncompliant-medium-03-01 | medium | 03 | EC2(2), RDS(1), S3 | violacao = regiao (us-west-2) |
| compliant-medium-03-02 | noncompliant-medium-03-02 | medium | 03 | EC2(3), RDS(1), S3 | violacao = regiao (eu-west-1) |
| compliant-medium-03-03 | noncompliant-medium-03-03 | medium | 03 | EC2(2), RDS(2), S3 | violacao = regiao (ap-southeast-1) |
| compliant-medium-03-04 | noncompliant-medium-03-04 | medium | 03 | EC2(3), RDS(2), S3 | violacao = regiao (sa-east-1) |
| compliant-medium-03-05 | noncompliant-medium-03-05 | medium | 03 | EC2(2), RDS(1), S3 | violacao = regiao (eu-central-1) |
| compliant-medium-04a-01 | noncompliant-medium-04a-01 | medium | 04A | EC2(2), RDS(1), S3 | violacao = EC2 fora da familia 't' em HML |
| compliant-medium-04a-02 | noncompliant-medium-04a-02 | medium | 04A | EC2(3), RDS(1), S3 | violacao = EC2 fora da familia 't' em HML |
| compliant-medium-04a-03 | noncompliant-medium-04a-03 | medium | 04A | EC2(2), RDS(2), S3 | violacao = EC2 fora da familia 't' em HML |
| compliant-medium-04a-04 | noncompliant-medium-04a-04 | medium | 04A | EC2(3), RDS(2), S3 | violacao = EC2 fora da familia 't' em HML |
| compliant-medium-04a-05 | noncompliant-medium-04a-05 | medium | 04A | EC2(2), RDS(1), S3 | violacao = EC2 fora da familia 't' em HML |
| compliant-medium-04b-01 | noncompliant-medium-04b-01 | medium | 04B | EC2(2), RDS(1), S3 | violacao = RDS fora da familia 'db.t' em HML |
| compliant-medium-04b-02 | noncompliant-medium-04b-02 | medium | 04B | EC2(3), RDS(1), S3 | violacao = RDS fora da familia 'db.t' em HML |
| compliant-medium-04b-03 | noncompliant-medium-04b-03 | medium | 04B | EC2(2), RDS(2), S3 | violacao = RDS fora da familia 'db.t' em HML |
| compliant-medium-04b-04 | noncompliant-medium-04b-04 | medium | 04B | EC2(3), RDS(2), S3 | violacao = RDS fora da familia 'db.t' em HML |
| compliant-medium-04b-05 | noncompliant-medium-04b-05 | medium | 04B | EC2(2), RDS(1), S3 | violacao = RDS fora da familia 'db.t' em HML |
| compliant-complex-01-01 | noncompliant-complex-01-01 | complex | 01 | EC2(4), RDS(2), S3, ELBv2, EKS | violacao = tag 'Time Responsável' vazia |
| compliant-complex-01-02 | noncompliant-complex-01-02 | complex | 01 | EC2(5), RDS(2), S3, ELBv2, EKS | violacao = tag 'Projeto' vazia |
| compliant-complex-01-03 | noncompliant-complex-01-03 | complex | 01 | EC2(6), RDS(3), S3, ELBv2, EKS | violacao = tag 'Projeto' vazia |
| compliant-complex-01-04 | noncompliant-complex-01-04 | complex | 01 | EC2(7), RDS(3), S3, ELBv2, EKS | violacao = tag 'Projeto' vazia |
| compliant-complex-01-05 | noncompliant-complex-01-05 | complex | 01 | EC2(8), RDS(2), S3, ELBv2, EKS | violacao = tag 'Time Responsável' vazia |
| compliant-complex-02-01 | noncompliant-complex-02-01 | complex | 02 | EC2(4), RDS(2), S3, ELBv2, EKS | violacao = Ambiente invalido ('DEV') |
| compliant-complex-02-02 | noncompliant-complex-02-02 | complex | 02 | EC2(5), RDS(2), S3, ELBv2, EKS | violacao = Ambiente invalido ('STG') |
| compliant-complex-02-03 | noncompliant-complex-02-03 | complex | 02 | EC2(6), RDS(3), S3, ELBv2, EKS | violacao = Ambiente invalido ('QA') |
| compliant-complex-02-04 | noncompliant-complex-02-04 | complex | 02 | EC2(7), RDS(3), S3, ELBv2, EKS | violacao = Ambiente invalido ('producao') |
| compliant-complex-02-05 | noncompliant-complex-02-05 | complex | 02 | EC2(8), RDS(2), S3, ELBv2, EKS | violacao = Ambiente invalido ('homolog') |
| compliant-complex-03-01 | noncompliant-complex-03-01 | complex | 03 | EC2(4), RDS(2), S3, ELBv2, EKS | violacao = regiao (us-west-2) |
| compliant-complex-03-02 | noncompliant-complex-03-02 | complex | 03 | EC2(5), RDS(2), S3, ELBv2, EKS | violacao = regiao (eu-west-1) |
| compliant-complex-03-03 | noncompliant-complex-03-03 | complex | 03 | EC2(6), RDS(3), S3, ELBv2, EKS | violacao = regiao (ap-southeast-1) |
| compliant-complex-03-04 | noncompliant-complex-03-04 | complex | 03 | EC2(7), RDS(3), S3, ELBv2, EKS | violacao = regiao (sa-east-1) |
| compliant-complex-03-05 | noncompliant-complex-03-05 | complex | 03 | EC2(8), RDS(2), S3, ELBv2, EKS | violacao = regiao (eu-central-1) |
| compliant-complex-04a-01 | noncompliant-complex-04a-01 | complex | 04A | EC2(4), RDS(2), S3, ELBv2, EKS | violacao = EC2 fora da familia 't' em HML |
| compliant-complex-04a-02 | noncompliant-complex-04a-02 | complex | 04A | EC2(5), RDS(2), S3, ELBv2, EKS | violacao = EC2 fora da familia 't' em HML |
| compliant-complex-04a-03 | noncompliant-complex-04a-03 | complex | 04A | EC2(6), RDS(3), S3, ELBv2, EKS | violacao = EC2 fora da familia 't' em HML |
| compliant-complex-04a-04 | noncompliant-complex-04a-04 | complex | 04A | EC2(7), RDS(3), S3, ELBv2, EKS | violacao = EC2 fora da familia 't' em HML |
| compliant-complex-04a-05 | noncompliant-complex-04a-05 | complex | 04A | EC2(8), RDS(2), S3, ELBv2, EKS | violacao = EC2 fora da familia 't' em HML |
| compliant-complex-04b-01 | noncompliant-complex-04b-01 | complex | 04B | EC2(4), RDS(2), S3, ELBv2, EKS | violacao = RDS fora da familia 'db.t' em HML |
| compliant-complex-04b-02 | noncompliant-complex-04b-02 | complex | 04B | EC2(5), RDS(2), S3, ELBv2, EKS | violacao = RDS fora da familia 'db.t' em HML |
| compliant-complex-04b-03 | noncompliant-complex-04b-03 | complex | 04B | EC2(6), RDS(3), S3, ELBv2, EKS | violacao = RDS fora da familia 'db.t' em HML |
| compliant-complex-04b-04 | noncompliant-complex-04b-04 | complex | 04B | EC2(7), RDS(3), S3, ELBv2, EKS | violacao = RDS fora da familia 'db.t' em HML |
| compliant-complex-04b-05 | noncompliant-complex-04b-05 | complex | 04B | EC2(8), RDS(2), S3, ELBv2, EKS | violacao = RDS fora da familia 'db.t' em HML |
| compliant-simple-multi-01 | noncompliant-simple-multi-01 | simple | 01+02 | EC2(1) | tag 'Projeto' vazia; Ambiente invalido ('STG') |
| compliant-simple-multi-02 | noncompliant-simple-multi-02 | simple | 01+03 | EC2(1) | tag 'Projeto' vazia; regiao (ap-southeast-1) |
| compliant-simple-multi-03 | noncompliant-simple-multi-03 | simple | 01+04A | EC2(1) | tag 'Projeto' vazia; EC2 fora da familia 't' em HML |
| compliant-simple-multi-04 | noncompliant-simple-multi-04 | simple | 01+04B | RDS(1) | tag 'Projeto' vazia; RDS fora da familia 'db.t' em HML |
| compliant-simple-multi-05 | noncompliant-simple-multi-05 | simple | 02+03 | EC2(1) | Ambiente invalido ('DEV'); regiao (us-west-2) |
| compliant-medium-multi-01 | noncompliant-medium-multi-01 | medium | 03+04A | EC2(2), RDS(1), S3 | regiao (eu-west-1); EC2 fora da familia 't' em HML |
| compliant-medium-multi-02 | noncompliant-medium-multi-02 | medium | 03+04B | EC2(3), RDS(1), S3 | regiao (ap-southeast-1); RDS fora da familia 'db.t' em HML |
| compliant-medium-multi-03 | noncompliant-medium-multi-03 | medium | 04A+04B | EC2(2), RDS(2), S3 | EC2 fora da familia 't' em HML; RDS fora da familia 'db.t' em HML |
| compliant-medium-multi-04 | noncompliant-medium-multi-04 | medium | 01+02+03 | EC2(3), RDS(2), S3 | tag 'Projeto' vazia; Ambiente invalido ('homolog'); regiao (eu-central-1) |
| compliant-medium-multi-05 | noncompliant-medium-multi-05 | medium | 01+03+04A | EC2(2), RDS(1), S3 | tag 'Projeto' vazia; regiao (us-west-2); EC2 fora da familia 't' em HML |
| compliant-complex-multi-01 | noncompliant-complex-multi-01 | complex | 01+03+04B | EC2(4), RDS(2), S3, ELBv2, EKS | tag 'Projeto' vazia; regiao (eu-west-1); RDS fora da familia 'db.t' em HML |
| compliant-complex-multi-02 | noncompliant-complex-multi-02 | complex | 01+04A+04B | EC2(5), RDS(2), S3, ELBv2, EKS | tag 'Projeto' vazia; EC2 fora da familia 't' em HML; RDS fora da familia 'db.t' em HML |
| compliant-complex-multi-03 | noncompliant-complex-multi-03 | complex | 03+04A+04B | EC2(6), RDS(3), S3, ELBv2, EKS | regiao (sa-east-1); EC2 fora da familia 't' em HML; RDS fora da familia 'db.t' em HML |
| compliant-complex-multi-04 | noncompliant-complex-multi-04 | complex | 01+02 | EC2(7), RDS(3), S3, ELBv2, EKS | tag 'Projeto' vazia; Ambiente invalido ('homolog') |
| compliant-complex-multi-05 | noncompliant-complex-multi-05 | complex | 03+04A | EC2(8), RDS(2), S3, ELBv2, EKS | regiao (us-west-2); EC2 fora da familia 't' em HML |
