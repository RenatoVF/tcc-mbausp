#!/bin/sh
set -e

# Gera a versao textual legivel ("terraform show") de cada plano .plan ja
# existente em /tfvars, para uso na revisao humana (analises/../revisao_humana).
# Nao gera planos novos: assume que sadcloud/tfvars/run_plans.sh ja rodou antes.

cd /infra
terraform init -input=false

mkdir -p /tfvars/human_review_raw

for planfile in /tfvars/*.plan; do
  [ -e "$planfile" ] || continue
  name=$(basename "$planfile" .plan)
  outfile="/tfvars/human_review_raw/${name}.txt"
  echo "Renderizando $name"
  terraform show -no-color "$planfile" > "$outfile"
done

echo "Concluido: planos legiveis em /tfvars/human_review_raw/*.txt"
