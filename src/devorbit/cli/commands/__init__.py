"""CLI Commands Package.

This package contains all built-in CLI commands organized by category.
Commands are automatically registered when this package is imported.

Command Categories:
- system: help, exit, version
- navigation: cd, pwd, ls
- session: clear, status, history, permissions
- model: model, provider, planning, multiline
- debug: debug, tokens, hooks, recovery
- file: cat, init
"""

# Import all command modules to register them
from . import debug, file, model, navigation, session, system


__all__ = [
    "debug",
    "file",
    "model",
    "navigation",
    "session",
    "system",
]

