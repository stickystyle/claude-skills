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

Semantic file discovery using ABOUTME headers. Instead of grep-searching or spawning Explore agents, this skill maintains a JSON index of human-written file descriptions.

**How it works:**

1. Add ABOUTME comments to your files:
   ```python
   # ABOUTME: JWT authentication module for AWS Cognito access tokens.
   # ABOUTME: Handles token validation, JWKS caching, and user context.
   ```

2. The index auto-rebuilds on session start

3. Claude reads one file to find what you need

[Full documentation](skills/aboutme-index/README.md)

## License

MIT
