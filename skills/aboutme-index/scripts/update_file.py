#!/usr/bin/env python3
# ABOUTME: Incremental update of ABOUTME index for a single file.
# ABOUTME: Updates the two-tier index: detail file first, then top-level summary.

"""
Update the ABOUTME index for a single file.

Usage:
    python update_file.py <file_path> [--index .claude/aboutme-index.md]
"""

import argparse
import sys
from pathlib import Path

from config import (
    should_skip_dir,
    extract_aboutme,
    load_index,
    save_index,
    content_hash,
    dir_slug,
    detail_dir_path,
    load_top_index,
    save_top_index,
    _acquire_lock,
)
from summarize import generate_summary, PENDING_HASH


def _parent_dir_key(rel_path: str) -> str:
    """Get the parent directory key for a file path.

    Returns "" for root-level files, or the parent directory path.
    """
    parts = Path(rel_path).parts
    if len(parts) <= 1:
        return ""
    return str(Path(*parts[:-1]))


def main():
    parser = argparse.ArgumentParser(
        description="Update ABOUTME index for a single file."
    )
    parser.add_argument("file_path", help="Path to the file to index")
    parser.add_argument(
        "--index",
        "-i",
        default=".claude/aboutme-index.md",
        help="Path to the index file (default: .claude/aboutme-index.md)",
    )
    parser.add_argument(
        "--project-dir",
        "-p",
        help="Project root directory (for computing relative paths)",
    )

    args = parser.parse_args()

    file_path = Path(args.file_path).resolve()

    # Determine project directory
    if args.project_dir:
        project_dir = Path(args.project_dir).resolve()
    else:
        # Try to find project root by looking for .claude or .git
        project_dir = file_path.parent
        while project_dir != project_dir.parent:
            if (project_dir / ".claude").exists() or (project_dir / ".git").exists():
                break
            project_dir = project_dir.parent
        else:
            project_dir = Path.cwd()

    index_path = project_dir / args.index

    # Compute relative path from project root
    try:
        rel_path = str(file_path.relative_to(project_dir))
    except ValueError:
        rel_path = str(file_path)

    # Skip files in excluded directories
    if any(should_skip_dir(part) for part in Path(rel_path).parts):
        sys.exit(0)

    aboutme = extract_aboutme(file_path)
    dir_key = _parent_dir_key(rel_path)

    if dir_key == "":
        # Root file: update inline in top-level index
        with _acquire_lock(index_path):
            root_entries, dir_summaries = load_top_index(index_path)
            if aboutme:
                root_entries[rel_path] = aboutme
                action = "updated"
            elif rel_path in root_entries:
                del root_entries[rel_path]
                action = "removed"
            else:
                action = None
            if action:
                save_top_index(root_entries, dir_summaries, index_path)
    else:
        # Subdir file: update detail file first, then top-level
        detail_dir = detail_dir_path(project_dir)
        detail_dir.mkdir(parents=True, exist_ok=True)
        slug = dir_slug(dir_key)
        detail_path = detail_dir / f"{slug}.md"

        # Lock detail file, update entry
        with _acquire_lock(detail_path):
            detail_index = load_index(detail_path)
            if aboutme:
                detail_index[rel_path] = aboutme
                action = "updated"
            elif rel_path in detail_index:
                del detail_index[rel_path]
                action = "removed"
            else:
                action = None

            if action:
                if detail_index:
                    save_index(detail_index, detail_path)
                elif detail_path.exists():
                    detail_path.unlink()

        if not action:
            sys.exit(0)

        # Now lock top-level and update summary
        with _acquire_lock(index_path):
            root_entries, dir_summaries = load_top_index(index_path)

            if not detail_index:
                # Directory is now empty - remove from top-level
                dir_summaries.pop(dir_key, None)
            else:
                # Compute new hash
                detail_content = detail_path.read_text(encoding="utf-8")
                new_hash = content_hash(detail_content)

                existing = dir_summaries.get(dir_key)
                if not existing or existing[1] != new_hash:
                    # Hash changed - regenerate summary
                    summary, is_llm = generate_summary(dir_key, detail_index)
                    if is_llm:
                        dir_summaries[dir_key] = (summary, new_hash)
                    else:
                        dir_summaries[dir_key] = (summary, PENDING_HASH)

            save_top_index(root_entries, dir_summaries, index_path)

    if action:
        print(f"{action}: {rel_path}")


if __name__ == "__main__":
    main()
