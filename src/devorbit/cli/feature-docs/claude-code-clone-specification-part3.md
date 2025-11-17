# Claude Code CLI - Complete Clone Specification (PART 3)

## 6. CONFIGURATION SYSTEM

### 6.1 Configuration File Hierarchy

**Priority Order (highest to lowest):**
```
1. Command-line flags          (--model, --provider, etc.)
2. Environment variables       (DEVORBIT_MODEL, DEVORBIT_PROVIDER)
3. Project config             (.devorbit/config.json)
4. User config                (~/.devorbit/config.json)
5. Global defaults            (built-in defaults)
```

### 6.2 Project Configuration

**File: `.devorbit/config.json`**
```json
{
  "version": "2.0",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5",
  "small_model": "claude-haiku-4-5",

  "context": {
    "max_tokens": 200000,
    "auto_compact": true,
    "compact_threshold": 0.8
  },

  "execution": {
    "mode": "auto",
    "dangerously_skip_permissions": false,
    "auto_commit": false
  },

  "permissions": {
    "allowed_tools": [
      "Read",
      "Write",
      "Edit",
      "Bash(git:*)",
      "Bash(npm:*)",
      "Grep",
      "Glob"
    ],
    "denied_tools": [
      "Bash(rm:*)",
      "Bash(sudo:*)"
    ],
    "file_patterns": {
      "allow": ["src/**", "tests/**", "docs/**"],
      "deny": [".env*", "**/*.key", "**/*.pem"]
    }
  },

  "git": {
    "auto_commit": false,
    "commit_message_template": "feat: ${summary}",
    "auto_push": false
  },

  "ui": {
    "theme": "dark",
    "statusline": "${model} | ${context} | ${git_branch} | ${cost}",
    "show_thinking": false,
    "diff_format": "unified",
    "syntax_highlighting": true
  },

  "mcp": {
    "config_file": ".mcp.json",
    "auto_load": true,
    "timeout": 30000
  },

  "hooks": {
    "enable": true,
    "config_file": ".devorbit/hooks.json"
  }
}
```

### 6.3 User Configuration

**File: `~/.devorbit/config.json`**
```json
{
  "api_keys": {
    "anthropic": "${ANTHROPIC_API_KEY}",
    "openai": "${OPENAI_API_KEY}",
    "google": "${GOOGLE_API_KEY}",
    "mistral": "${MISTRAL_API_KEY}"
  },

  "defaults": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-5",
    "temperature": 0.7,
    "max_tokens": 4000
  },

  "ui": {
    "theme": "dark",
    "color_enabled": true,
    "statusline_enabled": true,
    "notifications_enabled": true
  },

  "paths": {
    "sessions": "~/.devorbit/sessions",
    "commands": "~/.devorbit/commands",
    "agents": "~/.devorbit/agents",
    "skills": "~/.devorbit/skills",
    "exports": "~/devorbit-exports"
  },

  "telemetry": {
    "enabled": false,
    "anonymous_usage": true
  }
}
```

### 6.4 Settings File

**File: `~/.devorbit/settings.json`**
```json
{
  "session": {
    "auto_save": true,
    "save_interval": 30,
    "max_sessions": 100,
    "auto_resume": true
  },

  "context_management": {
    "auto_compact": true,
    "compact_threshold": 0.8,
    "preserve_recent_messages": 10
  },

  "tools": {
    "bash": {
      "persistent_session": true,
      "timeout": 30000,
      "max_output_length": 10000,
      "maintain_working_dir": true
    },
    "read": {
      "max_file_size": 1048576,
      "syntax_highlighting": true,
      "show_line_numbers": true
    },
    "edit": {
      "create_backup": true,
      "verify_unique_match": true
    }
  },

  "keyboard_shortcuts": {
    "send": "ctrl+enter",
    "newline": "shift+enter",
    "interrupt": "esc",
    "clear": "ctrl+l",
    "history_prev": "up",
    "history_next": "down",
    "history_search": "ctrl+r"
  }
}
```

### 6.5 DEVORBIT.md / CLAUDE.md File

