#!/bin/sh
set -e

FILENAME="$1"

cd /infra
terraform init -input=false

name=$(basename "$FILENAME" .tfvars)

planfile="/tfvars/${name}.plan"
jsonfile="/tfvars/${name}.json"
terraform plan -var-file="/tfvars/$FILENAME" -out="$planfile" -input=false
terraform show -json "$planfile" > "$jsonfile"
