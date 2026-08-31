# Unidade de análise: quais recursos cada avaliador de fato avalia

Este documento investiga se Checkov e LLM avaliam exatamente o mesmo conjunto de recursos dentro de um plano Terraform — em particular, se ambos tratam da mesma forma recursos que não estão sendo efetivamente criados/alterados (`actions: ["delete"]` ou `actions: ["no-op"]`), unidade de análise já filtrada explicitamente do lado do LLM.

## O filtro já existente do lado do LLM

`otimizar_plano_terraform()` (`common/llm/avaliador_llm.py`) descarta explicitamente qualquer `resource_change` cujo `change.actions` seja exatamente `["delete"]` ou `["no-op"]` antes de montar o payload enviado à API:

```python
for res in dados.get("resource_changes", []):
    acoes = res.get("change", {}).get("actions", [])
    if acoes == ["delete"] or acoes == ["no-op"]:
        continue
    ...
```

A pergunta era: o Checkov, ao escanear o mesmo plano JSON completo, aplica o mesmo critério — ou avalia recursos que o LLM já descarta?

## Investigação empírica

Como o Checkov não expõe essa lógica em documentação de forma direta, o comportamento foi testado de forma controlada, com o plano real `noncompliant-simple-01.json` (que viola `CKV_FINOPS_03` — região `us-west-2` em vez de `us-east-1`) como base, gerando variantes sintéticas de um único recurso (`module.ec2.aws_instance.main[0]`):

| Teste | O que foi alterado | Resultado (`CKV_FINOPS_03`) |
|---|---|---|
| `teste_create_original` | Nenhuma alteração (controle) — `actions: ["create"]` | FAILED |
| `teste_noop` | `actions` → `["no-op"]`, `before` = `after` (recurso "já existente", sem mudança) | FAILED (idêntico ao controle) |
| `teste_delete` | `actions` → `["delete"]`, `after` → `null` | FAILED (idêntico ao controle) |
| `teste_divergencia_pv_rc` | `planned_values` do recurso alterado para `região = us-east-1` (compliant), mantendo `resource_changes[].change.after.region = us-west-2` (não compliant) intocado | **PASSED** |

Os três primeiros testes deram resultado idêntico entre si — o que já era um indício de que o Checkov não está lendo o campo `resource_changes[].change.actions`/`.after` que foi alterado em cada variante. O quarto teste é decisivo: ao divergir deliberadamente `planned_values` (compliant) de `resource_changes[].change.after` (não compliant) para o mesmo recurso, o veredito do Checkov seguiu `planned_values`, não `resource_changes`.

**Conclusão da investigação**: o scanner `terraform_plan` do Checkov avalia os recursos a partir do bloco `planned_values` do plano JSON (o estado final planejado), não a partir de `resource_changes[].change.after` (o *delta* da mudança) — que é exatamente o campo que `otimizar_plano_terraform()` lê para montar o payload do LLM. Os dois avaliadores, portanto, leem fontes diferentes dentro do mesmo plano JSON.

## Por que isso poderia divergir em tese

`planned_values` reflete o estado que existirá **depois** de aplicado o plano:

- Um recurso com `actions: ["delete"]` deixa de existir depois do apply — portanto, na prática, o Terraform não o inclui em `planned_values`. Nesse caso as duas fontes concordam por omissão: nenhum avaliador o vê.
- Um recurso com `actions: ["no-op"]` continua existindo, inalterado — portanto, o Terraform o mantém em `planned_values`. Nesse caso as fontes **divergiriam**: o Checkov continuaria avaliando esse recurso (via `planned_values`), enquanto o LLM o descarta explicitamente (via o filtro em `otimizar_plano_terraform()`).

Ou seja, em tese, um cenário com recursos `no-op` não conformes seria sinalizado pelo Checkov e ignorado pela LLM — uma divergência real de unidade de análise.

## Por que isso não afeta este dataset (nem afetará o `test_set`)

Nenhum plano gerado por este pipeline pode conter `actions: ["no-op"]` ou `["delete"]`, por construção: `run_plans.sh` e `run_specific_plan.sh` (`common/sadcloud/scripts/`) executam `terraform init` seguido de `terraform plan -var-file=... -out=...` — **nunca `terraform apply`** — sempre a partir de um diretório de trabalho sem estado (`.tfstate`) prévio. Sem `apply`, o estado nunca é persistido entre execuções, então todo `terraform plan` roda contra um estado vazio, e todo recurso gerenciado só pode aparecer com `actions: ["create"]` (data sources aparecem como `["read"]`, irrelevantes para as 5 regras de FinOps).

Essa não é apenas uma observação sobre os dados atuais — é uma garantia estrutural do pipeline, confirmada empiricamente na varredura completa do `training_set`: das 386 entradas em `resource_changes` nos 30 planos, 370 são `["create"]` e 16 são `["read"]` (`aws_iam_policy_document`, um data source); nenhuma é `["no-op"]` ou `["delete"]`. Como o `test_set` será gerado pelos mesmos scripts, essa garantia se estende a ele.

Para `actions: ["create"]`, o Terraform sempre preenche `planned_values` e `resource_changes[].change.after` com os mesmos valores (as duas estruturas descrevem o mesmo estado final planejado, só que em formatos diferentes) — por isso, apesar de Checkov e LLM lerem campos estruturalmente diferentes do plano JSON, os valores lidos são sempre idênticos neste dataset, e os 30/30 resultados consistentes entre os dois métodos ao longo do trabalho confirmam isso na prática.

## Conclusão

A unidade de análise dos dois avaliadores está alinhada neste estudo — não porque leem o mesmo campo do plano JSON (não leem: Checkov lê `planned_values`, a LLM lê `resource_changes[].change.after`), mas porque o desenho do pipeline de geração de planos (sempre `plan` contra estado vazio, nunca `apply`) garante que as duas fontes sejam sempre idênticas para os únicos tipos de `actions` que podem ocorrer (`create`/`read`). O filtro de `delete`/`no-op` em `otimizar_plano_terraform()` é código defensivo correto, mas nunca é de fato exercitado neste dataset nem será no `test_set`, dado o método de geração dos planos.

Nenhuma alteração de código foi necessária. Fica registrado como limitação/observação metodológica: a equivalência entre as duas fontes é garantida pelo desenho experimental (plans sempre gerados do zero), não por uma equivalência genérica entre `planned_values` e `resource_changes` do Terraform — um pipeline que reutilizasse estado (ex.: `apply` incremental) exigiria revisitar esta análise.
