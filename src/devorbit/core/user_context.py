"""User-scoped context for multi-tenant support.

This module provides isolated contexts for each user/agent session,
enabling multiple users to use the SDK simultaneously without state conflicts.

All state that was previously global is now scoped to UserContext:
- Bash sessions
- Todo state
- Active tasks
- Permission rules
- Conversation history

Example:
    ```python
    from devorbit.core.user_context import get_context, UserContext

    # Get isolated context for a user
    ctx = get_context(user_id="user_123", session_id="session_abc")

    # All state is now user-scoped
    ctx.bash_sessions["session_1"] = some_bash_session
    ctx.todo_state.append({"id": "1", "content": "Task"})

    # Different user has completely isolated state
    ctx2 = get_context(user_id="user_456")
    assert ctx2.bash_sessions == {}  # Empty, isolated from user_123
    ```
"""

from __future__ import annotations

import atexit
import threading
import time
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, TypeVar


T = TypeVar("T")


@dataclass
class UserContext:
    """Isolated context for each user/agent session.

    All state that was previously global is now scoped to this context.
    Each user gets their own isolated state, enabling true multi-tenancy.

    Attributes:
        user_id: Unique identifier for the user/tenant
        session_id: Unique identifier for this session
        bash_sessions: Per-user bash session storage
        todo_state: Per-user todo list
        active_tasks: Per-user agent tasks
        conversation_history: Per-user conversation messages
        metadata: Additional user-specific metadata
    """

    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Per-user state (previously global!)
    bash_sessions: dict[str, Any] = field(default_factory=dict)
    todo_state: list[dict[str, Any]] = field(default_factory=list)
    todo_file_path: str | None = field(default=None)
    active_tasks: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)

    # Per-user tool customizations
    tool_overrides: dict[str, bool] = field(default_factory=dict)  # tool enable/disable
    permission_rules: list[Any] = field(default_factory=list)
    session_permissions: dict[str, str] = field(default_factory=dict)  # tool:path -> decision

    # User metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Internal state (not part of __init__)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    _created_at: float = field(default_factory=time.time, repr=False)
    _last_activity: float = field(default_factory=time.time, repr=False)

    def touch(self) -> None:
        """Update last activity timestamp."""
        self._last_activity = time.time()

    def is_stale(self, max_idle_seconds: float = 3600) -> bool:
        """Check if context is stale (idle for too long).

        Args:
            max_idle_seconds: Maximum idle time before context is considered stale

        Returns:
            True if context should be cleaned up
        """
        return time.time() - self._last_activity > max_idle_seconds

    def get_age(self) -> float:
        """Get context age in seconds."""
        return time.time() - self._created_at

    # Thread-safe accessors for commonly used state

    def get_bash_session(self, session_id: str) -> Any | None:
        """Thread-safe get bash session."""
        with self._lock:
            self.touch()
            return self.bash_sessions.get(session_id)

    def set_bash_session(self, session_id: str, session: Any) -> None:
        """Thread-safe set bash session."""
        with self._lock:
            self.touch()
            self.bash_sessions[session_id] = session

    def remove_bash_session(self, session_id: str) -> bool:
        """Thread-safe remove bash session."""
        with self._lock:
            self.touch()
            if session_id in self.bash_sessions:
                del self.bash_sessions[session_id]
                return True
            return False

    def get_todo_state(self) -> list[dict[str, Any]]:
        """Thread-safe get todo state (returns copy)."""
        with self._lock:
            self.touch()
            return list(self.todo_state)

    def set_todo_state(self, todos: list[dict[str, Any]]) -> None:
        """Thread-safe set todo state."""
        with self._lock:
            self.touch()
            self.todo_state = list(todos)

    def get_active_task(self, task_id: str) -> Any | None:
        """Thread-safe get active task."""
        with self._lock:
            self.touch()
            return self.active_tasks.get(task_id)

    def set_active_task(self, task_id: str, task: Any) -> None:
        """Thread-safe set active task."""
        with self._lock:
            self.touch()
            self.active_tasks[task_id] = task

    def remove_active_task(self, task_id: str) -> bool:
        """Thread-safe remove active task."""
        with self._lock:
            self.touch()
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                return True
            return False

    def get_session_permission(self, key: str) -> str | None:
        """Thread-safe get session permission decision."""
        with self._lock:
            return self.session_permissions.get(key)

    def set_session_permission(self, key: str, decision: str) -> None:
        """Thread-safe set session permission decision."""
        with self._lock:
            self.session_permissions[key] = decision

    def clear_session_permissions(self) -> None:
        """Thread-safe clear all session permissions."""
        with self._lock:
            self.session_permissions.clear()

    def cleanup(self) -> None:
        """Clean up all resources in this context."""
        with self._lock:
            # Close any bash sessions
            for _session_id, session in list(self.bash_sessions.items()):
                if hasattr(session, "stop"):
                    with suppress(Exception):
                        session.stop()

            self.bash_sessions.clear()
            self.todo_state.clear()
            self.active_tasks.clear()
            self.conversation_history.clear()
            self.session_permissions.clear()


