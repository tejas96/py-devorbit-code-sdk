# Current Tools Available in Devorbit SDK

**Last Updated:** 2025-11-14
**Version:** 0.1.0

---

## Overview

This document lists all tools currently available in the Devorbit Multi-LLM SDK.

---

## Built-in Agent Tools (3 Tools)

### 1. Computer Use Tool
**Function:** `create_computer_use_tool(display_width_px, display_height_px, display_number)`
**Type:** `computer_20241022`
**Purpose:** Control computer interfaces (mouse, keyboard, screen)
**Capabilities:**
- Move mouse cursor
- Click and drag
- Type text
- Take screenshots
- Control GUI applications

**Example:**
```python
from devorbit import create_computer_use_tool

tool = create_computer_use_tool(
    display_width_px=1920,
    display_height_px=1080,
    display_number=1
)

# Use in message
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    tools=[tool],
    messages=[{"role": "user", "content": "Open browser and search for Python"}]
)
```

---

### 2. Bash Tool
**Function:** `create_bash_tool()`
**Type:** `bash_20241022`
**Purpose:** Execute shell commands
**Capabilities:**
- Run bash commands
- Execute scripts
- System operations
- Command-line tools

**Example:**
```python
from devorbit import create_bash_tool

tool = create_bash_tool()

# Use in message
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    tools=[tool],
    messages=[{"role": "user", "content": "List files in current directory"}]
)
```

**Note:** Current implementation is basic. Does not support:
- Persistent sessions
- Environment inheritance
- Working directory management
- Background processes

---

### 3. Text Editor Tool
**Function:** `create_text_editor_tool()`
**Type:** `text_editor_20241022`
**Purpose:** File manipulation (read, write, edit)
**Capabilities:**
- Create files
- Read file contents
- Edit files
- Delete files

**Example:**
```python
from devorbit import create_text_editor_tool

tool = create_text_editor_tool()

# Use in message
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    tools=[tool],
    messages=[{"role": "user", "content": "Create a Python script that prints hello"}]
)
```

**Note:** Basic implementation. Claude Code has more sophisticated file tools.

---

### Get All Built-in Tools

**Function:** `get_all_builtin_tools(include_bash, include_editor, include_computer)`

```python
from devorbit import get_all_builtin_tools

# Get all tools
tools = get_all_builtin_tools(
    include_bash=True,
    include_editor=True,
    include_computer=True
)

# Get only bash and editor
tools = get_all_builtin_tools(
    include_bash=True,
    include_editor=True,
    include_computer=False
)
```

---

## Tool Helper Utilities (3 Utilities)

### 1. @beta_tool Decorator
**Purpose:** Auto-generate tool definitions from Python functions
**Features:**
- Extract function signature
- Parse docstrings
- Generate JSON schema
- Type hint support

**Example:**
```python
from devorbit import beta_tool

@beta_tool
def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get weather for a location.

    Args:
        location: City name or coordinates
        unit: Temperature unit (celsius or fahrenheit)

    Returns:
        Weather data dictionary
    """
    # Implementation
    return {"temp": 22, "location": location, "unit": unit}

# Automatically generates tool definition:
# {
#     "name": "get_weather",
#     "description": "Get weather for a location.",
#     "input_schema": {
#         "type": "object",
#         "properties": {
#             "location": {"type": "string", "description": "..."},
#             "unit": {"type": "string", "description": "...", "default": "celsius"}
#         },
#         "required": ["location"]
#     }
# }
```

---

### 2. ToolExecutor Class
**Purpose:** Automatic tool execution loops
**Features:**
- Execute single tools
- Automatic multi-turn loops
- MCP integration
- Async support

**Methods:**
- `execute_tool(tool_name, tool_input)` - Execute single tool (sync)
- `aexecute_tool(tool_name, tool_input)` - Execute single tool (async)
- `execute_tool_loop(client, messages, model, ...)` - Auto loop (sync)
- `aexecute_tool_loop(client, messages, model, ...)` - Auto loop (async)

**Example:**
```python
from devorbit import Devorbit, ToolExecutor, beta_tool

@beta_tool
def get_weather(location: str) -> dict:
    return {"temp": 22, "location": location}

@beta_tool
def search(query: str) -> dict:
    return {"results": ["result1", "result2"]}

# Create executor
tools = {"get_weather": get_weather, "search": search}
executor = ToolExecutor(tools)

# Automatic execution loop
client = Devorbit(provider="anthropic", api_key="...")
response = executor.execute_tool_loop(
    client=client,
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048
)
```

**With MCP:**
```python
from devorbit import AsyncDevorbit, ToolExecutor, MCPManager

async def main():
    # Load MCP servers
    mcp = MCPManager.from_config_file(".mcp.json")

    async with mcp:
        # Executor automatically includes MCP tools
        executor = ToolExecutor(mcp_manager=mcp)

        client = AsyncDevorbit(provider="anthropic", api_key="...")
        response = await executor.aexecute_tool_loop(
            client=client,
            messages=[{"role": "user", "content": "Fetch my Notion tasks"}],
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096
        )
```

