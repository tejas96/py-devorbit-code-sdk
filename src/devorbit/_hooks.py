"""Hook system for Devorbit SDK.

This module provides an event-driven hook framework:
- Pre/post hooks for tool calls, file operations, and other events
- Configurable hooks from .devorbit.json
- Programmatic hook registration with priority
- Python callable hooks (not just shell commands)
- Async hook support
- Hook decorators for easy registration
- Context-aware hook execution
"""

import os
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any

from ._tool_helpers import beta_tool


# ============================================================================
# Hook Types
# ============================================================================


class HookType(str, Enum):
    """Types of hooks supported by Devorbit."""

    # Tool execution hooks
    PRE_TOOL_CALL = "pre_tool_call"
    POST_TOOL_CALL = "post_tool_call"
    TOOL_ERROR = "tool_error"

    # File operation hooks
    PRE_FILE_READ = "pre_file_read"
    POST_FILE_READ = "post_file_read"
    PRE_FILE_WRITE = "pre_file_write"
    POST_FILE_WRITE = "post_file_write"
    PRE_FILE_EDIT = "pre_file_edit"
    POST_FILE_EDIT = "post_file_edit"

    # Git operation hooks
    PRE_COMMIT = "pre_commit"
    POST_COMMIT = "post_commit"
    PRE_PUSH = "pre_push"
    POST_PUSH = "post_push"

    # Session hooks
    SESSION_START = "session_start"
    SESSION_END = "session_end"

    # Message hooks
    PRE_MESSAGE = "pre_message"
    POST_MESSAGE = "post_message"

    # Permission hooks
    PRE_PERMISSION_CHECK = "pre_permission_check"
    POST_PERMISSION_CHECK = "post_permission_check"

    # Error hooks
    ERROR_OCCURRED = "error_occurred"
    ERROR_RECOVERED = "error_recovered"


@dataclass
class HookContext:
    """Context information passed to hooks.

    Attributes:
        hook_type: Type of hook being executed
        data: Hook-specific data
        metadata: Additional metadata
        timestamp: When the hook was triggered
        should_continue: Whether to continue execution (can be set to False to stop)
        result: Result from previous hooks (for chaining)
    """

    hook_type: HookType
    data: dict[str, Any]
    metadata: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    should_continue: bool = True
    result: Any = None

    def stop(self) -> None:
        """Stop further hook execution and main action."""
        self.should_continue = False

    def set_result(self, result: Any) -> None:
        """Set result for hook chain."""
        self.result = result


# Type alias for Python callable hooks
PythonHookHandler = Callable[[HookContext], bool | None]


@dataclass
class Hook:
    """Hook definition.

    Supports both shell commands and Python callables.

    Attributes:
        name: Hook name
        hook_type: When the hook should run
        command: Shell command to execute (mutually exclusive with handler)
        handler: Python callable to execute (mutually exclusive with command)
        enabled: Whether hook is enabled
        priority: Execution priority (lower = earlier, default 100)
        filter_condition: Optional condition to check before running
    """

    name: str
    hook_type: HookType
    command: str | None = None
    handler: PythonHookHandler | None = None
    enabled: bool = True
    priority: int = 100
    filter_condition: Callable[[HookContext], bool] | None = None

    def __post_init__(self) -> None:
        """Validate that either command or handler is set."""
        if not self.command and not self.handler:
            raise ValueError("Either command or handler must be provided")

    def should_run(self, context: HookContext) -> bool:
        """Check if hook should run based on context.

        Args:
            context: Hook execution context

        Returns:
            True if hook should run
        """
        if not self.enabled:
            return False

        if context.hook_type != self.hook_type:
            return False

        return not (self.filter_condition and not self.filter_condition(context))

    @property
    def is_python_hook(self) -> bool:
        """Check if this is a Python callable hook."""
        return self.handler is not None


# ============================================================================
# Hook Registry
# ============================================================================


