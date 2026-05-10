#!/bin/bash
# Helper script for updating SESSION.md during spec creation

set -e

AGENT_NAME="${1:-Unknown Agent}"
STAGE="${2:-Unknown Stage}"
STATUS="${3:-IN PROGRESS}"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M GMT%z')

cat >> SESSION.md << EOF

## $TIMESTAMP

### $STATUS: $AGENT_NAME - $STAGE

**Что сделано:**
- Stage: $STAGE
- Status: $STATUS

EOF

echo "✅ SESSION.md updated: $AGENT_NAME - $STAGE"
