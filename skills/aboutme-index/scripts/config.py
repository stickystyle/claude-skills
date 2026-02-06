# ABOUTME: Shared configuration and utilities for ABOUTME index scripts.
# ABOUTME: Contains excluded directories, extraction logic, and index I/O functions.

import fcntl
import hashlib
import re
from contextlib import contextmanager
from pathlib import Path

EXCLUDED_DIRS = {
    ".venv",
    "venv",
    ".env",
    "node_modules",
    "__pycache__",
    ".git",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "cdk.out",
}

EXCLUDED_SUFFIXES = {
    ".egg-info",
}


def should_skip_dir(dir_name: str) -> bool:
    """Check if a directory should be skipped."""
    if dir_name in EXCLUDED_DIRS:
        return True
    return any(dir_name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)


def escape_backticks(path: str) -> str:
    """Escape backticks in a path for markdown inline code."""
    return path.replace("`", "\\`")


def unescape_backticks(path: str) -> str:
    """Unescape backticks in a path from markdown inline code."""
    return path.replace("\\`", "`")


def format_index_line(path: str, description: str) -> str:
    """Format a single index entry as a markdown line."""
    escaped_path = escape_backticks(path)
    return f"- `{escaped_path}`: {description}"


def parse_index_line(line: str) -> tuple[str, str] | None:
    """Parse a markdown index line back to (path, description) tuple.

    Returns None if the line doesn't match the expected format.
    """
    line = line.strip()
    if not line.startswith("- `"):
        return None

    # Find the closing backtick, handling escaped backticks
    i = 3  # Start after "- `"
    while i < len(line):
        if line[i] == "`" and (i == 0 or line[i - 1] != "\\"):
            break
        i += 1
    else:
        return None

    path = unescape_backticks(line[3:i])

    # Skip "`: " after the backtick
    rest = line[i + 1 :]
    if not rest.startswith(": "):
        return None

    description = rest[2:]
    return (path, description)


def extract_aboutme(file_path: Path) -> str | None:
    """Extract ABOUTME lines from the first two lines of a file."""
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            aboutme_lines = []
            for i, line in enumerate(f):
                if i >= 2:
                    break
                match = re.match(r"^(?:#|//)\s*ABOUTME:\s*(.+)$", line.strip())
                if match:
                    aboutme_lines.append(match.group(1))

            return " ".join(aboutme_lines) if aboutme_lines else None
    except (IOError, UnicodeDecodeError):
        return None


def load_index(index_path: Path) -> dict:
    """Load existing index from markdown format or return empty dict."""
    if index_path.exists():
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                index = {}
                for line in f:
                    parsed = parse_index_line(line)
                    if parsed:
                        path, description = parsed
                        index[path] = description
                return index
        except IOError:
            return {}
    return {}


