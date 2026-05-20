#!/bin/bash
# copy_soul.sh — ensure SOUL.md is at HERMES_HOME/SOUL.md
#
# Hermes load_soul_md() function reads from $HERMES_HOME/SOUL.md (hardcoded path).
# Source: agent/prompt_builder.py:1308 — get_hermes_home() / "SOUL.md"
#
# Our SOUL.md lives in skills/aim/ which is mounted read-only (per D-03: skills
# from repo copied into Docker image at build time via COPY).
# Hermes DOES NOT search skills/ subdirectories for SOUL.md.
#
# Solution: copy SOUL.md to HERMES_HOME at container startup.
# Plan 15-03 will call this script before starting uvicorn in the Dockerfile.

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-/opt/data}"
SOURCE="/opt/hermes/skills/aim/SOUL.md"
TARGET="${HERMES_HOME}/SOUL.md"

if [ ! -f "$SOURCE" ]; then
    echo "[copy_soul] ERROR: SOUL.md not found at $SOURCE" >&2
    echo "[copy_soul] Skills directory may not be mounted correctly. Check Dockerfile COPY instruction." >&2
    exit 1
fi

mkdir -p "$HERMES_HOME"

# Copy if target doesn't exist or source is newer
# Using cp (not ln -s) because skills directory is mounted read-only per D-03
if [ ! -f "$TARGET" ] || [ "$SOURCE" -nt "$TARGET" ]; then
    cp "$SOURCE" "$TARGET"
    echo "[copy_soul] SOUL.md copied to $TARGET ($(wc -l < "$TARGET") lines)"
else
    echo "[copy_soul] SOUL.md already present at $TARGET (up to date)"
fi

# Copy supplementary knowledge files referenced by SOUL.md
# SOUL.md line 13: "services.md, processes.md, kpi.md (загружаются отдельно AIAgent)"
# These provide detailed service descriptions, processes, and KPIs
for FILE in services.md processes.md kpi.md; do
    SRC="/opt/hermes/skills/aim/$FILE"
    DST="${HERMES_HOME}/$FILE"
    if [ -f "$SRC" ]; then
        cp "$SRC" "$DST"
        echo "[copy_soul] $FILE copied to $DST ($(wc -l < "$DST") lines)"
    else
        echo "[copy_soul] WARNING: $FILE not found at $SRC" >&2
    fi
done
