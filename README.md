<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/coverage-30%25-yellow.svg" alt="Coverage">
</p>

<h1 align="center">🚀 Devorbit</h1>

<p align="center">
  <strong>Unified Python SDK for Multiple LLM Providers + AI Coding CLI</strong>
</p>

<p align="center">
  One API. All providers. Claude Code-like CLI included.
</p>

---

## ✨ What is Devorbit?

Devorbit is two things in one:

1. **SDK** - A unified Python interface to Anthropic, OpenAI, Google, Mistral, and Code Llama
2. **CLI** - An interactive terminal for AI-powered coding assistance (like Claude Code)

```python
# Same code works with ANY provider
from devorbit import Devorbit

client = Devorbit(provider="anthropic")  # or "openai", "gemini", "mistral"
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## 🎯 Quick Start

### Installation

```bash
pip install devorbit-multi-llm-sdk
```

### SDK Usage

```python
from devorbit import Devorbit

# Initialize with any provider
client = Devorbit(
    provider="anthropic",
    api_key="sk-ant-..."  # Or set ANTHROPIC_API_KEY env var
)

# Create a message
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain Python decorators"}]
)

print(response.content[0].text)
```

### CLI Usage

```bash
# Start interactive CLI
devorbit --provider anthropic

# Or with specific model
devorbit --provider openai --model gpt-4o
```

```
╔══════════════════════════════════════════════════════╗
║  🚀 Devorbit CLI - AI Coding Assistant               ║
╚══════════════════════════════════════════════════════╝

> @src/main.py explain this code
[Reading file...]

This is a FastAPI application that defines REST endpoints...

> Add error handling to the /users endpoint
[Tool: edit_file] ✓

Done! I've added try/except blocks...
```

---

## 🔌 Supported Providers

| Provider | Models | Streaming | Tools | Vision |
|----------|--------|-----------|-------|--------|
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus/Haiku | ✅ | ✅ | ✅ |
| **OpenAI** | GPT-4o, GPT-4, GPT-3.5 | ✅ | ✅ | ✅ |
| **Google** | Gemini 1.5 Pro/Flash | ✅ | ✅ | ✅ |
| **Mistral** | Large, Medium, Small, Codestral | ✅ | ✅ | ❌ |
| **Code Llama** | 70B, 34B, 13B, 7B | ✅ | ✅ | ❌ |

**Switch providers instantly:**

```python
# Anthropic
client = Devorbit(provider="anthropic", api_key="sk-ant-...")
response = client.messages.create(model="claude-sonnet-4-20250514", ...)

# OpenAI
client = Devorbit(provider="openai", api_key="sk-...")
response = client.messages.create(model="gpt-4o", ...)

# Google Gemini
client = Devorbit(provider="gemini", api_key="AIza...")
response = client.messages.create(model="gemini-1.5-pro", ...)
```

📖 **[Full Provider Guide →](src/devorbit/providers/README.md)**

---

## 🛠️ Built-in Tools

Devorbit includes all tools for autonomous coding agents:

| Category | Tools |
|----------|-------|
| **File** | `read_file`, `write_file`, `edit_file`, `multi_edit` |
| **Shell** | `bash`, `bash_output`, `kill_shell` |
| **Search** | `glob_files`, `grep_code` |
| **Tasks** | `todo_read`, `todo_write` |
| **Agents** | `task`, `task_status`, `task_cancel` |
| **Web** | `web_fetch`, `web_search` |
| **Notebook** | `notebook_read`, `notebook_edit` |

```python
from devorbit import bash, read_file, edit_file, glob_files

# Execute shell command
result = bash("ls -la")
print(result["output"])

# Read file with line numbers
content = read_file("/path/to/file.py")

# Edit file precisely
edit_file(
    file_path="/path/to/file.py",
    old_string="def old():",
    new_string="def new():"
)

