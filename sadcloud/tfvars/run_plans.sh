#!/bin/sh
set -e

cd /infra
terraform init -input=false

for tfvars in /tfvars/*.tfvars; do
  name=$(basename "$tfvars" .tfvars)
  planfile="/tfvars/${name}.plan"
  jsonfile="/tfvars/${name}.json"
  echo "Planning $name"
  terraform plan -var-file="$tfvars" -out="$planfile" -input=false
  terraform show -json "$planfile" > "$jsonfile"
done

echo "Done: JSON plans available as /tfvars/*.json"