**File: `.devorbit/DEVORBIT.md` or `CLAUDE.md`**
```markdown
# Project Guidelines for AI Assistant

## Project Overview
This is a web application built with React and Node.js.
Main features: user authentication, data visualization, API integration.

## Architecture
- Frontend: React 18 + TypeScript + Vite
- Backend: Node.js + Express + PostgreSQL
- Deployment: Docker + AWS

## Code Style
- Use TypeScript strict mode
- Follow Airbnb style guide
- Prefer functional components with hooks
- Use async/await over promises
- Maximum line length: 100 characters

## Testing
- Write tests for all new features
- Use Jest for unit tests
- Use Cypress for E2E tests
- Aim for 80%+ code coverage

## Git Workflow
- Feature branches from `develop`
- Commit messages: conventional commits format
- Squash commits before merging
- Always run tests before committing

## Commands to Use
```bash
# Development
npm run dev          # Start dev server
npm run build        # Build production
npm test             # Run tests
npm run lint         # Lint code

# Database
npm run migrate      # Run migrations
npm run seed         # Seed database
```

## Common Patterns

### API Error Handling
```typescript
try {
  const response = await api.get('/endpoint');
  return response.data;
} catch (error) {
  if (error.response) {
    // Handle HTTP errors
    throw new ApiError(error.response.status, error.response.data);
  }
  throw error;
}
```

### Component Structure
```typescript
// components/Feature/Feature.tsx
import { FC } from 'react';
import styles from './Feature.module.css';

interface FeatureProps {
  title: string;
  // ...
}

export const Feature: FC<FeatureProps> = ({ title }) => {
  // Implementation
};
```

## Important Notes
- Never commit .env files
- Always validate user input
- Use environment variables for config
- Document all public APIs
- Keep dependencies up to date

## File Imports
@docs/api.md           # API documentation
@docs/architecture.md  # System architecture
```

**File Import Syntax:**
```markdown
@path/to/file.md
```
This tells the AI to load and include the specified file's content
in the context when initializing.

### 6.6 Environment Variables

**File: `.env` or `.devorbit.env`**
```bash
# Provider API Keys
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxx
MISTRAL_API_KEY=xxx

# Model Configuration
DEVORBIT_PROVIDER=anthropic
DEVORBIT_MODEL=claude-sonnet-4-5
DEVORBIT_SMALL_MODEL=claude-haiku-4-5

# Context Settings
DEVORBIT_MAX_TOKENS=200000
DEVORBIT_TEMPERATURE=0.7

# Execution Settings
DEVORBIT_MODE=auto
DEVORBIT_SKIP_PERMISSIONS=false

# Git Settings
DEVORBIT_AUTO_COMMIT=false
DEVORBIT_AUTO_PUSH=false

# Bash Settings
CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=true

# MCP Settings
DEVORBIT_MCP_TIMEOUT=30000

# Logging
DEVORBIT_LOG_LEVEL=info
DEVORBIT_DEBUG=false

# Network (for debugging)
HTTPS_PROXY=
HTTP_PROXY=
```

### 6.7 MCP Configuration

**File: `.mcp.json`**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "scope": "project",
      "auto_start": true
    },

    "filesystem": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-filesystem",
        "~/projects/my-app"
      ],
      "scope": "project",
      "auto_start": true
    },

    "jira": {
      "command": "node",
      "args": [
        "~/mcp-servers/jira-server/index.js"
      ],
      "env": {
        "JIRA_URL": "${JIRA_URL}",
        "JIRA_TOKEN": "${JIRA_TOKEN}"
      },
      "scope": "user",
      "auto_start": false
    },

    "postgresql": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "mcp/postgres",
        "postgresql://user:pass@localhost/db"
      ],
      "scope": "project"
    }
  }
}
```

---

## 7. HOOKS SYSTEM

### 7.1 Hook Types

**Available Hook Points:**
```
PrePrompt         Before user prompt is sent
PostPrompt        After user prompt is processed
PreToolUse        Before any tool is executed
PostToolUse       After tool execution completes
Notification      When Claude sends a notification
Stop              When Claude finishes responding
PreCommit         Before git commit (if auto-commit enabled)
PostCommit        After git commit
Error             When an error occurs
```

### 7.2 Hooks Configuration

**File: `.devorbit/hooks.json`**
```json
{
  "hooks": [
    {
      "name": "format-code",
      "type": "PostToolUse",
      "matcher": "Edit|Write",
      "command": "npx",
      "args": ["prettier", "--write", "$FILE_PATH"],
      "async": true,
      "continue_on_error": true
    },

    {
      "name": "run-linter",
      "type": "PostToolUse",
      "matcher": "Edit|Write",
      "command": "npm",
      "args": ["run", "lint", "--", "--fix", "$FILE_PATH"],
      "async": true
    },

    {
      "name": "run-tests",
      "type": "Stop",
      "command": "npm",
      "args": ["test", "--", "--bail"],
      "prompt": "Should I run tests after these changes?",
      "model": "claude-haiku-4-5",
      "async": false
    },

    {
      "name": "notify-desktop",
      "type": "Stop",
      "command": "notify-send",
      "args": [
        "Devorbit",
        "Claude has finished responding"
      ],
      "async": true
    },

    {
      "name": "backup-before-edit",
      "type": "PreToolUse",
      "matcher": "Edit|Write",
      "command": "cp",
      "args": ["$FILE_PATH", "$FILE_PATH.backup"],
      "continue_on_error": true
    },

    {
      "name": "custom-validation",
      "type": "PreToolUse",
      "matcher": "Bash",
      "command": "node",
      "args": ["scripts/validate-command.js"],
      "stdin": true,
      "block_on_failure": true
    }
  ]
}
```

### 7.3 Hook Variables

**Available in hooks:**
```
$FILE_PATH        Path to file being operated on
$TOOL_NAME        Name of tool being executed
$TOOL_INPUT       JSON string of tool input
$TOOL_OUTPUT      JSON string of tool output
$SESSION_ID       Current session ID
$MESSAGE_COUNT    Number of messages in session
$PROVIDER         Current provider name
$MODEL            Current model name
$PROJECT_DIR      Project root directory
$GIT_BRANCH       Current git branch
$GIT_COMMIT       Latest commit hash
$USER             Current username
```

### 7.4 Hook Execution Flow

```
User sends message
       ↓
