# Claude Code CLI - Complete Clone Specification (PART 2)

## 4. BUILT-IN TOOLS SYSTEM

### 4.1 Read Tool

**Purpose:** Read file contents with line numbers and range support

**Tool Definition:**
```json
{
  "name": "Read",
  "description": "Read a file from the filesystem with optional line range",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Absolute or relative path to the file"
      },
      "start_line": {
        "type": "integer",
        "description": "Starting line number (1-indexed, optional)"
      },
      "end_line": {
        "type": "integer",
        "description": "Ending line number (inclusive, optional)"
      }
    },
    "required": ["file_path"]
  }
}
```

**Display Format:**
```
┌─ Read ────────────────────────────────────────────────────────┐
│ File: src/main.py                                             │
│ Lines: 1-50 of 150                                            │
├───────────────────────────────────────────────────────────────┤
│     1  import os                                              │
│     2  import sys                                             │
│     3                                                         │
│     4  def main():                                            │
│     5      print("Hello, World!")                            │
│    ...                                                        │
│    50  if __name__ == "__main__":                            │
│        [Show all 150 lines]                                  │
└───────────────────────────────────────────────────────────────┘
```

**Features:**
- Syntax highlighting based on file extension
- Line numbers with 6-character width
- Binary file detection (show hex/base64)
- Large file handling (lazy loading)
- Encoding detection (UTF-8, Latin-1, etc.)
- Preview for collapsed output (first/last 10 lines)
- File metadata (size, modified time)

### 4.2 Write Tool

**Purpose:** Create or overwrite files with safety checks

**Tool Definition:**
```json
{
  "name": "Write",
  "description": "Write content to a file (creates new or overwrites existing)",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Path to write to"
      },
      "content": {
        "type": "string",
        "description": "Content to write"
      },
      "create_directories": {
        "type": "boolean",
        "description": "Create parent directories if needed (default: false)"
      }
    },
    "required": ["file_path", "content"]
  }
}
```

**Safety Checks:**
```
Before writing:
1. If file exists:
   ┌─ Confirm Overwrite ─────────────────────────────────────┐
   │ File already exists: src/config.py                      │
   │ Size: 2.3 KB                                            │
   │ Last modified: 2025-11-17 10:30                         │
   │                                                          │
   │ [Show Diff] [Backup & Write] [Cancel] [Skip Check]     │
   └──────────────────────────────────────────────────────────┘

2. If path doesn't exist and needs directory creation:
   ┌─ Create Directories? ───────────────────────────────────┐
   │ Will create: src/new/nested/directory/                  │
   │                                                          │
   │ [Approve] [Cancel]                                      │
   └──────────────────────────────────────────────────────────┘

3. Read-before-write check (configurable):
   - Automatically reads existing file
   - Ensures Claude has latest content
   - Prevents accidental overwrites
```

**Display:**
```
┌─ Write ───────────────────────────────────────────────────────┐
│ File: src/utils/helpers.py                                    │
│ Action: Created (new file)                                    │
│ Size: 1.5 KB                                                  │
├───────────────────────────────────────────────────────────────┤
│ ✓ File written successfully                                   │
│ [View File] [Undo]                                           │
└───────────────────────────────────────────────────────────────┘
```

### 4.3 Edit Tool

**Purpose:** Make precise string-based edits to files

**Tool Definition:**
```json
{
  "name": "Edit",
  "description": "Edit a file by replacing exact string matches",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "Path to file to edit"
      },
      "old_string": {
        "type": "string",
        "description": "Exact string to find (must be unique)"
      },
      "new_string": {
        "type": "string",
        "description": "String to replace with"
      }
    },
    "required": ["file_path", "old_string", "new_string"]
  }
}
```

**Matching Rules:**
- Exact string match required
- Must be unique (error if multiple matches)
- Preserves whitespace and indentation
- Case-sensitive by default
- Supports multi-line strings

