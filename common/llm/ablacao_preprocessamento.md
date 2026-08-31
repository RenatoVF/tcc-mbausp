# Estudo de ablação — pré-processamento do LLM

Testa isoladamente se o bloco `variaveis_globais` do payload enviado ao LLM (ver `arquitetura_avaliadores.md`) é decisivo para sua acurácia em `CKV_FINOPS_03`, a única das 5 regras que depende da resolução de uma variável (`var.aws_region`).

## Desenho do experimento

Duas execuções do mesmo `avaliador_llm.py`, com o mesmo `prompt_sistema`, contra os mesmos 30 casos do `training_set`, variando apenas a variável de ambiente `PREPROCESSAMENTO`:

- **`completo`** (padrão/atual): o payload inclui `variaveis_globais` com os valores reais de todas as variáveis do plano — é a versão já avaliada em todas as versões anteriores deste protocolo.
- **`sem_variaveis`**: o payload envia `variaveis_globais` como um dicionário vazio. Quando a região do provider é uma referência de variável, o LLM não tem como resolvê-la — só recebe a referência não resolvida em `provedores`.

Nada mais muda entre as duas execuções (mesmo prompt, mesmas regras, mesmo filtro de `resource_changes`).

## Como reproduzir

```
# a partir de common/llm
OUT_DIR=../../training_set/llm/out_sem_preprocessamento PREPROCESSAMENTO=sem_variaveis docker compose up --build
docker run --rm -v ${PWD}:/app -v ${PWD}/../../training_set/llm/out_sem_preprocessamento:/app/out -v ${PWD}/../../training_set/analises:/analises -w /app python:3.12-slim python extrator_llm.py ./out ../analises/matriz_resultados_llm_sem_preprocessamento.csv
```

Depois, `python3 common/analises/metricas_por_regra.py training_set` já inclui automaticamente a linha "LLM (sem pre-processamento)" na comparação, se o arquivo acima existir.

## Resultado

Comparação de `CKV_FINOPS_03` (a única regra afetada pela mudança, já que é a única que depende de resolução de região) entre as duas execuções, contra o gabarito independente (`gerar_ground_truth.py`):

| Versão                        | TP | FP | FN | TN | Divergências N/A | Precision | Recall | F1    | Accuracy |
|--------------------------------|----|----|----|----|-------------------|-----------|--------|-------|----------|
| Checkov                        | 3  | 0  | 0  | 27 | 0                 | 1,000     | 1,000  | 1,000 | 1,000    |
| LLM — `completo` (com variáveis) | 3  | 0  | 0  | 27 | 0                 | 1,000     | 1,000  | 1,000 | 1,000    |
| LLM — `sem_variaveis`          | 1  | 12 | 0  | 0  | 17                | 0,077     | 1,000  | 0,143 | **0,077**    |

A Accuracy do LLM em `CKV_FINOPS_03` cai de 1,000 para 0,077 quando o bloco `variaveis_globais` é removido do payload. Sem ele, o modelo: (a) responde `FAILED` "no escuro" em 12 dos casos com região correta (falso positivo — parece assumir o pior quando não consegue resolver a variável), e (b) responde `N/A` em 17 casos, confundindo "não tenho informação suficiente para decidir" com "esta regra não se aplica" — um erro de semântica de N/A diferente do que resolvemos anteriormente (ali era uma interpretação errada de uma condição; aqui é ausência de dado mesmo). Acertou apenas 1 dos 30 casos.

**Interpretação**: o resultado da ablação não confirma a hipótese de que "a diferença arquitetural não importa" (formulada em `arquitetura_avaliadores.md` antes deste experimento) — na verdade a refuta parcialmente. A diferença importa, e muito, **para o LLM continuar funcionando nesta regra**: sem a ajuda de pré-processamento, sua acurácia desaba para próximo do acaso. O achado mais preciso é outro: os dois métodos empatam em 100% no cenário atual, mas por caminhos de robustez muito diferentes — o Checkov resolve a região nativamente, sem qualquer assistência externa, enquanto o LLM só alcança o mesmo resultado porque foi deliberadamente instrumentado (via pré-processamento e prompt engineering) para isso. Retirada essa instrumentação, a paridade desaparece. Isso é evidência ainda mais forte contra a alegação de "rastreabilidade semântica superior" do LLM do que a simples observação de empate: sugere que a robustez arquitetural do analisador estático, aqui, é maior que a do LLM, não menor.

## Correção aplicada após a ablação

Com base neste resultado, a arquitetura foi corrigida: `otimizar_plano_terraform` agora extrai o atributo `region` diretamente de cada recurso (o mesmo campo, já resolvido pelo Terraform, que o Checkov lê), em vez de enviar um bloco `provedores` bruto mais um bloco `variaveis_globais` separado para o LLM cruzar manualmente via prompt. O toggle `PREPROCESSAMENTO` (`completo`/`sem_variaveis`) descrito acima foi removido do código — deixou de fazer sentido, já que não existe mais um bloco de variáveis para ligar/desligar. Este documento permanece como registro histórico do experimento que motivou a correção; o código atual de `avaliador_llm.py` já reflete a versão corrigida.

**Verificação pós-correção**: confirmado. Rodando novamente contra o `training_set` com o payload corrigido (campo `region` direto, sem `provedores`/`variaveis_globais`), `CKV_FINOPS_03` manteve Accuracy = 1,000 (TP=3, FP=0, FN=0, TN=27) — igual ao resultado anterior, mas agora sem depender de nenhuma resolução de variável no prompt. A correção não introduziu regressão nesta regra.
