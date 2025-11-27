# ⌨️ Devorbit CLI Commands

> Interactive terminal interface for AI-powered coding assistance.

## Quick Start

```bash
# Start the CLI
devorbit --provider anthropic

# Or with specific model
devorbit --provider gemini --model gemini-1.5-flash

# With API key (if not in env)
devorbit --provider openai --api-key sk-...
```

---

## 🚀 Command Reference

### System Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/help` | `/h`, `/?` | Show help and available commands |
| `/exit` | `/quit`, `/q` | Exit the CLI |
| `/version` | `/v` | Show version information |

```bash
/help           # Show all commands
/help cd        # Help for specific command
/exit           # Exit CLI
```

### Navigation Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/cd <path>` | - | Change working directory |
| `/pwd` | - | Print working directory |
| `/ls [path]` | `/dir` | List directory contents |

```bash
/cd ~/projects/my-app    # Change directory
/pwd                     # Show current directory
/ls                      # List current directory
/ls src/                 # List specific directory
```

### Session Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/clear` | `/cls` | Clear conversation history |
| `/status` | `/info` | Show session status |
| `/history [n]` | `/hist` | Show last n messages |

```bash
/clear              # Clear chat history
/status             # Show provider, model, message count
/history            # Show all history
/history 5          # Show last 5 messages
```

### Model Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/model [name]` | `/m` | Show or change model |
| `/provider [name]` | `/p` | Show or change provider |
| `/planning` | `/plan` | Toggle planning mode |
| `/multiline` | `/ml` | Toggle multiline input |

```bash
/model                          # Show current model
/model gpt-4o                   # Switch to GPT-4o
/provider gemini                # Switch to Gemini
/planning                       # Toggle planning mode
/multiline                      # Toggle multiline (Ctrl+Enter to submit)
```

### Permission Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/permissions` | `/perms` | Manage tool permissions |
| `/autoapprove` | `/auto` | Toggle auto-approve mode |

```bash
/permissions                    # Show permission rules
/permissions list               # List all rules
/permissions add bash allow     # Auto-allow bash
/permissions add write ask      # Ask before writes
/permissions remove bash        # Remove bash rule
/permissions clear              # Clear all rules
/autoapprove                    # Toggle auto-approve
```

### Debug Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/debug` | `/d` | Toggle debug mode |
| `/tokens` | - | Show token usage |
| `/hooks` | - | Show registered hooks |
| `/recovery` | - | Show error recovery settings |

```bash
/debug              # Toggle debug output
/tokens             # Show token usage stats
/hooks              # List active hooks
/recovery           # Show retry/recovery config
```

### File Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `/cat <file>` | - | Display file contents |
| `/init` | - | Initialize config file |

```bash
/cat README.md          # Show file contents
/init                   # Create .devorbit.json config
```

---

## 📝 Input Features

### File Mentions (`@`)

Attach files to your message:

```bash
# Single file
> @src/main.py explain this code

# Multiple files
> @src/main.py @src/utils.py compare these

# Glob patterns
> @src/**/*.py analyze all Python files
> @**/*.md summarize the docs
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Autocomplete commands, files, models |
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | Exit CLI |
| `Ctrl+Enter` | Submit in multiline mode |
| `Ctrl+R` | Search command history |
| `Ctrl+L` | Clear screen |
| `↑` / `↓` | Navigate history |

### Multiline Mode

Toggle with `/multiline`:

```bash
/multiline
> Write a function that:
> - Takes a list of numbers
> - Returns the sum of even numbers
> - Handles empty lists
[Ctrl+Enter to submit]
```

---

## ⚙️ Configuration

### `.devorbit.json`

Create with `/init` or manually:

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
    "pre_tool_call": [
      {
        "name": "log_tool",
        "command": "echo \"Tool: $tool_name\"",
        "enabled": true
      }
    ],
    "post_file_write": [
      {
        "name": "format",
        "command": "prettier --write $file_path",
        "enabled": true
      }
    ]
  }
}
```

### Environment Variables

```bash
# API Keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."

# Default provider/model
export DEVORBIT_PROVIDER="anthropic"
export DEVORBIT_MODEL="claude-sonnet-4-20250514"
```

---

## 🔒 Permission System

Control what the AI can do:

### Permission Levels