# Find files
files = glob_files("**/*.py", path="./src")
```

📖 **[Full Tools Guide →](src/devorbit/tools/README.md)**

---

## ⌨️ CLI Features

The CLI provides an interactive coding assistant experience:

### Commands

```bash
/help           # Show all commands
/model gpt-4o   # Switch model
/cd ~/project   # Change directory
/clear          # Clear history
/permissions    # Manage tool permissions
/debug          # Toggle debug mode
```

### File Mentions

```bash
> @src/main.py explain this code
> @**/*.py analyze all Python files
```

### Permissions & Safety

```bash
/permissions add bash allow      # Auto-allow bash
/permissions add write_file ask  # Ask before writes
/autoapprove                     # Toggle auto-approve
```

### Hooks

Auto-run commands on events (lint, format, log):

```json
{
  "hooks": {
    "post_file_write": [
      {"name": "format", "command": "black $file_path"}
    ]
  }
}
```

📖 **[Full CLI Guide →](src/devorbit/cli/commands/README.md)**

---

## 🌊 Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

## 🔧 Tool Use (Function Calling)

```python
from devorbit import Devorbit, beta_tool, ToolExecutor

@beta_tool
def get_weather(location: str) -> dict:
    """Get weather for a location."""
    return {"temp": 22, "condition": "sunny", "location": location}

# Auto-execute tool loop
tools = {"get_weather": get_weather}
executor = ToolExecutor(tools)

response = executor.execute_tool_loop(
    client=client,
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}]
)
```

---

## 🔗 MCP (Model Context Protocol)

Connect to external tools like Notion, Jira, databases:

```python
from devorbit import AsyncDevorbit, MCPManager, ToolExecutor

async def main():
    mcp = MCPManager.from_config_file(".mcp.json")
    
    async with mcp:
        executor = ToolExecutor(mcp_manager=mcp)
        client = AsyncDevorbit(provider="anthropic", api_key="...")
        
        response = await executor.aexecute_tool_loop(
            client=client,
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": "Get my Notion tasks"}]
        )
```

---

## ⚡ Async Support

```python
from devorbit import AsyncDevorbit
import asyncio

async def main():
    client = AsyncDevorbit(provider="anthropic")
    
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    
    print(response.content[0].text)

asyncio.run(main())
```

---

## 📁 Project Structure

```
devorbit/
├── core/               # Core infrastructure
│   ├── client.py       # Main client
│   ├── models.py       # Data models
│   ├── hooks.py        # Hook system
│   ├── recovery.py     # Error recovery
│   └── tool_registry.py # Tool auto-discovery
├── providers/          # LLM providers
│   ├── anthropic.py
│   ├── openai.py
│   ├── gemini.py
│   ├── mistral.py
│   └── codellama.py
├── tools/              # Built-in tools
│   ├── bash.py
│   ├── file.py
│   ├── search.py
│   └── ...
├── cli/                # Interactive CLI
│   ├── commands/       # Slash commands
│   ├── core/           # CLI infrastructure
│   └── ui/             # Terminal UI
└── slash_commands/     # SDK slash commands
```

---

## 🔧 Configuration

### Environment Variables

```bash
# API Keys (recommended)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."
export MISTRAL_API_KEY="..."

# Defaults
export DEVORBIT_PROVIDER="anthropic"
export DEVORBIT_MODEL="claude-sonnet-4-20250514"
```

### `.devorbit.json`

```json
{
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "permissions": {
    "auto_approve": false,
    "rules": [
      {"tool": "read_file", "action": "allow"},
      {"tool": "bash", "action": "ask"}
    ]
  },
  "hooks": {
    "post_file_write": [
      {"name": "lint", "command": "ruff check $file_path --fix"}
    ]
  }
}
```

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [**Tools**](src/devorbit/tools/README.md) | File, bash, search, todo tools |
| [**Providers**](src/devorbit/providers/README.md) | Anthropic, OpenAI, Gemini, Mistral |
| [**CLI Commands**](src/devorbit/cli/commands/README.md) | Interactive terminal commands |
| [Examples](examples/) | Working code examples |

---

## 🧪 Development

```bash
# Clone
git clone https://github.com/tejas96/py-devorbit-code-sdk.git
cd py-devorbit-code-sdk

# Install
poetry install

# Run tests
poetry run pytest

# Lint
poetry run ruff check src/
poetry run mypy src/

# Format
poetry run black src/
poetry run isort src/
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for developers who want one SDK for all LLMs
</p>

<p align="center">
  <a href="https://github.com/tejas96/py-devorbit-code-sdk">GitHub</a> •
  <a href="src/devorbit/tools/README.md">Tools</a> •
  <a href="src/devorbit/providers/README.md">Providers</a> •
  <a href="src/devorbit/cli/commands/README.md">CLI</a>
</p>
