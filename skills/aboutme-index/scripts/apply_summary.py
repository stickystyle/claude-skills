#!/usr/bin/env python3
# ABOUTME: Background process to generate and apply an LLM summary for one directory.
# ABOUTME: Spawned by update_file.py when a directory's content hash changes.

"""Background process that generates an LLM summary and writes it to the top-level index."""

import sys
from pathlib import Path

from config import load_index, load_top_index, save_top_index, content_hash, _acquire_lock
from summarize import generate_summary


def main():
    if len(sys.argv) < 4:
        sys.exit(1)

    dir_path = sys.argv[1]
    project_dir = Path(sys.argv[2])
    detail_path = Path(sys.argv[3])
    index_path = project_dir / ".claude" / "aboutme-index.md"

    entries = load_index(detail_path)
    if not entries:
        return

    summary, is_llm = generate_summary(dir_path, entries)
    if not is_llm:
        return  # Don't overwrite fallback with another fallback

    # Lock top-level, update just this dir's summary
    with _acquire_lock(index_path):
        root_entries, dir_summaries = load_top_index(index_path)
        detail_content = detail_path.read_text(encoding="utf-8")
        current_hash = content_hash(detail_content)
        dir_summaries[dir_path] = (summary, current_hash)
        save_top_index(root_entries, dir_summaries, index_path)


if __name__ == "__main__":
    main()
