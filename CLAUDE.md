# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code plugin repository containing reusable "skills" that extend Claude's capabilities. Skills are installed via the plugin system and provide specialized tools, hooks, and knowledge.

## Commands

| Task | Command |
|------|---------|
| Build ABOUTME index | `python skills/aboutme-index/scripts/build_index.py . -o .claude/aboutme-index.json` |
| Check missing headers | `python skills/aboutme-index/scripts/build_index.py . --check` |
| Check index staleness | `python skills/aboutme-index/scripts/build_index.py . --stale` |
| Update single file | `python skills/aboutme-index/scripts/update_file.py <file>` |

## Architecture

### Skill Structure

Each skill is a self-contained plugin in `skills/<name>/`:
```
skills/<name>/
├── .claude-plugin/
│   └── plugin.json    # Skill's manifest (hooks, metadata)
├── SKILL.md           # YAML frontmatter + usage instructions for Claude
├── README.md          # User-facing documentation
├── commands/          # Slash commands (auto-discovered)
├── hooks/             # Shell scripts for lifecycle events
└── scripts/           # Python utilities invoked by hooks
```

### Plugin Distribution

The root `.claude-plugin/marketplace.json` is a catalog listing available skills. Each skill's `source` points to its directory, which contains its own `plugin.json`.

Users install individual skills:
```bash
/plugin marketplace add stickystyle/claude-skills
/plugin install aboutme-index@stickystyle-skills  # gets ONLY aboutme-index
/plugin install uv@stickystyle-skills             # gets ONLY uv
```

Skills are independent - installing one does not install another's hooks or commands.

### Hook Execution

Hooks use `${CLAUDE_PLUGIN_ROOT}` which resolves to the skill's root directory:
```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/hooks/rebuild-index-on-start.sh"
}
```

## Creating New Skills

1. Create the skill directory structure:
   ```
   skills/<name>/
   ├── .claude-plugin/plugin.json
   └── SKILL.md
   ```

2. Create `skills/<name>/.claude-plugin/plugin.json`:
   ```json
   {
     "name": "<name>",
     "description": "Brief description",
     "version": "1.0.0",
     "author": { "name": "Your Name" },
     "license": "MIT"
   }
   ```

3. Create `skills/<name>/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: Brief description shown in skill picker. Use when...
   ---
   # Usage instructions for Claude
   ```

4. Add hooks to `plugin.json` and create `hooks/` directory as needed

5. Add slash commands in `commands/` directory (auto-discovered)

6. Register in root `.claude-plugin/marketplace.json` under `plugins` array

## ABOUTME Convention

All code files use ABOUTME headers (first 2 lines) for semantic indexing:

```python
# ABOUTME: Brief description of what this file does.
# ABOUTME: Additional context about its purpose.
```

Run `--check` to find files missing headers.
