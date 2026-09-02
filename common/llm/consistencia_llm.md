# Reprodutibilidade e consistência do LLM

`temperature=0` reduz a variabilidade das respostas do modelo, mas não é uma garantia matemática de determinismo — a própria OpenAI documenta que pequenas diferenças de infraestrutura (paralelismo, hardware, etc.) podem produzir respostas diferentes mesmo com `temperature=0` e o mesmo prompt. Já observamos isso empiricamente antes: duas execuções idênticas do mesmo prompt, sobre o mesmo `training_set`, produziram vereditos diferentes para o mesmo caso (`noncompliant-simple-03`/`noncompliant-simple-04`, ver `historico_prompt.md` e a conversa que motivou este documento).

Duas medidas foram tomadas:

## 1. Metadados de reprodutibilidade

`avaliador_llm.py` agora grava, ao final de cada execução, um arquivo `metadata_execucao.json` na pasta de saída, com:

- `modelo_solicitado`: o alias pedido à API (`"gpt-4o"` — não é uma versão fixa, a OpenAI pode reapontá-lo para um snapshot diferente sem aviso).
- `modelos_resolvidos`: a lista de versões de modelo que **de fato** responderam (`response.model` de cada chamada) — esta é a informação confiável para reprodutibilidade, não o alias solicitado. Se essa lista tiver mais de um valor, significa que a OpenAI trocou a versão do modelo no meio da execução.
- `temperatura`, `sdk_openai_versao` (versão da biblioteca `openai` do Python), `prompt_sistema_sha256` (hash do prompt usado, para identificar exatamente qual versão do protocolo gerou aquela rodada — ver `historico_prompt.md`), e o intervalo de tempo (início/fim, UTC) da execução.

Cada arquivo `llm_eval_*.json` individual também grava `_modelo_resolvido` (o modelo que respondeu aquele caso específico).

## 2. Protocolo de repetições

Cada um dos 30 casos do `training_set` é reenviado ao LLM 5 vezes (mesmo prompt, mesmo `temperature=0`), em execuções independentes, e as 5 matrizes de resultado são comparadas por `common/analises/consistencia_repeticoes.py`, que calcula, por regra e no agregado, a proporção de casos em que as 5 respostas foram idênticas ("taxa de consistência"). Ver `common/comandos.txt` para os comandos exatos.

## Resultado

Executadas as 5 repetições completas (30 casos cada, mesmo prompt, `temperature=0`) contra o `training_set`. Todas as 5 execuções foram atendidas pela mesma versão exata do modelo (`gpt-4o-2024-08-06`, capturada via `response.model` em `metadata_execucao.json`), então a variabilidade observada não pode ser atribuída a uma troca de modelo no meio do experimento.

| Regra | Casos avaliados | Consistentes nas 5 repetições | Taxa de consistência |
|---|---|---|---|
| CKV_FINOPS_01 | 30 | 30 | 1,000 |
| CKV_FINOPS_02 | 30 | 29 | 0,967 |
| CKV_FINOPS_03 | 30 | 29 | 0,967 |
| CKV_FINOPS_04A | 30 | 30 | 1,000 |
| CKV_FINOPS_04B | 30 | 30 | 1,000 |
| **TODAS (150 avaliações)** | 150 | 148 | **0,987** |

Apenas 2 dos 150 pares (caso, regra) tiveram alguma divergência entre as 5 repetições:

- `CKV_FINOPS_02` em `noncompliant-simple-04`: `FAILED, FAILED, FAILED, FAILED, PASSED` (4/5 `FAILED`). O gabarito para este caso é `PASSED` — ou seja, a resposta *minoritária* (1 em 5) é a correta, e uma decisão por maioria simples entre as repetições erraria essa regra. Este é o mesmo caso e o mesmo tipo de erro (contaminação entre `CKV_FINOPS_02` e `CKV_FINOPS_04B`) observado antes — a repetição confirma que não é um evento isolado, é uma tendência sistemática do modelo neste caso específico, que na maioria das vezes (4/5) se manifesta.
- `CKV_FINOPS_03` em `compliant-simple-03`: `PASSED, N/A, PASSED, PASSED, PASSED` (4/5 `PASSED`, correto). Aqui a maioria acerta; a única execução divergente respondeu `N/A` em vez do valor resolvido da região — um lapso pontual, não um padrão.

**Interpretação**: a taxa de consistência agregada (98,7%) confirma que `temperature=0` reduz a variabilidade mas não a elimina — 2 em 150 respostas ainda variam entre execuções idênticas. Mais importante: o primeiro caso mostra que consistência e correção são propriedades diferentes — a resposta mais frequente entre as repetições nem sempre é a resposta certa. Isso reforça que "rodar mais vezes e ficar com a maioria" não é, sozinho, uma solução geral para os erros de contaminação entre regras identificados anteriormente; esse tipo de erro tende a se repetir de forma consistente entre execuções, não a se anular por votação.
