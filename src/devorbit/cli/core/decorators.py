"""Decorator Pattern implementations for CLI components.

This module provides decorators for easy registration of:
- Tools
- Commands
- Hooks

Decorators enable:
- Clean, declarative registration
- Automatic metadata extraction
- Type safety
- Reduced boilerplate
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

from .registry import ToolHandler, ToolRegistry, get_tool_registry


if TYPE_CHECKING:
    from devorbit._types import Tool


F = TypeVar("F", bound=Callable[..., Any])


def cli_tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    *,
    required: list[str] | None = None,
    param_mapper: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    registry: ToolRegistry | None = None,
) -> Callable[[ToolHandler], ToolHandler]:
    """Decorator to register a CLI tool.

    This decorator registers a function as a CLI tool, creating the
    tool definition and adding it to the registry.

    Example:
        ```python
        @cli_tool(
            name="bash",
            description="Execute bash commands",
            parameters={
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds"
                }
            },
            required=["command"]
        )
        def execute_bash(tool_input: dict) -> str:
            command = tool_input["command"]
            return run_bash(command)
        ```

    Args:
        name: Tool name (used by LLM)
        description: Tool description (shown to LLM)
        parameters: Parameter definitions (JSON schema style)
        required: List of required parameter names
        param_mapper: Optional function to transform params before execution
        registry: Optional custom registry (uses global if not provided)

    Returns:
        Decorator function
    """
    reg = registry or get_tool_registry()

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

        # Register tool
        reg.register_tool(
            name=name,
            handler=func,
            definition=definition,
            param_mapper=param_mapper,
        )

        # Preserve function metadata
        @wraps(func)
        def wrapper(tool_input: dict[str, Any]) -> str:
            return func(tool_input)

        return wrapper

    return decorator


def register_tool(
    definition: Tool,
    *,
    param_mapper: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    registry: ToolRegistry | None = None,
) -> Callable[[ToolHandler], ToolHandler]:
    """Decorator to register a tool with an existing definition.

    Use this when you already have a tool definition (e.g., from SDK)
    and want to register a handler for it.

    Example:
        ```python
        from devorbit._bash_tools import bash

        @register_tool(definition=bash.tool_definition)
        def bash_handler(tool_input: dict) -> str:
            result = bash(command=tool_input["command"])
            return format_result(result)
        ```

    Args:
        definition: Tool definition (from SDK or custom)
        param_mapper: Optional function to transform params
        registry: Optional custom registry

    Returns:
        Decorator function
    """
    reg = registry or get_tool_registry()
    tool_name = definition["name"]

    def decorator(func: ToolHandler) -> ToolHandler:
        reg.register_tool(
            name=tool_name,
            handler=func,
            definition=definition,
            param_mapper=param_mapper,
        )

        @wraps(func)
        def wrapper(tool_input: dict[str, Any]) -> str:
            return func(tool_input)

        return wrapper

    return decorator


def with_validation(
    validator: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> Callable[[ToolHandler], ToolHandler]:
    """Decorator to add input validation to a tool handler.

    The validator function should:
    - Return None if validation passes
    - Return error dict if validation fails

    Example:
        ```python
        def validate_path(tool_input: dict) -> dict | None:
            path = tool_input.get("path", "")
            if ".." in path:
                return {"error": "Path traversal not allowed"}
            return None

        @with_validation(validate_path)
        @cli_tool(name="read", ...)
        def read_file(tool_input: dict) -> str:
            ...
        ```

    Args:
        validator: Validation function

    Returns:
        Decorator function
    """

    def decorator(func: ToolHandler) -> ToolHandler:
        @wraps(func)
        def wrapper(tool_input: dict[str, Any]) -> str:
            # Run validation
            error = validator(tool_input)
            if error:
                return f"Validation error: {error.get('error', 'Unknown error')}"
            return func(tool_input)

        return wrapper

    return decorator


def with_logging(
    log_func: Callable[[str], None] | None = None,
) -> Callable[[F], F]:
    """Decorator to add logging to tool execution.

    Example:
        ```python
        @with_logging(lambda msg: print(f"[TOOL] {msg}"))
        @cli_tool(name="bash", ...)
        def bash_handler(tool_input: dict) -> str:
            ...
        ```

    Args:
        log_func: Logging function (defaults to print)

    Returns:
        Decorator function
    """
    log = log_func or print

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            log(f"Executing {func_name}...")
            try:
                result = func(*args, **kwargs)
                log(f"Completed {func_name}")
                return result
            except Exception as e:
                log(f"Error in {func_name}: {e}")
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def with_error_handling(
    error_handler: Callable[[Exception], str] | None = None,
) -> Callable[[ToolHandler], ToolHandler]:
    """Decorator to add error handling to tool execution.

    Example:
        ```python
        def handle_error(e: Exception) -> str:
            return f"Tool failed: {type(e).__name__}: {e}"

        @with_error_handling(handle_error)
        @cli_tool(name="risky_tool", ...)
        def risky_handler(tool_input: dict) -> str:
            ...
        ```

    Args:
        error_handler: Function to handle exceptions

    Returns:
        Decorator function
    """

    def default_handler(e: Exception) -> str:
        return f"Error: {type(e).__name__}: {e}"

    handler = error_handler or default_handler

    def decorator(func: ToolHandler) -> ToolHandler:
        @wraps(func)
        def wrapper(tool_input: dict[str, Any]) -> str:
            try:
                return func(tool_input)
            except Exception as e:
                return handler(e)

        return wrapper

    return decorator
