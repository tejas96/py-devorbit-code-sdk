# Devorbit Multi-LLM SDK

A unified Python SDK for multiple LLM providers with a Claude SDK-like interface.

**✨ Now with full agent development support!**

## Features

### **Core Features**
- **Unified API**: Single, consistent interface across multiple LLM providers
- **Claude SDK Compatible**: Exact feature parity with Claude SDK
- **Async Support**: Full async/await support with `AsyncDevorbit` client
- **Type Safe**: TypedDicts for requests, Pydantic models for responses
- **Streaming**: Server-sent events (SSE) streaming for all providers
- **Tool Use**: Function calling support across providers
- **Vision**: Image input support where available
- **Extensible**: Easy to add new providers

### **🎉 New: Agent Development Features**
- **Beta Namespace**: `client.beta.messages` with advanced features
- **Prompt Caching**: Reduce costs with `cache_control` on content blocks
- **Tool Helpers**: `@beta_tool` decorator for easy tool definition
- **Auto Tool Execution**: `ToolExecutor` for automatic tool loops
- **Extended Thinking**: Access model's reasoning process
- **Built-in Tools**: Computer use, Bash, Text editor tools
- **PDF Support**: Process PDF documents in messages
- **Message Batches**: Batch processing for parallel requests
- **🆕 MCP Support**: Model Context Protocol integration (like Claude Code!)

## Supported Providers

- **Anthropic** (Claude models)
- **OpenAI** (GPT models)
- **Google** (Gemini models)
- **Mistral** (Mistral models)
- **Code Llama** (Meta's Code Llama models)

## Installation

```bash
pip install devorbit-multi-llm-sdk
```

## Quick Start

```python
from devorbit import Devorbit

# Initialize client with provider
client = Devorbit(
    provider="anthropic",
    api_key="your-api-key"
)

# Create a message (just like Claude SDK)
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(message.content[0].text)
```

### Switching Providers

```python
# Use OpenAI instead
client = Devorbit(
    provider="openai",
    api_key="your-openai-key"
)

message = client.messages.create(
    model="gpt-4",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, GPT!"}
    ]
)
```

### Async Usage

```python
from devorbit import AsyncDevorbit

async def main():
    client = AsyncDevorbit(
        provider="anthropic",
        api_key="your-api-key"
    )

    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )

    print(message.content[0].text)

import asyncio
asyncio.run(main())
```

### Streaming

```python
# Streaming with context manager
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Write a haiku"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Or get the final message
message = stream.get_final_message()
```

### Tool Use

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
]

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in SF?"}
    ]
)
```

### Agent Development Features

#### Tool Helpers with @beta_tool

```python
from devorbit import Devorbit, beta_tool, ToolExecutor

@beta_tool
def get_weather(location: str) -> dict:
    """Get weather for a location."""
    return {"temp": 22, "location": location}

@beta_tool
def search(query: str) -> dict:
    """Search database."""
    return {"results": [...]}

# Automatic tool execution loop
tools = {"get_weather": get_weather, "search": search}
executor = ToolExecutor(tools)

client = Devorbit(provider="anthropic", api_key="...")
response = executor.execute_tool_loop(
    client=client,
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    model="claude-sonnet-4-5-20250929"
)
```

#### Prompt Caching

```python
client = Devorbit(provider="anthropic", api_key="...")

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system=[{
        "type": "text",
        "text": "Long system prompt...",
        "cache_control": {"type": "ephemeral"}  # Cache it!
    }],
    messages=[{"role": "user", "content": "Question"}]
)
```

#### Built-in Agent Tools

```python
from devorbit import Devorbit, get_all_builtin_tools

client = Devorbit(provider="anthropic", api_key="...")

# Get bash and text editor tools
tools = get_all_builtin_tools(
    include_bash=True,
    include_editor=True
)

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=2048,
    tools=tools,
    messages=[{"role": "user", "content": "Create a Python script"}]
)
```

#### MCP (Model Context Protocol) - Connect to External Tools

```python
from devorbit import AsyncDevorbit, MCPManager, ToolExecutor
import asyncio

async def main():
    # Load MCP servers from config (.mcp.json)
    mcp = MCPManager.from_config_file(".mcp.json")

    async with mcp:  # Auto-connect to all servers
        # Create executor with MCP tools
        executor = ToolExecutor(mcp_manager=mcp)

        client = AsyncDevorbit(provider="anthropic", api_key="...")

        # Agent automatically has access to all MCP tools
        # (Notion, Jira, ClickUp, databases, file systems, etc.)
        response = await executor.aexecute_tool_loop(
            client=client,
            messages=[{
                "role": "user",
                "content": "Fetch my Notion tasks and create a sprint plan"
            }],
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096
        )

        print(response.content[0].text)

asyncio.run(main())
```

**MCP Configuration** (`.mcp.json`):
```json
{
    "mcpServers": {
        "notion": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@notionhq/mcp-server-notion"],
            "env": {"NOTION_API_KEY": "your-key"}
        },
        "jira": {
            "transport": "stdio",
            "command": "python",
            "args": ["jira_server.py"],
            "env": {"JIRA_TOKEN": "your-token"}
        }
    }
}
```

See [MCP Guide](./docs/mcp-guide.md) for complete documentation.

## Documentation

- [Getting Started](./docs/getting-started.md)
- [API Reference](./docs/api-reference.md)
- [Provider Guide](./docs/providers.md)
- [MCP Guide](./docs/mcp-guide.md) - **🆕 NEW!**
- [Implementation Status](./IMPLEMENTATION_STATUS.md)
- [Examples](./examples/)
  - [Basic Usage](./examples/basic_usage.py)
  - [Streaming](./examples/streaming.py)
  - [Tool Use](./examples/tool_use.py)
  - [Tool Helpers](./examples/tool_helpers.py)
  - [Beta Features](./examples/beta_features.py)
  - [MCP Examples](./examples/mcp_examples.py) - **🆕 NEW!**
  - [Sprint Planning Agent](./examples/sprint_planning_agent.py) - **🆕 NEW!**
  - [Vision](./examples/vision.py)
  - [Async Usage](./examples/async_usage.py)

## Requirements

- Python 3.12+
- See `pyproject.toml` for dependency details

## License

MIT
