"""Search and discovery tools for finding code and files.

This module provides search tools matching Claude Code's behavior:
- Glob tool: Fast file pattern matching with glob patterns
- Grep tool: Powerful content search with regex support
"""

import os
import re
from pathlib import Path
from typing import Any, Optional

from ._tool_helpers import beta_tool


# ============================================================================
# Glob Tool
# ============================================================================


@beta_tool
def glob_files(
    pattern: str,
    path: Optional[str] = None,
) -> dict[str, Any]:
    """Fast file pattern matching tool.

    Find files by name patterns using glob syntax. Supports recursive
    patterns like "**/*.py" and returns matches sorted by modification time.

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "src/**/*.ts")
        path: Directory to search in (default: current working directory)

    Returns:
        Dictionary containing matched file paths or error message
    """
    try:
        # Determine search directory
        if path:
            search_path = Path(path)
        else:
            search_path = Path.cwd()

        # Validate path
        if not search_path.exists():
            return {
                "error": f"Directory not found: {path}",
                "pattern": pattern,
            }

        if not search_path.is_dir():
            return {
                "error": f"Path is not a directory: {path}",
                "pattern": pattern,
            }

        # Perform glob search
        matches = list(search_path.glob(pattern))

        # Filter out directories, keep only files
        file_matches = [m for m in matches if m.is_file()]

        # Sort by modification time (most recent first)
        file_matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Convert to absolute paths
        file_paths = [str(p.absolute()) for p in file_matches]

        return {
            "pattern": pattern,
            "search_path": str(search_path.absolute()),
            "matches": file_paths,
            "count": len(file_paths),
        }

    except Exception as e:
        return {
            "error": f"Glob search failed: {e!s}",
            "pattern": pattern,
        }


# ============================================================================
# Grep Tool
# ============================================================================


@beta_tool
def grep_code(
    pattern: str,
    path: Optional[str] = None,
    glob: Optional[str] = None,
    type: Optional[str] = None,
    case_insensitive: bool = False,
    multiline: bool = False,
    context_before: int = 0,
    context_after: int = 0,
    output_mode: str = "files_with_matches",
    head_limit: Optional[int] = None,
    offset: int = 0,
) -> dict[str, Any]:
    """Powerful code search tool with regex support.

    Search file contents using regex patterns. Supports filtering by file type,
    multiline matching, context lines, and different output modes.

    Args:
        pattern: Regular expression pattern to search for
        path: File or directory to search in (default: current working directory)
        glob: Glob pattern to filter files (e.g., "*.py", "*.{ts,tsx}")
        type: File type to search (e.g., "py", "js", "rust")
        case_insensitive: Case insensitive search (default: False)
        multiline: Enable multiline mode where . matches newlines (default: False)
        context_before: Number of lines to show before each match
        context_after: Number of lines to show after each match
        output_mode: Output format - "content", "files_with_matches", or "count"
        head_limit: Limit output to first N results
        offset: Skip first N results

    Returns:
        Dictionary containing search results or error message
    """
    try:
        # Determine search directory
        if path:
            search_path = Path(path)
        else:
            search_path = Path.cwd()

        # Validate path
        if not search_path.exists():
            return {
                "error": f"Path not found: {path}",
                "pattern": pattern,
            }

        # File type extensions mapping
        type_extensions = {
            "py": ["*.py"],
            "js": ["*.js", "*.jsx"],
            "ts": ["*.ts", "*.tsx"],
            "rust": ["*.rs"],
            "go": ["*.go"],
            "java": ["*.java"],
            "c": ["*.c", "*.h"],
            "cpp": ["*.cpp", "*.hpp", "*.cc", "*.hh"],
            "rb": ["*.rb"],
            "php": ["*.php"],
            "html": ["*.html", "*.htm"],
            "css": ["*.css"],
            "md": ["*.md"],
            "json": ["*.json"],
            "yaml": ["*.yaml", "*.yml"],
            "toml": ["*.toml"],
        }

        # Determine files to search
        if search_path.is_file():
            files_to_search = [search_path]
        else:
            # Build glob pattern
            if type and type in type_extensions:
                patterns = type_extensions[type]
            elif glob:
                # Handle brace expansion patterns like *.{js,jsx}
                if '{' in glob and '}' in glob:
                    # Manual brace expansion
                    import re as re_module
                    brace_pattern = r'\{([^}]+)\}'
                    match = re_module.search(brace_pattern, glob)
                    if match:
                        expansions = match.group(1).split(',')
                        patterns = [glob.replace(match.group(0), exp) for exp in expansions]
                    else:
                        patterns = [glob]
                else:
                    patterns = [glob]
            else:
                patterns = ["**/*"]

            files_to_search = []
            for pat in patterns:
                matches = search_path.rglob(pat) if "**" in pat else search_path.glob(pat)
                files_to_search.extend([m for m in matches if m.is_file()])

        # Compile regex pattern
        flags = re.IGNORECASE if case_insensitive else 0
        if multiline:
            flags |= re.MULTILINE | re.DOTALL

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return {
                "error": f"Invalid regex pattern: {e!s}",
                "pattern": pattern,
            }

        # Perform search based on output mode
        if output_mode == "files_with_matches":
            results = _grep_files_with_matches(files_to_search, regex, head_limit, offset)
        elif output_mode == "count":
            results = _grep_count(files_to_search, regex, head_limit, offset)
        elif output_mode == "content":
            results = _grep_content(
                files_to_search,
                regex,
                context_before,
                context_after,
                head_limit,
                offset,
                multiline,
            )
        else:
            return {
                "error": f"Invalid output_mode: {output_mode}",
                "pattern": pattern,
            }

        return {
            "pattern": pattern,
            "search_path": str(search_path.absolute()),
            "output_mode": output_mode,
            **results,
        }

    except Exception as e:
        return {
            "error": f"Grep search failed: {e!s}",
            "pattern": pattern,
        }