class ContextRegistry:
    """Thread-safe global registry for user contexts.

    This is the ONLY global state in the multi-tenant system.
    All user-specific state is isolated within UserContext instances.

    Example:
        ```python
        registry = get_context_registry()

        # Get or create context for a user
        ctx = registry.get("user_123", "session_abc")

        # List all active contexts
        for ctx in registry.list_all():
            print(f"User: {ctx.user_id}, Age: {ctx.get_age()}")

        # Cleanup stale contexts
        removed = registry.cleanup_stale(max_age=3600)
        ```
    """

    def __init__(self) -> None:
        """Initialize context registry."""
        self._contexts: dict[str, UserContext] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    def get(self, user_id: str, session_id: str | None = None) -> UserContext:
        """Get or create user context.

        Args:
            user_id: User identifier
            session_id: Optional session identifier (auto-generated if not provided)

        Returns:
            UserContext for the user/session
        """
        key = f"{user_id}:{session_id or 'default'}"

        with self._lock:
            # Auto-cleanup if needed
            self._maybe_cleanup()

            if key not in self._contexts:
                self._contexts[key] = UserContext(
                    user_id=user_id,
                    session_id=session_id or str(uuid.uuid4()),
                )
            else:
                # Touch existing context
                self._contexts[key].touch()

            return self._contexts[key]

    def get_by_key(self, key: str) -> UserContext | None:
        """Get context by full key (user_id:session_id).

        Args:
            key: Full context key

        Returns:
            UserContext if found, None otherwise
        """
        with self._lock:
            return self._contexts.get(key)

    def remove(self, user_id: str, session_id: str | None = None) -> bool:
        """Remove user context.

        Args:
            user_id: User identifier
            session_id: Optional session identifier

        Returns:
            True if context was removed, False if not found
        """
        key = f"{user_id}:{session_id or 'default'}"

        with self._lock:
            if key in self._contexts:
                # Cleanup resources before removing
                self._contexts[key].cleanup()
                del self._contexts[key]
                return True
            return False

    def remove_by_key(self, key: str) -> bool:
        """Remove context by full key.

        Args:
            key: Full context key

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if key in self._contexts:
                self._contexts[key].cleanup()
                del self._contexts[key]
                return True
            return False

    def list_all(self) -> list[UserContext]:
        """List all active contexts.

        Returns:
            List of all UserContext instances (copies to avoid mutation)
        """
        with self._lock:
            return list(self._contexts.values())

    def list_for_user(self, user_id: str) -> list[UserContext]:
        """List all contexts for a specific user.

        Args:
            user_id: User identifier

        Returns:
            List of contexts for the user
        """
        with self._lock:
            return [ctx for ctx in self._contexts.values() if ctx.user_id == user_id]

    def count(self) -> int:
        """Get number of active contexts."""
        with self._lock:
            return len(self._contexts)

    def cleanup_stale(self, max_age: float = 3600) -> int:
        """Remove stale contexts older than max_age seconds.

        Args:
            max_age: Maximum idle time in seconds

        Returns:
            Number of contexts removed
        """
        removed = 0

        with self._lock:
            stale_keys = [k for k, v in self._contexts.items() if v.is_stale(max_age)]

            for key in stale_keys:
                self._contexts[key].cleanup()
                del self._contexts[key]
                removed += 1

            self._last_cleanup = time.time()

        return removed

    def cleanup_all(self) -> int:
        """Remove all contexts (for shutdown).

        Returns:
            Number of contexts removed
        """
        with self._lock:
            count = len(self._contexts)

            for ctx in self._contexts.values():
                ctx.cleanup()

            self._contexts.clear()
            return count

    def _maybe_cleanup(self) -> None:
        """Auto-cleanup if enough time has passed (called while holding lock)."""
        if time.time() - self._last_cleanup > self._cleanup_interval:
            stale_keys = [k for k, v in self._contexts.items() if v.is_stale()]

            for key in stale_keys:
                self._contexts[key].cleanup()
                del self._contexts[key]

            self._last_cleanup = time.time()


# Global context registry (the ONLY global state needed for multi-tenancy)
_context_registry: ContextRegistry | None = None
_registry_lock = threading.Lock()


def get_context_registry() -> ContextRegistry:
    """Get the global context registry.

    Returns:
        Global ContextRegistry instance
    """
    global _context_registry  # noqa: PLW0603

    if _context_registry is None:
        with _registry_lock:
            if _context_registry is None:
                _context_registry = ContextRegistry()

    return _context_registry


def get_context(user_id: str, session_id: str | None = None) -> UserContext:
    """Convenience function to get user context.

    Args:
        user_id: User identifier
        session_id: Optional session identifier

    Returns:
        UserContext for the user/session
    """
    return get_context_registry().get(user_id, session_id)


def get_default_context() -> UserContext:
    """Get the default context for single-user/CLI mode.

    This provides backward compatibility for code that doesn't
    explicitly pass context.

    Returns:
        Default UserContext instance
    """
    return get_context("default", "default")


# Thread-local storage for current context
_current_context: threading.local = threading.local()


def set_current_context(ctx: UserContext) -> None:
    """Set the current context for this thread.

    Args:
        ctx: UserContext to set as current
    """
    _current_context.ctx = ctx


def get_current_context() -> UserContext:
    """Get the current context for this thread.

    Returns default context if none set.

    Returns:
        Current UserContext
    """
    ctx = getattr(_current_context, "ctx", None)
    if ctx is None:
        ctx = get_default_context()
        _current_context.ctx = ctx
    return ctx


def clear_current_context() -> None:
    """Clear the current context for this thread."""
    if hasattr(_current_context, "ctx"):
        delattr(_current_context, "ctx")


class ContextScope:
    """Context manager for temporarily setting current context.

    Example:
        ```python
        ctx = get_context("user_123")

        with ContextScope(ctx):
            # Inside this block, get_current_context() returns ctx
            result = some_tool_function()

        # Outside, get_current_context() returns previous context
        ```
    """

    def __init__(self, ctx: UserContext) -> None:
        """Initialize context scope.

        Args:
            ctx: Context to use within scope
        """
        self.ctx = ctx
        self.previous_ctx: UserContext | None = None

    def __enter__(self) -> UserContext:
        """Enter context scope."""
        self.previous_ctx = getattr(_current_context, "ctx", None)
        set_current_context(self.ctx)
        return self.ctx

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context scope."""
        if self.previous_ctx is not None:
            set_current_context(self.previous_ctx)
        else:
            clear_current_context()


def _cleanup_on_exit() -> None:
    """Cleanup all contexts on process exit."""
    if _context_registry is not None:
        _context_registry.cleanup_all()


# Register cleanup on exit
atexit.register(_cleanup_on_exit)


__all__ = [
    "ContextRegistry",
    "ContextScope",
    "UserContext",
    "clear_current_context",
    "get_context",
    "get_context_registry",
    "get_current_context",
    "get_default_context",
    "set_current_context",
]
