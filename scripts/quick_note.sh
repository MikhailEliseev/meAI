#!/bin/bash
# Quick note capture script for Architect Raw Inbox
# Usage: ./quick_note.sh "Your idea or note here"

set -e

# Paths
RAW_DIR="$(cd "$(dirname "$0")/../obsidian/architect/raw" && pwd)"
TIMESTAMP=$(date +"%Y%m%d-%H%M")
FILENAME="${TIMESTAMP}-quick.md"
FILEPATH="${RAW_DIR}/${FILENAME}"

# Check if note content provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"Your note content\""
    echo "Example: $0 \"Idea: Use AI agents for email marketing\""
    exit 1
fi

NOTE_CONTENT="$1"

# Create note with frontmatter
cat > "$FILEPATH" << NOTEEOF
---
title: "Quick Note ${TIMESTAMP}"
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
status: new
type: note
priority: medium
tags:
  - quick-note
---

# Quick Note

$NOTE_CONTENT

---

**Captured:** $(date +"%Y-%m-%d %H:%M:%S")
NOTEEOF

echo "✅ Note saved: $FILENAME"
echo "📍 Location: $FILEPATH"
echo ""
echo "Content:"
echo "$NOTE_CONTENT"
