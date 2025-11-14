"""Task management tools for tracking agent progress.

This module provides todo list management tools matching Claude Code's behavior:
- TodoWrite tool: Create and update task lists
- TodoRead tool: Read current task status
"""

import copy
import json
from pathlib import Path
from typing import Any, Literal

from ._tool_helpers import beta_tool


# Task status types
TaskStatus = Literal["pending", "in_progress", "completed"]


# Global todo state (in-memory storage)
_TODO_STATE: list[dict[str, Any]] = []
_TODO_FILE_PATH: Path | None = None


# ============================================================================
# TodoWrite Tool
# ============================================================================


@beta_tool
def todo_write(
    todos: list[dict[str, str]],
    persist_to_file: str | None = None,
) -> dict[str, Any]:
    """Create and manage a structured task list.

    Use this tool to track progress, organize complex tasks, and demonstrate
    thoroughness. Each task has content (what to do), activeForm (present
    continuous description), and status.

    Args:
        todos: List of task dictionaries with 'content', 'activeForm', and 'status' keys
        persist_to_file: Optional file path to persist todos (default: in-memory only)

    Returns:
        Dictionary containing success status and task summary
    """
    global _TODO_STATE, _TODO_FILE_PATH  # noqa: PLW0603

    try:
        # Validate todos
        if not todos:
            return {
                "error": "todos list cannot be empty",
            }

        valid_statuses = {"pending", "in_progress", "completed"}

        for i, todo in enumerate(todos):
            # Validate required fields
            if "content" not in todo:
                return {
                    "error": f"Todo {i + 1} missing 'content' field",
                }
            if "status" not in todo:
                return {
                    "error": f"Todo {i + 1} missing 'status' field",
                }
            if "activeForm" not in todo:
                return {
                    "error": f"Todo {i + 1} missing 'activeForm' field",
                }

            # Validate status
            if todo["status"] not in valid_statuses:
                return {
                    "error": f"Todo {i + 1} has invalid status: {todo['status']}. Must be one of: {valid_statuses}",
                }

            # Validate strings are not empty
            if not todo["content"].strip():
                return {
                    "error": f"Todo {i + 1} has empty 'content'",
                }
            if not todo["activeForm"].strip():
                return {
                    "error": f"Todo {i + 1} has empty 'activeForm'",
                }

        # Count in_progress tasks
        in_progress_count = sum(1 for t in todos if t["status"] == "in_progress")

        # Store todos in global state
        _TODO_STATE = todos.copy()

        # Persist to file if requested
        if persist_to_file:
            file_path = Path(persist_to_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with file_path.open("w", encoding="utf-8") as f:
                json.dump(todos, f, indent=2)

            _TODO_FILE_PATH = file_path

        # Calculate statistics
        total = len(todos)
        pending = sum(1 for t in todos if t["status"] == "pending")
        in_progress = in_progress_count
        completed = sum(1 for t in todos if t["status"] == "completed")

        return {
            "success": True,
            "total_tasks": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "persisted": persist_to_file is not None,
            "file_path": str(_TODO_FILE_PATH.absolute()) if _TODO_FILE_PATH else None,
            "message": "Todos have been modified successfully. Ensure that you continue to use the todo list to track your progress. Please proceed with the current tasks if applicable",
        }

    except Exception as e:
        return {
            "error": f"Failed to write todos: {e!s}",
        }


# ============================================================================
# TodoRead Tool
# ============================================================================


@beta_tool
def todo_read(
    load_from_file: str | None = None,
) -> dict[str, Any]:
    """Read the current task list.

    Returns the current state of all tasks including their status and progress.
    Can load from a file or return in-memory state.

    Args:
        load_from_file: Optional file path to load todos from (default: use in-memory state)

    Returns:
        Dictionary containing current todo list and statistics
    """
    global _TODO_STATE, _TODO_FILE_PATH  # noqa: PLW0603

    try:
        # Load from file if requested
        if load_from_file:
            file_path = Path(load_from_file)

            if not file_path.exists():
                return {
                    "error": f"Todo file not found: {load_from_file}",
                }

            with file_path.open(encoding="utf-8") as f:
                todos = json.load(f)

            _TODO_STATE = todos
            _TODO_FILE_PATH = file_path
        else:
            todos = _TODO_STATE

        # If no todos, return empty state
        if not todos:
            return {
                "todos": [],
                "total_tasks": 0,
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "message": "No tasks in todo list",
            }

        # Calculate statistics
        total = len(todos)
        pending = sum(1 for t in todos if t["status"] == "pending")
        in_progress = sum(1 for t in todos if t["status"] == "in_progress")
        completed = sum(1 for t in todos if t["status"] == "completed")

        # Format todos for display
        formatted_todos = []
        for i, todo in enumerate(todos, start=1):
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
            }
            formatted_todos.append(
                {
                    "number": i,
                    "content": todo["content"],
                    "activeForm": todo["activeForm"],
                    "status": todo["status"],
                    "display": f"{status_emoji.get(todo['status'], '❓')} [{todo['status']}] {todo['content']}",
                }
            )

        return {
            "todos": formatted_todos,
            "raw_todos": todos,
            "total_tasks": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
            "loaded_from_file": load_from_file is not None,
            "file_path": str(_TODO_FILE_PATH.absolute()) if _TODO_FILE_PATH else None,
        }

    except Exception as e:
        return {
            "error": f"Failed to read todos: {e!s}",
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_todo_tools() -> list[dict[str, Any]]:
    """Get all todo management tool definitions.

    Returns:
        List of todo tool definitions for use with Devorbit client
    """
    return [
        todo_write.tool_definition,  # type: ignore[attr-defined]
        todo_read.tool_definition,  # type: ignore[attr-defined]
    ]


def clear_todo_state() -> None:
    """Clear the in-memory todo state.

    Useful for testing or resetting the todo list.
    """
    global _TODO_STATE, _TODO_FILE_PATH  # noqa: PLW0603
    _TODO_STATE = []
    _TODO_FILE_PATH = None


def get_current_todos() -> list[dict[str, Any]]:
    """Get the current todo list.

    Returns:
        Current todo list (deep copy)
    """
    return copy.deepcopy(_TODO_STATE)


# Export tool instances for direct use
__all__ = [
    "clear_todo_state",
    "get_all_todo_tools",
    "get_current_todos",
    "todo_read",
    "todo_write",
]