**Display:**
```
┌─ Edit ────────────────────────────────────────────────────────┐
│ File: src/auth.py                                             │
│ Lines: 45-48                                                  │
├───────────────────────────────────────────────────────────────┤
│  45  def authenticate(user, password):                        │
│  46 -    if user.password == password:                        │
│  47 +    if verify_password(user.password, password):         │
│  48      return True                                          │
├───────────────────────────────────────────────────────────────┤
│ ✓ 1 replacement made                                          │
│ [View Full Diff] [Undo]                                       │
└───────────────────────────────────────────────────────────────┘
```

**Error Handling:**
```
✗ Edit failed: Could not find unique match

Found 0 matches for:
"def hello():"

In file: src/greetings.py

Suggestion: Make the search string more specific.
────────────────────────────────────────────────────────────────

✗ Edit failed: Multiple matches found

Found 3 matches for:
"return True"

At lines: 23, 45, 67

Suggestion: Include more surrounding context.
────────────────────────────────────────────────────────────────
```

### 4.4 MultiEdit Tool

**Purpose:** Edit multiple files or make multiple edits at once

**Tool Definition:**
```json
{
  "name": "MultiEdit",
  "description": "Edit multiple files in a single operation",
  "input_schema": {
    "type": "object",
    "properties": {
      "edits": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "file_path": {"type": "string"},
            "old_string": {"type": "string"},
            "new_string": {"type": "string"}
          }
        }
      }
    },
    "required": ["edits"]
  }
}
```

**Display:**
```
┌─ MultiEdit ───────────────────────────────────────────────────┐
│ Editing 5 files...                                            │
├───────────────────────────────────────────────────────────────┤
│ ✓ src/auth.py                (2 changes)                      │
│ ✓ src/user.py                (1 change)                       │
│ ✓ src/database.py            (3 changes)                      │
│ ⏳ src/api.py                (processing...)                  │
│ ○ src/utils.py               (pending)                        │
├───────────────────────────────────────────────────────────────┤
│ Progress: 3/5 files (60%)                                     │
│ [Show All Diffs] [Abort Remaining]                            │
└───────────────────────────────────────────────────────────────┘
```

**Atomic Operations:**
- All edits succeed or all fail (rollback on error)
- Preview all changes before applying
- Grouped undo/redo
- Batch diff display

### 4.5 Bash Tool

**Purpose:** Execute shell commands with persistent sessions

**Tool Definition:**
```json
{
  "name": "Bash",
  "description": "Execute shell commands in a persistent bash session",
  "input_schema": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "Shell command to execute"
      },
      "background": {
        "type": "boolean",
        "description": "Run in background (default: false)"
      },
      "timeout": {
        "type": "integer",
        "description": "Timeout in milliseconds (default: 30000)"
      }
    },
    "required": ["command"]
  }
}
```

**Session Features:**
- Persistent environment variables
- Working directory maintained across calls
- Command history within session
- Environment inheritance from parent shell
- Background process management

**Display:**
```
┌─ Bash ────────────────────────────────────────────────────────┐
│ $ npm test                                                    │
│ Working Directory: ~/project/                                 │
│ Duration: 2.3s                                                │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ > Running tests...                                            │
│                                                               │
│   ✓ Auth tests                 (15 tests, 0.5s)              │
│   ✓ User tests                 (8 tests, 0.3s)               │
│   ✗ Database tests             (2 failed, 12 passed, 1.2s)   │
│                                                               │
│ Test Suites: 2 passed, 1 failed, 3 total                     │
│ Tests:       23 passed, 2 failed, 25 total                   │
│                                                               │
│ Exit code: 1                                                  │
├───────────────────────────────────────────────────────────────┤
│ [Show Full Output] [Run Again] [Debug Failures]              │
└───────────────────────────────────────────────────────────────┘
```

**Background Execution:**
```
┌─ Bash (Background) ───────────────────────────────────────────┐
│ $ npm run dev                                                 │
│ Status: Running                                               │
│ PID: 12345                                                    │
│ Started: 14:30:25                                             │
├───────────────────────────────────────────────────────────────┤
│ Latest output:                                                │
│ > Server listening on http://localhost:3000                   │
│ > Compiled successfully                                       │
│                                                               │
│ [View Live Output] [Stop Process] [View Logs]                │
└───────────────────────────────────────────────────────────────┘
```