[PrePrompt Hooks] ← Can modify prompt
       ↓
Claude processes message
       ↓
Claude wants to use tool
       ↓
[PreToolUse Hooks] ← Can validate/block tool use
       ↓
Tool executes
       ↓
[PostToolUse Hooks] ← Can process results
       ↓
Claude continues response
       ↓
Claude finishes
       ↓
[Stop Hooks] ← Triggered after completion
       ↓
[Notification Hooks] ← If notification sent
```

### 7.5 Hook Display

**During Execution:**
```
┌─ Hooks Running ───────────────────────────────────────────────┐
│                                                               │
│ ⏳ format-code        Formatting src/main.py...              │
│ ✓ run-linter          Linting completed (0 issues)           │
│ ⏳ backup-before-edit Creating backup...                      │
│                                                               │
│ 2/3 hooks completed                                           │
└───────────────────────────────────────────────────────────────┘
```

**Hook Failure:**
```
✗ Hook 'run-tests' failed (exit code: 1)

Output:
  FAIL tests/auth.test.js
    ✕ should authenticate user

Continue anyway? [Y/n]: _
```

### 7.6 Interactive Hook Management

```
> /hooks

┌─ Hook Management ─────────────────────────────────────────────┐
│                                                               │
│ Active Hooks:                                                 │
│  ✓ format-code        PostToolUse   Edit|Write               │
│  ✓ run-linter         PostToolUse   Edit|Write               │
│  ✗ run-tests          Stop          (Disabled)               │
│  ✓ notify-desktop     Stop          All                      │
│                                                               │
│ [Enable/Disable] [Add Hook] [Edit] [Delete] [Close]          │
└───────────────────────────────────────────────────────────────┘
```

---

## 8. MCP INTEGRATION

### 8.1 MCP Server Management

**Starting Servers:**
```
On startup, Devorbit:
1. Reads .mcp.json
2. Starts servers with auto_start: true
3. Waits for server initialization
4. Lists available tools

Display:
⏳ Starting MCP servers...
  ✓ github (12 tools)
  ✓ filesystem (5 tools)
  ⏳ jira (connecting...)
  ✗ postgresql (connection failed)

3/4 servers started successfully
```

**Server Status:**
```
Active MCP Servers:
┌──────────────┬──────────┬───────┬──────────────────────┐
│ Server       │ Status   │ Tools │ Uptime               │
├──────────────┼──────────┼───────┼──────────────────────┤
│ github       │ Active   │ 12    │ 2h 15m               │
│ filesystem   │ Active   │ 5     │ 2h 15m               │
│ jira         │ Error    │ 0     │ -                    │
│ postgresql   │ Inactive │ 0     │ -                    │
└──────────────┴──────────┴───────┴──────────────────────┘
```

### 8.2 MCP Tool Discovery

**Automatic Discovery:**
```
When MCP server starts:
1. Query server for available tools
2. Register tools with internal registry
3. Make available to Claude
4. Show in /tools list

