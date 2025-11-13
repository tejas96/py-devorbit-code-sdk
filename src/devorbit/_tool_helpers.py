"""Tool helpers for easy tool definition and execution.

This module provides utilities similar to Claude SDK's beta tool helpers.
"""

import asyncio
import inspect
import json
from functools import wraps
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union, get_type_hints

from pydantic import BaseModel, create_model

from ._models import MessageResponse, ToolUseBlock
from ._types import Message, Tool

if TYPE_CHECKING:
    from ._mcp import MCPManager

T = TypeVar("T")


def beta_tool(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to convert a Python function into a tool definition.

    This mirrors Claude SDK's @beta_tool decorator.

    Example:
        ```python
        @beta_tool
        def get_weather(location: str, unit: str = "celsius") -> dict:
            '''Get the weather for a location.

            Args:
                location: The city name
                unit: Temperature unit (celsius or fahrenheit)
            '''
            return {"temp": 22, "unit": unit}

        # Automatically creates tool definition
        tool_def = get_weather.tool_definition
        ```
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return func(*args, **kwargs)

    # Extract function signature
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    doc = inspect.getdoc(func) or ""

    # Build input schema from function signature
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        if param_name == "self":
            continue

        param_type = type_hints.get(param_name, Any)
        param_schema = _python_type_to_json_schema(param_type)

        # Extract parameter description from docstring
        param_desc = _extract_param_description(doc, param_name)
        if param_desc:
            param_schema["description"] = param_desc

        properties[param_name] = param_schema

        # Required if no default value
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    # Create tool definition
    tool_def: Tool = {
        "name": func.__name__,
        "description": doc.split("\n\n")[0] if doc else f"Function {func.__name__}",
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required if required else [],
        },
    }

    # Attach tool definition to function
    wrapper.tool_definition = tool_def  # type: ignore
    wrapper.is_tool = True  # type: ignore

    return wrapper  # type: ignore


def _python_type_to_json_schema(python_type: Any) -> Dict[str, Any]:
    """Convert Python type to JSON schema type."""
    type_map = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }

    # Handle Optional types
    if hasattr(python_type, "__origin__"):
        if python_type.__origin__ is Union:
            # Check if it's Optional (Union with None)
            args = python_type.__args__
            if type(None) in args:
                # It's Optional, use the non-None type
                non_none_type = [t for t in args if t != type(None)][0]
                return _python_type_to_json_schema(non_none_type)

    return type_map.get(python_type, {"type": "string"})


def _extract_param_description(docstring: str, param_name: str) -> Optional[str]:
    """Extract parameter description from Google-style docstring."""
    lines = docstring.split("\n")
    in_args_section = False

    for i, line in enumerate(lines):
        if "Args:" in line or "Arguments:" in line:
            in_args_section = True
            continue

        if in_args_section:
            if line.strip().startswith(param_name + ":"):
                desc = line.split(":", 1)[1].strip()
                return desc
            elif line.strip() and not line.startswith(" "):
                # End of args section
                break

    return None


def gather_tools(obj: Any) -> List[Tool]:
    """Gather all tools from an object (class instance or module).

    Args:
        obj: Object to search for tools

    Returns:
        List of tool definitions
    """
    tools = []

    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue

        attr = getattr(obj, attr_name)
        if hasattr(attr, "is_tool") and hasattr(attr, "tool_definition"):
            tools.append(attr.tool_definition)

    return tools