**Permission Filtering:**
```
Configurable allowed commands:
- git add:*        # Allow all git add commands
- git status:*     # Allow git status
- git commit:*     # Allow git commit
- npm install:*    # Allow npm install
- python:*         # Allow python execution
- !rm:*            # Deny all rm commands
- !sudo:*          # Deny all sudo commands
```

### 4.6 Grep Tool

**Purpose:** Search file contents using ripgrep

**Tool Definition:**
```json
{
  "name": "Grep",
  "description": "Search for patterns in files using ripgrep",
  "input_schema": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "Search pattern (regex supported)"
      },
      "path": {
        "type": "string",
        "description": "Path to search (file or directory)"
      },
      "case_sensitive": {
        "type": "boolean",
        "description": "Case-sensitive search (default: false)"
      },
      "whole_word": {
        "type": "boolean",
        "description": "Match whole words only"
      },
      "context_lines": {
        "type": "integer",
        "description": "Lines of context around matches"
      },
      "max_count": {
        "type": "integer",
        "description": "Maximum number of matches to return"
      }
    },
    "required": ["pattern"]
  }
}
```

**Display:**
```
┌─ Grep ────────────────────────────────────────────────────────┐
│ Pattern: "authenticate"                                       │
│ Path: src/                                                    │
│ Found: 8 matches in 3 files                                   │
├───────────────────────────────────────────────────────────────┤
│ src/auth.py:                                                  │
│   45: def authenticate(user, password):                       │
│   67:     result = authenticate(user, pwd)                    │
│                                                               │
│ src/middleware.py:                                            │
│   12: from auth import authenticate                           │
│   23:     if not authenticate(req.user, req.password):        │
│                                                               │
│ src/api.py:                                                   │
│   34: # Authentication endpoint                               │
│   35: @app.post('/authenticate')                              │
│   36: def authenticate_user():                                │
│   78:     return authenticate(username, password)             │
├───────────────────────────────────────────────────────────────┤
│ [Show All] [Filter by File] [Export Results]                 │
└───────────────────────────────────────────────────────────────┘
```

**Features:**
- Regex pattern matching
- Case-sensitive/insensitive options
- Context lines (-A, -B, -C flags)
- File type filtering
- Exclude patterns
- Multiline search support
- Results preview with syntax highlighting

### 4.7 Glob Tool

**Purpose:** Find files by pattern matching

**Tool Definition:**
```json
{
  "name": "Glob",
  "description": "Find files matching patterns",
  "input_schema": {
    "type": "object",
    "properties": {
      "pattern": {
        "type": "string",
        "description": "Glob pattern (e.g., *.py, **/*.js)"
      },
      "path": {
        "type": "string",
        "description": "Base path to search from"
      },
      "exclude": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Patterns to exclude"
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum files to return"
      }
    },
    "required": ["pattern"]
  }
}
```

**Display:**
```
┌─ Glob ────────────────────────────────────────────────────────┐
│ Pattern: src/**/*.py                                          │
│ Found: 47 files                                               │
├───────────────────────────────────────────────────────────────┤
│ src/                                                          │
│  ├─ auth.py                     2.3 KB                        │
│  ├─ user.py                     1.8 KB                        │
│  ├─ database.py                 5.2 KB                        │
│  └─ utils/                                                    │
│     ├─ helpers.py               3.1 KB                        │
│     ├─ validators.py            2.7 KB                        │
│     └─ ...                                                    │
│  └─ api/                                                      │
│     ├─ routes.py                4.5 KB                        │
│     └─ ...                                                    │
│                                                               │
│ Total: 47 files (125.6 KB)                                    │
├───────────────────────────────────────────────────────────────┤
│ [Show All] [Filter] [Copy Paths]                             │
└───────────────────────────────────────────────────────────────┘
```

**Supported Patterns:**
```
*.py             # All .py files in current directory
**/*.py          # All .py files recursively
src/**/*.test.js # All .test.js files under src/
**/test_*.py     # All test files
!**/node_modules/** # Exclude node_modules
```

### 4.8 TodoWrite Tool

**Purpose:** Create and manage task lists

