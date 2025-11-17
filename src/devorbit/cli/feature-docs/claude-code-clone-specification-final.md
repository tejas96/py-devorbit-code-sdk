bash

cat > /tmp/claude-code-clone-specification-final.md << 'EOF'
# Claude Code CLI - Complete Clone Specification (PART 4 - FINAL)

## 11. PERMISSION SYSTEM

### 11.1 Permission Prompts

**Tool Permission Request:**
```
┌─ Permission Required ─────────────────────────────────────────┐
│                                                               │
│ Claude wants to:                                              │
│ Edit src/auth.py                                              │
│                                                               │
│ Changes:                                                      │
│  Line 45: - if user.password == password:                    │
│           + if verify_password(user.password, password):      │
│                                                               │
│ [A] Approve   [D] Deny   [V] View Full Diff                  │
│ [S] Skip this time   [Always allow Edit]                     │
│                                                               │
│ Your choice: _                                                │
└───────────────────────────────────────────────────────────────┘
```

**Bash Command Permission:**
```
┌─ Bash Permission Required ────────────────────────────────────┐
│                                                               │
│ Claude wants to run:                                          │
│ $ npm install express                                         │
│                                                               │
│ Working directory: ~/project/                                 │
│ Risk level: Low                                               │
│                                                               │
│ [A] Approve   [D] Deny   [E] Edit command                    │
│ [Always allow: npm install:*]                                 │
│                                                               │
│ Your choice: _                                                │
└───────────────────────────────────────────────────────────────┘
```

### 11.2 Permission Rules

**Configuration:**
```json
{
  "permissions": {
    "mode": "prompt",
    "rules": [
      {
        "tool": "Read",
        "action": "allow"
      },
      {
        "tool": "Write",
        "pattern": "src/**",
        "action": "allow"
      },
      {
        "tool": "Write",
        "pattern": ".env*",
        "action": "deny"
      },
      {
        "tool": "Bash",
        "pattern": "git:*",
        "action": "allow"
      },
      {
        "tool": "Bash",
        "pattern": "rm:*",
        "action": "deny"
      },
      {
        "tool": "Bash",
        "pattern": "sudo:*",
        "action": "deny"
      }
    ],
    "dangerous_patterns": [
      "rm -rf",
      "sudo rm",
      "> /dev/sd",
      "dd if=",
      "mkfs",
      ":(){:|:&};:"
    ]
  }
}
```

### 11.3 Auto-Approve Mode

**Enabling:**
```bash
devorbit --dangerously-skip-permissions

⚠ WARNING: All permissions will be automatically approved.
  This is dangerous and could lead to:
  - Data loss
  - System corruption
  - Security vulnerabilities

Continue? [y/N]: y

⚠ Auto-approve enabled
  All tool calls will execute without confirmation
```

**Safety in Auto-Approve:**
- Still respects deny rules
- Dangerous patterns blocked
- File permissions still checked
- Network isolation optional
- Sandbox mode recommended

---

## 12. CONTEXT MANAGEMENT

### 12.1 Context Window Display

**Status Line:**
```
Context: 45,234/200,000 tokens (22.6%)
▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
```

**Detailed View:**
```
> /context

┌─ Context Breakdown ───────────────────────────────────────────┐
│                                                               │
│ Total: 45,234 tokens (22.6% of 200,000)                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                               │
│ System Prompt      2,500 tokens   5.5%  ▓▓░░░░░░░░░░░░░░░░  │
│ Conversation      35,234 tokens  77.9%  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  │
│ File Contents      5,000 tokens  11.1%  ▓▓░░░░░░░░░░░░░░░░  │
│ Tool Outputs       2,500 tokens   5.5%  ▓░░░░░░░░░░░░░░░░░  │
│                                                               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                               │
│ Recent Messages (last 10):        12,000 tokens              │
│ Older Messages (35 messages):     23,234 tokens              │
│                                                               │
│ Attached Files:                                               │
│  • src/auth.py                     1,200 tokens              │
│  • src/user.py                     1,500 tokens              │
│  • tests/test_auth.py              2,300 tokens              │
│                                                               │
│ [Compact] [Detach Files] [Clear Old Messages] [Close]        │
└───────────────────────────────────────────────────────────────┘
```

### 12.2 Auto-Compaction

**Trigger:**
```
⚠ Context window is 80% full (160,000/200,000 tokens)

Auto-compaction will begin soon to preserve space.
Use /clear to start fresh or /compact to do it now.
```

**Compaction Process:**
```
⏳ Compacting conversation...

  • Analyzing 45 messages
  • Identifying key information
  • Preserving recent context (last 10 messages)
  • Summarizing tool outputs
  • Condensing older messages

✓ Compacted: 160,000 → 45,000 tokens (71% reduction)

Preserved:
  • Recent 10 messages (full text)
  • Important decisions and outcomes
  • Active file references
  • Todo list state

Summarized:
  • 35 older messages
  • Tool execution history
  • File change history
```

---

## 13. SESSION MANAGEMENT

### 13.1 Session Storage

**Directory Structure:**
```
~/.devorbit/sessions/
├── active/
│   └── abc123def456.jsonl          Current active session
├── archive/
│   ├── 2025-11-17/
│   │   ├── session-001.jsonl
│   │   ├── session-002.jsonl
│   │   └── ...
│   └── 2025-11-16/
│       └── ...
└── index.json                      Session metadata index
```

**Session File Format (.jsonl):**
```jsonl
{"type":"session_start","timestamp":"2025-11-17T14:30:00Z","session_id":"abc123","provider":"anthropic","model":"claude-sonnet-4-5"}
{"type":"user_message","timestamp":"2025-11-17T14:30:15Z","content":"explain this code","files":["src/main.py"]}
{"type":"assistant_message","timestamp":"2025-11-17T14:30:20Z","content":"This code implements..."}
{"type":"tool_call","timestamp":"2025-11-17T14:30:25Z","tool":"Read","input":{"file_path":"src/main.py"}}
{"type":"tool_result","timestamp":"2025-11-17T14:30:26Z","tool":"Read","output":"..."}
```

### 13.2 Session Metadata

**File: `~/.devorbit/sessions/index.json`**
```json
{
  "sessions": [
    {
      "session_id": "abc123def456",
      "created_at": "2025-11-17T14:30:00Z",
      "updated_at": "2025-11-17T16:45:30Z",
      "provider": "anthropic",
      "model": "claude-sonnet-4-5",
      "project_dir": "~/projects/my-app",
      "git_branch": "feature/auth",
      "message_count": 45,
      "tokens_used": 45234,
      "cost_estimate": 0.23,
      "files_modified": ["src/auth.py", "src/user.py"],
      "status": "active"
    }
  ]
}
```

### 13.3 Session Navigation

**List Sessions:**
```
> devorbit sessions --list

┌────────────────────────────────────────────────────────────────┐
│ Recent Sessions                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Today                                                          │
│  • abc123  14:30  my-app  45 msgs  $0.23  [Resume] [Export]  │
│  • def456  09:15  website 12 msgs  $0.05  [Resume] [Export]  │
│                                                                │
│ Yesterday                                                      │
│  • ghi789  16:20  api     67 msgs  $0.45  [Resume] [Export]  │
│                                                                │
│ This Week                                                      │
│  • jkl012  Mon    webapp  23 msgs  $0.12  [Resume] [Export]  │
│  • mno345  Sun    mobile  34 msgs  $0.18  [Resume] [Export]  │
│                                                                │
│ [Load More] [Search] [Filter] [Close]                         │
└────────────────────────────────────────────────────────────────┘
```

