# ABOUTME: LLM-based directory summary generation using claude CLI.
# ABOUTME: Falls back to simple description concatenation when LLM is unavailable.

"""Generate concise directory summaries via claude -p --model haiku."""

import subprocess

PENDING_HASH = "pending"

SYSTEM_PROMPT = (
    "You are a concise technical summarizer. Output ONLY a single summary sentence "
    "(under 120 chars) describing what this directory contains. No markdown, no quotes."
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
