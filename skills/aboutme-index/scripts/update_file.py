#!/usr/bin/env python3
# ABOUTME: Incremental update of ABOUTME index for a single file.
# ABOUTME: Fast alternative to full rebuild - updates only the specified file.

"""
Update the ABOUTME index for a single file.

Usage:
    python update_file.py <file_path> [--index .claude/aboutme-index.json]
"""

import argparse
import sys
from pathlib import Path

from config import should_skip_dir, extract_aboutme, locked_index


def main():
    parser = argparse.ArgumentParser(
        description="Update ABOUTME index for a single file."
    )
    parser.add_argument("file_path", help="Path to the file to index")
    parser.add_argument(
        "--index",
        "-i",
        default=".claude/aboutme-index.json",
        help="Path to the index file (default: .claude/aboutme-index.json)",
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

    with locked_index(index_path) as index:
        if aboutme:
            index[rel_path] = aboutme
            action = "updated"
        elif rel_path in index:
            del index[rel_path]
            action = "removed"
        else:
            action = None

    if action:
        print(f"{action}: {rel_path}")


if __name__ == "__main__":
    main()
