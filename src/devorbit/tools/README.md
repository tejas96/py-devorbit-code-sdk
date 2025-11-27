# 🛠️ Devorbit Tools

> Built-in tools for autonomous coding agents. Drop-in replacements for Claude Code tools.

## Quick Start

```python
from devorbit import (
    # File Operations
    read_file, write_file, edit_file, multi_edit,
    # Shell
    bash, bash_output, kill_shell, list_active_sessions,
    # Search
    glob_files, grep_code,
    # Tasks
    todo_read, todo_write,
    # Agents
    task, task_status, task_cancel,
)

# Read a file
result = read_file("/path/to/file.py")
print(result["content"])

# Execute shell command
result = bash("ls -la")
print(result["output"])

# Search for files
result = glob_files("**/*.py", path="./src")
print(result["matches"])
```

---

## 📁 File Tools

### `read_file`
Read files with line numbers (like `cat -n`).

```python
result = read_file(
    file_path="/path/to/file.py",
    offset=10,    # Start from line 10 (optional)
    limit=50,     # Read 50 lines (optional)
)

# Returns:
{
    "content": "  1| line one\n  2| line two\n...",
    "file_path": "/path/to/file.py",
    "total_lines": 100,
    "lines_read": 50,
}
```

### `write_file`
Create or overwrite files with safety checks.

```python
result = write_file(
    file_path="/path/to/new_file.py",
    content="print('Hello, World!')",
)

# Returns:
{
    "success": True,
    "file_path": "/path/to/new_file.py",
    "bytes_written": 23,
}
```

### `edit_file`
Make precise edits using search/replace (preferred for modifications).

```python
result = edit_file(
    file_path="/path/to/file.py",
    old_string="def old_function():",
    new_string="def new_function():",
)

# Returns:
{
    "success": True,
    "file_path": "/path/to/file.py",
    "changes_made": 1,
}
```

**⚡ Pro Tip:** Always prefer `edit_file` over `write_file` for modifications. It's safer and preserves file structure.

### `multi_edit`
Batch multiple edits to a single file atomically.

```python
result = multi_edit(
    file_path="/path/to/file.py",
    edits=[
        {"old_string": "foo", "new_string": "bar"},
        {"old_string": "baz", "new_string": "qux"},
    ],
)

# Returns:
{
    "success": True,
    "file_path": "/path/to/file.py",
    "edits_applied": 2,
}
```

---

## 🖥️ Bash Tools

### `bash`
Execute shell commands with optional persistent sessions.

```python
# Simple command (non-persistent, recommended)
result = bash("echo 'Hello World'")
# Returns: {"output": "Hello World\n", "exit_code": 0, "cwd": "/current/dir"}

# Persistent session (state retained between commands)
result = bash("cd /tmp && export MY_VAR=hello", session_id="my-session")
result = bash("echo $MY_VAR && pwd", session_id="my-session")
# Returns: {"output": "hello\n/tmp\n", "session_id": "my-session", ...}

# Background execution
result = bash("sleep 100", run_in_background=True)
# Returns: {"status": "running", "session_id": "auto-generated-id"}

# With timeout
result = bash("long_command", timeout=30.0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | str | required | Shell command to execute |
| `session_id` | str | None | Session ID for persistent state |
| `cwd` | str | None | Working directory |
| `timeout` | float | 120 | Timeout in seconds |
| `run_in_background` | bool | False | Run in background |

### `bash_output`
Get output from a background session.

```python
result = bash_output(session_id="my-session")
# Returns: {"output": "...", "is_running": True, "cwd": "/path"}
```

### `kill_shell`
Terminate a bash session.

```python
result = kill_shell(session_id="my-session")
# Returns: {"success": True, "shell_id": "my-session"}
```

### `list_active_sessions`
List all active bash sessions.

```python
sessions = list_active_sessions()
# Returns: [{"session_id": "...", "is_running": True, "cwd": "..."}, ...]
```

### `cleanup_sessions`
Clean up all bash sessions.

```python
cleanup_sessions()
```

---

## 🔍 Search Tools

### `glob_files`
Find files by pattern (like `find` with glob).

```python
result = glob_files(
    pattern="**/*.py",           # Glob pattern
    path="./src",                # Search directory (optional)
)

# Returns:
{
    "pattern": "**/*.py",
    "search_path": "/absolute/path/src",
    "matches": ["/path/to/file1.py", "/path/to/file2.py"],
    "count": 2,
}
```

**Common Patterns:**
| Pattern | Matches |
|---------|---------|
| `*.py` | Python files in current dir |
| `**/*.py` | Python files recursively |
| `src/**/*.ts` | TypeScript files in src |
| `test_*.py` | Test files |
| `**/README.md` | All READMEs |

### `grep_code`
Search file contents with regex.

```python
result = grep_code(
    pattern="def\\s+\\w+",       # Regex pattern
    path="./src",                # Search directory
    include="*.py",              # File filter (optional)
    context_lines=2,             # Lines before/after (optional)
)

