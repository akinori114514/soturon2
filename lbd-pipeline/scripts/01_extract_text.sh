#!/bin/bash
# 01_extract_text.sh - Extract text from all PDFs in refs/ directory
# Usage: ./01_extract_text.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
REFS_DIR="$BASE_DIR/refs"
OUTPUT_DIR="$BASE_DIR/lbd-pipeline/extracted"

echo "=== PDF Text Extraction ==="
echo "Source: $REFS_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Check if pdftotext is available
if ! command -v pdftotext &> /dev/null; then
    echo "Error: pdftotext not found. Install poppler: brew install poppler"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Count PDFs
total=$(find "$REFS_DIR" -maxdepth 1 -name "*.pdf" | wc -l | tr -d ' ')
echo "Found $total PDF files"
echo ""

# Process each PDF
count=0
success=0
failed=0

for pdf in "$REFS_DIR"/*.pdf; do
    if [ -f "$pdf" ]; then
        count=$((count + 1))
        filename=$(basename "$pdf" .pdf)
        output_file="$OUTPUT_DIR/${filename}.txt"

        printf "[%d/%d] Processing: %s ... " "$count" "$total" "$filename"

        if pdftotext -layout "$pdf" "$output_file" 2>/dev/null; then
            chars=$(wc -c < "$output_file" | tr -d ' ')
            printf "OK (%s chars)\n" "$chars"
            success=$((success + 1))
        else
            printf "FAILED\n"
            failed=$((failed + 1))
            echo "$filename" >> "$OUTPUT_DIR/failed.log"
        fi
    fi
done

echo ""
echo "=== Summary ==="
echo "Total: $count"
echo "Success: $success"
echo "Failed: $failed"

# Calculate total characters
total_chars=$(cat "$OUTPUT_DIR"/*.txt 2>/dev/null | wc -c | tr -d ' ')
echo "Total characters extracted: $total_chars"

echo ""
echo "Done. Output saved to: $OUTPUT_DIR"
