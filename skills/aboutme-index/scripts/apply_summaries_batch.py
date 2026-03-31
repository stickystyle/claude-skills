#!/usr/bin/env python3
# ABOUTME: Background process to generate and apply LLM summaries for multiple directories.
# ABOUTME: Spawned by build_index.py to batch all directory summaries into one LLM call.

"""Background process that generates LLM summaries for multiple directories in one call."""

import json
import sys
from pathlib import Path

from config import (
    load_index,
    load_top_index,
    save_top_index,
    content_hash,
    detail_dir_path,
    dir_slug,
    _acquire_lock,
)
from summarize import generate_summaries_batch


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    # Read dir list from stdin (JSON)
    dir_list = json.loads(sys.stdin.read())

    if not dir_list:
        return

    detail_dir = detail_dir_path(project_dir)
    dir_entries = {}
    for d in dir_list:
        slug = dir_slug(d)
        detail_path = detail_dir / f"{slug}.md"
        entries = load_index(detail_path)
        if entries:
            dir_entries[d] = entries

    if not dir_entries:
        return

    summaries = generate_summaries_batch(dir_entries)

    # Lock top-level once, update all summaries
    index_path = project_dir / ".claude" / "aboutme-index.md"
    with _acquire_lock(index_path):
        root_entries, dir_summaries = load_top_index(index_path)
        for d, summary in summaries.items():
            slug = dir_slug(d)
            detail_path = detail_dir / f"{slug}.md"
            if detail_path.exists():
                detail_content = detail_path.read_text(encoding="utf-8")
                current_hash = content_hash(detail_content)
                dir_summaries[d] = (summary, current_hash)
        save_top_index(root_entries, dir_summaries, index_path)


if __name__ == "__main__":
    main()
