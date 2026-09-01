# TCC – Comparativo de Validação de Conformidade FinOps em IaC (LLM vs. Checkov vs. Avaliação Humana)

Este repositório contém o dataset, os scripts e as análises produzidas para o Trabalho de Conclusão de Curso do MBA em Engenharia de Software (USP/Esalq). O texto final do TCC cita este repositório no Apêndice A, fixando a tag `protocol-frozen-v2` como a versão que gerou os resultados reportados.

## 1. Objetivo

Comparar o desempenho de três abordagens de validação de alterações de infraestrutura via Terraform (IaC) quanto à conformidade com regras de FinOps pré-estabelecidas:

1. **LLM** (GPT-4o, via API da OpenAI)
2. **Ferramenta estática** (Checkov, com regras customizadas)
3. **Avaliadores humanos** (3 especialistas, identificados apenas como R1/R2/R3 — ver seção 7)

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

O `training_set` (os 30 casos originais) é tratado exclusivamente como **conjunto de desenvolvimento**: foi usado para refinar o prompt da LLM e as regras do Checkov, e portanto **não é usado** para reportar os resultados principais do TCC — esses números vêm do `test_set`.

O estado do prompt, das regras do Checkov e da lógica de extração usado durante o refino inicial está marcado na tag git `training-set-frozen-v1`. Esse refino continuou depois dessa tag (ajustes na semântica de N/A, correção de uma assimetria de informação entre LLM e Checkov, reforço de minimização de dados no payload da LLM, entre outros — ver `common/analises/` e `common/llm/*.md` para o detalhamento de cada um), sempre sobre o `training_set`, nunca sobre o `test_set`. Esse segundo ciclo de refino está congelado na tag **`protocol-frozen-v2`**, que é o estado do protocolo usado para gerar todos os resultados do `test_set` reportados no TCC.

Qualquer alteração de prompt, regra ou lógica de extração feita depois de `protocol-frozen-v2` conta como uma nova versão do protocolo, e só pode ser aplicada a um novo `test_set` (ou reportada como resultado principal) depois de também estar congelada em uma nova tag — nunca ajustar o protocolo observando o desempenho no próprio `test_set`.

## 4. Estrutura do repositório

```
Dataset/
├── common/          # código e infraestrutura reutilizável (não muda entre datasets)
├── training_set/    # os 30 casos originais (15 pares) - conjunto de DESENVOLVIMENTO
└── test_set/        # os 180 planos (90 pares) - HOLDOUT oficial, fonte dos resultados principais do TCC
```

**`common/`** — todo o código, infraestrutura como código e scripts de pipeline, independentes de qual conjunto de dados está sendo processado:

- `sadcloud/` — projeto Sadcloud (módulos Terraform AWS parametrizáveis) usado para gerar os planos, mais os scripts de execução (`scripts/run_plans.sh`, `run_specific_plan.sh`, `run_show_all.sh` — este último gera a renderização legível `terraform show`, usada como material da revisão humana).
- `checkov/` — as 5 regras de FinOps (`rules/`), o script de execução (`run_checkov_all.sh`) e o extrator (`extrator_checkov.py`).
- `infracost/` — script de execução e extrator de custos.
- `llm/` — `avaliador_llm.py` (chamada à API do GPT-4o, com suporte a retomada — pula planos já avaliados em execuções anteriores), extrator e infraestrutura Docker.
- `revisao_humana/` — `gerar_mapa_ids.py` (gera, para cada avaliador em `REVISORES = ["R1", "R2", "R3"]`, um embaralhamento independente dos casos), `finalizar_planos_publicos.py` (monta os pacotes anonimizados por avaliador, com checagem automática contra vazamento de rótulo) e `gerar_formulario.js` (gera o formulário `.docx` de coleta). Os dois scripts Python recebem o caminho do conjunto (`training_set` ou `test_set`) como argumento.
- `analises/` — `gerar_ground_truth.py` (gabarito independente por regra, calculado direto do plano JSON bruto), `metricas_por_regra.py` (Precision/Recall/F1/Acurácia por regra e agregado, para cada avaliador disponível), `testes_estatisticos.py` (Teste de McNemar exato e intervalos de confiança por bootstrap), além dos geradores dos apêndices e do gráfico de impacto financeiro.
- `comandos.txt` — todos os comandos de execução do pipeline (Docker), com a variante para rodar contra o `training_set` (padrão) ou o `test_set`.

**`training_set/`** e **`test_set/`** — mesma forma interna, contendo apenas **dados** (nenhum script): os planos gerados (`sadcloud/tfvars/`), as saídas brutas de cada ferramenta (`checkov/out/`, `infracost/out/`, `llm/out/`), as análises consolidadas (`analises/`) e, no `test_set`, o material de revisão humana (`revisao_humana/`).

Dentro de `revisao_humana/`, a separação entre `privada/` e `publica/` é a barreira de cegamento do experimento:

