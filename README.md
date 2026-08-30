# TCC – Comparativo de Validação de Conformidade FinOps em IaC (LLM vs. Checkov vs. Avaliação Humana)

Este repositório contém o dataset, os scripts e as análises produzidas para o Trabalho de Conclusão de Curso do MBA em Engenharia de Software (USP/Esalq).

## 1. Objetivo

Comparar o desempenho de três abordagens de validação de alterações de infraestrutura via Terraform (IaC) quanto à conformidade com regras de FinOps pré-estabelecidas:

1. **LLM** (GPT-4o, via API da OpenAI)
2. **Ferramenta estática** (Checkov, com regras customizadas)
3. **Avaliadores humanos**

O experimento segue um desenho A/B: para cada cenário de infraestrutura são gerados dois planos Terraform gêmeos — um **conforme** e um **não conforme** — variando apenas uma violação controlada.

## 2. Regras de FinOps avaliadas

| ID Checkov | Regra | Descrição |
|---|---|---|
| `CKV_FINOPS_01` | Tags obrigatórias | `aws_instance`, `aws_db_instance` e `aws_s3_bucket` devem conter as tags `Projeto`, `Time Responsável` e `Ambiente`, todas preenchidas (não vazias). |
| `CKV_FINOPS_02` | Valores válidos de `Ambiente` | A tag `Ambiente` só pode assumir os valores `PRD` ou `HML`. |
| `CKV_FINOPS_03` | Região única | Todo recurso deve ser provisionado exclusivamente em `us-east-1`. |
| `CKV_FINOPS_04A` | Família `t` para EC2 em HML | Se `Ambiente = HML`, instâncias `aws_instance` devem pertencer à família `t`. |
| `CKV_FINOPS_04B` | Família `t` para RDS em HML | Se `Ambiente = HML`, instâncias `aws_db_instance` devem pertencer à família `db.t`. |

Definições formais em `common/checkov/rules/*.yaml`, replicadas em linguagem natural no prompt de sistema em `common/llm/avaliador_llm.py`.

## 3. Estrutura do repositório

O repositório é dividido em três áreas:

```
Dataset/
├── common/          # código e infraestrutura reutilizável (não muda entre datasets)
├── training_set/    # os 30 casos originais (15 pares) - usados para refinar prompt da LLM e regras do Checkov
└── test_set/        # os novos 180 planos (90 pares) - dataset de avaliação real, do qual 15 pares (30 planos) vão para revisão humana
```

**`common/`** — todo o código, infraestrutura como código e scripts de pipeline, independentes de qual conjunto de dados está sendo processado:

- `sadcloud/` — projeto Sadcloud (módulos Terraform AWS parametrizáveis) usado para gerar os planos, mais os scripts de execução (`scripts/run_plans.sh`, `run_specific_plan.sh`, `run_show_all.sh`).
- `checkov/` — as 5 regras de FinOps (`rules/`), o script de execução (`run_checkov_all.sh`) e o extrator (`extrator_checkov.py`).
- `infracost/` — script de execução e extrator de custos.
- `llm/` — `avaliador_llm.py` (chamada à API do GPT-4o), extrator e infraestrutura Docker.
- `revisao_humana/` — os dois scripts que geram e anonimizam o material de revisão humana (`gerar_mapa_ids.py`, `finalizar_planos_publicos.py`) e o gerador do formulário (`gerar_formulario.js`). Ambos os scripts Python recebem o caminho do conjunto (`training_set` ou `test_set`) como argumento.
- `analises/` — os geradores dos apêndices e do gráfico de impacto financeiro.
- `comandos.txt` — todos os comandos de execução do pipeline, com instruções para rodar contra o `training_set` (padrão) ou o `test_set`.

**`training_set/`** e **`test_set/`** — mesma forma interna, contendo apenas **dados** (nenhum script): os planos gerados (`sadcloud/tfvars/`), as saídas brutas de cada ferramenta (`checkov/out/`, `infracost/out/`, `llm/out/`), as análises consolidadas (`analises/`) e o material de revisão humana (`revisao_humana/`).

O `training_set/` contém os 30 casos originais, que serviram para refinar o prompt da LLM e as regras do Checkov antes da coleta de dados real. O `test_set/` está com o esqueleto pronto (pastas vazias, com `.gitkeep`) aguardando a geração dos 180 novos planos (90 pares conforme/não-conforme), dos quais 15 pares (30 planos) serão selecionados para a etapa de revisão humana.

## 4. Pipeline de execução

Ver `common/comandos.txt` para todos os comandos, na ordem: geração dos planos (Sadcloud) → estimativa de custo (Infracost) / análise estática (Checkov) / análise via LLM (podem rodar em paralelo) → revisão humana → geração dos apêndices e dados do TCC. O arquivo já traz a variante de comando para rodar contra o `test_set` em vez do `training_set` (variáveis `TFVARS_DIR` / `OUT_DIR`, ou trocar o caminho passado aos scripts de revisão humana e aos geradores de análise).

## 5. Amostragem do test_set

Ainda a definir (em conversa com o orientador): os critérios de geração dos 90 pares e o critério de seleção dos 15 pares que irão para avaliação humana.