def _grep_files_with_matches(
    files: list[Path],
    regex: re.Pattern[str],
    head_limit: Optional[int],
    offset: int,
) -> dict[str, Any]:
    """Find files that contain matches."""
    matching_files = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if regex.search(content):
                    matching_files.append(str(file_path.absolute()))
        except Exception:
            continue

    # Apply offset and head_limit
    total = len(matching_files)
    matching_files = matching_files[offset:]
    if head_limit:
        matching_files = matching_files[:head_limit]

    return {
        "matching_files": matching_files,
        "total_matches": total,
        "shown_matches": len(matching_files),
    }


def _grep_count(
    files: list[Path],
    regex: re.Pattern[str],
    head_limit: Optional[int],
    offset: int,
) -> dict[str, Any]:
    """Count matches per file."""
    counts = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                match_count = len(regex.findall(content))
                if match_count > 0:
                    counts.append({
                        "file": str(file_path.absolute()),
                        "count": match_count,
                    })
        except Exception:
            continue

    # Sort by count (descending)
    counts.sort(key=lambda x: x["count"], reverse=True)

    # Apply offset and head_limit
    total = len(counts)
    counts = counts[offset:]
    if head_limit:
        counts = counts[:head_limit]

    return {
        "match_counts": counts,
        "total_files": total,
        "shown_files": len(counts),
    }


def _grep_content(
    files: list[Path],
    regex: re.Pattern[str],
    context_before: int,
    context_after: int,
    head_limit: Optional[int],
    offset: int,
    multiline: bool,
) -> dict[str, Any]:
    """Get matching lines with context."""
    all_matches = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                if multiline:
                    # Multiline mode: search entire content
                    content = f.read()
                    for match in regex.finditer(content):
                        # Find line number
                        line_num = content[:match.start()].count("\n") + 1
                        all_matches.append({
                            "file": str(file_path.absolute()),
                            "line": line_num,
                            "content": match.group(),
                        })
                else:
                    # Line-by-line mode
                    lines = f.readlines()
                    for i, line in enumerate(lines, start=1):
                        if regex.search(line):
                            # Gather context
                            start_ctx = max(0, i - 1 - context_before)
                            end_ctx = min(len(lines), i + context_after)
                            context_lines = lines[start_ctx:end_ctx]

                            # Format with line numbers
                            formatted = []
                            for j, ctx_line in enumerate(context_lines, start=start_ctx + 1):
                                prefix = f"{j:6d}:"
                                formatted.append(f"{prefix} {ctx_line.rstrip()}")

                            all_matches.append({
                                "file": str(file_path.absolute()),
                                "line": i,
                                "content": "\n".join(formatted),
                            })
        except Exception:
            continue

    # Apply offset and head_limit
    total = len(all_matches)
    all_matches = all_matches[offset:]
    if head_limit:
        all_matches = all_matches[:head_limit]

    return {
        "matches": all_matches,
        "total_matches": total,
        "shown_matches": len(all_matches),
    }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_search_tools() -> list[dict[str, Any]]:
    """Get all search tool definitions.

    Returns:
        List of search tool definitions for use with Devorbit client
    """
    return [
        glob_files.tool_definition,  # type: ignore[attr-defined]
        grep_code.tool_definition,  # type: ignore[attr-defined]
    ]


# Export tool instances for direct use
__all__ = [
    "glob_files",
    "grep_code",
    "get_all_search_tools",
]