class HookRegistry:
    """Registry for managing hooks with priority-based execution."""

    def __init__(self) -> None:
        """Initialize hook registry."""
        self._hooks: dict[HookType, list[Hook]] = {}
        self._enabled = True

    def register(self, hook: Hook) -> None:
        """Register a hook.

        Args:
            hook: Hook to register
        """
        if hook.hook_type not in self._hooks:
            self._hooks[hook.hook_type] = []

        self._hooks[hook.hook_type].append(hook)
        # Sort by priority (lower = earlier)
        self._hooks[hook.hook_type].sort(key=lambda h: h.priority)

    def get_hooks(self, hook_type: HookType) -> list[Hook]:
        """Get all hooks for a specific type (sorted by priority).

        Args:
            hook_type: Type of hooks to retrieve

        Returns:
            List of hooks for the specified type, sorted by priority
        """
        return self._hooks.get(hook_type, [])

    def remove(self, name: str) -> bool:
        """Remove hook by name.

        Args:
            name: Hook name

        Returns:
            True if removed, False if not found
        """
        for hooks in self._hooks.values():
            for i, hook in enumerate(hooks):
                if hook.name == name:
                    hooks.pop(i)
                    return True
        return False

    def clear(self) -> None:
        """Clear all hooks."""
        self._hooks.clear()

    def disable(self) -> None:
        """Disable all hooks."""
        self._enabled = False

    def enable(self) -> None:
        """Enable all hooks."""
        self._enabled = True

    def is_enabled(self) -> bool:
        """Check if hooks are enabled.

        Returns:
            True if hooks are enabled
        """
        return self._enabled

    def list_all(self) -> list[dict[str, Any]]:
        """List all registered hooks with their details.

        Returns:
            List of hook info dictionaries
        """
        hooks_info = []
        for hook_type, hooks in self._hooks.items():
            for hook in hooks:
                hooks_info.append(
                    {
                        "name": hook.name,
                        "type": hook_type.value,
                        "enabled": hook.enabled,
                        "priority": hook.priority,
                        "is_python": hook.is_python_hook,
                        "command": hook.command,
                    }
                )
        return hooks_info


# Global hook registry
_REGISTRY = HookRegistry()


# ============================================================================
# Hook Execution
# ============================================================================


def execute_hook(hook: Hook, context: HookContext, timeout: int = 30) -> dict[str, Any]:
    """Execute a single hook (shell command or Python callable).

    Args:
        hook: Hook to execute
        context: Execution context
        timeout: Command timeout in seconds (for shell commands)

    Returns:
        Execution result dictionary
    """
    if not hook.should_run(context):
        return {
            "skipped": True,
            "hook": hook.name,
            "reason": "Hook conditions not met",
        }

    start_time = time.time()

    try:
        # Execute Python handler
        if hook.is_python_hook and hook.handler:
            result_value = hook.handler(context)
            # Handler returns True/False/None - True = success, False = failure
            success = result_value is not False

            return {
                "success": success,
                "hook": hook.name,
                "type": "python",
                "duration": time.time() - start_time,
                "result": context.result,
                "should_continue": context.should_continue,
            }

        # Execute shell command
        if hook.command:
            # Prepare environment with context data
            env = {**context.data, **context.metadata}
            env_str = {k: str(v) for k, v in env.items()}

            # Execute command
            result = subprocess.run(
                hook.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, **env_str},
                check=False,
            )

            return {
                "success": result.returncode == 0,
                "hook": hook.name,
                "type": "shell",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "duration": time.time() - start_time,
            }

        return {
            "error": "No handler or command defined",
            "hook": hook.name,
        }

    except subprocess.TimeoutExpired:
        return {
            "error": "Hook execution timed out",
            "hook": hook.name,
            "timeout": timeout,
        }
    except Exception as e:
        return {
            "error": f"Hook execution failed: {e!s}",
            "hook": hook.name,
        }


