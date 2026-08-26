# TCC – Comparativo de Validação de Conformidade FinOps em IaC (LLM vs. Checkov vs. Avaliação Humana)

Este repositório contém o dataset, os scripts e as análises produzidas para o Trabalho de Conclusão de Curso do MBA em Engenharia de Software (USP/Esalq).

## 1. Objetivo

Comparar o desempenho de três abordagens de validação de alterações de infraestrutura via Terraform (IaC) quanto à conformidade com regras de FinOps pré-estabelecidas:

1. **LLM** (GPT-4o, via API da OpenAI)
2. **Ferramenta estática** (Checkov, com regras customizadas)
3. **Avaliadores humanos**

O experimento segue um desenho A/B: para cada cenário de infraestrutura são gerados dois planos Terraform gêmeos — um **conforme** e um **não conforme** — variando apenas uma violação controlada, o que permite isolar o efeito da não-conformidade na avaliação de cada método.

## 2. Regras de FinOps avaliadas

| ID Checkov | Regra | Descrição |
|---|---|---|
| `CKV_FINOPS_01` | Tags obrigatórias | `aws_instance`, `aws_db_instance` e `aws_s3_bucket` devem conter as tags `Projeto`, `Time Responsável` e `Ambiente`, todas preenchidas (não vazias). |
| `CKV_FINOPS_02` | Valores válidos de `Ambiente` | A tag `Ambiente` só pode assumir os valores `PRD` ou `HML`. |
| `CKV_FINOPS_03` | Região única | Todo recurso deve ser provisionado exclusivamente em `us-east-1`. |
| `CKV_FINOPS_04A` | Família `t` para EC2 em HML | Se `Ambiente = HML`, instâncias `aws_instance` devem pertencer à família `t` (ex.: `t2.micro`, `t3.medium`). |
| `CKV_FINOPS_04B` | Família `t` para RDS em HML | Se `Ambiente = HML`, instâncias `aws_db_instance` devem pertencer à família `db.t` (ex.: `db.t3.micro`). |

As definições formais dessas regras estão em `checkov/rules/*.yaml` (uma por arquivo) e são replicadas em linguagem natural no prompt de sistema usado pela LLM (`llm/avaliador_llm.py`).

## 3. Dataset (30 amostras)

Os 30 planos são organizados em 15 pares conforme/não-conforme, distribuídos em 3 níveis de complexidade (5 pares cada):

- **Simples**: 1 recurso principal (EC2 ou RDS) além da rede.
- **Médio**: múltiplos recursos (EC2, RDS, S3, ELBv2) com dependências entre módulos.
- **Complexo**: infraestrutura completa (EC2, RDS, S3, ELBv2, EKS) com vários recursos por tipo.

Em cada par, o cenário não conforme mantém a mesma topologia de recursos do conforme, mudando apenas uma violação controlada (região errada, tag ausente/vazia, valor inválido de `Ambiente`, ou família de instância incorreta em HML). O mapeamento completo dos 30 casos (arquivo base, complexidade, regra violada, recursos criados e dependências) está documentado em `analises/amostras.md`.

## 4. Estrutura de pastas

### 4.1 `sadcloud/`

Base para geração dos planos Terraform. O projeto **Sadcloud** (infraestrutura AWS deliberadamente parametrizável via módulos — `network`, `ec2`, `rds`, `s3`, `elb`/`elbv2`, `eks`, entre outros, em `sadcloud/modules/aws`) é usado para gerar os planos via manipulação de arquivos `.tfvars`.

- `sadcloud/tfvars/`: contém os 30 cenários, cada um com três arquivos:
  - `<caso>.tfvars` — variáveis de entrada (região, tags, flags de habilitação de módulos, tipos de instância);
  - `<caso>.plan` — plano binário do Terraform;
  - `<caso>.json` — plano exportado em JSON (`terraform show -json`), que é o artefato consumido pelo Checkov e pela LLM.
  - `run_plans.sh` / `run_specific_plan.sh`: scripts para gerar todos os planos ou um plano específico.

### 4.2 `infracost/`

Estimativa de custo mensal de cada um dos 30 planos gerados em `sadcloud/tfvars`.

- `infracost/out/`: saída bruta do Infracost por caso (`*.infracost.json`).
- `extrator_infracost.py`: consolida as saídas em `analises/matriz_custos_infracost.csv`.

### 4.3 `checkov/`

Análise estática dos 30 planos contra as 5 regras de FinOps.

- `checkov/rules/`: definição de cada regra em YAML (policy DSL nativa do Checkov), uma por arquivo (`mandatory_tags.yaml`, `tag_ambiente_valid_values.yaml`, `valid_region.yaml`, `ec2_hml_valid_types.yaml`, `rds_hml_valid_types.yaml`).
- `checkov/out/`: saída bruta do Checkov por caso (`*.checkov.json`) — inclui não só as 5 regras FinOps customizadas, mas também os checks nativos do Checkov (que não são usados na comparação).
- `extrator_checkov.py`: filtra apenas as 5 regras FinOps na saída bruta e monta a matriz `PASSED/FAILED`/`N/A` por caso, salva em `analises/matriz_resultados_checkov.csv`. O veredito final do caso é `FAILED` se qualquer uma das regras aplicáveis falhar.