- `privada/revisores/<código>/mapa_ids.csv` — gabarito de cada avaliador (mapeia `plano_NN` de volta ao caso real e à conformidade). **Nunca vai para o git** (protegido em `.gitignore`) — existe só localmente, fora deste repositório.
- `publica/<código>/planos/plano_01.txt` … `plano_30.txt` — os planos que de fato são enviados ao avaliador, renomeados e sem qualquer referência a arquivo original ou status de conformidade (checado automaticamente por `finalizar_planos_publicos.py` antes de liberar o pacote). Essa parte **é versionada**.

## 5. Pipeline de execução

Ver `common/comandos.txt` para todos os comandos, na ordem: geração dos planos (Sadcloud) → estimativa de custo (Infracost) / análise estática (Checkov) / análise via LLM (podem rodar em paralelo) → revisão humana → geração dos apêndices, métricas e testes estatísticos. O arquivo traz a variante de comando para rodar contra o `test_set` em vez do `training_set`.

## 6. Amostragem do test_set

Definida em resposta ao feedback do orientador sobre os resultados preliminares: aumentar substancialmente o número de casos automatizados frente aos 30 originais e incluir cenários com violações múltiplas simultâneas (o experimento original testava exatamente uma violação por caso, o que é pouco realista). Os 30 planos (15 pares) de avaliação humana são mantidos nesse tamanho por causa do esforço dos especialistas revisores.

**Total: 90 pares (180 planos)**, divididos em:

- **75 pares de violação única** — 5 regras (`CKV_FINOPS_01` a `04B`) × 3 níveis de complexidade (Simples/Médio/Complexo) × 5 repetições cada.
- **15 pares de violação múltipla** (~17% do total) — 5 por nível de complexidade, cada um combinando 2 a 3 regras violadas simultaneamente.

**Seleção dos 15 pares (30 planos) para a revisão humana**: amostragem estratificada com seed fixa e documentada — 5 pares por nível de complexidade (4 de violação única + 1 de violação múltipla cada), mapeada em `test_set/analises/selecao_revisao_humana.md`.

## 7. Avaliação humana

Três avaliadores especialistas revisam, de forma cega e independente, os mesmos 30 planos selecionados na seção 6. Cada avaliador recebe:

- Uma ordem própria e embaralhada dos 30 planos (`plano_01.txt` a `plano_30.txt`), com seed independente por avaliador (`SEED_BASE + índice`) — os planos são o **mesmo conteúdo** para os três, só a numeração/ordem muda, para reduzir efeito de aprendizado/fadiga e impedir comparação de anotações por número de plano entre avaliadores.
- Um formulário `.docx` idêntico (`common/revisao_humana/Formulario_Revisao_FinOps.docx`), pedindo, por plano, o veredito (Aprovado/Falhou/N/A) de cada uma das 5 regras, mais observações e tempo de análise, além de experiência profissional do avaliador (anos em TI, anos com AWS/Terraform, certificações).

Cada avaliador é identificado, em qualquer artefato deste repositório, apenas pelo código anônimo **R1**, **R2** ou **R3** — nomes reais nunca são versionados (ficam só em `revisao_humana/privada/mapa_revisores.csv`, fora do git).

**Status atual**: pacotes gerados e entregues aos 3 avaliadores; aguardando devolução dos formulários preenchidos. Quando retornarem, o próximo passo é um extrator que cruza cada formulário com o `mapa_ids.csv` do respectivo avaliador para produzir `test_set/analises/matriz_resultados_humanos.csv` (ainda não existe), habilitando o cálculo de concordância entre avaliadores (ex.: Kappa de Fleiss) e a comparação de 3 vias completa (Cochran's Q).

## 8. Análises estatísticas

Sobre o `test_set`, já calculados (Checkov e LLM; a parte que envolve os 3 avaliadores humanos depende da seção 7):

- `analises/metricas_por_regra.csv` — Precision, Recall, F1 e Acurácia por regra e agregado, classe positiva = não conformidade (`FAILED`).
- `analises/discrepancias_por_regra.csv` — todo caso em que um avaliador divergiu do gabarito, individualmente listado.
- `analises/mcnemar_checkov_vs_llm.csv` — Teste de McNemar exato (binomial de sinal), por regra e agregado, comparando Checkov e LLM sobre a mesma população de casos.
- `analises/intervalos_confianca.csv` — IC 95% (bootstrap percentil, 10.000 reamostragens, seed documentada) para as 4 métricas acima, por avaliador/regra/agregado.

Pendente (depende da avaliação humana, seção 7): Cochran's Q entre os 3 métodos e medida de concordância entre os 3 avaliadores humanos.

## 9. Manutenção deste README

**Este README deve ser atualizado sempre que o repositório receber uma etapa relevante do trabalho** — geração de um novo conjunto de dados, execução de um avaliador (Checkov/LLM/humano) sobre um conjunto, novo script ou nova análise em `common/analises/`, mudança na disciplina dev-set/holdout, nova tag de protocolo, ou qualquer decisão de desenho que mude o que está descrito aqui. O objetivo é que quem abrir o repositório (incluindo o orientador, via o link citado no Apêndice A do TCC) encontre sempre uma descrição fiel do estado atual, sem depender do histórico de commits para reconstruir o que já foi feito.
