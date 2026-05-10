#!/bin/bash
# Helper script for creating standardized commit messages for agent specifications

set -e

AGENT_NAME="${1:-Agent}"
BRIEF_POINTS="${2:-Brief created}"
RESEARCH_TOPIC="${3:-Research completed}"
FEATURES="${4:-Features implemented}"
SIZE_LINES="${5:-XXX}"
SIZE_KB="${6:-XX}"
RESEARCH_MODE="${7:-standard}"
RESEARCH_COST="${8:-\$1.50}"

cat << EOF
docs: create ${AGENT_NAME} specification (hybrid approach)

Created specification based on user brief + deep research + existing implementation:
- Brief: ${BRIEF_POINTS}
- Research: ${RESEARCH_TOPIC}
- Features: ${FEATURES}

Size: ${SIZE_LINES} lines, ~${SIZE_KB} KB
Research: ${RESEARCH_MODE} (~${RESEARCH_COST})

Co-Authored-By: Claude Opus 4 <noreply@anthropic.com>
EOF
