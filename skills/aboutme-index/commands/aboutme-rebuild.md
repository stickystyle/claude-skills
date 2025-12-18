---
description: Rebuild the ABOUTME index from scratch
---

# Rebuild ABOUTME Index

Rebuild the complete ABOUTME index for the project. This scans all source files for ABOUTME headers and writes the index to `.claude/aboutme-index.json`.

Execute this command:

```bash
cd "${CLAUDE_PLUGIN_ROOT}/skills/aboutme-index/scripts" && python build_index.py "${CLAUDE_PROJECT_DIR:-.}" -o "${CLAUDE_PROJECT_DIR:-.}/.claude/aboutme-index.json"
```

Report the results to the user, including how many files were indexed.
