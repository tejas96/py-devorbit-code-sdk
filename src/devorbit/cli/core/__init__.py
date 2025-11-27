"""Core infrastructure for Devorbit CLI.

This module provides the foundational patterns for the CLI:
- Registry Pattern: Central registration for tools, commands, hooks
- Decorator Pattern: Easy registration via decorators
- Validation: Input validation and sanitization
"""

from .registry import Registry, ToolRegistry
from .decorators import cli_tool, register_tool
from .validation import InputValidator, sanitize_path, validate_input

__all__ = [
    # Registry
    "Registry",
    "ToolRegistry",
    # Decorators
    "cli_tool",
    "register_tool",
    # Validation
    "InputValidator",
    "sanitize_path",
    "validate_input",
]
