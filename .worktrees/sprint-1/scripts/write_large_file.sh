#!/bin/bash
# Helper script for writing large files using Write + Bash append pattern

set -e

FILE_PATH="$1"
CONTENT_FILE="$2"
CHUNK_SIZE="${3:-200}"

if [ -z "$FILE_PATH" ] || [ -z "$CONTENT_FILE" ]; then
    echo "Usage: $0 <file_path> <content_file> [chunk_size]"
    echo "Example: $0 spec.md content.txt 200"
    exit 1
fi

if [ ! -f "$CONTENT_FILE" ]; then
    echo "Error: Content file not found: $CONTENT_FILE"
    exit 1
fi

# Count total lines
TOTAL_LINES=$(wc -l < "$CONTENT_FILE")
echo "📝 Writing large file: $FILE_PATH ($TOTAL_LINES lines)"

# Extract first chunk
head -n "$CHUNK_SIZE" "$CONTENT_FILE" > "${FILE_PATH}.tmp"
echo "✅ First chunk written ($CHUNK_SIZE lines)"

# If file has more lines, append the rest
if [ "$TOTAL_LINES" -gt "$CHUNK_SIZE" ]; then
    REMAINING=$((TOTAL_LINES - CHUNK_SIZE))
    echo "📎 Appending remaining $REMAINING lines..."

    tail -n "+$((CHUNK_SIZE + 1))" "$CONTENT_FILE" >> "${FILE_PATH}.tmp"
    echo "✅ Remaining lines appended"
fi

# Move to final location
mv "${FILE_PATH}.tmp" "$FILE_PATH"

# Verify
FINAL_LINES=$(wc -l < "$FILE_PATH")
FILE_SIZE=$(ls -lh "$FILE_PATH" | awk '{print $5}')

echo "✅ File written successfully:"
echo "   Lines: $FINAL_LINES"
echo "   Size: $FILE_SIZE"
echo "   Path: $FILE_PATH"