Format:
Server: github
Tools:
  • github_create_issue
  • github_list_issues
  • github_create_pr
  • github_get_file
  • ...
```

**Tool Usage:**
```
┌─ MCP Tool: github_create_issue ───────────────────────────────┐
│ Server: github                                                │
│ Action: Creating GitHub issue                                 │
├───────────────────────────────────────────────────────────────┤
│ Repository: owner/repo                                        │
│ Title: Fix authentication bug                                 │
│ Body: [Issue description]                                     │
│                                                               │
│ ⏳ Executing...                                               │
├───────────────────────────────────────────────────────────────┤
│ ✓ Issue created: #123                                         │
│ URL: https://github.com/owner/repo/issues/123                 │
└───────────────────────────────────────────────────────────────┘
```

### 8.3 MCP Debugging

**Debug Mode:**
```bash
devorbit --mcp-debug

Output:
[MCP] Connecting to server: github
[MCP] Server stdout: Server started on port 3000
[MCP] Tool discovered: github_create_issue
[MCP] Tool schema: {...}
[MCP] Sending request: {"method": "tools/list"}
[MCP] Response: {"tools": [...]}
```

**Connection Issues:**
```
✗ MCP Server 'jira' failed to start

Error: Connection timeout after 30s

Troubleshooting:
1. Check server command: node jira-server/index.js
2. Verify environment variables: JIRA_URL, JIRA_TOKEN
3. Test server manually: node jira-server/index.js
4. Check logs: ~/.devorbit/logs/mcp-jira.log

[Retry] [Disable Server] [View Logs]
```

---

## 9. SUBAGENTS SYSTEM

### 9.1 Subagent Definition

**File: `.devorbit/agents/code-reviewer.md`**
```markdown
---
name: code-reviewer
description: Expert code reviewer. Use immediately after writing or modifying code to ensure quality.
tools: [Read, Grep, Glob]
model: claude-opus-4-1
temperature: 0.3
---

# Code Reviewer Agent

You are a senior software engineer focused on code review.

## Your responsibilities:
1. Check code quality and maintainability
2. Identify security vulnerabilities
3. Verify best practices are followed
4. Ensure proper error handling
5. Check for performance issues
6. Verify test coverage

## Review checklist:
- [ ] Code follows project style guide
- [ ] No security vulnerabilities
- [ ] Proper error handling
- [ ] Adequate test coverage
- [ ] Performance considerations
- [ ] Documentation is clear