### 4.4 `llm/`

Análise dos mesmos 30 planos via LLM (GPT-4o).

- `avaliador_llm.py`: para cada plano, otimiza o JSON bruto (extrai apenas variáveis globais, provider e atributos relevantes dos recursos — tags, `instance_type`, `instance_class` — descartando o restante para economizar tokens), envia para a API da OpenAI (`gpt-4o`, `temperature=0`, `response_format=json_object`) com um prompt de sistema que replica as 5 regras de FinOps em linguagem natural, e recebe de volta um veredito `PASSED`/`FAILED` por regra mais uma justificativa textual.
- `llm/out/`: saída da LLM por caso (`llm_eval_<caso>.json`).
- `extrator_llm.py`: consolida as saídas em `analises/matriz_resultados_llm.csv`.

### 4.5 `analises/`

Compilado final dos resultados, usado para gerar os dados e apêndices do TCC.

- `amostras.md`: mapeamento dos 30 casos (ID, arquivo base, complexidade, regra violada, recursos criados, dependências).
- `matriz_resultados_checkov.csv`, `matriz_resultados_llm.csv`, `matriz_custos_infracost.csv`: matrizes brutas consolidadas de cada fonte.
- `apendice_a_matriz_amostra.csv`: apêndice com a caracterização das amostras + custo mensal (gerado por `gerador_apendice_a.py`).
- `apendice_c_matriz_checkov.csv`: veredito do Checkov traduzido para Aprovado/Falhou (gerado por `gerador_apendice_c.py`).
- `apendice_e_matriz_llm.csv`: idem para a LLM (gerado por `gerador_apendice_e.py`).
- `dados_grafico_impacto_financeiro.csv`: impacto financeiro por par conforme/não-conforme, calculado como `IF = Custo Não Conforme − Custo Conforme` (gerado por `gerador_impacto_financeiro.py`, a partir do apêndice A).

> **Observação**: não há, até o momento, nenhum artefato (script, planilha ou saída) referente à etapa de **avaliação humana** dentro desta estrutura. Essa parte da comparação de três vias (LLM x Checkov x humano) ainda precisa ser incorporada ao dataset/pipeline, ou está sendo conduzida fora desta pasta.

## 5. Pipeline de execução

Todos os comandos abaixo (extraídos e organizados a partir de `comandos.txt`) são executados via Docker, cada um a partir do diretório da respectiva etapa.

### 5.1 Geração dos planos (Sadcloud)

```sh
# gera todos os 30 planos definidos em sadcloud/tfvars
docker compose run --rm --entrypoint sh terraform -c "../tfvars/run_plans.sh"

# gera (ou regenera) um plano específico
docker compose run --rm --entrypoint sh terraform -c "../tfvars/run_specific_plan.sh noncompliant-complex-05.tfvars"
```

### 5.2 Estimativa de custo (Infracost)

```sh
# roda o Infracost sobre todos os planos em sadcloud/tfvars, salvando em infracost/out
docker compose run --rm --entrypoint sh infracost -c "sh /scripts/run_infracost_all.sh"

# consolida infracost/out em analises/matriz_custos_infracost.csv
docker run --rm -v ${PWD}:/app -v ${PWD}/../analises:/analises -w /app python:3.12-slim python extrator_infracost.py
```

### 5.3 Análise estática (Checkov)

```sh
# roda o Checkov (com as regras de checkov/rules) sobre todos os planos, salvando em checkov/out
docker compose run --rm checkov -c "sh /scripts/run_checkov_all.sh"

# filtra as 5 regras FinOps e consolida em analises/matriz_resultados_checkov.csv
docker run --rm -v ${PWD}:/app -v ${PWD}/../analises:/analises -w /app python:3.12-slim python extrator_checkov.py
```

### 5.4 Análise via LLM

```sh
# sobe o container que executa avaliador_llm.py contra todos os planos, salvando em llm/out
docker compose up --build

# consolida llm/out em analises/matriz_resultados_llm.csv
docker run --rm -v ${PWD}:/app -v ${PWD}/../analises:/analises -w /app python:3.12-slim python extrator_llm.py
```

### 5.5 Geração dos apêndices e dados do TCC

```sh
# a partir da pasta analises/
docker run --rm -v ${PWD}:/app -w /app python:3.12-slim python gerador_apendice_a.py
docker run --rm -v ${PWD}:/app -w /app python:3.12-slim python gerador_apendice_c.py
docker run --rm -v ${PWD}:/app -w /app python:3.12-slim python gerador_apendice_e.py
docker run --rm -v ${PWD}:/app -w /app python:3.12-slim python gerador_impacto_financeiro.py
```

**Ordem de execução recomendada**: 5.1 (Sadcloud) → 5.2, 5.3 e 5.4 (podem rodar em paralelo, todos consomem `sadcloud/tfvars`) → 5.5 (depende das matrizes geradas nas etapas anteriores).

## 6. Pontos em aberto

- **Avaliação humana**: ainda não há artefatos desta etapa no repositório (nem script, nem planilha de coleta, nem saída consolidada). Precisa ser definida a forma de coleta (ex.: formulário com os mesmos 30 planos) e o formato de saída para poder alimentar uma matriz equivalente a `matriz_resultados_checkov.csv` / `matriz_resultados_llm.csv`.
