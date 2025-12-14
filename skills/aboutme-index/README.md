# ABOUTME Index

A Claude Code skill for semantic file discovery using ABOUTME headers.

## What It Does

Instead of grep-searching or spawning Explore agents to find relevant files, this skill maintains a JSON index of human-written file descriptions. When you ask "where is authentication handled?", Claude reads one file and instantly finds the answer.

## How It Works

1. **Convention**: All code files start with ABOUTME comments:
   ```python
   # ABOUTME: JWT authentication module for AWS Cognito access tokens.
   # ABOUTME: Handles token validation, JWKS caching, and user context.
   ```

2. **Indexer**: A Python script extracts these into `.claude/aboutme-index.json`

3. **Hooks**: The index auto-rebuilds on session start and updates incrementally on edits

## Setup Your Project

1. Add ABOUTME headers to your files (first 2 lines):
   ```python
   # ABOUTME: Brief description of what this file does.
   # ABOUTME: Additional context about its purpose.
   ```

2. Add to your project's `CLAUDE.md`:
   ```markdown
   ## File Discovery

   This project has ABOUTME headers in all files. When searching for relevant files,
   read the index at `.claude/aboutme-index.json` instead of using grep or Explore.
   ```

3. Optionally add `.claude/aboutme-index.json` to `.gitignore` (it rebuilds on session start)

## Commands

| Task | Command |
|------|---------|
| Read index | `cat .claude/aboutme-index.json` |
| Full rebuild | `python ~/.claude/skills/aboutme-index/scripts/build_index.py . -o .claude/aboutme-index.json` |
| Check coverage | `python ~/.claude/skills/aboutme-index/scripts/build_index.py . --check` |
| Check staleness | `python ~/.claude/skills/aboutme-index/scripts/build_index.py . --stale` |

## Index Format

```json
{
  "app/src/auth.py": "JWT authentication module for AWS Cognito access tokens...",
  "app/src/config.py": "Centralized configuration using Pydantic settings..."
}
```

## Why This Pattern?

- **Speed**: 1 file read vs. multiple grep/glob operations
- **Accuracy**: Human-curated descriptions beat pattern matching
- **Semantic**: Natural language queries match natural language descriptions
- **Low overhead**: 2-line comments per file, auto-maintained index

## Supported File Types

The indexer looks for ABOUTME headers in:
- `.py` - Python
- `.sh` - Shell scripts
- `.yml`, `.yaml` - YAML configs
- `.toml` - TOML configs
