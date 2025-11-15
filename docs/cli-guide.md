# Devorbit CLI User Guide

Welcome to the Devorbit CLI! This guide will help you get started with the interactive command-line interface for autonomous coding with multiple LLM providers.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Using the REPL](#using-the-repl)
- [Slash Commands](#slash-commands)
- [Working with Files](#working-with-files)
- [Agent Orchestration](#agent-orchestration)
- [Planning Mode](#planning-mode)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)

## Installation

Install Devorbit with CLI support:

```bash
pip install devorbit-multi-llm-sdk[cli]
```

## Quick Start

### Starting the CLI

Start with default settings (Anthropic Claude):

```bash
export ANTHROPIC_API_KEY="your-api-key"
devorbit
```

Or specify options directly:

```bash
devorbit --provider anthropic --api-key your-api-key
```

### Basic Interaction

Once the CLI starts, you'll see the welcome banner and prompt:

```
devorbit project> Hello! Can you help me create a Python function?
```

The assistant will respond and can execute tools automatically to help you.

## Configuration

### Environment Variables

Set API keys for different providers:

```bash
# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Google Gemini
export GOOGLE_API_KEY="your-google-key"

# Mistral
export MISTRAL_API_KEY="your-mistral-key"
```

### Command Line Options

```bash
devorbit [OPTIONS]
```

Available options:

- `--provider, -p`: LLM provider (anthropic, openai, gemini, mistral, codellama)
- `--model, -m`: Specific model to use
- `--api-key, -k`: API key for the provider
- `--working-dir, -w`: Working directory for file operations
- `--no-color`: Disable colored output
- `--debug`: Enable debug mode with verbose logging
- `--version`: Show version information
- `--help`: Show help message

### Examples

Use OpenAI GPT-4:

```bash
devorbit --provider openai --model gpt-4-turbo --api-key your-key
```

Use Gemini in a specific directory:

```bash
devorbit --provider gemini --working-dir /path/to/project
```

Enable debug mode:

```bash
devorbit --debug
```

## Using the REPL

### Interactive Loop

The REPL (Read-Eval-Print Loop) provides an interactive session with the LLM:

1. **Type** your request or question
2. **Press Enter** to send it
3. **Wait** for the assistant's response
4. **Continue** the conversation

### Key Bindings

- **Enter**: Send message
- **Ctrl+C**: Cancel current operation
- **Ctrl+D**: Exit the REPL (same as `/exit`)
- **Up/Down Arrows**: Navigate command history

### Conversation History

The CLI maintains conversation history throughout your session:

- All messages are saved in memory
- Use `/history` to view past messages
- Use `/clear` to start fresh

## Slash Commands

Slash commands start with `/` and provide system-level functionality.

### General Commands

#### `/help`

Display help information and available commands:

```
devorbit> /help
```

#### `/exit` or `/quit`

Exit the REPL:

```
devorbit> /exit
Goodbye! 👋
```

#### `/clear`

Clear conversation history:

```
devorbit> /clear
✓ Conversation history cleared
```

#### `/history`

Show conversation history:

```
devorbit> /history

Conversation History:

1. [user] Hello!
2. [assistant] Hi there! How can I help you today?

Total messages: 2
```

### Session Commands

#### `/status`

Show current session status:

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

#### `/model [name]`

Show or change the current model:

```bash
# Show current model
devorbit> /model
Current model: claude-sonnet-4-5-20250929

# Change model
devorbit> /model gpt-4
✓ Model changed to: gpt-4
```

#### `/provider`

Show current provider:

```
devorbit> /provider
Current provider: anthropic
Note: Provider cannot be changed during session
```

### Navigation Commands

#### `/pwd`

Print working directory:

```
devorbit> /pwd
/home/user/project
```

#### `/cd <path>`

Change working directory:

```bash
devorbit> /cd /path/to/other/project
✓ Changed working directory to: /path/to/other/project

# Use ~ for home directory
devorbit> /cd ~
✓ Changed working directory to: /home/user
```

### Feature Commands

#### `/planning`

Toggle planning mode:

```
devorbit> /planning
✓ Planning mode enabled
i The agent will present plans for approval before executing changes
```

Toggle again to disable:

```
devorbit> /planning
✓ Planning mode disabled
```

## Working with Files

The CLI provides powerful file operation tools that the LLM can use automatically.

### Reading Files

Ask the assistant to read files:

```
devorbit> Can you read the contents of config.py?
```

The assistant will use the `read_file` tool to access and display the file.

### Writing Files

Request file creation or updates:

```
devorbit> Create a new file called hello.py with a simple hello world function
```

### Editing Files

Ask for specific edits:

```
devorbit> In app.py, change the PORT constant from 8000 to 3000
```

The assistant will use the `edit_file` tool to make precise changes.

### Searching Files

#### Glob Search

Find files by pattern:

```
devorbit> Find all Python files in the src directory
```

The assistant will use `glob_files` to search.

#### Grep Search

Search file contents:

```
devorbit> Find all files that contain the word "database"
```

The assistant will use `grep_code` to search.

### Directory Listing

List directory contents:

```
devorbit> Show me what files are in the current directory
```

The assistant will use `ls_directory` to list files and folders.

## Agent Orchestration

The CLI supports advanced agent orchestration for complex tasks.

### Task Tool

Launch specialized subagents for specific tasks:

```
devorbit> Use the explore agent to analyze the codebase structure
```

Available agent types:

- **general-purpose**: Multi-step tasks, research, code search
- **explore**: Fast codebase exploration and search
- **plan**: Break down complex tasks into steps
- **code-reviewer**: Analyze code quality
- **test-runner**: Execute and analyze tests

### Multi-Turn Conversations

The CLI maintains context across multiple turns:

```
devorbit> Read the file app.py
[Assistant reads the file]

devorbit> Now add error handling to the main function
[Assistant makes the edit]

devorbit> Great! Now run the tests
[Assistant executes tests]
```

## Planning Mode

Planning mode provides a safety layer for code changes.

### Enabling Planning Mode

```
devorbit> /planning
✓ Planning mode enabled
```

### How It Works

1. **Request**: You ask for a code change
2. **Plan**: The assistant presents a plan
3. **Review**: You review and approve/modify
4. **Execute**: Changes are applied after approval

### Example Workflow

```
devorbit> Refactor the database module to use async/await

[Planning Mode] The assistant presents a plan:

Plan:
1. Update database.py connection methods to async
2. Convert query methods to async/await
3. Update all callers to use await
4. Add asyncio imports

Approve this plan? (yes/no)

devorbit> yes

[Assistant executes the plan]
```

## Advanced Features

### Bash Commands

Execute shell commands:

```
devorbit> Run npm install to install dependencies
```

The assistant uses the `bash` tool to execute commands.

### Web Search

Search the web:

```
devorbit> Search for the latest Python best practices for 2025
```

The assistant uses `web_search` to find information.

### Web Fetch

Fetch web content:

```
devorbit> Fetch the content from https://example.com/api/docs
```

The assistant uses `web_fetch` to retrieve content.

### Todo Management

Track tasks:

```
devorbit> Add these tasks to my todo list: implement login, add tests, update docs
```

The assistant uses `todo_write` to manage tasks.

View todos:

```
devorbit> Show me my current todos
```

## Troubleshooting

### Common Issues

#### API Key Not Found

**Problem**: `Error: No API key provided for anthropic`

**Solution**: Set the appropriate environment variable:

```bash
export ANTHROPIC_API_KEY="your-key"
```

Or use the `--api-key` option:

```bash
devorbit --api-key your-key
```

#### Permission Denied

**Problem**: File operation fails with permission error

**Solution**:
- Check file permissions
- Run with appropriate permissions
- Change working directory to accessible location

#### Connection Errors

**Problem**: Network or API connection failures

**Solution**:
- Check internet connection
- Verify API key is valid
- Check provider service status
- Use `--debug` flag for more details

### Debug Mode

Enable debug mode for detailed error information:

```bash
devorbit --debug
```

This will:
- Show full stack traces
- Display detailed API calls
- Log tool executions
- Print internal state

### Getting Help

1. Use `/help` in the REPL for command reference
2. Use `--help` flag for CLI options
3. Check the [Command Reference](cli-commands.md)
4. Visit the [GitHub repository](https://github.com/tejas96/py-devorbit-code-sdk)

## Best Practices

### 1. Use Planning Mode for Critical Changes

Enable planning mode when making important code modifications:

```
devorbit> /planning
devorbit> Refactor the authentication system
```

### 2. Clear History for New Topics

Start fresh when switching to unrelated tasks:

```
devorbit> /clear
```

### 3. Use Specific Requests

Be clear and specific in your requests:

❌ "Fix the code"
✅ "Fix the null pointer exception in app.py line 42"

### 4. Review Changes

Always review file modifications before committing:

```
devorbit> Show me the diff of changes made to app.py
```

### 5. Leverage Agent Types

Use specialized agents for specific tasks:

```
devorbit> Use the code-reviewer agent to analyze security issues
```

## Next Steps

- Read the [Command Reference](cli-commands.md) for detailed command documentation
- Explore the [API Documentation](api-reference.md) for programmatic usage
- Check out [Examples](../examples/) for common use cases
- Learn about [MCP Integration](mcp-integration.md) for extending functionality

## Conclusion

The Devorbit CLI provides a powerful interface for autonomous coding with multiple LLM providers. Experiment with different features, use planning mode for safety, and leverage the built-in tools to maximize productivity.

Happy coding! 🚀
