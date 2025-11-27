"""Context management for Devorbit CLI.

This module provides:
- ExecutionContext: Runtime context for tool/command execution
- ContextManager: Thread-safe context stack management
- context_scope: Context manager for scoped execution

Usage:
    from devorbit.cli.core.context import ContextManager, ExecutionContext

    ctx_manager = ContextManager()

    with ctx_manager.scope(ExecutionContext(operation="file_edit")) as ctx:
        # Execute within context
        ctx.set("file_path", "/path/to/file")
        result = perform_operation()
        ctx.set("result", result)
"""

from __future__ import annotations

import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path  # noqa: TC003 - Used at runtime in dataclass
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class ExecutionContext:
    """Context for a single execution scope.

    Holds runtime information about the current operation being performed.
    Thread-safe and supports nested contexts.
    """

    # Unique identifier for this context
    context_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Operation being performed
    operation: str = ""

    # Timestamp when context was created
    created_at: float = field(default_factory=time.time)

    # Working directory for this context
    working_dir: Path | None = None

    # Parent context (for nesting)
    parent: ExecutionContext | None = None

    # Custom data storage
    _data: dict[str, Any] = field(default_factory=dict)

    # Metadata about the execution
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from context data.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Value or default
        """
        # Check local data first, then parent
        if key in self._data:
            return self._data[key]
        if self.parent:
            return self.parent.get(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        """Set a value in context data.

        Args:
            key: Key to set
            value: Value to store
        """
        self._data[key] = value

    def has(self, key: str) -> bool:
        """Check if a key exists in context.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        if key in self._data:
            return True
        if self.parent:
            return self.parent.has(key)
        return False

    def delete(self, key: str) -> bool:
        """Delete a key from context.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted
        """
        if key in self._data:
            del self._data[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all context data."""
        self._data.clear()

    def elapsed_ms(self) -> float:
        """Get elapsed time since context creation.

        Returns:
            Elapsed time in milliseconds
        """
        return (time.time() - self.created_at) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "context_id": self.context_id,
            "operation": self.operation,
            "created_at": self.created_at,
            "working_dir": str(self.working_dir) if self.working_dir else None,
            "parent_id": self.parent.context_id if self.parent else None,
            "data": dict(self._data),
            "metadata": dict(self.metadata),
        }


class ContextManager:
    """Thread-safe context stack manager.

    Manages a stack of ExecutionContext objects for nested operations.
    Each thread has its own context stack.
    """

    def __init__(self) -> None:
        """Initialize the context manager."""
        self._local = threading.local()
        self._lock = threading.Lock()

    @property
    def _stack(self) -> list[ExecutionContext]:
        """Get the context stack for current thread."""
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        stack: list[ExecutionContext] = self._local.stack
        return stack

    def push(self, ctx: ExecutionContext) -> ExecutionContext:
        """Push a context onto the stack.

        Args:
            ctx: Context to push

        Returns:
            The pushed context (with parent set)
        """
        with self._lock:
            # Set parent to current context
            if self._stack:
                ctx.parent = self._stack[-1]
            self._stack.append(ctx)
        return ctx

    def pop(self) -> ExecutionContext | None:
        """Pop the current context from stack.

        Returns:
            The popped context or None if empty
        """
        with self._lock:
            if self._stack:
                return self._stack.pop()
        return None

    def current(self) -> ExecutionContext | None:
        """Get the current context.

        Returns:
            Current context or None if no context
        """
        if self._stack:
            return self._stack[-1]
        return None

    def depth(self) -> int:
        """Get the current nesting depth.

        Returns:
            Number of contexts on stack
        """
        return len(self._stack)

    def clear(self) -> None:
        """Clear all contexts for current thread."""
        with self._lock:
            self._stack.clear()

    @contextmanager
    def scope(
        self,
        ctx: ExecutionContext | None = None,
        *,
        operation: str = "",
        working_dir: Path | None = None,
    ) -> Iterator[ExecutionContext]:
        """Create a scoped context.

        Args:
            ctx: Existing context to use (creates new if None)
            operation: Operation name for new context
            working_dir: Working directory for new context

        Yields:
            The execution context
        """
        if ctx is None:
            ctx = ExecutionContext(operation=operation, working_dir=working_dir)

        self.push(ctx)
        try:
            yield ctx
        finally:
            self.pop()


# Singleton holder for global context manager
class _ContextManagerHolder:
    """Holder for global ContextManager instance."""

    instance: ContextManager | None = None


def get_context_manager() -> ContextManager:
    """Get the global context manager.

    Returns:
        Global ContextManager instance
    """
    if _ContextManagerHolder.instance is None:
        _ContextManagerHolder.instance = ContextManager()
    return _ContextManagerHolder.instance


def current_context() -> ExecutionContext | None:
    """Get the current execution context.

    Returns:
        Current context or None
    """
    return get_context_manager().current()


@contextmanager
def context_scope(
    operation: str = "",
    working_dir: Path | None = None,
    **metadata: Any,
) -> Iterator[ExecutionContext]:
    """Convenience function for creating a scoped context.

    Args:
        operation: Operation name
        working_dir: Working directory
        **metadata: Additional metadata

    Yields:
        The execution context
    """
    ctx = ExecutionContext(
        operation=operation,
        working_dir=working_dir,
        metadata=metadata,
    )

    with get_context_manager().scope(ctx):
        yield ctx


__all__ = [
    "ContextManager",
    "ExecutionContext",
    "context_scope",
    "current_context",
    "get_context_manager",
]