**Tool Definition:**
```json
{
  "name": "TodoWrite",
  "description": "Write tasks to the todo list",
  "input_schema": {
    "type": "object",
    "properties": {
      "tasks": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {"type": "string"},
            "description": {"type": "string"},
            "status": {
              "type": "string",
              "enum": ["pending", "in_progress", "completed", "blocked"]
            },
            "priority": {
              "type": "string",
              "enum": ["low", "medium", "high", "urgent"]
            }
          }
        }
      }
    },
    "required": ["tasks"]
  }
}
```

**Display:**
```
┌─ Todo List ───────────────────────────────────────────────────┐
│                                                               │
│ 📋 Current Sprint Tasks                                       │
│                                                               │
│ ✓ [1] Fix authentication bug                   [Completed]   │
│ ⏳ [2] Add error handling to API              [In Progress]  │
│ ○ [3] Write unit tests                          [Pending]    │
│ ⚠ [4] Update documentation                      [Blocked]    │
│ ○ [5] Refactor database layer                   [Pending]    │
│                                                               │
│ Progress: 1/5 completed (20%)                                 │
│ ▓▓▒▒▒▒▒▒▒▒                                                    │
│                                                               │
│ [Edit Task] [Add Task] [Clear Completed]                     │
└───────────────────────────────────────────────────────────────┘
```

**Task States:**
- ○ Pending (not started)
- ⏳ In Progress (currently working)
- ✓ Completed (finished)
- ⚠ Blocked (waiting on something)
- ✗ Cancelled (not doing)

### 4.9 TodoRead Tool

**Purpose:** Read and display todo list

**Tool Definition:**
```json
{
  "name": "TodoRead",
  "description": "Read the current todo list",
  "input_schema": {
    "type": "object",
    "properties": {
      "filter": {
        "type": "string",
        "enum": ["all", "pending", "in_progress", "completed", "blocked"]
      }
    }
  }
}
```

### 4.10 NotebookEdit Tool

**Purpose:** Edit Jupyter notebook cells

**Tool Definition:**
```json
{
  "name": "NotebookEdit",
  "description": "Edit cells in Jupyter notebooks",
  "input_schema": {
    "type": "object",
    "properties": {
      "notebook_path": {"type": "string"},
      "cell_index": {"type": "integer"},
      "new_content": {"type": "string"},
      "cell_type": {
        "type": "string",
        "enum": ["code", "markdown"]
      }
    },
    "required": ["notebook_path", "cell_index", "new_content"]
  }
}
```

### 4.11 NotebookRead Tool

**Purpose:** Read Jupyter notebook contents

**Display:**
```
┌─ Notebook: analysis.ipynb ────────────────────────────────────┐
│                                                               │
│ [Cell 1] Markdown                                             │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ # Data Analysis Report                                   │  │
│ │ This notebook contains...                                │  │
│ └─────────────────────────────────────────────────────────┘  │
│                                                               │
│ [Cell 2] Code                                                 │
│ ┌─────────────────────────────────────────────────────────┐  │
│ │ import pandas as pd                                      │  │
│ │ import matplotlib.pyplot as plt                          │  │
│ │                                                          │  │
│ │ df = pd.read_csv('data.csv')                            │  │
│ │ df.head()                                                │  │
│ └─────────────────────────────────────────────────────────┘  │
│ Output:                                                       │
│   [DataFrame preview]                                         │
│                                                               │
│ Total cells: 12                                               │
│ [Edit Cell] [Run Cell] [Add Cell] [Delete Cell]              │
└───────────────────────────────────────────────────────────────┘
```

### 4.12 WebFetch Tool

**Purpose:** Fetch and process web content

**Tool Definition:**
```json
{
  "name": "WebFetch",
  "description": "Fetch content from a URL",
  "input_schema": {
    "type": "object",
    "properties": {
      "url": {"type": "string"},
      "format": {
        "type": "string",
        "enum": ["html", "markdown", "text", "json"]
      }
    },
    "required": ["url"]
  }
}
```

### 4.13 WebSearch Tool

**Purpose:** Search the web

