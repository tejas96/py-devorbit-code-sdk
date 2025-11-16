"""Devorbit CLI - Interactive command-line interface for the Devorbit SDK.

This module provides a Claude Code-like CLI experience with:
- Interactive REPL with rich terminal UI
- Streaming responses with token-by-token display
- Interactive tool confirmation prompts
- Token usage tracking and display
- Slash commands support
- Agent orchestration
- File operations and code manipulation
- Multi-provider LLM support

Usage:
    $ devorbit                     # Start interactive REPL
    $ devorbit --help              # Show help
    $ devorbit --no-confirm        # Disable tool confirmations
    $ devorbit --no-stream         # Disable streaming responses
    $ devorbit --provider openai   # Use OpenAI provider
"""

__all__ = [
    "CLIFormatter",
    "CLISession",
    "CommandHandler",
    "DevorbitREPL",
    "StreamingHandler",
    "main",
]


# Lazy import to avoid loading CLI dependencies unless needed
def main() -> None:
    """Main entry point for the Devorbit CLI."""
    from .main import main as cli_main  # noqa: PLC0415

    cli_main()
