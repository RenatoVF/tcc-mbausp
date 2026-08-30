#!/bin/sh
set -e

# expect JSON plans mounted at /data
if [ ! -d /data ]; then
  echo "/data not found"
  exit 1
fi

for f in /data/*.json; do
  [ -e "$f" ] || continue
  name=$(basename "$f" .json)
  echo "Running Infracost for $name"
  infracost breakdown --path "$f" --format json --out-file "/out/${name}.infracost.json" || {
    echo "Infracost failed for $name"
  }
done

echo "All done. Outputs: /out/*.infracost.json"
