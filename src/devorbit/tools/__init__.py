"""Devorbit SDK Tools Module.

This module contains all built-in tools for the Devorbit SDK.
Import from individual modules for specific functionality.

Tools are automatically registered with the ToolRegistry on import.
"""

from devorbit.core.tool_registry import ToolCategory, get_tool_registry

# Re-export commonly used items
from .bash import bash, get_all_bash_tools
from .file import edit_file, get_all_file_tools, read_file, write_file
from .search import get_all_search_tools, glob_files, grep_code


def _register_builtin_tools() -> None:
    """Register all built-in tools with the global registry.

    This is called automatically on module import.
    """
    registry = get_tool_registry()

    # Register bash tool
    bash_def = bash.tool_definition  # type: ignore[attr-defined]
    registry.register(
        name="bash",
        func=bash,
        definition=bash_def,
        category=ToolCategory.BASH,
    )

    # Register file tools
    for tool_def in get_all_file_tools():
        tool_name = tool_def["name"]
        if tool_name == "read_file":
            registry.register(
                name="read_file",
                func=read_file,
                definition=tool_def,  # type: ignore[arg-type]
                category=ToolCategory.FILE,
            )
        elif tool_name == "write_file":
            registry.register(
                name="write_file",
                func=write_file,
                definition=tool_def,  # type: ignore[arg-type]
                category=ToolCategory.FILE,
            )
        elif tool_name == "edit_file":
            registry.register(
                name="edit_file",
                func=edit_file,
                definition=tool_def,  # type: ignore[arg-type]
                category=ToolCategory.FILE,
            )

    # Register search tools
    for tool_def in get_all_search_tools():
        tool_name = tool_def["name"]
        if tool_name == "grep_code":
            # Register as 'grep' for CLI compatibility
            grep_def = tool_def.copy()
            grep_def["name"] = "grep"
            grep_def["description"] = (
                "Search for patterns in files using regex. "
                "Returns matching lines with line numbers."
            )
            registry.register(
                name="grep",
                func=grep_code,
                definition=grep_def,  # type: ignore[arg-type]
                category=ToolCategory.SEARCH,
            )
        elif tool_name == "glob_files":
            # Register as 'glob' for CLI compatibility
            glob_def = tool_def.copy()
            glob_def["name"] = "glob"
            glob_def["description"] = (
                "Find files matching a glob pattern. Returns list of matching file paths."
            )
            registry.register(
                name="glob",
                func=glob_files,
                definition=glob_def,  # type: ignore[arg-type]
                category=ToolCategory.SEARCH,
            )


# Auto-register tools on import
_register_builtin_tools()


__all__ = [
    "bash",
    "get_all_bash_tools",
    "edit_file",
    "read_file",
    "write_file",
    "get_all_file_tools",
    "grep_code",
    "glob_files",
    "get_all_search_tools",
]
