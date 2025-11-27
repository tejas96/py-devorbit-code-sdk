"""Core infrastructure for Devorbit CLI.

This module provides the foundational patterns for the CLI:
- Registry Pattern: Central registration for tools, commands, hooks
- Decorator Pattern: Easy registration via decorators
- Command Pattern: Structured command handling with history
- Validation: Input validation and sanitization
"""

from .commands import (
    Command,
    CommandCategory,
    CommandContext,
    CommandDefinition,
    CommandHandler,
    CommandHistoryEntry,
    CommandInvoker,
    CommandRegistry,
    CommandResult,
    command,
    get_command_registry,
    reset_command_registry,
)
from .decorators import cli_tool, register_tool
from .registry import Registry, ToolRegistry
from .validation import InputValidator, sanitize_path, validate_input


__all__ = [
    # Registry
    "Registry",
    "ToolRegistry",
    # Commands
    "Command",
    "CommandCategory",
    "CommandContext",
    "CommandDefinition",
    "CommandHandler",
    "CommandHistoryEntry",
    "CommandInvoker",
    "CommandRegistry",
    "CommandResult",
    "command",
    "get_command_registry",
    "reset_command_registry",
    # Decorators
    "cli_tool",
    "register_tool",
    # Validation
    "InputValidator",
    "sanitize_path",
    "validate_input",
]
