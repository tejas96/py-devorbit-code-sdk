"""Registry Pattern implementation for CLI components.

This module provides a generic Registry pattern that can be used for:
- Tools
- Commands
- Hooks
- Providers
- Any other pluggable component

The Registry pattern enables:
- Central registration of components
- Discovery and lookup
- Plugin architecture
- Easy extension
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any, TypeVar


if TYPE_CHECKING:
    from devorbit.core.types import Tool


T = TypeVar("T")


class Registry[T]:
    """Generic registry for storing and retrieving components by name.

    A flexible registry that can store any type of component and provides:
    - Registration via register() method
    - Lookup via get() method
    - Iteration via __iter__
    - Count via __len__

    Example:
        ```python
        # Create a registry for handlers
        handler_registry = Registry[Callable]()

        # Register handlers
        handler_registry.register("bash", bash_handler)
        handler_registry.register("read", read_handler)

        # Get handler
        handler = handler_registry.get("bash")

        # Iterate all
        for name, handler in handler_registry:
            print(f"{name}: {handler}")
        ```
    """

    def __init__(self, name: str = "registry") -> None:
        """Initialize the registry.

        Args:
            name: Name of this registry (for debugging/logging)
        """
        self._name = name
        self._items: dict[str, T] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        """Get registry name."""
        return self._name

    def register(
        self,
        name: str,
        item: T,
        *,
        metadata: dict[str, Any] | None = None,
        replace: bool = False,
    ) -> T:
        """Register an item in the registry.

        Args:
            name: Unique name for the item
            item: The item to register
            metadata: Optional metadata about the item
            replace: If True, replace existing item; if False, raise on duplicate

        Returns:
            The registered item (for chaining)

        Raises:
            ValueError: If name already exists and replace=False
        """
        if name in self._items and not replace:
            raise ValueError(
                f"Item '{name}' already registered in {self._name}. Use replace=True to override."
            )

        self._items[name] = item
        if metadata:
            self._metadata[name] = metadata

        return item

    def unregister(self, name: str) -> T | None:
        """Remove an item from the registry.

        Args:
            name: Name of item to remove

        Returns:
            The removed item, or None if not found
        """
        item = self._items.pop(name, None)
        self._metadata.pop(name, None)
        return item

    def get(self, name: str) -> T | None:
        """Get an item by name.

        Args:
            name: Name of item to retrieve

        Returns:
            The item, or None if not found
        """
        return self._items.get(name)

    def get_or_raise(self, name: str) -> T:
        """Get an item by name, raising if not found.

        Args:
            name: Name of item to retrieve

        Returns:
            The item

        Raises:
            KeyError: If item not found
        """
        if name not in self._items:
            raise KeyError(f"Item '{name}' not found in {self._name}")
        return self._items[name]

    def get_metadata(self, name: str) -> dict[str, Any]:
        """Get metadata for an item.

        Args:
            name: Name of item

        Returns:
            Metadata dict (empty if no metadata)
        """
        return self._metadata.get(name, {})

    def has(self, name: str) -> bool:
        """Check if an item is registered.

        Args:
            name: Name to check

        Returns:
            True if registered
        """
        return name in self._items

    def names(self) -> list[str]:
        """Get all registered names.

        Returns:
            List of registered names
        """
        return list(self._items.keys())

    def items(self) -> list[tuple[str, T]]:
        """Get all name-item pairs.

        Returns:
            List of (name, item) tuples
        """
        return list(self._items.items())

    def values(self) -> list[T]:
        """Get all registered items.

        Returns:
            List of items
        """
        return list(self._items.values())

    def clear(self) -> None:
        """Remove all items from the registry."""
        self._items.clear()
        self._metadata.clear()

    def __len__(self) -> int:
        """Get number of registered items."""
        return len(self._items)

    def __iter__(self) -> Iterator[tuple[str, T]]:
        """Iterate over (name, item) pairs."""
        return iter(self._items.items())

    def __contains__(self, name: str) -> bool:
        """Check if name is registered."""
        return name in self._items

    def __repr__(self) -> str:
        """String representation."""
        return f"Registry(name={self._name!r}, items={len(self._items)})"


# Type alias for tool handlers
ToolHandler = Callable[[dict[str, Any]], str]


class ToolRegistry(Registry[ToolHandler]):
    """Specialized registry for CLI tools.

    Extends the generic Registry with tool-specific functionality:
    - Tool definition storage
    - SDK tool integration
    - Parameter mapping support

    Example:
        ```python
        registry = ToolRegistry()

        # Register a tool with its definition and handler
        @registry.tool(
            name="bash",
            description="Execute bash commands",
            parameters={"command": {"type": "string", "required": True}}
        )
        def bash_handler(tool_input: dict) -> str:
            return execute_bash(tool_input["command"])

        # Get tool definitions for LLM
        definitions = registry.get_definitions()

        # Execute a tool
        result = registry.execute("bash", {"command": "ls"})
        ```
    """

    def __init__(self) -> None:
        """Initialize tool registry."""
        super().__init__(name="tools")
        self._definitions: dict[str, Tool] = {}
        self._param_mappers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register_tool(
        self,
        name: str,
        handler: ToolHandler,
        definition: Tool,
        *,
        param_mapper: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        replace: bool = False,
    ) -> ToolHandler:
        """Register a tool with its handler and definition.

        Args:
            name: Tool name
            handler: Function to execute the tool
            definition: Tool definition for LLM
            param_mapper: Optional function to map LLM params to SDK params
            metadata: Optional metadata
            replace: If True, replace existing tool

        Returns:
            The handler function
        """
        # Register handler
        self.register(name, handler, metadata=metadata, replace=replace)

        # Store definition
        self._definitions[name] = definition

        # Store param mapper
        if param_mapper:
            self._param_mappers[name] = param_mapper

        return handler

    def get_definition(self, name: str) -> Tool | None:
        """Get tool definition by name.

        Args:
            name: Tool name

        Returns:
            Tool definition or None
        """
        return self._definitions.get(name)

    def get_definitions(self) -> list[Tool]:
        """Get all tool definitions.

        Returns:
            List of all tool definitions
        """
        return list(self._definitions.values())

    def execute(self, name: str, tool_input: dict[str, Any]) -> str:
        """Execute a tool by name.

        Args:
            name: Tool name
            tool_input: Tool input parameters

        Returns:
            Tool execution result

        Raises:
            KeyError: If tool not found
        """
        handler = self.get_or_raise(name)

        # Apply param mapper if exists
        mapper = self._param_mappers.get(name)
        if mapper:
            tool_input = mapper(tool_input)

        return handler(tool_input)

    def tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        *,
        required: list[str] | None = None,
        param_mapper: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> Callable[[ToolHandler], ToolHandler]:
        """Decorator to register a tool.

        Example:
            ```python
            @registry.tool(
                name="bash",
                description="Execute bash commands",
                parameters={
                    "command": {"type": "string", "description": "Command to run"}
                },
                required=["command"]
            )
            def bash_handler(tool_input: dict) -> str:
                return run_command(tool_input["command"])
            ```

        Args:
            name: Tool name
            description: Tool description
            parameters: Parameter definitions
            required: List of required parameter names
            param_mapper: Optional parameter mapping function

        Returns:
            Decorator function
        """

        def decorator(func: ToolHandler) -> ToolHandler:
            # Build tool definition
            definition: Tool = {
                "name": name,
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": parameters,
                    "required": required or [],
                },
            }

            # Register
            self.register_tool(
                name=name,
                handler=func,
                definition=definition,
                param_mapper=param_mapper,
            )

            return func

        return decorator


# Global tool registry instance (module-level singleton)
class _ToolRegistrySingleton:
    """Singleton holder for global tool registry."""

    _instance: ToolRegistry | None = None

    @classmethod
    def get(cls) -> ToolRegistry:
        """Get the global tool registry."""
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the global tool registry (for testing)."""
        cls._instance = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry.

    Returns:
        The global ToolRegistry instance
    """
    return _ToolRegistrySingleton.get()


def reset_tool_registry() -> None:
    """Reset the global tool registry (for testing)."""
    _ToolRegistrySingleton.reset()
