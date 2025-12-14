# ABOUTME Index

A Claude Code skill for semantic file discovery using ABOUTME headers.

## What It Does

Instead of grep-searching or spawning Explore agents to find relevant files, this skill maintains a JSON index of human-written file descriptions. When you ask "where is authentication handled?", Claude reads one file and instantly finds the answer.

## Example

```
> which files handle authentication?

⏺ Let me check the ABOUTME index for authentication-related files.

⏺ Read(.claude/aboutme-index.json)
  ⎿  Read 85 lines

⏺ Authentication is handled by these files:

  Core Authentication:
  - app/src/auth.py - JWT authentication module for AWS Cognito access tokens.
    Handles token validation, JWKS caching, and user context management
  - app/src/context.py - GraphQL context with authenticated user and application
    services. Provides CustomContext class for type-safe access in resolvers

  Tests:
  - app/src/tests/unit/test_auth_config.py - Cognito configuration loading from SSM
  - app/src/tests/unit/test_auth_module.py - JWKS client factory and JWT components
  - app/src/tests/unit/test_jwks_caching.py - JWKS key caching behavior
  - app/src/tests/unit/test_jwt_validation.py - JWT validation FastAPI dependency
  - app/src/tests/unit/test_context.py - CustomContext class and get_context()
  - app/src/tests/integration/test_graphql_auth.py - GraphQL HTTP auth flow
```

**1 tool call.** Without the index, this would require an Explore agent or multiple grep searches.

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

2. Add to your `CLAUDE.md` (global `~/.claude/CLAUDE.md` or project-level):
   ```markdown
   # Writing code

   - All code files should start with a brief 2 line comment explaining what the file does. Each line of the comment should start with the string "ABOUTME: " to make it easy to grep for.
   ```

   **This makes the system self-updating** - Claude will automatically add ABOUTME headers to any new files it creates.

3. Add to your project's `CLAUDE.md` to tell Claude how to use the index:
   ```markdown
   ## File Discovery

   This project has ABOUTME headers in all files. When searching for relevant files,
   read the index at `.claude/aboutme-index.json` instead of using grep or Explore.
   ```

4. Optionally add `.claude/aboutme-index.json` to `.gitignore` (it rebuilds on session start)

## Bootstrapping an Existing Codebase

For projects with existing code that lacks ABOUTME headers, use Claude to help add them:

1. Run the check command to find files missing headers:
   ```bash
   python ~/.claude/skills/aboutme-index/scripts/build_index.py . --check
   ```

2. Ask Claude to add headers to the listed files:
   ```
   These files are missing ABOUTME headers: [paste list]

   For each file, read it and add a 2-line ABOUTME comment at the top
   describing what the file does. Use # for Python/shell/YAML or // for JS/TS.
   ```

3. Claude will read each file, understand its purpose, and add appropriate headers.

4. Re-run `--check` to verify all files are covered, then rebuild the index:
   ```bash
   python ~/.claude/skills/aboutme-index/scripts/build_index.py . -o .claude/aboutme-index.json
   ```

## Hooks Setup

The skill includes two hooks that keep the index automatically updated:

### SessionStart Hook (Full Rebuild)

Rebuilds the entire index when you start a Claude Code session. This catches any changes made outside of Claude (manual edits, git pulls, etc.).

**Location**: `hooks/rebuild-index-on-start.sh`

**Configure in** `~/.claude/settings.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "~/.claude/skills/aboutme-index/hooks/rebuild-index-on-start.sh"
      }
    ]
  }
}
```

### File Edit Hook (Incremental Update)

Updates just the edited file whenever Claude modifies a file. Much faster than a full rebuild.

**Location**: `hooks/update-aboutme-index.sh`

**Configure in** `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "~/.claude/skills/aboutme-index/hooks/update-aboutme-index.sh",
        "tools": ["edit_file", "write_file"]
      }
    ]
  }
}
```

### Combined Configuration

Add both hooks together:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "~/.claude/skills/aboutme-index/hooks/rebuild-index-on-start.sh"
      }
    ],
    "PostToolUse": [
      {
        "type": "command",
        "command": "~/.claude/skills/aboutme-index/hooks/update-aboutme-index.sh",
        "tools": ["edit_file", "write_file"]
      }
    ]
  }
}
```

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
- `.py` - Python (`# ABOUTME:`)
- `.sh` - Shell scripts (`# ABOUTME:`)
- `.yml`, `.yaml` - YAML configs (`# ABOUTME:`)
- `.toml` - TOML configs (`# ABOUTME:`)
- `.js` - JavaScript (`// ABOUTME:`)
- `.ts` - TypeScript (`// ABOUTME:`)
- `.jsx` - React JSX (`// ABOUTME:`)
- `.tsx` - React TSX (`// ABOUTME:`)
