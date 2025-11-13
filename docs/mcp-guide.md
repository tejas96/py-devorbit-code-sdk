## Model Context Protocol (MCP) Support

The Devorbit SDK includes full support for the **Model Context Protocol (MCP)**, enabling your AI agents to connect to external data sources and tools exactly like Claude Code.

### What is MCP?

**MCP** is an open-source protocol that standardizes how AI applications connect to external systems. Think of it as **USB-C for AI** - a universal connector for AI models to access:

- 📝 Project management tools (Notion, Jira, ClickUp)
- 💾 Databases (PostgreSQL, MongoDB, Redis)
- 📁 File systems and cloud storage
- 🔍 Search engines and knowledge bases
- 🛠️ Development tools and APIs
- 🌐 Web services and REST APIs

### Key Benefits

✅ **Standardized Interface** - One protocol for all integrations
✅ **Tool Discovery** - AI agents automatically discover available tools
✅ **Type Safety** - Structured tool definitions with JSON schemas
✅ **Multi-Server** - Connect to multiple MCP servers simultaneously
✅ **Async Support** - Full async/await support for efficient I/O
✅ **Auto-Execution** - Seamless integration with ToolExecutor

---

## Quick Start

### Installation

```bash
pip install devorbit mcp
```

### Basic Usage

```python
import asyncio
from devorbit import AsyncDevorbit, MCPManager, ToolExecutor

async def main():
    # Load MCP servers from config
    mcp = MCPManager.from_config_file(".mcp.json")

    async with mcp:
        # Create tool executor with MCP support
        executor = ToolExecutor(mcp_manager=mcp)

        # Create AI client
        client = AsyncDevorbit(provider="anthropic", api_key="...")

        # Agent automatically has access to all MCP tools
        response = await executor.aexecute_tool_loop(
            client=client,
            messages=[{"role": "user", "content": "Fetch my Notion tasks"}],
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048
        )

asyncio.run(main())
```

---

## Configuration

### MCP Configuration File

Create a `.mcp.json` file in your project root:

```json
{
    "mcpServers": {
        "notion": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@notionhq/mcp-server-notion"],
            "env": {
                "NOTION_API_KEY": "your-api-key"
            }
        },
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
        },
        "postgres": {
            "transport": "stdio",
            "command": "python",
            "args": ["postgres_mcp_server.py"],
            "env": {
                "DATABASE_URL": "postgresql://user:pass@localhost/db"
            }
        }
    }
}
```

### Configuration Locations

The SDK searches for MCP configuration in the following order:

1. **`.mcp.json`** - Project-scoped, version-controlled
2. **`.claude/settings.local.json`** - Project-specific, local only
3. **`~/.claude/settings.local.json`** - User-specific, global

### Auto-Loading Configuration

```python
from devorbit import load_mcp_config

# Automatically finds and loads config
mcp = load_mcp_config()  # Searches standard locations

# Or specify project directory
mcp = load_mcp_config(project_dir="/path/to/project")
```

---

## Core Components

### MCPClient

Connect to a single MCP server:

```python
from devorbit import MCPClient, MCPServerConfig

# Configure server
config = MCPServerConfig(
    name="notion",
    transport="stdio",
    command="npx",
    args=["-y", "@notionhq/mcp-server-notion"],
    env={"NOTION_API_KEY": "your-key"}
)

# Connect and use
async with MCPClient(config) as client:
    # List available tools
    tools = await client.list_tools()

    # Call a tool
    result = await client.call_tool("search_pages", {"query": "sprint"})

    # List resources
    resources = await client.list_resources()

    # Read a resource
    content = await client.read_resource("resource://uri")
```

### MCPManager

Manage multiple MCP servers:

```python
from devorbit import MCPManager, MCPServerConfig

# Create manager
manager = MCPManager()

# Add servers
manager.add_server(MCPServerConfig(
    name="notion",
    transport="stdio",
    command="npx",
    args=["-y", "@notionhq/mcp-server-notion"],
    env={"NOTION_API_KEY": "key"}
))

manager.add_server(MCPServerConfig(
    name="jira",
    transport="stdio",
    command="python",
    args=["jira_server.py"],
    env={"JIRA_TOKEN": "token"}
))

# Connect to all servers
async with manager:
    # Get all tools from all servers
    all_tools = await manager.get_all_tools()
    # Returns: {"notion": [...], "jira": [...]}

    # Get flat list with server prefixes
    flat_tools = await manager.get_all_tools_flat(prefix_with_server=True)
    # Tool names: "notion__search_pages", "jira__create_issue"

    # Call tool on specific server
    result = await manager.call_tool("notion", "search_pages", {"query": "..."})
```