# Returns:
{
    "pattern": "def\\s+\\w+",
    "matches": [
        {
            "file": "/path/to/file.py",
            "line": 42,
            "content": "def my_function():",
            "context_before": ["", "# Helper"],
            "context_after": ["    pass", ""],
        }
    ],
    "total_matches": 15,
}
```

---

## ✅ Todo Tools

### `todo_read`
Read the current todo list.

```python
result = todo_read()
# Returns:
{
    "todos": [
        {"id": "1", "content": "Fix bug", "status": "in_progress"},
        {"id": "2", "content": "Add tests", "status": "pending"},
    ],
    "count": 2,
}
```

### `todo_write`
Create or update todos.

```python
result = todo_write(
    todos=[
        {"id": "1", "content": "Implement feature", "status": "in_progress"},
        {"id": "2", "content": "Write docs", "status": "pending"},
    ],
    merge=True,  # Merge with existing (False = replace all)
)
```

**Status Values:** `pending`, `in_progress`, `completed`, `cancelled`

---

## 🤖 Agent Tools

### `task`
Create a subtask for parallel agent execution.

```python
result = task(
    description="Analyze the codebase structure",
    prompt="List all Python modules and their purposes",
)

# Returns:
{
    "task_id": "task-abc123",
    "status": "queued",
    "description": "Analyze the codebase structure",
}
```

### `task_status`
Check status of a task.

```python
result = task_status(task_id="task-abc123")
# Returns:
{
    "task_id": "task-abc123",
    "status": "completed",
    "result": "Found 15 modules...",
}
```

### `task_cancel`
Cancel a running task.

```python
result = task_cancel(task_id="task-abc123")
# Returns: {"success": True, "task_id": "task-abc123"}
```

---

## 🌐 Web Tools

### `web_fetch`
Fetch content from a URL.

```python
result = web_fetch(url="https://example.com/api/data")
# Returns: {"content": "...", "status_code": 200, "url": "..."}
```

### `web_search`
Search the web (requires API configuration).

```python
result = web_search(query="Python best practices 2024")
# Returns: {"results": [...], "query": "..."}
```

---

## 📓 Notebook Tools

### `notebook_read`
Read Jupyter notebook cells.

```python
result = notebook_read(
    notebook_path="/path/to/notebook.ipynb",
    cell_index=0,  # Optional: specific cell
)
```

### `notebook_edit`
Edit Jupyter notebook cells.

```python
result = notebook_edit(
    notebook_path="/path/to/notebook.ipynb",
    cell_index=0,
    new_source="print('Updated!')",
)
```

---

## 🔧 Tool Registry

All tools are auto-registered with the global `ToolRegistry`:

```python
from devorbit.core.tool_registry import get_tool_registry

registry = get_tool_registry()

# List all tools
for tool in registry.get_all_tools():
    print(f"{tool.name}: {tool.description}")

# Execute tool generically
result = registry.execute("read_file", file_path="/path/to/file.py")

# Get tool definitions (for LLM)
definitions = registry.get_all_definitions()
```

### Creating Custom Tools

Use the `@tool` decorator for auto-registration:

```python
from devorbit.core.tool_registry import tool
from devorbit.core.types import ToolCategory

@tool(category=ToolCategory.FILE, name="my_tool")
def my_custom_tool(path: str, option: bool = False) -> dict:
    """My custom tool description.
    
    Args:
        path: Path to process
        option: Enable special mode
    
    Returns:
        Result dictionary
    """
    return {"success": True, "path": path}
```

---

## 📊 Tool Categories

| Category | Tools |
|----------|-------|
| **File** | `read_file`, `write_file`, `edit_file`, `multi_edit` |
| **Shell** | `bash`, `bash_output`, `kill_shell`, `list_active_sessions` |
| **Search** | `glob_files`, `grep_code` |
| **Todo** | `todo_read`, `todo_write` |
| **Agent** | `task`, `task_status`, `task_cancel` |
| **Web** | `web_fetch`, `web_search` |
| **Notebook** | `notebook_read`, `notebook_edit` |

---

## 💡 Best Practices

1. **Use `edit_file` over `write_file`** for modifications - it's safer
2. **Use simple bash** (no `session_id`) for one-off commands
3. **Use persistent sessions** only when you need state (env vars, cd)
4. **Set timeouts** for potentially long operations
5. **Use `glob_files`** before reading to find correct paths
6. **Use `grep_code`** to locate code before editing

---

## 🔗 See Also

- [Providers README](../providers/README.md)
- [CLI Commands README](../cli/commands/README.md)
- [Main README](../../../README.md)

