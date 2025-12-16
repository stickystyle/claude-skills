#!/bin/bash
# ABOUTME: SessionStart hook to rebuild ABOUTME index on session start.
# ABOUTME: Ensures index is always fresh regardless of external edits.

set -e

# Get the project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Determine script directory from this script's location
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$HOOK_DIR")"
SCRIPT_DIR="$SKILL_DIR/scripts"
SCRIPT_PATH="$SCRIPT_DIR/build_index.py"

# Output path for the index
OUTPUT_PATH="$PROJECT_DIR/.claude/aboutme-index.json"

# Only rebuild if the project has an existing index or ABOUTME files
if [ -f "$OUTPUT_PATH" ] || grep -rq "^# ABOUTME:" "$PROJECT_DIR" --include="*.py" 2>/dev/null; then
    if [ -f "$SCRIPT_PATH" ]; then
        cd "$SCRIPT_DIR"
        python3 build_index.py "$PROJECT_DIR" -o "$OUTPUT_PATH" 2>/dev/null
    fi
fi

exit 0
