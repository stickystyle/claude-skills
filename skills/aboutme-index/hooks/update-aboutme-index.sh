#!/bin/bash
# ABOUTME: Hook script for incremental ABOUTME index updates.
# ABOUTME: Updates only the single file that was edited, not the entire index.

set -e

# Read JSON from stdin
INPUT=$(cat)

# Extract the file path that was edited
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Exit early if no file path
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Get the project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Determine script directory from this script's location
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$HOOK_DIR")"
SCRIPT_PATH="$SKILL_DIR/scripts/update_file.py"

# Run incremental update
if [ -f "$SCRIPT_PATH" ]; then
    python3 "$SCRIPT_PATH" "$FILE_PATH" --project-dir "$PROJECT_DIR" 2>/dev/null || true
fi

exit 0