---

## 14. STATUS LINE SYSTEM

### 14.1 Default Status Line

```
[Sonnet 4.5] [45k/200k] [main ✓] [$0.23] [2:34]
```

### 14.2 Customizable Template

**Configuration:**
```json
{
  "statusline": "${model_short} | ${context_percent}% | ${git_info} | ${cost} | ${duration}"
}
```

**Available Variables:**
```
${model}              Full model name
${model_short}        Short model name
${provider}           Provider name
${context}            Context usage (e.g., "45k/200k")
${context_percent}    Context percentage (e.g., "22%")
${context_bar}        Visual bar (e.g., "▓▓▒▒▒")
${git_branch}         Current git branch
${git_status}         Git status symbol (✓, ±, ✗)
${git_info}           Branch + status
${cost}               Session cost
${cost_total}         Total cost today
${duration}           Session duration
${message_count}      Number of messages
${time}               Current time
${date}               Current date
${project_name}       Project directory name
${mcp_servers}        Active MCP servers
${hooks_active}       Active hooks count
```

### 14.3 Multi-Line Status Line

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Sonnet 4.5 • Context: 45k/200k (22%) • Cost: $0.23  │
│ Project: my-app • Branch: main ✓ • Duration: 2h 34m        │
│ MCP: github, jira • Hooks: 3 active • Messages: 45         │
└─────────────────────────────────────────────────────────────┘
```

### 14.4 Status Line Themes

**Minimal:**
```
[Sonnet 4.5] 22% $0.23
```

**Detailed:**
```
┌─ Session Info ───────────────────────────────────────────────┐
│ Model: Claude Sonnet 4.5 (Anthropic)                        │
│ Context: 45,234/200,000 tokens (22.6%)                      │
│ Project: ~/projects/my-app                                  │
│ Git: main ✓ (clean, 3 commits ahead)                       │
│ Cost: $0.23 this session, $1.45 today                       │
│ Duration: 2h 34m 12s                                        │
│ MCP Servers: github (12 tools), jira (8 tools)             │
│ Active Hooks: format-code, run-linter, notify-desktop      │
└──────────────────────────────────────────────────────────────┘
```

---

## 15. KEYBOARD SHORTCUTS

### 15.1 Global Shortcuts

```
Ctrl+C            Interrupt current operation
Ctrl+D            Exit (if input is empty)
Ctrl+Z            Suspend Devorbit (resume with 'fg')
Ctrl+L            Clear screen (keep conversation)

Esc               Interrupt / Cancel input
Double Esc        Emergency stop / Trigger rewind

Tab               Autocomplete
Shift+Tab         Reverse autocomplete

Up Arrow          Previous command in history
Down Arrow        Next command in history
Ctrl+R            Search command history (reverse)
Ctrl+S            Search command history (forward)
```

### 15.2 Input Editing

```
Enter             Send message (single-line mode)
Ctrl+Enter        Send message (always)
Shift+Enter       New line (multi-line mode)

Ctrl+A            Move to beginning of line
Ctrl+E            Move to end of line
Ctrl+K            Delete from cursor to end
Ctrl+U            Delete from cursor to beginning
Ctrl+W            Delete previous word
Ctrl+Y            Paste (yank) deleted text

Alt+Left          Move cursor backward one word
Alt+Right         Move cursor forward one word
Alt+Backspace     Delete previous word

Ctrl+F            Move cursor forward one character
Ctrl+B            Move cursor backward one character
```

### 15.3 Navigation Shortcuts

```
Page Up           Scroll up one page
Page Down         Scroll down one page
Home              Jump to start of conversation
End               Jump to end of conversation

Ctrl+Home         Jump to first message
Ctrl+End          Jump to last message

j                 Scroll down (vim-style)
k                 Scroll up (vim-style)
g                 Go to top (vim-style)
G                 Go to bottom (vim-style)
```

### 15.4 Tool Interaction

```
e                 Expand collapsed tool output
c                 Collapse expanded tool output
v                 View full diff
a                 Apply changes (in permission prompt)
d                 Deny/Dismiss
y                 Yes/Approve
n                 No/Deny
```

---

## 16. ERROR HANDLING & MESSAGES

### 16.1 Error Types

**API Errors:**
```
✗ API Error: Rate limit exceeded

You've made too many requests. Please wait 60 seconds.

Rate limit: 50 requests per minute
Current usage: 52 requests in last minute
Reset in: 45 seconds

[Wait and Retry] [Switch Model] [Cancel]
```

**File Errors:**
```
✗ File Error: Permission denied

Cannot write to: /etc/hosts

Reason: Insufficient permissions
Suggestion: Check file permissions or run with appropriate access

[View Permissions] [Try Different Path] [Cancel]
```

**Network Errors:**
```
✗ Network Error: Connection timeout

Failed to connect to Anthropic API after 30s.

Possible causes:
• No internet connection
• Firewall blocking requests
• API service is down

[Retry] [Check Connection] [Switch Provider]
```

**Tool Errors:**
```
✗ Tool Error: Command failed

Bash command failed: npm test

Exit code: 1
Output:
  FAIL tests/auth.test.js
    ✕ should authenticate user (25 ms)

[View Full Output] [Debug] [Continue Anyway]
```

### 16.2 Warning Messages

**Context Warnings:**
```
⚠ Context window is 80% full

You've used 160,000 of 200,000 tokens.

Recommendations:
• Use /clear to start fresh
• Use /compact to compress conversation
• Detach unused files with /context

[Compact Now] [Ignore] [Clear]
```

**Model Warnings:**
```
⚠ Using fast model for this task

Current model: Claude Haiku 4.5

This model is optimized for speed but may be less capable
for complex tasks. Consider switching to Sonnet or Opus.

