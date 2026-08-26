# Revisão humana — organização e fluxo de trabalho

Esta pasta organiza a etapa de avaliação por revisores humanos, espelhando o
papel do Checkov (`checkov/`) e da LLM (`llm/`) para os mesmos 30 planos.

## Estrutura

```
revisao_humana/
├── publica/                          # isto (e só isto) vira o .zip enviado a cada revisor
│   ├── planos/                       # plano_01.txt .. plano_30.txt (terraform show, anonimizado)
│   └── Formulario_Revisao_FinOps.docx
└── privada/                          # NUNCA compartilhar com os revisores
    ├── mapa_ids.csv                  # gabarito: id_publico <-> arquivo original, conformidade real, etc.
    ├── gerar_mapa_ids.py             # gera/regera mapa_ids.csv e o esqueleto de pastas (seed fixa)
    ├── finalizar_planos_publicos.py  # copia os planos renderizados para publica/planos, já anonimizados
    └── revisores/                    # uma subpasta por revisor (formulários preenchidos recebidos)
        ├── R1/
        ├── R2/
        └── ...
```

## Fluxo de geração (uma vez, ou sempre que o dataset mudar)

1. **Gerar os planos legíveis** (precisa do Docker, no host — não roda dentro do
   ambiente sandbox do Claude). A partir de `sadcloud/sadcloud/`:

   ```sh
   docker compose run --rm --entrypoint sh terraform -c "../tfvars/run_show_all.sh"
   ```

   Isso lê os `.plan` já existentes em `sadcloud/tfvars/` e gera a versão
   texto (`terraform show`) de cada um em `sadcloud/tfvars/human_review_raw/*.txt`.
   Não recria os planos — só os torna legíveis.

2. **Montar a pasta pública** (roda local, sem Docker):

   ```sh
   cd revisao_humana/privada
   python3 finalizar_planos_publicos.py
   ```

   Lê `mapa_ids.csv`, copia cada plano renderizado para
   `revisao_humana/publica/planos/plano_XX.txt` com o número anonimizado, e
   faz uma checagem de segurança para garantir que nenhuma string
   "compliant"/"noncompliant" vazou para o texto público.

3. **Conferir manualmente** o conteúdo de `publica/` antes de compactar —
   principalmente `publica/planos/*.txt`, para garantir que nada identifica o
   caso original.

4. **Gerar o .zip** de `revisao_humana/publica/` e enviar uma cópia idêntica
   para cada revisor.

## Regerando o mapa de IDs

`mapa_ids.csv` já foi gerado com uma seed fixa (documentada no topo de
`gerar_mapa_ids.py`), garantindo que o embaralhamento não correlacione o
número do plano com conformidade, complexidade ou posição original. Só rode
`gerar_mapa_ids.py` de novo se o dataset de amostras mudar — isso
sobrescreve `mapa_ids.csv` com uma nova distribuição.

## Recebendo as avaliações

Ao receber o `.docx` preenchido de cada revisor, salve-o em
`privada/revisores/<código-do-revisor>/` (ex.: `R1/`, `R2/`, `R3/`). Use um
código por revisor (não o nome completo) nos arquivos e nas análises depois
— mantenha a correspondência nome real → código em um lugar separado dentro
de `privada/` (não incluído aqui de propósito, para você preencher com os
nomes reais).

## Próximo passo (fora do escopo desta pasta)

Depois de coletadas as avaliações, um extrator (nos moldes de
`checkov/extrator_checkov.py` e `llm/extrator_llm.py`) deve ler os `.docx`
preenchidos, cruzar com `mapa_ids.csv` para recuperar o `arquivo_original` e
gerar uma `matriz_resultados_humanos.csv` equivalente às já existentes em
`analises/`, permitindo comparar as três abordagens regra a regra.