### Integration with ToolExecutor

The `ToolExecutor` automatically integrates MCP tools:

```python
from devorbit import ToolExecutor, MCPManager, beta_tool

# Define custom tools
@beta_tool
def calculate(expression: str) -> dict:
    """Calculate a math expression."""
    return {"result": eval(expression)}

# Load MCP servers
mcp = MCPManager.from_config_file(".mcp.json")

await mcp.connect_all()

# Create executor with both custom and MCP tools
executor = ToolExecutor(
    tools={"calculate": calculate},  # Custom tools
    mcp_manager=mcp  # MCP tools automatically added
)

# AI agent now has access to ALL tools
response = await executor.aexecute_tool_loop(
    client=client,
    messages=[...],
    model="claude-sonnet-4-5-20250929"
)
```

---

## Transport Types

### Stdio Transport

Runs MCP server as a subprocess, communicates via stdin/stdout:

```json
{
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@notionhq/mcp-server-notion"],
    "env": {
        "NOTION_API_KEY": "your-key"
    }
}
```

```python
config = MCPServerConfig(
    name="server",
    transport="stdio",
    command="node",
    args=["server.js"],
    env={"API_KEY": "key"}
)
```

### SSE Transport

Connects to remote MCP server via HTTP Server-Sent Events:

```json
{
    "transport": "sse",
    "url": "https://mcp-server.example.com/sse"
}
```

```python
config = MCPServerConfig(
    name="remote",
    transport="sse",
    url="https://mcp-server.example.com/sse"
)
```

---

## Available MCP Servers

### Official Anthropic Servers

- **`@modelcontextprotocol/server-filesystem`** - File system access
- **`@modelcontextprotocol/server-memory`** - In-memory key-value store
- **`@modelcontextprotocol/server-github`** - GitHub API integration
- **`@modelcontextprotocol/server-git`** - Git repository operations
- **`@modelcontextprotocol/server-brave-search`** - Web search

### Third-Party Servers

- **`@notionhq/mcp-server-notion`** - Notion workspace integration
- **Jira** - Custom implementations available
- **ClickUp** - Custom implementations available
- **PostgreSQL** - Database access
- **MongoDB** - NoSQL database
- **Slack** - Team communication
- **And thousands more!**

### Finding MCP Servers

Browse the MCP ecosystem:
- GitHub: [github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)
- npm: Search for "mcp-server"
- PyPI: Search for "mcp"

---

## Complete Examples

### Sprint Planning Agent

```python
"""Sprint planning agent with Notion, Jira, and ClickUp."""
import asyncio
from devorbit import AsyncDevorbit, MCPManager, ToolExecutor, beta_tool

@beta_tool
def calculate_velocity(points: int, days: int) -> dict:
    """Calculate team velocity."""
    return {"velocity": points / days}

async def main():
    # Load MCP servers (Notion, Jira, ClickUp)
    mcp = MCPManager.from_config_file(".mcp.json")

    async with mcp:
        # Create executor
        executor = ToolExecutor(
            tools={"calculate_velocity": calculate_velocity},
            mcp_manager=mcp
        )

        # Create client
        client = AsyncDevorbit(provider="anthropic", api_key="...")

        # Plan sprint using MCP tools
        response = await executor.aexecute_tool_loop(
            client=client,
            messages=[{
                "role": "user",
                "content": """Plan Sprint 42:
                1. Fetch all high-priority tasks from Notion
                2. Check Jira for blockers
                3. Create sprint in ClickUp with 40 story points
                4. Calculate expected velocity"""
            }],
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096
        )

        for block in response.content:
            if block.type == "text":
                print(block.text)

asyncio.run(main())
```

### Multi-Tool Agent

```python
"""Agent with access to files, memory, and GitHub."""
from devorbit import MCPManager, MCPServerConfig

# Create manager
mcp = MCPManager()

# Add multiple servers
mcp.add_server(MCPServerConfig(
    name="filesystem",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "."]
))

mcp.add_server(MCPServerConfig(
    name="memory",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-memory"]
))

mcp.add_server(MCPServerConfig(
    name="github",
    transport="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={"GITHUB_TOKEN": "ghp_..."}
))

async with mcp:
    executor = ToolExecutor(mcp_manager=mcp)

    response = await executor.aexecute_tool_loop(
        client=client,
        messages=[{
            "role": "user",
            "content": """
            1. Read README.md from filesystem
            2. Store summary in memory
            3. Create GitHub issue with the summary
            """
        }],
        model="claude-sonnet-4-5-20250929"
    )
```

