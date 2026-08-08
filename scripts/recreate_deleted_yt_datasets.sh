#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUDIT_TSV="${1:-/tmp/yt_pronunciation_audit.tsv}"
OUTPUT_TSV="${2:-/tmp/yt_recreate_results.tsv}"

if [[ ! -f "$AUDIT_TSV" ]]; then
  echo "audit report not found: $AUDIT_TSV" >&2
  exit 2
fi

if [[ ! -f "$OUTPUT_TSV" ]]; then
  printf 'dataset_name\tstatus\tdataset_id\tmessage\n' > "$OUTPUT_TSV"
fi

mapfile -t DATASETS < <(awk -F $'\t' 'NR > 1 && $1 == "needs_fix" {print $2}' "$AUDIT_TSV")

for dataset_name in "${DATASETS[@]}"; do
  if awk -F $'\t' -v name="$dataset_name" 'NR > 1 && $1 == name && $2 == "success" {found=1} END {exit found ? 0 : 1}' "$OUTPUT_TSV"; then
    echo "[INFO] skip already recreated $dataset_name" >&2
    continue
  fi
  dataset_dir="$ROOT_DIR/datasets/$dataset_name"
  if [[ ! -d "$dataset_dir" ]]; then
    printf '%s\tmissing_dir\t\t%s\n' "$dataset_name" "$dataset_dir" >> "$OUTPUT_TSV"
    continue
  fi
  if [[ ! -f "$dataset_dir/df.jsonl" || ! -f "$dataset_dir/sf.jsonl" ]]; then
    printf '%s\tmissing_manifest\t\t%s\n' "$dataset_name" "$dataset_dir" >> "$OUTPUT_TSV"
    continue
  fi

  echo "[INFO] recreating $dataset_name" >&2
  tmp_log="$(mktemp)"
  if (
    cd "$dataset_dir"
    unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY
    ds-cli create -t phy -df df.jsonl -sf sf.jsonl -n "$dataset_name" --test
  ) >"$tmp_log" 2>&1; then
    dataset_id="$(grep -Eo 'ds[0-9A-Z]+' "$tmp_log" | tail -n1 || true)"
    message="$(tail -n 1 "$tmp_log" | tr '\t' ' ' | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')"
    printf '%s\tsuccess\t%s\t%s\n' "$dataset_name" "$dataset_id" "$message" >> "$OUTPUT_TSV"
  else
    message="$(tail -n 20 "$tmp_log" | tr '\t' ' ' | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')"
    printf '%s\tfailed\t\t%s\n' "$dataset_name" "$message" >> "$OUTPUT_TSV"
  fi
  rm -f "$tmp_log"
done

echo "$OUTPUT_TSV"