| Level | Description |
|-------|-------------|
| `allow` | Always allow (no prompt) |
| `deny` | Always deny |
| `ask` | Ask every time |
| `ask_once` | Ask once per session |
| `allow_session` | Allow for this session |

### Setting Permissions

```bash
# Via command
/permissions add bash allow
/permissions add write_file ask
/permissions add "rm *" deny

# Pattern matching
/permissions add "*.py" allow    # Allow Python file ops
/permissions add "/etc/*" deny   # Deny system files
```

### Dangerous Commands

The CLI warns on dangerous patterns:
- `rm -rf`, `rm -r`, `rm -f`
- `sudo`, `su`
- System paths (`/etc`, `/usr`, `/bin`)
- Force flags on destructive commands

---

## 🪝 Hooks System

Run custom commands on events:

### Available Hooks

| Hook | When | Variables |
|------|------|-----------|
| `pre_tool_call` | Before any tool | `$tool_name`, `$tool_input` |
| `post_tool_call` | After any tool | `$tool_name`, `$result` |
| `post_file_write` | After file write | `$file_path` |
| `post_file_edit` | After file edit | `$file_path` |
| `on_error` | On tool error | `$error`, `$tool_name` |

### Example Hooks

```json
{
  "hooks": {
    "post_file_write": [
      {
        "name": "lint",
        "command": "ruff check $file_path --fix",
        "enabled": true
      },
      {
        "name": "format",
        "command": "black $file_path",
        "enabled": true
      }
    ],
    "pre_tool_call": [
      {
        "name": "log",
        "command": "echo \"$(date): $tool_name\" >> ~/.devorbit.log",
        "enabled": true
      }
    ]
  }
}
```

---

## 🔄 Error Recovery

Automatic retry on transient errors:

```bash
/recovery           # Show current settings
```

Settings in `.devorbit.json`:

```json
{
  "recovery": {
    "max_retries": 3,
    "base_delay": 1.0,
    "max_delay": 30.0,
    "exponential_base": 2.0
  }
}
```

---

## 💬 Example Session

```bash
$ devorbit --provider anthropic

╔══════════════════════════════════════════════════════╗
║  🚀 Devorbit CLI - AI Coding Assistant               ║
║  Provider: anthropic | Model: claude-sonnet-4-20250514 ║
║  Type /help for commands, Ctrl+D to exit             ║
╚══════════════════════════════════════════════════════╝

> /cd ~/projects/my-app
Changed directory to /Users/me/projects/my-app

> @src/main.py explain this code
[Reading src/main.py...]

This is a FastAPI application that...

> Add error handling to the /users endpoint

I'll add proper error handling. Let me edit the file:

[Tool: edit_file]
[Allow? (y/n/a/d)] y

✓ File edited successfully

> /status
Session Status:
    Provider: anthropic
    Model: claude-sonnet-4-20250514
    Working Directory: /Users/me/projects/my-app
    Messages: 4

> /exit
Goodbye! 👋
```

---

## 🎨 UI Customization

### Colors & Themes

The CLI uses Rich for beautiful output:
- Syntax highlighting for code blocks
- Progress indicators for long operations
- Colored tool execution status
- Formatted tables and panels

### Status Line

Shows real-time information:
- Current provider and model
- Working directory
- Token usage
- Active operations

---

## 🚀 Pro Tips

1. **Use file mentions** - `@file.py` is faster than explaining code
2. **Set permissions once** - `/permissions add read_file allow`
3. **Use hooks** - Auto-format, lint, or log everything
4. **Tab complete** - Works for commands, files, and models
5. **Check status** - `/status` shows token usage
6. **Use planning mode** - `/planning` for complex tasks
7. **Review history** - `/history 10` to see recent context

---

## 🐛 Troubleshooting

### "API key not found"
```bash
export ANTHROPIC_API_KEY="your-key"
# or
devorbit --provider anthropic --api-key "your-key"
```

### "Model not found"
```bash
/model  # Shows available models
```

### "Permission denied"
```bash
/permissions list  # Check rules
/autoapprove      # Toggle auto-approve
```

### Tool keeps timing out
```bash
# Use simple bash for long commands
> run the tests (use bash with timeout 300)
```

---

## 🔗 See Also

- [Tools README](../../tools/README.md)
- [Providers README](../../providers/README.md)
- [Main README](../../../../README.md)

