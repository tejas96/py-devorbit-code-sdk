"""Built-in CLI commands for Devorbit.

This module registers all built-in slash commands using the Command Pattern.
Commands are automatically registered with the global registry when imported.

Commands are now organized in separate modules under cli/commands/:
- system.py: help, exit, version
- navigation.py: cd, pwd, ls
- session.py: clear, status, history, permissions, autoapprove
- model.py: model, provider, planning, multiline
- debug.py: debug, tokens, hooks, recovery
- file.py: cat, init

Usage:
    # Import to register all built-in commands
    import devorbit.cli.builtin_commands  # noqa: F401
"""

from __future__ import annotations

# Import all command modules to register them
from .commands import debug, file, model, navigation, session, system  # noqa: F401


def register_builtin_commands() -> None:
    """Register all built-in commands.

    This function is called automatically when the module is imported,
    but can also be called explicitly to ensure registration.
    """
    # All commands are registered via decorators when modules load
    pass


__all__ = ["register_builtin_commands"]
