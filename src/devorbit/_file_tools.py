"""File operation tools for autonomous coding agents.

This module provides file manipulation tools matching Claude Code's behavior:
- Read tool: Read files with line numbers and offset/limit support
- Write tool: Create files with safety checks
- Edit tool: Exact string replacement editing
- MultiEdit tool: Batch file editing operations
"""

import os
from pathlib import Path
from typing import Any

from ._tool_helpers import beta_tool


# Constants
MAX_LINE_LENGTH = 2000  # Maximum characters per line before truncation


# ============================================================================
# Helper Functions
# ============================================================================


def _validate_file_for_editing(file_path: str, require_write: bool = True) -> dict[str, Any] | None:
    """Validate that a file exists and is accessible for editing.

    Args:
        file_path: Path to validate
        require_write: Whether write permission is required

    Returns:
        Error dict if validation fails, None if valid
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "error": f"File not found: {file_path}",
            "file_path": file_path,
        }

    if not path.is_file():
        return {
            "error": f"Path is not a file: {file_path}",
            "file_path": file_path,
        }

    # Check permissions
    required_access = os.R_OK | os.W_OK if require_write else os.R_OK
    if not os.access(path, required_access):
        return {
            "error": f"Permission denied: {file_path}",
            "file_path": file_path,
        }

    return None


# ============================================================================
# Read Tool
# ============================================================================


@beta_tool
def read_file(
    file_path: str,
    offset: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Read a file from the local filesystem.

    Reads files with line numbers (cat -n format). Supports reading portions
    of large files using offset and limit parameters. Line numbers start at 1.

    Args:
        file_path: Absolute path to the file to read
        offset: Line number to start reading from (0-indexed)
        limit: Number of lines to read (default: 2000)

    Returns:
        Dictionary containing file contents with line numbers or error message
    """
    try:
        path = Path(file_path)

        # Validate path
        if not path.exists():
            return {
                "error": f"File not found: {file_path}",
                "file_path": file_path,
            }

        if not path.is_file():
            return {
                "error": f"Path is not a file: {file_path}",
                "file_path": file_path,
            }

        # Check permissions
        if not os.access(path, os.R_OK):
            return {
                "error": f"Permission denied: {file_path}",
                "file_path": file_path,
            }

        # Read file
        with path.open(encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        # Apply offset and limit
        start_line = offset if offset is not None else 0
        default_limit = 2000
        end_line = start_line + (limit if limit is not None else default_limit)

        # Ensure bounds are valid
        start_line = max(0, start_line)
        end_line = min(len(lines), end_line)

        selected_lines = lines[start_line:end_line]

        # Format with line numbers (cat -n format)
        numbered_lines = []
        for i, line in enumerate(selected_lines, start=start_line + 1):
            # Truncate very long lines
            display_line = (
                line
                if len(line) <= MAX_LINE_LENGTH
                else line[:MAX_LINE_LENGTH] + "... [truncated]\n"
            )
            numbered_lines.append(f"{i:6d}\t{display_line}")

        content = "".join(numbered_lines)

        # Build result
        result = {
            "file_path": str(path.absolute()),
            "content": content,
            "total_lines": len(lines),
            "lines_shown": len(selected_lines),
            "start_line": start_line + 1,
            "end_line": end_line,
        }

        # Add truncation warning if needed
        if end_line < len(lines):
            result["truncated"] = True
            result["warning"] = (
                f"File has {len(lines)} lines. Showing lines {start_line + 1}-{end_line}. "
                f"Use offset and limit parameters to read more."
            )

        return result

    except UnicodeDecodeError:
        return {
            "error": f"File is not a text file (binary content): {file_path}",
            "file_path": file_path,
        }
    except Exception as e:
        return {
            "error": f"Failed to read file: {e!s}",
            "file_path": file_path,
        }


# ============================================================================
# Write Tool
# ============================================================================


@beta_tool
def write_file(
    file_path: str,
    content: str,
) -> dict[str, Any]:
    """Write a file to the local filesystem.

    Creates a new file or overwrites an existing file. For existing files,
    requires that the file was read first (safety check). Creates parent
    directories if they don't exist.

    Args:
        file_path: Absolute path to the file to write
        content: Content to write to the file

    Returns:
        Dictionary containing success status and file information
    """
    try:
        path = Path(file_path)

        # Check if file exists before writing
        file_existed = path.exists()

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Check if overwriting existing file
        if file_existed:
            if not path.is_file():
                return {
                    "error": f"Path exists but is not a file: {file_path}",
                    "file_path": file_path,
                }

            # Check write permissions
            if not os.access(path, os.W_OK):
                return {
                    "error": f"Permission denied: {file_path}",
                    "file_path": file_path,
                }

        # Write file
        with path.open("w", encoding="utf-8") as f:
            f.write(content)

        # Get file stats
        stat = path.stat()
        lines = content.count("\n") + 1

        return {
            "success": True,
            "file_path": str(path.absolute()),
            "bytes_written": stat.st_size,
            "lines_written": lines,
            "action": "overwritten" if file_existed else "created",
        }

    except PermissionError:
        return {
            "error": f"Permission denied: {file_path}",
            "file_path": file_path,
        }
    except Exception as e:
        return {
            "error": f"Failed to write file: {e!s}",
            "file_path": file_path,
        }


# ============================================================================
# Edit Tool
# ============================================================================


@beta_tool
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> dict[str, Any]:
    """Perform exact string replacements in files.

    Uses exact string matching to replace content. The old_string must match
    exactly (including whitespace). If old_string appears multiple times,
    use replace_all=True or provide more context to make it unique.

    Args:
        file_path: Absolute path to the file to modify
        old_string: Text to replace (must match exactly)
        new_string: Text to replace it with (must be different from old_string)
        replace_all: Replace all occurrences (default: False, requires unique match)

    Returns:
        Dictionary containing edit results or error message
    """
    try:
        # Validate file exists and is writable
        error = _validate_file_for_editing(file_path)
        if error:
            return error

        # Validate inputs
        if old_string == new_string:
            return {
                "error": "old_string and new_string must be different",
                "file_path": file_path,
            }

        # Read file
        path = Path(file_path)
        with path.open(encoding="utf-8") as f:
            content = f.read()

        # Validate string presence and count
        if old_string not in content:
            return {
                "error": "old_string not found in file",
                "file_path": file_path,
                "old_string": old_string,
            }

        occurrences = content.count(old_string)
        if occurrences > 1 and not replace_all:
            return {
                "error": (
                    f"old_string appears {occurrences} times in file. "
                    "Either provide more context to make it unique or use replace_all=True"
                ),
                "file_path": file_path,
                "occurrences": occurrences,
            }

        # Perform replacement and write
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacements = occurrences
        else:
            new_content = content.replace(old_string, new_string, 1)
            replacements = 1

        with path.open("w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "success": True,
            "file_path": str(path.absolute()),
            "replacements": replacements,
            "replace_all": replace_all,
        }

    except Exception as e:
        return {
            "error": f"Failed to edit file: {e!s}",
            "file_path": file_path,
        }


# ============================================================================
# MultiEdit Tool
# ============================================================================


@beta_tool
def multi_edit_file(
    file_path: str,
    edits: list[dict[str, str]],
) -> dict[str, Any]:
    """Perform multiple exact string replacements in a single file.

    Applies multiple edits sequentially in the order provided. Each edit
    must specify old_string and new_string. Useful for batch editing operations.

    Args:
        file_path: Absolute path to the file to modify
        edits: List of edit operations, each with 'old_string' and 'new_string' keys

    Returns:
        Dictionary containing batch edit results or error message
    """
    try:
        # Validate file exists and is writable
        error = _validate_file_for_editing(file_path)
        if error:
            return error

        # Validate edits list
        if not edits:
            return {
                "error": "edits list cannot be empty",
                "file_path": file_path,
            }

        # Validate each edit has required fields
        for i, edit in enumerate(edits):
            if "old_string" not in edit or "new_string" not in edit:
                return {
                    "error": f"Edit {i + 1} missing 'old_string' or 'new_string'",
                    "file_path": file_path,
                }

        # Read and process file
        path = Path(file_path)
        with path.open(encoding="utf-8") as f:
            current_content = f.read()

        # Apply edits sequentially
        edit_results = []
        for i, edit in enumerate(edits):
            old_str = edit["old_string"]
            new_str = edit["new_string"]

            if old_str in current_content:
                current_content = current_content.replace(old_str, new_str, 1)
                edit_results.append({"edit_number": i + 1, "success": True})
            else:
                edit_results.append(
                    {
                        "edit_number": i + 1,
                        "success": False,
                        "error": "old_string not found",
                    }
                )

        # Write back
        with path.open("w", encoding="utf-8") as f:
            f.write(current_content)

        successful_edits = sum(1 for r in edit_results if r["success"])

        return {
            "success": True,
            "file_path": str(path.absolute()),
            "total_edits": len(edits),
            "successful_edits": successful_edits,
            "failed_edits": len(edits) - successful_edits,
            "edit_results": edit_results,
        }

    except Exception as e:
        return {
            "error": f"Failed to perform multi-edit: {e!s}",
            "file_path": file_path,
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_file_tools() -> list[dict[str, Any]]:
    """Get all file operation tool definitions.

    Returns:
        List of file tool definitions for use with Devorbit client
    """
    return [
        read_file.tool_definition,  # type: ignore[attr-defined]
        write_file.tool_definition,  # type: ignore[attr-defined]
        edit_file.tool_definition,  # type: ignore[attr-defined]
        multi_edit_file.tool_definition,  # type: ignore[attr-defined]
    ]


# Export tool instances for direct use
__all__ = [
    "edit_file",
    "get_all_file_tools",
    "multi_edit_file",
    "read_file",
    "write_file",
]
