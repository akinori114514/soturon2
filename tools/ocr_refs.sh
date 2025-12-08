#!/usr/bin/env bash
set -euo pipefail

REFS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../refs" && pwd)"
OCR_DIR="${REFS_DIR}/_ocr"
TEXT_DIR="${REFS_DIR}/_text"
REPORT="${OCR_DIR}/ocr_report.md"

mkdir -p "$OCR_DIR" "$TEXT_DIR"

processed=0
skipped=0
failed=0
fail_list=()

while IFS= read -r -d '' pdf; do
  rel="${pdf#$REFS_DIR/}"
  # skip files already under _ocr
  case "$rel" in
    _ocr/*) continue ;;
  esac
  out_pdf="${OCR_DIR}/${rel}"
  out_txt="${TEXT_DIR}/${rel%.pdf}.txt"
  mkdir -p "$(dirname "$out_pdf")" "$(dirname "$out_txt")"

  if [[ -f "$out_pdf" && "$out_pdf" -nt "$pdf" ]]; then
    ((skipped++))
    continue
  fi

  ((processed++))
  if ! ocrmypdf --skip-text --deskew --rotate-pages -l jpn+chi_sim+eng --sidecar "$out_txt" "$pdf" "$out_pdf" >/tmp/ocr_refs.log 2>&1; then
    ((failed++))
    fail_list+=("$rel")
  fi
done < <(find "$REFS_DIR" -name '*.pdf' -print0)

{
  echo "# OCR Report"
  echo ""
  echo "- Processed: $processed"
  echo "- Skipped (up-to-date): $skipped"
  echo "- Failed: $failed"
  echo ""
  if (( failed > 0 )); then
    echo "## Failed files"
    for f in "${fail_list[@]}"; do
      echo "- $f"
    done
  fi
} > "$REPORT"

exit 0
