"""Command handler for slash commands in Devorbit CLI.

This module provides the CommandHandler class that bridges the REPL
with the Command Pattern implementation in cli/core/commands.py.

The actual command implementations are in builtin_commands.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Import builtin commands to register them
from . import builtin_commands as _builtin_commands  # noqa: F401
from .core.commands import CommandContext, CommandInvoker, CommandResult, get_command_registry


if TYPE_CHECKING:
    from .session import CLISession


class CommandHandler:
    """Handles slash commands in the REPL.

    This class provides the interface between the REPL and the
    Command Pattern implementation. It uses CommandInvoker for
    execution and maintains backward compatibility with the
    existing REPL interface.
    """

    def __init__(self, session: CLISession) -> None:
        """Initialize command handler.

        Args:
            session: CLI session instance
        """
        self.session = session
        self.registry = get_command_registry()
        self.invoker = CommandInvoker(registry=self.registry)

    def handle_command(self, command_line: str) -> bool:
        """Handle a slash command.

        Args:
            command_line: Full command line starting with /

        Returns:
            True to continue REPL, False to exit
        """
        result = self.invoker.execute(command_line, self.session)

        # Handle special cases
        if result.data.get("action") == "toggle_multiline":
            # Return True and let REPL handle multiline toggle
            # The REPL checks for /multiline command specifically
            return True

        # Display messages based on result
        if result.success:
            if result.message and result.message not in ("toggle_multiline", ""):
                # Message is informational, already printed by command
                pass
        elif result.message:
            # Error message
            self.session.print_error(result.message)

        return result.continue_repl

    def get_completions(self, prefix: str = "") -> list[str]:
        """Get command name completions for autocomplete.

        Args:
            prefix: Prefix to filter by

        Returns:
            List of matching command names with / prefix
        """
        completions = self.registry.get_completions(prefix.lstrip("/"))
        return ["/" + c for c in completions]

    def is_command(self, text: str) -> bool:
        """Check if text is a valid command.

        Args:
            text: Text to check

        Returns:
            True if text starts with / and is a known command
        """
        if not text.startswith("/"):
            return False

        parts = text[1:].split()
        if not parts:
            return False

        return self.registry.exists(parts[0])

    def get_command_help(self, command_name: str) -> str | None:
        """Get help text for a specific command.

        Args:
            command_name: Command name (with or without /)

        Returns:
            Help text or None if command not found
        """
        name = command_name.lstrip("/")
        cmd = self.registry.get(name)
        if cmd:
            return cmd.get_help()
        return None

    def list_commands(self) -> list[str]:
        """List all available command names.

        Returns:
            List of command names (without / prefix)
        """
        return [cmd.name for cmd in self.registry.list_commands()]

    def execute_command(
        self,
        name: str,
        args: list[str] | None = None,
    ) -> CommandResult:
        """Execute a command programmatically.

        Args:
            name: Command name (without /)
            args: Command arguments

        Returns:
            CommandResult from execution
        """
        args = args or []
        command_line = f"/{name} {' '.join(args)}".strip()
        return self.invoker.execute(command_line, self.session)

    def get_context(self, args: list[str] | None = None) -> CommandContext:
        """Create a CommandContext for the current session.

        Args:
            args: Command arguments

        Returns:
            CommandContext instance
        """
        return CommandContext(
            session=self.session,
            working_dir=self.session.working_dir,
            args=args or [],
            raw_input="",
        )


__all__ = ["CommandHandler"]
