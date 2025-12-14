#!/bin/bash
# ABOUTME: SessionStart hook to rebuild ABOUTME index on session start.
# ABOUTME: Ensures index is always fresh regardless of external edits.

set -e

# Get the project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Path to the build script
SCRIPT_PATH="$HOME/.claude/skills/aboutme-index/scripts/build_index.py"

# Output path for the index
OUTPUT_PATH="$PROJECT_DIR/.claude/aboutme-index.json"

# Only rebuild if the project has an existing index or ABOUTME files
if [ -f "$OUTPUT_PATH" ] || grep -rq "^# ABOUTME:" "$PROJECT_DIR" --include="*.py" 2>/dev/null; then
    if [ -f "$SCRIPT_PATH" ]; then
        cd "$HOME/.claude/skills/aboutme-index/scripts"
        python3 build_index.py "$PROJECT_DIR" -o "$OUTPUT_PATH" 2>/dev/null
    fi
fi

exit 0
