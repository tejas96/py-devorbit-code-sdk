# Devorbit CLI Command Reference

Complete reference for all Devorbit CLI commands and options.

## Table of Contents

- [CLI Invocation](#cli-invocation)
- [Slash Commands](#slash-commands)
- [Tool Reference](#tool-reference)
- [Environment Variables](#environment-variables)

## CLI Invocation

### Command Syntax

```bash
devorbit [OPTIONS]
```

### Options

#### `--provider, -p <PROVIDER>`

Select the LLM provider to use.

**Choices**: `anthropic`, `openai`, `gemini`, `mistral`, `codellama`

**Default**: `anthropic`

**Example**:
```bash
devorbit --provider openai
devorbit -p gemini
```

#### `--model, -m <MODEL>`

Specify the model to use for the selected provider.

**Type**: String

**Default**: Provider-specific default

**Examples**:
```bash
devorbit --model claude-sonnet-4-5-20250929
devorbit --model gpt-4-turbo
devorbit -m gemini-pro
```

**Provider Defaults**:
- Anthropic: `claude-sonnet-4-5-20250929`
- OpenAI: `gpt-4-turbo-preview`
- Gemini: `gemini-pro`
- Mistral: `mistral-medium`
- CodeLlama: `codellama-34b`

#### `--api-key, -k <KEY>`

API key for the provider.

**Type**: String

**Environment Variable**: `ANTHROPIC_API_KEY` (for Anthropic)

**Required**: Yes (either via option or environment variable)

**Example**:
```bash
devorbit --api-key sk-ant-...
devorbit -k your-api-key
```

#### `--working-dir, -w <PATH>`

Working directory for file operations.

**Type**: Path (must exist and be a directory)

**Default**: Current directory

**Example**:
```bash
devorbit --working-dir /path/to/project
devorbit -w ~/projects/myapp
```

#### `--no-color`

Disable colored output.

**Type**: Flag

**Default**: `false`

**Example**:
```bash
devorbit --no-color
```

#### `--debug`

Enable debug mode with verbose logging.

**Type**: Flag

**Default**: `false`

**Example**:
```bash
devorbit --debug
```

#### `--version`

Show version information and exit.

**Example**:
```bash
devorbit --version
```

#### `--help`

Show help message and exit.

**Example**:
```bash
devorbit --help
```

### Complete Examples

Start with all options:
```bash
devorbit \
  --provider anthropic \
  --model claude-sonnet-4-5-20250929 \
  --api-key sk-ant-... \
  --working-dir /path/to/project \
  --debug
```

Short form:
```bash
devorbit -p openai -m gpt-4 -k sk-... -w ~/project
```

## Slash Commands

Slash commands are entered in the REPL and start with `/`.

### General Commands

#### `/help`

**Description**: Display help information and available commands

**Syntax**: `/help`

**Arguments**: None

**Output**: Shows list of all commands, current session info, and tips

**Example**:
```
devorbit> /help
```

---

#### `/exit`

**Description**: Exit the REPL

**Syntax**: `/exit`

**Aliases**: `/quit`

**Arguments**: None

**Behavior**: Gracefully terminates the session

**Example**:
```
devorbit> /exit
Goodbye! 👋
```

---

#### `/quit`

**Description**: Alias for `/exit`

**Syntax**: `/quit`

**See**: `/exit`

---

#### `/clear`

**Description**: Clear conversation history

**Syntax**: `/clear`

**Arguments**: None

**Effect**: Removes all messages from current session

**Example**:
```
devorbit> /clear
✓ Conversation history cleared
```

---

#### `/history`

**Description**: Show conversation history

**Syntax**: `/history`

**Arguments**: None

**Output**: List of all messages with preview (truncated to 100 chars)

**Example**:
```
devorbit> /history

Conversation History:

1. [user] Hello!
2. [assistant] Hi there! How can I help you today?
3. [user] Can you create a Python function?
4. [assistant] Sure! What should the function do?

Total messages: 4
```

---

### Session Commands

#### `/status`

**Description**: Show current session status

**Syntax**: `/status`

**Arguments**: None

**Output**: Displays:
- Provider
- Model
- Working directory
- Message count
- Planning mode status
- Debug mode status

**Example**:
```
devorbit> /status

Session Status:
    Provider: anthropic
    Model: claude-sonnet-4-5-20250929
    Working Directory: /home/user/project
    Messages: 10
    Planning Mode: Disabled
    Debug Mode: Disabled
```

---

#### `/model`

**Description**: Show or change the current model

**Syntax**:
- `/model` - Show current model
- `/model <name>` - Change to specified model

**Arguments**:
- `<name>` (optional): New model name

**Examples**:
```
devorbit> /model
Current model: claude-sonnet-4-5-20250929

devorbit> /model gpt-4-turbo
✓ Model changed to: gpt-4-turbo
```

---

#### `/provider`

**Description**: Show current provider

**Syntax**: `/provider`

**Arguments**: None

**Note**: Provider cannot be changed during an active session

**Example**:
```
devorbit> /provider
Current provider: anthropic
i Note: Provider cannot be changed during session
```

---

### Navigation Commands

#### `/pwd`

**Description**: Print working directory

**Syntax**: `/pwd`

**Arguments**: None

**Output**: Absolute path of current working directory

**Example**:
```
devorbit> /pwd
/home/user/project
```

---

#### `/cd`

**Description**: Change working directory

**Syntax**: `/cd <path>`

**Arguments**:
- `<path>` (required): Path to new directory

**Features**:
- Supports `~` for home directory
- Path expansion and resolution
- Validates directory exists

**Examples**:
```bash
# Change to absolute path
devorbit> /cd /path/to/project
✓ Changed working directory to: /path/to/project

# Change to home
devorbit> /cd ~
✓ Changed working directory to: /home/user

# Change to relative path
devorbit> /cd ../other-project
✓ Changed working directory to: /home/user/other-project
```

**Error Cases**:
```bash
# No path provided
devorbit> /cd
Error: Usage: /cd <path>

# Directory doesn't exist
devorbit> /cd /nonexistent
Error: Directory not found: /nonexistent

# Path is a file
devorbit> /cd /home/user/file.txt
Error: Not a directory: /home/user/file.txt
```

---

### Feature Commands

#### `/planning`

**Description**: Toggle planning mode

**Syntax**: `/planning`

**Arguments**: None

**Behavior**: Toggles between enabled and disabled

**Effects**:
- **Enabled**: Agent presents plans before executing changes
- **Disabled**: Agent executes changes directly

**Examples**:
```bash
# Enable planning mode
devorbit> /planning
✓ Planning mode enabled
i The agent will present plans for approval before executing changes

# Disable planning mode
devorbit> /planning
✓ Planning mode disabled
```

---

## Tool Reference

These tools are available to the LLM during conversations.

### File Tools

#### `read_file`

Read contents of a file.

**Parameters**:
- `path` (string): File path to read

---

#### `write_file`

Write content to a file (creates or overwrites).

**Parameters**:
- `path` (string): File path to write
- `content` (string): Content to write

---

#### `edit_file`

Make precise edits to a file.

**Parameters**:
- `path` (string): File path
- `old_text` (string): Text to replace
- `new_text` (string): Replacement text

---

#### `multi_edit_file`

Make multiple edits to a file in one operation.

**Parameters**:
- `path` (string): File path
- `edits` (array): List of edit operations

---

#### `ls_directory`

List directory contents.

**Parameters**:
- `path` (string, optional): Directory path (default: current)

---

### Search Tools

#### `glob_files`

Find files matching a pattern.

**Parameters**:
- `pattern` (string): Glob pattern (e.g., `*.py`, `src/**/*.js`)
- `path` (string, optional): Base directory

---

#### `grep_code`

Search file contents for text/regex.

**Parameters**:
- `pattern` (string): Search pattern (regex supported)
- `path` (string, optional): Directory to search
- `file_pattern` (string, optional): Filter by file pattern

---

### Bash Tools

#### `bash`

Execute a bash command.

**Parameters**:
- `command` (string): Command to execute
- `working_dir` (string, optional): Working directory

---

#### `bash_output`

Get output from a background bash session.

**Parameters**:
- `session_id` (string): Session ID

---

#### `kill_shell`

Kill a background bash session.

**Parameters**:
- `session_id` (string): Session ID

---

### Web Tools

#### `web_search`

Search the web for information.

**Parameters**:
- `query` (string): Search query

---

#### `web_fetch`

Fetch content from a URL.

**Parameters**:
- `url` (string): URL to fetch
- `selector` (string, optional): CSS selector

---

### Todo Tools

#### `todo_read`

Read current todo list.

**Parameters**: None

---

#### `todo_write`

Write/update todo list.

**Parameters**:
- `todos` (array): List of todo items

---

### Agent Tools

#### `task`

Launch a specialized subagent.

**Parameters**:
- `prompt` (string): Task description
- `subagent_type` (string): Agent type (general-purpose, explore, plan, etc.)
- `description` (string, optional): Short description
- `model` (string, optional): Model override

---

#### `task_status`

Get status of a running task.

**Parameters**:
- `task_id` (string): Task ID

---

#### `task_cancel`

Cancel a running task.

**Parameters**:
- `task_id` (string): Task ID

---

## Environment Variables

### Provider API Keys

#### `ANTHROPIC_API_KEY`

API key for Anthropic Claude.

**Required when**: Using `--provider anthropic` (default)

**Example**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

#### `OPENAI_API_KEY`

API key for OpenAI.

**Required when**: Using `--provider openai`

**Example**:
```bash
export OPENAI_API_KEY="sk-..."
```

---

#### `GOOGLE_API_KEY`

API key for Google Gemini.

**Required when**: Using `--provider gemini`

**Example**:
```bash
export GOOGLE_API_KEY="..."
```

---

#### `MISTRAL_API_KEY`

API key for Mistral AI.

**Required when**: Using `--provider mistral`

**Example**:
```bash
export MISTRAL_API_KEY="..."
```

---

### Other Variables

#### `NO_COLOR`

Disable colored output (alternative to `--no-color` flag).

**Values**: Any value disables color

**Example**:
```bash
export NO_COLOR=1
devorbit
```

---

## Error Codes

### Exit Codes

- `0`: Successful execution
- `1`: Error occurred (API error, invalid arguments, etc.)
- `130`: Interrupted by user (Ctrl+C)

### Common Errors

#### API Key Missing

**Exit Code**: `1`

**Message**: `Error: No API key provided for <provider>`

**Solution**: Set appropriate environment variable or use `--api-key`

---

#### Invalid Provider

**Exit Code**: `2`

**Message**: `Error: Invalid value for '--provider'`

**Solution**: Use a valid provider from: anthropic, openai, gemini, mistral, codellama

---

#### Invalid Working Directory

**Exit Code**: `2`

**Message**: `Error: Invalid value for '--working-dir': Path '...' does not exist`

**Solution**: Provide a valid, existing directory path

---

## See Also

- [CLI User Guide](cli-guide.md) - Comprehensive usage guide
- [API Documentation](api-reference.md) - Programmatic API reference
- [Examples](../examples/) - Example use cases
- [MCP Integration](mcp-integration.md) - Extend with MCP servers
