"""Model Context Protocol (MCP) integration.

This module provides MCP client functionality to connect to MCP servers
and use their tools with the Devorbit SDK, exactly like Claude Code.
"""

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from mcp import ClientSession, StdioServerParameters

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.sse import sse_client
    from mcp.client.stdio import stdio_client

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    if not TYPE_CHECKING:
        ClientSession = None  # type: ignore[assignment,misc]
        StdioServerParameters = None  # type: ignore[assignment,misc]


TransportType = Literal["stdio", "sse"]


class MCPServerConfig:
    """Configuration for an MCP server connection."""

    def __init__(
        self,
        name: str,
        transport: TransportType = "stdio",
        command: str | None = None,
        args: list[str] | None = None,
        url: str | None = None,
        env: dict[str, str] | None = None,
    ):
        """Initialize MCP server configuration.

        Args:
            name: Name of the MCP server
            transport: Transport type ("stdio" or "sse")
            command: Command to run the server (for stdio)
            args: Arguments for the server command (for stdio)
            url: URL for the server (for sse)
            env: Environment variables for the server
        """
        self.name = name
        self.transport = transport
        self.command = command
        self.args = args or []
        self.url = url
        self.env = env or {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPServerConfig":
        """Create config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            MCPServerConfig instance
        """
        return cls(
            name=data["name"],
            transport=data.get("transport", "stdio"),
            command=data.get("command"),
            args=data.get("args", []),
            url=data.get("url"),
            env=data.get("env", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "name": self.name,
            "transport": self.transport,
            "command": self.command,
            "args": self.args,
            "url": self.url,
            "env": self.env,
        }


class MCPClient:
    """MCP client for connecting to MCP servers and accessing their tools."""

    def __init__(self, server_config: MCPServerConfig):
        """Initialize MCP client.

        Args:
            server_config: Server configuration

        Raises:
            ImportError: If mcp package is not installed
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP support requires the 'mcp' package. " "Install it with: pip install mcp"
            )

        self.config = server_config
        self.session: ClientSession | None = None
        self._read: Any = None
        self._write: Any = None
        self._client_context: Any = None
        self._session_context: Any = None

    async def __aenter__(self) -> "MCPClient":
        """Connect to MCP server.

        Returns:
            Self for context manager
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Disconnect from MCP server."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self.config.transport == "stdio":
            if not self.config.command:
                raise ValueError("stdio transport requires 'command' in config")

            server_params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env if self.config.env else None,
            )

            self._client_context = stdio_client(server_params)
            self._read, self._write = await self._client_context.__aenter__()

        elif self.config.transport == "sse":
            if not self.config.url:
                raise ValueError("sse transport requires 'url' in config")

            self._client_context = sse_client(self.config.url)
            self._read, self._write = await self._client_context.__aenter__()

        else:
            raise ValueError(f"Unsupported transport: {self.config.transport}")

        # Create session
        self._session_context = ClientSession(self._read, self._write)
        self.session = await self._session_context.__aenter__()

        # Initialize connection
        await self.session.initialize()

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
            self._session_context = None
            self.session = None

        if self._client_context:
            await self._client_context.__aexit__(None, None, None)
            self._client_context = None
            self._read = None
            self._write = None

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the MCP server.

        Returns:
            List of tool definitions

        Raises:
            RuntimeError: If not connected to server
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        response = await self.session.list_tools()

        # Convert MCP tools to our tool format
        tools = []
        for tool in response.tools:
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                }
            )

        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            RuntimeError: If not connected to server
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        result = await self.session.call_tool(name, arguments=arguments)

        # Extract content from result
        if hasattr(result, "content") and result.content:
            # MCP returns a list of content blocks
            content_parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    content_parts.append(content.text)
                elif hasattr(content, "data"):
                    content_parts.append(content.data)

            if len(content_parts) == 1:
                return content_parts[0]
            return content_parts

        return result

    async def list_resources(self) -> list[dict[str, Any]]:
        """List available resources from the MCP server.

        Returns:
            List of resource definitions

        Raises:
            RuntimeError: If not connected to server
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        response = await self.session.list_resources()

        resources = []
        for resource in response.resources:
            resources.append(
                {
                    "uri": resource.uri,
                    "name": resource.name or "",
                    "description": resource.description or "",
                    "mimeType": getattr(resource, "mimeType", None),
                }
            )

        return resources

    async def read_resource(self, uri: str) -> Any:
        """Read a resource from the MCP server.

        Args:
            uri: Resource URI

        Returns:
            Resource content

        Raises:
            RuntimeError: If not connected to server
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")

        result = await self.session.read_resource(uri)  # type: ignore[arg-type]

        # Extract content
        if hasattr(result, "contents") and result.contents:
            content_parts = []
            for content in result.contents:
                if hasattr(content, "text"):
                    content_parts.append(content.text)
                elif hasattr(content, "blob"):
                    content_parts.append(content.blob)

            if len(content_parts) == 1:
                return content_parts[0]
            return content_parts

        return result