---

## Best Practices

### 1. Security

- **Never commit API keys** - Use `.env` files or environment variables
- **Use `.claude/settings.local.json`** for sensitive configs (gitignored)
- **Limit filesystem access** - Specify exact directories in server args
- **Validate inputs** - MCP tools should validate all inputs

### 2. Error Handling

```python
async with mcp:
    try:
        result = await mcp.call_tool("notion", "search", {"query": "..."})
    except KeyError:
        print("Server not found")
    except Exception as e:
        print(f"Tool error: {e}")
```

### 3. Performance

- **Cache tool lists** - ToolExecutor caches MCP tools automatically
- **Reuse connections** - Keep MCP manager alive for multiple requests
- **Limit iterations** - Set reasonable `max_iterations` in tool loops

### 4. Tool Naming

```python
# With prefix (recommended for multiple servers)
flat_tools = await mcp.get_all_tools_flat(prefix_with_server=True)
# Tools: "notion__search", "jira__create_issue"

# Without prefix (only if no naming conflicts)
flat_tools = await mcp.get_all_tools_flat(prefix_with_server=False)
# Tools: "search", "create_issue" (may conflict!)
```

### 5. Configuration Management

```python
# Development: Local config
mcp = load_mcp_config(project_dir=".")

# Production: Programmatic config
mcp = MCPManager()
mcp.add_server(MCPServerConfig(
    name="prod_db",
    transport="stdio",
    command="python",
    args=["prod_server.py"],
    env={"DB_URL": os.environ["DATABASE_URL"]}
))
```

---

## Troubleshooting

### MCP Package Not Installed

```bash
pip install mcp
```

### Connection Errors

- Check that the server command exists: `which npx`, `which python`
- Verify server package is installed: `npx -y @notionhq/mcp-server-notion --version`
- Check environment variables are set correctly
- Review server logs (if available)

### Tool Not Found

```python
# List all available tools
tools = await mcp.get_all_tools()
for server, server_tools in tools.items():
    print(f"{server}:")
    for tool in server_tools:
        print(f"  - {tool['name']}")
```

### Import Errors

If you get `ImportError: cannot import name 'MCPClient'`:

```bash
# Reinstall with MCP support
pip install --upgrade devorbit mcp
```

---

## API Reference

### MCPServerConfig

```python
MCPServerConfig(
    name: str,                      # Server name (unique)
    transport: Literal["stdio", "sse"] = "stdio",  # Transport type
    command: Optional[str] = None,  # Command for stdio
    args: Optional[List[str]] = None,  # Command arguments
    url: Optional[str] = None,      # URL for SSE
    env: Optional[Dict[str, str]] = None  # Environment variables
)
```

### MCPClient

```python
async with MCPClient(config) as client:
    tools = await client.list_tools()
    result = await client.call_tool(name, arguments)
    resources = await client.list_resources()
    content = await client.read_resource(uri)
```

### MCPManager

```python
manager = MCPManager()
manager.add_server(config)
manager.remove_server(name)

async with manager:
    await manager.connect_all()
    tools = await manager.get_all_tools()
    tools = await manager.get_all_tools_flat(prefix_with_server=True)
    result = await manager.call_tool(server_name, tool_name, arguments)
    await manager.disconnect_all()
```

### load_mcp_config

```python
mcp = load_mcp_config(project_dir: Optional[str] = None)
# Returns MCPManager or None
```

---

## Learn More

- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **MCP Python SDK**: [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- **Example Servers**: [github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)
- **Claude Code MCP**: [docs.claude.com/mcp](https://docs.claude.com/en/docs/mcp)

---

## Next Steps

1. ✅ Install MCP: `pip install mcp`
2. ✅ Create `.mcp.json` configuration
3. ✅ Choose MCP servers for your use case
4. ✅ Build your agent with `ToolExecutor` + `MCPManager`
5. ✅ See `examples/sprint_planning_agent.py` for complete example

**Your agents now have the power to connect to any system via MCP!** 🚀