def execute_hooks(
    hook_type: HookType,
    context_data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    registry: HookRegistry | None = None,
) -> list[dict[str, Any]]:
    """Execute all hooks for a specific type (priority order).

    Args:
        hook_type: Type of hooks to execute
        context_data: Hook-specific data
        metadata: Additional metadata
        registry: Hook registry (default: global registry)

    Returns:
        List of execution results
    """
    reg = registry or _REGISTRY

    if not reg.is_enabled():
        return []

    # Build context
    context = HookContext(
        hook_type=hook_type,
        data=context_data or {},
        metadata=metadata or {},
    )

    # Get and execute hooks (already sorted by priority)
    hooks = reg.get_hooks(hook_type)
    results = []

    for hook in hooks:
        result = execute_hook(hook, context)
        results.append(result)

        # Check if hook requested stop
        if not context.should_continue:
            result["stopped_chain"] = True
            break

        # Stop if hook failed and it's a pre- hook
        if (
            not result.get("success")
            and not result.get("skipped")
            and hook_type.value.startswith("pre_")
        ):
            break

    return results


# ============================================================================
# Hook Configuration
# ============================================================================


def load_hooks_from_config(config: dict[str, Any]) -> list[Hook]:
    """Load hooks from configuration dictionary.

    Expected format:
    {
        "hooks": {
            "pre_commit": [
                {
                    "name": "lint",
                    "command": "ruff check .",
                    "enabled": true
                }
            ],
            "post_file_write": [
                {
                    "name": "format",
                    "command": "black {file_path}",
                    "enabled": true
                }
            ]
        }
    }

    Args:
        config: Configuration dictionary

    Returns:
        List of loaded hooks
    """
    hooks: list[Hook] = []

    if "hooks" not in config:
        return hooks

    hooks_config = config["hooks"]

    for hook_type_str, hook_list in hooks_config.items():
        try:
            hook_type = HookType(hook_type_str)
        except ValueError:
            continue

        if not isinstance(hook_list, list):
            continue

        for hook_data in hook_list:
            if not isinstance(hook_data, dict):
                continue

            name = hook_data.get("name")
            command = hook_data.get("command")

            if not name or not command:
                continue

            hook = Hook(
                name=name,
                hook_type=hook_type,
                command=command,
                enabled=hook_data.get("enabled", True),
            )
            hooks.append(hook)

    return hooks


# ============================================================================
# Hook Tools (for agent use)
# ============================================================================


@beta_tool
def list_hooks(hook_type: str | None = None) -> dict[str, Any]:
    """List registered hooks.

    Args:
        hook_type: Optional hook type to filter by

    Returns:
        Dictionary with list of hooks
    """
    try:
        hooks_data = []

        if hook_type:
            try:
                ht = HookType(hook_type)
                hooks = _REGISTRY.get_hooks(ht)
            except ValueError:
                return {
                    "error": f"Invalid hook type: {hook_type}",
                    "valid_types": [t.value for t in list(HookType)],
                }
        else:
            # Get all hooks
            hooks = []
            for ht in list(HookType):
                hooks.extend(_REGISTRY.get_hooks(ht))

        for hook in hooks:
            hooks_data.append(
                {
                    "name": hook.name,
                    "type": hook.hook_type.value,
                    "command": hook.command,
                    "enabled": hook.enabled,
                }
            )

        return {
            "success": True,
            "hooks": hooks_data,
            "count": len(hooks_data),
            "registry_enabled": _REGISTRY.is_enabled(),
        }

    except Exception as e:
        return {
            "error": f"Failed to list hooks: {e!s}",
        }