---

### 3. gather_tools() Function
**Purpose:** Collect all @beta_tool decorated methods from a class/module
**Returns:** List of tool definitions

**Example:**
```python
from devorbit import beta_tool, gather_tools

class WeatherService:
    @beta_tool
    def get_weather(self, location: str) -> dict:
        """Get current weather."""
        return {"temp": 22}

    @beta_tool
    def get_forecast(self, location: str, days: int) -> dict:
        """Get weather forecast."""
        return {"forecast": [...]}

# Gather all tools from class
service = WeatherService()
tools = gather_tools(service)

# Returns list of tool definitions
# [
#     {"name": "get_weather", "description": "...", "input_schema": {...}},
#     {"name": "get_forecast", "description": "...", "input_schema": {...}}
# ]
```

---

## MCP (Model Context Protocol) Tools

### 1. MCPClient
**Purpose:** Connect to single MCP server
**Methods:**
- `list_tools()` - Get available tools
- `call_tool(name, arguments)` - Execute a tool
- `list_resources()` - Get available resources
- `read_resource(uri)` - Read a resource

**Example:**
```python
from devorbit import MCPClient, MCPServerConfig
import asyncio

async def main():
    config = MCPServerConfig(
        name="notion",
        transport="stdio",
        command="npx",
        args=["-y", "@notionhq/mcp-server-notion"],
        env={"NOTION_API_KEY": "your-key"}
    )

    async with MCPClient(config) as client:
        # List tools
        tools = await client.list_tools()
        print(f"Available tools: {tools}")

        # Call tool
        result = await client.call_tool(
            "notion_search",
            {"query": "project tasks"}
        )
        print(result)

asyncio.run(main())
```

---

### 2. MCPManager
**Purpose:** Manage multiple MCP servers
**Methods:**
- `add_server(name, config)` - Add server
- `remove_server(name)` - Remove server
- `connect_all()` - Connect all servers
- `disconnect_all()` - Disconnect all
- `get_all_tools()` - Get tools by server
- `get_all_tools_flat()` - All tools with prefixes
- `call_tool(server_name, tool_name, args)` - Call tool on server

**Example:**
```python
from devorbit import MCPManager, MCPServerConfig
import asyncio

async def main():
    # Create manager
    manager = MCPManager()

    # Add servers
    manager.add_server("notion", MCPServerConfig(
        name="notion",
        transport="stdio",
        command="npx",
        args=["-y", "@notionhq/mcp-server-notion"],
        env={"NOTION_API_KEY": "your-key"}
    ))

    manager.add_server("jira", MCPServerConfig(
        name="jira",
        transport="stdio",
        command="python",
        args=["jira_server.py"],
        env={"JIRA_TOKEN": "your-token"}
    ))

    async with manager:
        # Get all tools
        all_tools = await manager.get_all_tools_flat()
        print(f"Total tools: {len(all_tools)}")
        # Tools are prefixed: notion__search, jira__get_issue, etc.

        # Call specific tool
        result = await manager.call_tool(
            "notion",
            "notion_search",
            {"query": "tasks"}
        )

asyncio.run(main())
```

---

### 3. Load MCP Config
**Function:** `load_mcp_config(config_path)`
**Purpose:** Load MCP servers from config file
**Search Paths:**
1. `.mcp.json` (project-scoped)
2. `.claude/settings.local.json` (project-local)
3. `~/.claude/settings.local.json` (user-global)

**Config Format (.mcp.json):**
```json
{
    "mcpServers": {
        "notion": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@notionhq/mcp-server-notion"],
            "env": {
                "NOTION_API_KEY": "your-key"
            }
        },
        "jira": {
            "transport": "stdio",
            "command": "python",
            "args": ["jira_server.py"],
            "env": {
                "JIRA_TOKEN": "your-token"
            }
        }
    }
}
```

**Example:**
```python
from devorbit import MCPManager

# Auto-load from config
manager = MCPManager.from_config_file(".mcp.json")

# Or load from specific path
manager = MCPManager.from_config_file("/path/to/config.json")
```

---

## Available MCP Servers (External)

These servers can be connected via MCP:

### **Project Management**
- `@notionhq/mcp-server-notion` - Notion integration
- `jira-mcp-server` - Jira integration
- `clickup-mcp-server` - ClickUp integration

### **Databases**
- `mcp-server-postgresql` - PostgreSQL access
- `mcp-server-mongodb` - MongoDB access
- `mcp-server-redis` - Redis access

### **Storage**
- `mcp-server-filesystem` - File system access
- `mcp-server-memory` - In-memory storage

### **Web & APIs**
- `mcp-server-puppeteer` - Browser automation
- `mcp-server-fetch` - HTTP requests
- `mcp-server-github` - GitHub API

### **Custom Servers**
You can create your own MCP servers using the MCP protocol.

---

## Tool Count Summary