**Tool Definition:**
```json
{
  "name": "WebSearch",
  "description": "Search the web using a search engine",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "num_results": {"type": "integer"}
    },
    "required": ["query"]
  }
}
```

### 4.14 Task Tool

**Purpose:** Launch specialized subagents

**Tool Definition:**
```json
{
  "name": "Task",
  "description": "Launch a specialized subagent for a task",
  "input_schema": {
    "type": "object",
    "properties": {
      "agent_name": {"type": "string"},
      "task_description": {"type": "string"},
      "context": {"type": "object"}
    },
    "required": ["agent_name", "task_description"]
  }
}
```

**Display:**
```
┌─ Task: Code Review ───────────────────────────────────────────┐
│ Agent: code-reviewer                                          │
│ Status: Running                                               │
│ Started: 14:30:25                                             │
├───────────────────────────────────────────────────────────────┤
│ ⏳ Analyzing src/auth.py...                                   │
│ ⏳ Checking security issues...                                │
│ ✓ Found 3 potential improvements                              │
│                                                               │
│ [View Results] [Stop Task]                                    │
└───────────────────────────────────────────────────────────────┘
```

---

## 5. SLASH COMMANDS SYSTEM

### 5.1 Built-in Slash Commands

**Complete List:**
```
/help              Show all commands
/model             Switch model
/mode              Change execution mode
/clear             Clear conversation
/compact           Compact context
/rewind            Rewind conversation
/export            Export session
/history           Show command history
/context           Manage context
/attach            Attach files
/mcp               MCP configuration
/hooks             Manage hooks
/skills            Manage skills
/agents            Manage subagents
/settings          Open settings
/doctor            Run diagnostics
/terminal-setup    Configure terminal
/statusline        Configure status line
/bug               Report bug
/quit              Exit
/exit              Exit (alias)
```

### 5.2 Command Details

**A. /help Command:**
```
> /help

╔═══════════════════════════════════════════════════════════════╗
║                    DEVORBIT CLI COMMANDS                       ║
╠═══════════════════════════════════════════════════════════════╣
║ Navigation & Control:                                         ║
║   /clear          Clear conversation history                  ║
║   /compact        Compact context window                      ║
║   /rewind [n]     Rewind N steps back                        ║
║   /history        Show command history                        ║
║   /quit           Exit Devorbit                               ║
║                                                               ║
║ Configuration:                                                ║
║   /model          Switch AI model                            ║
║   /mode           Change execution mode                       ║
║   /settings       Open settings                               ║
║   /statusline     Configure status line                       ║
║                                                               ║
║ Files & Context:                                              ║
║   /attach <path>  Attach file(s) to context                  ║
║   /context        Manage conversation context                 ║
║   /export         Export session                              ║
║                                                               ║
║ Advanced:                                                     ║
║   /mcp            MCP server configuration                    ║
║   /hooks          Manage execution hooks                      ║
║   /skills         Manage AI skills                           ║
║   /agents         Manage subagents                            ║
║   /doctor         Run system diagnostics                      ║
║                                                               ║
║ Project Commands: (defined in .devorbit/commands/)           ║
║   /project:*      Custom project commands                     ║
║                                                               ║
║ User Commands: (defined in ~/.devorbit/commands/)            ║
║   /*              Your personal commands                      ║
╚═══════════════════════════════════════════════════════════════╝

Type /help <command> for detailed help on a specific command
Example: /help model
```

**B. /model Command:**
```
> /model

┌─ Available Models ────────────────────────────────────────────┐
│                                                               │
│ ANTHROPIC (Current Provider)                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ● claude-sonnet-4-5    Fastest & smartest    [CURRENT]      │
│  ○ claude-opus-4-1      Most capable                          │
│  ○ claude-haiku-4-5     Ultra fast                            │
│                                                               │
│ OPENAI                                                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ○ gpt-5                Latest & greatest                     │
│  ○ gpt-5-codex-mini     Optimized for code                    │
│  ○ gpt-4-turbo          Fast GPT-4                            │
│                                                               │
│ GOOGLE                                                        │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ○ gemini-pro-2-5       Latest Gemini                         │
│  ○ gemini-flash-2       Ultra fast                            │
│                                                               │
│ Select model: █                                               │
│ Or type provider name to switch: anthropic, openai, google    │
└───────────────────────────────────────────────────────────────┘

> /model opus
✓ Switched to claude-opus-4-1

> /model openai gpt-5
✓ Switched provider to OpenAI
✓ Switched model to gpt-5
```

