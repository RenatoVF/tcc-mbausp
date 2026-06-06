# Mapeamento dos 30 casos

| ID | Arquivo Base | Complexidade | Regra Violada | Recursos Criados | Dependências |
|---:|---|---|---|---|---|
| C001 | compliant-simple-01 | Simples | Nenhuma | Network, EC2(1) | `network` -> `ec2` (subnet) |
| NC001 | noncompliant-simple-01 | Simples | Região diferente | Network, EC2(1) | `network` -> `ec2` |
| C002 | compliant-simple-02 | Simples | Nenhuma | Network, RDS(1) | `network` -> `rds` (db subnet group) |
| NC002 | noncompliant-simple-02 | Simples | Tag `Time Responsável` vazia | Network, RDS(1) | `network` -> `rds` |
| C003 | compliant-simple-03 | Simples | Nenhuma | Network, EC2(1) (HML, t-family) | `network` -> `ec2` |
| NC003 | noncompliant-simple-03 | Simples | Valor da Tag `Ambiente` inválido | Network, EC2(1) | `network` -> `ec2` |
| C004 | compliant-simple-04 | Simples | Nenhuma | Network, RDS(1) (HML, db.t) | `network` -> `rds` |
| NC004 | noncompliant-simple-04 | Simples | RDS fora da família `db.t` | Network, RDS(1) | `network` -> `rds` |
| C005 | compliant-simple-05 | Simples | Nenhuma | Network, EC2(1) | `network` -> `ec2` |
| NC005 | noncompliant-simple-05 | Simples | Tag `Projeto` vazia | Network, EC2(1) | `network` -> `ec2` |
| C006 | compliant-medium-01 | Médio | Nenhuma | Network, EC2(2), RDS(1), S3 | `network` -> `ec2`,`rds`; `s3` é independente |
| NC006 | noncompliant-medium-01 | Médio | Região diferente | Network, EC2(2), RDS(1), S3 | mesmas dependências |
| C007 | compliant-medium-02 | Médio | Nenhuma | Network, EC2(2) (HML t-family), RDS(1) | mesmas dependências |
| NC007 | noncompliant-medium-02 | Médio | EC2 fora da família `t` (HML) | Network, EC2(2), RDS(1) | mesmas dependências |
| C008 | compliant-medium-03 | Médio | Nenhuma | Network, EC2(3), RDS(1), S3 | mesmas dependências |
| NC008 | noncompliant-medium-03 | Médio | Tag `Ambiente` vazia | Network, EC2(3), RDS(1), S3 | mesmas dependências |
| C009 | compliant-medium-04 | Médio | Nenhuma | Network, EC2(2), RDS(2), S3 | mesmas dependências |
| NC009 | noncompliant-medium-04 | Médio | Valor da Tag `Ambiente` inválido | Network, EC2(2), RDS(2), S3 | mesmas dependências |
| C010 | compliant-medium-05 | Médio | Nenhuma | Network, EC2(2), RDS(1), ELBv2 | `elbv2` depende de subnets |
| NC010 | noncompliant-medium-05 | Médio | Tag `Time Responsável` vazia | Network, EC2(2), RDS(1), ELBv2 | mesmas dependências |
| C011 | compliant-complex-01 | Complexo | Nenhuma | Network, EC2(4), RDS(2), S3, ELBv2, EKS | Vários módulos com dependências em `network` |
| NC011 | noncompliant-complex-01 | Complexo | Região diferente | Network, EC2(4), RDS(2), S3, ELBv2, EKS | mesmas dependências |
| C012 | compliant-complex-02 | Complexo | Nenhuma | Network, EC2(5 HML t), RDS(2), S3, ELBv2, EKS | mesmas dependências |
| NC012 | noncompliant-complex-02 | Complexo | EC2 fora da família `t` (HML) | Network, EC2(5 HML t), RDS(2), S3, ELBv2, EKS | mesmas dependências |
| C013 | compliant-complex-03 | Complexo | Nenhuma | Network, EC2(6), RDS(3), S3, ELBv2, EKS | mesmas dependências |
| NC013 | noncompliant-complex-03 | Complexo | Tag `Projeto` vazia | Network, EC2(6), RDS(3), S3, ELBv2, EKS | mesmas dependências |
| C014 | compliant-complex-04 | Complexo | Nenhuma | Network, EC2(8 HML t), RDS(2), S3, ELBv2, EKS | mesmas dependências |
| NC014 | noncompliant-complex-04 | Complexo |  Valor da Tag `Ambiente` inválido | mesmos recursos | mesmas dependências |
| C015 | compliant-complex-05 | Complexo | Nenhuma | Network, EC2(10), RDS(3), S3, ELBv2, EKS | mesmas dependências |
| NC015 | noncompliant-complex-05 | Complexo | RDS fora da família `db.t` | mesmos recursos | mesmas dependências |

> Observação: cada par (Cxxx / NCxxx) mantém os mesmos módulos ativados e contagem de recursos; a diferença é apenas a violação controlada listada na coluna "Regra Violada".
