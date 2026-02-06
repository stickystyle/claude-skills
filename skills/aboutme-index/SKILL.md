---
name: aboutme-index
model: haiku
description: Index-based file discovery using ABOUTME headers. Use INSTEAD of grep or Explore agent when searching for files by purpose or feature. Faster and more accurate than scanning code. Invoke this skill when user asks "which files handle X", "where is Y implemented", or when you need to find files related to a feature or task.
---

# ABOUTME Index

This is a read-only lookup skill. Use the Read tool to find files by purpose.

## Usage

1. Read the top-level directory overview:
   - Read `.claude/aboutme-index.md`

2. Find the relevant directory, convert its slug (`/` becomes `--`), and read the detail file:
   - `services/tracking/` -> Read `.claude/aboutme-index/services--tracking.md`
   - `db/` -> Read `.claude/aboutme-index/db.md`

3. Read the specific source files you need.

## Slug Conversion

Directory paths map to detail filenames by replacing `/` with `--`:
- `services/tracking/` -> `services--tracking.md`
- `db/migrations/versions/` -> `db--migrations--versions.md`
- `db/` -> `db.md`

## Commands

| Command | Description |
|---------|-------------|
| `/aboutme-check` | Find files missing ABOUTME headers |
| `/aboutme-rebuild` | Rebuild the entire index |
| `/aboutme-stale` | Check for stale headers |

## Index Format

### Top-level index (directory summaries)

```markdown
<!-- ABOUTME Index: directory summaries. For file-level detail, read .claude/aboutme-index/<slug>.md -->
- `celery_app.py`: Celery application entry point Configures task queues and worker settings
- `main.py`: FastAPI application entry point Mounts domain routers and configures middleware
- `db/`: SQLAlchemy models, async sessions, enums, and Alembic migrations <!-- hash:a1b2c3d4e5f6a1b2 -->
- `services/tracking/`: Shipment tracking with registration, polling, webhooks <!-- hash:e5f6a1b2c3d4e5f6 -->
```

Root files (no trailing `/`) appear inline. Directories (trailing `/`) have summaries. Ignore `<!-- hash:... -->` comments.

### Detail files (per-file entries)

```markdown
- `services/tracking/api.py`: FastAPI router for tracking/shipment endpoints
- `services/tracking/service.py`: Business logic for shipment tracking
```

The index auto-rebuilds on session start and updates incrementally on file edits.
