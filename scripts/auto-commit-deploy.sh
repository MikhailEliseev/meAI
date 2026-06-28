#!/bin/bash
# Auto-commit before deploy to prevent data loss

set -e

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BRANCH=$(git branch --show-current)

echo "=== Auto-commit before deploy ==="
echo "Branch: $BRANCH"
echo "Time: $TIMESTAMP"

# Check if there are changes
if [[ -z $(git status -s) ]]; then
    echo "No changes to commit"
    exit 0
fi

# Show what will be committed
echo ""
echo "Changes to commit:"
git status -s

# Commit everything
git add -A
git commit -m "auto: pre-deploy snapshot $TIMESTAMP

Auto-committed before deploy to preserve working state.
Branch: $BRANCH
Session: $(cat .current-task 2>/dev/null || echo 'unknown')
"

echo ""
echo "✅ Auto-commit complete: $(git rev-parse --short HEAD)"
echo ""
