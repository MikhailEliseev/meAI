#!/bin/bash
# Setup alias for Architect - Quick access from anywhere
# Run this once: ./setup_alias.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║              🏗️  ARCHITECT - Setup Alias                     ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Определяем shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo -e "${YELLOW}⚠️  Unknown shell. Please add alias manually.${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Detected shell: ${SHELL_NAME}"
echo -e "${GREEN}✓${NC} Config file: ${SHELL_RC}"
echo ""

# Проверяем, есть ли уже алиас
if grep -q "alias architect=" "$SHELL_RC" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Alias 'architect' already exists in ${SHELL_RC}${NC}"
    echo ""
    echo "Current alias:"
    grep "alias architect=" "$SHELL_RC"
    echo ""
    read -p "Replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Удаляем старый алиас
    sed -i.bak '/alias architect=/d' "$SHELL_RC"
    sed -i.bak '/# meAI Architect/d' "$SHELL_RC"
fi

# Добавляем алиас
echo "" >> "$SHELL_RC"
echo "# meAI Architect - Quick access from anywhere" >> "$SHELL_RC"
echo "alias architect='/Users/mikhaileliseev/Desktop/Dev/meAI/architect.sh'" >> "$SHELL_RC"

echo -e "${GREEN}✅ Alias added successfully!${NC}"
echo ""
echo -e "${BLUE}To activate now, run:${NC}"
echo -e "  ${YELLOW}source ${SHELL_RC}${NC}"
echo ""
echo -e "${BLUE}Or just open a new terminal.${NC}"
echo ""
echo -e "${BLUE}Usage:${NC}"
echo -e "  ${GREEN}architect \"Your question\"${NC}"
echo ""
echo -e "${BLUE}Examples:${NC}"
echo "  architect \"Какую нишу выбрать первой?\""
echo "  architect \"Создай SEO агента\""
echo "  architect \"Запусти AIM Agency\""
echo ""
echo -e "${GREEN}🎉 Done!${NC}"