## Output format:
Provide a structured review with:
1. Summary (2-3 sentences)
2. Critical issues (must fix)
3. Suggestions (should consider)
4. Positive notes (what's done well)

Be constructive and specific in feedback.
```

### 9.2 Subagent Invocation

**Automatic Invocation:**
```
Claude detects it should use subagent:

⏺ I've made changes to the authentication code.
   Let me have the code reviewer check this...

┌─ Launching Subagent: code-reviewer ───────────────────────────┐
│ Task: Review authentication changes                           │
│ Model: claude-opus-4-1                                        │
│ Tools: Read, Grep, Glob                                       │
├───────────────────────────────────────────────────────────────┤
│ ⏳ Reading modified files...                                  │
│ ⏳ Analyzing code quality...                                  │
│ ⏳ Checking security...                                       │
├───────────────────────────────────────────────────────────────┤
│ ✓ Review complete                                             │
│                                                               │
│ Summary:                                                      │
│ The authentication implementation is solid overall. Found     │
│ one critical security issue and three minor improvements.     │
│                                                               │
│ Critical Issues:                                              │
│ • Password comparison is not timing-safe                      │
│   Fix: Use constant-time comparison function                  │
│                                                               │
│ Suggestions:                                                  │
│ • Add rate limiting to prevent brute force                    │
│ • Log failed authentication attempts                          │
│ • Add input validation for username                           │
│                                                               │
│ [View Full Review] [Apply Fixes]                              │
└───────────────────────────────────────────────────────────────┘
```

**Manual Invocation:**
```
> Use the code-reviewer subagent to review src/auth.py

✓ Launching code-reviewer subagent...
```

### 9.3 Subagent Types

**Common Subagent Roles:**
```
1. code-reviewer     Code quality & security
2. test-engineer     Writing & running tests
3. debugger          Finding & fixing bugs
4. doc-writer        Documentation
5. refactorer        Code refactoring
6. security-auditor  Security analysis
7. performance       Performance optimization
8. api-designer      API design & consistency
9. data-analyst      Data analysis & visualization
10. devops           Deployment & infrastructure
```

### 9.4 Subagent Communication

**Parent → Subagent:**
```json
{
  "task": "Review authentication implementation",
  "context": {
    "files": ["src/auth.py", "src/user.py"],
    "recent_changes": "Added JWT authentication",
    "focus_areas": ["security", "performance"]
  },
  "constraints": {
    "tools": ["Read", "Grep"],
    "timeout": 60000
  }
}
```

**Subagent → Parent:**
```json
{
  "status": "completed",
  "summary": "Review found 1 critical issue",
  "results": {
    "critical": ["Timing-safe password comparison needed"],
    "suggestions": ["Add rate limiting", "Log failures"],
    "positive": ["Good input validation", "Clear error messages"]
  },
  "recommendations": [
    "Apply security fix immediately",
    "Consider rate limiting for next iteration"
  ]
}
```

### 9.5 Multi-Agent Coordination

**Parallel Execution:**
```
┌─ Multi-Agent Task ────────────────────────────────────────────┐
│                                                               │
│ Task: Implement new feature                                   │
│ Agents: 3 running in parallel                                 │
│                                                               │
│ ⏳ developer         Writing feature code         (50%)       │
│ ⏳ test-engineer     Writing tests               (30%)       │
│ ✓ doc-writer         Documentation complete                   │
│                                                               │
│ [View Progress] [Stop All] [View Individual]                 │
└───────────────────────────────────────────────────────────────┘
```

---

## 10. SKILLS SYSTEM

### 10.1 Skill Structure

**Skill Directory:**
```
.devorbit/skills/my-skill/
├── SKILL.md              Main skill definition
├── examples/             Example usage
│   └── example1.md
├── prompts/              Reusable prompts
│   └── analyze.md
└── scripts/              Helper scripts
    └── process.py
```

**File: `.devorbit/skills/my-skill/SKILL.md`**
```markdown
---
name: my-skill
description: Description of what this skill does
version: 1.0.0
author: Your Name
tags: [coding, analysis]
---

# Skill Name

## Purpose
Describe what this skill is for.

## When to use
- Situation 1
- Situation 2

## How it works
1. Step 1
2. Step 2

## Examples
See examples/ directory for usage examples.

## Tools required
- Read
- Write
- Bash

## Configuration
Optional configuration settings.
```

### 10.2 Built-in Skills

**Anthropic-Managed Skills:**
```
1. docx-skill         Work with Word documents
2. xlsx-skill         Work with Excel spreadsheets
3. pptx-skill         Work with PowerPoint presentations
4. pdf-skill          Work with PDF files
5. git-workflow       Advanced git operations
6. test-generation    Generate comprehensive tests
7. code-review        Structured code review
8. api-design         REST API design patterns
```

### 10.3 Skill Activation

**Automatic Activation:**
```
User: "Can you create a PowerPoint presentation?"

⏺ I'll use the pptx-skill for this task.

┌─ Skill Activated: pptx-skill ────────────────────────────────┐
│ Loading PowerPoint manipulation capabilities...               │
│ ✓ Skill loaded                                                │
└───────────────────────────────────────────────────────────────┘

⏺ I'll create a presentation with the following structure:
   1. Title slide
   2. Overview
   3. ...
```

**Manual Activation:**
```
> /skills enable git-workflow

✓ Enabled skill: git-workflow
✓ Loaded 5 workflow templates
✓ Available commands:
   • Advanced merge strategies
   • Conflict resolution
   • Branch management
   • PR workflows
```

### 10.4 Skill Management

```
> /skills

┌─ Skills Management ───────────────────────────────────────────┐
│                                                               │
│ Active Skills:                                                │
│  ✓ pptx-skill         PowerPoint operations                   │
│  ✓ git-workflow       Advanced git workflows                  │
│                                                               │
│ Available Skills:                                             │
│  ○ docx-skill         Word documents                          │
│  ○ xlsx-skill         Excel spreadsheets                      │
│  ○ pdf-skill          PDF manipulation                        │
│  ○ test-generation    Test generation                         │
│                                                               │
│ Custom Skills: (.devorbit/skills/)                           │
│  ○ my-custom-skill    Custom workflow                         │
│                                                               │
│ [Enable] [Disable] [Add Custom] [Close]                      │
└───────────────────────────────────────────────────────────────┘
```

---

*Part 3 complete. Part 4 will continue with remaining sections...*
