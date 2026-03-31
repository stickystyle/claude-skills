#!/usr/bin/env python3
# ABOUTME: Script to build an index of ABOUTME headers from all files.
# ABOUTME: Outputs markdown with file paths and their descriptions for quick lookup.

"""
Build an index of ABOUTME headers from all files in a project.

Usage:
    python build_index.py [directory] [--output index.md]
    python build_index.py [directory] --check  # List files missing ABOUTME headers
    python build_index.py [directory] --stale  # Check if index is stale
"""

import argparse
import os
import sys
from pathlib import Path

from config import (
    should_skip_dir,
    extract_aboutme,
    format_index_line,
    group_by_directory,
    content_hash,
    dir_slug,
    detail_dir_path,
    load_top_index,
    save_top_index,
    save_index,
    _acquire_lock,
)
from summarize import _fallback_summary, spawn_background_batch

# File extensions that should have ABOUTME headers
ABOUTME_EXTENSIONS = {".py", ".sh", ".yml", ".yaml", ".toml", ".js", ".ts", ".jsx", ".tsx"}

# Default index path
DEFAULT_INDEX = ".claude/aboutme-index.md"


def build_index(root_dir: Path) -> dict:
    """Build an index of all ABOUTME headers in files."""
    index = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            aboutme = extract_aboutme(file_path)

            if aboutme:
                rel_path = file_path.relative_to(root_dir)
                index[str(rel_path)] = aboutme

    return index


def find_files_missing_aboutme(root_dir: Path) -> list[str]:
    """Find files that should have ABOUTME headers but don't."""
    missing = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            ext = file_path.suffix.lower()

            if ext not in ABOUTME_EXTENSIONS:
                continue

            aboutme = extract_aboutme(file_path)
            if not aboutme:
                rel_path = file_path.relative_to(root_dir)
                missing.append(str(rel_path))

    return sorted(missing)


def check_staleness(root_dir: Path, index_path: Path) -> tuple[bool, str]:
    """Check if index is stale by comparing mtimes.

    Returns (is_stale, message).
    """
    if not index_path.exists():
        return True, "Index does not exist"

    index_mtime = index_path.stat().st_mtime
    newest_file = None
    newest_mtime = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path.suffix.lower() not in ABOUTME_EXTENSIONS:
                continue
            try:
                mtime = file_path.stat().st_mtime
                if mtime > newest_mtime:
                    newest_mtime = mtime
                    newest_file = file_path.relative_to(root_dir)
            except OSError:
                continue

    if newest_mtime > index_mtime:
        return True, f"Index is stale. Newest file: {newest_file}"

    return False, "Index is up to date"


def build_tiered_index(root_dir: Path, output_path: Path, no_summaries: bool = False, flat_index: dict | None = None) -> None:
    """Build a two-tier ABOUTME index with directory summaries and detail files.

    Top-level index at output_path gets directory summaries + inline root files.
    Detail files go into the sibling aboutme-index/ directory.
    """
    if flat_index is None:
        flat_index = build_index(root_dir)
    groups = group_by_directory(flat_index)

    detail_dir = detail_dir_path(root_dir)
    detail_dir.mkdir(parents=True, exist_ok=True)

    # Load existing top-level index for hash comparison
    existing_root, existing_dirs = load_top_index(output_path)

    root_entries = {}
    dir_summaries = {}
    active_slugs = set()
    dirs_needing_summary = []

    for dir_key, entries in groups.items():
        if dir_key == "":
            # Root files go inline in top-level
            root_entries.update(entries)
            continue

        # Write detail file
        slug = dir_slug(dir_key)
        active_slugs.add(slug)
        detail_path = detail_dir / f"{slug}.md"
        save_index(entries, detail_path)

        # Compute hash of detail file content
        detail_content = detail_path.read_text(encoding="utf-8")
        new_hash = content_hash(detail_content)

        # Check if summary needs regeneration
        existing = existing_dirs.get(dir_key)
        if existing and existing[1] == new_hash:
            # Hash matches - keep existing (possibly LLM) summary
            dir_summaries[dir_key] = existing
        else:
            # Hash changed or new dir - write fallback summary immediately
            summary = _fallback_summary(entries)
            dir_summaries[dir_key] = (summary, new_hash)
            dirs_needing_summary.append(dir_key)

    # Clean up orphaned detail files
    for existing_file in detail_dir.iterdir():
        if existing_file.suffix == ".md" and existing_file.stem not in active_slugs:
            existing_file.unlink()

    # Write top-level index (locked)
    with _acquire_lock(output_path):
        save_top_index(root_entries, dir_summaries, output_path)

    # Spawn background process to generate LLM summaries
    if not no_summaries and dirs_needing_summary:
        spawn_background_batch(dirs_needing_summary, root_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Build an index of ABOUTME headers from all files."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--check",
        "-c",
        action="store_true",
        help="List files missing ABOUTME headers",
    )
    parser.add_argument(
        "--stale",
        "-s",
        action="store_true",
        help="Check if index is stale (files newer than index)",
    )
    parser.add_argument(
        "--no-summaries",
        action="store_true",
        help="Skip LLM summary generation (use fallback summaries)",
    )

    args = parser.parse_args()

    root_dir = Path(args.directory).resolve()
    if not root_dir.is_dir():
        print(f"Error: {root_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    if args.stale:
        index_path = root_dir / DEFAULT_INDEX
        is_stale, message = check_staleness(root_dir, index_path)
        print(message)
        sys.exit(1 if is_stale else 0)

    if args.check:
        missing = find_files_missing_aboutme(root_dir)
        if missing:
            print("These files are missing ABOUTME headers:\n")
            for path in missing:
                print(f"  {path}")
            print(
                "\nFor each file, read it and add a 2-line ABOUTME comment at the top "
                "describing what the file does. Use # for Python/shell/YAML or // for JS/TS."
            )
            sys.exit(1)
        else:
            print("All files have ABOUTME headers.")
            sys.exit(0)

    index = build_index(root_dir)

    if args.output:
        output_path = Path(args.output)
        build_tiered_index(root_dir, output_path, no_summaries=args.no_summaries, flat_index=index)
        print(f"Index written to {args.output} ({len(index)} files)")
    else:
        for path in sorted(index.keys()):
            print(format_index_line(path, index[path]))


if __name__ == "__main__":
    main()
