# Claude Code CLI - Complete 10000% Clone Specification
## Comprehensive Implementation Guide for Devorbit CLI

**Version:** 2.0 Complete
**Target:** Pixel-Perfect Claude Code Clone with Multi-Provider Support
**Date:** November 17, 2025

---

## TABLE OF CONTENTS

- [Claude Code CLI - Complete 10000% Clone Specification](#claude-code-cli---complete-10000-clone-specification)
  - [Comprehensive Implementation Guide for Devorbit CLI](#comprehensive-implementation-guide-for-devorbit-cli)
  - [TABLE OF CONTENTS](#table-of-contents)
  - [1. TERMINAL UI/UX SPECIFICATIONS](#1-terminal-uiux-specifications)
    - [1.1 Color Scheme \& Theme](#11-color-scheme--theme)
    - [1.2 Terminal Layout Structure](#12-terminal-layout-structure)
    - [1.3 User Prompt Display](#13-user-prompt-display)
    - [1.4 Claude Response Display](#14-claude-response-display)
    - [1.5 Progress Indicators](#15-progress-indicators)
    - [1.6 Message Formatting](#16-message-formatting)
    - [1.7 Notification System](#17-notification-system)
    - [1.8 Input Area Design](#18-input-area-design)
    - [1.9 Scrolling \& Navigation](#19-scrolling--navigation)
    - [1.10 Loading States](#110-loading-states)
  - [2. COMMAND LINE INTERFACE](#2-command-line-interface)
    - [2.1 Main Command](#21-main-command)
    - [2.2 Global Flags](#22-global-flags)
    - [2.3 Print Mode (-p / --print)](#23-print-mode--p----print)
    - [2.4 Session Commands](#24-session-commands)
    - [2.5 Configuration Commands](#25-configuration-commands)
    - [2.6 MCP Management Commands](#26-mcp-management-commands)
    - [2.7 Diagnostic Commands](#27-diagnostic-commands)
  - [3. INTERACTIVE MODE FEATURES](#3-interactive-mode-features)
    - [3.1 Startup Sequence](#31-startup-sequence)
    - [3.2 Input Methods](#32-input-methods)
    - [3.3 Autocomplete System](#33-autocomplete-system)
    - [3.4 Command History](#34-command-history)
    - [3.5 Multi-line Editing](#35-multi-line-editing)
    - [3.6 Context Selection](#36-context-selection)
    - [3.7 Interruption \& Control](#37-interruption--control)
    - [3.8 Session Navigation](#38-session-navigation)

---

## 1. TERMINAL UI/UX SPECIFICATIONS

### 1.1 Color Scheme & Theme

**Default Color Palette:**
```
Primary Colors:
- Brand Orange: #FF6B35 (RGB: 255, 107, 53)
- Brand Blue: #004E89 (RGB: 0, 78, 137)
- Success Green: #10B981 (RGB: 16, 185, 129)
- Warning Yellow: #F59E0B (RGB: 245, 158, 11)
- Error Red: #EF4444 (RGB: 239, 68, 68)

Background Colors:
- Primary Background: #0D1117 (RGB: 13, 17, 23)
- Secondary Background: #161B22 (RGB: 22, 27, 34)
- Tertiary Background: #1C2128 (RGB: 28, 33, 40)
- Border Color: #30363D (RGB: 48, 54, 61)

Text Colors:
- Primary Text: #E6EDF3 (RGB: 230, 237, 243)
- Secondary Text: #8B949E (RGB: 139, 148, 158)
- Muted Text: #6E7681 (RGB: 110, 118, 129)
- Link Color: #58A6FF (RGB: 88, 166, 255)

Syntax Highlighting:
- Keyword: #FF7B72 (RGB: 255, 123, 114)
- String: #A5D6FF (RGB: 165, 214, 255)
- Number: #79C0FF (RGB: 121, 192, 255)
- Comment: #8B949E (RGB: 139, 148, 158)
- Function: #D2A8FF (RGB: 210, 168, 255)
- Variable: #FFA657 (RGB: 255, 166, 87)
```

**Terminal ANSI Color Codes:**
```python
COLORS = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'dim': '\033[2m',
    'italic': '\033[3m',
    'underline': '\033[4m',
    'blink': '\033[5m',
    'reverse': '\033[7m',
    'hidden': '\033[8m',
    'strikethrough': '\033[9m',

    # Foreground colors
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'bright_black': '\033[90m',
    'bright_red': '\033[91m',
    'bright_green': '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue': '\033[94m',
    'bright_magenta': '\033[95m',
    'bright_cyan': '\033[96m',
    'bright_white': '\033[97m',

    # Background colors
    'bg_black': '\033[40m',
    'bg_red': '\033[41m',
    'bg_green': '\033[42m',
    'bg_yellow': '\033[43m',
    'bg_blue': '\033[44m',
    'bg_magenta': '\033[45m',
    'bg_cyan': '\033[46m',
    'bg_white': '\033[47m',

    # RGB colors (24-bit true color)
    # Use: f'\033[38;2;{r};{g};{b}m' for foreground
    # Use: f'\033[48;2;{r};{g};{b}m' for background
}
```

### 1.2 Terminal Layout Structure

**Main Interface Layout:**
```
┌────────────────────────────────────────────────────────────────────────┐
│ Status Line (Top)                                                       │
│ [Model] [Context: 45k/200k] [Git: main] [Cost: $0.23] [Time: 2:34]   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Conversation Area (Scrollable)                                         │
│                                                                         │
│ > User prompt appears here                                             │
│                                                                         │
│ ⏺ Claude's response streams here                                       │
│   - Tool calls shown inline                                            │
│   - Thinking blocks (if enabled)                                       │
│   - Code blocks with syntax highlighting                               │
│   - File diffs with +/- indicators                                     │
│                                                                         │
├────────────────────────────────────────────────────────────────────────┤
│ Input Area (Bottom)                                                     │
│ > [Cursor here] Type your message...                                   │
│ [Tab] for autocomplete | [Ctrl+R] history | [Esc] interrupt           │
└────────────────────────────────────────────────────────────────────────┘
```

**Dimensions:**
- Minimum terminal width: 80 columns
- Recommended width: 120+ columns
- Minimum terminal height: 24 rows
- Status line: 1-4 rows (configurable)
- Input area: 1+ rows (auto-expands for multi-line)
- Conversation area: Remaining space (scrollable)

### 1.3 User Prompt Display

**Format:**
```
> [User Icon] Your prompt text here
  @file1.py @file2.js
  [Image: screenshot.png]
```

**Specifications:**
- Prefix: `> ` (blue color #58A6FF)
- User icon: `👤` or `>` (configurable)
- Text color: Primary text (#E6EDF3)
- File mentions: Cyan with @ prefix (#A5D6FF)
- Timestamp: Muted text on hover/expand
- Multi-line: Preserves formatting
- Word wrap: At terminal width - 2 chars
- Padding: 2 spaces left margin

### 1.4 Claude Response Display

**Streaming Response Format:**
```
⏺ [Thinking...] (if extended thinking enabled)
▸ Let me help you with that.

▸ I'll need to:
  1. Read the current file
  2. Make the necessary changes
  3. Run tests to verify

[Tool Call: Read]
──────────────────────────────────────────
Tool: Read
File: src/main.py
──────────────────────────────────────────
[Show Output] [Collapse]

▸ Based on the file contents, I'll update...
```

**Response Components:**

**A. Response Prefix:**
- Streaming: `⏺` (orange circle, animated)
- Complete: `●` (solid circle)
- Error: `⚠` (warning triangle, red)
- Color: Brand orange (#FF6B35)

**B. Thinking Blocks:**
```
┌─ Extended Thinking ─────────────────────────────────────┐
│ Let me analyze the requirements...                      │
│ - First, I need to understand the current structure     │
│ - Then identify the best approach                       │
│ - Finally implement the solution                        │
└──────────────────────────────────────────────────────────┘
```
- Border: Dim border color
- Background: Slightly lighter than terminal
- Text: Italic, muted color
- Collapsible: Click to expand/collapse
- Show by default: When --extended-thinking flag used

**C. Tool Calls Display:**
```
┌─ Tool: Read ─────────────────────────────────────────────┐
│ File: src/components/Header.tsx                          │
│ Status: ✓ Success                                        │
├──────────────────────────────────────────────────────────┤
│ [Output Preview - Click to expand]                       │
│ import React from 'react';                               │
│ ...                                                      │
└──────────────────────────────────────────────────────────┘
```
- Tool name: Bold, cyan color
- Parameters: Muted color
- Status indicator:
  - `⏳` Pending (yellow)
  - `✓` Success (green)
  - `✗` Failed (red)
  - `⏸` Waiting for permission (orange)
- Output: Collapsible, max 20 lines preview
- Duration: Shown in ms/s
- Expandable: Click or press 'e' to expand

**D. Code Blocks:**
````
```python  [Copy] [Apply]
def hello_world():
    print("Hello, World!")
```
````
- Language identifier: Top-right, muted
- Background: Slightly darker than terminal
- Border: Left border 2px, language color
- Line numbers: Optional (toggle with setting)
- Syntax highlighting: Full support
- Buttons: Copy, Apply (top-right corner)
- Copy feedback: "Copied!" tooltip (2s)

**E. File Diffs:**
```
╭─ src/main.py ──────────────────────────────────────╮
│ @@ -10,3 +10,4 @@                                  │
│ def main():                                        │
│ -    print("Hello")                      [Old]    │
│ +    print("Hello, World!")              [New]    │
│ +    return 0                            [New]    │
╰────────────────────────────────────────────────────╯
```
- File path: Bold, top of diff
- Line numbers: Muted, left side
- Removed lines: Red background (#3F1F1F), `-` prefix
- Added lines: Green background (#1F3F1F), `+` prefix
- Context lines: Normal background
- Syntax highlighting: Applied to diff content
- Expand button: "Show full diff" if truncated
- Unified diff format by default
- Side-by-side: Optional (--diff-format=side-by-side)

### 1.5 Progress Indicators

**A. Streaming Indicator:**
```
⏺ Analyzing codebase... ▓▓▓▓▓▒▒▒▒▒ 50%
```
- Animation: Spinner chars `⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`
- Progress bar: ASCII blocks `▓▒░`
- Color: Cyan (#58A6FF)
- Update frequency: 100ms

**B. Tool Execution Progress:**
```
[●●●●○○○○○○] Reading files... 40% (2/5)
```
- Filled: `●` (green)
- Empty: `○` (dim)
- Percentage: Right-aligned
- Count: `(current/total)`

**C. Background Task Indicator:**
```
⚙ Running tests in background... [View Output]
```
- Icon: `⚙` (animated rotation)
- Status: Updated every second
- Link: Clickable to view output

### 1.6 Message Formatting

**Text Formatting:**
- **Bold**: `**text**` → **text**
- *Italic*: `*text*` → *text*
- `Code`: `` `text` `` → `text`
- ~~Strikethrough~~: `~~text~~` → ~~text~~
- [Link](url): Blue underlined text
- > Quote: Left border, indented

**Lists:**
```
• Unordered item 1
• Unordered item 2
  • Nested item

1. Ordered item 1
2. Ordered item 2
   a. Nested item
```

**Tables:**
```
┌─────────┬──────────┬──────────┐
│ Column1 │ Column2  │ Column3  │
├─────────┼──────────┼──────────┤
│ Data1   │ Data2    │ Data3    │
│ Data4   │ Data5    │ Data6    │
└─────────┴──────────┴──────────┘
```

### 1.7 Notification System

**A. Info Notifications:**
```
ℹ Session saved to ~/.devorbit/sessions/abc123
```
- Icon: `ℹ` (blue)
- Duration: 3 seconds
- Position: Top-right corner
- Background: Semi-transparent blue

**B. Warning Notifications:**
```
⚠ Context window is 80% full. Consider using /clear
```
- Icon: `⚠` (yellow)
- Duration: 5 seconds
- Background: Semi-transparent yellow
- Dismissible: Press 'd' or click X

**C. Error Notifications:**
```
✗ Failed to read file: Permission denied
```
- Icon: `✗` (red)
- Duration: Persistent until dismissed
- Background: Semi-transparent red
- Action buttons: [Retry] [Dismiss]

**D. Success Notifications:**
```
✓ 5 files modified successfully
```
- Icon: `✓` (green)
- Duration: 2 seconds
- Background: Semi-transparent green

### 1.8 Input Area Design

**Default State:**
```
> █ Type your message... (Ctrl+Enter to send)
```

**Multi-line State:**
```
┌─ Message ────────────────────────────────────────────────┐
│ > Line 1 of your message                                 │
│ > Line 2 of your message                                 │
│ > Line 3█                                                │
│                                                           │
│ [Ctrl+Enter] Send | [Shift+Enter] New line | [Esc] Clear│
└───────────────────────────────────────────────────────────┘
```

**With File Attachments:**
```
> Your message here
📎 Attached:
  • file1.py (2.3 KB) [×]
  • file2.js (1.5 KB) [×]
  • image.png (150 KB) [×]
```

**Autocomplete Active:**
```
> /mo█
┌─ Suggestions ─────┐
│ ▸ /model          │
│   /move           │
│   /mcp            │
└───────────────────┘
```

### 1.9 Scrolling & Navigation

**Scroll Indicators:**
```
Top of conversation:
┌────────────────────────────────────────────┐
│ ▲ Start of session                         │
└────────────────────────────────────────────┘

More content above:
┌────────────────────────────────────────────┐
│ ▲▲▲ Scroll up to see earlier messages      │
└────────────────────────────────────────────┘

More content below:
┌────────────────────────────────────────────┐
│ ▼▼▼ Scroll down to see recent messages     │
└────────────────────────────────────────────┘

End of conversation:
┌────────────────────────────────────────────┐
│ ▼ End of session                           │
└────────────────────────────────────────────┘
```

**Scroll Behavior:**
- Mouse wheel: 3 lines per scroll
- Page Up/Down: Full page scroll
- Home/End: Jump to start/end
- Vim keys: j/k for up/down
- Auto-scroll: Follow new messages
- Snap to bottom: On new user input

### 1.10 Loading States

**Initial Load:**
```
┌────────────────────────────────────────────┐
│                                            │
│        🤖 Devorbit CLI v2.0                │
│                                            │
│        ⏳ Initializing...                  │
│        • Loading configuration             │
│        • Connecting to provider            │
│        • Preparing tools                   │
│                                            │
└────────────────────────────────────────────┘
```

**Model Switching:**
```
⚙ Switching to Claude Sonnet 4.5... Done ✓
```

**File Processing:**
```
📁 Processing files...
  ✓ file1.py (0.2s)
  ✓ file2.js (0.3s)
  ⏳ file3.ts (processing...)
  ○ file4.css (pending)
```

---

## 2. COMMAND LINE INTERFACE

### 2.1 Main Command

**Syntax:**
```bash
devorbit [command] [options] [prompt]
```

**Primary Commands:**
```bash
# Interactive mode (default)
devorbit
devorbit --interactive

# Print mode (one-off prompt)
devorbit -p "your prompt here"
devorbit --print "your prompt here"

# Resume previous session
devorbit --resume
devorbit --resume <session-id>

# Continue last session
devorbit --continue

# Chat mode (continuous conversation)
devorbit --chat

# List sessions
devorbit sessions
devorbit sessions --list

# Export session
devorbit export <session-id>

# Import session
devorbit import <session-file>

# MCP management
devorbit mcp
devorbit mcp add <server-name>
devorbit mcp remove <server-name>
devorbit mcp list

# Configuration
devorbit config
devorbit config --init
devorbit config --edit

# Doctor (diagnostics)
devorbit doctor

# Version info
devorbit --version
devorbit -v

# Help
devorbit --help
devorbit -h
```

### 2.2 Global Flags

**Provider Selection:**
```bash
# Select LLM provider
--provider <name>           # anthropic, openai, gemini, mistral, codellama
-P <name>                   # Short form

# Examples:
devorbit --provider openai
devorbit -P gemini
```

**Model Selection:**
```bash
# Select specific model
--model <model-name>
-m <model-name>

# Small fast model for simple tasks
--small-model <model-name>
--fast-model <model-name>

# Examples:
devorbit --model claude-sonnet-4-5
devorbit --model gpt-4
devorbit --model gemini-pro
devorbit -m mistral-large
```

**Available Models by Provider:**
```
Anthropic:
  - claude-opus-4-1
  - claude-opus-4
  - claude-sonnet-4-5
  - claude-sonnet-4
  - claude-haiku-4-5
  - claude-haiku-3-5

OpenAI:
  - gpt-5
  - gpt-5-codex-mini
  - gpt-4-turbo
  - gpt-4
  - gpt-3.5-turbo

Google:
  - gemini-pro-2-5
  - gemini-pro-2
  - gemini-pro-1-5
  - gemini-flash-2
  - gemini-flash-1-5

Mistral:
  - mistral-large-2
  - mistral-large
  - mistral-medium
  - mistral-small

Code Llama:
  - codellama-70b
  - codellama-34b
  - codellama-13b
```

**Context & Memory:**
```bash
--max-tokens <number>       # Max context window tokens
--temperature <float>       # Temperature (0.0-1.0)
--top-p <float>             # Top-p sampling
--top-k <integer>           # Top-k sampling
--cache-prompt              # Enable prompt caching
--no-cache                  # Disable all caching
```

**Output Control:**
```bash
--output-format <format>    # json, text, markdown
-o <format>                 # Short form
--stream                    # Enable streaming (default)
--no-stream                 # Disable streaming
--verbose                   # Verbose output
-v                          # Short form
--quiet                     # Minimal output
-q                          # Short form
--debug                     # Debug mode
--log-level <level>         # trace, debug, info, warn, error
```

**File & Directory:**
```bash
--file <path>               # Include file in context
-f <path>                   # Short form (can be used multiple times)
--directory <path>          # Include directory
-d <path>                   # Short form
--exclude <pattern>         # Exclude files matching pattern
--include <pattern>         # Only include files matching pattern
```

**Execution Control:**
```bash
--dangerously-skip-permissions  # Skip all permission prompts
--auto-approve              # Auto-approve all actions
--dry-run                   # Show what would be done without executing
--sandbox                   # Run in sandboxed environment
--network-isolation         # Disable network access
--filesystem-isolation      # Restrict filesystem access
```

**System Prompts:**
```bash
--system-prompt <text>      # Custom system prompt (replaces default)
--append-system-prompt <text> # Append to default system prompt
--system-prompt-file <path> # Load system prompt from file
```

**Session Management:**
```bash
--session-id <id>           # Use specific session ID
--no-save                   # Don't save session
--save-to <path>            # Save session to specific location
```

**MCP & Tools:**
```bash
--mcp-config <path>         # MCP configuration file
--mcp-debug                 # Enable MCP debugging
--disable-tools             # Disable all tools
--enable-tools <list>       # Enable specific tools (comma-separated)
--disable-tool <name>       # Disable specific tool
```

**Agents & Skills:**
```bash
--agents <json>             # Define custom subagents (JSON)
--agent-file <path>         # Load agents from file
--skills <list>             # Enable specific skills
--disable-skills            # Disable all skills
```

**Mode Selection:**
```bash
--mode <mode>               # auto, plan, execute
--plan-mode                 # Enable planning mode
--extended-thinking         # Enable extended thinking
--no-thinking               # Disable thinking blocks
```

**Display & UI:**
```bash
--no-color                  # Disable colored output
--color <mode>              # auto, always, never
--statusline <template>     # Custom status line template
--no-statusline             # Disable status line
--theme <name>              # Color theme (dark, light, custom)
--diff-format <format>      # unified, side-by-side, compact
```

**Git Integration:**
```bash
--auto-commit               # Auto-commit changes
--no-commit                 # Disable auto-commit
--commit-message <text>     # Custom commit message template
--branch <name>             # Work in specific branch
--worktree <path>           # Use git worktree
```

**Advanced:**
```bash
--checkpoint <name>         # Create checkpoint
--rewind <steps>            # Rewind N steps
--replay <session-id>       # Replay session
--export-format <format>    # Export format (json, markdown, html)
--hooks-enable              # Enable hooks
--hooks-disable             # Disable all hooks
--plugin <name>             # Load specific plugin
```

### 2.3 Print Mode (-p / --print)

**Basic Usage:**
```bash
# Single prompt, exit after response
devorbit -p "explain this code" -f main.py

# With specific model
devorbit -p "write tests" --model claude-sonnet-4-5

# With output format
devorbit -p "analyze bugs" -o json > output.json

# Pipe input
cat error.log | devorbit -p "explain these errors"

# Multiple files
devorbit -p "refactor these files" -f src/*.py
```

**Output Formats:**
```bash
# JSON output
devorbit -p "..." -o json
{
  "content": "Response text",
  "tool_calls": [...],
  "usage": { "input_tokens": 100, "output_tokens": 200 },
  "model": "claude-sonnet-4-5",
  "finish_reason": "end_turn"
}

# Plain text (default)
devorbit -p "..."
Response text only, no formatting

# Markdown
devorbit -p "..." -o markdown
# Response
Response with markdown formatting
```

**Streaming in Print Mode:**
```bash
# Stream output (default)
devorbit -p "..." --stream

# No streaming (wait for complete response)
devorbit -p "..." --no-stream
```

**Error Handling:**
```bash
# Exit codes:
0  - Success
1  - General error
2  - Invalid arguments
3  - API error
4  - Permission denied
5  - File not found
6  - Network error
7  - Timeout
8  - Interrupted by user
```

### 2.4 Session Commands

**List Sessions:**
```bash
devorbit sessions --list
devorbit sessions -l

# Output:
┌────────────────────┬─────────────────────┬──────────┬────────┐
│ Session ID         │ Last Modified       │ Messages │ Cost   │
├────────────────────┼─────────────────────┼──────────┼────────┤
│ abc123def456       │ 2025-11-17 14:30   │ 45       │ $0.23  │
│ xyz789uvw012       │ 2025-11-16 09:15   │ 12       │ $0.05  │
│ ...                │ ...                 │ ...      │ ...    │
└────────────────────┴─────────────────────┴──────────┴────────┘
```

**Resume Session:**
```bash
# Resume last session
devorbit --resume

# Resume specific session
devorbit --resume abc123def456

# Resume with different model
devorbit --resume abc123 --model gpt-4
```

**Continue Session:**
```bash
# Continue from where you left off
devorbit --continue

# Equivalent to:
devorbit --resume <last-session-id>
```

**Delete Session:**
```bash
devorbit sessions delete <session-id>
devorbit sessions rm <session-id>

# Delete all sessions
devorbit sessions clear --confirm
```

**Export Session:**
```bash
# Export to JSON
devorbit export <session-id>
devorbit export <session-id> -o session.json

# Export to Markdown
devorbit export <session-id> --format markdown -o session.md

# Export to HTML
devorbit export <session-id> --format html -o session.html
```

**Import Session:**
```bash
devorbit import session.json
devorbit import session.json --session-id new-id
```

### 2.5 Configuration Commands

**Initialize Configuration:**
```bash
devorbit config --init

# Creates:
# ~/.devorbit/config.json
# ~/.devorbit/settings.json
# ~/.devorbit/.env
```

**Edit Configuration:**
```bash
# Open in default editor
devorbit config --edit

# Open specific config file
devorbit config --edit settings
devorbit config --edit mcp
```

**Get Configuration Value:**
```bash
devorbit config get <key>
devorbit config get provider
devorbit config get model
```

**Set Configuration Value:**
```bash
devorbit config set <key> <value>
devorbit config set provider anthropic
devorbit config set model claude-sonnet-4-5
```

**List All Settings:**
```bash
devorbit config list
devorbit config show
```

### 2.6 MCP Management Commands

**List MCP Servers:**
```bash
devorbit mcp list
devorbit mcp ls

# Output:
┌─────────────┬──────────┬─────────┬───────────────────┐
│ Server      │ Status   │ Tools   │ Location          │
├─────────────┼──────────┼─────────┼───────────────────┤
│ github      │ Active   │ 12      │ Project           │
│ jira        │ Active   │ 8       │ User              │
│ filesystem  │ Inactive │ 5       │ Project           │
└─────────────┴──────────┴─────────┴───────────────────┘
```

**Add MCP Server:**
```bash
# Add from template
devorbit mcp add github

# Add custom server
devorbit mcp add my-server --command "node server.js" --args '["--port", "3000"]'

# Add to project config
devorbit mcp add github --scope project

# Add to user config
devorbit mcp add github --scope user
```

**Remove MCP Server:**
```bash
devorbit mcp remove <server-name>
devorbit mcp rm <server-name>
```

**Test MCP Server:**
```bash
devorbit mcp test <server-name>
```

**Reload MCP Servers:**
```bash
devorbit mcp reload
```

### 2.7 Diagnostic Commands

**Run Diagnostics:**
```bash
devorbit doctor
devorbit --doctor

# Checks:
# ✓ Provider API keys
# ✓ MCP servers
# ✓ Tool availability
# ✓ Configuration validity
# ✓ Network connectivity
# ✓ Filesystem permissions
# ✓ Git configuration
# ⚠ Warnings for non-critical issues
# ✗ Errors that need attention
```

**Output Format:**
```
🔍 Running diagnostics...

Provider Configuration:
  ✓ Anthropic API key found
  ✓ OpenAI API key found
  ⚠ Gemini API key not configured
  ✗ Mistral API key invalid

MCP Servers:
  ✓ github (12 tools available)
  ✓ jira (8 tools available)
  ✗ filesystem (connection failed)

Tools:
  ✓ Read
  ✓ Write
  ✓ Edit
  ✓ Bash
  ✓ Grep
  ✓ Glob

Configuration:
  ✓ ~/.devorbit/config.json valid
  ✓ ./.devorbit/DEVORBIT.md found
  ✓ ./.mcp.json valid

Git:
  ✓ Git installed (v2.40.0)
  ✓ Repository initialized
  ✓ Clean working directory

Summary:
  ✓ 15 checks passed
  ⚠ 1 warning
  ✗ 2 errors

Run 'devorbit doctor --fix' to auto-fix common issues.
```

**Auto-fix Issues:**
```bash
devorbit doctor --fix
```

---

## 3. INTERACTIVE MODE FEATURES

### 3.1 Startup Sequence

**Initial Display:**
```
████████▄     ▄████████  ▄█    █▄   ▄██████▄     ▄████████  ▀█████████▄   ▄█      ███
███   ▀███   ███    ███ ███    ███ ███    ███   ███    ███   ███    ███ ███  ▀█████████▄
███    ███   ███    █▀  ███    ███ ███    ███   ███    ███   ███    ███ ███▌    ▀███▀▀██
███    ███  ▄███▄▄▄     ███    ███ ███    ███  ▄███▄▄▄▄██▀  ▄███▄▄▄██▀  ███▌     ███   ▀
███    ███ ▀▀███▀▀▀     ███    ███ ███    ███ ▀▀███▀▀▀▀▀   ▀▀███▀▀▀██▄  ███▌     ███
███    ███   ███    █▄  ███    ███ ███    ███ ▀███████████   ███    ██▄ ███      ███
███   ▄███   ███    ███ ███    ███ ███    ███   ███    ███   ███    ███ ███      ███
████████▀    ██████████  ▀██████▀   ▀██████▀    ███    ███ ▄█████████▀  █▀      ▄████▀
                                                 ███    ███

🤖 Devorbit CLI v2.0.0 - Multi-Provider AI Coding Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Provider:  Anthropic (Claude Sonnet 4.5)
Context:   0/200,000 tokens
Project:   ~/projects/my-app
Git:       main branch (clean)

Type /help for available commands or start chatting!
Type /examples to see common usage patterns.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

>█
```

**Loading States:**
```
⏳ Loading configuration...       ✓
⏳ Connecting to Anthropic...     ✓
⏳ Initializing tools...          ✓
⏳ Loading MCP servers...         ✓
⏳ Checking git status...         ✓

Ready! Start typing your message.
```

### 3.2 Input Methods

**Text Input:**
- Single line: Type and press Enter
- Multi-line: Press Shift+Enter for new line
- Submit: Ctrl+Enter (configurable)
- Cancel: Esc to clear current input
- History: Up/Down arrows to navigate

**File Attachments:**
```bash
# Method 1: @ mention
> @src/main.py explain this file

# Method 2: Drag and drop (hold Shift)
[File dropped: main.py]

# Method 3: Explicit attach command
> /attach src/main.py
> now explain this code

# Method 4: Multiple files with glob
> @src/**/*.py analyze all Python files
```

**Image Input:**
```bash
# Method 1: Paste from clipboard (Ctrl+V)
[Image pasted: screenshot.png]

# Method 2: File path
> @images/mockup.png implement this design

# Method 3: URL
> @https://example.com/image.png describe this image
```

**Context Menu:**
```
Right-click in input area:
┌─────────────────────────┐
│ Paste                   │
│ Paste Image (Ctrl+V)    │
│ Attach File... (Ctrl+F) │
│ Insert Snippet          │
│ Clear (Esc)             │
│ Settings                │
└─────────────────────────┘
```

### 3.3 Autocomplete System

**Slash Command Autocomplete:**
```
> /mo█
┌─ Commands ────────────────────────────────────────┐
│ ▸ /model                Switch model              │
│   /move                 Move files                │
│   /mcp                  MCP configuration         │
│ ───────────────────────────────────────────────── │
│ Tab to complete │ Enter to select │ Esc to cancel │
└───────────────────────────────────────────────────┘
```

**File Path Autocomplete:**
```
> @src/comp█
┌─ Files ───────────────────────────────────────────┐
│ ▸ src/components/                                 │
│   src/compiler/                                   │
│   src/compute/                                    │
└───────────────────────────────────────────────────┘
```

**Tool Name Autocomplete:**
```
In custom agents/skills:
tools: [Rea█
┌─ Tools ───────────────────────────────────────────┐
│ ▸ Read                Read files                  │
│   ReadNotebook        Read Jupyter notebooks      │
└───────────────────────────────────────────────────┘
```

**Model Name Autocomplete:**
```
/model clau█
┌─ Models (Anthropic) ──────────────────────────────┐
│ ▸ claude-sonnet-4-5          Fastest & smartest  │
│   claude-opus-4-1            Most capable         │
│   claude-haiku-4-5           Ultra fast           │
└───────────────────────────────────────────────────┘
```

### 3.4 Command History

**History Navigation:**
- Up arrow: Previous command
- Down arrow: Next command
- Ctrl+R: Search history (reverse)
- Ctrl+S: Search history (forward)

**History Search:**
```
(reverse-i-search)`test': devorbit -p "run tests" -f src/**/*.py
```

**History Display:**
```
> /history
┌─ Recent Commands ─────────────────────────────────┐
│ 1. explain this code @main.py                     │
│ 2. write tests for the Auth class                 │
│ 3. /model claude-opus-4-1                         │
│ 4. refactor the database module                   │
│ 5. /clear                                         │
└───────────────────────────────────────────────────┘

Use !n to repeat command (e.g., !3)
```

**History File:**
- Location: `~/.devorbit/history`
- Format: Plain text, one command per line
- Max size: 10,000 entries (configurable)
- Persistence: Across sessions

### 3.5 Multi-line Editing

**Activation:**
- Automatic: When text contains newlines
- Manual: Shift+Enter

**Display:**
```
┌─ Message (Ctrl+Enter to send) ────────────────────┐
│ > Can you help me with:                           │
│ > 1. Fix the login bug                            │
│ > 2. Add error handling                           │
│ > 3. Write tests                                  │
│ >█                                                │
│                                                    │
│ [Ctrl+Enter] Send │ [Shift+Enter] New line │      │
│ [Esc] Clear │ [Ctrl+K] Clear from cursor          │
└────────────────────────────────────────────────────┘
```

**Editing Commands:**
- Ctrl+A: Select all
- Ctrl+K: Cut from cursor to end
- Ctrl+U: Cut from cursor to beginning
- Ctrl+W: Cut previous word
- Ctrl+Y: Paste (yank)

### 3.6 Context Selection

**Manual Context:**
```
> @src/main.py @docs/api.md @tests/test_auth.py
> Review these files for consistency
```

**Glob Patterns:**
```
> @src/**/*.py
> Analyze all Python files

> @tests/**/*.test.js
> Run all JavaScript tests

> @docs/*.md
> Update documentation
```

**Exclude Patterns:**
```
> @src/**/*.py !@src/legacy/**
> Analyze Python files except legacy code
```

**Smart Context:**
```
Claude automatically includes:
- Currently open files (from IDE plugins)
- Recently modified files
- Files mentioned in conversation
- Related files (imports, references)
```

### 3.7 Interruption & Control

**Interrupt Current Operation:**
- Press: Esc
- Double tap: Emergency stop
- Display:
```
⚠ Interrupted by user

Would you like to:
[C] Continue
[R] Retry from last step
[S] Stop completely
[U] Undo last action

Choice: █
```

**Pause/Resume:**
```
Ctrl+Z: Suspend Devorbit
fg: Resume in background
bg: Continue in background

Status while suspended:
⏸ Devorbit paused. Type 'fg' to resume.
```

**Cancel Input:**
- Esc: Clear current input
- Ctrl+C: Interrupt and clear
- Ctrl+D: Exit (if input is empty)

### 3.8 Session Navigation

**Jump to Message:**
```
> /goto <number>
> /goto 15        # Jump to message #15

> /search <query>
> /search "error handling"  # Find messages mentioning this
```

**Scroll Commands:**
```
> /top           # Scroll to top of conversation
> /bottom        # Scroll to bottom
> /up [n]        # Scroll up n messages (default: 10)
> /down [n]      # Scroll down n messages
```

**Message Numbers:**
```
Each message shows its number:

[#15] > Your prompt here

[#16] ⏺ Claude's response
```

---

*This is Part 1 of the specification. Part 2 will continue with remaining sections...*
