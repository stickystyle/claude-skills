# ABOUTME: LLM-based directory summary generation using claude CLI.
# ABOUTME: Falls back to simple description concatenation when LLM is unavailable.

"""Generate concise directory summaries via claude -p --model haiku."""

import json
import subprocess
from pathlib import Path

PENDING_HASH = "pending"

SYSTEM_PROMPT = (
    "You are a concise technical summarizer. Output ONLY a single summary sentence "
    "(under 120 chars) describing what this directory contains. No markdown, no quotes."
)

BATCH_SYSTEM_PROMPT = (
    "You are a concise technical summarizer. For each directory listed, output a single "
    "summary sentence (under 120 chars) describing what it contains. Output ONLY valid JSON "
    "mapping directory paths to summaries. No markdown, no extra text."
)


def generate_summary(dir_path: str, entries: dict[str, str]) -> tuple[str, bool]:
    """Generate a one-line summary for a directory's contents.

    Args:
        dir_path: The directory path (e.g. "services/tracking")
        entries: {file_path: description} for all files in that directory

    Returns:
        (summary_text, is_llm_generated) tuple.
        If the LLM call fails, returns a fallback summary with is_llm_generated=False.
    """
    file_list = "\n".join(
        f"- {path}: {desc}" for path, desc in sorted(entries.items())
    )
    prompt_input = f"Directory: {dir_path}/\n\nFiles:\n{file_list}"

    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--model", "haiku",
                "--tools", "",
                "--system-prompt", SYSTEM_PROMPT,
                "--setting-sources", "",
                "--no-session-persistence",
                "--output-format", "text",
            ],
            input=prompt_input,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            summary = result.stdout.strip()
            # Ensure it's a single line and reasonable length
            summary = summary.split("\n")[0]
            if len(summary) > 200:
                summary = summary[:197] + "..."
            return (summary, True)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return (_fallback_summary(entries), False)


def _fallback_summary(entries: dict[str, str]) -> str:
    """Generate a fallback summary from the first 3 file descriptions."""
    sorted_entries = sorted(entries.items())
    parts = []
    for _, desc in sorted_entries[:3]:
        # Take first few words of each description
        words = desc.split()
        parts.append(" ".join(words[:6]))
    summary = "; ".join(parts)
    remaining = len(sorted_entries) - 3
    if remaining > 0:
        summary += f"; and {remaining} more files"
    if len(summary) > 200:
        summary = summary[:197] + "..."
    return summary


def generate_summaries_batch(dir_entries: dict[str, dict[str, str]]) -> dict[str, str]:
    """Generate summaries for multiple directories in a single LLM call.

    Args:
        dir_entries: {dir_path: {file_path: description, ...}, ...}

    Returns:
        {dir_path: summary} for all directories. Falls back to individual
        _fallback_summary() for any directory not in the LLM response.
    """
    # Build prompt listing all directories
    parts = []
    for dir_path in sorted(dir_entries.keys()):
        entries = dir_entries[dir_path]
        file_list = ", ".join(
            f"{path}: {desc}" for path, desc in sorted(entries.items())
        )
        parts.append(f"- {dir_path}/: [{file_list}]")
    prompt_input = "Directories:\n" + "\n".join(parts)
    prompt_input += (
        '\n\nOutput format: {"dir_path": "summary", ...}'
    )

    results = {}
    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--model", "haiku",
                "--tools", "",
                "--system-prompt", BATCH_SYSTEM_PROMPT,
                "--setting-sources", "",
                "--no-session-persistence",
                "--output-format", "text",
            ],
            input=prompt_input,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            raw = result.stdout.strip()
            # Extract JSON from response (may have markdown fences)
            if "```" in raw:
                # Strip markdown code fences, keep only content inside
                lines = raw.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                raw = "\n".join(json_lines)
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                for dir_path, summary in parsed.items():
                    if isinstance(summary, str) and summary.strip():
                        s = summary.strip().split("\n")[0]
                        if len(s) > 200:
                            s = s[:197] + "..."
                        results[dir_path] = s
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError,
            json.JSONDecodeError, ValueError):
        pass

    # Fill in fallbacks for any dirs not in the LLM response
    for dir_path, entries in dir_entries.items():
        if dir_path not in results:
            results[dir_path] = _fallback_summary(entries)

    return results


def spawn_background_summary(dir_path: str, project_dir: Path, detail_path: Path) -> None:
    """Spawn a background process to generate an LLM summary for one directory.

    The background process is detached (start_new_session=True) so it survives
    hook timeouts and parent process exit.
    """
    script = Path(__file__).parent / "apply_summary.py"
    subprocess.Popen(
        ["python3", str(script), dir_path, str(project_dir), str(detail_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def spawn_background_batch(dirs_needing_summary: list[str], project_dir: Path) -> None:
    """Spawn a background process to generate LLM summaries for multiple directories.

    The dir list is passed via stdin as JSON. The background process is detached
    so it survives hook timeouts.
    """
    script = Path(__file__).parent / "apply_summaries_batch.py"
    proc = subprocess.Popen(
        ["python3", str(script), str(project_dir)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # Write dir list and close stdin (non-blocking since process is detached)
    proc.stdin.write(json.dumps(dirs_needing_summary).encode("utf-8"))
    proc.stdin.close()
