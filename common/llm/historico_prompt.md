# Histórico de versões do prompt do LLM — semântica de N/A por regra

Este documento registra, de forma objetiva e com evidências, as iterações feitas no `prompt_sistema` de `avaliador_llm.py` durante o refinamento do protocolo posterior ao congelamento `training-set-frozen-v1`. O objetivo é servir de material de apoio para a seção de metodologia/limitações do TCC, especificamente sobre a dificuldade de fazer um LLM seguir de forma confiável uma semântica de "não aplicável" (N/A) em regras condicionais, mesmo com instruções explícitas e reforçadas.

Todas as execuções abaixo foram feitas exclusivamente contra o `training_set` (conjunto de desenvolvimento, 30 casos), nunca contra o `test_set` — nenhuma dessas iterações compromete a disciplina de holdout, já que o `test_set` segue sem nenhum plano gerado.

## Contexto

O prompt original (estado congelado em `training-set-frozen-v1`) só permitia que o LLM respondesse `PASSED` ou `FAILED` por regra, nunca `N/A`. Isso tornava a comparação por regra com o Checkov e com o formulário humano desigual, já que ambos usam `N/A` para indicar que uma regra não se aplica a um determinado plano (por exemplo, `CKV_FINOPS_04A` não se aplica a um plano sem nenhum recurso `aws_instance`). Uma análise por regra desse prompt original mostrou o LLM evitando `N/A` mesmo em casos claramente inaplicáveis (10 de 30 avaliações aplicáveis a `04A`/`04B` no `training_set`), respondendo `PASSED` no lugar.

## Versão 2 — introdução do N/A

Adicionada a opção `N/A` a todas as 5 regras, com o critério de aplicabilidade definido por regra (mesma lógica usada no gabarito independente de `gerar_ground_truth.py`): `N/A` quando o plano não contém nenhum recurso do(s) tipo(s) coberto(s) pela regra.

**Resultado**: `CKV_FINOPS_01`, `02` e `03` passaram a ter Precision/Recall/F1/Accuracy = 1,000 nos casos aplicáveis. Porém `CKV_FINOPS_04A` e `04B` apresentaram um número alto de divergências de aplicabilidade — 17 e 14 casos, respectivamente, em 30 — todas no mesmo padrão: o gabarito diz `PASSED` (existe o recurso, mas com `Ambiente` diferente de `HML`, logo a regra se aplica e não é violada) e o LLM responde `N/A`.

**Evidência** (caso `compliant-simple-01`, plano com um `aws_instance` com `Ambiente = PRD`):

> "CKV_FINOPS_04A é não aplicável pois não há instâncias em 'HML'."

Ou seja, o modelo interpretou "aplicável" como "a condição da regra (`Ambiente = HML`) foi satisfeita", e não como "existe o tipo de recurso ao qual a regra se refere" — que é a semântica adotada no gabarito, no Checkov e no formulário humano.

## Versão 3 — reforço explícito em prosa

Reescrita da descrição das regras `04A`/`04B` separando explicitamente "critério de aplicabilidade" de "critério de violação", com a frase adicional: *"Ambiente diferente de HML NUNCA é motivo para retornar N/A, é motivo para retornar PASSED"*.

**Resultado**: praticamente nenhuma mudança (16 e 11 divergências, respectivamente, ante 17 e 14). A justificativa retornada pelo LLM para o mesmo caso (`compliant-simple-01`) foi **idêntica, palavra por palavra**, à da versão anterior — o reforço textual não alterou o comportamento do modelo.

**Achado metodológico**: reforçar uma instrução em prosa, mesmo de forma explícita, repetida e com a proibição direta do comportamento indesejado, não foi suficiente para alterar a interpretação do modelo sobre a aplicabilidade de uma regra condicional. Isso é evidência relevante para a discussão sobre os limites de controle comportamental de LLMs via prompt engineering, complementar à limitação de que `temperature=0` não garante determinismo: aqui o problema não é variabilidade entre execuções, e sim uma interpretação sistemática e estável, porém incorreta em relação à semântica desejada.

## Observações adicionais coletadas no processo

- Em pelo menos um caso (`noncompliant-simple-01`, versão 3), o campo `justificativa` foi retornado como um objeto JSON aninhado (um dicionário por regra) em vez de uma string simples, mesmo com o mesmo prompt e schema (`response_format: json_object`) usados em todos os outros casos — indício adicional de inconsistência estrutural na saída do modelo.
- O número de falsos positivos em `CKV_FINOPS_01` variou entre execuções (3 casos na versão inicial do prompt, caindo para 1 caso nas versões 2 e 3), sem que a descrição dessa regra específica tivesse sido alterada — comportamento consistente com não-determinismo residual mesmo em `temperature=0`, a ser investigado formalmente com um protocolo de repetições.

## Versão 4 — procedimento numerado (em avaliação)

Reescrita de `04A`/`04B` como um procedimento sequencial numerado (passo 1: checar existência do tipo de recurso → N/A se ausente; passo 2: checar violação apenas entre os recursos existentes; passo 3: `PASSED` em qualquer outro caso, incluindo `Ambiente` diferente de `HML`), no lugar de uma descrição em prosa. A hipótese é que uma instrução estruturada como algoritmo passo a passo reduza a ambiguidade que persistiu nas versões 2 e 3.

