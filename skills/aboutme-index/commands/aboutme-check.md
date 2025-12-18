---
description: Check for files missing ABOUTME headers
---

# Check ABOUTME Coverage

Run the ABOUTME index checker to find files that are missing ABOUTME headers.

Execute this command from the skill's scripts directory:

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts" && python3 build_index.py "${CLAUDE_PROJECT_DIR:-.}" --check
```

The output is formatted as a copy-paste ready prompt. If files are missing headers, show the user the output and offer to add headers to those files.
