# Revisão humana — scripts comuns

Estes scripts são compartilhados entre `training_set` e `test_set`: ambos
recebem o caminho do conjunto como argumento de linha de comando, então
nunca precisam ser duplicados nem editados entre um conjunto e outro.

Cada avaliador
recebe uma **ordem própria e independente** dos 30 planos selecionados, para
reduzir efeitos de aprendizado/fadiga e para que avaliadores não consigam
comparar respostas por número de plano. Os avaliadores são identificados
apenas pelos códigos anônimos `R1`, `R2`, `R3` (constante `REVISORES` no
topo dos scripts) — o nome real de cada um, se necessário, fica só em
`<set>/revisao_humana/privada/mapa_revisores.csv` (cópia de trabalho local,
nunca commitada — ver `.gitignore`; o arquivo versionado é o template vazio
`mapa_revisores.csv.template`).

- `gerar_mapa_ids.py <caminho_do_set>` — lê a seleção de casos do set (ver
  "Fonte dos casos" abaixo), e para CADA avaliador em `REVISORES` gera um
  embaralhamento independente (seed própria = `SEED_BASE` + índice do
  avaliador, documentada no script) e escreve
  `<set>/revisao_humana/privada/revisores/<código>/mapa_ids.csv` (o gabarito
  daquele avaliador), além do esqueleto de pastas
  `<set>/revisao_humana/publica/<código>/planos`.
- `finalizar_planos_publicos.py <caminho_do_set>` — para cada avaliador, lê
  o `mapa_ids.csv` correspondente e os planos renderizados em
  `<set>/sadcloud/tfvars/human_review_raw/` (gerados pelo
  `common/sadcloud/scripts/run_show_all.sh`), e monta
  `<set>/revisao_humana/publica/<código>/planos/plano_01.txt ... plano_30.txt`
  daquele avaliador — já anonimizados, com checagem de segurança contra
  vazamento das strings "compliant"/"noncompliant" no texto renderizado.
- `gerar_formulario.js` — gera `Formulario_Revisao_FinOps.docx` (via
  `node gerar_formulario.js`, precisa do pacote `docx` do npm), escrito ao
  lado do script. O formulário é genérico (não referencia nenhum caso
  específico) e por isso é o **mesmo arquivo enviado a todos os
  avaliadores** — só a pasta `planos/` que acompanha cada envio muda. Tem 30
  linhas fixas (`plano_01` a `plano_30`); se o número de casos selecionados
  mudar, ajuste a constante do loop (`for (let i = 1; i <= 30; i++)`) antes
  de gerar. Inclui, na seção "Identificação do revisor": nome, e-mail, datas
  de início/término, anos de experiência em TI, anos de experiência com
  AWS/Terraform e certificações relevantes.

## Fonte dos casos (`gerar_mapa_ids.py`)

1. `<set>/analises/selecao_revisao_humana.md` — formato em pares, usado pelo
   `test_set` (15 pares = 30 planos selecionados dentre os 90 pares do
   holdout). As colunas "Recursos" de cada par são enriquecidas via join com
   `<set>/analises/amostras.md`.
2. `<set>/analises/amostras.md` (formato em linha por arquivo, IDs
   `C0xx`/`NC0xx`) — fallback para o formato original do `training_set`.

## Fluxo, para qualquer um dos dois sets

1. Gerar os planos legíveis (no host, com Docker — ver `common/comandos.txt`):
   `docker compose run --rm --entrypoint sh terraform -c "sh /scripts/run_show_all.sh"`
   (com `TFVARS_DIR` apontando para `<set>/sadcloud/tfvars` quando for o test_set).
2. `python3 gerar_mapa_ids.py <caminho_do_set>`
3. `python3 finalizar_planos_publicos.py <caminho_do_set>`
4. Conferir manualmente `<set>/revisao_humana/publica/<código>/` de cada
   avaliador antes de compactar (nenhum aviso `[ATENCAO]` deve aparecer).
5. `node gerar_formulario.js` (uma vez só — o formulário é o mesmo para
   todos os avaliadores).
6. Para cada avaliador, montar um `.zip` com
   `<set>/revisao_humana/publica/<código>/planos/` +
   `Formulario_Revisao_FinOps.docx`, e enviar.
7. Ao receber os formulários preenchidos, salvar em
   `<set>/revisao_humana/privada/revisores/<código>/` (nunca commitar) e
   preencher `<set>/revisao_humana/privada/mapa_revisores.csv` (cópia de
   trabalho local, a partir do template) com o nome real de cada avaliador.

## Extração dos resultados (`extrator_revisao_humana.py`)

Depois de receber os formulários preenchidos (passo 7 acima), rode:

    python3 extrator_revisao_humana.py <caminho_do_set>

O script exige que o formulário preenchido de cada avaliador seja o
**único arquivo `.docx`** dentro de
`<set>/revisao_humana/privada/revisores/<código>/` (mesmo lugar do
`mapa_ids.csv` daquele avaliador) — qualquer nome de arquivo serve. Ele lê
a tabela de respostas, normaliza o texto digitado (aceita variações
razoáveis de grafia/acentuação de "Aprovado"/"Falhou"/"N/A"), cruza cada
`plano_NN` com o `mapa_ids.csv` para recuperar o `arquivo_original`, e
gera em `<set>/analises/`:

- `matriz_resultados_humanos_bruta.csv` — uma linha por (avaliador, caso),
  resposta bruta normalizada por regra (usada pelo cálculo de concordância).
- `matriz_resultados_humanos.csv` — uma linha por caso, com o veredito por
  **maioria** entre os 3 avaliadores, no mesmo formato de
  `matriz_resultados_checkov.csv`/`matriz_resultados_llm.csv` (consumido
  diretamente por `metricas_por_regra.py` e `testes_estatisticos_3vias.py`).
  Quando os 3 avaliadores discordam totalmente entre si (sem maioria), a
  célula fica `SEM_MAIORIA` e o caso/regra também é listado em
  `divergencias_avaliadores.csv`, para revisão manual.
- `experiencia_avaliadores.csv` — anos de experiência em TI, anos com
  AWS/Terraform, certificações e tempo médio de análise, por código
  (`R1`/`R2`/`R3`) — **nunca** nome ou e-mail do avaliador. A extração
  desses campos de experiência é *best-effort* (regex sobre texto livre);
  revise manualmente antes de reportar no TCC.

Célula vazia ou com texto não reconhecido gera um aviso no console (nunca
é adivinhada silenciosamente) — resolva manualmente antes de usar os
resultados nas análises seguintes.

Na sequência, `common/analises/concordancia_humana.py` (concordância
exata e Kappa de Fleiss por regra, a partir da matriz bruta) e
`common/analises/testes_estatisticos_3vias.py` (Cochran's Q e McNemar
pareado com correção de Holm-Bonferroni entre Checkov/LLM/Humano, a
partir da matriz agregada) completam a comparação estatística entre
Checkov, LLM e avaliação humana — ver o cabeçalho de cada script para
detalhes.