[Switch to Sonnet] [Continue with Haiku] [Don't Show Again]
```

### 16.3 Success Messages

```
✓ File saved: src/auth.py
✓ Tests passed (25/25)
✓ Committed: feat: add authentication
✓ MCP server started: github
✓ Session exported: session.json
```

---

## 17. FILE OPERATIONS

### 17.1 File Watching

**Auto-Reload on External Changes:**
```
⚠ File modified externally: src/auth.py

The file was changed outside of this session.

Options:
[R] Reload file content
[I] Ignore changes
[D] Show diff
[A] Always reload automatically

Choice: _
```

### 17.2 Backup System

**Automatic Backups:**
```
Before destructive operations:
• Edit creates: file.ext.backup
• Write (overwrite) creates: file.ext.backup
• MultiEdit creates: .devorbit/backups/timestamp/

Backup location: .devorbit/backups/2025-11-17-14-30-25/
Files backed up:
  • src/auth.py
  • src/user.py
```

**Restore from Backup:**
```
> /restore src/auth.py

┌─ Available Backups ───────────────────────────────────────────┐
│                                                               │
│ src/auth.py backups:                                          │
│  1. 2025-11-17 14:30  Before edit  (2.3 KB)                  │
│  2. 2025-11-17 13:15  Before edit  (2.1 KB)                  │
│  3. 2025-11-17 09:45  Before write (1.9 KB)                  │
│                                                               │
│ Select backup to restore: _                                   │
│ [Preview] [Compare] [Restore] [Cancel]                       │
└───────────────────────────────────────────────────────────────┘
```

---

## 18. GIT INTEGRATION

### 18.1 Git Status Awareness

**Status Display:**
```
Git: main ✓           Clean working directory
Git: main ±           Uncommitted changes
Git: main ✗           Merge conflicts
Git: (no branch)      Detached HEAD
Git: -                Not a git repository
```

### 18.2 Auto-Commit

**Configuration:**
```json
{
  "git": {
    "auto_commit": true,
    "commit_message_template": "${type}: ${summary}\n\n${details}",
    "commit_on_every_change": false,
    "commit_on_session_end": true,
    "auto_push": false
  }
}
```

**Commit Prompt:**
```
✓ Changes made to 3 files

Create a commit? [Y/n]: y

Commit message: feat: add authentication system

[Edit Message] [Skip] [Commit & Push] [Cancel]

✓ Committed: feat: add authentication system (abc1234)
```

### 18.3 Branch Management

```
> /git branch feature/new-feature

✓ Created branch: feature/new-feature
✓ Switched to: feature/new-feature

> /git worktree ../my-app-review feature/review

✓ Created worktree: ../my-app-review
✓ Branch: feature/review
✓ Can run separate Claude instance there
```

---

## 19. MODES & EXECUTION

### 19.1 Auto Mode (Default)

```
Auto Mode: Execute immediately without planning

User: Add error handling to the API

⏺ I'll add error handling to the API endpoints.

[Tool: Read] Reading src/api.py...
✓ Read complete

[Tool: Edit] Adding try-catch blocks...
✓ Edit complete

[Tool: Bash] Running tests...
✓ Tests passed

✓ Error handling added successfully
```

### 19.2 Plan Mode

```
Plan Mode: Create a plan before executing

User: /mode plan
✓ Plan mode enabled

User: Add error handling to the API

⏺ Let me think through this carefully...

┌─ Extended Thinking ───────────────────────────────────────────┐
│ To add comprehensive error handling, I need to:               │
│ 1. Identify all API endpoints                                 │
│ 2. Determine error scenarios for each                         │
│ 3. Implement appropriate error handling                       │
│ 4. Add error response formatting                              │
│ 5. Update tests to cover error cases                          │
└───────────────────────────────────────────────────────────────┘

⏺ Here's my plan:

**Phase 1: Analysis**
- Read all API route files
- List current error handling
- Identify gaps

**Phase 2: Implementation**
- Add try-catch blocks to each endpoint
- Create error response formatter
- Handle validation errors
- Handle database errors
- Handle authentication errors

**Phase 3: Testing**
- Write error case tests
- Run existing tests
- Verify error responses

Estimated changes: 5 files
Time estimate: 15-20 minutes

Proceed with this plan? [Y/n]: _
```

### 19.3 Manual Mode

```
Manual Mode: Ask permission for each step

User: /mode manual
✓ Manual mode enabled

User: Add error handling

⏺ I'll add error handling. First, I need to read the API files.

May I read src/api.py? [Y/n]: y

[Tool: Read] ...
✓ Done

I see 5 endpoints without error handling.
May I edit src/api.py to add try-catch blocks? [Y/n]: y

[Tool: Edit] ...
✓ Done

Would you like me to run tests? [Y/n]: y

[Tool: Bash] npm test
✓ Tests passed
```

---

## 20. OUTPUT FORMATS

### 20.1 JSON Output

```bash
devorbit -p "analyze this code" -f main.py -o json

{
  "session_id": "abc123",
  "timestamp": "2025-11-17T14:30:00Z",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5",
  "prompt": "analyze this code",
  "response": {
    "content": "This code implements...",
    "tool_calls": [
      {
        "tool": "Read",
        "input": {"file_path": "main.py"},
        "output": "..."
      }
    ]
  },
  "usage": {
    "input_tokens": 1000,
    "output_tokens": 500,
    "total_tokens": 1500
  },
  "cost": 0.05,
  "duration_ms": 2500,
  "finish_reason": "end_turn"
}
```

### 20.2 Markdown Output

```bash
devorbit export abc123 --format markdown

# Devorbit Session Export
**Session ID:** abc123
**Date:** November 17, 2025
**Model:** Claude Sonnet 4.5
**Duration:** 2h 34m

## Conversation

### User [14:30:15]
> Explain this code: main.py

### Claude [14:30:20]
This code implements a web server using Express...

[Tool: Read]
File: main.py
...

### User [14:35:10]
> Add error handling

### Claude [14:35:15]
I'll add comprehensive error handling...

## Summary
- Files modified: 3
- Tests run: 25 passed
- Commits: 1
- Total cost: $0.23
```

---

## 21. ADVANCED FEATURES

### 21.1 Rewind/Checkpoint System

**Create Checkpoint:**
```
> /checkpoint save pre-refactor

✓ Checkpoint created: pre-refactor
  Saved state:
  • 45 messages
  • 8 modified files
  • Git state: main@abc1234

> /checkpoint list

Checkpoints:
  1. pre-refactor      2025-11-17 14:30  (45 msgs, 8 files)
  2. after-auth        2025-11-17 13:15  (30 msgs, 5 files)
  3. initial-setup     2025-11-17 09:00  (10 msgs, 2 files)
```

**Restore Checkpoint:**
```
> /checkpoint restore pre-refactor

⚠ This will revert to checkpoint 'pre-refactor'

Files that will be reverted: 8
Messages that will be lost: 15

Continue? [y/N]: y

✓ Restored checkpoint: pre-refactor
✓ Conversation restored to message #45
✓ 8 files reverted
✓ Git restored to: main@abc1234
```

### 21.2 Parallel Agents

**Launch Multiple Agents:**
```bash
# Terminal 1
devorbit --session-id session-1
> Implement feature A

# Terminal 2
devorbit --session-id session-2
> Implement feature B

# Terminal 3
devorbit --session-id session-3
> Write tests for features A and B
```

**Git Worktrees for Parallel Work:**
```bash
# Main work
cd ~/project
devorbit
> Implement feature

# Separate review
git worktree add ../project-review -b review/cleanup
cd ../project-review
devorbit
> Review and improve code quality
```

### 21.3 Background Tasks

**Long-Running Commands:**
```
> npm run build --prod

⏺ This will take a while. I'll run it in the background.

┌─ Background Task ─────────────────────────────────────────────┐
│ Command: npm run build --prod                                 │
│ Status: Running                                               │
│ Started: 14:30:25                                             │
│ PID: 12345                                                    │
│                                                               │
│ Latest output:                                                │
│ > Building for production...                                  │
│ > Optimizing assets...                                        │
│                                                               │
│ [View Live] [Stop] [Foreground]                               │
└───────────────────────────────────────────────────────────────┘

You can continue working while this runs.
I'll notify you when it completes.
```

**Completion Notification:**
```
[15 minutes later]

🔔 Background task completed

Command: npm run build --prod
Status: Success (exit code 0)
Duration: 15m 32s

Output:
  Build completed successfully
  Bundle size: 2.3 MB
  Generated files in dist/

[View Full Output] [Dismiss]
```

---

## 22. IMPLEMENTATION CHECKLIST

### Phase 1: Core Foundation
- [ ] Terminal UI framework (Rich/Textual)
- [ ] Color scheme & theming system
- [ ] Input handling & multi-line support
- [ ] Message display & formatting
- [ ] Streaming response handling
- [ ] Keyboard shortcuts
- [ ] Command line argument parsing
- [ ] Configuration file loading

### Phase 2: Provider Integration
- [ ] Multi-provider support (5 providers)
- [ ] Model switching
- [ ] API key management
- [ ] Request/response handling
- [ ] Token counting
- [ ] Cost calculation
- [ ] Error handling

### Phase 3: Built-in Tools
- [ ] Read tool
- [ ] Write tool
- [ ] Edit tool
- [ ] MultiEdit tool
- [ ] Bash tool (persistent session)
- [ ] Grep tool (ripgrep)
- [ ] Glob tool
- [ ] TodoWrite/TodoRead tools
- [ ] NotebookEdit/NotebookRead tools
- [ ] WebFetch tool
- [ ] WebSearch tool
- [ ] Task tool (subagents)

### Phase 4: Command System
- [ ] Slash command registry
- [ ] Built-in commands (/help, /model, /clear, etc.)
- [ ] Custom command loading (.devorbit/commands/)
- [ ] Command autocomplete
- [ ] Command history
- [ ] Command aliases

### Phase 5: Permission System
- [ ] Permission prompts
- [ ] Permission rules engine
- [ ] Auto-approve mode
- [ ] Dangerous pattern detection
- [ ] File pattern matching
- [ ] Tool allowlist/denylist

### Phase 6: Context Management
- [ ] Token counting & display
- [ ] Context window visualization
- [ ] Auto-compaction
- [ ] File attachment system
- [ ] Context breakdown view
- [ ] /clear and /compact commands

### Phase 7: Session Management
- [ ] Session persistence (.jsonl format)
- [ ] Session metadata index
- [ ] Resume/continue functionality
- [ ] Session export (JSON/Markdown/HTML)
- [ ] Session import
- [ ] Session list & search

### Phase 8: MCP Integration
- [ ] MCP client implementation
- [ ] Server lifecycle management
- [ ] Tool discovery
- [ ] .mcp.json configuration
- [ ] MCP debugging mode
- [ ] Server status monitoring

### Phase 9: Hooks System
- [ ] Hook execution engine
- [ ] Hook types (Pre/Post/Notification/Stop)
- [ ] Hook configuration (.devorbit/hooks.json)
- [ ] Hook variable substitution
- [ ] Async hook execution
- [ ] Hook error handling

### Phase 10: Subagents
- [ ] Subagent definition (.devorbit/agents/)
- [ ] Subagent invocation (Task tool)
- [ ] Subagent lifecycle management
- [ ] Parent-child communication
- [ ] Multi-agent coordination
- [ ] Subagent result integration

### Phase 11: Skills System
- [ ] Skill structure (SKILL.md format)
- [ ] Skill loading & activation
- [ ] Built-in skills integration
- [ ] Custom skill support
- [ ] Skill management UI

### Phase 12: Git Integration
- [ ] Git status detection
- [ ] Auto-commit functionality
- [ ] Commit message templates
- [ ] Branch management
- [ ] Worktree support
- [ ] Git operations display

### Phase 13: Status Line
- [ ] Status line rendering
- [ ] Template system
- [ ] Variable substitution
- [ ] Multi-line support
- [ ] Theme support
- [ ] Real-time updates

### Phase 14: Advanced Features
- [ ] Checkpoint/rewind system
- [ ] Background task management
- [ ] Parallel agent support
- [ ] Planning mode
- [ ] Manual mode
- [ ] File backup system
- [ ] Diff display (unified/side-by-side)

### Phase 15: Error Handling
- [ ] Comprehensive error messages
- [ ] Error recovery suggestions
- [ ] Warning system
- [ ] Success notifications
- [ ] Retry mechanisms

### Phase 16: Documentation
- [ ] Command reference
- [ ] Configuration guide
- [ ] API documentation
- [ ] Usage examples
- [ ] Best practices guide
- [ ] Troubleshooting guide

---

## 23. TECHNICAL REQUIREMENTS

### Dependencies
```
Python 3.10+
rich >= 13.0.0          # Terminal UI
textual >= 0.50.0       # Alternative terminal framework
prompt_toolkit >= 3.0   # Advanced input handling
pygments >= 2.17.0      # Syntax highlighting
httpx >= 0.26.0         # Async HTTP client
pydantic >= 2.5.0       # Data validation
click >= 8.1.0          # CLI framework
python-dotenv >= 1.0.0  # Environment variables
```

### Performance Targets
```
Startup time:        < 500ms
Input lag:           < 50ms
Streaming response:  Real-time (no buffering)
Context compaction:  < 2 seconds
Session save:        < 100ms
Tool execution:      Provider-dependent
Memory usage:        < 200MB baseline
```

### Compatibility
```
Operating Systems:
- Linux (Ubuntu 20.04+, other distros)
- macOS (12+)
- Windows (WSL2 recommended, native support)

Terminals:
- iTerm2
- Terminal.app
- Windows Terminal
- Alacritty
- kitty
- gnome-terminal
- konsole
- Any xterm-compatible terminal

Python:
- 3.10, 3.11, 3.12, 3.13
```

---

## 24. TESTING STRATEGY

### Unit Tests
- All tools (Read, Write, Edit, Bash, etc.)
- Command parsing
- Configuration loading
- Permission system
- Context management
- Session persistence

### Integration Tests
- Provider communication
- MCP server interaction
- Hooks execution
- Subagent coordination
- Git operations
- File operations

### E2E Tests
- Complete workflows
- Multi-turn conversations
- Tool chains
- Error recovery
- Session resume

### UI Tests
- Terminal rendering
- Input handling
- Keyboard shortcuts
- Color themes
- Status line updates

---

## CONCLUSION

This specification provides a 10000% complete blueprint for implementing a Claude Code CLI clone with multi-provider support. Every feature, UI element, command, configuration option, and behavior is documented in pixel-perfect detail.

**Key Implementation Priorities:**
1. Core terminal UI with streaming
2. Multi-provider integration (Anthropic, OpenAI, Google, Mistral, Code Llama)
3. All 15+ built-in tools
4. Complete command system with slash commands
5. Permission and context management
6. MCP integration
7. Session management
8. Hooks and subagents
9. Git integration
10. Advanced features (rewind, checkpoints, etc.)

**Estimated Timeline:**
- Core foundation: 4-6 weeks
- All tools: 3-4 weeks
- Commands & permissions: 2-3 weeks
- MCP & advanced: 3-4 weeks
- Polish & testing: 2-3 weeks
**Total: 14-20 weeks with 2-3 developers**

This specification is ready to be given to AI tools or development teams for implementation.
EOF
cat /tmp/claude-code-clone-specification-final.md
Output

# Claude Code CLI - Complete Clone Specification (PART 4 - FINAL)

## 11. PERMISSION SYSTEM

### 11.1 Permission Prompts

**Tool Permission Request:**
```
┌─ Permission Required ─────────────────────────────────────────┐
│                                                               │
│ Claude wants to:                                              │
│ Edit src/auth.py                                              │
│                                                               │
│ Changes:                                                      │
│  Line 45: - if user.password == password:                    │
│           + if verify_password(user.password, password):      │
│                                                               │
│ [A] Approve   [D] Deny   [V] View Full Diff                  │
│ [S] Skip this time   [Always allow Edit]                     │
│                                                               │
│ Your choice: _                                                │
└───────────────────────────────────────────────────────────────┘
```

**Bash Command Permission:**
```
┌─ Bash Permission Required ────────────────────────────────────┐
│                                                               │
│ Claude wants to run:                                          │
│ $ npm install express                                         │
│                                                               │
│ Working directory: ~/project/                                 │
│ Risk level: Low                                               │
│                                                               │
│ [A] Approve   [D] Deny   [E] Edit command                    │
│ [Always allow: npm install:*]                                 │
│                                                               │
│ Your choice: _                                                │
└───────────────────────────────────────────────────────────────┘
```

### 11.2 Permission Rules

**Configuration:**
```json
{
  "permissions": {
    "mode": "prompt",
    "rules": [
      {
        "tool": "Read",
        "action": "allow"
      },
      {
        "tool": "Write",
        "pattern": "src/**",
        "action": "allow"
      },
      {
        "tool": "Write",
        "pattern": ".env*",
        "action": "deny"
      },
      {
        "tool": "Bash",
        "pattern": "git:*",
        "action": "allow"
      },
      {
        "tool": "Bash",
        "pattern": "rm:*",
        "action": "deny"
      },
      {
        "tool": "Bash",
        "pattern": "sudo:*",
        "action": "deny"
      }
    ],
    "dangerous_patterns": [
      "rm -rf",
      "sudo rm",
      "> /dev/sd",
      "dd if=",
      "mkfs",
      ":(){:|:&};:"
    ]
  }
}
```

### 11.3 Auto-Approve Mode

**Enabling:**
```bash
devorbit --dangerously-skip-permissions

⚠ WARNING: All permissions will be automatically approved.
  This is dangerous and could lead to:
  - Data loss
  - System corruption
  - Security vulnerabilities

Continue? [y/N]: y

⚠ Auto-approve enabled
  All tool calls will execute without confirmation
```

**Safety in Auto-Approve:**
- Still respects deny rules
- Dangerous patterns blocked
- File permissions still checked
- Network isolation optional
- Sandbox mode recommended

---

## 12. CONTEXT MANAGEMENT

### 12.1 Context Window Display

**Status Line:**
```
Context: 45,234/200,000 tokens (22.6%)
▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
```

**Detailed View:**
```
> /context

┌─ Context Breakdown ───────────────────────────────────────────┐
│                                                               │
│ Total: 45,234 tokens (22.6% of 200,000)                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                               │
│ System Prompt      2,500 tokens   5.5%  ▓▓░░░░░░░░░░░░░░░░  │
│ Conversation      35,234 tokens  77.9%  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░  │
│ File Contents      5,000 tokens  11.1%  ▓▓░░░░░░░░░░░░░░░░  │
│ Tool Outputs       2,500 tokens   5.5%  ▓░░░░░░░░░░░░░░░░░  │
│                                                               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                               │
│ Recent Messages (last 10):        12,000 tokens              │
│ Older Messages (35 messages):     23,234 tokens              │
│                                                               │
│ Attached Files:                                               │
│  • src/auth.py                     1,200 tokens              │
│  • src/user.py                     1,500 tokens              │
│  • tests/test_auth.py              2,300 tokens              │
│                                                               │
│ [Compact] [Detach Files] [Clear Old Messages] [Close]        │
└───────────────────────────────────────────────────────────────┘
```

### 12.2 Auto-Compaction

**Trigger:**
```
⚠ Context window is 80% full (160,000/200,000 tokens)

Auto-compaction will begin soon to preserve space.
Use /clear to start fresh or /compact to do it now.
```

**Compaction Process:**
```
⏳ Compacting conversation...

  • Analyzing 45 messages
  • Identifying key information
  • Preserving recent context (last 10 messages)
  • Summarizing tool outputs
  • Condensing older messages

✓ Compacted: 160,000 → 45,000 tokens (71% reduction)

Preserved:
  • Recent 10 messages (full text)
  • Important decisions and outcomes
  • Active file references
  • Todo list state

Summarized:
  • 35 older messages
  • Tool execution history
  • File change history
```

---

## 13. SESSION MANAGEMENT

### 13.1 Session Storage

**Directory Structure:**
```
~/.devorbit/sessions/
├── active/
│   └── abc123def456.jsonl          Current active session
├── archive/
│   ├── 2025-11-17/
│   │   ├── session-001.jsonl
│   │   ├── session-002.jsonl
│   │   └── ...
│   └── 2025-11-16/
│       └── ...
└── index.json                      Session metadata index
```

**Session File Format (.jsonl):**
```jsonl
{"type":"session_start","timestamp":"2025-11-17T14:30:00Z","session_id":"abc123","provider":"anthropic","model":"claude-sonnet-4-5"}
{"type":"user_message","timestamp":"2025-11-17T14:30:15Z","content":"explain this code","files":["src/main.py"]}
{"type":"assistant_message","timestamp":"2025-11-17T14:30:20Z","content":"This code implements..."}
{"type":"tool_call","timestamp":"2025-11-17T14:30:25Z","tool":"Read","input":{"file_path":"src/main.py"}}
{"type":"tool_result","timestamp":"2025-11-17T14:30:26Z","tool":"Read","output":"..."}
```

### 13.2 Session Metadata

**File: `~/.devorbit/sessions/index.json`**
```json
{
  "sessions": [
    {
      "session_id": "abc123def456",
      "created_at": "2025-11-17T14:30:00Z",
      "updated_at": "2025-11-17T16:45:30Z",
      "provider": "anthropic",
      "model": "claude-sonnet-4-5",
      "project_dir": "~/projects/my-app",
      "git_branch": "feature/auth",
      "message_count": 45,
      "tokens_used": 45234,
      "cost_estimate": 0.23,
      "files_modified": ["src/auth.py", "src/user.py"],
      "status": "active"
    }
  ]
}
```

### 13.3 Session Navigation

**List Sessions:**
```
> devorbit sessions --list

┌────────────────────────────────────────────────────────────────┐
│ Recent Sessions                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│ Today                                                          │
│  • abc123  14:30  my-app  45 msgs  $0.23  [Resume] [Export]  │
│  • def456  09:15  website 12 msgs  $0.05  [Resume] [Export]  │
│                                                                │
│ Yesterday                                                      │
│  • ghi789  16:20  api     67 msgs  $0.45  [Resume] [Export]  │
│                                                                │
│ This Week                                                      │
│  • jkl012  Mon    webapp  23 msgs  $0.12  [Resume] [Export]  │
│  • mno345  Sun    mobile  34 msgs  $0.18  [Resume] [Export]  │
│                                                                │
│ [Load More] [Search] [Filter] [Close]                         │
└────────────────────────────────────────────────────────────────┘
```

---

## 14. STATUS LINE SYSTEM

### 14.1 Default Status Line

```
[Sonnet 4.5] [45k/200k] [main ✓] [$0.23] [2:34]
```

### 14.2 Customizable Template

**Configuration:**
```json
{
  "statusline": "${model_short} | ${context_percent}% | ${git_info} | ${cost} | ${duration}"
}
```

**Available Variables:**
```
${model}              Full model name
${model_short}        Short model name
${provider}           Provider name
${context}            Context usage (e.g., "45k/200k")
${context_percent}    Context percentage (e.g., "22%")
${context_bar}        Visual bar (e.g., "▓▓▒▒▒")
${git_branch}         Current git branch
${git_status}         Git status symbol (✓, ±, ✗)
${git_info}           Branch + status
${cost}               Session cost
${cost_total}         Total cost today
${duration}           Session duration
${message_count}      Number of messages
${time}               Current time
${date}               Current date
${project_name}       Project directory name
${mcp_servers}        Active MCP servers
${hooks_active}       Active hooks count
```

### 14.3 Multi-Line Status Line

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Sonnet 4.5 • Context: 45k/200k (22%) • Cost: $0.23  │
│ Project: my-app • Branch: main ✓ • Duration: 2h 34m        │
│ MCP: github, jira • Hooks: 3 active • Messages: 45         │
└─────────────────────────────────────────────────────────────┘
```

### 14.4 Status Line Themes

**Minimal:**
```
[Sonnet 4.5] 22% $0.23
```

**Detailed:**
```
┌─ Session Info ───────────────────────────────────────────────┐
│ Model: Claude Sonnet 4.5 (Anthropic)                        │
│ Context: 45,234/200,000 tokens (22.6%)                      │
│ Project: ~/projects/my-app                                  │
│ Git: main ✓ (clean, 3 commits ahead)                       │
│ Cost: $0.23 this session, $1.45 today                       │
│ Duration: 2h 34m 12s                                        │
│ MCP Servers: github (12 tools), jira (8 tools)             │
│ Active Hooks: format-code, run-linter, notify-desktop      │
└──────────────────────────────────────────────────────────────┘
```

---

## 15. KEYBOARD SHORTCUTS

### 15.1 Global Shortcuts

```
Ctrl+C            Interrupt current operation
Ctrl+D            Exit (if input is empty)
Ctrl+Z            Suspend Devorbit (resume with 'fg')
Ctrl+L            Clear screen (keep conversation)

Esc               Interrupt / Cancel input
Double Esc        Emergency stop / Trigger rewind

Tab               Autocomplete
Shift+Tab         Reverse autocomplete

Up Arrow          Previous command in history
Down Arrow        Next command in history
Ctrl+R            Search command history (reverse)
Ctrl+S            Search command history (forward)
```

### 15.2 Input Editing

```
Enter             Send message (single-line mode)
Ctrl+Enter        Send message (always)
Shift+Enter       New line (multi-line mode)

Ctrl+A            Move to beginning of line
Ctrl+E            Move to end of line
Ctrl+K            Delete from cursor to end
Ctrl+U            Delete from cursor to beginning
Ctrl+W            Delete previous word
Ctrl+Y            Paste (yank) deleted text

Alt+Left          Move cursor backward one word
Alt+Right         Move cursor forward one word
Alt+Backspace     Delete previous word

Ctrl+F            Move cursor forward one character
Ctrl+B            Move cursor backward one character
```

### 15.3 Navigation Shortcuts

```
Page Up           Scroll up one page
Page Down         Scroll down one page
Home              Jump to start of conversation
End               Jump to end of conversation

Ctrl+Home         Jump to first message
Ctrl+End          Jump to last message

j                 Scroll down (vim-style)
k                 Scroll up (vim-style)
g                 Go to top (vim-style)
G                 Go to bottom (vim-style)
```

### 15.4 Tool Interaction

```
e                 Expand collapsed tool output
c                 Collapse expanded tool output
v                 View full diff
a                 Apply changes (in permission prompt)
d                 Deny/Dismiss
y                 Yes/Approve
n                 No/Deny
```

---

## 16. ERROR HANDLING & MESSAGES

### 16.1 Error Types

**API Errors:**
```
✗ API Error: Rate limit exceeded

You've made too many requests. Please wait 60 seconds.

Rate limit: 50 requests per minute
Current usage: 52 requests in last minute
Reset in: 45 seconds

[Wait and Retry] [Switch Model] [Cancel]
```

**File Errors:**
```
✗ File Error: Permission denied

Cannot write to: /etc/hosts

Reason: Insufficient permissions
Suggestion: Check file permissions or run with appropriate access

[View Permissions] [Try Different Path] [Cancel]
```

**Network Errors:**
```
✗ Network Error: Connection timeout

Failed to connect to Anthropic API after 30s.

Possible causes:
• No internet connection
• Firewall blocking requests
• API service is down

[Retry] [Check Connection] [Switch Provider]
```

**Tool Errors:**
```
✗ Tool Error: Command failed

Bash command failed: npm test

Exit code: 1
Output:
  FAIL tests/auth.test.js
    ✕ should authenticate user (25 ms)

[View Full Output] [Debug] [Continue Anyway]
```

### 16.2 Warning Messages

**Context Warnings:**
```
⚠ Context window is 80% full

You've used 160,000 of 200,000 tokens.

Recommendations:
• Use /clear to start fresh
• Use /compact to compress conversation
• Detach unused files with /context

[Compact Now] [Ignore] [Clear]
```

**Model Warnings:**
```
⚠ Using fast model for this task

Current model: Claude Haiku 4.5

This model is optimized for speed but may be less capable
for complex tasks. Consider switching to Sonnet or Opus.

[Switch to Sonnet] [Continue with Haiku] [Don't Show Again]
```

### 16.3 Success Messages

```
✓ File saved: src/auth.py
✓ Tests passed (25/25)
✓ Committed: feat: add authentication
✓ MCP server started: github
✓ Session exported: session.json
```

---

## 17. FILE OPERATIONS

### 17.1 File Watching

**Auto-Reload on External Changes:**
```
⚠ File modified externally: src/auth.py

The file was changed outside of this session.

Options:
[R] Reload file content
[I] Ignore changes
[D] Show diff
[A] Always reload automatically

Choice: _
```

### 17.2 Backup System

**Automatic Backups:**
```
Before destructive operations:
• Edit creates: file.ext.backup
• Write (overwrite) creates: file.ext.backup
• MultiEdit creates: .devorbit/backups/timestamp/

Backup location: .devorbit/backups/2025-11-17-14-30-25/
Files backed up:
  • src/auth.py
  • src/user.py
```

**Restore from Backup:**
```
> /restore src/auth.py

┌─ Available Backups ───────────────────────────────────────────┐
│                                                               │
│ src/auth.py backups:                                          │
│  1. 2025-11-17 14:30  Before edit  (2.3 KB)                  │
│  2. 2025-11-17 13:15  Before edit  (2.1 KB)                  │
│  3. 2025-11-17 09:45  Before write (1.9 KB)                  │
│                                                               │
│ Select backup to restore: _                                   │
│ [Preview] [Compare] [Restore] [Cancel]                       │
└───────────────────────────────────────────────────────────────┘
```

---

## 18. GIT INTEGRATION

### 18.1 Git Status Awareness

**Status Display:**
```
Git: main ✓           Clean working directory
Git: main ±           Uncommitted changes
Git: main ✗           Merge conflicts
Git: (no branch)      Detached HEAD
Git: -                Not a git repository
```

### 18.2 Auto-Commit

**Configuration:**
```json
{
  "git": {
    "auto_commit": true,
    "commit_message_template": "${type}: ${summary}\n\n${details}",
    "commit_on_every_change": false,
    "commit_on_session_end": true,
    "auto_push": false
  }
}
```

**Commit Prompt:**
```
✓ Changes made to 3 files

Create a commit? [Y/n]: y

Commit message: feat: add authentication system

[Edit Message] [Skip] [Commit & Push] [Cancel]

✓ Committed: feat: add authentication system (abc1234)
```

### 18.3 Branch Management

```
> /git branch feature/new-feature

✓ Created branch: feature/new-feature
✓ Switched to: feature/new-feature

> /git worktree ../my-app-review feature/review

✓ Created worktree: ../my-app-review
✓ Branch: feature/review
✓ Can run separate Claude instance there
```

---

## 19. MODES & EXECUTION

### 19.1 Auto Mode (Default)

```
Auto Mode: Execute immediately without planning

User: Add error handling to the API

⏺ I'll add error handling to the API endpoints.

[Tool: Read] Reading src/api.py...
✓ Read complete

[Tool: Edit] Adding try-catch blocks...
✓ Edit complete

[Tool: Bash] Running tests...
✓ Tests passed

✓ Error handling added successfully
```

### 19.2 Plan Mode

```
Plan Mode: Create a plan before executing

User: /mode plan
✓ Plan mode enabled

User: Add error handling to the API

⏺ Let me think through this carefully...

┌─ Extended Thinking ───────────────────────────────────────────┐
│ To add comprehensive error handling, I need to:               │
│ 1. Identify all API endpoints                                 │
│ 2. Determine error scenarios for each                         │
│ 3. Implement appropriate error handling                       │
│ 4. Add error response formatting                              │
│ 5. Update tests to cover error cases                          │
└───────────────────────────────────────────────────────────────┘

⏺ Here's my plan:

**Phase 1: Analysis**
- Read all API route files
- List current error handling
- Identify gaps

**Phase 2: Implementation**
- Add try-catch blocks to each endpoint
- Create error response formatter
- Handle validation errors
- Handle database errors
- Handle authentication errors

**Phase 3: Testing**
- Write error case tests
- Run existing tests
- Verify error responses

Estimated changes: 5 files
Time estimate: 15-20 minutes

Proceed with this plan? [Y/n]: _
```

### 19.3 Manual Mode

```
Manual Mode: Ask permission for each step

User: /mode manual
✓ Manual mode enabled

User: Add error handling

⏺ I'll add error handling. First, I need to read the API files.

May I read src/api.py? [Y/n]: y

[Tool: Read] ...
✓ Done

I see 5 endpoints without error handling.
May I edit src/api.py to add try-catch blocks? [Y/n]: y

[Tool: Edit] ...
✓ Done

Would you like me to run tests? [Y/n]: y

[Tool: Bash] npm test
✓ Tests passed
```

---

## 20. OUTPUT FORMATS

### 20.1 JSON Output

```bash
devorbit -p "analyze this code" -f main.py -o json

{
  "session_id": "abc123",
  "timestamp": "2025-11-17T14:30:00Z",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5",
  "prompt": "analyze this code",
  "response": {
    "content": "This code implements...",
    "tool_calls": [
      {
        "tool": "Read",
        "input": {"file_path": "main.py"},
        "output": "..."
      }
    ]
  },
  "usage": {
    "input_tokens": 1000,
    "output_tokens": 500,
    "total_tokens": 1500
  },
  "cost": 0.05,
  "duration_ms": 2500,
  "finish_reason": "end_turn"
}
```

### 20.2 Markdown Output

```bash
devorbit export abc123 --format markdown

# Devorbit Session Export
**Session ID:** abc123
**Date:** November 17, 2025
**Model:** Claude Sonnet 4.5
**Duration:** 2h 34m

## Conversation

### User [14:30:15]
> Explain this code: main.py

### Claude [14:30:20]
This code implements a web server using Express...

[Tool: Read]
File: main.py
...

### User [14:35:10]
> Add error handling

### Claude [14:35:15]
I'll add comprehensive error handling...

## Summary
- Files modified: 3
- Tests run: 25 passed
- Commits: 1
- Total cost: $0.23
```

---

## 21. ADVANCED FEATURES

### 21.1 Rewind/Checkpoint System

**Create Checkpoint:**
```
> /checkpoint save pre-refactor

✓ Checkpoint created: pre-refactor
  Saved state:
  • 45 messages
  • 8 modified files
  • Git state: main@abc1234

> /checkpoint list

Checkpoints:
  1. pre-refactor      2025-11-17 14:30  (45 msgs, 8 files)
  2. after-auth        2025-11-17 13:15  (30 msgs, 5 files)
  3. initial-setup     2025-11-17 09:00  (10 msgs, 2 files)
```

**Restore Checkpoint:**
```
> /checkpoint restore pre-refactor

⚠ This will revert to checkpoint 'pre-refactor'

Files that will be reverted: 8
Messages that will be lost: 15

Continue? [y/N]: y

✓ Restored checkpoint: pre-refactor
✓ Conversation restored to message #45
✓ 8 files reverted
✓ Git restored to: main@abc1234
```

### 21.2 Parallel Agents

**Launch Multiple Agents:**
```bash
# Terminal 1
devorbit --session-id session-1
> Implement feature A

# Terminal 2
devorbit --session-id session-2
> Implement feature B

# Terminal 3
devorbit --session-id session-3
> Write tests for features A and B
```

**Git Worktrees for Parallel Work:**
```bash
# Main work
cd ~/project
devorbit
> Implement feature

# Separate review
git worktree add ../project-review -b review/cleanup
cd ../project-review
devorbit
> Review and improve code quality
```

### 21.3 Background Tasks

**Long-Running Commands:**
```
> npm run build --prod

⏺ This will take a while. I'll run it in the background.

┌─ Background Task ─────────────────────────────────────────────┐
│ Command: npm run build --prod                                 │
│ Status: Running                                               │
│ Started: 14:30:25                                             │
│ PID: 12345                                                    │
│                                                               │
│ Latest output:                                                │
│ > Building for production...                                  │
│ > Optimizing assets...                                        │
│                                                               │
│ [View Live] [Stop] [Foreground]                               │
└───────────────────────────────────────────────────────────────┘

You can continue working while this runs.
I'll notify you when it completes.
```

**Completion Notification:**
```
[15 minutes later]

🔔 Background task completed

Command: npm run build --prod
Status: Success (exit code 0)
Duration: 15m 32s

Output:
  Build completed successfully
  Bundle size: 2.3 MB
  Generated files in dist/

[View Full Output] [Dismiss]
```

---

## 22. IMPLEMENTATION CHECKLIST

### Phase 1: Core Foundation
- [ ] Terminal UI framework (Rich/Textual)
- [ ] Color scheme & theming system
- [ ] Input handling & multi-line support
- [ ] Message display & formatting
- [ ] Streaming response handling
- [ ] Keyboard shortcuts
- [ ] Command line argument parsing
- [ ] Configuration file loading

### Phase 2: Provider Integration
- [ ] Multi-provider support (5 providers)
- [ ] Model switching
- [ ] API key management
- [ ] Request/response handling
- [ ] Token counting
- [ ] Cost calculation
- [ ] Error handling

### Phase 3: Built-in Tools
- [ ] Read tool
- [ ] Write tool
- [ ] Edit tool
- [ ] MultiEdit tool
- [ ] Bash tool (persistent session)
- [ ] Grep tool (ripgrep)
- [ ] Glob tool
- [ ] TodoWrite/TodoRead tools
- [ ] NotebookEdit/NotebookRead tools
- [ ] WebFetch tool
- [ ] WebSearch tool
- [ ] Task tool (subagents)

### Phase 4: Command System
- [ ] Slash command registry
- [ ] Built-in commands (/help, /model, /clear, etc.)
- [ ] Custom command loading (.devorbit/commands/)
- [ ] Command autocomplete
- [ ] Command history
- [ ] Command aliases

### Phase 5: Permission System
- [ ] Permission prompts
- [ ] Permission rules engine
- [ ] Auto-approve mode
- [ ] Dangerous pattern detection
- [ ] File pattern matching
- [ ] Tool allowlist/denylist

### Phase 6: Context Management
- [ ] Token counting & display
- [ ] Context window visualization
- [ ] Auto-compaction
- [ ] File attachment system
- [ ] Context breakdown view
- [ ] /clear and /compact commands

### Phase 7: Session Management
- [ ] Session persistence (.jsonl format)
- [ ] Session metadata index
- [ ] Resume/continue functionality
- [ ] Session export (JSON/Markdown/HTML)
- [ ] Session import
- [ ] Session list & search

### Phase 8: MCP Integration
- [ ] MCP client implementation
- [ ] Server lifecycle management
- [ ] Tool discovery
- [ ] .mcp.json configuration
- [ ] MCP debugging mode
- [ ] Server status monitoring

### Phase 9: Hooks System
- [ ] Hook execution engine
- [ ] Hook types (Pre/Post/Notification/Stop)
- [ ] Hook configuration (.devorbit/hooks.json)
- [ ] Hook variable substitution
- [ ] Async hook execution
- [ ] Hook error handling

### Phase 10: Subagents
- [ ] Subagent definition (.devorbit/agents/)
- [ ] Subagent invocation (Task tool)
- [ ] Subagent lifecycle management
- [ ] Parent-child communication
- [ ] Multi-agent coordination
- [ ] Subagent result integration

### Phase 11: Skills System
- [ ] Skill structure (SKILL.md format)
- [ ] Skill loading & activation
- [ ] Built-in skills integration
- [ ] Custom skill support
- [ ] Skill management UI

### Phase 12: Git Integration
- [ ] Git status detection
- [ ] Auto-commit functionality
- [ ] Commit message templates
- [ ] Branch management
- [ ] Worktree support
- [ ] Git operations display

### Phase 13: Status Line
- [ ] Status line rendering
- [ ] Template system
- [ ] Variable substitution
- [ ] Multi-line support
- [ ] Theme support
- [ ] Real-time updates

### Phase 14: Advanced Features
- [ ] Checkpoint/rewind system
- [ ] Background task management
- [ ] Parallel agent support
- [ ] Planning mode
- [ ] Manual mode
- [ ] File backup system
- [ ] Diff display (unified/side-by-side)

### Phase 15: Error Handling
- [ ] Comprehensive error messages
- [ ] Error recovery suggestions
- [ ] Warning system
- [ ] Success notifications
- [ ] Retry mechanisms

### Phase 16: Documentation
- [ ] Command reference
- [ ] Configuration guide
- [ ] API documentation
- [ ] Usage examples
- [ ] Best practices guide
- [ ] Troubleshooting guide

---

## 23. TECHNICAL REQUIREMENTS

### Dependencies
```
Python 3.10+
rich >= 13.0.0          # Terminal UI
textual >= 0.50.0       # Alternative terminal framework
prompt_toolkit >= 3.0   # Advanced input handling
pygments >= 2.17.0      # Syntax highlighting
httpx >= 0.26.0         # Async HTTP client
pydantic >= 2.5.0       # Data validation
click >= 8.1.0          # CLI framework
python-dotenv >= 1.0.0  # Environment variables
```

### Performance Targets
```
Startup time:        < 500ms
Input lag:           < 50ms
Streaming response:  Real-time (no buffering)
Context compaction:  < 2 seconds
Session save:        < 100ms
Tool execution:      Provider-dependent
Memory usage:        < 200MB baseline
```

### Compatibility
```
Operating Systems:
- Linux (Ubuntu 20.04+, other distros)
- macOS (12+)
- Windows (WSL2 recommended, native support)

Terminals:
- iTerm2
- Terminal.app
- Windows Terminal
- Alacritty
- kitty
- gnome-terminal
- konsole
- Any xterm-compatible terminal

Python:
- 3.10, 3.11, 3.12, 3.13
```

---

## 24. TESTING STRATEGY

### Unit Tests
- All tools (Read, Write, Edit, Bash, etc.)
- Command parsing
- Configuration loading
- Permission system
- Context management
- Session persistence

### Integration Tests
- Provider communication
- MCP server interaction
- Hooks execution
- Subagent coordination
- Git operations
- File operations

### E2E Tests
- Complete workflows
- Multi-turn conversations
- Tool chains
- Error recovery
- Session resume

### UI Tests
- Terminal rendering
- Input handling
- Keyboard shortcuts
- Color themes
- Status line updates

---

## CONCLUSION

This specification provides a 10000% complete blueprint for implementing a Claude Code CLI clone with multi-provider support. Every feature, UI element, command, configuration option, and behavior is documented in pixel-perfect detail.

**Key Implementation Priorities:**
1. Core terminal UI with streaming
2. Multi-provider integration (Anthropic, OpenAI, Google, Mistral, Code Llama)
3. All 15+ built-in tools
4. Complete command system with slash commands
5. Permission and context management
6. MCP integration
7. Session management
8. Hooks and subagents
9. Git integration
10. Advanced features (rewind, checkpoints, etc.)

**Estimated Timeline:**
- Core foundation: 4-6 weeks
- All tools: 3-4 weeks
- Commands & permissions: 2-3 weeks
- MCP & advanced: 3-4 weeks
- Polish & testing: 2-3 weeks
**Total: 14-20 weeks with 2-3 developers**

This specification is ready to be given to AI tools or development teams for implementation.
