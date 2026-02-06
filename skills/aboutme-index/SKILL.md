---
name: aboutme-index
description: Index-based file discovery using ABOUTME headers. Use INSTEAD of grep or Explore agent when searching for files by purpose or feature. Faster and more accurate than scanning code. Invoke this skill when user asks "which files handle X", "where is Y implemented", or when you need to find files related to a feature or task.
---

# ABOUTME Index

Read `.claude/aboutme-index.md` to find files by purpose instead of grep-searching.

## Usage

1. Read the directory overview:
```bash
cat .claude/aboutme-index.md
```

2. Find the relevant directory, then read its detail file:
```bash
cat .claude/aboutme-index/services--tracking.md
```

3. Read the specific source files you need.

## Commands

| Command | Description |
|---------|-------------|
| `/aboutme-check` | Find files missing ABOUTME headers |
| `/aboutme-rebuild` | Rebuild the entire index |
| `/aboutme-stale` | Check for stale headers |
| `cat .claude/aboutme-index.md` | Read the top-level directory overview |
| `cat .claude/aboutme-index/<slug>.md` | Read detail file for a specific directory |

## Index Format

### Top-level index (directory summaries)

```markdown
<!-- ABOUTME Index: directory summaries. For file-level detail, read .claude/aboutme-index/<slug>.md -->
- `celery_app.py`: Celery application entry point Configures task queues and worker settings
- `main.py`: FastAPI application entry point Mounts domain routers and configures middleware
- `db/`: SQLAlchemy models, async sessions, enums, and Alembic migrations <!-- hash:a1b2c3d4e5f6a1b2 -->
- `services/tracking/`: Shipment tracking with registration, polling, webhooks <!-- hash:e5f6a1b2c3d4e5f6 -->
```

### Detail files (per-file entries)

```markdown
- `services/tracking/api.py`: FastAPI router for tracking/shipment endpoints
- `services/tracking/service.py`: Business logic for shipment tracking
```

Directory slugs use `--` as separator: `services/tracking/` -> `services--tracking.md`

The index is auto-rebuilt on session start and updated incrementally on file edits.
