#!/usr/bin/env python3
# ABOUTME: Script to build an index of ABOUTME headers from all files.
# ABOUTME: Outputs JSON with file paths and their descriptions for quick lookup.

"""
Build an index of ABOUTME headers from all files in a project.

Usage:
    python build_index.py [directory] [--output index.json]
    python build_index.py [directory] --check  # List files missing ABOUTME headers
    python build_index.py [directory] --stale  # Check if index is stale
"""

import argparse
import json
import os
import sys
from pathlib import Path

from config import should_skip_dir, extract_aboutme, save_index

# File extensions that should have ABOUTME headers
ABOUTME_EXTENSIONS = {".py", ".sh", ".yml", ".yaml", ".toml"}

# Default index path
DEFAULT_INDEX = ".claude/aboutme-index.json"


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
            print(f"Files missing ABOUTME headers ({len(missing)}):\n")
            for path in missing:
                print(f"  {path}")
            sys.exit(1)
        else:
            print("All files have ABOUTME headers.")
            sys.exit(0)

    index = build_index(root_dir)

    if args.output:
        save_index(index, Path(args.output))
        print(f"Index written to {args.output} ({len(index)} files)")
    else:
        print(json.dumps(index, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
