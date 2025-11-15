"""Hook system for Devorbit SDK.

This module provides an event-driven hook framework:
- Pre/post hooks for tool calls, file operations, and other events
- Configurable hooks from .devorbit.json
- Programmatic hook registration
- Context-aware hook execution
"""

import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
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


@dataclass
class HookContext:
    """Context information passed to hooks.

    Attributes:
        hook_type: Type of hook being executed
        data: Hook-specific data
        metadata: Additional metadata
    """

    hook_type: HookType
    data: dict[str, Any]
    metadata: dict[str, Any]


@dataclass
class Hook:
    """Hook definition.

    Attributes:
        name: Hook name
        hook_type: When the hook should run
        command: Shell command to execute
        enabled: Whether hook is enabled
        filter_condition: Optional condition to check before running
    """

    name: str
    hook_type: HookType
    command: str
    enabled: bool = True
    filter_condition: Callable[[HookContext], bool] | None = None

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


# ============================================================================
# Hook Registry
# ============================================================================


class HookRegistry:
    """Registry for managing hooks."""

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

    def get_hooks(self, hook_type: HookType) -> list[Hook]:
        """Get all hooks for a specific type.

        Args:
            hook_type: Type of hooks to retrieve

        Returns:
            List of hooks for the specified type
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


# Global hook registry
_REGISTRY = HookRegistry()


# ============================================================================
# Hook Execution
# ============================================================================


def execute_hook(hook: Hook, context: HookContext, timeout: int = 30) -> dict[str, Any]:
    """Execute a single hook.

    Args:
        hook: Hook to execute
        context: Execution context
        timeout: Command timeout in seconds

    Returns:
        Execution result dictionary
    """
    if not hook.should_run(context):
        return {
            "skipped": True,
            "hook": hook.name,
            "reason": "Hook conditions not met",
        }

    try:
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
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
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
    """Execute all hooks for a specific type.

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

    # Get and execute hooks
    hooks = reg.get_hooks(hook_type)
    results = []

    for hook in hooks:
        result = execute_hook(hook, context)
        results.append(result)

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
    command: str,
    enabled: bool = True,
) -> None:
    """Register a hook programmatically.

    Args:
        name: Hook name
        hook_type: When the hook should run
        command: Shell command to execute
        enabled: Whether hook is enabled
    """
    if isinstance(hook_type, str):
        hook_type = HookType(hook_type)

    hook = Hook(
        name=name,
        hook_type=hook_type,
        command=command,
        enabled=enabled,
    )
    _REGISTRY.register(hook)


def get_registry() -> HookRegistry:
    """Get the global hook registry.

    Returns:
        Global hook registry
    """
    return _REGISTRY


# Export hook classes and functions
__all__ = [
    "Hook",
    "HookContext",
    "HookRegistry",
    "HookType",
    "execute_hook",
    "execute_hooks",
    "get_all_hook_tools",
    "get_registry",
    "list_hooks",
    "load_hooks_from_config",
    "register_hook",
    "trigger_hook",
]