| Category | Count | Tools |
|----------|-------|-------|
| **Built-in Agent Tools** | 3 | Computer Use, Bash, Text Editor |
| **Tool Helpers** | 3 | @beta_tool, ToolExecutor, gather_tools |
| **MCP Integration** | 3 | MCPClient, MCPManager, load_mcp_config |
| **Total SDK Tools** | 9 | - |
| **MCP External Tools** | ∞ | Via MCP servers (Notion, Jira, DBs, etc.) |

---

## Comparison with Claude Code Tools

| Tool Type | Our SDK | Claude Code |
|-----------|---------|-------------|
| **Agent Tools** | 3 (Computer, Bash, Editor) | 3 (Same) |
| **File Operations** | ❌ 0 tools | ✅ 4 tools (Read, Edit, Write, MultiEdit) |
| **Search Tools** | ❌ 0 tools | ✅ 2 tools (Glob, Grep) |
| **Web Tools** | ❌ 0 tools | ✅ 2 tools (WebFetch, WebSearch) |
| **Workflow Tools** | ❌ 0 tools | ✅ 3 tools (Todo, Task, Skill) |
| **Notebook Tools** | ⚠️ 1 (NotebookEdit in types) | ✅ 2 tools (NotebookRead, NotebookEdit) |
| **MCP Integration** | ✅ Full support | ✅ Full support |
| **Tool Helpers** | ✅ 3 helpers | ⚠️ Limited |

**Total Built-in Tools:**
- Our SDK: 3 agent tools + MCP
- Claude Code: 15+ tools + MCP

---

## What's Missing

### **Critical Missing Tools** (Cannot function as coding agent without these)
1. ❌ **Read Tool** - Read files from filesystem
2. ❌ **Edit Tool** - Safe string replacement in files
3. ❌ **Write Tool** - Create new files
4. ❌ **Glob Tool** - Find files by patterns
5. ❌ **Grep Tool** - Search file contents

### **Important Missing Tools** (Significant functionality gaps)
6. ❌ **MultiEdit Tool** - Edit multiple files at once
7. ❌ **WebFetch Tool** - Fetch and process web content
8. ❌ **WebSearch Tool** - Search the web
9. ❌ **TodoWrite/TodoRead** - Task management
10. ❌ **Task Tool** - Launch subagents

### **Nice to Have Tools** (Enhancement opportunities)
11. ❌ **NotebookRead Tool** - Read Jupyter notebooks (have edit only)
12. ❌ **Skill Tool** - Execute pre-defined skills
13. ❌ **SlashCommand Tool** - Custom command shortcuts

---

## Usage Examples

### Example 1: Using Built-in Tools
```python
from devorbit import Devorbit, get_all_builtin_tools

client = Devorbit(provider="anthropic", api_key="...")

tools = get_all_builtin_tools(
    include_bash=True,
    include_editor=True,
    include_computer=False
)

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "Create a Python script that prints 'Hello World' and run it"
    }]
)
```

### Example 2: Custom Tools with @beta_tool
```python
from devorbit import Devorbit, beta_tool, ToolExecutor

@beta_tool
def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression."""
    # Safe evaluation implementation
    return eval(expression)

@beta_tool
def get_time() -> str:
    """Get current time."""
    from datetime import datetime
    return datetime.now().isoformat()

tools = {"calculate": calculate, "get_time": get_time}
executor = ToolExecutor(tools)

client = Devorbit(provider="anthropic", api_key="...")
response = executor.execute_tool_loop(
    client=client,
    messages=[{"role": "user", "content": "What's 2+2 and what time is it?"}],
    model="claude-sonnet-4-5-20250929"
)
```

### Example 3: MCP Integration
```python
from devorbit import AsyncDevorbit, MCPManager, ToolExecutor
import asyncio

async def main():
    # Load MCP servers
    mcp = MCPManager.from_config_file(".mcp.json")

    async with mcp:
        # Create executor with MCP tools
        executor = ToolExecutor(mcp_manager=mcp)

        client = AsyncDevorbit(provider="openai", api_key="...")

        # Agent has access to all MCP tools
        response = await executor.aexecute_tool_loop(
            client=client,
            messages=[{
                "role": "user",
                "content": "Search my Notion for 'sprint planning' tasks"
            }],
            model="gpt-4",
            max_tokens=4096
        )

        print(response.content[0].text)

asyncio.run(main())
```

---

## Next Steps

To build a competitive agent SDK, the following tools should be implemented next:

### **Phase 1: Essential File Operations** (Weeks 1-2)
1. Read Tool
2. Write Tool
3. Edit Tool

### **Phase 2: Essential Search Tools** (Week 3)
1. Glob Tool
2. Grep Tool

### **Phase 3: Workflow Tools** (Weeks 4-5)
1. TodoWrite/TodoRead
2. Task/Subagent Tool
3. MultiEdit Tool

With these additions, the SDK will have all essential tools for autonomous coding agents.

---

**Last Updated:** 2025-11-14
**For detailed implementation guide, see:** `FEATURE_GAP_ANALYSIS_REPORT.md`
