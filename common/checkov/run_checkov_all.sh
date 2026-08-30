#!/bin/sh
set -e

# expect JSON plans mounted at /data
if [ ! -d /data ]; then
  echo "/data not found"
  exit 1
fi

# ensure output directory exists
mkdir -p /out

echo "Running Checkov on Terraform plans..."
for f in /data/*.json; do
  [ -e "$f" ] || continue
  name=$(basename "$f" .json)
  echo "Checking $name"
  tfvars_file="/data/${name}.tfvars"
  if [ -f "$tfvars_file" ]; then
    echo "Using variable file $tfvars_file"
    var_file_args="--var-file $tfvars_file"
  else
    var_file_args=""
  fi

  if checkov \
    --framework terraform_plan \
    --file "$f" \
    $var_file_args \
    --external-checks-dir /rules \
    --output json \
    --compact >"/out/${name}.checkov.json" 2>&1; then
    echo "Checkov completed for $name"
  else
    rc=$?
    echo "Checkov failed for $name (exit code: $rc)"
  fi
done
