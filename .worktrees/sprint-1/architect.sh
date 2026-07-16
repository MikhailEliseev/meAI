#!/bin/bash
# Quick connect to Architect - One-click interface
# Usage: ./architect.sh "Your question"

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if question provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                                                              ║${NC}"
    echo -e "${YELLOW}║              🏗️  ARCHITECT - Quick Connect                   ║${NC}"
    echo -e "${YELLOW}║                                                              ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "  ./architect.sh \"Your question\""
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  ./architect.sh \"Какую нишу выбрать первой?\""
    echo "  ./architect.sh \"Создай SEO агента\""
    echo "  ./architect.sh \"Запусти AIM Agency\""
    echo ""
    exit 1
fi

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Architect
echo -e "${GREEN}🔄 Connecting to Architect...${NC}"
echo ""

python scripts/talk_to_architect.py "$1"

echo ""
echo -e "${GREEN}✅ Done!${NC}"
