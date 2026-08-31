# TCC – Comparativo de Validação de Conformidade FinOps em IaC (LLM vs. Checkov vs. Avaliação Humana)

Este repositório contém o dataset, os scripts e as análises produzidas para o Trabalho de Conclusão de Curso do MBA em Engenharia de Software (USP/Esalq).

## 1. Objetivo

Comparar o desempenho de três abordagens de validação de alterações de infraestrutura via Terraform (IaC) quanto à conformidade com regras de FinOps pré-estabelecidas:

1. **LLM** (GPT-4o, via API da OpenAI)
2. **Ferramenta estática** (Checkov, com regras customizadas)
3. **Avaliadores humanos**

O experimento segue um desenho A/B: para cada cenário de infraestrutura são gerados dois planos Terraform gêmeos — um **conforme** e um **não conforme** — variando uma ou mais violações controladas.

## 2. Regras de FinOps avaliadas

| ID Checkov | Regra | Descrição |
|---|---|---|
| `CKV_FINOPS_01` | Tags obrigatórias | `aws_instance`, `aws_db_instance` e `aws_s3_bucket` devem conter as tags `Projeto`, `Time Responsável` e `Ambiente`, todas preenchidas (não vazias). |
| `CKV_FINOPS_02` | Valores válidos de `Ambiente` | A tag `Ambiente` só pode assumir os valores `PRD` ou `HML`. |
| `CKV_FINOPS_03` | Região única | Todo recurso deve ser provisionado exclusivamente em `us-east-1`. |
| `CKV_FINOPS_04A` | Família `t` para EC2 em HML | Se `Ambiente = HML`, instâncias `aws_instance` devem pertencer à família `t`. |
| `CKV_FINOPS_04B` | Família `t` para RDS em HML | Se `Ambiente = HML`, instâncias `aws_db_instance` devem pertencer à família `db.t`. |

Definições formais em `common/checkov/rules/*.yaml`, replicadas em linguagem natural no prompt de sistema em `common/llm/avaliador_llm.py`.

## 3. Disciplina dev-set / holdout

O `training_set` (os 30 casos originais) é tratado exclusivamente como **conjunto de desenvolvimento**: foi usado para refinar o prompt da LLM e as regras do Checkov, e portanto **não pode** ser usado para reportar os resultados principais do TCC — esses números devem vir do `test_set`.

O estado do prompt, das regras do Checkov e da lógica de extração usado durante o refino inicial está marcado na tag git `training-set-frozen-v1`. Esse refino continuou depois dessa tag (ajustes na semântica de N/A, correção de uma assimetria de informação entre LLM e Checkov, reforço de minimização de dados no payload da LLM, entre outros — ver `common/analises/` e `common/llm/*.md` para o detalhamento de cada um), sempre sobre o `training_set`, nunca sobre o `test_set`. Esse segundo ciclo de refino está congelado na tag `protocol-frozen-v2`, que é o estado atual do protocolo.

Qualquer alteração de prompt, regra ou lógica de extração feita depois de `protocol-frozen-v2` conta como uma nova versão do protocolo, e um `test_set` só pode ser gerado (e seus resultados só podem ser reportados como principais) depois que essa nova versão também estiver congelada em uma nova tag — nunca ajustar o protocolo observando o desempenho no próprio `test_set`.

## 4. Estrutura do repositório

O repositório é dividido em três áreas:

```
Dataset/
├── common/          # código e infraestrutura reutilizável (não muda entre datasets)
├── training_set/    # os 30 casos originais (15 pares) - conjunto de DESENVOLVIMENTO, não reportar como resultado principal
└── test_set/        # os novos 180 planos (90 pares) - HOLDOUT oficial, fonte dos resultados principais do TCC
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

O `test_set/` está com o esqueleto pronto (pastas vazias, com `.gitkeep`) aguardando a geração dos 180 novos planos (90 pares conforme/não-conforme), dos quais 15 pares (30 planos) serão selecionados para a etapa de revisão humana.

## 5. Pipeline de execução

Ver `common/comandos.txt` para todos os comandos, na ordem: geração dos planos (Sadcloud) → estimativa de custo (Infracost) / análise estática (Checkov) / análise via LLM (podem rodar em paralelo) → revisão humana → geração dos apêndices e dados do TCC. O arquivo já traz a variante de comando para rodar contra o `test_set` em vez do `training_set` (variáveis `TFVARS_DIR` / `OUT_DIR`, ou trocar o caminho passado aos scripts de revisão humana e aos geradores de análise).

## 6. Amostragem do test_set

Definida em resposta ao feedback do orientador sobre os resultados preliminares: aumentar substancialmente o número de casos automatizados frente aos 30 originais e incluir cenários com violações múltiplas simultâneas (o experimento original testava exatamente uma violação por caso, o que é pouco realista). Os 30 planos (15 pares) de avaliação humana são mantidos nesse tamanho por causa do esforço dos especialistas revisores.

**Total: 90 pares (180 planos)**, divididos em:

- **75 pares de violação única** — 5 regras (`CKV_FINOPS_01` a `04B`) × 3 níveis de complexidade (Simples/Médio/Complexo) × 5 repetições cada. Dentro dos 15 pares de `CKV_FINOPS_01` (tags), a violação é rotacionada entre os 3 tipos possíveis (`Projeto` vazio, `Time Responsável` vazio, `Ambiente` vazio/ausente), para preservar a diversidade que já existia nos 30 casos originais.
- **15 pares de violação múltipla** (~17% do total) — 5 por nível de complexidade, cada um combinando 2 a 3 regras violadas simultaneamente, em combinações variadas (não repetidas). O objetivo é testar se cada método consegue sinalizar corretamente **todas** as regras violadas num mesmo caso, e não só acertar o veredito agregado do plano — o que conecta diretamente com a necessidade de ground truth por regra (também levantado pelo orientador).

**Seleção dos 15 pares (30 planos) para a revisão humana**: amostragem estratificada com seed fixa e documentada (mesmo padrão reprodutível já usado em `common/revisao_humana/gerar_mapa_ids.py`) — 5 pares por nível de complexidade, sendo em cada nível 4 pares de violação única (priorizando cobrir o maior número possível de regras distintas) e 1 par de violação múltipla. Isso mantém, na amostra que os humanos avaliam, uma proporção de casos multi-violação (~20%) próxima da proporção no conjunto completo (~17%).

A tabela de mapeamento completa (arquivo, regras violadas, complexidade) será gerada junto com os planos, no mesmo formato de `training_set/analises/amostras.md`. O ID público entregue aos revisores continua embaralhado e sem qualquer relação com conformidade, exatamente como no fluxo já existente para o `training_set`.

Geração ainda pendente de execução — nenhum plano do `test_set` foi criado até o momento. Quando for gerado, deve respeitar a tag `protocol-frozen-v2` (nenhum ajuste de prompt/regras a partir da observação dos resultados deste conjunto).