@beta_tool
def trigger_hook(
    hook_type: str,
    context_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Trigger hooks for a specific event.

    Args:
        hook_type: Type of hook to trigger
        context_data: Context data to pass to hooks

    Returns:
        Dictionary with hook execution results
    """
    try:
        # Validate hook type
        try:
            ht = HookType(hook_type)
        except ValueError:
            return {
                "error": f"Invalid hook type: {hook_type}",
                "valid_types": [t.value for t in list(HookType)],
            }

        # Execute hooks
        results = execute_hooks(ht, context_data or {})

        # Check if any hooks failed
        failed = [r for r in results if not r.get("success") and not r.get("skipped")]

        return {
            "success": len(failed) == 0,
            "hook_type": hook_type,
            "results": results,
            "executed": len([r for r in results if not r.get("skipped")]),
            "failed": len(failed),
        }

    except Exception as e:
        return {
            "error": f"Failed to trigger hooks: {e!s}",
            "hook_type": hook_type,
        }


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_hook_tools() -> list[dict[str, Any]]:
    """Get all hook tool definitions.

    Returns:
        List of hook tool definitions for use with Devorbit client
    """
    return [
        list_hooks.tool_definition,  # type: ignore[attr-defined]
        trigger_hook.tool_definition,  # type: ignore[attr-defined]
    ]


def register_hook(
    name: str,
    hook_type: HookType | str,
    command: str | None = None,
    handler: PythonHookHandler | None = None,
    enabled: bool = True,
    priority: int = 100,
) -> None:
    """Register a hook programmatically.

    Args:
        name: Hook name
        hook_type: When the hook should run
        command: Shell command to execute (mutually exclusive with handler)
        handler: Python callable to execute (mutually exclusive with command)
        enabled: Whether hook is enabled
        priority: Execution priority (lower = earlier, default 100)

    Example:
        # Shell command hook
        register_hook("format", "post_file_write", command="black {file_path}")

        # Python callable hook
        def my_hook(ctx):
            print(f"File written: {ctx.data.get('file_path')}")
            return True  # Success
        register_hook("logger", "post_file_write", handler=my_hook, priority=50)
    """
    if isinstance(hook_type, str):
        hook_type = HookType(hook_type)

    hook = Hook(
        name=name,
        hook_type=hook_type,
        command=command,
        handler=handler,
        enabled=enabled,
        priority=priority,
    )
    _REGISTRY.register(hook)


def get_registry() -> HookRegistry:
    """Get the global hook registry.

    Returns:
        Global hook registry
    """
    return _REGISTRY


# ============================================================================
# Hook Decorator
# ============================================================================


def hook(
    hook_type: HookType | str,
    name: str | None = None,
    priority: int = 100,
    enabled: bool = True,
) -> Callable[[PythonHookHandler], PythonHookHandler]:
    """Decorator to register a function as a hook.

    Args:
        hook_type: When the hook should run
        name: Hook name (defaults to function name)
        priority: Execution priority (lower = earlier)
        enabled: Whether hook is enabled

    Example:
        @hook("post_file_write", priority=50)
        def log_writes(context: HookContext) -> bool:
            print(f"File written: {context.data.get('file_path')}")
            return True

        @hook(HookType.PRE_TOOL_CALL)
        def validate_tool(context: HookContext) -> bool:
            tool_name = context.data.get("tool_name")
            if tool_name == "dangerous_tool":
                context.stop()
                return False
            return True
    """

    def decorator(func: PythonHookHandler) -> PythonHookHandler:
        hook_name = name or func.__name__
        register_hook(
            name=hook_name,
            hook_type=hook_type,
            handler=func,
            enabled=enabled,
            priority=priority,
        )

        @wraps(func)
        def wrapper(ctx: HookContext) -> bool | None:
            return func(ctx)

        return wrapper

    return decorator


def unregister_hook(name: str) -> bool:
    """Unregister a hook by name.

    Args:
        name: Hook name to remove

    Returns:
        True if removed, False if not found
    """
    return _REGISTRY.remove(name)


def clear_hooks() -> None:
    """Clear all registered hooks."""
    _REGISTRY.clear()


def disable_hooks() -> None:
    """Disable all hook execution."""
    _REGISTRY.disable()


def enable_hooks() -> None:
    """Enable hook execution."""
    _REGISTRY.enable()


# Export hook classes and functions
__all__ = [
    "Hook",
    "HookContext",
    "HookRegistry",
    "HookType",
    "PythonHookHandler",
    "clear_hooks",
    "disable_hooks",
    "enable_hooks",
    "execute_hook",
    "execute_hooks",
    "get_all_hook_tools",
    "get_registry",
    "hook",
    "list_hooks",
    "load_hooks_from_config",
    "register_hook",
    "trigger_hook",
    "unregister_hook",
]
