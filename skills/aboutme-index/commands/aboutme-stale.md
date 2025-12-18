---
description: Check for stale ABOUTME headers that may need updating
---

# Check Stale ABOUTME Headers

Check if any files have ABOUTME headers that may be out of date compared to their content.

Execute this command:

```bash
cd "${CLAUDE_PLUGIN_ROOT}/scripts" && python3 build_index.py "${CLAUDE_PROJECT_DIR:-.}" --stale
```

If stale headers are found, show the user which files may need their ABOUTME headers updated and offer to review and update them.
