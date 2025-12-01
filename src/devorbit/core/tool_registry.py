"""Tool Registry for auto-discovery and execution.

This module provides a centralized registry for tools, enabling:
- Auto-registration via @tool decorator
- Auto-discovery of all tools
- Generic execution by name
- Category-based organization

This follows the same pattern as HookRegistry and CommandRegistry.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from .types import Tool


class ToolCategory(Enum):
    """Categories for organizing tools."""

    FILE = "file"  # File operations (read, write, edit)
    BASH = "bash"  # Shell command execution
    SEARCH = "search"  # Search operations (grep, glob)
    NETWORK = "network"  # Network operations (fetch, etc.)
    AGENT = "agent"  # Agent/task operations
    MCP = "mcp"  # MCP server tools
    OTHER = "other"  # Uncategorized


@dataclass
class RegisteredTool:
    """A registered tool with metadata."""

    name: str
    func: Callable[..., Any]
    definition: Tool
    category: ToolCategory = ToolCategory.OTHER
    description: str = ""
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """Central registry for all tools.

    Provides auto-discovery, execution, and management of tools.
    Follows the singleton pattern for global access.

    Example:
        ```python
        from devorbit.core.tool_registry import get_tool_registry, tool

        @tool(category="file")
        def my_tool(path: str) -> str:
            '''Do something with a file.'''
            return "done"

        # Tool is auto-registered!

        registry = get_tool_registry()
        definitions = registry.get_all_definitions()
        result = registry.execute("my_tool", {"path": "/tmp/test"})
        ```
    """

    def __init__(self) -> None:
        """Initialize tool registry."""
        self._tools: dict[str, RegisteredTool] = {}
        self._enabled = True
        # Cache for tool definitions (invalidated on register/unregister)
        self._definitions_cache: list[Tool] | None = None
        self._cache_category: ToolCategory | None = None
        self._cache_enabled_only: bool = True

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        definition: Tool,
        category: ToolCategory = ToolCategory.OTHER,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name (unique identifier)
            func: Tool function
            definition: Tool definition (JSON schema)
            category: Tool category for organization
            description: Optional description override
            metadata: Additional metadata
        """
        tool = RegisteredTool(
            name=name,
            func=func,
            definition=definition,
            category=category,
            description=description or definition.get("description", ""),
            metadata=metadata or {},
        )
        self._tools[name] = tool
        self._invalidate_cache()

    def unregister(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            self._invalidate_cache()
            return True
        return False

    def _invalidate_cache(self) -> None:
        """Invalidate the definitions cache."""
        self._definitions_cache = None

    def get(self, name: str) -> RegisteredTool | None:
        """Get a registered tool by name.

        Args:
            name: Tool name

        Returns:
            RegisteredTool or None if not found
        """
        return self._tools.get(name)

    def get_function(self, name: str) -> Callable[..., Any] | None:
        """Get the function for a tool.

        Args:
            name: Tool name

        Returns:
            Tool function or None if not found
        """
        tool = self._tools.get(name)
        return tool.func if tool else None

    def get_all_definitions(
        self,
        category: ToolCategory | None = None,
        enabled_only: bool = True,
    ) -> list[Tool]:
        """Get all tool definitions (cached for performance).

        Args:
            category: Filter by category (None = all)
            enabled_only: Only return enabled tools

        Returns:
            List of tool definitions
        """
        # Use cache if available and params match
        if (
            self._definitions_cache is not None
            and self._cache_category == category
            and self._cache_enabled_only == enabled_only
        ):
            return self._definitions_cache

        # Build definitions list
        definitions: list[Tool] = []
        for tool in self._tools.values():
            if enabled_only and not tool.enabled:
                continue
            if category and tool.category != category:
                continue
            definitions.append(tool.definition)

        # Cache for common case (all enabled tools)
        if category is None and enabled_only:
            self._definitions_cache = definitions
            self._cache_category = category
            self._cache_enabled_only = enabled_only

        return definitions

    def get_all_tools(
        self,
        category: ToolCategory | None = None,
    ) -> list[RegisteredTool]:
        """Get all registered tools.

        Args:
            category: Filter by category (None = all)

        Returns:
            List of registered tools
        """
        if category:
            return [t for t in self._tools.values() if t.category == category]
        return list(self._tools.values())

    def execute(
        self,
        name: str,
        params: dict[str, Any],
        validate: bool = True,
    ) -> Any:
        """Execute a tool by name.

        Args:
            name: Tool name
            params: Tool parameters
            validate: Whether to validate parameters (not implemented yet)

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or disabled
        """
        tool = self._tools.get(name)

        if not tool:
            raise ValueError(f"Tool not found: {name}")

        if not tool.enabled:
            raise ValueError(f"Tool is disabled: {name}")

        # Execute the tool function
        return tool.func(**params)

    def list_names(self) -> list[str]:
        """Get list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def count(self) -> int:
        """Get number of registered tools.

        Returns:
            Number of tools
        """
        return len(self._tools)

    def enable(self, name: str) -> bool:
        """Enable a tool.

        Args:
            name: Tool name

        Returns:
            True if enabled, False if not found
        """
        tool = self._tools.get(name)
        if tool:
            tool.enabled = True
            self._invalidate_cache()  # Cache must be invalidated when enabled state changes
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a tool.

        Args:
            name: Tool name

        Returns:
            True if disabled, False if not found
        """
        tool = self._tools.get(name)
        if tool:
            tool.enabled = False
            self._invalidate_cache()  # Cache must be invalidated when enabled state changes
            return True
        return False

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._invalidate_cache()


# Global registry state holder
class _RegistryHolder:
    """Holder for global registry instance (avoids global statement)."""

    instance: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry.

    Returns:
        Global ToolRegistry instance
    """
    if _RegistryHolder.instance is None:
        _RegistryHolder.instance = ToolRegistry()
    return _RegistryHolder.instance


def reset_tool_registry() -> None:
    """Reset the global tool registry (mainly for testing)."""
    if _RegistryHolder.instance:
        _RegistryHolder.instance.clear()
    _RegistryHolder.instance = None


# Type variable for decorator
T = TypeVar("T", bound=Callable[..., Any])


def tool(
    category: ToolCategory | str = ToolCategory.OTHER,
    name: str | None = None,
    enabled: bool = True,
) -> Callable[[T], T]:
    """Decorator to register a function as a tool.

    Combines the functionality of @beta_tool (schema generation)
    with auto-registration to the global registry.

    Args:
        category: Tool category (ToolCategory enum or string)
        name: Override tool name (default: function name)
        enabled: Whether tool is enabled by default

    Returns:
        Decorated function with tool_definition attribute

    Example:
        ```python
        @tool(category="file")
        def read_file(path: str) -> str:
            '''Read a file.

            Args:
                path: File path to read
            '''
            return open(path).read()

        # Tool is auto-registered with:
        # - name: "read_file"
        # - definition: auto-generated from signature + docstring
        # - category: ToolCategory.FILE
        ```
    """
    from .tool_helpers import beta_tool  # noqa: PLC0415 - avoid circular import

    # Convert string category to enum
    if isinstance(category, str):
        try:
            cat = ToolCategory(category)
        except ValueError:
            cat = ToolCategory.OTHER
    else:
        cat = category

    def decorator(func: T) -> T:
        # First apply beta_tool to generate definition
        decorated = beta_tool(func)

        # Get generated definition
        definition: Tool = getattr(decorated, "tool_definition", {})  # type: ignore[assignment]

        # Use provided name or function name
        tool_name = name or func.__name__

        # Register with global registry
        registry = get_tool_registry()
        registry.register(
            name=tool_name,
            func=decorated,
            definition=definition,
            category=cat,
            metadata={"enabled": enabled},
        )

        # Enable/disable based on parameter
        if not enabled:
            registry.disable(tool_name)

        return decorated  # type: ignore[return-value]

    return decorator


__all__ = [
    "RegisteredTool",
    "ToolCategory",
    "ToolRegistry",
    "get_tool_registry",
    "reset_tool_registry",
    "tool",
]