class ToolExecutor:
    """Automatic tool execution helper with MCP support.

    This class helps execute tools automatically in a loop, similar to
    Claude SDK's tool execution runners. It supports both regular tools
    and MCP (Model Context Protocol) tools.

    Example:
        ```python
        # Regular tools
        executor = ToolExecutor(tools_dict)
        result = executor.execute_tool_loop(client, initial_messages)

        # With MCP support
        from devorbit import MCPManager
        mcp = MCPManager.from_config_file(".mcp.json")
        executor = ToolExecutor(tools_dict, mcp_manager=mcp)
        result = await executor.aexecute_tool_loop(client, initial_messages)
        ```
    """

    def __init__(
        self,
        tools: Optional[Dict[str, Callable]] = None,
        mcp_manager: Optional["MCPManager"] = None,
    ) -> None:
        """Initialize tool executor.

        Args:
            tools: Dictionary mapping tool names to callable functions
            mcp_manager: Optional MCP manager for MCP tool support
        """
        self.tools = tools or {}
        self.mcp_manager = mcp_manager
        self._mcp_tools_cache: Optional[List[Dict[str, Any]]] = None

    async def _get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions including MCP tools.

        Returns:
            List of all tool definitions
        """
        definitions = [
            func.tool_definition
            for func in self.tools.values()
            if hasattr(func, "tool_definition")
        ]

        # Add MCP tools
        if self.mcp_manager:
            if self._mcp_tools_cache is None:
                self._mcp_tools_cache = await self.mcp_manager.get_all_tools_flat(
                    prefix_with_server=True
                )
            definitions.extend(self._mcp_tools_cache)

        return definitions

    def execute_tool(self, tool_use: ToolUseBlock) -> Any:
        """Execute a single tool.

        Args:
            tool_use: Tool use block from model response

        Returns:
            Tool execution result
        """
        tool_func = self.tools.get(tool_use.name)
        if not tool_func:
            return {"error": f"Tool '{tool_use.name}' not found"}

        try:
            result = tool_func(**tool_use.input)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def aexecute_tool(self, tool_use: ToolUseBlock) -> Any:
        """Execute a single tool asynchronously (supports MCP tools).

        Args:
            tool_use: Tool use block from model response

        Returns:
            Tool execution result
        """
        # Check if it's an MCP tool (prefixed with server name)
        if self.mcp_manager and "__" in tool_use.name:
            server_name, tool_name = tool_use.name.split("__", 1)
            if server_name in self.mcp_manager.clients:
                try:
                    result = await self.mcp_manager.call_tool(
                        server_name, tool_name, tool_use.input
                    )
                    return result
                except Exception as e:
                    return {"error": f"MCP tool error: {str(e)}"}

        # Regular tool
        tool_func = self.tools.get(tool_use.name)
        if not tool_func:
            return {"error": f"Tool '{tool_use.name}' not found"}

        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**tool_use.input)
            else:
                result = tool_func(**tool_use.input)
            return result
        except Exception as e:
            return {"error": str(e)}

    def execute_tool_loop(
        self,
        client: Any,
        messages: List[Message],
        model: str,
        max_tokens: int = 1024,
        max_iterations: int = 10,
        **kwargs: Any,
    ) -> MessageResponse:
        """Execute tools in a loop until completion.

        Args:
            client: Devorbit client instance
            messages: Initial messages
            model: Model to use
            max_tokens: Maximum tokens per request
            max_iterations: Maximum tool execution iterations
            **kwargs: Additional parameters for message creation

        Returns:
            Final message response
        """
        tool_definitions = [
            func.tool_definition
            for func in self.tools.values()
            if hasattr(func, "tool_definition")
        ]

        current_messages = messages.copy()

        for _ in range(max_iterations):
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=current_messages,
                tools=tool_definitions,
                **kwargs,
            )

            if response.stop_reason != "tool_use":
                return response

            # Execute tools
            tool_results = []
            assistant_content = []

            for block in response.content:
                if isinstance(block, ToolUseBlock):
                    result = self.execute_tool(block)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )
                    assistant_content.append(
                        {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                    )
                else:
                    assistant_content.append({"type": "text", "text": getattr(block, "text", "")})

            # Add assistant message and tool results
            current_messages.append({"role": "assistant", "content": assistant_content})
            current_messages.append({"role": "user", "content": tool_results})

        # Max iterations reached
        return response

    async def aexecute_tool_loop(
        self,
        client: Any,
        messages: List[Message],
        model: str,
        max_tokens: int = 1024,
        max_iterations: int = 10,
        **kwargs: Any,
    ) -> MessageResponse:
        """Execute tools in a loop asynchronously until completion.

        Supports both regular tools and MCP tools automatically.

        Args:
            client: AsyncDevorbit client instance
            messages: Initial messages
            model: Model to use
            max_tokens: Maximum tokens per request
            max_iterations: Maximum tool execution iterations
            **kwargs: Additional parameters for message creation

        Returns:
            Final message response
        """
        # Get all tool definitions (regular + MCP)
        tool_definitions = await self._get_all_tool_definitions()

        current_messages = messages.copy()

        for _ in range(max_iterations):
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=current_messages,
                tools=tool_definitions,
                **kwargs,
            )

            if response.stop_reason != "tool_use":
                return response

            # Execute tools
            tool_results = []
            assistant_content = []

            for block in response.content:
                if isinstance(block, ToolUseBlock):
                    result = await self.aexecute_tool(block)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result,
                        }
                    )
                    assistant_content.append(
                        {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                    )
                else:
                    assistant_content.append({"type": "text", "text": getattr(block, "text", "")})

            # Add assistant message and tool results
            current_messages.append({"role": "assistant", "content": assistant_content})
            current_messages.append({"role": "user", "content": tool_results})

        # Max iterations reached
        return response