**C. /mode Command:**
```
> /mode

┌─ Execution Modes ─────────────────────────────────────────────┐
│                                                               │
│  ● auto          Execute immediately (default)                │
│  ○ plan          Create plan before execution                 │
│  ○ manual        Ask permission for each step                 │
│                                                               │
│ Select mode: █                                                │
└───────────────────────────────────────────────────────────────┘

> /mode plan
✓ Execution mode set to: plan

Next message will trigger planning mode with extended thinking.
```

**D. /clear Command:**
```
> /clear

⚠ This will clear the conversation history and reset context.

Are you sure? [y/N]: y

✓ Conversation cleared
✓ Context window reset (0/200,000 tokens)
✓ Session continues with ID: abc123

Starting fresh! What would you like to work on?
```

**E. /compact Command:**
```
> /compact Focus on preserving the authentication implementation

⏳ Compacting conversation...
  • Analyzing 45 messages
  • Identifying key information
  • Preserving authentication details
  • Summarizing tool outputs
  • Removing redundant content

✓ Context compacted: 45,000 → 12,000 tokens (73% reduction)
✓ Preserved: Authentication code, recent changes, todo list

Context window: 12,000/200,000 tokens (6%)
```

**F. /rewind Command:**
```
> /rewind

┌─ Conversation History ────────────────────────────────────────┐
│                                                               │
│ Current position: Message #45                                 │
│                                                               │
│ [#45] Fixed the login bug ✓                                   │
│ [#44] Wrote tests for auth                                    │
│ [#43] Refactored user model                                   │
│ [#42] Added error handling                                    │
│ [#41] Updated documentation                                   │
│ [#40] ...                                                     │
│                                                               │
│ Rewind to message: █ (or number of steps back)               │
└───────────────────────────────────────────────────────────────┘

> /rewind 3
⚠ This will undo the last 3 messages and their effects.

Files affected:
  • src/auth.py (3 changes will be reverted)
  • tests/test_auth.py (will be deleted)

Continue? [y/N]: y

✓ Rewound to message #42
✓ Reverted 3 file changes
✓ Deleted 1 test file

You're now at: "Added error handling"
```

**G. /context Command:**
```
> /context

┌─ Context Management ──────────────────────────────────────────┐
│                                                               │
│ Context Window: 45,234/200,000 tokens (22.6%)                │
│ ▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒                      │
│                                                               │
│ Breakdown:                                                    │
│ • System Prompt      2,500 tokens  (5.5%)                    │
│ • Conversation      35,234 tokens (77.9%)                    │
│ • File Contents      5,000 tokens (11.1%)                    │
│ • Tool Outputs       2,500 tokens  (5.5%)                    │
│                                                               │
│ Attached Files: (5,000 tokens)                               │
│ • src/auth.py                1,200 tokens                     │
│ • src/user.py                1,500 tokens                     │
│ • tests/test_auth.py         2,300 tokens                     │
│                                                               │
│ Commands:                                                     │
│ [C] Compact context                                           │
│ [D] Detach files                                              │
│ [V] View breakdown                                            │
│ [X] Close                                                     │
└───────────────────────────────────────────────────────────────┘
```

**H. /attach Command:**
```
> /attach src/auth.py

✓ Attached src/auth.py (1,200 tokens)

> /attach src/**/*.py

Found 15 Python files. Attach all? [y/N]: y

✓ Attached 15 files (8,500 tokens total)

> /attach --detach src/auth.py

✓ Detached src/auth.py (freed 1,200 tokens)

> /attach --list

Attached Files:
• src/user.py           1,500 tokens
• src/database.py       2,100 tokens
• tests/test_auth.py    2,300 tokens

Total: 5,900 tokens
```

