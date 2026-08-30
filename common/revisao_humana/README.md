# Revisão humana — scripts comuns

Estes dois scripts são compartilhados entre `training_set` e `test_set`:
ambos recebem o caminho do conjunto como argumento de linha de comando, então
nunca precisam ser duplicados nem editados entre um conjunto e outro.

- `gerar_mapa_ids.py <caminho_do_set>` — lê `<set>/analises/amostras.md`,
  embaralha os casos (seed fixa, documentada no topo do script) e escreve
  `<set>/revisao_humana/privada/mapa_ids.csv` (o gabarito), além de criar o
  esqueleto de pastas `<set>/revisao_humana/publica/planos` e
  `<set>/revisao_humana/privada/revisores`.
- `finalizar_planos_publicos.py <caminho_do_set>` — lê o `mapa_ids.csv` do
  set e os planos renderizados em `<set>/sadcloud/tfvars/human_review_raw/`
  (gerados pelo `common/sadcloud/scripts/run_show_all.sh`), e monta
  `<set>/revisao_humana/publica/planos/plano_01.txt ... plano_NN.txt`,
  já anonimizados, com uma checagem de segurança contra vazamento das
  strings "compliant"/"noncompliant" no texto renderizado.
- `gerar_formulario.js` — gera o `Formulario_Revisao_FinOps.docx` (via
  `node gerar_formulario.js`, precisa do pacote `docx` do npm). O formulário
  em si tem 30 linhas fixas (`plano_01` a `plano_30`), reaproveitável tanto
  para os 30 casos do training_set quanto para os 15 pares (= 30 planos)
  selecionados do test_set para avaliação humana. Se o número de casos
  selecionados mudar, ajuste a constante do loop (`for (let i = 1; i <= 30; i++)`)
  no script antes de gerar.

## Fluxo, para qualquer um dos dois sets

1. Gerar os planos legíveis (no host, com Docker — ver `common/comandos.txt`):
   `docker compose run --rm --entrypoint sh terraform -c "sh /scripts/run_show_all.sh"`
   (com `TFVARS_DIR` apontando para `<set>/sadcloud/tfvars` quando for o test_set).
2. `python3 gerar_mapa_ids.py <caminho_do_set>`
3. `python3 finalizar_planos_publicos.py <caminho_do_set>`
4. Conferir manualmente `<set>/revisao_humana/publica/` antes de compactar.
5. Gerar o `.zip` de `<set>/revisao_humana/publica/` e enviar aos revisores.
6. Ao receber os formulários preenchidos, salvar em
   `<set>/revisao_humana/privada/revisores/<código>/` (R1, R2, R3) e
   preencher `<set>/revisao_humana/privada/revisores/mapa_revisores.csv`
   com o nome real de cada revisor (esse arquivo nunca sai da pasta privada).

## Próximo passo (fora do escopo desta pasta)

Depois de coletadas as avaliações, um extrator (nos moldes de
`common/checkov/extrator_checkov.py`) deve ler os `.docx` preenchidos, cruzar
com `mapa_ids.csv` do set correspondente para recuperar o `arquivo_original`,
e gerar uma `matriz_resultados_humanos.csv` dentro de `<set>/analises/`,
equivalente às já existentes, para comparar as três abordagens regra a regra.