def save_index(index: dict, index_path: Path) -> None:
    """Save index to file in markdown format."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        for path in sorted(index.keys()):
            f.write(format_index_line(path, index[path]) + "\n")


def _get_lock_path(index_path: Path) -> Path:
    """Return the lock file path for a given index path."""
    return index_path.with_suffix(".lock")


@contextmanager
def _acquire_lock(index_path: Path):
    """Context manager that acquires an exclusive lock on the index."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = _get_lock_path(index_path)

    with open(lock_path, "w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


@contextmanager
def locked_index(index_path: Path):
    """Context manager for atomic index updates with file locking.

    Acquires an exclusive lock before reading, holds it through modification,
    and releases after writing. Prevents race conditions when multiple
    processes update the index concurrently.

    Usage:
        with locked_index(index_path) as index:
            index["file.py"] = "description"
        # Index is automatically saved on context exit
    """
    with _acquire_lock(index_path):
        index = load_index(index_path)
        yield index
        save_index(index, index_path)


def locked_save_index(index: dict, index_path: Path) -> None:
    """Save index to file with exclusive locking.

    Use this for full index rebuilds where read-modify-write isn't needed.
    """
    with _acquire_lock(index_path):
        save_index(index, index_path)


# --- Two-tier index utilities ---


def dir_slug(dir_path: str) -> str:
    """Convert a directory path to a slug for detail file naming.

    "" -> "_root", "db" -> "db", "services/tracking" -> "services--tracking"
    """
    if not dir_path:
        return "_root"
    return dir_path.rstrip("/").replace("/", "--")


def detail_dir_path(project_dir: Path) -> Path:
    """Return the path to the detail files directory."""
    return project_dir / ".claude" / "aboutme-index"


def group_by_directory(index: dict) -> dict[str, dict]:
    """Group a flat {path: desc} index by parent directory.

    Root files (no directory component) are grouped under "".
    """
    groups: dict[str, dict] = {}
    for path, desc in index.items():
        parts = Path(path).parts
        if len(parts) <= 1:
            dir_key = ""
        else:
            dir_key = str(Path(*parts[:-1]))
        groups.setdefault(dir_key, {})[path] = desc
    return groups


def content_hash(text: str) -> str:
    """Return first 16 hex chars of SHA-256 hash of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def format_summary_line(dir_path: str, summary: str, hash_val: str) -> str:
    """Format a directory summary line for the top-level index."""
    escaped = escape_backticks(dir_path.rstrip("/") + "/")
    return f"- `{escaped}`: {summary} <!-- hash:{hash_val} -->"


def parse_summary_line(line: str) -> tuple[str, str, str | None] | None:
    """Parse a top-level index line into (path, description, hash_or_none).

    Handles both root file entries (no hash) and directory summary entries (with hash).
    Returns None if the line doesn't match expected format.
    """
    line = line.strip()
    if not line.startswith("- `"):
        return None

    # Find the closing backtick, handling escaped backticks
    i = 3
    while i < len(line):
        if line[i] == "`" and (i == 0 or line[i - 1] != "\\"):
            break
        i += 1
    else:
        return None

    path = unescape_backticks(line[3:i])

    rest = line[i + 1:]
    if not rest.startswith(": "):
        return None

    desc_part = rest[2:]

    # Check for hash comment
    hash_match = re.search(r"\s*<!-- hash:(\S+) -->$", desc_part)
    if hash_match:
        hash_val = hash_match.group(1)
        desc = desc_part[:hash_match.start()]
        return (path, desc, hash_val)

    return (path, desc_part, None)


TOP_INDEX_HEADER = "<!-- ABOUTME Index: directory summaries. For file-level detail, read .claude/aboutme-index/<slug>.md -->\n"


def load_top_index(path: Path) -> tuple[dict, dict]:
    """Load the top-level index file.

    Returns (root_entries, dir_summaries) where:
      root_entries: {file_path: description} for inline root files
      dir_summaries: {dir_path: (summary, hash)} for directory entries
    """
    root_entries = {}
    dir_summaries = {}

    if not path.exists():
        return root_entries, dir_summaries

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parsed = parse_summary_line(line)
                if not parsed:
                    continue
                entry_path, desc, hash_val = parsed
                if entry_path.endswith("/"):
                    # Directory entry
                    dir_summaries[entry_path.rstrip("/")] = (desc, hash_val or "")
                else:
                    # Root file entry
                    root_entries[entry_path] = desc
    except IOError:
        pass

    return root_entries, dir_summaries


def save_top_index(root_entries: dict, dir_summaries: dict, path: Path) -> None:
    """Write the top-level index file.

    root_entries: {file_path: description} for inline root files
    dir_summaries: {dir_path: (summary, hash)} for directory entries
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(TOP_INDEX_HEADER)
        # Root file entries first, sorted
        for file_path in sorted(root_entries.keys()):
            f.write(format_index_line(file_path, root_entries[file_path]) + "\n")
        # Directory summaries, sorted
        for dir_path in sorted(dir_summaries.keys()):
            summary, hash_val = dir_summaries[dir_path]
            f.write(format_summary_line(dir_path, summary, hash_val) + "\n")