**Resultado**: o problema de aplicabilidade foi totalmente resolvido — zero divergências de N/A em qualquer regra, nas 30 avaliações do `training_set` (ante 17/14 na versão 2 e 16/11 na versão 3). A hipótese se confirmou: framing como procedimento sequencial numerado eliminou a ambiguidade que persistia com reforço em prosa.

Restam apenas 3 discrepâncias no total (nenhuma delas ligada a N/A), todas do tipo falso positivo/negativo comum:

- `CKV_FINOPS_01` em `noncompliant-simple-03` (falso positivo): o LLM marca `01` como `FAILED` citando a tag `Ambiente = 'DEV'`, mas essa é uma violação de `CKV_FINOPS_02` (valor inválido), não de `CKV_FINOPS_01` (existência/preenchimento da tag) — a tag existe e não está vazia, então `01` deveria ser `PASSED`. Este é o mesmo padrão de erro observado anteriormente (contaminação entre regras que compartilham a mesma tag), reproduzido de forma estável nas versões 2, 3 e 4 para este caso específico.
- `CKV_FINOPS_02` em `noncompliant-simple-04` (falso positivo) e `CKV_FINOPS_04B` no mesmo caso (falso negativo): o LLM atribui a violação real de `04B` (um `aws_db_instance` em `HML` com `instance_class = 'db.m5.large'`, fora da família `db.t`) à regra `02`, e então conclui — de forma factualmente incorreta, pela própria justificativa retornada — que `04B` está `PASSED`. Novamente, contaminação entre regras adjacentes (aqui, entre a regra de valores válidos de `Ambiente` e a regra condicional de família de instância).

Esses três casos residuais não são causados pela mudança de prompt deste documento — são o mesmo tipo de erro de atribuição entre regras adjacentes que motivou originalmente a criação do gabarito independente por regra (ver metodologia de ground truth). Ficam registrados aqui como achado residual, não tratado neste ponto do protocolo.

## Versão 5 — procedimento numerado também em CKV_FINOPS_01/02 + cláusulas de exclusividade

Aplicando a mesma técnica que resolveu o problema de N/A em `04A`/`04B`, `CKV_FINOPS_01` e `CKV_FINOPS_02` foram reescritas como procedimentos numerados, cada uma explicitando que avalia *apenas* seu próprio critério (existência/preenchimento da tag, no caso de `01`; validade do valor, no caso de `02`). Também foram adicionadas cláusulas de exclusividade cruzada em `02`, `04A` e `04B` ("esta violação é exclusiva desta regra, nunca marque a regra X como FAILED por causa dela"), e um parágrafo geral de "independência das regras" com os dois exemplos observados nas versões anteriores.

**Resultado**: de 3 discrepâncias (versão 4) para **1 única discrepância** em 150 avaliações (30 casos × 5 regras). A contaminação entre `CKV_FINOPS_02` e `CKV_FINOPS_04B` (caso `noncompliant-simple-04`) foi totalmente corrigida — ambas as regras passaram a acertar. Métricas agregadas (micro-média): TP=16, FP=1, FN=0, TN=123, Precision=0,941, Recall=1,000, F1=0,970, Accuracy=0,993.

A única discrepância remanescente é, novamente, `CKV_FINOPS_01` no caso `noncompliant-simple-03` — o mesmo caso que já falhava desde a versão 2. A justificativa retornada pelo LLM nesta versão é ainda mais explícita sobre a causa do erro:

> "CKV_FINOPS_01: O recurso 'aws_instance' não possui a tag 'Ambiente' com um valor permitido ('PRD' ou 'HML')."

Note que essa frase é literalmente a definição de `CKV_FINOPS_02`, usada como justificativa para a falha de `CKV_FINOPS_01` — isso apesar do prompt conter, para este caso específico: (a) um procedimento numerado que restringe `01` a checar somente existência/não-vacuidade da tag; (b) uma frase explícita dizendo que um valor como 'DEV' "CONTA como presente e preenchida" para `01`; (c) uma cláusula de exclusividade em `02` dizendo para nunca marcar `01` como FAILED por causa de valor inválido; e (d) um parágrafo geral final citando exatamente este cenário ('Ambiente' inválido) como exemplo do que não fazer.

**Achado metodológico**: este caso específico se mostrou resistente a quatro tentativas sucessivas de correção via engenharia de prompt, cada uma mais explícita e redundante que a anterior. Isso é uma evidência forte — mais forte que os achados das versões 2 e 3 — de um limite genuíno da abordagem de "corrigir via mais instrução": há pelo menos um padrão de entrada (tag 'Ambiente' com valor semanticamente inválido) que o modelo consistentemente associa à noção geral de "tags mal configuradas" o suficiente para vazar entre regras adjacentes, independentemente de quão explícitas sejam as instruções em contrário. Dado o ganho já obtido (de 32 para 1 discrepância em 150 avaliações) e o custo de cada nova rodada de validação (chamadas de API pagas), esta é uma boa parada para a iteração de prompt sobre este ponto específico — o caso fica registrado como limitação documentada, não como algo a perseguir indefinidamente com mais ajustes de texto.