class MCPManager:
    """Manager for multiple MCP server connections."""

    def __init__(self) -> None:
        """Initialize MCP manager."""
        self.clients: dict[str, MCPClient] = {}
        self._connected = False

    @classmethod
    def from_config_file(cls, config_path: str | Path) -> "MCPManager":
        """Load MCP servers from a configuration file.

        Config file format (.mcp.json or .claude/settings.local.json):
        {
            "mcpServers": {
                "notion": {
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "@notionhq/mcp-server-notion"]
                },
                "jira": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["path/to/jira_mcp_server.py"]
                }
            }
        }

        Args:
            config_path: Path to configuration file

        Returns:
            MCPManager instance with loaded servers
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_path.open() as f:
            config = json.load(f)

        manager = cls()

        # Load servers from config
        mcp_servers = config.get("mcpServers", {})
        for name, server_config in mcp_servers.items():
            server_config["name"] = name
            config_obj = MCPServerConfig.from_dict(server_config)
            manager.add_server(config_obj)

        return manager

    def add_server(self, config: MCPServerConfig) -> None:
        """Add an MCP server.

        Args:
            config: Server configuration
        """
        client = MCPClient(config)
        self.clients[config.name] = client

    def remove_server(self, name: str) -> None:
        """Remove an MCP server.

        Args:
            name: Server name
        """
        if name in self.clients:
            del self.clients[name]

    async def connect_all(self) -> None:
        """Connect to all MCP servers."""
        tasks = []
        for client in self.clients.values():
            tasks.append(client.connect())

        await asyncio.gather(*tasks)
        self._connected = True

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        tasks = []
        for client in self.clients.values():
            tasks.append(client.disconnect())

        await asyncio.gather(*tasks)
        self._connected = False

    async def get_all_tools(self) -> dict[str, list[dict[str, Any]]]:
        """Get tools from all connected MCP servers.

        Returns:
            Dictionary mapping server names to their tool lists

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect_all() first.")

        tools_by_server = {}
        for name, client in self.clients.items():
            tools_by_server[name] = await client.list_tools()

        return tools_by_server

    async def get_all_tools_flat(self, prefix_with_server: bool = True) -> list[dict[str, Any]]:
        """Get all tools from all servers as a flat list.

        Args:
            prefix_with_server: Whether to prefix tool names with server name

        Returns:
            List of all tool definitions

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect_all() first.")

        all_tools = []
        for name, client in self.clients.items():
            tools = await client.list_tools()
            if prefix_with_server:
                # Prefix tool names with server name to avoid conflicts
                for tool in tools:
                    tool["name"] = f"{name}__{tool['name']}"
                    tool["_mcp_server"] = name
                    tool["_original_name"] = tool["name"].replace(f"{name}__", "")
            all_tools.extend(tools)

        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on a specific MCP server.

        Args:
            server_name: Server name
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            KeyError: If server not found
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected. Call connect_all() first.")

        if server_name not in self.clients:
            raise KeyError(f"MCP server not found: {server_name}")

        return await self.clients[server_name].call_tool(tool_name, arguments)

    async def __aenter__(self) -> "MCPManager":
        """Connect to all servers."""
        await self.connect_all()
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Disconnect from all servers."""
        await self.disconnect_all()


def load_mcp_config(
    project_dir: str | Path | None = None,
) -> MCPManager | None:
    """Load MCP configuration from standard locations.

    Searches for MCP config in:
    1. .mcp.json (project-scoped, version-controlled)
    2. .claude/settings.local.json (project-specific)
    3. ~/.claude/settings.local.json (user-specific)

    Args:
        project_dir: Project directory to search in (defaults to current directory)

    Returns:
        MCPManager with loaded servers, or None if no config found
    """
    project_dir = Path.cwd() if project_dir is None else Path(project_dir)

    # Search paths in priority order
    search_paths = [
        project_dir / ".mcp.json",
        project_dir / ".claude" / "settings.local.json",
        Path.home() / ".claude" / "settings.local.json",
    ]

    for config_path in search_paths:
        if config_path.exists():
            try:
                return MCPManager.from_config_file(config_path)
            except Exception:
                # Try next config file if current one fails
                continue

    return None
