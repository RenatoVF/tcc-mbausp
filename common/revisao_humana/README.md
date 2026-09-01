# Revisão humana — scripts comuns

Estes scripts são compartilhados entre `training_set` e `test_set`: ambos
recebem o caminho do conjunto como argumento de linha de comando, então
nunca precisam ser duplicados nem editados entre um conjunto e outro.

Ajuste (ponto 8 da resposta do orientador, 2026-08-31): cada avaliador
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
  AWS/Terraform e certificações relevantes (itens pedidos no ponto 8).

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

## Próximo passo (fora do escopo desta pasta)

Depois de coletadas as avaliações, um extrator (nos moldes de
`common/checkov/extrator_checkov.py`) deve ler os `.docx` preenchidos de
cada avaliador, cruzar com o `mapa_ids.csv` daquele avaliador (dentro de
`<set>/revisao_humana/privada/revisores/<código>/`) para recuperar o
`arquivo_original`, e gerar uma `matriz_resultados_humanos.csv` dentro de
`<set>/analises/` (com uma coluna por avaliador, ex.: `R1`, `R2`, `R3`),
equivalente às já existentes, para comparar as três abordagens regra a
regra e calcular a concordância entre avaliadores (ex.: Fleiss' Kappa,
ponto 8/10 da resposta do orientador).
