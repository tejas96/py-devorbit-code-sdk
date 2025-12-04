"""Task management tools for tracking agent progress.

This module provides todo list management tools matching Claude Code's behavior:
- TodoWrite tool: Create and update task lists
- TodoRead tool: Read current task status

Multi-tenant Support:
    Todo state is now stored per-user via UserContext, enabling multiple
    users to have isolated todo lists simultaneously.
"""

import copy
import json
from pathlib import Path
from typing import Any, Literal

from devorbit.core.tool_helpers import beta_tool
from devorbit.core.user_context import UserContext, get_current_context


# Task status types
TaskStatus = Literal["pending", "in_progress", "completed"]


# ============================================================================
# Helper Functions
# ============================================================================


def _generate_active_form(content: str) -> str:
    """Generate activeForm from content by converting to present continuous.

    Args:
        content: Task content string

    Returns:
        Present continuous form of the task
    """
    # Simple heuristic: prepend "Working on" if content doesn't already have a verb form
    content_lower = content.lower().strip()
    if content_lower.startswith(("working", "doing", "fixing", "adding", "updating", "creating")):
        return content
    return f"Working on: {content}"


def _validate_and_normalize_todos(
    todos: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    """Validate and normalize todo list structure and content.

    Auto-generates 'activeForm' if not provided for better LLM compatibility.

    Args:
        todos: List of todo dictionaries to validate

    Returns:
        Tuple of (normalized_todos, error_dict or None)
    """
    if not todos:
        return [], {"error": "todos list cannot be empty"}

    valid_statuses = {"pending", "in_progress", "completed"}
    normalized: list[dict[str, str]] = []

    for i, todo in enumerate(todos):
        if "content" not in todo:
            return [], {"error": f"Todo {i + 1} missing 'content' field"}
        if "status" not in todo:
            return [], {"error": f"Todo {i + 1} missing 'status' field"}

        if todo["status"] not in valid_statuses:
            return [], {
                "error": f"Todo {i + 1} has invalid status: {todo['status']}. Must be one of: {valid_statuses}"
            }

        if not todo["content"].strip():
            return [], {"error": f"Todo {i + 1} has empty 'content'"}

        # Normalize todo: auto-generate activeForm if missing
        normalized_todo = dict(todo)
        if "activeForm" not in normalized_todo or not normalized_todo["activeForm"].strip():
            normalized_todo["activeForm"] = _generate_active_form(todo["content"])

        normalized.append(normalized_todo)

    return normalized, None


def _get_context(ctx: UserContext | None = None) -> UserContext:
    """Get the user context for todo operations.

    Args:
        ctx: Optional explicit context, uses current thread's context if None

    Returns:
        UserContext to use for todo operations
    """
    return ctx or get_current_context()


# ============================================================================
# TodoWrite Tool
# ============================================================================


@beta_tool
def todo_write(
    todos: list[dict[str, str]],
    persist_to_file: str | None = None,
    _context: UserContext | None = None,
) -> dict[str, Any]:
    """Create and manage a structured task list.

    Use this tool to track progress, organize complex tasks, and demonstrate
    thoroughness. Each task requires 'content' and 'status' fields. The
    'activeForm' field is optional and will be auto-generated if not provided.

    Args:
        todos: List of task dictionaries with required 'content' and 'status' keys.
               Optional 'activeForm' for present continuous description (auto-generated if missing).
               Status must be one of: 'pending', 'in_progress', 'completed'
        persist_to_file: Optional file path to persist todos (default: in-memory only)
        _context: Optional UserContext for multi-tenant support (internal use)

    Returns:
        Dictionary containing success status and task summary
    """
    ctx = _get_context(_context)

    try:
        # Validate and normalize todos structure (auto-generates activeForm if missing)
        normalized_todos, error = _validate_and_normalize_todos(todos)
        if error:
            return error

        # Count in_progress tasks
        in_progress_count = sum(1 for t in normalized_todos if t["status"] == "in_progress")

        # Store normalized todos in user context (thread-safe)
        ctx.set_todo_state(normalized_todos)

        # Persist to file if requested
        file_path_str: str | None = None
        if persist_to_file:
            file_path = Path(persist_to_file)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with file_path.open("w", encoding="utf-8") as f:
                json.dump(normalized_todos, f, indent=2)

            ctx.todo_file_path = str(file_path.absolute())
            file_path_str = ctx.todo_file_path

        # Calculate statistics
        total = len(normalized_todos)
        pending = sum(1 for t in normalized_todos if t["status"] == "pending")
        in_progress = in_progress_count
        completed = sum(1 for t in normalized_todos if t["status"] == "completed")

        return {
            "success": True,
            "total_tasks": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "persisted": persist_to_file is not None,
            "file_path": file_path_str,
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
    _context: UserContext | None = None,
) -> dict[str, Any]:
    """Read the current task list.

    Returns the current state of all tasks including their status and progress.
    Can load from a file or return in-memory state.

    Args:
        load_from_file: Optional file path to load todos from (default: use in-memory state)
        _context: Optional UserContext for multi-tenant support (internal use)

    Returns:
        Dictionary containing current todo list and statistics
    """
    ctx = _get_context(_context)

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

            ctx.set_todo_state(todos)
            ctx.todo_file_path = str(file_path.absolute())
        else:
            todos = ctx.get_todo_state()

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
                    "activeForm": todo.get("activeForm", todo["content"]),
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
            "file_path": ctx.todo_file_path,
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


def clear_todo_state(ctx: UserContext | None = None) -> None:
    """Clear the in-memory todo state.

    Useful for testing or resetting the todo list.

    Args:
        ctx: Optional UserContext, uses current context if None
    """
    context = _get_context(ctx)
    context.set_todo_state([])
    context.todo_file_path = None


def get_current_todos(ctx: UserContext | None = None) -> list[dict[str, Any]]:
    """Get the current todo list.

    Args:
        ctx: Optional UserContext, uses current context if None

    Returns:
        Current todo list (deep copy)
    """
    context = _get_context(ctx)
    return copy.deepcopy(context.get_todo_state())


# Export tool instances for direct use
__all__ = [
    "clear_todo_state",
    "get_all_todo_tools",
    "get_current_todos",
    "todo_read",
    "todo_write",
]
