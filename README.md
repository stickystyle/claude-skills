# Claude Skills

A collection of Claude Code skills by Ryan Parrish.

## Installation

```bash
# Add the marketplace
/plugin marketplace add stickystyle/claude-skills

# Install a specific skill
/plugin install aboutme-index@stickystyle-skills
```

## Available Skills

### aboutme-index

Semantic file discovery using ABOUTME headers. Instead of grep-searching or spawning Explore agents, this skill maintains an index of human-written file descriptions.

**How it works:**

1. Add ABOUTME comments to your files:
   ```python
   # ABOUTME: JWT authentication module for AWS Cognito access tokens.
   # ABOUTME: Handles token validation, JWKS caching, and user context.
   ```

2. The index auto-rebuilds on session start

3. Claude reads one file to find what you need

[Full documentation](skills/aboutme-index/README.md)

### uv

Python package manager and project tooling using [uv](https://docs.astral.sh/uv/). Provides Claude with a field manual for working with Python projects, managing dependencies, virtual environments, workspaces, and more.

### markdown-oxide-lsp

Configures the [markdown-oxide](https://github.com/Feel-ix-343/markdown-oxide) language server for Markdown and Obsidian vault intelligence. Provides wikilink completion, hover info, goto-definition, and diagnostics for Markdown files.

## License

MIT
