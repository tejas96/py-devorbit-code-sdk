"""Devorbit CLI - Interactive command-line interface for the Devorbit SDK.

This module provides a Claude Code-like CLI experience with:
- Interactive REPL with rich terminal UI
- Slash commands support
- Agent orchestration
- File operations and code manipulation
- Multi-provider LLM support

Usage:
    $ devorbit                    # Start interactive REPL
    $ devorbit --help             # Show help
    $ devorbit --provider openai  # Use OpenAI provider
"""

__all__ = [
    "main",
]


# Lazy import to avoid loading CLI dependencies unless needed
def main() -> None:
    """Main entry point for the Devorbit CLI."""
    from .main import main as cli_main

    cli_main()