**I. /export Command:**
```
> /export

┌─ Export Session ──────────────────────────────────────────────┐
│                                                               │
│ Session ID: abc123def456                                      │
│ Messages: 45                                                  │
│ Files modified: 8                                             │
│ Duration: 2h 34m                                              │
│                                                               │
│ Export format:                                                │
│  ● JSON          Machine-readable format                      │
│  ○ Markdown      Human-readable document                      │
│  ○ HTML          Interactive web page                         │
│                                                               │
│ Include:                                                      │
│  ☑ Conversation messages                                      │
│  ☑ Tool calls and outputs                                     │
│  ☑ File changes (diffs)                                       │
│  ☑ Metadata (timestamps, model, cost)                         │
│  ☐ Thinking blocks                                            │
│                                                               │
│ Save to: ~/exports/session-2025-11-17.json █                 │
│                                                               │
│ [Export] [Cancel]                                             │
└───────────────────────────────────────────────────────────────┘

> /export markdown session.md
✓ Exported to session.md (125 KB)
```

**J. /mcp Command:**
```
> /mcp

┌─ MCP Server Management ───────────────────────────────────────┐
│                                                               │
│ Active Servers:                                               │
│  ✓ github          12 tools      [Disable] [Configure]       │
│  ✓ jira             8 tools      [Disable] [Configure]       │
│  ✗ filesystem       5 tools      [Enable]  [Configure]       │
│                                                               │
│ Available Servers:                                            │
│  • slack                          [Add]                       │
│  • google-drive                   [Add]                       │
│  • postgresql                     [Add]                       │
│  • custom                         [Add Custom...]             │
│                                                               │
│ [Reload All] [Debug Mode] [Add Server] [Close]               │
└───────────────────────────────────────────────────────────────┘

> /mcp add github --scope project
✓ Added github MCP server
✓ Loaded 12 tools
✓ Saved to .mcp.json
```

### 5.3 Custom Slash Commands

**Project Commands:**
```
Location: .devorbit/commands/

File: .devorbit/commands/review.md
───────────────────────────────────────────────────────────────
---
description: Perform code review
allowed-tools: Read, Grep, Bash
---

Review the following files for:
1. Code quality and best practices
2. Security vulnerabilities
3. Performance issues
4. Test coverage

Focus on: $ARGUMENTS
───────────────────────────────────────────────────────────────

Usage:
> /project:review "authentication module"
```

**User Commands:**
```
Location: ~/.devorbit/commands/

File: ~/.devorbit/commands/deploy.md
───────────────────────────────────────────────────────────────
---
description: Deploy to staging
allowed-tools: Bash(git:*), Bash(npm:*), Bash(ssh:*)
---

Deploy current branch to staging:
1. Run tests
2. Build production bundle
3. Push to staging server
4. Run smoke tests

Environment: $ARGUMENTS
───────────────────────────────────────────────────────────────

Usage:
> /deploy staging
```

**Command Frontmatter Options:**
```yaml
---
description: Short description shown in autocomplete
allowed-tools: [Read, Write, Edit, Bash]  # Tool permissions
model: claude-opus-4-1                     # Specific model
temperature: 0.7                           # Temperature override
max-tokens: 4000                           # Token limit
cache: true                                # Enable caching
---
```

**Variables in Commands:**
```
$ARGUMENTS    - All text after command
$PROJECT_DIR  - Current project directory
$GIT_BRANCH   - Current git branch
$GIT_COMMIT   - Latest git commit hash
$USER         - Current username
$DATE         - Current date (YYYY-MM-DD)
$TIME         - Current time (HH:MM:SS)
```

### 5.4 Command Autocomplete

```
> /pro█
┌─ Commands ────────────────────────────────────────────────────┐
│ PROJECT COMMANDS                                              │
│  ▸ /project:review       Perform code review                 │
│    /project:test         Run project tests                    │
│    /project:deploy       Deploy to environment               │
│                                                               │
│ SYSTEM COMMANDS                                               │
│    /prompt               Custom prompt                        │
│                                                               │
│ Tab to complete │ Enter to select │ ↑↓ to navigate           │
└───────────────────────────────────────────────────────────────┘
```

---

*Part 2 continues... will create Part 3 with remaining sections*
